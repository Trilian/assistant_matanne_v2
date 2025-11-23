"""
Service Météo
Intégration OpenWeatherMap API
"""

import httpx
from typing import Dict, Optional
from datetime import datetime, date
import logging

from src.core.config import settings
from src.core.database import get_db_context
from src.core.models import WeatherLog

logger = logging.getLogger(__name__)


class WeatherService:
    """Service de récupération de la météo"""

    def __init__(self):
        self.api_key = settings.WEATHER_API_KEY
        self.api_url = settings.WEATHER_API_URL
        self.city = settings.WEATHER_CITY
        self.country = settings.WEATHER_COUNTRY
        self.units = settings.WEATHER_UNITS
        self.enabled = settings.ENABLE_WEATHER and self.api_key

    async def get_current_weather(self) -> Optional[Dict]:
        """Récupère la météo actuelle"""
        if not self.enabled:
            logger.warning("Service météo désactivé ou clé API manquante")
            return self._get_mock_weather()

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.api_url}/weather",
                    params={
                        "q": f"{self.city},{self.country}",
                        "appid": self.api_key,
                        "units": self.units,
                        "lang": "fr"
                    }
                )
                response.raise_for_status()
                data = response.json()

                return self._format_weather_data(data)

        except Exception as e:
            logger.error(f"Erreur récupération météo : {e}")
            return self._get_mock_weather()

    async def get_forecast(self, days: int = 5) -> Optional[Dict]:
        """Récupère les prévisions sur X jours"""
        if not self.enabled:
            return None

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.api_url}/forecast",
                    params={
                        "q": f"{self.city},{self.country}",
                        "appid": self.api_key,
                        "units": self.units,
                        "lang": "fr",
                        "cnt": days * 8  # 8 prévisions par jour (3h)
                    }
                )
                response.raise_for_status()
                data = response.json()

                return self._format_forecast_data(data)

        except Exception as e:
            logger.error(f"Erreur récupération prévisions : {e}")
            return None

    def _format_weather_data(self, data: Dict) -> Dict:
        """Formate les données météo"""
        return {
            "condition": data["weather"][0]["description"].capitalize(),
            "condition_code": data["weather"][0]["main"],
            "temperature": round(data["main"]["temp"], 1),
            "feels_like": round(data["main"]["feels_like"], 1),
            "temp_min": round(data["main"]["temp_min"], 1),
            "temp_max": round(data["main"]["temp_max"], 1),
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind_speed": round(data["wind"]["speed"] * 3.6, 1),  # m/s → km/h
            "clouds": data["clouds"]["all"],
            "sunrise": datetime.fromtimestamp(data["sys"]["sunrise"]),
            "sunset": datetime.fromtimestamp(data["sys"]["sunset"]),
            "icon": data["weather"][0]["icon"]
        }

    def _format_forecast_data(self, data: Dict) -> Dict:
        """Formate les prévisions"""
        forecasts = []

        for item in data["list"]:
            forecasts.append({
                "datetime": datetime.fromtimestamp(item["dt"]),
                "temperature": round(item["main"]["temp"], 1),
                "condition": item["weather"][0]["description"].capitalize(),
                "condition_code": item["weather"][0]["main"],
                "humidity": item["main"]["humidity"],
                "wind_speed": round(item["wind"]["speed"] * 3.6, 1),
                "precipitation": item.get("rain", {}).get("3h", 0),
                "icon": item["weather"][0]["icon"]
            })

        return {
            "city": data["city"]["name"],
            "forecasts": forecasts
        }

    def _get_mock_weather(self) -> Dict:
        """Retourne des données météo mockées"""
        return {
            "condition": "Partiellement nuageux",
            "condition_code": "Clouds",
            "temperature": 18.0,
            "feels_like": 17.0,
            "temp_min": 15.0,
            "temp_max": 22.0,
            "humidity": 65,
            "pressure": 1013,
            "wind_speed": 15.0,
            "clouds": 40,
            "sunrise": datetime.now().replace(hour=7, minute=30),
            "sunset": datetime.now().replace(hour=20, minute=15),
            "icon": "02d"
        }

    def save_to_database(self, weather_data: Dict):
        """Sauvegarde la météo en base de données"""
        try:
            with get_db_context() as db:
                # Vérifier si déjà enregistré aujourd'hui
                existing = db.query(WeatherLog).filter(
                    WeatherLog.date == date.today()
                ).first()

                if existing:
                    # Mettre à jour
                    existing.condition = weather_data["condition"]
                    existing.temperature = weather_data["temperature"]
                    existing.humidity = weather_data["humidity"]
                    existing.wind_speed = weather_data["wind_speed"]
                    existing.forecast_data = weather_data
                else:
                    # Créer nouvelle entrée
                    log = WeatherLog(
                        date=date.today(),
                        condition=weather_data["condition"],
                        temperature=weather_data["temperature"],
                        humidity=weather_data["humidity"],
                        wind_speed=weather_data["wind_speed"],
                        forecast_data=weather_data
                    )
                    db.add(log)

                db.commit()
                logger.info("Météo sauvegardée en base")

        except Exception as e:
            logger.error(f"Erreur sauvegarde météo : {e}")

    def get_weather_icon_emoji(self, condition_code: str) -> str:
        """Retourne un emoji selon la condition météo"""
        icons = {
            "Clear": "☀️",
            "Clouds": "☁️",
            "Rain": "🌧️",
            "Drizzle": "🌦️",
            "Thunderstorm": "⛈️",
            "Snow": "❄️",
            "Mist": "🌫️",
            "Fog": "🌫️"
        }
        return icons.get(condition_code, "🌤️")

    def get_weather_recommendations(self, weather_data: Dict) -> list[str]:
        """Génère des recommandations selon la météo"""
        recommendations = []

        temp = weather_data["temperature"]
        condition = weather_data["condition_code"]
        wind = weather_data["wind_speed"]
        humidity = weather_data["humidity"]

        # Température
        if temp < 5:
            recommendations.append("🥶 Protège tes plantes sensibles au gel")
        elif temp > 30:
            recommendations.append("🔥 Arrose plus fréquemment, il fait chaud")
        elif 15 <= temp <= 25:
            recommendations.append("🌱 Conditions idéales pour le jardinage")

        # Pluie
        if condition == "Rain":
            recommendations.append("🌧️ Pas besoin d'arroser aujourd'hui")
            recommendations.append("⚠️ Attends que ça sèche pour travailler le sol")
        elif condition == "Clear" and humidity < 40:
            recommendations.append("💧 Pense à arroser, l'air est sec")

        # Vent
        if wind > 40:
            recommendations.append("💨 Vent fort : tuteure tes plantes")

        # Soleil
        if condition == "Clear" and temp > 25:
            recommendations.append("☀️ Arrose tôt le matin ou tard le soir")

        return recommendations


# Instance globale
weather_service = WeatherService()