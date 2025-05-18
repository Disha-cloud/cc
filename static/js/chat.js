// Chat functionality

document.addEventListener('DOMContentLoaded', function() {
    const messageContainer = document.getElementById('messages');
    const messageForm = document.getElementById('message-form');
    
    if (messageContainer) {
        // Scroll to bottom of messages
        messageContainer.scrollTop = messageContainer.scrollHeight;
        
        // Submit message form with AJAX
        if (messageForm) {
            messageForm.addEventListener('submit', function(event) {
                event.preventDefault();
                
                const formData = new FormData(messageForm);
                
                fetch(messageForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Add new message to chat
                        const messageDiv = document.createElement('div');
                        messageDiv.className = 'message sent';
                        messageDiv.innerHTML = `
                            <div class="message-content">
                                <p>${data.message.content}</p>
                                <small>${data.message.time}</small>
                            </div>
                        `;
                        messageContainer.appendChild(messageDiv);
                        
                        // Clear form and scroll to bottom
                        document.getElementById('content').value = '';
                        messageContainer.scrollTop = messageContainer.scrollHeight;
                    } else {
                        alert('Error sending message. Please try again.');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error sending message. Please try again.');
                });
            });
        }
    }
});