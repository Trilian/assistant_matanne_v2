"""
Script de seed - Données de démonstration
Remplit la base avec des données réalistes pour tester l'application
"""

import sys
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, date, timedelta
from src.core.database import get_db_context
from src.core.models import (
    User, UserProfile, Notification,
    Ingredient, Recipe, RecipeIngredient, InventoryItem, BatchMeal, ShoppingList,
    ChildProfile, WellbeingEntry, Routine, RoutineTask,
    Project, ProjectTask, GardenItem, GardenLog,
    CalendarEvent, WeatherLog
)


def clear_database():
    """Nettoie toutes les données (optionnel)"""
    print("🧹 Nettoyage de la base...")

    with get_db_context() as db:
        # Supprimer dans l'ordre inverse des dépendances
        db.query(GardenLog).delete()
        db.query(GardenItem).delete()
        db.query(ProjectTask).delete()
        db.query(Project).delete()
        db.query(RoutineTask).delete()
        db.query(Routine).delete()
        db.query(WellbeingEntry).delete()
        db.query(ChildProfile).delete()
        db.query(ShoppingList).delete()
        db.query(BatchMeal).delete()
        db.query(RecipeIngredient).delete()
        db.query(InventoryItem).delete()
        db.query(Recipe).delete()
        db.query(Ingredient).delete()
        db.query(CalendarEvent).delete()
        db.query(WeatherLog).delete()
        db.query(Notification).delete()
        db.query(UserProfile).delete()
        db.query(User).delete()

        db.commit()

    print("✅ Base nettoyée")


def seed_users():
    """Crée les utilisateurs"""
    print("👤 Création des utilisateurs...")

    with get_db_context() as db:
        # Utilisateur principal
        anne = User(
            username="Anne",
            email="anne@matanne.app",
            settings={
                "theme": "light",
                "notifications": True,
                "language": "fr"
            }
        )
        db.add(anne)
        db.flush()

        # Profils
        profil_anne = UserProfile(
            user_id=anne.id,
            profile_name="Anne (Maman)",
            role="parent",
            preferences={"favoris": ["cuisine", "jardin"]},
            is_active=True
        )

        profil_mathieu = UserProfile(
            user_id=anne.id,
            profile_name="Mathieu (Papa)",
            role="parent",
            preferences={"favoris": ["projets", "jardin"]},
            is_active=True
        )

        db.add_all([profil_anne, profil_mathieu])
        db.commit()

        print(f"✅ Utilisateur '{anne.username}' créé avec 2 profils")
        return anne.id


def seed_ingredients():
    """Crée les ingrédients de base"""
    print("🥕 Création des ingrédients...")

    ingredients_data = [
        # Légumes
        ("Tomates", "kg", "Légumes"),
        ("Carottes", "kg", "Légumes"),
        ("Oignons", "kg", "Légumes"),
        ("Pommes de terre", "kg", "Légumes"),
        ("Courgettes", "kg", "Légumes"),
        ("Poivrons", "pcs", "Légumes"),

        # Féculents
        ("Pâtes", "g", "Féculents"),
        ("Riz", "g", "Féculents"),
        ("Farine", "g", "Féculents"),
        ("Pain", "pcs", "Féculents"),

        # Protéines
        ("Poulet", "g", "Protéines"),
        ("Boeuf haché", "g", "Protéines"),
        ("Oeufs", "pcs", "Protéines"),
        ("Saumon", "g", "Protéines"),

        # Laitier
        ("Lait", "L", "Laitier"),
        ("Fromage râpé", "g", "Laitier"),
        ("Yaourts", "pcs", "Laitier"),
        ("Beurre", "g", "Laitier"),
        ("Crème fraîche", "mL", "Laitier"),

        # Fruits
        ("Pommes", "pcs", "Fruits"),
        ("Bananes", "pcs", "Fruits"),
        ("Oranges", "pcs", "Fruits"),

        # Épices et autres
        ("Sel", "g", "Épices"),
        ("Poivre", "g", "Épices"),
        ("Huile d'olive", "mL", "Huiles"),
        ("Ail", "pcs", "Épices"),
    ]

    with get_db_context() as db:
        for nom, unite, categorie in ingredients_data:
            ingredient = Ingredient(name=nom, unit=unite, category=categorie)
            db.add(ingredient)

        db.commit()

    print(f"✅ {len(ingredients_data)} ingrédients créés")


