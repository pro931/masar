function sendMessage() {
    const userInput = document.getElementById('userInput').value.trim();
    if (!userInput) {
        console.log("الإدخال فارغ، لن يتم إرسال الرسالة.");
        return;
    }

    const chatMessages = document.getElementById('chatMessages');

    // إضافة رسالة المستخدم
    const userMessage = document.createElement('p');
    userMessage.className = 'user-message';
    userMessage.style.direction = 'rtl';
    userMessage.textContent = 'أنت: ' + userInput;
    chatMessages.appendChild(userMessage);

    // إضافة رسالة تحميل
    const loadingMessage = document.createElement('p');
    loadingMessage.className = 'bot-message loading';
    loadingMessage.style.direction = 'rtl';
    loadingMessage.textContent = 'مسار: جارٍ التفكير... 🤖';
    chatMessages.appendChild(loadingMessage);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // إرسال الرسالة للـ FastAPI
    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userInput })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`خطأ في الشبكة: ${response.status} - ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        chatMessages.removeChild(loadingMessage);
        const botMessage = document.createElement('p');
        botMessage.className = 'bot-message';
        botMessage.style.direction = 'rtl';
        botMessage.textContent = 'مسار: ' + data.response;
        chatMessages.appendChild(botMessage);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    })
    .catch(error => {
        chatMessages.removeChild(loadingMessage);
        const errorMessage = document.createElement('p');
        errorMessage.className = 'bot-message';
        errorMessage.style.direction = 'rtl';
        errorMessage.textContent = `مسار: حدث خطأ: ${error.message}. حاول مرة أخرى لاحقًا.`;
        chatMessages.appendChild(errorMessage);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });

    // تفريغ الحقل
    document.getElementById('userInput').value = '';
}

// دعم الإرسال بزر Enter
document.getElementById('userInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
