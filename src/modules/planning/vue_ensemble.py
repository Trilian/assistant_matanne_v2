"""
Module Vue d'ensemble Planning
Dashboard global avec toutes les informations importantes
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict

from src.core.database import get_db_context
from src.core.models import (
    BatchMeal, Recipe, Project, RoutineTask, Routine,
    InventoryItem, Ingredient, CalendarEvent, GardenItem
)


# ===================================
# HELPERS
# ===================================

def get_dashboard_data() -> Dict:
    """Récupère toutes les données pour le dashboard"""
    with get_db_context() as db:
        today = date.today()
        week_end = today + timedelta(days=7)

        data = {
            # Repas
            "repas_semaine": db.query(BatchMeal).filter(
                BatchMeal.scheduled_date.between(today, week_end),
                BatchMeal.status == "à faire"
            ).count(),

            # Projets
            "projets_actifs": db.query(Project).filter(
                Project.status.in_(["à faire", "en cours"])
            ).count(),

            "projets_urgents": db.query(Project).filter(
                Project.status.in_(["à faire", "en cours"]),
                Project.end_date != None,
                Project.end_date <= week_end
            ).count(),

            # Routines
            "taches_jour": db.query(RoutineTask).join(Routine).filter(
                RoutineTask.status == "à faire",
                Routine.is_active == True
            ).count(),

            # Inventaire
            "stock_bas": db.query(InventoryItem).filter(
                InventoryItem.quantity < InventoryItem.min_quantity
            ).count(),

            # Événements
            "events_semaine": db.query(CalendarEvent).filter(
                CalendarEvent.start_date >= datetime.combine(today, datetime.min.time()),
                CalendarEvent.start_date <= datetime.combine(week_end, datetime.max.time())
            ).count(),

            # Jardin
            "plantes_arroser": db.query(GardenItem).filter(
                GardenItem.last_watered != None
            ).count()
        }

        return data


def get_prochaines_actions() -> list:
    """Liste les prochaines actions importantes"""
    actions = []

    with get_db_context() as db:
        today = date.today()

        # Repas non planifiés
        repas_3j = db.query(BatchMeal).filter(
            BatchMeal.scheduled_date.between(today, today + timedelta(days=3))
        ).count()

        if repas_3j < 3:
            actions.append({
                "priorite": "haute",
                "module": "Batch Cooking",
                "action": "Planifier les repas des 3 prochains jours",
                "link": "cuisine.batch_cooking"
            })

        # Stock bas
        stock_bas = db.query(InventoryItem).filter(
            InventoryItem.quantity < InventoryItem.min_quantity
        ).count()

        if stock_bas > 0:
            actions.append({
                "priorite": "haute",
                "module": "Courses",
                "action": f"{stock_bas} article(s) en stock bas",
                "link": "cuisine.courses"
            })

        # Projets échéance proche
        projets_urgents = db.query(Project).filter(
            Project.status.in_(["à faire", "en cours"]),
            Project.end_date != None,
            Project.end_date <= today + timedelta(days=7)
        ).all()

        for projet in projets_urgents[:2]:
            delta = (projet.end_date - today).days
            actions.append({
                "priorite": "moyenne",
                "module": "Projets",
                "action": f"{projet.name} - échéance dans {delta} jours",
                "link": "maison.projets"
            })

        # Routines en attente
        taches = db.query(RoutineTask).join(Routine).filter(
            RoutineTask.status == "à faire",
            Routine.is_active == True
        ).count()

        if taches > 5:
            actions.append({
                "priorite": "basse",
                "module": "Routines",
                "action": f"{taches} tâches de routine en attente",
                "link": "famille.routines"
            })

    return actions


# ===================================
# MODULE PRINCIPAL
# ===================================

def app():
    """Module Vue d'ensemble"""

    st.title("🎯 Vue d'Ensemble")
    st.caption("Toutes les informations importantes en un coup d'œil")

    # ===================================
    # STATISTIQUES GLOBALES
    # ===================================

    data = get_dashboard_data()

    st.markdown("### 📊 Cette semaine")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🍽️ Repas planifiés", data["repas_semaine"])

    with col2:
        st.metric("📅 Événements", data["events_semaine"])

    with col3:
        st.metric("🏗️ Projets actifs", data["projets_actifs"],
                  delta=f"{data['projets_urgents']} urgents" if data['projets_urgents'] > 0 else None,
                  delta_color="inverse")

    with col4:
        st.metric("⏰ Tâches jour", data["taches_jour"])

    st.markdown("---")

    # ===================================
    # ACTIONS PRIORITAIRES
    # ===================================

    st.markdown("### 🎯 Actions prioritaires")

    actions = get_prochaines_actions()

    if not actions:
        st.success("✅ Tout est sous contrôle ! Aucune action urgente.")
    else:
        for action in actions:
            priorite_color = {
                "haute": "🔴",
                "moyenne": "🟡",
                "basse": "🟢"
            }.get(action["priorite"], "⚪")

            col_action1, col_action2 = st.columns([3, 1])

            with col_action1:
                st.markdown(f"{priorite_color} **{action['module']}** : {action['action']}")

            with col_action2:
                if st.button("Aller →", key=f"action_{action['link']}", use_container_width=True):
                    st.session_state.current_module = action['link']
                    st.rerun()

    st.markdown("---")

    # ===================================
    # VUE RAPIDE MODULES
    # ===================================

    col_mod1, col_mod2 = st.columns(2)

    with col_mod1:
        st.markdown("### 🍲 Cuisine")

        with get_db_context() as db:
            # Prochains repas
            repas = db.query(BatchMeal, Recipe).join(
                Recipe, BatchMeal.recipe_id == Recipe.id
            ).filter(
                BatchMeal.scheduled_date >= date.today()
            ).order_by(BatchMeal.scheduled_date).limit(3).all()

            if repas:
                for batch, recipe in repas:
                    st.write(f"• {batch.scheduled_date.strftime('%d/%m')} : {recipe.name}")
            else:
                st.caption("Aucun repas planifié")

            # Stock bas
            if data["stock_bas"] > 0:
                st.warning(f"⚠️ {data['stock_bas']} article(s) en stock bas")

        st.markdown("---")

        st.markdown("### 👶 Famille")

        with get_db_context() as db:
            # Routines du jour
            routines = db.query(RoutineTask, Routine).join(
                Routine, RoutineTask.routine_id == Routine.id
            ).filter(
                RoutineTask.status == "à faire",
                Routine.is_active == True
            ).limit(3).all()

            if routines:
                for task, routine in routines:
                    heure = task.scheduled_time or "—"
                    st.write(f"• {heure} : {task.task_name}")
            else:
                st.caption("Toutes les routines complétées ✅")

    with col_mod2:
        st.markdown("### 🏡 Maison")

        with get_db_context() as db:
            # Projets en cours
            projets = db.query(Project).filter(
                Project.status == "en cours"
            ).order_by(Project.priority.desc()).limit(3).all()

            if projets:
                for projet in projets:
                    st.write(f"• {projet.name} ({projet.progress}%)")
            else:
                st.caption("Aucun projet en cours")

        st.markdown("---")

        st.markdown("### 🌱 Jardin")

        with get_db_context() as db:
            # Plantes à arroser
            today = date.today()
            plantes = db.query(GardenItem).filter(
                GardenItem.last_watered != None
            ).all()

            a_arroser = []
            for plante in plantes:
                delta = (today - plante.last_watered).days
                if delta >= plante.watering_frequency_days:
                    a_arroser.append(plante.name)

            if a_arroser:
                st.write(f"💧 À arroser : {', '.join(a_arroser[:3])}")
            else:
                st.caption("Arrosage OK ✅")

    st.markdown("---")

    # ===================================
    # TIMELINE SEMAINE
    # ===================================

    st.markdown("### 📅 Timeline de la semaine")

    today = date.today()

    for i in range(7):
        jour = today + timedelta(days=i)
        jour_nom = jour.strftime("%A %d/%m")

        with get_db_context() as db:
            # Compter événements du jour
            repas = db.query(BatchMeal).filter(BatchMeal.scheduled_date == jour).count()
            events = db.query(CalendarEvent).filter(
                CalendarEvent.start_date >= datetime.combine(jour, datetime.min.time()),
                CalendarEvent.start_date < datetime.combine(jour + timedelta(days=1), datetime.min.time())
            ).count()
            projets = db.query(Project).filter(
                Project.end_date == jour,
                Project.status.in_(["à faire", "en cours"])
            ).count()

            total = repas + events + projets

            if total > 0:
                is_today = jour == today
                style = "🔵" if is_today else "•"
                st.write(f"{style} **{jour_nom}** : {repas} repas, {events} événements, {projets} échéances")
            else:
                st.write(f"• {jour_nom} : Rien de prévu")

    st.markdown("---")

    # ===================================
    # ACCÈS RAPIDES
    # ===================================

    st.markdown("### 🚀 Accès rapides")

    col_r1, col_r2, col_r3 = st.columns(3)

    raccourcis = [
        ("🍲 Recettes", "cuisine.recettes"),
        ("📦 Inventaire", "cuisine.inventaire"),
        ("🛒 Courses", "cuisine.courses"),
        ("🥘 Batch Cooking", "cuisine.batch_cooking"),
        ("👶 Suivi Jules", "famille.suivi_jules"),
        ("💚 Bien-être", "famille.bien_etre"),
        ("⏰ Routines", "famille.routines"),
        ("🏗️ Projets", "maison.projets"),
        ("🌱 Jardin", "maison.jardin"),
    ]

    for i, (label, module) in enumerate(raccourcis):
        col = [col_r1, col_r2, col_r3][i % 3]
        with col:
            if st.button(label, use_container_width=True, key=f"quick_{module}"):
                st.session_state.current_module = module
                st.rerun()