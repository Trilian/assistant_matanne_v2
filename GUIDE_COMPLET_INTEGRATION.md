# 📚 Guide Complet d'Intégration

## 🎯 Vue d'ensemble

Tu as maintenant **tous les fichiers** pour une application complète et moderne :

### ✅ Ce qui est prêt

1. **Architecture complète** (15+ fichiers de config)
2. **Module Recettes fonctionnel** avec IA intégrée
3. **Tests complets** (30+ tests)
4. **Migrations Alembic** (version initiale)
5. **Configuration professionnelle**

---

## 📂 Structure des fichiers à créer

```
assistant-matanne-v2/
├── pyproject.toml                    # ✅ Généré
├── Makefile                          # ✅ Généré
├── docker-compose.yml                # ✅ Généré
├── Dockerfile                        # ✅ Généré
├── .env.example                      # ✅ Généré
├── .gitignore                        # ✅ Généré
├── alembic.ini                       # ✅ Généré
├── README.md                         # ✅ Généré
├── QUICK_START.md                    # ✅ Généré
│
├── alembic/
│   ├── env.py                        # ✅ Généré
│   └── versions/
│       └── 001_initial_schema.py     # ✅ Généré
│
├── src/
│   ├── app.py                        # ✅ Généré
│   ├── core/
│   │   ├── __init__.py               # Vide (à créer)
│   │   ├── config.py                 # ✅ Généré
│   │   ├── database.py               # ✅ Généré
│   │   ├── models.py                 # ✅ Généré
│   │   └── ai_agent.py               # ✅ Généré
│   │
│   ├── modules/
│   │   ├── __init__.py               # Vide (à créer)
│   │   ├── cuisine/
│   │   │   ├── __init__.py           # Vide (à créer)
│   │   │   └── recettes.py           # ✅ Généré
│   │   │
│   │   ├── famille/
│   │   │   └── __init__.py           # À créer
│   │   │
│   │   ├── maison/
│   │   │   └── __init__.py           # À créer
│   │   │
│   │   └── planning/
│   │       └── __init__.py           # À créer
│   │
│   └── services/
│       └── __init__.py               # À créer
│
├── tests/
│   ├── __init__.py                   # Vide (à créer)
│   ├── conftest.py                   # ✅ Généré
│   └── test_modules/
│       ├── __init__.py               # Vide (à créer)
│       └── test_cuisine.py           # ✅ Généré
│
├── scripts/
│   └── init_alembic.sh               # ✅ Généré
│
├── data/
│   └── backups/                      # Créé automatiquement
│
└── logs/                             # Créé automatiquement
```

---

## 🚀 Installation pas à pas

### Étape 1 : Créer le projet

```bash
# Créer le répertoire
mkdir assistant-matanne-v2
cd assistant-matanne-v2

# Initialiser git
git init

# Créer la structure des dossiers
mkdir -p src/{core,modules/{cuisine,famille,maison,planning},services}
mkdir -p tests/test_modules
mkdir -p scripts
mkdir -p alembic/versions
mkdir -p data/backups
mkdir -p logs

# Créer les __init__.py
touch src/__init__.py
touch src/core/__init__.py
touch src/modules/__init__.py
touch src/modules/cuisine/__init__.py
touch src/modules/famille/__init__.py
touch src/modules/maison/__init__.py
touch src/modules/planning/__init__.py
touch src/services/__init__.py
touch tests/__init__.py
touch tests/test_modules/__init__.py
```

### Étape 2 : Copier tous les fichiers générés

**Copie chaque fichier que je t'ai généré dans le bon répertoire.**

Liste des fichiers à copier :
- `pyproject.toml` → racine
- `Makefile` → racine
- `docker-compose.yml` → racine
- `Dockerfile` → racine
- `.env.example` → racine
- `.gitignore` → racine
- `alembic.ini` → racine
- `README.md` → racine
- `QUICK_START.md` → racine
- `alembic/env.py`
- `alembic/versions/001_initial_schema.py`
- `src/app.py`
- `src/core/config.py`
- `src/core/database.py`
- `src/core/models.py`
- `src/core/ai_agent.py`
- `src/modules/cuisine/recettes.py`
- `tests/conftest.py`
- `tests/test_modules/test_cuisine.py`
- `scripts/init_alembic.sh`

### Étape 3 : Installer Poetry

```bash
# Installer Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Vérifier l'installation
poetry --version
```

### Étape 4 : Installer les dépendances

```bash
# Installer toutes les dépendances
make install

# Ou manuellement :
poetry install
```

### Étape 5 : Configurer l'environnement

```bash
# Copier le fichier d'environnement
cp .env.example .env

# Éditer avec tes paramètres
nano .env
```

**Configuration minimale dans `.env` :**
```env
POSTGRES_PASSWORD=ton_mot_de_passe_fort
SECRET_KEY=$(uuidgen)  # Générer un UUID
WEATHER_API_KEY=ta_cle_api  # Optionnel
```

### Étape 6 : Démarrer PostgreSQL

```bash
# Avec Docker (recommandé)
make docker-db

# Vérifier que ça tourne
docker ps
```

### Étape 7 : Créer la base de données

```bash
# Appliquer les migrations
make init-db

# Vérifier
python -c "from src.core.database import check_connection; print('✅ OK' if check_connection() else '❌ KO')"
```

### Étape 8 : Installer et démarrer Ollama

```bash
# Option 1 : Script automatique
make install-ollama

# Option 2 : Manuel
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama2

# Démarrer Ollama (terminal séparé)
ollama serve
```

### Étape 9 : Lancer l'application

