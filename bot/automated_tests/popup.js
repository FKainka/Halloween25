// Popup-Script für Browser Extension
document.addEventListener('DOMContentLoaded', function() {
    const status = document.getElementById('status');
    
    // Event Listeners
    document.getElementById('openTelegram').addEventListener('click', () => {
        chrome.tabs.create({ url: 'https://web.telegram.org/k/' });
        updateStatus('Telegram Web geöffnet');
    });
    
    document.getElementById('runAutoTest').addEventListener('click', () => {
        executeInActiveTab('startAutoTest');
        updateStatus('Auto-Test gestartet...');
    });
    
    document.getElementById('sendStart').addEventListener('click', () => {
        executeInActiveTab('sendCommand', ['/start']);
        updateStatus('/start gesendet');
    });
    
    document.getElementById('sendHelp').addEventListener('click', () => {
        executeInActiveTab('sendCommand', ['/help']);
        updateStatus('/help gesendet');
    });
    
    document.getElementById('sendPunkte').addEventListener('click', () => {
        executeInActiveTab('sendCommand', ['/punkte']);
        updateStatus('/punkte gesendet');
    });
    
    document.getElementById('joinTeam').addEventListener('click', () => {
        executeInActiveTab('sendCommand', ['/teamid 480514']);
        updateStatus('Team Matrix Beitritt gesendet');
    });
    
    function updateStatus(message) {
        status.textContent = message;
        console.log('[Bot Tester]', message);
    }
    
    function executeInActiveTab(functionName, args = []) {
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            if (tabs[0].url.includes('web.telegram.org')) {
                chrome.scripting.executeScript({
                    target: { tabId: tabs[0].id },
                    func: executeFunction,
                    args: [functionName, args]
                });
            } else {
                updateStatus('❌ Nicht auf Telegram Web!');
            }
        });
    }
    
    function executeFunction(functionName, args) {
        // Diese Funktion läuft im Content-Script-Context
        if (window.TelegramBotTestHelper) {
            const instance = new window.TelegramBotTestHelper();
            if (typeof instance[functionName] === 'function') {
                instance[functionName](...args);
            }
        } else {
            console.log('TelegramBotTestHelper nicht gefunden');
        }
    }
});