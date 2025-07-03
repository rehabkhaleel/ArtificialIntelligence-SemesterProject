document.addEventListener('DOMContentLoaded', function() {
    // File upload handling
    const fileInput = document.getElementById('file-input');
    const fileName = document.getElementById('file-name');
    const uploadForm = document.getElementById('upload-form');
    const uploadProgress = document.getElementById('upload-progress');
    const uploadError = document.getElementById('upload-error');
    const errorMessage = document.getElementById('error-message');
    

    if (fileInput) {
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                fileName.textContent = this.files[0].name;
            } else {
                fileName.textContent = 'No file chosen';
            }
        });
    }
    
   if (uploadForm) {
    uploadForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const formData = new FormData(this);

        // Clear previous error
        uploadError.classList.add('hidden');
        errorMessage.textContent = '';

        if (!fileInput.files.length) {
            uploadError.classList.remove('hidden');
            errorMessage.textContent = 'Please select a file to upload.';
            return;
        }

        // Show upload progress
        uploadProgress.classList.remove('hidden');

        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(async response => {
            uploadProgress.classList.add('hidden');
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Server error: ' + response.status);
            }
            return response.json();
        })
        .then(data => {
             // Optional: You could store some response data in sessionStorage if needed
            // sessionStorage.setItem('reportData', JSON.stringify(data));

            // Redirect to the analysis page
            window.location.href = '/analyze';
        })
        .catch(error => {
            uploadProgress.classList.add('hidden');
            uploadError.classList.remove('hidden');
            errorMessage.textContent = error.message;
        });
    });
}

    
    // Chat functionality
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const suggestionButtons = document.querySelectorAll('.suggestion');
    
    function addMessage(content, isUser = false) {
        const cleanContent = content.replace(/\*/g, '');

        const messageDiv = document.createElement('div');
        messageDiv.className = isUser ? 'message user' : 'message system';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const messageParagraph = document.createElement('p');
        messageParagraph.textContent = cleanContent;
        
        messageContent.appendChild(messageParagraph);
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // old code ,do not delete
    // function sendMessage(message) {
    //     if (!message.trim()) return;
        
    //     // Add user message to chat
    //     addMessage(message, true);
        
    //     // Clear input
    //     userInput.value = '';
        
    //     // Send to server
    //     fetch('/chat', {
    //         method: 'POST',
    //         headers: {
    //             'Content-Type': 'application/json'
    //         },
    //         body: JSON.stringify({ query: message })
    //     })
    //     .then(response => response.json())
    //     .then(data => {
    //         // Add response to chat
    //         addMessage(data.response);
    //     })
    //     .catch(error => {
    //         addMessage('Sorry, there was an error processing your request.');
    //         console.error('Error:', error);
    //     });
    // }

    function sendMessage(message) {
    if (!message.trim()) return;

    addMessage(message, true);
    userInput.value = '';

    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: message })
    })
        .then(response => response.json())
        .then(data => {
            addMessage(data.response, false, true); // Enable typing animation
        })
        .catch(error => {
            addMessage('Sorry, there was an error processing your request.', false, false);
            console.error('Error:', error);
        });
}

    
    if (sendButton) {
        sendButton.addEventListener('click', function() {
            sendMessage(userInput.value);
        });
    }
    
    if (userInput) {
        userInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage(userInput.value);
            }
        });
    }
    
    if (suggestionButtons) {
        suggestionButtons.forEach(button => {
            button.addEventListener('click', function() {
                const query = this.getAttribute('data-query');
                sendMessage(query);
            });
        });
    }
    
    // Progress bar animation for demo purposes
    const progressFill = document.querySelector('.progress-fill');
    if (progressFill && uploadProgress && !uploadProgress.classList.contains('hidden')) {
        let width = 0;
        const interval = setInterval(() => {
            if (width >= 100) {
                clearInterval(interval);
            } else {
                width += 1;
                progressFill.style.width = width + '%';
            }
        }, 20);
    }
});
document.getElementById("send-button").addEventListener("click", async () => {
    const input = document.getElementById("user-input").value;
    if (!input) return;

    const res = await fetch("/chat", {
        method: "POST",
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ query: input })
    });

    const data = await res.json();
    const reply = data.response;

    // Append messages to chat
    const messages = document.getElementById("chat-messages");
    messages.innerHTML += `<div class="message user"><div class="message-content">${input}</div></div>`;
    messages.innerHTML += `<div class="message system"><div class="message-content">${reply}</div></div>`;
    document.getElementById("user-input").value = "";
});
