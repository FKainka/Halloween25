"""
OpenAI Vision API Integration für Film-Referenz und Puzzle-Bewertung.
"""
import json
import logging
from typing import Dict, Optional, Tuple
from pathlib import Path
import base64

from openai import OpenAI
from openai import APIError, APITimeoutError, RateLimitError

from config import config


logger = logging.getLogger('bot.services.ai_evaluator')


class AIEvaluator:
    """
    Bewertet Film-Referenzen mit OpenAI Vision API.
    """
    
    def __init__(self):
        """Initialisiert OpenAI Client."""
        # Token-Tracking
        self.total_tokens_used = 0
        self.total_requests = 0
        self.total_cost_usd = 0.0
        
        if not config.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY nicht gesetzt - KI-Bewertung deaktiviert")
            self.client = None
        else:
            try:
                self.client = OpenAI(api_key=config.OPENAI_API_KEY)
                logger.info("AI Evaluator initialisiert")
            except Exception as e:
                logger.error(f"Fehler beim Initialisieren des OpenAI Clients: {e}")
                self.client = None
    
    def get_usage_stats(self) -> dict:
        """
        Gibt API-Nutzungsstatistiken zurück.
        
        Returns:
            dict: Statistiken über Token-Verbrauch und Kosten
        """
        return {
            'total_requests': self.total_requests,
            'total_tokens_used': self.total_tokens_used,
            'total_cost_usd': round(self.total_cost_usd, 4),
            'avg_tokens_per_request': round(self.total_tokens_used / max(self.total_requests, 1), 2)
        }
    
    def _encode_image(self, image_path: str) -> str:
        """
        Kodiert Bild zu Base64.
        
        Args:
            image_path: Pfad zum Bild
            
        Returns:
            Base64-kodiertes Bild
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _create_prompt(self, film_title: str, easter_egg_description: str = None) -> str:
        """
        Erstellt Prompt für Film-Bewertung.
        
        Args:
            film_title: Name des Films
            easter_egg_description: Beschreibung des Easter Eggs (optional)
            
        Returns:
            Formatierter Prompt
        """
        easter_egg_hint = ""
        if easter_egg_description:
            easter_egg_hint = f"\n\nBESONDERS WICHTIG: Für diesen Film gibt es ein spezifisches Easter Egg:\n{easter_egg_description}\n"
        
        prompt = f"""Du bist ein Experte für Sci-Fi-Filme und analysierst ein Foto von einer Halloween-Party.

Die Person behauptet, dass dieses Foto eine Referenz zum Film "{film_title}" zeigt.
{easter_egg_hint}
Prüfe das Foto auf:
1. **Easter Eggs** - Spezifische Gegenstände oder Symbole aus dem Film (siehe Beschreibung oben)
2. **Nachgestellte Szenen** - Person(en) stellen ikonische Filmszene nach
3. **Filmszene vom Bildschirm** - Foto eines laufenden Films/Szene auf TV/Monitor
4. **Film-Plakat** - Offizielles oder nachgebautes Filmplakat
5. **Kostüme/Charaktere** - Verkleidung als Film-Charakter
6. **Requisiten/Props** - Ikonische Gegenstände aus dem Film

WICHTIG: Es muss eine ERKENNBARE und EINDEUTIGE Referenz zum Film "{film_title}" sein!
Einfache Ähnlichkeiten oder vage Assoziationen zählen NICHT.

Antworte NUR mit einem JSON-Objekt in folgendem Format (keine zusätzlichen Texte):
{{
  "is_reference": true oder false,
  "confidence": 0-100 (Wie sicher bist du?),
  "reasoning": "Detaillierte Erklärung was du siehst und warum es eine Referenz ist/nicht ist",
  "detected_elements": ["Element 1", "Element 2", ...],
  "reference_type": "easter_egg" oder "scene" oder "screen_capture" oder "poster" oder "costume" oder "prop" oder "other"
}}

Beispiele für GUTE Referenzen:
- Matrix: Grüner Code, rote/blaue Pille, Agent Smith Sonnenbrille, "There is no spoon" Löffel
- Terminator: Rote LED-Augen, Metallskelett, "I'll be back" Schild, Totenkopf mit roten LEDs
- V wie Vendetta: Guy Fawkes Maske, Rose, "Remember Remember" Text

Beispiele für KEINE Referenzen:
- Nur schwarze Kleidung (zu allgemein)
- Generische Sci-Fi Props ohne Film-Bezug
- Normale Alltagsgegenstände
"""
        return prompt
    
    def _create_puzzle_prompt(self, film_title: str, poster_urls: list = None) -> str:
        """
        Erstellt Prompt für Puzzle-Poster-Bewertung.
        
        Args:
            film_title: Name des Films
            poster_urls: URLs zu offiziellen Postern (optional)
            
        Returns:
            Formatierter Prompt
        """
        poster_hint = ""
        if poster_urls:
            poster_hint = f"\n\nHinweis: Offizielle Poster findest du hier:\n" + "\n".join(f"- {url}" for url in poster_urls[:2])
        
        prompt = f"""Du analysierst ein Puzzle-Screenshot von einer Halloween-Party.