```bash
# Démarrer l'app
make run

# L'app est sur http://localhost:8501
```

---

## 🧪 Lancer les tests

```bash
# Tous les tests
make test

# Tests avec couverture
make coverage

# Tests d'un module spécifique
poetry run pytest tests/test_modules/test_cuisine.py -v

# Tests marqués
poetry run pytest -m "not slow"  # Exclure les tests lents
poetry run pytest -m "ai"         # Seulement les tests IA
```

---

## 🔧 Commandes Alembic

```bash
# Vérifier la version actuelle
alembic current

# Voir l'historique
alembic history

# Appliquer toutes les migrations
alembic upgrade head

# Créer une nouvelle migration (après modification des modèles)
alembic revision --autogenerate -m "Description du changement"

# Annuler la dernière migration
alembic downgrade -1

# Revenir à une version spécifique
alembic downgrade 001_initial
```

---

## 📝 Créer un nouveau module

### Exemple : Module Inventaire

```bash
# 1. Créer le fichier
touch src/modules/cuisine/inventaire.py
```

```python
# 2. Contenu du fichier
"""
Module Inventaire avec IA intégrée
"""

import streamlit as st
from src.core.database import get_db_context
from src.core.models import InventoryItem, Ingredient


def app():
    """Module Inventaire"""
    st.title("📦 Inventaire")
    
    # Récupérer l'agent IA
    agent = st.session_state.get("agent_ia")
    
    # Ton code ici
    st.info("Module en construction...")
    
    # Exemple d'utilisation de l'IA
    if st.button("🤖 Analyser le stock"):
        with st.spinner("Analyse en cours..."):
            # Utiliser l'agent
            result = await agent.detecter_gaspillage([...])
            st.json(result)
```

### 3. L'ajouter dans app.py

Dans `src/app.py`, ajouter dans le dictionnaire `module_map` :

```python
module_map = {
    # ... existant
    "cuisine.inventaire": "src.modules.cuisine.inventaire",
}
```

---

## 🐛 Dépannage

### PostgreSQL ne démarre pas

```bash
# Voir les logs
make logs-db

# Redémarrer proprement
make docker-db-stop
make docker-db
```

### Erreur "module not found"

```bash
# Vérifier que Poetry est activé
poetry shell

# Ou préfixer les commandes
poetry run streamlit run src/app.py
```

### Tests échouent

```bash
# Créer la DB de test
createdb matanne_test

# Réinstaller
make clean
make install
```

### Ollama ne répond pas

```bash
# Vérifier qu'il tourne
ps aux | grep ollama

# Tester manuellement
curl http://localhost:11434/api/tags

# Redémarrer
pkill ollama
ollama serve
```

---

## 🎨 Personnalisation

### Changer le modèle IA

Dans `.env` :
```env
OLLAMA_MODEL=mistral  # Au lieu de llama2
```

### Ajouter des catégories de recettes

Dans `src/modules/cuisine/recettes.py`, modifier :
```python
categories = ["Entrée", "Plat", "Dessert", "Goûter", "Apéritif"]  # Ajouter les tiennes
```

### Modifier le thème Streamlit

Créer `.streamlit/config.toml` :
```toml
[theme]
primaryColor = "#4caf50"
backgroundColor = "#f6f8f7"
secondaryBackgroundColor = "#ffffff"
textColor = "#2d4d36"
font = "sans serif"
```

---

## 📊 Prochaines étapes

### Modules à créer (par priorité)

1. **Inventaire** (`src/modules/cuisine/inventaire.py`)
    - CRUD items
    - Alertes stock bas (avec IA)
    - Suggestions courses

2. **Batch Cooking** (`src/modules/cuisine/batch_cooking.py`)
    - Planification repas
    - Génération auto par IA
    - Export calendrier

3. **Courses** (`src/modules/cuisine/courses.py`)
    - Liste de courses
    - Optimisation par rayon (IA)
    - Export PDF

4. **Suivi Jules** (`src/modules/famille/suivi_jules.py`)
    - Suivi développement
    - Conseils IA adaptés à l'âge
    - Graphiques

5. **Routines** (`src/modules/famille/routines.py`)
    - Gestion routines
    - Rappels intelligents (IA)

### Améliorations

- [ ] Module Accueil avec dashboard
- [ ] Notifications push
- [ ] Export PDF pour recettes
- [ ] Import recettes depuis URL
- [ ] Synchronisation Google Calendar
- [ ] Mode offline
- [ ] Application mobile (Progressive Web App)

---

## 🚢 Déploiement Streamlit Cloud

1. Pusher sur GitHub
2. Se connecter sur [share.streamlit.io](https://share.streamlit.io)
3. Sélectionner le repo
4. Configurer les secrets :

```toml
DATABASE_URL = "postgresql://user:pass@host:5432/db"
SECRET_KEY = "ton-uuid"
WEATHER_API_KEY = "ta_cle"
ENABLE_AI = false  # Ou héberger Ollama séparément
```

5. Déployer !

---

## 🤝 Contribution

```bash
# Créer une branche
git checkout -b feature/nouvelle-feature

# Faire les modifs
# ...

# Tester
make test
make lint

# Commit
git add .
git commit -m "feat: description"

# Push
git push origin feature/nouvelle-feature
```

---

## 📞 Support

- **GitHub Issues** : Pour les bugs
- **GitHub Discussions** : Pour les questions
- **Documentation** : Dans `docs/`

---

**🎉 Félicitations ! Tu as maintenant une application moderne et complète prête à l'emploi !**

L'agent IA est intégré partout et prêt à réduire la charge mentale. 🤖💚