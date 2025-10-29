"""
Einfacher Immich Kiosk Loader für Fully Kiosk Browser und Fire TV
Lädt kiosk.fkainka.de auf allen Geräten
"""

import requests
import yaml
import logging
import time
from pathlib import Path
from typing import List, Dict
from urllib.parse import urlencode, quote

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ImmichKioskLoader:
    """Lädt Immich Kiosk auf allen Geräten"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Args:
            config_path: Pfad zur config.yaml
        """
        self.config_path = Path(config_path).resolve()
        
        # Lade Konfiguration
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        logger.info(f"Konfiguration geladen: {self.config_path}")
    
    def _build_immich_url(self) -> str:
        """
        Erstellt Immich Kiosk URL mit optionalen Parametern
        
        Returns:
            Vollständige URL
        """
        base_url = self.config['immich_kiosk']['base_url']
        params = self.config['immich_kiosk'].get('params', {})
        
        if params:
            # Filtere None/leere Werte
            clean_params = {k: v for k, v in params.items() if v is not None}
            if clean_params:
                query_string = urlencode(clean_params)
                return f"{base_url}?{query_string}"
        
        return base_url
    
    def _load_url_on_tablet(self, device: Dict) -> bool:
        """
        Lädt URL auf einem Fully Kiosk Tablet
        
        Args:
            device: Device Config mit name, ip, password
            
        Returns:
            True wenn erfolgreich
        """
        name = device['name']
        ip = device['ip']
        password = device['password']
        
        immich_url = self._build_immich_url()
        
        # Fully Kiosk REST API
        fully_command = f"http://{ip}:2323/?cmd=loadURL&url={requests.utils.quote(immich_url)}&password={password}"
        
        try:
            logger.info(f"📱 {name} ({ip})")
            logger.info(f"   → {immich_url}")
            
            response = requests.get(fully_command, timeout=5)
            
            if response.status_code == 200:
                logger.info(f"   ✓ Geladen")
                return True
            else:
                logger.error(f"   ✗ HTTP {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"   ✗ Fehler: {e}")
            return False
    
    def _load_url_on_fire_tv(self, device: Dict) -> bool:
        """
        Lädt URL auf Fire TV via ADB und aktiviert Fullscreen
        
        Args:
            device: Device Config mit entity_id, name
            
        Returns:
            True wenn erfolgreich
        """
        entity_id = device['entity_id']
        name = device['name']
        
        immich_url = self._build_immich_url()
        
        # Home Assistant API
        ha_url = self.config['home_assistant']['url']
        ha_token = self.config['home_assistant']['token']
        
        headers = {
            'Authorization': f'Bearer {ha_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            logger.info(f"📺 {name} ({entity_id})")
            logger.info(f"   → {immich_url}")
            
            # 1. Öffne URL in Silk Browser
            adb_command = f'am start -a android.intent.action.VIEW -d "{immich_url}"'
            payload = {
                'entity_id': entity_id,
                'command': adb_command
            }
            
            response = requests.post(
                f"{ha_url}/api/services/androidtv/adb_command",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"   ✗ HTTP {response.status_code}: {response.text}")
                return False
            
            logger.info(f"   ✓ URL geladen, aktiviere Fullscreen...")
            
            # 2. Warte kurz, dann drücke 2x Menu-Taste (Keycode 82)
            time.sleep(3)
            
            # KEYCODE_MENU = 82 (2x drücken für Fullscreen)
            menu_command = 'input keyevent 82'
            payload = {
                'entity_id': entity_id,
                'command': menu_command
            }
            
            # Erste Menu-Taste
            response = requests.post(
                f"{ha_url}/api/services/androidtv/adb_command",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"   ✗ Fehler bei erster Menu-Taste: {response.status_code}")
                return False
            
            logger.info(f"   ✓ Menu-Taste 1/2 gedrückt")
            time.sleep(0.5)
            
            # Zweite Menu-Taste
            response = requests.post(
                f"{ha_url}/api/services/androidtv/adb_command",
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"   ✓ Menu-Taste 2/2 gedrückt (Fullscreen aktiviert)")
                return True
            else:
                logger.warning(f"   ⚠ Fullscreen konnte nicht aktiviert werden")
                return True  # URL wurde trotzdem geladen
                
        except requests.exceptions.RequestException as e:
            logger.error(f"   ✗ Fehler: {e}")
            return False
    
    def load_all_devices(self) -> Dict[str, int]:
        """
        Lädt Immich Kiosk auf allen konfigurierten Geräten
        
        Returns:
            Dict mit Erfolgsstatistiken
        """
        fire_tvs = self.config.get('fire_tv_devices', [])
        tablets = self.config.get('fully_kiosk_devices', [])
        
        total = len(fire_tvs) + len(tablets)
        
        if total == 0:
            logger.warning("Keine Geräte konfiguriert!")
            return {'fire_tv': 0, 'tablets': 0}
        
        logger.info(f"=== Lade Immich Kiosk auf {total} Gerät(en) ===\n")
        
        # Fire TV
        fire_tv_success = 0
        if fire_tvs:
            logger.info("--- Fire TV Geräte ---")
            for device in fire_tvs:
                if self._load_url_on_fire_tv(device):
                    fire_tv_success += 1
                print()
        
        # Fully Kiosk Tablets
        tablet_success = 0
        if tablets:
            logger.info("--- Fully Kiosk Tablets ---")
            for device in tablets:
                if self._load_url_on_tablet(device):
                    tablet_success += 1
                print()
        
        logger.info(f"=== Fertig ===")
        logger.info(f"Fire TV: {fire_tv_success}/{len(fire_tvs)} erfolgreich")
        logger.info(f"Tablets: {tablet_success}/{len(tablets)} erfolgreich")
        
        return {'fire_tv': fire_tv_success, 'tablets': tablet_success}
    
    def load_all_tablets(self) -> int:
        """
        Lädt Immich Kiosk auf allen konfigurierten Tablets
        
        Returns:
            Anzahl erfolgreich geladener Tablets
        """
        devices = self.config.get('fully_kiosk_devices', [])
        
        if not devices:
            logger.warning("Keine Fully Kiosk Geräte konfiguriert!")
            return 0
        
        logger.info(f"=== Lade Immich Kiosk auf {len(devices)} Tablet(s) ===\n")
        
        success_count = 0
        for device in devices:
            if self._load_url_on_tablet(device):
                success_count += 1
            print()  # Leerzeile
        
        logger.info(f"=== Fertig: {success_count}/{len(devices)} erfolgreich ===")
        return success_count


def main():
    """Main Entry Point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Immich Kiosk Loader für Fully Kiosk Browser und Fire TV")
    parser.add_argument('--config', default='config.yaml', help='Pfad zur config.yaml')
    args = parser.parse_args()
    
    loader = ImmichKioskLoader(config_path=args.config)
    loader.load_all_devices()


if __name__ == "__main__":
    main()
