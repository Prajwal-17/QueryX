document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const messagesContainer = document.getElementById('chat-messages');
    
    // View Toggles
    const landingView = document.getElementById('landing-view');
    const chatView = document.getElementById('chat-view');
    const getStartedBtn = document.getElementById('get-started-btn');
    const backBtn = document.getElementById('back-to-home');

    getStartedBtn.addEventListener('click', () => {
        landingView.classList.remove('active-view');
        landingView.classList.add('hidden-view');
        chatView.classList.remove('hidden-view');
        chatView.classList.add('active-view');
        setTimeout(() => userInput.focus(), 100);
    });

    backBtn.addEventListener('click', () => {
        chatView.classList.remove('active-view');
        chatView.classList.add('hidden-view');
        landingView.classList.remove('hidden-view');
        landingView.classList.add('active-view');
    });

    const createMessageElement = (content, sender, isHtml = false) => {
        const div = document.createElement('div');
        div.className = `message ${sender}-message animate-entry`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (isHtml) {
            contentDiv.innerHTML = content;
        } else {
            contentDiv.textContent = content; // Prevent XSS for user input
        }
        
        div.appendChild(contentDiv);
        return div;
    };

    const addLoadingDots = () => {
        const element = createMessageElement(
            '<div class="loading-dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>',
            'assistant',
            true
        );
        element.id = 'loading-message';
        messagesContainer.appendChild(element);
        scrollToBottom();
    };

    const removeLoadingDots = () => {
        const loading = document.getElementById('loading-message');
        if (loading) loading.remove();
    };

    const scrollToBottom = () => {
        const lastMessage = messagesContainer.lastElementChild;
        if (lastMessage) {
            lastMessage.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
    };

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const text = userInput.value.trim();
        if (!text) return;
        
        // Add user message
        const userMsg = createMessageElement(text, 'user');
        messagesContainer.appendChild(userMsg);
        userInput.value = '';
        scrollToBottom();
        
        // Add loading indicator
        addLoadingDots();

        // Simulate a tiny delay for realism before network request
        await new Promise(r => setTimeout(r, 400));
        
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query: text })
            });
            
            removeLoadingDots();
            
            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.detail || 'Server responded with an error');
            }
            
            const data = await response.json();
            
            // Parse Markdown from the AI
            const parsedHTML = marked.parse(data.answer);
            const assistantMsg = createMessageElement(parsedHTML, 'assistant', true);
            messagesContainer.appendChild(assistantMsg);
            
        } catch (error) {
            removeLoadingDots();
            console.error('Chat error:', error);
            const errorMsg = createMessageElement(`Sorry, I encountered an error: ${error.message}. Please try again later.`, 'assistant');
            errorMsg.querySelector('.message-content').style.color = '#ef4444'; // Red error text
            messagesContainer.appendChild(errorMsg);
        }
        
        scrollToBottom();
    });
});
