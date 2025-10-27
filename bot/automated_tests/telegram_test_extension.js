// Browser Extension für assistierte Telegram Bot Tests
// Für Chrome/Firefox - automatisiert wiederkehrende Test-Schritte

class TelegramBotTestHelper {
    constructor() {
        this.testQueue = [];
        this.currentTest = 0;
        this.results = [];
        
        // Test-Konfiguration
        this.config = {
            botUsername: 'your_halloween_bot', // ANPASSEN!
            testCommands: [
                '/start',
                '/help', 
                '/punkte',
                '/teamid 480514',
                '/punkte'
            ],
            testPhotoCaptions: [
                '', // Party-Foto ohne Caption
                'Film: Matrix',
                'Team: 480514'
            ]
        };
        
        this.init();
    }
    
    init() {
        console.log('🎃 Halloween Bot Test Helper geladen!');
        this.createTestUI();
        this.detectTelegram();
    }
    
    detectTelegram() {
        // Prüfe ob wir auf Telegram Web sind
        if (window.location.hostname.includes('web.telegram.org')) {
            console.log('✅ Telegram Web erkannt!');
            this.setupTelegramHelpers();
        } else {
            console.log('ℹ️ Nicht auf Telegram Web - Extension wartet...');
        }
    }
    
    createTestUI() {
        // Erstelle floating Test-Panel
        const panel = document.createElement('div');
        panel.id = 'telegram-bot-test-panel';
        panel.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            width: 300px;
            background: #2c3e50;
            color: white;
            border-radius: 10px;
            padding: 15px;
            z-index: 10000;
            font-family: Arial, sans-serif;
            font-size: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        `;
        
        panel.innerHTML = `
            <h3 style="margin: 0 0 10px 0;">🎃 Bot Test Helper</h3>
            <div id="test-status">Bereit für Tests</div>
            <hr style="margin: 10px 0;">
            
            <button id="start-auto-test" style="width: 100%; margin: 5px 0; padding: 8px;">
                🚀 Auto-Test starten
            </button>
            
            <button id="send-start" style="width: 100%; margin: 5px 0; padding: 8px;">
                📤 /start senden
            </button>
            
            <button id="send-help" style="width: 100%; margin: 5px 0; padding: 8px;">
                📤 /help senden
            </button>
            
            <button id="send-punkte" style="width: 100%; margin: 5px 0; padding: 8px;">
                📤 /punkte senden
            </button>
            
            <button id="join-matrix-team" style="width: 100%; margin: 5px 0; padding: 8px;">
                🎭 Team Matrix beitreten
            </button>
            
            <hr style="margin: 10px 0;">
            
            <div style="font-size: 10px; opacity: 0.8;">
                Test-Fortschritt: <span id="test-progress">0/5</span><br>
                Letzter Test: <span id="last-test">-</span>
            </div>
            
            <button id="toggle-panel" style="position: absolute; top: 5px; right: 5px; background: none; border: none; color: white;">
                ×
            </button>
        `;
        
        document.body.appendChild(panel);
        
        // Event Listeners
        document.getElementById('start-auto-test').onclick = () => this.startAutoTest();
        document.getElementById('send-start').onclick = () => this.sendCommand('/start');
        document.getElementById('send-help').onclick = () => this.sendCommand('/help');
        document.getElementById('send-punkte').onclick = () => this.sendCommand('/punkte');
        document.getElementById('join-matrix-team').onclick = () => this.sendCommand('/teamid 480514');
        document.getElementById('toggle-panel').onclick = () => this.togglePanel();
    }
    
    setupTelegramHelpers() {
        // Helper-Funktionen für Telegram Web
        this.findMessageInput = () => {
            const selectors = [
                '[contenteditable="true"][data-testid="message-input"]',
                '.input-message-input',
                'div[contenteditable="true"]',
                '.composer-input'
            ];
            
            for (const selector of selectors) {
                const element = document.querySelector(selector);
                if (element) return element;
            }
            return null;
        };
        
        this.findSendButton = () => {
            const selectors = [
                '[data-testid="send-button"]',
                '.btn-send',
                'button[title*="Send"], button[aria-label*="Send"]'
            ];
            
            for (const selector of selectors) {
                const element = document.querySelector(selector);
                if (element) return element;
            }
            return null;
        };
    }
    
    sendCommand(command) {
        const input = this.findMessageInput();
        if (!input) {
            this.updateStatus(`❌ Message-Input nicht gefunden`);
            return false;
        }
        
        // Text eingeben
        input.focus();
        input.textContent = command;
        
        // Input-Event triggern
        input.dispatchEvent(new Event('input', { bubbles: true }));
        
        // Enter drücken oder Send-Button klicken
        setTimeout(() => {
            const sendButton = this.findSendButton();
            if (sendButton) {
                sendButton.click();
            } else {
                // Fallback: Enter-Taste
                const enterEvent = new KeyboardEvent('keydown', {
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    bubbles: true
                });
                input.dispatchEvent(enterEvent);
            }
            
            this.updateStatus(`✅ Command gesendet: ${command}`);
            this.updateProgress();
            
        }, 100);
        
        return true;
    }
    
    startAutoTest() {
        this.updateStatus('🚀 Auto-Test startet...');
        this.currentTest = 0;
        
        // Test-Sequenz
        const tests = [
            { cmd: '/start', delay: 3000 },
            { cmd: '/help', delay: 2000 },
            { cmd: '/punkte', delay: 2000 },
            { cmd: '/teamid 480514', delay: 3000 },
            { cmd: '/punkte', delay: 2000 }
        ];
        
        this.runTestSequence(tests);
    }
    
    runTestSequence(tests) {
        if (this.currentTest >= tests.length) {
            this.updateStatus('🎉 Auto-Test abgeschlossen!');
            this.showResults();
            return;
        }
        
        const test = tests[this.currentTest];
        this.updateStatus(`📤 Test ${this.currentTest + 1}/${tests.length}: ${test.cmd}`);
        
        if (this.sendCommand(test.cmd)) {
            setTimeout(() => {
                this.currentTest++;
                this.runTestSequence(tests);
            }, test.delay);
        }
    }
    
    updateStatus(message) {
        const status = document.getElementById('test-status');
        if (status) {
            status.textContent = message;
            console.log(`[Bot Test Helper] ${message}`);
        }
    }
    
    updateProgress() {
        const progress = document.getElementById('test-progress');
        const lastTest = document.getElementById('last-test');
        
        if (progress) {
            progress.textContent = `${this.currentTest + 1}/5`;
        }
        
        if (lastTest) {
            lastTest.textContent = new Date().toLocaleTimeString();
        }
    }
    
    togglePanel() {
        const panel = document.getElementById('telegram-bot-test-panel');
        if (panel) {
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        }
    }
    
    showResults() {
        alert(`🎃 Halloween Bot Test abgeschlossen!\n\n` +
              `Tests ausgeführt: ${this.currentTest}\n` +
              `Zeit: ${new Date().toLocaleString()}\n\n` +
              `Prüfe die Chat-Responses manuell für Korrektheit.`);
    }
}

// Auto-Start wenn Seite geladen
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new TelegramBotTestHelper());
} else {
    new TelegramBotTestHelper();
}

// Global verfügbar machen für Konsole
window.TelegramBotTestHelper = TelegramBotTestHelper;