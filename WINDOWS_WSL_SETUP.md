# 🪟 Guide d'installation Windows/WSL

## Prérequis

### 1. Installer WSL2

```powershell
# Dans PowerShell en administrateur
wsl --install
wsl --set-default-version 2
```

### 2. Installer Ubuntu sur WSL

```powershell
wsl --install -d Ubuntu-22.04
```

### 3. Installer Docker Desktop

1. Télécharger depuis [docker.com](https://www.docker.com/products/docker-desktop/)
2. Installer et redémarrer
3. Dans Docker Desktop Settings :
    - ✅ Activer "Use the WSL 2 based engine"
    - ✅ Dans Resources > WSL Integration : activer Ubuntu

---

## Installation dans WSL

### 1. Ouvrir le terminal WSL

```bash
# Ouvrir Ubuntu depuis le menu démarrer
# OU
wsl
```

### 2. Mettre à jour le système

```bash
sudo apt update && sudo apt upgrade -y
```

### 3. Installer les dépendances de base

```bash
# Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Curl
sudo apt install -y curl

# Build essentials
sudo apt install -y build-essential libpq-dev
```

### 4. Installer Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -

# Ajouter au PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Vérifier
poetry --version
```

### 5. Cloner le projet

```bash
# Depuis ton dossier de travail WSL
cd ~
git clone <ton-repo> assistant-matanne-v2
cd assistant-matanne-v2
```

### 6. Créer le fichier .env

```bash
# Copier le template
cp .env.example .env

# Éditer avec nano ou vim
nano .env
```

**Configuration minimale dans `.env` :**
```env
POSTGRES_PASSWORD=matanne_secret_2024
DATABASE_URL=postgresql://matanne:matanne_secret_2024@localhost:5432/matanne
ENABLE_AI=True
```

### 7. Rendre le script exécutable

```bash
chmod +x scripts/start.sh
```

### 8. Lancer le script de démarrage

```bash
bash scripts/start.sh
```

Le script va :
- ✅ Vérifier Poetry
- ✅ Vérifier Docker
- ✅ Installer les dépendances
- ✅ Démarrer PostgreSQL
- ✅ Créer la base de données
- ✅ Charger les données de démo (optionnel)

### 9. Démarrer l'application

```bash
make run

# OU
poetry run streamlit run src/app.py
```

L'application sera accessible sur : **http://localhost:8501**

---

## Commandes utiles

```bash
# Démarrer PostgreSQL
make docker-db

# Arrêter PostgreSQL
make docker-db-stop

# Voir les logs PostgreSQL
docker compose logs -f postgres

# Réinitialiser la base
make reset-db

# Lancer les tests
make test

# Voir l'état de Docker
docker compose ps
```

---

## 🐛 Dépannage

### Problème : "docker: command not found"

**Solution :**
```bash
# Vérifier que Docker Desktop est démarré
# Vérifier l'intégration WSL dans Docker Desktop Settings
```

### Problème : "poetry: command not found"

**Solution :**
```bash
# Réinstaller Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Ajouter au PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Problème : "alembic: No module named alembic.__main__"

**Solution :**
```bash
# Réinstaller les dépendances
poetry install --no-root
poetry install
```

### Problème : "Can't connect to PostgreSQL"

**Solution :**
```bash
# Attendre que PostgreSQL démarre complètement
docker compose logs postgres

# Vérifier que le port 5432 n'est pas utilisé
netstat -an | grep 5432

# Redémarrer PostgreSQL
docker compose restart postgres
```

### Problème : Permission denied sur les scripts

**Solution :**
```bash
# Rendre les scripts exécutables
chmod +x scripts/*.sh
```

---

## 💡 Astuces Windows/WSL

### Accéder aux fichiers WSL depuis Windows

```
\\wsl$\Ubuntu-22.04\home\<ton-user>\assistant-matanne-v2
```

### Accéder aux fichiers Windows depuis WSL

```bash
cd /mnt/c/Users/<ton-user>/Documents
```

### Utiliser IntelliJ avec WSL

1. **File** > **Settings** > **Build, Execution, Deployment** > **Python Interpreter**
2. Cliquer sur ⚙️ > **Add**
3. Sélectionner **WSL**
4. Sélectionner l'interpréteur Poetry : `~/.cache/pypoetry/virtualenvs/...`

### Ouvrir le projet dans VSCode

```bash
# Depuis WSL
code .
```

---

## 🚀 Workflow recommandé

1. **Démarrer Docker Desktop** (Windows)
2. **Ouvrir terminal WSL** (Ubuntu)
3. **Naviguer vers le projet**
   ```bash
   cd ~/assistant-matanne-v2
   ```
4. **Démarrer PostgreSQL** (si pas déjà fait)
   ```bash
   make docker-db
   ```
5. **Lancer l'app**
   ```bash
   make run
   ```
6. **Ouvrir le navigateur** : http://localhost:8501

---

## 📚 Ressources

- [Documentation WSL](https://docs.microsoft.com/en-us/windows/wsl/)
- [Docker Desktop WSL2](https://docs.docker.com/desktop/windows/wsl/)
- [Poetry Documentation](https://python-poetry.org/docs/)

---

## ✅ Checklist de vérification

- [ ] WSL2 installé et configuré
- [ ] Docker Desktop installé et démarré
- [ ] Intégration WSL activée dans Docker Desktop
- [ ] Poetry installé dans WSL
- [ ] Fichier `.env` créé et configuré
- [ ] PostgreSQL démarre avec `make docker-db`
- [ ] Base de données initialisée avec `make init-db`
- [ ] Application se lance avec `make run`

Si tous les points sont cochés, tu es prêt ! 🎉