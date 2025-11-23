# 🤖 Assistant MaTanne v2 - Application Moderne avec IA

Application familiale intelligente pour la gestion du quotidien avec agent IA intégré.

## 📁 Structure du projet

```
assistant-matanne-v2/
├── pyproject.toml              # Configuration Poetry
├── Makefile                    # Commandes automatisées
├── docker-compose.yml          # PostgreSQL + App
├── Dockerfile                  # Image Docker
├── .env.example                # Variables d'environnement
├── .gitignore
├── .streamlit/
│   └── config.toml            # Config Streamlit
│
├── src/
│   ├── __init__.py
│   │
│   ├── app.py                 # Point d'entrée Streamlit
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── database.py        # Connexion PostgreSQL + migrations
│   │   ├── config.py          # Configuration centralisée
│   │   ├── models.py          # SQLAlchemy models
│   │   └── ai_agent.py        # Agent IA Ollama (cœur)
│   │
│   ├── modules/
│   │   ├── __init__.py
│   │   │
│   │   ├── cuisine/
│   │   │   ├── __init__.py
│   │   │   ├── recettes.py         # + Suggestions IA
│   │   │   ├── inventaire.py       # + Détection stock bas
│   │   │   ├── batch_cooking.py    # + Planification IA
│   │   │   └── courses.py          # + Optimisation IA
│   │   │
│   │   ├── famille/
│   │   │   ├── __init__.py
│   │   │   ├── suivi_jules.py      # + Conseils IA
│   │   │   ├── bien_etre.py        # + Analyse IA
│   │   │   └── routines.py         # + Rappels IA
│   │   │
│   │   ├── maison/
│   │   │   ├── __init__.py
│   │   │   ├── projets.py          # + Priorisation IA
│   │   │   ├── jardin.py           # + Météo + IA
│   │   │   └── entretien.py        # + Planning IA
│   │   │
│   │   ├── planning/
│   │   │   ├── __init__.py
│   │   │   ├── calendrier.py       # + IA intégrée
│   │   │   └── agenda.py           # Sync externe
│   │   │
│   │   └── parametres/
│   │       ├── __init__.py
│   │       ├── profils.py
│   │       └── notifications.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── weather.py         # API météo
│   │   └── ollama_client.py   # Client Ollama
│   │
│   └── utils/
│       ├── __init__.py
│       ├── helpers.py
│       └── decorators.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Fixtures pytest
│   ├── test_core/
│   │   ├── test_database.py
│   │   └── test_ai_agent.py
│   ├── test_modules/
│   │   ├── test_cuisine.py
│   │   ├── test_famille.py
│   │   └── test_maison.py
│   └── fixtures/
│       └── sample_data.sql
│
├── scripts/
│   ├── init_db.py             # Initialisation DB
│   ├── seed_data.py           # Données de démo
│   └── backup.py              # Sauvegarde
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   └── USER_GUIDE.md
│
└── data/
    └── backups/               # Sauvegardes
```

## 🚀 Installation rapide

### Prérequis

- Python 3.11+
- Docker & Docker Compose
- Ollama installé localement

### Installation

```bash
# 1. Cloner le repo
git clone https://github.com/ton-compte/assistant-matanne-v2
cd assistant-matanne-v2

# 2. Installer les dépendances
make install

# 3. Configurer l'environnement
cp .env.example .env
# Éditer .env avec tes paramètres

# 4. Démarrer PostgreSQL
make docker-db

# 5. Initialiser la base
make init-db

# 6. Démarrer Ollama (dans un autre terminal)
ollama serve

# 7. Charger le modèle IA
ollama pull llama2

# 8. Lancer l'application
make run
```

## 🎯 Fonctionnalités

### 🤖 Agent IA intégré partout

L'IA est **dans chaque module**, pas à part :

#### 🍲 Cuisine
- **Suggestions automatiques** de recettes selon inventaire
- **Détection anti-gaspillage** (items proches péremption)
- **Planification intelligente** batch cooking
- **Optimisation courses** par magasin/rayon

#### 👶 Famille
- **Conseils développement** adaptés à l'âge de Jules
- **Analyse bien-être** (sommeil, humeur)
- **Rappels intelligents** routines quotidiennes

#### 🏡 Maison
- **Priorisation projets** selon urgence
- **Suggestions jardin** selon météo et saison
- **Planning entretien** automatique

#### 📅 Planning
- **Synchronisation calendrier** externe
- **Suggestions horaires** optimales

#### 🌤️ Météo
- **Analyse impact** sur jardinage
- **Suggestions tâches** selon prévisions
- **Alertes** gel, canicule, pluie

## 🧪 Tests

```bash
# Lancer tous les tests
make test

# Tests avec couverture
make coverage

# Tests d'un module spécifique
make test-cuisine
make test-agent

# Tests d'intégration
make test-integration
```

## 📦 Déploiement

### Local
```bash
make run
```

### Docker
```bash
make docker-build
make docker-run
```

### Streamlit Cloud

1. Pusher sur GitHub
2. Connecter à [share.streamlit.io](https://share.streamlit.io)
3. Configurer les secrets (PostgreSQL, Ollama)
4. Déployer !

## 🛠️ Commandes Make

```bash
make help              # Affiche toutes les commandes
make install           # Installation complète
make run               # Lance l'app
make test              # Tests complets
make coverage          # Rapport de couverture
make lint              # Vérification code
make format            # Formatage automatique
make docker-build      # Build image Docker
make docker-run        # Lance avec Docker
make docker-db         # PostgreSQL uniquement
make init-db           # Init base de données
make seed              # Données de démo
make backup            # Sauvegarde DB
make clean             # Nettoyage
```

## 🔧 Configuration

### Variables d'environnement (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/matanne

# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Weather API
WEATHER_API_KEY=ton_api_key

# App
DEBUG=False
SECRET_KEY=ton_secret_key
```

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Guide utilisateur](docs/USER_GUIDE.md)
- [Déploiement](docs/DEPLOYMENT.md)

## 🤝 Contribution

```bash
# Créer une branche
git checkout -b feature/ma-feature

# Faire les changements
# ...

# Tests
make test

# Lint
make lint

# Commit
git commit -m "feat: ma nouvelle feature"

# Push
git push origin feature/ma-feature
```

## 📄 Licence

MIT

## 👨‍💻 Auteur

Anne - Assistant Familial Intelligent