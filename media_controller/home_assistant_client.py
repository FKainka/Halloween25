"""
Home Assistant API Client für Fire TV und Fully Kiosk Browser Steuerung
"""
import requests
import logging
from typing import Dict, List, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)


class HomeAssistantClient:
    """Client für die Kommunikation mit Home Assistant API"""
    
    def __init__(self, url: str, token: str):
        """
        Initialisiert den Home Assistant Client
        
        Args:
            url: Home Assistant URL (z.B. http://homeassistant.local:8123)
            token: Long-lived Access Token aus Home Assistant
        """
        self.url = url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }
        logger.info(f"Home Assistant Client initialisiert: {self.url}")
    
    def test_connection(self) -> bool:
        """
        Testet die Verbindung zu Home Assistant
        
        Returns:
            True wenn Verbindung erfolgreich, sonst False
        """
        try:
            response = requests.get(
                f"{self.url}/api/",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            logger.info("✓ Home Assistant Verbindung erfolgreich")
            return True
        except Exception as e:
            logger.error(f"✗ Home Assistant Verbindung fehlgeschlagen: {e}")
            return False
    
    def get_state(self, entity_id: str) -> Optional[Dict]:
        """
        Holt den aktuellen Status eines Entity
        
        Args:
            entity_id: Die Entity ID (z.B. media_player.fire_tv_wohnzimmer)
            
        Returns:
            Dictionary mit Status-Informationen oder None bei Fehler
        """
        try:
            response = requests.get(
                f"{self.url}/api/states/{entity_id}",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Fehler beim Abrufen von {entity_id}: {e}")
            return None
    
    def play_media_on_fire_tv(self, entity_id: str, media_url: str, fire_tv_ip: Optional[str] = None) -> bool:
        """
        Spielt ein Video auf einem Fire TV ab über ADB
        
        Args:
            entity_id: Fire TV Entity ID
            media_url: YouTube URL
            fire_tv_ip: (Optional, nicht mehr benötigt für ADB)
            
        Returns:
            True wenn erfolgreich, sonst False
        """
        try:
            # Video-ID extrahieren
            video_id = self._extract_youtube_video_id(media_url)
            if not video_id:
                logger.error(f"✗ Konnte Video-ID nicht extrahieren aus: {media_url}")
                return False
            
            # ADB Command über Home Assistant
            adb_command = f"am start -a android.intent.action.VIEW -d vnd.youtube:{video_id}"
            
            logger.info(f"▶ Spiele Video über ADB ab: {video_id}")
            logger.debug(f"   ADB Command: {adb_command}")
            
            data = {
                'entity_id': entity_id,
                'command': adb_command
            }
            
            response = requests.post(
                f"{self.url}/api/services/androidtv/adb_command",
                headers=self.headers,
                json=data,
                timeout=15
            )
            
            if response.status_code == 200:
                logger.info(f"✓ Fire TV {entity_id}: Video wird abgespielt")
                return True
            else:
                logger.error(f"✗ ADB Command fehlgeschlagen: {response.status_code} - {response.text}")
                return False
            
        except Exception as e:
            logger.error(f"✗ Fehler beim Abspielen auf {entity_id}: {e}")
            return False
    
    def _start_kodi_app(self, entity_id: str) -> bool:
        """
        Startet Kodi App auf Fire TV
        
        Args:
            entity_id: Fire TV Entity ID
            
        Returns:
            True wenn erfolgreich
        """
        try:
            data = {
                'entity_id': entity_id,
                'source': 'org.xbmc.kodi'
            }
            
            response = requests.post(
                f"{self.url}/api/services/media_player/select_source",
                headers=self.headers,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            logger.debug(f"✓ Kodi gestartet auf {entity_id}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Fehler beim Starten von Kodi: {e}")
            return False
    
    def _play_youtube_via_kodi(self, fire_tv_ip: str, youtube_url: str, kodi_username: str = "kodi", kodi_password: str = "") -> bool:
        """
        Spielt YouTube Video über Kodi JSON-RPC ab
        
        Args:
            fire_tv_ip: IP-Adresse des Fire TV
            youtube_url: YouTube URL
            kodi_username: Kodi Username (falls Auth aktiviert)
            kodi_password: Kodi Passwort (falls Auth aktiviert)
            
        Returns:
            True wenn erfolgreich
        """
        try:
            # Video-ID extrahieren
            video_id = self._extract_youtube_video_id(youtube_url)
            if not video_id:
                logger.error(f"✗ Konnte Video-ID nicht extrahieren aus: {youtube_url}")
                return False
            
            # Kodi JSON-RPC URL
            kodi_url = f"http://{fire_tv_ip}:8080/jsonrpc"
            
            # YouTube Plugin URL
            plugin_url = f"plugin://plugin.video.youtube/play/?video_id={video_id}"
            
            payload = {
                "jsonrpc": "2.0",
                "method": "Player.Open",
                "params": {
                    "item": {"file": plugin_url}
                },
                "id": 1
            }
            
            # Auth wenn Username/Passwort vorhanden
            auth = None
            if kodi_username:
                auth = (kodi_username, kodi_password)
            
            response = requests.post(kodi_url, json=payload, auth=auth, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    logger.info(f"✓ Video wird über Kodi abgespielt: {video_id}")
                    return True
                else:
                    logger.error(f"✗ Kodi Playback fehlgeschlagen: {result}")
                    return False
            else:
                logger.error(f"✗ Kodi JSON-RPC Error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Fehler bei Kodi Playback: {e}")
            return False
    
    def _extract_youtube_video_id(self, youtube_url: str) -> Optional[str]:
        """
        Extrahiert Video-ID aus YouTube URL
        
        Args:
            youtube_url: YouTube URL
            
        Returns:
            Video-ID oder None
        """
        import re
        
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\?\/]+)',
            r'youtube\.com\/watch\?.*v=([^&]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, youtube_url)
            if match:
                return match.group(1)
        
        return None
    
    def control_fire_tv(self, entity_id: str, command: str) -> bool:
        """
        Sendet Steuerungsbefehle an Fire TV (play, pause, stop)
        
        Args:
            entity_id: Fire TV Entity ID
            command: Befehl (play, pause, stop)
            
        Returns:
            True wenn erfolgreich
        """
        try:
            service_map = {
                'play': 'media_play',
                'pause': 'media_pause',
                'stop': 'media_stop'
            }
            
            service = service_map.get(command, 'media_play')
            
            response = requests.post(
                f"{self.url}/api/services/media_player/{service}",
                headers=self.headers,
                json={'entity_id': entity_id},
                timeout=10
            )
            response.raise_for_status()
            logger.debug(f"Fire TV {entity_id}: {command}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler bei Fire TV Steuerung {entity_id} ({command}): {e}")
            return False
    
    def load_url_on_fully_kiosk(self, device: Dict, url: str) -> bool:
        """
        Lädt eine URL auf einem Fully Kiosk Browser mit Vollbild-Unterstützung
        
        Args:
            device: Device Dictionary mit 'url_command' und 'name'
            url: URL die geladen werden soll
            
        Returns:
            True wenn erfolgreich
        """
        try:
            # Konvertiere YouTube URLs zu Embed-Format für Vollbild
            video_url = self._convert_to_fullscreen_url(url)
            
            logger.debug(f"Original URL: {url}")
            logger.debug(f"Vollbild URL: {video_url}")
            
            # Fully Kiosk REST API verwenden
            url_command = device['url_command'].format(url=quote(video_url))
            
            response = requests.get(url_command, timeout=10)
            response.raise_for_status()
            
            logger.info(f"✓ Fully Kiosk {device['name']}: URL geladen (Vollbild)")
            return True
            
        except Exception as e:
            logger.error(f"✗ Fehler bei Fully Kiosk {device['name']}: {e}")
            return False
    
    def _convert_to_fullscreen_url(self, url: str) -> str:
        """
        Konvertiert YouTube URLs zu Vollbild-Embed-Format
        
        Args:
            url: Original YouTube URL
            
        Returns:
            Embed URL mit Autoplay-Parameter
        """
        # Extrahiere Video-ID
        video_id = self._extract_youtube_video_id(url)
        
        if video_id:
            # YouTube Embed URL mit autoplay Parameter
            # autoplay=1: Video startet automatisch (funktioniert mit "Run embedded videos on start")
            embed_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1"
            
            logger.debug(f"Konvertiert zu Embed mit Autoplay: {video_id}")
            return embed_url
        else:
            # Keine YouTube URL, gib Original zurück
            return url
    
    def load_url_on_fully_via_ha(self, entity_id: str, url: str) -> bool:
        """
        Alternative: Lädt URL über Home Assistant Fully Kiosk Integration
        
        Args:
            entity_id: Fully Kiosk Entity ID in Home Assistant
            url: URL die geladen werden soll
            
        Returns:
            True wenn erfolgreich
        """
        try:
            data = {
                'entity_id': entity_id,
                'url': url
            }
            
            response = requests.post(
                f"{self.url}/api/services/fully_kiosk/load_url",
                headers=self.headers,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"✓ Fully Kiosk {entity_id}: URL über HA geladen")
            return True
            
        except Exception as e:
            logger.error(f"✗ Fehler bei Fully Kiosk HA Integration {entity_id}: {e}")
            return False
    
    def get_all_media_players(self) -> List[Dict]:
        """
        Holt alle verfügbaren Media Player Entities
        
        Returns:
            Liste von Media Player Dictionaries
        """
        try:
            response = requests.get(
                f"{self.url}/api/states",
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            all_states = response.json()
            media_players = [
                state for state in all_states 
                if state['entity_id'].startswith('media_player.')
            ]
            
            logger.info(f"Gefundene Media Players: {len(media_players)}")
            return media_players
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Media Players: {e}")
            return []
    
    def call_service(self, domain: str, service: str, data: Dict) -> bool:
        """
        Generischer Service-Aufruf für Home Assistant
        
        Args:
            domain: Service Domain (z.B. 'media_player')
            service: Service Name (z.B. 'play_media')
            data: Service Daten
            
        Returns:
            True wenn erfolgreich
        """
        try:
            response = requests.post(
                f"{self.url}/api/services/{domain}/{service}",
                headers=self.headers,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Service-Aufruf fehlgeschlagen {domain}.{service}: {e}")
            return False