def seed_recipes():
    """Crée des recettes d'exemple"""
    print("📖 Création des recettes...")

    with get_db_context() as db:
        # Recette 1 : Pâtes à la tomate
        r1 = Recipe(
            name="Pâtes à la tomate",
            category="Plat",
            instructions="1. Faire cuire les pâtes\n2. Préparer la sauce tomate\n3. Mélanger et servir",
            prep_time=10,
            cook_time=15,
            servings=4,
            difficulty="Facile"
        )
        db.add(r1)
        db.flush()

        # Ingrédients pâtes tomate
        ing_pates = db.query(Ingredient).filter(Ingredient.name == "Pâtes").first()
        ing_tomates = db.query(Ingredient).filter(Ingredient.name == "Tomates").first()
        ing_ail = db.query(Ingredient).filter(Ingredient.name == "Ail").first()

        db.add_all([
            RecipeIngredient(recipe_id=r1.id, ingredient_id=ing_pates.id, quantity=400, unit="g"),
            RecipeIngredient(recipe_id=r1.id, ingredient_id=ing_tomates.id, quantity=0.5, unit="kg"),
            RecipeIngredient(recipe_id=r1.id, ingredient_id=ing_ail.id, quantity=2, unit="pcs"),
        ])

        # Recette 2 : Poulet rôti
        r2 = Recipe(
            name="Poulet rôti aux légumes",
            category="Plat",
            instructions="1. Préparer le poulet\n2. Couper les légumes\n3. Enfourner 45min à 180°C",
            prep_time=15,
            cook_time=45,
            servings=4,
            difficulty="Moyen"
        )
        db.add(r2)
        db.flush()

        ing_poulet = db.query(Ingredient).filter(Ingredient.name == "Poulet").first()
        ing_carottes = db.query(Ingredient).filter(Ingredient.name == "Carottes").first()
        ing_pdt = db.query(Ingredient).filter(Ingredient.name == "Pommes de terre").first()

        db.add_all([
            RecipeIngredient(recipe_id=r2.id, ingredient_id=ing_poulet.id, quantity=1200, unit="g"),
            RecipeIngredient(recipe_id=r2.id, ingredient_id=ing_carottes.id, quantity=0.5, unit="kg"),
            RecipeIngredient(recipe_id=r2.id, ingredient_id=ing_pdt.id, quantity=0.6, unit="kg"),
        ])

        # Recette 3 : Omelette
        r3 = Recipe(
            name="Omelette nature",
            category="Plat",
            instructions="1. Battre les oeufs\n2. Cuire à la poêle\n3. Servir chaud",
            prep_time=5,
            cook_time=10,
            servings=2,
            difficulty="Facile"
        )
        db.add(r3)
        db.flush()

        ing_oeufs = db.query(Ingredient).filter(Ingredient.name == "Oeufs").first()
        ing_beurre = db.query(Ingredient).filter(Ingredient.name == "Beurre").first()

        db.add_all([
            RecipeIngredient(recipe_id=r3.id, ingredient_id=ing_oeufs.id, quantity=4, unit="pcs"),
            RecipeIngredient(recipe_id=r3.id, ingredient_id=ing_beurre.id, quantity=20, unit="g"),
        ])

        # Recette 4 : Gratin dauphinois (générée par IA)
        r4 = Recipe(
            name="Gratin dauphinois",
            category="Accompagnement",
            instructions="1. Émincer les pommes de terre\n2. Préparer la crème\n3. Enfourner 1h",
            prep_time=20,
            cook_time=60,
            servings=6,
            difficulty="Moyen",
            ai_generated=True,
            ai_score=92.5
        )
        db.add(r4)
        db.flush()

        ing_creme = db.query(Ingredient).filter(Ingredient.name == "Crème fraîche").first()
        ing_fromage = db.query(Ingredient).filter(Ingredient.name == "Fromage râpé").first()

        db.add_all([
            RecipeIngredient(recipe_id=r4.id, ingredient_id=ing_pdt.id, quantity=1.0, unit="kg"),
            RecipeIngredient(recipe_id=r4.id, ingredient_id=ing_creme.id, quantity=300, unit="mL"),
            RecipeIngredient(recipe_id=r4.id, ingredient_id=ing_fromage.id, quantity=150, unit="g"),
        ])

        db.commit()

    print("✅ 4 recettes créées (dont 1 par IA)")


