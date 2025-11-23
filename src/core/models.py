"""
Modèles SQLAlchemy pour PostgreSQL
Tous les modèles de l'application
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Float, Boolean,
    ForeignKey, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
import enum

Base = declarative_base()


# ===================================
# ENUMS
# ===================================

class PrioriteEnum(str, enum.Enum):
    BASSE = "basse"
    MOYENNE = "moyenne"
    HAUTE = "haute"


class StatutEnum(str, enum.Enum):
    A_FAIRE = "à faire"
    EN_COURS = "en cours"
    TERMINE = "terminé"
    ANNULE = "annulé"


class HumeurEnum(str, enum.Enum):
    BIEN = "😊 Bien"
    MOYEN = "😐 Moyen"
    MAL = "😞 Mal"


# ===================================
# 👤 UTILISATEURS & PROFILS
# ===================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relations
    profiles: Mapped[List["UserProfile"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[List["Notification"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    profile_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(50))  # parent, enfant, autre
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    user: Mapped["User"] = relationship(back_populates="profiles")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(SQLEnum(PrioriteEnum), default=PrioriteEnum.MOYENNE)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    user: Mapped["User"] = relationship(back_populates="notifications")


# ===================================
# 🍲 CUISINE
# ===================================

class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    instructions: Mapped[Optional[str]] = mapped_column(Text)
    prep_time: Mapped[Optional[int]] = mapped_column(Integer)  # minutes
    cook_time: Mapped[Optional[int]] = mapped_column(Integer)
    servings: Mapped[int] = mapped_column(Integer, default=4)
    difficulty: Mapped[Optional[str]] = mapped_column(String(50))
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_score: Mapped[Optional[float]] = mapped_column(Float)  # Score de faisabilité IA
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relations
    ingredients: Mapped[List["RecipeIngredient"]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan"
    )
    batch_meals: Mapped[List["BatchMeal"]] = relationship(back_populates="recipe")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    unit: Mapped[str] = mapped_column(String(50))  # kg, L, pcs, etc.
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    recipes: Mapped[List["RecipeIngredient"]] = relationship(back_populates="ingredient")
    inventory_items: Mapped[List["InventoryItem"]] = relationship(back_populates="ingredient")


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"))
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id", ondelete="CASCADE"))
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(50))

    # Relations
    recipe: Mapped["Recipe"] = relationship(back_populates="ingredients")
    ingredient: Mapped["Ingredient"] = relationship(back_populates="recipes")


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id", ondelete="CASCADE"))
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    min_quantity: Mapped[float] = mapped_column(Float, default=1.0)  # Seuil alerte
    location: Mapped[Optional[str]] = mapped_column(String(100))  # frigo, placard, etc.
    expiry_date: Mapped[Optional[date]] = mapped_column(Date)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    ai_alert_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relations
    ingredient: Mapped["Ingredient"] = relationship(back_populates="inventory_items")


class ShoppingList(Base):
    __tablename__ = "shopping_lists"

    id: Mapped[int] = mapped_column(primary_key=True)
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredients.id", ondelete="CASCADE"))
    needed_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    priority: Mapped[str] = mapped_column(SQLEnum(PrioriteEnum), default=PrioriteEnum.MOYENNE)
    purchased: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_suggested: Mapped[bool] = mapped_column(Boolean, default=False)
    store_section: Mapped[Optional[str]] = mapped_column(String(100))  # Rayon
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    purchased_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relations
    ingredient: Mapped["Ingredient"] = relationship()


class BatchMeal(Base):
    __tablename__ = "batch_meals"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"))
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    portions: Mapped[int] = mapped_column(Integer, default=4)
    status: Mapped[str] = mapped_column(SQLEnum(StatutEnum), default=StatutEnum.A_FAIRE)
    ai_planned: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    recipe: Mapped["Recipe"] = relationship(back_populates="batch_meals")


# ===================================
# 👶 FAMILLE
# ===================================

class ChildProfile(Base):
    __tablename__ = "child_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    wellbeing_entries: Mapped[List["WellbeingEntry"]] = relationship(
        back_populates="child", cascade="all, delete-orphan"
    )
    routines: Mapped[List["Routine"]] = relationship(back_populates="child")


class WellbeingEntry(Base):
    __tablename__ = "wellbeing_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("child_profiles.id", ondelete="CASCADE")
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    mood: Mapped[str] = mapped_column(SQLEnum(HumeurEnum), nullable=False)
    sleep_hours: Mapped[Optional[float]] = mapped_column(Float)
    activity: Mapped[Optional[str]] = mapped_column(String(200))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    username: Mapped[Optional[str]] = mapped_column(String(100))  # Pour adultes
    ai_analysis: Mapped[Optional[dict]] = mapped_column(JSON)  # Analyse IA
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    child: Mapped[Optional["ChildProfile"]] = relationship(back_populates="wellbeing_entries")


class Routine(Base):
    __tablename__ = "routines"

    id: Mapped[int] = mapped_column(primary_key=True)
    child_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("child_profiles.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    frequency: Mapped[str] = mapped_column(String(50), default="quotidien")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_suggested: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    child: Mapped[Optional["ChildProfile"]] = relationship(back_populates="routines")
    tasks: Mapped[List["RoutineTask"]] = relationship(
        back_populates="routine", cascade="all, delete-orphan"
    )


class RoutineTask(Base):
    __tablename__ = "routine_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    routine_id: Mapped[int] = mapped_column(ForeignKey("routines.id", ondelete="CASCADE"))
    task_name: Mapped[str] = mapped_column(String(200), nullable=False)
    scheduled_time: Mapped[Optional[str]] = mapped_column(String(10))  # HH:MM
    status: Mapped[str] = mapped_column(SQLEnum(StatutEnum), default=StatutEnum.A_FAIRE)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    ai_reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relations
    routine: Mapped["Routine"] = relationship(back_populates="tasks")


# ===================================
# 🏡 MAISON
# ===================================

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    priority: Mapped[str] = mapped_column(SQLEnum(PrioriteEnum), default=PrioriteEnum.MOYENNE)
    status: Mapped[str] = mapped_column(SQLEnum(StatutEnum), default=StatutEnum.A_FAIRE)
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100%
    ai_priority_score: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relations
    tasks: Mapped[List["ProjectTask"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class ProjectTask(Base):
    __tablename__ = "project_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    task_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(SQLEnum(StatutEnum), default=StatutEnum.A_FAIRE)
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    estimated_duration: Mapped[Optional[int]] = mapped_column(Integer)  # minutes

    # Relations
    project: Mapped["Project"] = relationship(back_populates="tasks")


class GardenItem(Base):
    __tablename__ = "garden_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(100))  # Légume, Fruit, Fleur, etc.
    planting_date: Mapped[Optional[date]] = mapped_column(Date)
    harvest_date: Mapped[Optional[date]] = mapped_column(Date)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    location: Mapped[Optional[str]] = mapped_column(String(200))
    watering_frequency_days: Mapped[int] = mapped_column(Integer, default=2)
    last_watered: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    ai_suggestions: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relations
    logs: Mapped[List["GardenLog"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )


class GardenLog(Base):
    __tablename__ = "garden_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("garden_items.id", ondelete="CASCADE"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)  # arrosage, taille, etc.
    date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    weather_condition: Mapped[Optional[str]] = mapped_column(String(100))

    # Relations
    item: Mapped["GardenItem"] = relationship(back_populates="logs")


# ===================================
# 📅 PLANNING & MÉTÉO
# ===================================

class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    location: Mapped[Optional[str]] = mapped_column(String(200))
    category: Mapped[Optional[str]] = mapped_column(String(100))
    external_id: Mapped[Optional[str]] = mapped_column(String(500))  # ID Google Calendar
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class WeatherLog(Base):
    __tablename__ = "weather_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, unique=True)
    condition: Mapped[str] = mapped_column(String(100))  # sunny, rainy, cloudy, etc.
    temperature: Mapped[float] = mapped_column(Float)
    humidity: Mapped[Optional[int]] = mapped_column(Integer)
    wind_speed: Mapped[Optional[float]] = mapped_column(Float)
    precipitation: Mapped[Optional[float]] = mapped_column(Float)
    forecast_data: Mapped[Optional[dict]] = mapped_column(JSON)
    ai_tasks_suggested: Mapped[Optional[List[str]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ===================================
# 🤖 IA - Logs et historique
# ===================================

class AIInteraction(Base):
    __tablename__ = "ai_interactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    module: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    prompt: Mapped[str] = mapped_column(Text)
    response: Mapped[str] = mapped_column(Text)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    execution_time: Mapped[Optional[float]] = mapped_column(Float)  # secondes
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)