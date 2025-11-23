"""
Script de seed minimaliste - Version qui fonctionne à coup sûr
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, date, timedelta
from src.core.database import get_db_context
from src.core.models import (
    Ingredient, Recipe, RecipeIngredient, InventoryItem,
    ChildProfile, User, UserProfile
)

print("🌱 Seed minimaliste - Données de base")
print("=" * 50)

# 1. Utilisateur
print("\n1. Création utilisateur...")
with get_db_context() as db:
    user = User(username="Anne", email="anne@matanne.app")
    db.add(user)
    db.flush()

    profile = UserProfile(
        user_id=user.id,
        profile_name="Anne",
        role="parent",
        is_active=True
    )
    db.add(profile)
print("✅ Utilisateur créé")

# 2. Ingrédients de base
print("\n2. Création ingrédients...")
with get_db_context() as db:
    ingredients = [
        Ingredient(name="Tomates", unit="kg", category="Légumes"),
        Ingredient(name="Pâtes", unit="g", category="Féculents"),
        Ingredient(name="Fromage", unit="g", category="Laitier"),
        Ingredient(name="Oeufs", unit="pcs", category="Protéines"),
        Ingredient(name="Lait", unit="L", category="Laitier"),
    ]
    for ing in ingredients:
        db.add(ing)
print("✅ 5 ingrédients créés")

# 3. Une recette simple
print("\n3. Création recette...")
with get_db_context() as db:
    recipe = Recipe(
        name="Pâtes à la tomate",
        category="Plat",
        instructions="Cuire les pâtes, ajouter la sauce",
        prep_time=10,
        cook_time=15,
        servings=4
    )
    db.add(recipe)
    db.flush()

    # Récupérer les IDs des ingrédients
    pates = db.query(Ingredient).filter(Ingredient.name == "Pâtes").first()
    tomates = db.query(Ingredient).filter(Ingredient.name == "Tomates").first()

    db.add(RecipeIngredient(recipe_id=recipe.id, ingredient_id=pates.id, quantity=400, unit="g"))
    db.add(RecipeIngredient(recipe_id=recipe.id, ingredient_id=tomates.id, quantity=0.5, unit="kg"))
print("✅ Recette créée")

# 4. Inventaire
print("\n4. Création inventaire...")
with get_db_context() as db:
    pates = db.query(Ingredient).filter(Ingredient.name == "Pâtes").first()
    tomates = db.query(Ingredient).filter(Ingredient.name == "Tomates").first()
    lait = db.query(Ingredient).filter(Ingredient.name == "Lait").first()

    db.add(InventoryItem(ingredient_id=pates.id, quantity=500, min_quantity=200, location="Placard"))
    db.add(InventoryItem(ingredient_id=tomates.id, quantity=2, min_quantity=1, location="Frigo"))
    db.add(InventoryItem(ingredient_id=lait.id, quantity=0.3, min_quantity=1, location="Frigo"))
print("✅ Inventaire créé")

# 5. Jules
print("\n5. Création profil Jules...")
with get_db_context() as db:
    jules = ChildProfile(
        name="Jules",
        birth_date=date(2024, 6, 22),
        notes="Notre petit bout de chou ❤️"
    )
    db.add(jules)
print("✅ Jules créé")

print("\n" + "=" * 50)
print("✅ SEED TERMINÉ AVEC SUCCÈS")
print("=" * 50)
print("\nDonnées créées:")
print("  • 1 utilisateur")
print("  • 5 ingrédients")
print("  • 1 recette")
print("  • 3 articles en stock")
print("  • 1 enfant (Jules)")
print("\n🚀 Lance l'app: poetry run streamlit run src/app.py")