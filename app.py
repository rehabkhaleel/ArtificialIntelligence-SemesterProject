from flask import Flask, render_template, request, jsonify, session
import os
import uuid
import json
from werkzeug.utils import secure_filename
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from gensim.models import Word2Vec
import spacy
import google.generativeai as genai
from dotenv import load_dotenv
import PyPDF2
import docx
import re

# Load environment variables
load_dotenv()

# Download NLTK resources
nltk.download('punkt')
nltk.download('stopwords')

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')

# File upload configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize spaCy
nlp = spacy.load('en_core_web_sm')

# Configure Gemini API
gemini_model = None
if os.getenv('GEMINI_API_KEY'):
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
    gemini_model = genai.GenerativeModel('gemini-1.5-flash-001')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_file(file_path):
    ext = file_path.split('.')[-1].lower()
    try:
        if ext == 'txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif ext == 'pdf':
            reader = PyPDF2.PdfReader(open(file_path, 'rb'))
            return ''.join(page.extract_text() for page in reader.pages if page.extract_text())
        elif ext == 'docx':
            doc = docx.Document(file_path)
            return ' '.join([p.text for p in doc.paragraphs])
    except Exception as e:
        return f"Error extracting text: {e}"
    return ""


def preprocess_text(text):
    sentences = sent_tokenize(text)
    stop_words = set(stopwords.words('english'))
    processed = []
    for sentence in sentences:
        words = word_tokenize(sentence.lower())
        words = [w for w in words if w.isalpha() and w not in stop_words]
        if words:
            processed.append(words)
    return processed


def extract_medical_entities(text):
    doc = nlp(text)
    entities = [{'text': ent.text, 'label': ent.label_} for ent in doc.ents]

    custom_patterns = [
        r'\b(?:cancer|tumor|carcinoma|sarcoma|leukemia|lymphoma)\b',
        r'\b(?:diabetes|hypertension|arthritis|asthma)\b',
        r'\b\d{2,3}\s?(mg/dl|mmol/l)\b',
        r'\b\d{1,2}\.\d\s?g/dl\b',
        r'\b\d{3,4} x10\^3/\u03bcL\b',
        r'\b(?:elevated|reduced|normal|abnormal)\b',
        r'\b(?:blood pressure|heart rate|temperature|pulse|respiration)\b'
    ]

    for pattern in custom_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            entities.append({'text': match.group(), 'label': 'MEDICAL_TERM'})
    return entities


def analyze_with_gemini(text):
    if not gemini_model:
        return {'summary': 'Gemini not configured.', 'insights': [], 'recommendations': []}

    prompt = f"""
    Analyze this medical report. Return:
    1. A concise summary
    2. Key insights
    3. Follow-up recommendations

    Report:
    {text}

    Respond in JSON:
    {{
        "summary": "...",
        "insights": ["..."],
        "recommendations": ["..."]
    }}
    """
    try:
        response = gemini_model.generate_content(prompt)
        match = re.search(r'{.*}', response.text, re.DOTALL)
        return json.loads(match.group()) if match else {
            'summary': 'Could not parse Gemini response.',
            'insights': [], 'recommendations': []
        }
    except Exception as e:
        return {'summary': f'Gemini error: {e}', 'insights': [], 'recommendations': []}


def generate_word_embeddings(sentences):
    model = Word2Vec(sentences=sentences, vector_size=100, window=5, min_count=1, workers=2)
    vocab = model.wv.index_to_key
    return vocab[:20], [model.wv[w] for w in vocab[:20]]


