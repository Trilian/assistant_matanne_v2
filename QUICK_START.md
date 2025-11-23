# 🚀 Démarrage Rapide - Assistant MaTanne v2

## 📋 Prérequis

- **Python 3.11+**
- **PostgreSQL 14+** (ou Docker)
- **Ollama** (pour l'IA)
- **Redis** (optionnel, pour cache)

## ⚡ Installation en 5 minutes

### 1. Cloner et installer

```bash
# Cloner le projet
git clone https://github.com/ton-compte/assistant-matanne-v2
cd assistant-matanne-v2

# Installer Poetry (si pas déjà fait)
curl -sSL https://install.python-poetry.org | python3 -

# Installer les dépendances
make install
```

### 2. Configuration

```bash
# Copier le fichier d'environnement
cp .env.example .env

# Éditer .env avec tes paramètres
nano .env
```

**Configuration minimale dans `.env` :**
```env
# Database
POSTGRES_PASSWORD=ton_mot_de_passe_securise

# IA
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Météo (optionnel)
WEATHER_API_KEY=ta_cle_api_openweathermap
```

### 3. Démarrer PostgreSQL

**Option A - Docker (recommandé) :**
```bash
make docker-db
```

**Option B - PostgreSQL local :**
```bash
# Créer la base
createdb matanne
```

### 4. Initialiser la base

```bash
# Créer les tables
make init-db

# Charger des données de démo (optionnel)
make seed
```

### 5. Installer et démarrer Ollama

```bash
# Installer Ollama
make install-ollama

# OU manuellement :
curl -fsSL https://ollama.com/install.sh | sh

# Télécharger le modèle
ollama pull llama2

# Démarrer le serveur (dans un terminal séparé)
ollama serve
```

### 6. Lancer l'application

```bash
make run
```

🎉 **L'application est accessible sur http://localhost:8501**

---

## 🧪 Vérifications

### Tester la connexion DB

```python
python -c "from src.core.database import check_connection; print('✅ DB OK' if check_connection() else '❌ DB KO')"
```

### Tester Ollama

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama2",
  "prompt": "Bonjour"
}'
```

### Lancer les tests

```bash
make test
```

---

## 📦 Commandes utiles

```bash
# Développement
make run                  # Lancer l'app
make dev                  # Mode dev (reload auto)
make test                 # Tests
make coverage             # Tests + couverture
make format               # Formater le code
make lint                 # Vérifier le code

# Base de données
make docker-db            # Démarrer PostgreSQL
make init-db              # Créer les tables
make seed                 # Données de démo
make reset-db             # Réinitialiser
make backup               # Sauvegarder

# Docker
make docker-build         # Build image
make docker-run           # Lancer avec Docker
make docker-stop          # Arrêter

# Déploiement
make deploy-streamlit     # Préparer pour Streamlit Cloud
make check-deploy         # Vérifier avant déploiement
```

---

## 🏗️ Structure du projet

```
assistant-matanne-v2/
├── src/
│   ├── app.py              # 👈 Application principale
│   ├── core/
│   │   ├── ai_agent.py     # 🤖 Agent IA (cœur)
│   │   ├── config.py       # ⚙️ Configuration
│   │   ├── database.py     # 🗄️ Connexion DB
│   │   └── models.py       # 📊 Modèles SQLAlchemy
│   └── modules/
│       ├── cuisine/        # 🍲
│       ├── famille/        # 👶
│       ├── maison/         # 🏡
│       └── planning/       # 📅
├── tests/                  # 🧪 Tests
├── pyproject.toml          # 📦 Dépendances
├── Makefile                # 🛠️ Commandes
├── docker-compose.yml      # 🐳 Docker
└── .env                    # 🔐 Configuration
```

---

## 🤖 Utiliser l'IA

L'IA est **intégrée dans chaque module**. Exemples :

### Dans le code (développement)

```python
from src.core.ai_agent import AgentIA

agent = AgentIA()