def seed_inventory():
    """Remplit l'inventaire"""
    print("📦 Remplissage de l'inventaire...")

    inventory_data = [
        ("Tomates", 2.5, 1.0, "Frigo"),
        ("Carottes", 1.2, 0.5, "Frigo"),
        ("Oignons", 0.8, 0.3, "Placard"),
        ("Pommes de terre", 3.0, 1.0, "Placard"),
        ("Pâtes", 800, 200, "Placard"),
        ("Riz", 500, 200, "Placard"),
        ("Poulet", 0, 500, "Congélateur"),  # Stock vide
        ("Oeufs", 6, 6, "Frigo"),
        ("Lait", 0.5, 1.0, "Frigo"),  # Stock bas
        ("Fromage râpé", 50, 100, "Frigo"),  # Stock bas
        ("Huile d'olive", 500, 100, "Placard"),
    ]

    with get_db_context() as db:
        for nom, qty, seuil, location in inventory_data:
            ingredient = db.query(Ingredient).filter(Ingredient.name == nom).first()
            if ingredient:
                item = InventoryItem(
                    ingredient_id=ingredient.id,
                    quantity=qty,
                    min_quantity=seuil,
                    location=location
                )
                db.add(item)

        db.commit()

    print(f"✅ {len(inventory_data)} articles ajoutés à l'inventaire")


def seed_batch_meals():
    """Planifie des repas"""
    print("🍽️ Planification de repas...")

    with get_db_context() as db:
        today = date.today()

        # Récupérer les recettes
        recettes = db.query(Recipe).all()

        for i, recette in enumerate(recettes[:7]):  # 7 jours
            batch = BatchMeal(
                recipe_id=recette.id,
                scheduled_date=today + timedelta(days=i),
                portions=4,
                status="à faire" if i >= 2 else "terminé",
                ai_planned=(i % 2 == 0)  # Un repas sur deux par IA
            )
            db.add(batch)

        db.commit()

    print("✅ 7 repas planifiés")


def seed_child_and_family():
    """Crée Jules et ses données"""
    print("👶 Création du profil de Jules...")

    with get_db_context() as db:
        # Jules
        jules = ChildProfile(
            name="Jules",
            birth_date=date(2024, 6, 22),
            notes="Notre petit bout de chou ❤️"
        )
        db.add(jules)
        db.flush()

        # Entrées bien-être
        for i in range(7):
            entry = WellbeingEntry(
                child_id=jules.id,
                date=date.today() - timedelta(days=i),
                mood=["😊 Bien", "😐 Moyen", "😊 Bien"][i % 3],
                sleep_hours=7.5 + (i % 3) * 0.5,
                activity=["Crèche", "Promenade", "Jeux à la maison"][i % 3],
                notes=f"Journée du {(date.today() - timedelta(days=i)).strftime('%d/%m')}"
            )
            db.add(entry)

        # Routine
        routine = Routine(
            child_id=jules.id,
            name="Routine du soir",
            description="Routine avant le coucher",
            frequency="quotidien",
            is_active=True
        )
        db.add(routine)
        db.flush()

        # Tâches de routine
        taches = [
            ("Bain", "19:00", "terminé"),
            ("Dîner", "19:30", "terminé"),
            ("Brossage dents", "20:00", "à faire"),
            ("Histoire", "20:15", "à faire"),
            ("Dodo", "20:30", "à faire"),
        ]

        for nom, heure, statut in taches:
            task = RoutineTask(
                routine_id=routine.id,
                task_name=nom,
                scheduled_time=heure,
                status=statut
            )
            db.add(task)

        db.commit()

    print("✅ Jules et sa routine créés")


