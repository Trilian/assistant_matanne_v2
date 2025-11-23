"""
Connexion PostgreSQL et gestion des sessions
"""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool
import logging

from src.core.config import settings
from src.core.models import Base

logger = logging.getLogger(__name__)


# ===================================
# CONFIGURATION ENGINE
# ===================================

def get_engine():
    """Crée l'engine PostgreSQL avec configuration optimisée"""

    engine_kwargs = {
        "echo": settings.DEBUG,
        "future": True,
    }

    # Configuration du pool de connexions
    if settings.ENV == "production":
        engine_kwargs["poolclass"] = QueuePool
        engine_kwargs["pool_size"] = 10
        engine_kwargs["max_overflow"] = 20
        engine_kwargs["pool_pre_ping"] = True  # Vérifier la connexion avant utilisation
        engine_kwargs["pool_recycle"] = 3600  # Recycler après 1h
    else:
        # En développement, pool plus simple
        engine_kwargs["poolclass"] = NullPool if settings.ENV == "test" else QueuePool
        engine_kwargs["pool_size"] = 5
        engine_kwargs["max_overflow"] = 10

    engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

    # Activer les contraintes de clés étrangères pour PostgreSQL
    @event.listens_for(engine, "connect")
    def set_postgresql_config(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("SET timezone='UTC'")
        cursor.close()

    return engine


# Engine global
engine = get_engine()

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)


# ===================================
# GESTION DES SESSIONS
# ===================================

def get_session() -> Session:
    """
    Obtenir une session de base de données
    À utiliser dans les fonctions normales
    """
    return SessionLocal()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager pour gérer automatiquement les sessions

    Usage:
        with get_db_context() as db:
            # Faire des opérations
            db.query(...)
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur base de données: {e}")
        raise
    finally:
        db.close()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency pour FastAPI/Streamlit
    À utiliser avec Depends() si nécessaire
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ===================================
# INITIALISATION & MIGRATIONS
# ===================================

def create_all_tables():
    """Crée toutes les tables (développement uniquement)"""
    logger.info("Création des tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tables créées")


def drop_all_tables():
    """Supprime toutes les tables (DANGER!)"""
    logger.warning("⚠️ SUPPRESSION de toutes les tables")
    Base.metadata.drop_all(bind=engine)
    logger.warning("✅ Tables supprimées")


def reset_database():
    """Reset complet de la base (développement uniquement)"""
    if settings.ENV == "production":
        raise RuntimeError("❌ Reset impossible en production!")

    logger.warning("🔄 Reset de la base de données...")
    drop_all_tables()
    create_all_tables()
    logger.info("✅ Base réinitialisée")


# ===================================
# VÉRIFICATIONS & SANTÉ
# ===================================

def check_connection() -> bool:
    """Vérifie que la connexion fonctionne"""
    try:
        with get_db_context() as db:
            db.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"❌ Connexion DB échouée: {e}")
        return False


def get_db_info() -> dict:
    """Informations sur la base de données"""
    try:
        with get_db_context() as db:
            result = db.execute("""
                SELECT 
                    version() as version,
                    current_database() as database,
                    current_user as user
            """).fetchone()

            return {
                "status": "connected",
                "version": result[0],
                "database": result[1],
                "user": result[2],
                "url": settings.DATABASE_URL.split("@")[1] if "@" in settings.DATABASE_URL else "hidden"
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# ===================================
# STREAMLIT CACHE
# ===================================

import streamlit as st
from functools import wraps


def cached_query(ttl: int = 300):
    """
    Décorateur pour cacher les requêtes dans Streamlit

    Args:
        ttl: Time to live en secondes (défaut: 5 minutes)

    Usage:
        @cached_query(ttl=600)
        def get_recipes():
            with get_db_context() as db:
                return db.query(Recipe).all()
    """
    def decorator(func):
        @wraps(func)
        @st.cache_data(ttl=ttl)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ===================================
# HELPERS SPÉCIFIQUES
# ===================================

def bulk_insert(model_class, data: list[dict]) -> int:
    """
    Insertion en masse efficace

    Args:
        model_class: Classe du modèle SQLAlchemy
        data: Liste de dictionnaires avec les données

    Returns:
        Nombre d'enregistrements insérés
    """
    with get_db_context() as db:
        objects = [model_class(**item) for item in data]
        db.bulk_save_objects(objects)
        return len(objects)


def bulk_update(model_class, data: list[dict]) -> int:
    """
    Mise à jour en masse

    Args:
        model_class: Classe du modèle
        data: Liste de dicts avec 'id' et les champs à mettre à jour

    Returns:
        Nombre d'enregistrements mis à jour
    """
    with get_db_context() as db:
        updated = 0
        for item in data:
            item_id = item.pop('id')
            db.query(model_class).filter(
                model_class.id == item_id
            ).update(item)
            updated += 1
        return updated


def execute_raw_sql(sql: str, params: dict = None) -> list:
    """
    Exécute du SQL brut (avec précaution!)

    Args:
        sql: Requête SQL
        params: Paramètres nommés

    Returns:
        Liste de résultats
    """
    with get_db_context() as db:
        result = db.execute(sql, params or {})
        return result.fetchall()


# ===================================
# CLEANUP
# ===================================

def cleanup_old_logs(days: int = 90):
    """
    Nettoie les anciens logs IA et interactions

    Args:
        days: Garder les logs des X derniers jours
    """
    from datetime import timedelta
    from src.core.models import AIInteraction

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    with get_db_context() as db:
        deleted = db.query(AIInteraction).filter(
            AIInteraction.created_at < cutoff_date
        ).delete()

        logger.info(f"🗑️ {deleted} logs IA supprimés (>{days} jours)")
        return deleted


def vacuum_database():
    """
    Optimise la base PostgreSQL (à lancer régulièrement)
    """
    if settings.ENV == "production":
        logger.info("🧹 VACUUM de la base de données...")
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute("VACUUM ANALYZE")
        logger.info("✅ VACUUM terminé")