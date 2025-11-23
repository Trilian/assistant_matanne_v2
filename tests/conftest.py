"""
Configuration pytest - Fixtures globales
"""

import pytest
import sys
from pathlib import Path

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.core.models import Base
from src.core.config import settings


# ===================================
# CONFIGURATION BASE DE DONNÉES TEST
# ===================================

# URL de test (utilise une DB séparée)
TEST_DATABASE_URL = settings.DATABASE_URL.replace("/matanne", "/matanne_test")


@pytest.fixture(scope="session")
def test_engine():
    """Crée un engine pour les tests"""
    engine = create_engine(
        TEST_DATABASE_URL,
        echo=False,
        pool_pre_ping=True
    )

    # Créer toutes les tables
    Base.metadata.create_all(engine)

    yield engine

    # Nettoyer après tous les tests
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine):
    """
    Crée une session de DB pour chaque test
    Rollback automatique après chaque test
    """
    connection = test_engine.connect()
    transaction = connection.begin()

    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


# ===================================
# FIXTURES AGENT IA
# ===================================

@pytest.fixture
def mock_agent_ia(monkeypatch):
    """Mock de l'agent IA pour les tests sans Ollama"""
    from src.core.ai_agent import AgentIA

    class MockAgentIA(AgentIA):
        async def _call_ollama(self, prompt, system_prompt="", temperature=0.7, max_tokens=500):
            """Retourne une réponse mockée"""
            return '{"nom": "Recette Test", "ingredients": ["test1", "test2"], "faisabilite": 85}'

    return MockAgentIA()


# ===================================
# FIXTURES DONNÉES DE TEST
# ===================================

@pytest.fixture
def test_user(db_session):
    """Crée un utilisateur de test"""
    from src.core.models import User

    user = User(
        username="test_user",
        email="test@example.com",
        settings={"theme": "light"}
    )
    db_session.add(user)
    db_session.commit()

    return user


@pytest.fixture
def test_child(db_session):
    """Crée un profil enfant de test"""
    from src.core.models import ChildProfile
    from datetime import date

    child = ChildProfile(
        name="Test Jules",
        birth_date=date(2024, 6, 22)
    )
    db_session.add(child)
    db_session.commit()

    return child


# ===================================
# UTILITAIRES
# ===================================

@pytest.fixture
def clean_database(db_session):
    """Nettoie complètement la base entre les tests"""
    from src.core.models import (
        Recipe, Ingredient, InventoryItem, User,
        Project, ChildProfile, Routine
    )

    # Supprimer toutes les données
    for model in [Recipe, InventoryItem, Ingredient, User, Project, ChildProfile, Routine]:
        db_session.query(model).delete()

    db_session.commit()


@pytest.fixture
def sample_data(db_session):
    """Charge un jeu de données complet de test"""
    from src.core.models import (
        User, Ingredient, Recipe, RecipeIngredient,
        InventoryItem, ChildProfile
    )
    from datetime import date

    # User
    user = User(username="anne", email="anne@test.com")
    db_session.add(user)

    # Child
    child = ChildProfile(name="Jules", birth_date=date(2024, 6, 22))
    db_session.add(child)

    # Ingredients
    ing1 = Ingredient(name="Tomates", unit="pcs", category="Légumes")
    ing2 = Ingredient(name="Pâtes", unit="g", category="Féculents")
    ing3 = Ingredient(name="Fromage", unit="g", category="Laitier")

    db_session.add_all([ing1, ing2, ing3])
    db_session.flush()

    # Recipe
    recipe = Recipe(
        name="Pâtes tomate",
        category="Plat",
        instructions="Cuire et mélanger",
        prep_time=10,
        cook_time=15
    )
    db_session.add(recipe)
    db_session.flush()

    # Recipe ingredients
    rec_ing1 = RecipeIngredient(
        recipe_id=recipe.id,
        ingredient_id=ing1.id,
        quantity=3
    )
    rec_ing2 = RecipeIngredient(
        recipe_id=recipe.id,
        ingredient_id=ing2.id,
        quantity=400
    )
    db_session.add_all([rec_ing1, rec_ing2])

    # Inventory
    inv1 = InventoryItem(ingredient_id=ing1.id, quantity=5)
    inv2 = InventoryItem(ingredient_id=ing2.id, quantity=500)
    inv3 = InventoryItem(ingredient_id=ing3.id, quantity=1, min_quantity=2)

    db_session.add_all([inv1, inv2, inv3])

    db_session.commit()

    return {
        "user": user,
        "child": child,
        "ingredients": [ing1, ing2, ing3],
        "recipe": recipe,
        "inventory": [inv1, inv2, inv3]
    }


# ===================================
# MARKERS
# ===================================

def pytest_configure(config):
    """Configuration des markers personnalisés"""
    config.addinivalue_line(
        "markers", "slow: marque les tests lents"
    )
    config.addinivalue_line(
        "markers", "integration: tests d'intégration"
    )
    config.addinivalue_line(
        "markers", "ai: tests nécessitant Ollama"
    )
    config.addinivalue_line(
        "markers", "db: tests nécessitant la base de données"
    )


# ===================================
# SKIP CONDITIONS
# ===================================

@pytest.fixture
def skip_if_no_ollama():
    """Skip le test si Ollama n'est pas disponible"""
    import httpx

    try:
        response = httpx.get(f"{settings.OLLAMA_URL}/api/tags", timeout=2)
        if response.status_code != 200:
            pytest.skip("Ollama non disponible")
    except Exception:
        pytest.skip("Ollama non disponible")


@pytest.fixture
def skip_if_no_db():
    """Skip le test si la DB n'est pas disponible"""
    from src.core.database import check_connection

    if not check_connection():
        pytest.skip("Base de données non disponible")