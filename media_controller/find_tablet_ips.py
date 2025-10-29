"""
IP-Finder für Fully Kiosk / Fire Tablet Geräte
Findet IPs über Home Assistant Sensoren
"""

import requests
import yaml
from pathlib import Path

# Lade Config
config_path = Path("config.yaml").resolve()
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

ha_url = config['home_assistant']['url']
ha_token = config['home_assistant']['token']

headers = {
    'Authorization': f'Bearer {ha_token}',
    'Content-Type': 'application/json'
}

print("=" * 70)
print("🔍 IP-FINDER für Fire Tablets / Fully Kiosk")
print("=" * 70)
print()

# Hole alle States
print("📡 Lade Geräte-Informationen...")
response = requests.get(f"{ha_url}/api/states", headers=headers, timeout=10)

if response.status_code != 200:
    print(f"✗ Fehler: {response.status_code}")
    exit(1)

states = response.json()

# Suche nach Fire Tablet IP-Informationen
tablet_names = ['fire_tablet_4', 'fire_tablet', 'fire_tablet_3']
tablet_info = {}

for tablet_name in tablet_names:
    print(f"\n--- {tablet_name} ---")
    
    # Suche alle Sensoren für dieses Tablet
    for state in states:
        entity_id = state['entity_id']
        
        if tablet_name in entity_id:
            # Zeige relevante Infos
            if 'ip' in entity_id or 'address' in entity_id:
                print(f"📍 {entity_id}: {state['state']}")
                
                if tablet_name not in tablet_info:
                    tablet_info[tablet_name] = {}
                tablet_info[tablet_name]['ip'] = state['state']
            
            elif 'battery' in entity_id:
                print(f"🔋 {entity_id}: {state['state']}%")
            
            elif 'screen' in entity_id or 'display' in entity_id:
                print(f"📺 {entity_id}: {state['state']}")

print()
print("=" * 70)
print("📋 ZUSAMMENFASSUNG")
print("=" * 70)
print()

for tablet_name, info in tablet_info.items():
    friendly_name = {
        'fire_tablet_4': 'Dashboard Schlafzimmer',
        'fire_tablet': 'Dashboard Dachboden',
        'fire_tablet_3': 'Dashboard Esszimmer'
    }.get(tablet_name, tablet_name)
    
    print(f"{friendly_name}:")
    print(f"  IP: {info.get('ip', 'NICHT GEFUNDEN')}")

if not tablet_info:
    print("⚠ Keine IP-Adressen automatisch gefunden")
    print()
    print("💡 Manuell herausfinden:")
    print("   1. Öffne Fully Kiosk App auf dem Tablet")
    print("   2. Gehe zu Settings → Advanced Web Settings")
    print("   3. Notiere die IP-Adresse bei 'Remote Admin (IP)'")
    print()
    print("   Oder suche in Home Assistant Developer Tools → States")
    print("   nach 'fire_tablet' und 'ip'")
