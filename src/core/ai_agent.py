"""
Agent IA central - Ollama
Intégré dans chaque module de l'application
"""

import httpx
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from src.core.config import settings
from src.core.database import get_session
from src.core.models import *


class AIRequest(BaseModel):
    """Requête vers l'agent IA"""
    prompt: str
    context: Optional[Dict[str, Any]] = None
    max_tokens: int = Field(default=500, gt=0, le=2000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    system_prompt: Optional[str] = None


class AIResponse(BaseModel):
    """Réponse de l'agent IA"""
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class AgentIA:
    """
    Agent IA central utilisant Ollama
    S'intègre dans tous les modules
    """

    def __init__(self):
        self.base_url = settings.OLLAMA_URL
        self.model = settings.OLLAMA_MODEL
        self.client = httpx.AsyncClient(timeout=30.0)

    async def _call_ollama(
            self,
            prompt: str,
            system_prompt: str = "",
            temperature: float = 0.7,
            max_tokens: int = 500
    ) -> str:
        """Appel API Ollama"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                }
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")

        except httpx.HTTPError as e:
            print(f"Erreur Ollama: {e}")
            return f"[IA non disponible] Erreur: {str(e)}"

    # ===================================
    # 🍲 CUISINE - Suggestions recettes
    # ===================================

    async def suggerer_recettes(
            self,
            inventaire: List[Dict],
            preferences: Optional[List[str]] = None,
            nb_suggestions: int = 3
    ) -> List[Dict]:
        """
        Suggère des recettes basées sur l'inventaire disponible
        """
        items_text = "\n".join([
            f"- {item['nom']}: {item['quantite']} {item['unite']}"
            for item in inventaire
        ])

        pref_text = f"\nPréférences: {', '.join(preferences)}" if preferences else ""

        system_prompt = f"""Tu es un chef cuisinier expert.
Suggère {nb_suggestions} recettes RÉALISABLES avec les ingrédients disponibles.
Réponds UNIQUEMENT en JSON valide :
[
  {{
    "nom": "Nom de la recette",
    "ingredients": ["ing1", "ing2"],
    "faisabilite": 85,
    "raison": "Explication courte",
    "temps_preparation": 30
  }}
]
"""

        prompt = f"""Inventaire disponible :
{items_text}{pref_text}

Suggère {nb_suggestions} recettes faisables MAINTENANT."""

        response = await self._call_ollama(prompt, system_prompt, temperature=0.8)

        try:
            # Nettoyer la réponse (enlever markdown si présent)
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            suggestions = json.loads(cleaned.strip())
            return suggestions[:nb_suggestions]

        except json.JSONDecodeError:
            # Fallback : réponse structurée simple
            return [{
                "nom": "Erreur parsing",
                "ingredients": [item["nom"] for item in inventaire[:3]],
                "faisabilite": 0,
                "raison": "Impossible de parser la réponse IA",
                "temps_preparation": 0
            }]

    async def detecter_gaspillage(self, inventaire: List[Dict]) -> Dict:
        """Détecte les items à risque de gaspillage"""
        items_faibles = [
            item for item in inventaire
            if item.get("quantite", 0) < 2
        ]

        if not items_faibles:
            return {
                "statut": "OK",
                "message": "Aucun risque détecté",
                "suggestions": []
            }

        items_text = ", ".join([item["nom"] for item in items_faibles])

        system_prompt = """Tu es un expert anti-gaspillage.
Suggère des recettes RAPIDES pour utiliser ces ingrédients.
Format JSON:
{
  "recettes_urgentes": ["recette1", "recette2"],
  "conseil": "Conseil pratique"
}
"""

        prompt = f"Items à utiliser rapidement : {items_text}"
        response = await self._call_ollama(prompt, system_prompt)

        try:
            result = json.loads(response.strip())
            result["statut"] = "ATTENTION"
            result["items"] = items_text
            return result
        except:
            return {
                "statut": "ATTENTION",
                "items": items_text,
                "recettes_urgentes": [f"Utiliser {items_text} en salade/soupe"],
                "conseil": "À consommer rapidement"
            }

    async def optimiser_courses(
            self,
            inventaire: List[Dict],
            recettes_prevues: List[str]
    ) -> Dict:
        """Optimise la liste de courses"""
        inv_text = ", ".join([i["nom"] for i in inventaire if i.get("quantite", 0) < 3])
        rec_text = ", ".join(recettes_prevues)

        system_prompt = """Tu es un expert en courses.
Optimise la liste par rayon/magasin.
Format JSON:
{
  "par_rayon": {
    "Frais": ["item1", "item2"],
    "Épicerie": ["item3"]
  },
  "budget_estime": 50
}
"""

        prompt = f"""Stock bas: {inv_text}
Recettes prévues: {rec_text}

Crée une liste optimisée."""

        response = await self._call_ollama(prompt, system_prompt)

        try:
            return json.loads(response.strip())
        except:
            return {
                "par_rayon": {"À acheter": [inv_text]},
                "budget_estime": 50
            }

    # ===================================
    # 👶 FAMILLE - Conseils Jules
    # ===================================

    async def conseiller_developpement(
            self,
            age_mois: int,
            contexte: Optional[Dict] = None
    ) -> Dict:
        """Conseils développement selon l'âge"""
        system_prompt = f"""Tu es un pédiatre expert.
Donne des conseils adaptés à un bébé de {age_mois} mois.
Format JSON:
{{
  "conseils": ["conseil1", "conseil2"],
  "activites": ["activité1", "activité2"],
  "alertes": []
}}
"""

        ctx_text = ""
        if contexte:
            ctx_text = f"\nContexte: {json.dumps(contexte, indent=2)}"

        prompt = f"Bébé de {age_mois} mois.{ctx_text}\nQuels conseils ?"

        response = await self._call_ollama(prompt, system_prompt, temperature=0.5)

        try:
            return json.loads(response.strip())
        except:
            return {
                "conseils": ["Consulter un pédiatre pour conseils personnalisés"],
                "activites": ["Adaptées à l'âge"],
                "alertes": []
            }

    async def analyser_bien_etre(
            self,
            donnees_sommeil: List[Dict],
            donnees_humeur: List[Dict]
    ) -> Dict:
        """Analyse bien-être et tendances"""
        somm_text = "\n".join([
            f"- {d['date']}: {d['heures']}h" for d in donnees_sommeil[-7:]
        ])
        humeur_text = "\n".join([
            f"- {d['date']}: {d['humeur']}" for d in donnees_humeur[-7:]
        ])

        system_prompt = """Tu es psychologue spécialisé en bien-être familial.
Analyse les tendances et donne des recommandations.
Format JSON:
{
  "tendances": "Description",
  "recommandations": ["reco1", "reco2"],
  "score_bien_etre": 75
}
"""

        prompt = f"""Sommeil (7 derniers jours):
{somm_text}

Humeur:
{humeur_text}

Analyse ces données."""

        response = await self._call_ollama(prompt, system_prompt, temperature=0.6)

        try:
            return json.loads(response.strip())
        except:
            return {
                "tendances": "Données insuffisantes",
                "recommandations": ["Continuer le suivi"],
                "score_bien_etre": 70
            }

    async def rappeler_routines(
            self,
            routines: List[Dict],
            heure_actuelle: str
    ) -> List[Dict]:
        """Génère des rappels intelligents pour les routines"""
        routines_text = "\n".join([
            f"- {r['nom']} à {r['heure']}" for r in routines
        ])

        system_prompt = """Tu es assistant organisationnel.
Identifie les routines à rappeler maintenant ou bientôt.
Format JSON:
[
  {"routine": "nom", "priorite": "haute", "message": "Rappel"}
]
"""

        prompt = f"""Heure actuelle: {heure_actuelle}
Routines:
{routines_text}

Quelles routines rappeler ?"""

        response = await self._call_ollama(prompt, system_prompt, temperature=0.3)

        try:
            return json.loads(response.strip())
        except:
            return []

    # ===================================
    # 🏡 MAISON - Projets & Jardin
    # ===================================

    async def prioriser_projets(
            self,
            projets: List[Dict],
            contraintes: Optional[Dict] = None
    ) -> List[Dict]:
        """Priorise les projets selon urgence/importance"""
        proj_text = "\n".join([
            f"- {p['nom']}: {p.get('statut', 'À faire')}" for p in projets
        ])

        contr_text = ""
        if contraintes:
            contr_text = f"\nContraintes: {json.dumps(contraintes)}"

        system_prompt = """Tu es expert en gestion de projets.
Priorise les projets selon urgence/importance (Matrice Eisenhower).
Format JSON:
[
  {"projet": "nom", "priorite": 1, "raison": "explication"}
]
"""

        prompt = f"""Projets:
{proj_text}{contr_text}

Priorise-les."""

        response = await self._call_ollama(prompt, system_prompt)

        try:
            return json.loads(response.strip())
        except:
            return [{"projet": p["nom"], "priorite": i+1, "raison": "Ordre original"}
                    for i, p in enumerate(projets)]

    async def suggerer_jardin(
            self,
            saison: str,
            meteo: Dict,
            plantes_actuelles: List[str]
    ) -> Dict:
        """Suggestions jardinage selon météo et saison"""
        plantes_text = ", ".join(plantes_actuelles)
        meteo_text = f"{meteo.get('condition', 'inconnue')}, {meteo.get('temp', 0)}°C"

        system_prompt = """Tu es expert en jardinage.
Suggère des actions selon la météo et la saison.
Format JSON:
{
  "actions_jour": ["action1", "action2"],
  "plantations": ["plante1"],
  "entretien": ["entretien1"],
  "alertes": []
}
"""

        prompt = f"""Saison: {saison}
Météo: {meteo_text}
Plantes: {plantes_text}

Que faire au jardin aujourd'hui ?"""

        response = await self._call_ollama(prompt, system_prompt, temperature=0.7)

        try:
            return json.loads(response.strip())
        except:
            return {
                "actions_jour": ["Vérifier l'arrosage"],
                "plantations": [],
                "entretien": ["Désherbage"],
                "alertes": []
            }

    # ===================================
    # 📅 PLANNING - Organisation
    # ===================================

    async def generer_planning_semaine(
            self,
            contraintes: Dict,
            recettes_dispo: List[str]
    ) -> Dict:
        """Génère un planning hebdomadaire optimisé"""
        rec_text = ", ".join(recettes_dispo)
        contr_text = json.dumps(contraintes, indent=2)

        system_prompt = """Tu es planificateur familial expert.
Crée un planning équilibré et réaliste pour 7 jours.
Format JSON:
{
  "planning": [
    {"jour": "Lundi", "repas": "Nom", "raison": "Explication"}
  ],
  "courses": ["item1", "item2"]
}
"""

        prompt = f"""Recettes disponibles: {rec_text}
Contraintes: {contr_text}

Crée un planning de 7 jours."""

        response = await self._call_ollama(prompt, system_prompt, temperature=0.8)

        try:
            return json.loads(response.strip())
        except:
            jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
            return {
                "planning": [
                    {"jour": j, "repas": recettes_dispo[i % len(recettes_dispo)], "raison": "Rotation"}
                    for i, j in enumerate(jours)
                ],
                "courses": ["À définir"]
            }

    # ===================================
    # 💬 CHAT - Conversationnel
    # ===================================

    async def chat(
            self,
            message: str,
            historique: List[Dict],
            contexte: Optional[Dict] = None
    ) -> str:
        """Interface conversationnelle générale"""
        hist_text = "\n".join([
            f"{h['role']}: {h['content']}"
            for h in historique[-5:]  # 5 derniers messages
        ])

        ctx_text = ""
        if contexte:
            ctx_text = f"\n\nContexte actuel:\n{json.dumps(contexte, indent=2)}"

        system_prompt = f"""Tu es l'assistant familial "MaTanne".
Tu aides à gérer:
- Cuisine (recettes, inventaire, courses)
- Famille (Jules, routines, bien-être)
- Maison (projets, jardin)
- Planning

Réponds de manière concise, amicale et actionnable.{ctx_text}"""

        prompt = f"""Historique:
{hist_text}

Utilisateur: {message}"""