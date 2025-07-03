# Medical Report Analyzer

A comprehensive web application for analyzing medical reports using Natural Language Processing (NLP) and AI techniques.

## Features

- **Medical Report Upload**: Support for PDF, DOCX, and TXT , PNG, JPEG, JPG files
- **NLP Analysis**: Extract medical entities, key terms, and insights from reports
- **AI-Powered Insights**: Get summaries, insights, and recommendations (requires Gemini API)
- **Interactive Chatbot**: Ask questions about your medical reports (RAG)

## Technologies Used

- **Backend**: Flask, Python
- **NLP Libraries**: NLTK, spaCy, Gensim
- **AI Integration**: Google Gemini API
- **Frontend**: HTML, CSS, JavaScript

## Setup Instructions

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Download required NLTK and spaCy resources:
   ```
   python -m nltk.downloader punkt stopwords
   python -m spacy download en_core_web_sm
   ```
5. Create a `.env` file based on `.env.example` and add your Gemini API key
6. Run the application:
   ```
   python app.py
   ```
7. Open your browser and navigate to `http://127.0.0.1:5000`

## Project Structure

- `app.py`: Main Flask application
- `templates/`: HTML templates
- `static/`: CSS, JavaScript, and other static files
- `uploads/`: Directory for uploaded medical reports (created automatically)

## Usage

1. Upload a medical report in PDF, DOCX, or TXT format
2. View the analysis results including medical entities, key terms, and insights
3. Use the chatbot to ask specific questions about your report

## Notes

- For full functionality, a Google Gemini API key is required