def seed_projects():
    """Crée des projets maison"""
    print("🏗️ Création des projets...")

    with get_db_context() as db:
        # Projet 1
        p1 = Project(
            name="Aménagement jardin",
            description="Créer un potager et une zone détente",
            category="Extérieur",
            start_date=date(2025, 4, 1),
            end_date=date(2025, 12, 31),
            priority="haute",
            status="en cours",
            progress=35
        )
        db.add(p1)
        db.flush()

        db.add_all([
            ProjectTask(project_id=p1.id, task_name="Préparer le sol", status="terminé", due_date=date(2025, 4, 15)),
            ProjectTask(project_id=p1.id, task_name="Acheter graines", status="terminé", due_date=date(2025, 5, 1)),
            ProjectTask(project_id=p1.id, task_name="Planter légumes", status="en cours", due_date=date(2025, 5, 15)),
            ProjectTask(project_id=p1.id, task_name="Installer arrosage", status="à faire", due_date=date(2025, 6, 1)),
        ])

        # Projet 2
        p2 = Project(
            name="Rénovation chambre",
            description="Refaire la peinture et changer les meubles",
            category="Intérieur",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            priority="moyenne",
            status="à faire",
            progress=0
        )
        db.add(p2)
        db.flush()

        db.add_all([
            ProjectTask(project_id=p2.id, task_name="Choisir couleurs", status="à faire"),
            ProjectTask(project_id=p2.id, task_name="Acheter peinture", status="à faire"),
        ])

        db.commit()

    print("✅ 2 projets créés")


def seed_garden():
    """Crée le jardin"""
    print("🌱 Plantation du jardin...")

    with get_db_context() as db:
        plantes = [
            ("Tomates cerises", "Légume", date(2025, 5, 1), date(2025, 8, 1), 3, 2),
            ("Courgettes", "Légume", date(2025, 5, 10), date(2025, 7, 15), 2, 3),
            ("Basilic", "Aromatique", date(2025, 4, 20), None, 1, 1),
            ("Fraisiers", "Fruit", date(2025, 4, 1), date(2025, 6, 15), 5, 2),
        ]

        for nom, cat, plant, harvest, qty, water_freq in plantes:
            item = GardenItem(
                name=nom,
                category=cat,
                planting_date=plant,
                harvest_date=harvest,
                quantity=qty,
                watering_frequency_days=water_freq,
                last_watered=date.today() - timedelta(days=1)
            )
            db.add(item)
            db.flush()

            # Ajouter un log
            log = GardenLog(
                item_id=item.id,
                action="Arrosage",
                date=date.today() - timedelta(days=1),
                notes="Arrosage régulier"
            )
            db.add(log)

        db.commit()

    print("✅ 4 plantes ajoutées au jardin")


def seed_notifications(user_id: int):
    """Crée des notifications"""
    print("🔔 Création de notifications...")

    with get_db_context() as db:
        notifs = [
            ("Inventaire", "Stock bas : Lait, Fromage râpé", "haute", False),
            ("Batch Cooking", "Aucun repas planifié pour après-demain", "moyenne", False),
            ("Routines", "2 tâches du soir en attente", "basse", False),
            ("Jardin", "Les tomates ont besoin d'eau", "moyenne", True),
        ]

        for module, message, priority, read in notifs:
            notif = Notification(
                user_id=user_id,
                module=module,
                message=message,
                priority=priority,
                read=read
            )
            db.add(notif)

        db.commit()

    print(f"✅ {len(notifs)} notifications créées")


def main():
    """Point d'entrée principal"""
    print("=" * 60)
    print("🌱 SEED DATABASE - Assistant MaTanne v2")
    print("=" * 60)
    print()

    # Demander confirmation pour nettoyer
    response = input("⚠️  Nettoyer la base avant (supprime toutes les données) ? (o/N) : ")

    if response.lower() in ['o', 'oui', 'y', 'yes']:
        clear_database()
        print()

    # Seed
    user_id = seed_users()
    seed_ingredients()
    seed_recipes()
    seed_inventory()
    seed_batch_meals()
    seed_child_and_family()
    seed_projects()
    seed_garden()
    seed_notifications(user_id)

    print()
    print("=" * 60)
    print("✅ SEED TERMINÉ AVEC SUCCÈS")
    print("=" * 60)
    print()
    print("📊 Résumé des données créées :")
    print("  • 1 utilisateur (Anne)")
    print("  • 2 profils (Anne, Mathieu)")
    print("  • 26 ingrédients")
    print("  • 4 recettes (dont 1 IA)")
    print("  • 11 articles en inventaire")
    print("  • 7 repas planifiés")
    print("  • 1 enfant (Jules)")
    print("  • 7 entrées bien-être")
    print("  • 1 routine (5 tâches)")
    print("  • 2 projets (6 tâches)")
    print("  • 4 plantes au jardin")
    print("  • 4 notifications")
    print()
    print("🚀 Tu peux maintenant lancer l'application !")
    print("   make run")
    print()


if __name__ == "__main__":
    main()