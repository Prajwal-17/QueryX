document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const form = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const messagesContainer = document.getElementById('chat-messages');

    // Theme setup
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (prefersDark) {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
    
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        
        // Update icon based on theme
        const svg = themeToggle.querySelector('svg');
        if (newTheme === 'dark') {
            svg.innerHTML = '<circle cx="12" cy="12" r="5"/><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>';
        } else {
            svg.innerHTML = '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>';
        }
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
            
            const assistantMsg = createMessageElement(data.answer, 'assistant');
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
