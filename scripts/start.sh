#!/bin/bash

# Script de démarrage pour WSL/Windows
# Usage: bash scripts/start.sh

set -e

echo "🚀 Démarrage de l'Assistant MaTanne v2"
echo "======================================"
echo ""

# Couleurs
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Vérifier que Poetry est installé
echo -e "${YELLOW}1. Vérification de Poetry...${NC}"
if ! command -v poetry &> /dev/null; then
    echo -e "${RED}❌ Poetry n'est pas installé${NC}"
    echo "Installe-le avec : curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi
echo -e "${GREEN}✅ Poetry OK${NC}"
echo ""

# 2. Vérifier que Docker est en cours d'exécution
echo -e "${YELLOW}2. Vérification de Docker...${NC}"
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker n'est pas démarré${NC}"
    echo "Lance Docker Desktop ou démarre le service Docker"
    exit 1
fi
echo -e "${GREEN}✅ Docker OK${NC}"
echo ""

# 3. Installer les dépendances
echo -e "${YELLOW}3. Installation des dépendances...${NC}"
poetry install
echo -e "${GREEN}✅ Dépendances installées${NC}"
echo ""

# 4. Vérifier le fichier .env
echo -e "${YELLOW}4. Vérification du fichier .env...${NC}"
if [ ! -f .env ]; then
    echo -e "${RED}❌ Fichier .env manquant${NC}"
    echo "Copie .env.example vers .env et configure-le"
    cp .env.example .env 2>/dev/null || true
    echo -e "${YELLOW}⚠️  Fichier .env créé, configure-le avant de continuer${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Fichier .env présent${NC}"
echo ""

# 5. Démarrer PostgreSQL
echo -e "${YELLOW}5. Démarrage de PostgreSQL...${NC}"
docker compose up -d postgres
echo "⏳ Attente de 15 secondes pour que PostgreSQL démarre..."
sleep 15
echo -e "${GREEN}✅ PostgreSQL démarré${NC}"
echo ""

# 6. Vérifier la connexion à la base
echo -e "${YELLOW}6. Vérification de la connexion DB...${NC}"
if docker compose exec -T postgres pg_isready -U matanne > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Base de données accessible${NC}"
else
    echo -e "${RED}❌ Impossible de se connecter à la base${NC}"
    echo "Vérifie les logs avec : docker compose logs postgres"
    exit 1
fi
echo ""

# 7. Initialiser la base de données
echo -e "${YELLOW}7. Initialisation de la base de données...${NC}"
poetry run alembic upgrade head
echo -e "${GREEN}✅ Base initialisée${NC}"
echo ""

# 8. Charger les données de démo (optionnel)
echo -e "${YELLOW}8. Charger les données de démo ? (o/n)${NC}"
read -r response
if [[ "$response" =~ ^([oO][uU][iI]|[oO]|[yY][eE][sS]|[yY])$ ]]; then
    poetry run python scripts/seed_data.py
    echo -e "${GREEN}✅ Données de démo chargées${NC}"
else
    echo "⏭️  Données de démo ignorées"
fi
echo ""

# 9. Démarrer l'application
echo -e "${GREEN}======================================"
echo "🎉 Tout est prêt !"
echo "======================================"
echo ""
echo "Pour démarrer l'application :"
echo "  make run"
echo ""
echo "Ou directement :"
echo "  poetry run streamlit run src/app.py"
echo ""
echo -e "${NC}"