def is_medical_query(query):
    medical_terms = [
    # General
    "diagnosis", "treatment", "symptom", "condition", "disease", "medication", "prescription",
    "report", "record", "recovery", "prognosis", "concerning", "follow-up",

    # Anatomy & Body Parts
    "heart", "lung", "liver", "kidney", "pancreas", "intestine", "brain", "spinal cord",
    "stomach", "esophagus", "bladder", "gallbladder", "colon", "throat", "ear", "eye", "nose",

    # Vital Signs & Measurements
    "heart rate", "blood pressure", "temperature", "respiration", "oxygen", "pulse",
    "BMI", "body mass index", "cholesterol", "glucose", "blood sugar",

    # Symptoms
    "fever", "fatigue", "headache", "cough", "sore throat", "nausea", "vomiting", "diarrhea",
    "pain", "chills", "sweating", "shortness of breath", "dizziness", "rash", "itching", "bleeding",

    # Diseases
    "cancer", "diabetes", "hypertension", "asthma", "arthritis", "pneumonia", "tuberculosis",
    "stroke", "epilepsy", "obesity", "hepatitis", "anemia", "HIV", "AIDS", "covid", "depression",
    "anxiety", "bipolar", "schizophrenia",

    # Infections
    "infection", "bacterial", "viral", "fungal", "sepsis", "UTI", "influenza", "cold", "flu",

    # Treatments & Procedures
    "surgery", "chemotherapy", "radiation", "transplant", "dialysis", "vaccination", "immunization",
    "therapy", "physiotherapy", "rehabilitation", "biopsy", "IV", "injection", "infusion",

    # Tests & Diagnostics
    "MRI", "CT", "PET scan", "X-ray", "ultrasound", "blood test", "lab results", "lab result",
    "EKG", "ECG", "EEG", "CBC", "metabolic panel", "urine test", "swab", "biopsy", "screening",

    # Medications
    "panadol", "paracetamol", "ibuprofen", "aspirin", "insulin", "metformin", "atorvastatin",
    "omeprazole", "amoxicillin", "antibiotic", "antiviral", "steroid", "antidepressant", "antihistamine",

    # Oncology terms
    "tumor", "benign", "malignant", "oncology", "metastasis", "carcinoma", "lymphoma", "melanoma",
    "sarcoma", "biopsy", "radiologist", "oncologist", "chemotherapy", "radiation therapy",

    # Cardiology
    "cardiology", "arrhythmia", "tachycardia", "bradycardia", "myocardial infarction", "angioplasty",
    "bypass surgery", "cholesterol", "echocardiogram", "cardiologist",

    # Neurology
    "neurology", "seizure", "stroke", "parkinson", "dementia", "alzheimer", "multiple sclerosis",
    "nerve", "neuron", "neurologist",

    # Pediatrics / OB-GYN
    "obstetrics", "gynecology", "pregnancy", "labor", "delivery", "ultrasound", "fetus", "infant",
    "pediatrician", "contraception", "menstruation", "fertility",

    # Mental Health
    "psychiatry", "psychology", "depression", "anxiety", "stress", "trauma", "PTSD", "OCD",
    "bipolar", "therapy", "counseling", "psychiatrist", "psychologist",

    # Surgery / Wounds
    "incision", "suturing", "stitches", "anesthesia", "laparoscopic", "post-op", "pre-op",
    "recovery", "drain", "bandage", "wound care",

    # Emergency & Monitoring
    "ICU", "emergency", "triage", "monitoring", "vital signs", "ER", "CPR", "defibrillator",
    "oxygen saturation", "respirator", "ventilator"
]

    query = query.lower()
    return any(term in query for term in medical_terms)


def chat_response(query, report_text):
    if not is_medical_query(query):
        return "Please ask a medical question related to your uploaded report."

    if gemini_model:
        try:
            prompt = f"Medical Report:\n{report_text}\n\nQuestion:\n{query}\n\nAnswer:"
            return gemini_model.generate_content(prompt).text
        except Exception as e:
            return f"Gemini error: {e}"
    return chat_response_rag(query, report_text)


def chat_response_rag(query, report_text):
    return "RAG not implemented. Please configure Gemini for better results."


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded.'}), 400

    file = request.files['file']
    if not file or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type.'}), 400

    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(path)

    text = extract_text_from_file(path)
    session['report_text'] = text
    session['report_filename'] = filename

    processed = preprocess_text(text)
    entities = extract_medical_entities(text)
    vocab, _ = generate_word_embeddings(processed)
    gemini_data = analyze_with_gemini(text)

    return jsonify({
        'filename': filename,
        'text_length': len(text),
        'sentences': len(processed),
        'entities': entities,
        'key_terms': vocab,
        'gemini_analysis': gemini_data
    })


@app.route('/analyze')
def analyze():
    text = session.get('report_text', '')
    filename = session.get('report_filename', '')
    if not text:
        return render_template('index.html', error="No report uploaded.")

    processed = preprocess_text(text)
    entities = extract_medical_entities(text)
    vocab, _ = generate_word_embeddings(processed)
    gemini_data = analyze_with_gemini(text)

    return render_template('analyze.html',
                           filename=filename,
                           text_preview=text[:500] + '...' if len(text) > 500 else text,
                           text_length=len(text),
                           sentences=len(processed),
                           entities=entities,
                           key_terms=vocab,
                           gemini_analysis=gemini_data)


@app.route('/chat', methods=['POST'])
def chat():
    query = request.json.get('query', '')
    report_text = session.get('report_text', '')
    response = chat_response(query, report_text)
    return jsonify({'response': response})


if __name__ == '__main__':
    import spacy.util
    if not spacy.util.is_package('en_core_web_sm'):
        os.system('python -m spacy download en_core_web_sm')
    app.run(debug=True)