Die Person hat ein Puzzle gelöst und behauptet, es zeigt ein Filmplakat zu "{film_title}".
{poster_hint}

AUFGABE: Prüfe ob das Foto ein GELÖSTES PUZZLE zeigt, das ein FILMPLAKAT von "{film_title}" darstellt.

Wichtige Prüfpunkte:
1. Ist das Puzzle **vollständig gelöst** (keine fehlenden Teile)?
2. Zeigt es ein **Filmplakat** (keine Szene, kein Screenshot)?
3. Ist es eindeutig zum Film **"{film_title}"** (Titel, Logo, ikonische Charaktere)?

WICHTIG: 
- Puzzle muss GELÖST sein (alle Teile vorhanden)
- Es muss ein PLAKAT sein, keine Filmszene
- Film-Titel oder eindeutige visuelle Elemente müssen erkennbar sein

Antworte NUR mit einem JSON-Objekt:
{{
  "is_valid": true oder false,
  "confidence": 0-100,
  "reasoning": "Was siehst du? Ist es ein gelöstes Puzzle mit dem richtigen Filmplakat?",
  "detected_elements": ["Puzzle-Teile", "Film-Titel", "Charaktere", ...],
  "issues": ["Problem 1", "Problem 2", ...] (leer wenn alles ok)
}}

Beispiele für GÜLTIG:
- Vollständig gelöstes Puzzle mit Matrix-Plakat (Neo, grüner Code, Titel sichtbar)
- Gelöstes Puzzle mit Terminator-Plakat (T-800, roter Hintergrund, Titel)

