"""
Auto-Discovery für Fire TV und Fully Kiosk Geräte aus Home Assistant
Aktualisiert automatisch die config.yaml
"""

import requests
import yaml
from pathlib import Path
from typing import List, Dict

# Lade aktuelle Config
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
print("🔍 AUTO-DISCOVERY: Fire TV & Fully Kiosk Geräte")
print("=" * 70)
print()

# Hole alle States von Home Assistant
print("📡 Lade alle Geräte von Home Assistant...")
response = requests.get(f"{ha_url}/api/states", headers=headers, timeout=10)

if response.status_code != 200:
    print(f"✗ Fehler: {response.status_code}")
    exit(1)

states = response.json()
print(f"✓ {len(states)} Entities gefunden\n")

# Finde Fire TV Geräte (androidtv integration)
print("--- Fire TV Geräte ---")
fire_tv_devices = []

for state in states:
    entity_id = state['entity_id']
    
    # Fire TV Geräte haben meist "fire_tv" im Namen oder sind von androidtv integration
    if entity_id.startswith('media_player.') and 'fire_tv' in entity_id.lower():
        name = state['attributes'].get('friendly_name', entity_id.replace('media_player.', '').replace('_', ' ').title())
        
        fire_tv_devices.append({
            'entity_id': entity_id,
            'name': name
        })
        print(f"✓ {name}")
        print(f"  Entity: {entity_id}")

if not fire_tv_devices:
    print("⚠ Keine Fire TV Geräte gefunden")
    print("  Tipp: Suche nach media_player Entities mit 'fire_tv' im Namen")

print()

# Finde Fully Kiosk Geräte
print("--- Fully Kiosk Browser Geräte ---")
fully_devices = []

for state in states:
    entity_id = state['entity_id']
    
    # Fully Kiosk Geräte haben meist "fully" im Namen oder sind sensor/binary_sensor
    if 'fully' in entity_id.lower():
        # Versuche IP und andere Infos zu finden
        attributes = state['attributes']
        
        # Wenn es ein media_player ist, nehmen wir den
        if entity_id.startswith('media_player.'):
            name = attributes.get('friendly_name', entity_id.replace('media_player.', '').replace('_', ' ').title())
            
            # Versuche IP zu finden (oft in anderen Sensoren)
            ip = None
            for s in states:
                if entity_id.replace('media_player.', '') in s['entity_id'] and 'ip' in s['entity_id']:
                    ip = s['state']
                    break
            
            if not ip:
                ip = "UNKNOWN"  # Muss manuell eingetragen werden
            
            fully_devices.append({
                'name': name,
                'ip': ip,
                'password': 'duckya'  # Standard-Passwort
            })
            print(f"✓ {name}")
            print(f"  IP: {ip} (bitte manuell prüfen)")

# Falls keine Fully Kiosk gefunden, suche generischer
if not fully_devices:
    print("⚠ Keine Fully Kiosk Geräte automatisch gefunden")
    print("  Tipp: Suche in Home Assistant nach 'fully' oder 'tablet'")
    print()
    
    # Zeige alle media_player Entities
    print("📱 Verfügbare media_player Entities:")
    for state in states:
        if state['entity_id'].startswith('media_player.'):
            name = state['attributes'].get('friendly_name', state['entity_id'])
            print(f"  - {state['entity_id']}: {name}")

print()
print("=" * 70)

# Frage ob Config aktualisiert werden soll
print()
print(f"Gefundene Geräte:")
print(f"  Fire TV: {len(fire_tv_devices)}")
print(f"  Fully Kiosk: {len(fully_devices)}")
print()

if fire_tv_devices or fully_devices:
    answer = input("Config.yaml aktualisieren? (j/n): ")
    
    if answer.lower() in ['j', 'y', 'ja', 'yes']:
        # Aktualisiere Config
        if fire_tv_devices:
            config['fire_tv_devices'] = fire_tv_devices
        
        if fully_devices:
            # Behalte alte Geräte falls IPs bekannt sind
            old_fully = {d['name']: d for d in config.get('fully_kiosk_devices', [])}
            
            for device in fully_devices:
                if device['name'] in old_fully and old_fully[device['name']]['ip'] != 'UNKNOWN':
                    device['ip'] = old_fully[device['name']]['ip']
                    device['password'] = old_fully[device['name']]['password']
            
            config['fully_kiosk_devices'] = fully_devices
        
        # Speichere Config
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        print(f"✓ Config aktualisiert: {config_path}")
        print()
        print("⚠ Bitte prüfe die IPs der Fully Kiosk Geräte manuell!")
    else:
        print("Abgebrochen")
else:
    print("Keine Geräte gefunden zum Aktualisieren")