# Suggérer des recettes
suggestions = await agent.suggerer_recettes(
    inventaire=[
        {"nom": "Tomates", "quantite": 5, "unite": "pcs"},
        {"nom": "Pâtes", "quantite": 500, "unite": "g"}
    ],
    nb_suggestions=3
)

# Chat
reponse = await agent.chat(
    "Qu'est-ce que je peux cuisiner ce soir ?",
    historique=[],
    contexte={"stock_bas": ["lait", "œufs"]}
)
```

### Dans l'interface

Chaque module a des boutons IA intégrés :
- **🍲 Cuisine** → "✨ Suggérer des recettes"
- **👶 Famille** → "💡 Conseils développement"
- **🏡 Maison** → "🎯 Prioriser les projets"
- **🌱 Jardin** → "☀️ Actions selon météo"

---

## 🌤️ Configuration météo

1. Créer un compte sur [OpenWeatherMap](https://openweathermap.org/api)
2. Obtenir une clé API (gratuite)
3. Ajouter dans `.env` :

```env
WEATHER_API_KEY=ta_cle_ici
WEATHER_CITY=Ta_Ville
```

4. L'IA utilisera automatiquement la météo pour :
    - Suggérer des tâches de jardinage
    - Planifier les activités extérieures
    - Alerter en cas de gel/canicule

---

## 🚢 Déploiement Streamlit Cloud

### 1. Préparer le déploiement

```bash
make deploy-streamlit
```

Cela génère `requirements.txt` depuis `pyproject.toml`.

### 2. Créer une base PostgreSQL externe

**Options recommandées (gratuites) :**
- [Supabase](https://supabase.com) - 500 MB gratuit
- [ElephantSQL](https://www.elephantsql.com) - 20 MB gratuit
- [Neon](https://neon.tech) - 0.5 GB gratuit

### 3. Configurer les secrets sur Streamlit Cloud

Dans l'interface Streamlit Cloud :

```toml
# .streamlit/secrets.toml

DATABASE_URL = "postgresql://user:pass@host:5432/db"
SECRET_KEY = "ton-secret-key-uuid"
WEATHER_API_KEY = "ta_cle_openweathermap"

# Ollama (optionnel, si hébergé séparément)
OLLAMA_URL = "http://ton-serveur-ollama:11434"
ENABLE_AI = true
```

### 4. Déployer

1. Pusher sur GitHub
2. Se connecter sur [share.streamlit.io](https://share.streamlit.io)
3. Sélectionner le repo
4. Configurer les secrets
5. Déployer !

**Note :** L'IA (Ollama) ne fonctionnera pas directement sur Streamlit Cloud car il faut un serveur dédié. Options :
- Désactiver l'IA : `ENABLE_AI=false`
- Héberger Ollama séparément (VPS, etc.)
- Utiliser OpenAI API à la place (modification mineure du code)

---

## 🐛 Dépannage

### PostgreSQL ne démarre pas

```bash
# Vérifier les logs
make logs-db

# Redémarrer
make docker-db-stop
make docker-db
```

### Ollama ne répond pas

```bash
# Vérifier qu'il tourne
ps aux | grep ollama

# Redémarrer
pkill ollama
ollama serve
```

### Erreur "module not found"

```bash
# Réinstaller
make clean
make install
```

### Tests échouent

```bash
# Vérifier l'environnement de test
ENV=test make test

# Réinitialiser la DB de test
ENV=test make reset-db
```

---

## 📚 Documentation complète

- [Architecture](docs/ARCHITECTURE.md)
- [Guide utilisateur](docs/USER_GUIDE.md)
- [Contribution](docs/CONTRIBUTING.md)

---

## 🤝 Support

- **Issues :** [GitHub Issues](https://github.com/ton-compte/assistant-matanne-v2/issues)
- **Discussions :** [GitHub Discussions](https://github.com/ton-compte/assistant-matanne-v2/discussions)

---

**🎉 Bienvenue dans Assistant MaTanne v2 !**

L'agent IA est prêt à réduire ta charge mentale. 🤖💚