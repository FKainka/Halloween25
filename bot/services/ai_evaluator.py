"""
OpenAI Vision API Integration für Film-Referenz-Bewertung.
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
        if not config.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY nicht gesetzt - KI-Bewertung deaktiviert")
            self.client = None
        else:
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
            logger.info("AI Evaluator initialisiert")
    
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
    
    def _create_prompt(self, film_title: str) -> str:
        """
        Erstellt Prompt für Film-Bewertung.
        
        Args:
            film_title: Name des Films
            
        Returns:
            Formatierter Prompt
        """
        prompt = f"""Du bist ein Experte für Sci-Fi-Filme und analysierst ein Foto von einer Halloween-Party.

Die Person behauptet, dass dieses Foto eine Referenz zum Film "{film_title}" zeigt.

Prüfe das Foto auf:
- Easter Eggs (spezifische Gegenstände aus dem Film)
- Nachgestellte Szenen oder ikonische Momente
- Charaktere, Kostüme oder Verkleidungen
- Ikonische Requisiten, Symbole oder Settings aus dem Film
- Visuelle Elemente die eindeutig auf den Film hinweisen

WICHTIG: Es muss eine ERKENNBARE und EINDEUTIGE Referenz zum Film sein!
Einfache Ähnlichkeiten oder vage Assoziationen zählen NICHT.

Antworte NUR mit einem JSON-Objekt in folgendem Format (keine zusätzlichen Texte):
{{
  "is_reference": true oder false,
  "confidence": 0-100 (Wie sicher bist du?),
  "reasoning": "Kurze Erklärung was du siehst und warum es eine Referenz ist/nicht ist",
  "detected_elements": ["Element 1", "Element 2", ...]
}}

Beispiele für GUTE Referenzen:
- Matrix: Grüner Code, rote/blaue Pille, Agent Smith Sonnenbrille, "There is no spoon" Löffel
- Terminator: Rote LED-Augen, Metallskelett, "I'll be back" Schild
- Star Wars: Lichtschwert, Darth Vader Maske, R2D2 Roboter

Beispiele für KEINE Referenzen:
- Nur schwarze Kleidung (zu allgemein)
- Generische Sci-Fi Props ohne Film-Bezug
- Normale Alltagsgegenstände
"""
        return prompt
    
    def evaluate_film_reference(
        self, 
        photo_path: str, 
        film_title: str
    ) -> Tuple[bool, int, str, Dict]:
        """
        Bewertet ob Foto eine Referenz zum Film zeigt.
        
        Args:
            photo_path: Pfad zum Foto
            film_title: Name des Films
            
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
                                "text": self._create_prompt(film_title)
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
            
            # Threshold prüfen
            is_approved = is_reference and confidence >= config.AI_CONFIDENCE_THRESHOLD
            
            logger.info(
                f"KI-Bewertung: {film_title} | "
                f"Reference={is_reference} | Confidence={confidence}% | "
                f"Approved={is_approved} | Elements={detected_elements}"
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
    
    def is_available(self) -> bool:
        """
        Prüft ob KI-Service verfügbar ist.
        
        Returns:
            True wenn OpenAI API-Key gesetzt
        """
        return self.client is not None


# Singleton-Instanz
ai_evaluator = AIEvaluator()
