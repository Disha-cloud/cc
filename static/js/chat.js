document.addEventListener('DOMContentLoaded', function() {
    const messageContainer = document.getElementById('messages');
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const typingIndicator = document.getElementById('typing-indicator');
    
    // Variables for tracking
    let lastMessageId = 0;
    let typingTimer;
    let isTyping = false;
    
    // Find the last message id
    if (messageContainer) {
        const allMessages = messageContainer.querySelectorAll('.message');
        if (allMessages.length > 0) {
            // Get the data-id of the last message if exists
            const lastMessage = allMessages[allMessages.length - 1];
            if (lastMessage.dataset.id) {
                lastMessageId = parseInt(lastMessage.dataset.id);
            }
        }
        
        // Scroll to bottom of messages
        messageContainer.scrollTop = messageContainer.scrollHeight;
    }
    
    // Set up typing indicator events
    if (messageInput) {
        messageInput.addEventListener('keydown', function() {
            if (!isTyping) {
                isTyping = true;
                // Signal to server that user is typing (could be done via AJAX)
            }
            
            clearTimeout(typingTimer);
            typingTimer = setTimeout(function() {
                isTyping = false;
                // Signal to server that user stopped typing
            }, 1000);
        });
    }
    
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
                    messageDiv.dataset.id = data.message.id;
                    messageDiv.innerHTML = `
                        ${data.message.content}
                        <div class="message-time">${data.message.time}</div>
                    `;
                    messageContainer.appendChild(messageDiv);
                    
                    // Clear form and scroll to bottom
                    messageInput.value = '';
                    messageContainer.scrollTop = messageContainer.scrollHeight;
                    
                    // Update last message id
                    if (data.message.id > lastMessageId) {
                        lastMessageId = data.message.id;
                    }
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
    
    // Set up polling for new messages
    if (messageContainer) {
        const receiverId = messageForm.querySelector('input[name="receiver_id"]').value;
        
        // Poll for new messages every 3 seconds
        setInterval(function() {
            fetch(`/get_new_messages/${receiverId}/${lastMessageId}`)
                .then(response => response.json())
                .then(messages => {
                    if (messages.length > 0) {
                        // Add new messages to chat
                        messages.forEach(msg => {
                            const messageDiv = document.createElement('div');
                            messageDiv.className = `message ${msg.is_self ? 'sent' : 'received'}`;
                            messageDiv.dataset.id = msg.id;
                            messageDiv.innerHTML = `
                                ${msg.content}
                                <div class="message-time">${msg.time}</div>
                            `;
                            messageContainer.appendChild(messageDiv);
                            
                            // Update last message id
                            if (msg.id > lastMessageId) {
                                lastMessageId = msg.id;
                            }
                        });
                        
                        // Scroll to bottom when new messages arrive
                        messageContainer.scrollTop = messageContainer.scrollHeight;
                    }
                })
                .catch(error => console.error('Error fetching new messages:', error));
        }, 3000);
    }
    
    // Show/hide typing indicator (this would normally be driven by server events)
    // This is just a demo of the UI - in a real app you'd use websockets
    if (typingIndicator) {
        // Randomly show typing indicator for demo purposes
        setInterval(function() {
            const shouldShow = Math.random() > 0.8; // 20% chance to show
            if (shouldShow) {
                typingIndicator.style.display = 'block';
                setTimeout(function() {
                    typingIndicator.style.display = 'none';
                }, 2000 + Math.random() * 3000); // Show for 2-5 seconds
            }
        }, 10000); // Check every 10 seconds
    }
});