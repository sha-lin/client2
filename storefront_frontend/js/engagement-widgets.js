/**
 * Engagement Widgets Module
 * Handles WhatsApp, AI Chat Bot, and Email Sales interactions
 */

class EngagementWidgets {
    constructor(config = {}) {
        this.config = {
            whatsappNumber: config.whatsappNumber || '1234567890',
            whatsappMessage: config.whatsappMessage || 'Hi, I\'d like to know more about your services',
            chatbotApiUrl: config.chatbotApiUrl || '/api/v1/chatbot/',
            salesEmail: config.salesEmail || 'sales@printduka.com',
            ...config
        };
        
        this.chatbotActive = false;
        this.conversationHistory = [];
        this.init();
    }

    /**
     * Initialize engagement widgets
     */
    init() {
        this.setupEventListeners();
        this.loadChatbotModal();
    }

    /**
     * Setup event listeners for widgets
     */
    setupEventListeners() {
        const chatbotTrigger = document.getElementById('chatbot-trigger');
        
        if (chatbotTrigger) {
            chatbotTrigger.addEventListener('click', (e) => {
                e.preventDefault();
                // Toggle chatbot - open if closed, close if open
                if (this.chatbotActive) {
                    this.closeChatbot();
                } else {
                    this.openChatbot();
                }
            });
        }

        // Close chatbot on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.chatbotActive) {
                this.closeChatbot();
            }
        });
    }

    /**
     * Load chatbot modal HTML
     */
    loadChatbotModal() {
        const chatbotModalHTML = `
            <div id="chatbot-modal" class="chatbot-modal" style="display: none;">
                <div class="chatbot-container">
                    <div class="chatbot-header">
                        <div class="chatbot-header-content">
                            <h3>PrintDuka Assistant</h3>
                            <p class="chatbot-status">Online & Ready to Help</p>
                        </div>
                        <button class="chatbot-close-btn" id="chatbot-close">&times;</button>
                    </div>
                    
                    <div class="chatbot-messages" id="chatbot-messages">
                        <div class="chatbot-message bot-message">
                            <div class="message-content">
                                <p>👋 Hello! I'm your PrintDuka Assistant. How can I help you today?</p>
                                <div class="quick-replies">
                                    <button class="quick-reply-btn" data-question="Tell me about your services">Services</button>
                                    <button class="quick-reply-btn" data-question="What are your pricing options?">Pricing</button>
                                    <button class="quick-reply-btn" data-question="How do I place an order?">How to Order</button>
                                    <button class="quick-reply-btn" data-question="What's your delivery time?">Delivery</button>
                                </div>
                            </div>
                            <span class="message-time">just now</span>
                        </div>
                    </div>
                    
                    <div class="chatbot-input-area">
                        <input 
                            type="text" 
                            id="chatbot-input" 
                            class="chatbot-input" 
                            placeholder="Type your message..."
                            autocomplete="off">
                        <button class="chatbot-send-btn" id="chatbot-send">
                            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" viewBox="0 0 16 16">
                                <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.354a.5.5 0 0 0 0 .708L7.293 7l-1.939 1.939a.5.5 0 1 0 .707.707L8 7.707l1.939 1.939a.5.5 0 0 0 .707-.707L8.707 7l1.939-1.939a.5.5 0 0 0-.707-.707L8 6.293 6.061 4.354a.5.5 0 0 0-.707 0z"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>

            <style>
                .chatbot-modal {
                    position: fixed;
                    bottom: 0;
                    right: 20px;
                    width: 380px;
                    max-height: 600px;
                    background: white;
                    border-radius: 12px 12px 0 0;
                    box-shadow: 0 5px 40px rgba(0, 0, 0, 0.2);
                    display: flex;
                    flex-direction: column;
                    z-index: 9999;
                    animation: slideUp 0.3s ease-out;
                }

                @keyframes slideUp {
                    from {
                        transform: translateY(100%);
                        opacity: 0;
                    }
                    to {
                        transform: translateY(0);
                        opacity: 1;
                    }
                }

                .chatbot-container {
                    display: flex;
                    flex-direction: column;
                    height: 100%;
                }

                .chatbot-header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 1rem;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-radius: 12px 12px 0 0;
                }

                .chatbot-header h3 {
                    margin: 0;
                    font-size: 1.1rem;
                    font-weight: 600;
                }

                .chatbot-status {
                    margin: 0.25rem 0 0 0;
                    font-size: 0.85rem;
                    opacity: 0.9;
                }

                .chatbot-close-btn {
                    background: none;
                    border: none;
                    color: white;
                    font-size: 1.5rem;
                    cursor: pointer;
                    padding: 0;
                    width: 30px;
                    height: 30px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: transform 0.2s;
                }

                .chatbot-close-btn:hover {
                    transform: scale(1.1);
                }

                .chatbot-messages {
                    flex: 1;
                    overflow-y: auto;
                    padding: 1rem;
                    background-color: #f5f5f5;
                }

                .chatbot-message {
                    margin-bottom: 1rem;
                    animation: fadeIn 0.3s ease-in;
                }

                @keyframes fadeIn {
                    from {
                        opacity: 0;
                        transform: translateY(10px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }

                .bot-message .message-content {
                    background: white;
                    padding: 0.75rem 1rem;
                    border-radius: 12px;
                    border-left: 3px solid #667eea;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                }

                .bot-message .message-content p {
                    margin: 0 0 0.5rem 0;
                    font-size: 0.95rem;
                    color: #333;
                }

                .user-message .message-content {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 0.75rem 1rem;
                    border-radius: 12px;
                    margin-left: 2rem;
                }

                .user-message .message-content p {
                    margin: 0;
                    font-size: 0.95rem;
                }

                .message-time {
                    font-size: 0.75rem;
                    color: #999;
                    margin-top: 0.25rem;
                    display: block;
                    text-align: right;
                }

                .quick-replies {
                    display: flex;
                    flex-direction: column;
                    gap: 0.5rem;
                    margin-top: 0.5rem;
                }

                .quick-reply-btn {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 0.5rem 1rem;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 0.85rem;
                    transition: all 0.2s;
                }

                .quick-reply-btn:hover {
                    transform: translateX(4px);
                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
                }

                .chatbot-input-area {
                    display: flex;
                    gap: 0.5rem;
                    padding: 1rem;
                    background: white;
                    border-top: 1px solid #eee;
                }

                .chatbot-input {
                    flex: 1;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    padding: 0.75rem;
                    font-size: 0.95rem;
                    font-family: inherit;
                    transition: border-color 0.2s;
                }

                .chatbot-input:focus {
                    outline: none;
                    border-color: #667eea;
                    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
                }

                .chatbot-send-btn {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 0.75rem 1rem;
                    border-radius: 6px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s;
                }

                .chatbot-send-btn:hover {
                    transform: scale(1.05);
                }

                .chatbot-send-btn:active {
                    transform: scale(0.95);
                }

                .typing-indicator {
                    display: flex;
                    gap: 4px;
                    padding: 0.75rem 1rem;
                }

                .typing-dot {
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    background: #999;
                    animation: typing 1.4s infinite;
                }

                .typing-dot:nth-child(2) {
                    animation-delay: 0.2s;
                }

                .typing-dot:nth-child(3) {
                    animation-delay: 0.4s;
                }

                @keyframes typing {
                    0%, 60%, 100% {
                        opacity: 0.3;
                    }
                    30% {
                        opacity: 1;
                    }
                }

                /* Mobile responsiveness */
                @media (max-width: 480px) {
                    .chatbot-modal {
                        width: 100%;
                        right: 0;
                        max-height: 80vh;
                        border-radius: 12px 12px 0 0;
                    }
                }
            </style>
        `;

        // Append chatbot modal to body
        if (!document.getElementById('chatbot-modal')) {
            document.body.insertAdjacentHTML('beforeend', chatbotModalHTML);
            this.setupChatbotListeners();
        }
    }

    /**
     * Setup chatbot modal event listeners
     */
    setupChatbotListeners() {
        const closeBtn = document.getElementById('chatbot-close');
        const sendBtn = document.getElementById('chatbot-send');
        const inputField = document.getElementById('chatbot-input');
        const quickReplyBtns = document.querySelectorAll('.quick-reply-btn');

        closeBtn.addEventListener('click', () => this.closeChatbot());
        sendBtn.addEventListener('click', () => this.sendMessage());
        inputField.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });

        quickReplyBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const question = e.target.dataset.question;
                this.handleUserMessage(question);
            });
        });
    }

    /**
     * Open chatbot modal
     */
    openChatbot() {
        const modal = document.getElementById('chatbot-modal');
        if (modal) {
            modal.style.display = 'flex';
            this.chatbotActive = true;
            document.getElementById('chatbot-input').focus();
        }
    }

    /**
     * Close chatbot modal
     */
    closeChatbot() {
        const modal = document.getElementById('chatbot-modal');
        if (modal) {
            modal.style.display = 'none';
            this.chatbotActive = false;
        }
    }

    /**
     * Send message from input
     */
    sendMessage() {
        const inputField = document.getElementById('chatbot-input');
        const message = inputField.value.trim();
        
        if (message.length > 0) {
            this.handleUserMessage(message);
            inputField.value = '';
            inputField.focus();
        }
    }

    /**
     * Handle user message and get bot response
     */
    async handleUserMessage(userMessage) {
        // Add user message to conversation
        this.addMessageToChat(userMessage, 'user');
        this.conversationHistory.push({
            role: 'user',
            content: userMessage,
            timestamp: new Date()
        });

        // Show typing indicator
        this.showTypingIndicator();

        try {
            // Get bot response
            const response = await this.getBotResponse(userMessage);
            
            // Remove typing indicator
            this.removeTypingIndicator();

            // Add bot response to chat
            this.addMessageToChat(response, 'bot');
            this.conversationHistory.push({
                role: 'bot',
                content: response,
                timestamp: new Date()
            });
        } catch (error) {
            this.removeTypingIndicator();
            const errorMessage = 'Sorry, I encountered an error. Please try again or contact our sales team.';
            this.addMessageToChat(errorMessage, 'bot');
        }
    }

    /**
     * Get bot response from API or predefined responses
     */
    async getBotResponse(userMessage) {
        // Predefined responses for common questions
        const responses = {
            'services': 'We offer a wide range of printing services including digital printing, offset printing, packaging design, and more. Visit our products page for detailed information about our services.',
            'pricing': 'Our pricing depends on the volume, type of service, and specifications. We recommend using our Quote Builder to get an instant quote, or you can email our sales team for a custom quote.',
            'order': 'You can place an order by:\n1. Creating a quote using our Quote Builder\n2. Logging into your account\n3. Placing a new order\n4. Tracking your order in real-time',
            'delivery': 'Delivery times vary based on the order complexity and volume. Standard orders are delivered within 5-7 business days. Rush orders available for an additional fee.',
            'contact': 'You can reach us via:\n📧 Email: sales@printduka.com\n📞 WhatsApp: +1234567890\n💬 This chat',
        };

        // Check if message matches any keyword
        const lowerMessage = userMessage.toLowerCase();
        
        for (const [key, response] of Object.entries(responses)) {
            if (lowerMessage.includes(key)) {
                return response;
            }
        }

        // Default response
        return 'Thank you for your question! Our team is here to help. For more detailed information, please reach out to our sales team via email (sales@printduka.com) or WhatsApp. You can also visit our Products page to explore our services.';
    }

    /**
     * Add message to chat display
     */
    addMessageToChat(message, sender) {
        const messagesContainer = document.getElementById('chatbot-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chatbot-message ${sender}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Handle multi-line messages
        const paragraphs = message.split('\n').filter(line => line.trim());
        paragraphs.forEach(para => {
            const p = document.createElement('p');
            p.textContent = para;
            contentDiv.appendChild(p);
        });

        messageDiv.appendChild(contentDiv);

        const timeSpan = document.createElement('span');
        timeSpan.className = 'message-time';
        timeSpan.textContent = this.getCurrentTime();
        messageDiv.appendChild(timeSpan);

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    /**
     * Show typing indicator
     */
    showTypingIndicator() {
        const messagesContainer = document.getElementById('chatbot-messages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chatbot-message bot-message';
        typingDiv.id = 'typing-indicator';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content typing-indicator';
        contentDiv.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;

        typingDiv.appendChild(contentDiv);
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    /**
     * Remove typing indicator
     */
    removeTypingIndicator() {
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    /**
     * Get current time in HH:MM format
     */
    getCurrentTime() {
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        return `${hours}:${minutes}`;
    }

    /**
     * Update WhatsApp number
     */
    updateWhatsAppNumber(number) {
        this.config.whatsappNumber = number;
    }

    /**
     * Update sales email
     */
    updateSalesEmail(email) {
        this.config.salesEmail = email;
    }
}

// Initialize engagement widgets when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (typeof window.engagementWidgets === 'undefined') {
        window.engagementWidgets = new EngagementWidgets({
            whatsappNumber: '1234567890', // Update with your actual business number
            salesEmail: 'sales@printduka.com' // Update with your sales email
        });
    }
});
