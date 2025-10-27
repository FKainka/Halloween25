.PHONY: help build up down restart logs shell clean backup

help: ## Zeigt diese Hilfe an
	@echo "Halloween Bot - Docker Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Bot-Image bauen
	docker-compose build

up: ## Bot starten
	docker-compose up -d
	@echo "Bot läuft! Logs anzeigen mit: make logs"

down: ## Bot stoppen
	docker-compose down

restart: ## Bot neu starten
	docker-compose restart
	@echo "Bot neu gestartet!"

rebuild: down build up ## Bot neu bauen und starten

logs: ## Live-Logs anzeigen (Ctrl+C zum Beenden)
	docker-compose logs -f

logs-tail: ## Letzte 50 Zeilen der Logs
	docker-compose logs --tail=50

shell: ## Shell im Container öffnen
	docker-compose exec halloween-bot bash

ps: ## Container-Status anzeigen
	docker-compose ps

stats: ## Resource-Nutzung anzeigen
	docker stats halloween-bot --no-stream

clean: ## Container und Volumes entfernen (ACHTUNG: Löscht Daten!)
	docker-compose down -v
	@echo "WARNUNG: Volumes wurden entfernt!"

backup: ## Datenbank-Backup erstellen
	@mkdir -p backups
	@cp bot.db backups/bot.db.backup-$$(date +%Y%m%d-%H%M%S)
	@echo "Backup erstellt in backups/"

dev: ## Development-Modus mit Live-Reload starten
	@echo "Starte im Development-Modus..."
	docker-compose -f docker-compose.yml up

setup: ## Initiales Setup (env kopieren)
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo ".env Datei erstellt - bitte anpassen!"; \
	else \
		echo ".env existiert bereits"; \
	fi
