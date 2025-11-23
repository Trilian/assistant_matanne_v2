FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Ajouter Poetry au PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Installation de Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY pyproject.toml poetry.lock* ./

# Installer les dépendances (production uniquement)
RUN poetry install --no-root --only main

# Copier le code source
COPY . .

# Installer l'application
RUN poetry install --only-root

# Créer les répertoires nécessaires
RUN mkdir -p /app/data/backups

# Utilisateur non-root pour la sécurité
RUN useradd -m -u 1000 matanne && \
    chown -R matanne:matanne /app
USER matanne

# Port Streamlit
EXPOSE 8501

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Commande par défaut
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]