Beispiele für UNGÜLTIG:
- Unvollständiges Puzzle (fehlende Teile)
- Foto einer Filmszene statt Plakat
- Falscher Film
- Kein Puzzle erkennbar
"""
        return prompt
    
    def evaluate_film_reference(
        self, 
        photo_path: str, 
        film_title: str,
        easter_egg_description: str = None
    ) -> Tuple[bool, int, str, Dict]:
        """
        Bewertet ob Foto eine Referenz zum Film zeigt.
        
        Args:
            photo_path: Pfad zum Foto
            film_title: Name des Films
            easter_egg_description: Beschreibung des Easter Eggs (optional)
            
        Returns:
            Tuple[is_approved, confidence, reasoning, full_response]
            - is_approved: True wenn Referenz erkannt
            - confidence: Confidence-Score (0-100)
            - reasoning: Begründung der KI
            - full_response: Komplette KI-Response als Dict
        """
        # Fallback wenn KI deaktiviert
        if not self.client:
            logger.warning(f"KI deaktiviert - Auto-Approve für {film_title}")
            return True, 100, "KI-Bewertung deaktiviert (kein API-Key)", {}
        
        try:
            # Bild laden und kodieren
            logger.info(f"Bewerte Film-Referenz: {film_title} | Foto: {photo_path}")
            base64_image = self._encode_image(photo_path)
            
            # API-Request
            response = self.client.chat.completions.create(
                model="gpt-4o",  # GPT-4 Vision
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self._create_prompt(film_title, easter_egg_description)
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                timeout=config.AI_TIMEOUT_SECONDS
            )
            
            # Token-Nutzung tracken
            if hasattr(response, 'usage'):
                tokens_used = response.usage.total_tokens
                self.total_tokens_used += tokens_used
                self.total_requests += 1
                # Kosten berechnen (GPT-4o: ~$0.005 per 1K tokens input, ~$0.015 per 1K tokens output)
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                cost = (prompt_tokens * 0.005 / 1000) + (completion_tokens * 0.015 / 1000)
                self.total_cost_usd += cost
                logger.debug(f"API-Call: {tokens_used} tokens | Cost: ${cost:.4f}")
            
            # Response parsen
            content = response.choices[0].message.content
            logger.debug(f"OpenAI Response: {content}")
            
            # JSON extrahieren (manchmal ist die Response in ```json ... ``` wrapped)
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            if content.startswith("```"):
                content = content[3:]  # Remove ```
            if content.endswith("```"):
                content = content[:-3]  # Remove ```
            content = content.strip()
            
            result = json.loads(content)
            
            # Werte extrahieren
            is_reference = result.get('is_reference', False)
            confidence = int(result.get('confidence', 0))
            reasoning = result.get('reasoning', 'Keine Begründung')
            detected_elements = result.get('detected_elements', [])
            reference_type = result.get('reference_type', 'unknown')
            
            # Threshold prüfen
            is_approved = is_reference and confidence >= config.AI_CONFIDENCE_THRESHOLD
            
            logger.info(
                f"KI-Bewertung Film: {film_title} | "
                f"Reference={is_reference} | Confidence={confidence}% | "
                f"Type={reference_type} | Approved={is_approved} | Elements={detected_elements}"
            )
            
            return is_approved, confidence, reasoning, result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON-Parse-Fehler: {e} | Content: {content}")
            # Fallback: Bei Parse-Fehler ablehnen
            return False, 0, "Fehler bei der KI-Bewertung (JSON-Parse)", {}
            
        except APITimeoutError:
            logger.error(f"OpenAI API Timeout nach {config.AI_TIMEOUT_SECONDS}s")
            # Fallback: Bei Timeout -> manuelle Review
            return False, 0, "KI-Bewertung Timeout - bitte Admin kontaktieren", {}
            
        except RateLimitError:
            logger.error("OpenAI API Rate Limit erreicht")
            return False, 0, "Zu viele Anfragen - bitte später versuchen", {}
            
        except APIError as e:
            logger.error(f"OpenAI API Error: {e}")
            return False, 0, "KI-Service vorübergehend nicht verfügbar", {}
            
        except Exception as e:
            logger.error(f"Unerwarteter Fehler bei KI-Bewertung: {e}", exc_info=True)
            return False, 0, "Technischer Fehler bei der Bewertung", {}
    
    def evaluate_puzzle_poster(
        self,
        photo_path: str,
        film_title: str,
        poster_urls: list = None
    ) -> Tuple[bool, int, str, Dict]:
        """
        Bewertet ob Puzzle-Screenshot ein gelöstes Filmplakat zeigt.
        
        Args:
            photo_path: Pfad zum Screenshot
            film_title: Name des Films
            poster_urls: URLs zu offiziellen Postern (optional)
            
        Returns:
            Tuple[is_valid, confidence, reasoning, full_response]
        """
        # Fallback wenn KI deaktiviert
        if not self.client:
            logger.warning(f"KI deaktiviert - Auto-Approve für Puzzle {film_title}")
            return True, 100, "KI-Bewertung deaktiviert (kein API-Key)", {}
        
        try:
            # Bild laden und kodieren
            logger.info(f"Bewerte Puzzle-Poster: {film_title} | Foto: {photo_path}")
            base64_image = self._encode_image(photo_path)
            
            # API-Request
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self._create_puzzle_prompt(film_title, poster_urls)
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                timeout=config.AI_TIMEOUT_SECONDS
            )
            
            # Token-Nutzung tracken
            if hasattr(response, 'usage'):
                tokens_used = response.usage.total_tokens
                self.total_tokens_used += tokens_used
                self.total_requests += 1
                # Kosten berechnen (GPT-4o: ~$0.005 per 1K tokens input, ~$0.015 per 1K tokens output)
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                cost = (prompt_tokens * 0.005 / 1000) + (completion_tokens * 0.015 / 1000)
                self.total_cost_usd += cost
                logger.debug(f"API-Call (Puzzle): {tokens_used} tokens | Cost: ${cost:.4f}")
            
            # Response parsen
            content = response.choices[0].message.content
            logger.debug(f"OpenAI Response (Puzzle): {content}")
            
            # JSON extrahieren
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            result = json.loads(content)
            
            # Werte extrahieren
            is_valid = result.get('is_valid', False)
            confidence = int(result.get('confidence', 0))
            reasoning = result.get('reasoning', 'Keine Begründung')
            issues = result.get('issues', [])
            
            # Threshold prüfen
            is_approved = is_valid and confidence >= config.AI_CONFIDENCE_THRESHOLD
            
            logger.info(
                f"KI-Bewertung Puzzle: {film_title} | "
                f"Valid={is_valid} | Confidence={confidence}% | "
                f"Approved={is_approved} | Issues={issues}"
            )
            
            return is_approved, confidence, reasoning, result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON-Parse-Fehler (Puzzle): {e} | Content: {content}")
            return False, 0, "Fehler bei der KI-Bewertung (JSON-Parse)", {}
            
        except APITimeoutError:
            logger.error(f"OpenAI API Timeout bei Puzzle-Bewertung")
            return False, 0, "KI-Bewertung Timeout - bitte Admin kontaktieren", {}
            
        except RateLimitError:
            logger.error("OpenAI API Rate Limit bei Puzzle-Bewertung")
            return False, 0, "Zu viele Anfragen - bitte später versuchen", {}
            
        except APIError as e:
            logger.error(f"OpenAI API Error (Puzzle): {e}")
            return False, 0, "KI-Service vorübergehend nicht verfügbar", {}
            
        except Exception as e:
            logger.error(f"Unerwarteter Fehler bei Puzzle-Bewertung: {e}", exc_info=True)
            return False, 0, "Technischer Fehler bei der Bewertung", {}
    
    def is_available(self) -> bool:
        """
        Prüft ob KI-Service verfügbar ist.
        
        Returns:
            True wenn OpenAI API-Key gesetzt
        """
        return self.client is not None


# Singleton-Instanz
ai_evaluator = AIEvaluator()
