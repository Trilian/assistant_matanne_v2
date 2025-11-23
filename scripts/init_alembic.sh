#!/bin/bash

# Script d'initialisation Alembic
# Crée la structure et la première migration

set -e

echo "🔧 Initialisation d'Alembic..."

# Créer le répertoire alembic s'il n'existe pas
if [ ! -d "alembic" ]; then
    echo "📁 Création du répertoire alembic/"
    alembic init alembic
    echo "✅ Répertoire créé"
else
    echo "✅ Répertoire alembic/ existe déjà"
fi

# Créer le répertoire versions s'il n'existe pas
mkdir -p alembic/versions

echo ""
echo "🔄 Configuration d'Alembic..."

# Vérifier si env.py existe
if [ -f "alembic/env.py" ]; then
    echo "⚠️  env.py existe déjà - vérifier la configuration manuellement"
else
    echo "✅ Utiliser le env.py fourni"
fi

echo ""
echo "📝 Création de la migration initiale..."

# Créer la première migration
echo "Commande à exécuter : alembic revision --autogenerate -m 'Initial schema'"
echo ""
echo "OU"
echo ""
echo "Si tu as déjà le fichier 001_initial_schema.py, lancer :"
echo "  alembic upgrade head"

echo ""
echo "✅ Initialisation terminée"
echo ""
echo "📚 Commandes utiles :"
echo "  alembic upgrade head         # Appliquer toutes les migrations"
echo "  alembic downgrade -1         # Annuler la dernière migration"
echo "  alembic current              # Voir la version actuelle"
echo "  alembic history              # Voir l'historique"
echo "  alembic revision --autogenerate -m 'message'  # Créer une nouvelle migration"