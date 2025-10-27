"""
Automatisierte Telegram Bot Tests mit Playwright
Testet den Halloween Bot über die Telegram Web-App

WICHTIG: Telegram hat starke Anti-Bot-Mechanismen!
Diese Tests dienen als Vorlage - manuelle Anpassungen erforderlich.
"""

import asyncio
import os
import time
from pathlib import Path
from playwright.async_api import async_playwright, expect
import pytest
from datetime import datetime

# Test-Konfiguration
class TestConfig:
    TELEGRAM_WEB_URL = "https://web.telegram.org/k/"
    BOT_USERNAME = "your_halloween_bot"  # ANPASSEN!
    HEADLESS = False  # Auf True für CI/CD
    SCREENSHOT_DIR = Path("screenshots")
    TIMEOUT = 30000  # 30 Sekunden
    
    # Test-Team-IDs (Matrix)
    MATRIX_TRINITY_ID = "246935"
    MATRIX_NEO_ID = "233579" 
    MATRIX_TEAM_ID = "480514"


class TelegramBotTest:
    """Basis-Klasse für Telegram Bot Tests"""
    
    def __init__(self):
        self.config = TestConfig()
        self.page = None
        self.browser = None
        self.context = None
        
    async def setup(self):
        """Browser und Telegram Web-App öffnen"""
        playwright = await async_playwright().start()
        
        # Browser starten
        self.browser = await playwright.chromium.launch(
            headless=self.config.HEADLESS,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        # Context mit Desktop User-Agent
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        self.page = await self.context.new_page()
        
        # Screenshots-Ordner erstellen
        self.config.SCREENSHOT_DIR.mkdir(exist_ok=True)
        
        # Telegram Web öffnen
        print(f"🔗 Öffne Telegram Web: {self.config.TELEGRAM_WEB_URL}")
        await self.page.goto(self.config.TELEGRAM_WEB_URL)
        
    async def teardown(self):
        """Browser schließen"""
        if self.browser:
            await self.browser.close()
            
    async def take_screenshot(self, name: str):
        """Screenshot mit Timestamp erstellen"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.config.SCREENSHOT_DIR / f"{name}_{timestamp}.png"
        await self.page.screenshot(path=filename)
        print(f"📸 Screenshot: {filename}")
        
    async def wait_for_login(self):
        """Warten bis User eingeloggt ist"""
        print("⏳ Warte auf Telegram Login...")
        print("   👤 Bitte manuell in Telegram einloggen!")
        
        # Warte auf Chat-Liste oder ähnliches Element
        try:
            await self.page.wait_for_selector(
                '[data-testid="chat-list"], .chat-list, .sidebar-left', 
                timeout=60000  # 1 Minute
            )
            print("✅ Login erfolgreich!")
            return True
        except:
            print("❌ Login-Timeout! Versuche es manuell.")
            await self.take_screenshot("login_failed")
            return False
            
    async def find_bot(self):
        """Bot im Chat finden oder neue Unterhaltung starten"""
        print(f"🔍 Suche Bot: @{self.config.BOT_USERNAME}")
        
        # Suchfeld finden und Bot suchen
        search_selectors = [
            'input[placeholder*="Search"], input[placeholder*="search"]',
            '.input-search input',
            '#telegram-search-input'
        ]
        
        for selector in search_selectors:
            try:
                search_input = await self.page.wait_for_selector(selector, timeout=5000)
                await search_input.fill(f"@{self.config.BOT_USERNAME}")
                await self.page.keyboard.press('Enter')
                break
            except:
                continue
        else:
            print("⚠️ Suchfeld nicht gefunden - versuche direkte Navigation")
            # Fallback: Direkte URL
            bot_url = f"{self.config.TELEGRAM_WEB_URL}#@{self.config.BOT_USERNAME}"
            await self.page.goto(bot_url)
            
        await asyncio.sleep(2)
        await self.take_screenshot("bot_search")
        
    async def send_message(self, message: str):
        """Nachricht an Bot senden"""
        print(f"💬 Sende: {message}")
        
        # Message-Input finden
        input_selectors = [
            '[contenteditable="true"][data-testid="message-input"]',
            '.input-message-input',
            'div[contenteditable="true"]'
        ]
        
        for selector in input_selectors:
            try:
                message_input = await self.page.wait_for_selector(selector, timeout=5000)
                await message_input.click()
                await message_input.fill(message)
                await self.page.keyboard.press('Enter')
                print(f"✅ Nachricht gesendet: {message}")
                await asyncio.sleep(1)  # Rate limiting
                return True
            except Exception as e:
                continue
                
        print(f"❌ Konnte Nachricht nicht senden: {message}")
        await self.take_screenshot("send_failed")
        return False
        
    async def wait_for_bot_response(self, timeout: int = 10):
        """Warten auf Bot-Antwort"""
        print("⏳ Warte auf Bot-Antwort...")
        
        # Warte kurz und mache Screenshot
        await asyncio.sleep(2)
        await self.take_screenshot("bot_response")
        
        # Versuche Bot-Nachricht zu finden
        message_selectors = [
            '.message-content',
            '.bubble-content', 
            '[data-testid="message-text"]'
        ]
        
        try:
            for selector in message_selectors:
                messages = await self.page.query_selector_all(selector)
                if messages:
                    last_message = messages[-1]
                    text = await last_message.inner_text()
                    print(f"🤖 Bot antwortete: {text[:100]}...")
                    return text
        except Exception as e:
            print(f"⚠️ Fehler beim Lesen der Bot-Antwort: {e}")
            
        return None
        
    async def upload_photo(self, photo_path: str, caption: str = ""):
        """Foto mit Caption hochladen"""
        print(f"📷 Lade Foto hoch: {photo_path}")
        
        if caption:
            print(f"📝 Mit Caption: {caption}")
            
        # File-Upload Button finden
        upload_selectors = [
            'input[type="file"]',
            '[data-testid="file-upload"]',
            '.attach-file input'
        ]
        
        for selector in upload_selectors:
            try:
                file_input = await self.page.wait_for_selector(selector, timeout=5000)
                await file_input.set_input_files(photo_path)
                
                # Caption hinzufügen falls vorhanden
                if caption:
                    caption_selectors = [
                        '.input-message-input',
                        '[placeholder*="caption"], [placeholder*="Caption"]'
                    ]
                    
                    for cap_selector in caption_selectors:
                        try:
                            caption_input = await self.page.wait_for_selector(cap_selector, timeout=3000)
                            await caption_input.fill(caption)
                            break
                        except:
                            continue
                
                # Senden
                await self.page.keyboard.press('Enter')
                print("✅ Foto gesendet!")
                await asyncio.sleep(2)
                return True
                
            except Exception as e:
                continue
                
        print("❌ Foto-Upload fehlgeschlagen!")
        await self.take_screenshot("upload_failed")
        return False


# Test-Cases
class HalloweenBotTests(TelegramBotTest):
    """Spezifische Tests für den Halloween Bot"""
    
    async def test_complete_flow(self):
        """Vollständiger Test-Durchlauf"""
        print("\n🎃 Halloween Bot - Vollständiger Test")
        print("=" * 50)
        
        try:
            # Setup
            await self.setup()
            
            # Login warten
            if not await self.wait_for_login():
                return False
                
            # Bot finden
            await self.find_bot()
            
            # Test 1: /start
            print("\n📍 Test 1: /start Command")
            await self.send_message("/start")
            response = await self.wait_for_bot_response()
            
            if response and "2097" in response:
                print("✅ /start erfolgreich - Story erkannt")
            else:
                print("❌ /start fehlgeschlagen")
                
            # Test 2: /help  
            print("\n📍 Test 2: /help Command")
            await self.send_message("/help")
            response = await self.wait_for_bot_response()
            
            if response and "Punkte" in response:
                print("✅ /help erfolgreich - Spielregeln erkannt")
            else:
                print("❌ /help fehlgeschlagen")
                
            # Test 3: /punkte (leer)
            print("\n📍 Test 3: /punkte Command (leer)")
            await self.send_message("/punkte")
            response = await self.wait_for_bot_response()
            
            if response and "0" in response:
                print("✅ /punkte erfolgreich - 0 Punkte erkannt")
            else:
                print("❌ /punkte fehlgeschlagen")
                
            # Test 4: Team-Beitritt
            print("\n📍 Test 4: Team-Beitritt Matrix")
            team_command = f"/teamid {self.config.MATRIX_TEAM_ID}"
            await self.send_message(team_command)
            response = await self.wait_for_bot_response()
            
            if response and "Matrix" in response and "25" in response:
                print("✅ Team-Beitritt erfolgreich")
            else:
                print("❌ Team-Beitritt fehlgeschlagen")
                
            # Test 5: /punkte (mit Punkten)
            print("\n📍 Test 5: /punkte Command (mit Team)")
            await self.send_message("/punkte")
            response = await self.wait_for_bot_response()
            
            if response and "25" in response:
                print("✅ Punkte-Update erfolgreich")
            else:
                print("❌ Punkte-Update fehlgeschlagen")
                
            print("\n🎉 Test-Durchlauf abgeschlossen!")
            await self.take_screenshot("test_completed")
            
        except Exception as e:
            print(f"❌ Test-Fehler: {e}")
            await self.take_screenshot("test_error")
            
        finally:
            await self.teardown()
            

# Ausführung
async def main():
    """Hauptfunktion für Test-Ausführung"""
    tester = HalloweenBotTests()
    await tester.test_complete_flow()


if __name__ == "__main__":
    print("🚀 Starte Telegram Bot Tests...")
    print("\n⚠️  WICHTIG:")
    print("1. Bot-Username in TestConfig anpassen!")
    print("2. Telegram Web-App manuell einloggen wenn gefragt")
    print("3. Tests können durch Anti-Bot-Mechanismen fehlschlagen")
    print("4. Für echte Tests: Manueller Test-Plan verwenden!\n")
    
    # Bot-Username prüfen
    if TestConfig.BOT_USERNAME == "your_halloween_bot":
        print("❌ STOPP: Bot-Username noch nicht konfiguriert!")
        print("   Ändere 'BOT_USERNAME' in TestConfig!")
        exit(1)
        
    asyncio.run(main())