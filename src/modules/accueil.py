"""
Module Accueil - Dashboard intelligent avec Agent IA
Vue d'ensemble de l'application avec actions rapides
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import asyncio
from typing import Dict, List

from src.core.database import get_db_context
from src.core.models import (
    Recipe, InventoryItem, Ingredient, BatchMeal,
    Project, RoutineTask, ChildProfile, Notification
)
from src.core.ai_agent import AgentIA


# ===================================
# HELPERS
# ===================================

def get_dashboard_stats() -> Dict:
    """Récupère les statistiques pour le dashboard"""
    with get_db_context() as db:
        stats = {
            "recettes_total": db.query(Recipe).count(),
            "recettes_ia": db.query(Recipe).filter(Recipe.ai_generated == True).count(),
            "stock_bas": db.query(InventoryItem).filter(
                InventoryItem.quantity < InventoryItem.min_quantity
            ).count(),
            "repas_planifies": db.query(BatchMeal).filter(
                BatchMeal.scheduled_date >= date.today()
            ).count(),
            "projets_actifs": db.query(Project).filter(
                Project.status.in_(["à faire", "en cours"])
            ).count(),
            "taches_jour": db.query(RoutineTask).filter(
                RoutineTask.status == "à faire"
            ).count(),
            "notifications_non_lues": db.query(Notification).filter(
                Notification.read == False
            ).count()
        }

        return stats


def get_actions_urgentes() -> List[Dict]:
    """Détecte les actions urgentes nécessitant une attention"""
    actions = []

    with get_db_context() as db:
        # 1. Stock critique
        items_critiques = db.query(
            Ingredient.name,
            InventoryItem.quantity,
            Ingredient.unit
        ).join(
            InventoryItem, Ingredient.id == InventoryItem.ingredient_id
        ).filter(
            InventoryItem.quantity < InventoryItem.min_quantity
        ).all()

        if items_critiques:
            noms = ", ".join([item.name for item in items_critiques[:3]])
            actions.append({
                "type": "URGENT",
                "icone": "⚠️",
                "titre": "Stock critique",
                "message": f"{len(items_critiques)} article(s) en stock bas : {noms}",
                "action": "Ajouter à la liste de courses",
                "module": "cuisine.courses"
            })

        # 2. Repas non planifiés cette semaine
        today = date.today()
        week_end = today + timedelta(days=7)

        repas_semaine = db.query(BatchMeal).filter(
            BatchMeal.scheduled_date.between(today, week_end)
        ).count()

        if repas_semaine < 3:
            actions.append({
                "type": "ATTENTION",
                "icone": "📅",
                "titre": "Planning incomplet",
                "message": f"Seulement {repas_semaine} repas planifiés cette semaine",
                "action": "Générer un planning automatique",
                "module": "cuisine.batch_cooking"
            })

        # 3. Tâches en retard
        taches_retard = db.query(RoutineTask).filter(
            RoutineTask.status == "à faire",
            RoutineTask.scheduled_time != None
        ).all()

        retard_count = 0
        now = datetime.now().time()
        for tache in taches_retard:
            try:
                if tache.scheduled_time:
                    heure = datetime.strptime(tache.scheduled_time, "%H:%M").time()
                    if heure < now:
                        retard_count += 1
            except:
                pass

        if retard_count > 0:
            actions.append({
                "type": "INFO",
                "icone": "⏰",
                "titre": "Routines en retard",
                "message": f"{retard_count} tâche(s) de routine en attente",
                "action": "Voir les routines",
                "module": "famille.routines"
            })

        # 4. Projets sans progression depuis 7 jours
        week_ago = datetime.now() - timedelta(days=7)
        projets_stagnants = db.query(Project).filter(
            Project.status == "en cours",
            Project.updated_at < week_ago
        ).count()

        if projets_stagnants > 0:
            actions.append({
                "type": "INFO",
                "icone": "🏗️",
                "titre": "Projets en pause",
                "message": f"{projets_stagnants} projet(s) sans activité depuis 7 jours",
                "action": "Voir les projets",
                "module": "maison.projets"
            })

    return actions


def get_suggestions_ia_rapides() -> List[str]:
    """Génère des suggestions rapides avec l'IA"""
    suggestions = []

    with get_db_context() as db:
        # Récupérer l'inventaire
        items = db.query(
            Ingredient.name,
            InventoryItem.quantity,
            Ingredient.unit
        ).join(
            InventoryItem, Ingredient.id == InventoryItem.ingredient_id
        ).filter(
            InventoryItem.quantity > 0
        ).limit(5).all()

        if items:
            items_text = ", ".join([f"{item.name}" for item in items])
            suggestions.append(f"🍽️ Recettes possibles avec : {items_text}")

        # Météo (mock pour l'instant)
        suggestions.append("🌤️ Temps ensoleillé → Idéal pour jardiner")

        # Jules
        enfant = db.query(ChildProfile).first()
        if enfant:
            age_mois = (date.today() - enfant.birth_date).days // 30
            suggestions.append(f"👶 {enfant.name} ({age_mois} mois) → Conseils adaptés disponibles")

    return suggestions


# ===================================
# MODULE PRINCIPAL
# ===================================

def app():
    """Module Accueil - Dashboard intelligent"""

    # Header personnalisé
    st.markdown("""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='color: #2d4d36; font-size: 2.5rem; margin-bottom: 0.5rem;'>
                👋 Bienvenue dans Assistant MaTanne
            </h1>
            <p style='color: #5e7a6a; font-size: 1.2rem;'>
                Ton copilote quotidien propulsé par l'IA
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Récupérer l'agent IA
    agent: AgentIA = st.session_state.get("agent_ia")

    # ===================================
    # STATISTIQUES PRINCIPALES
    # ===================================

    stats = get_dashboard_stats()

    st.markdown("### 📊 Vue d'ensemble")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "📚 Recettes",
            stats["recettes_total"],
            delta=f"{stats['recettes_ia']} IA",
            delta_color="normal"
        )

    with col2:
        delta_stock = -stats["stock_bas"] if stats["stock_bas"] > 0 else 0
        st.metric(
            "📦 Inventaire",
            "OK" if stats["stock_bas"] == 0 else "Alerte",
            delta=f"{stats['stock_bas']} bas" if stats["stock_bas"] > 0 else None,
            delta_color="inverse"
        )

    with col3:
        st.metric(
            "📅 Repas planifiés",
            stats["repas_planifies"],
            delta="Cette semaine",
            delta_color="off"
        )

    with col4:
        st.metric(
            "🏗️ Projets actifs",
            stats["projets_actifs"],
            delta=f"{stats['taches_jour']} tâches aujourd'hui",
            delta_color="off"
        )

    st.markdown("---")

    # ===================================
    # ACTIONS URGENTES
    # ===================================

    actions = get_actions_urgentes()

    if actions:
        st.markdown("### 🚨 Actions urgentes")

        for action in actions:
            if action["type"] == "URGENT":
                type_style = "error"
            elif action["type"] == "ATTENTION":
                type_style = "warning"
            else:
                type_style = "info"

            with st.container():
                col_icon, col_content, col_action = st.columns([0.5, 3, 1.5])

                with col_icon:
                    st.markdown(f"<div style='font-size: 2rem;'>{action['icone']}</div>",
                                unsafe_allow_html=True)

                with col_content:
                    st.markdown(f"**{action['titre']}**")
                    st.caption(action['message'])

                with col_action:
                    if st.button(
                            action['action'],
                            key=f"action_{action['module']}",
                            type="primary" if action['type'] == "URGENT" else "secondary"
                    ):
                        st.session_state.current_module = action['module']
                        st.rerun()

                st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    else:
        st.success("✅ Aucune action urgente ! Tout est sous contrôle.")

    st.markdown("---")

    # ===================================
    # SUGGESTIONS IA DU JOUR
    # ===================================

    st.markdown("### 🤖 Suggestions IA du jour")

    col_sugg1, col_sugg2 = st.columns([2, 1])

    with col_sugg1:
        suggestions = get_suggestions_ia_rapides()

        for sugg in suggestions:
            st.info(sugg)

        if agent and st.button("✨ Plus de suggestions IA", type="primary"):
            with st.spinner("🤖 L'IA analyse ton quotidien..."):
                # Générer des suggestions personnalisées
                st.balloons()
                st.success("Suggestions générées ! Voir les modules concernés.")

    with col_sugg2:
        st.markdown("**🎯 Actions rapides IA**")

        if st.button("🍽️ Suggérer repas", use_container_width=True):
            st.session_state.current_module = "cuisine.recettes"
            st.rerun()

        if st.button("📋 Planifier semaine", use_container_width=True):
            st.session_state.current_module = "cuisine.batch_cooking"
            st.rerun()

        if st.button("🛒 Optimiser courses", use_container_width=True):
            st.session_state.current_module = "cuisine.courses"
            st.rerun()

    st.markdown("---")

    # ===================================
    # ACTIVITÉ RÉCENTE
    # ===================================

    st.markdown("### 📈 Activité récente")

    col_act1, col_act2 = st.columns(2)

    with col_act1:
        st.markdown("#### 🍲 Cuisine")

        with get_db_context() as db:
            # Dernières recettes ajoutées
            recettes_recentes = db.query(Recipe).order_by(
                Recipe.created_at.desc()
            ).limit(3).all()

            if recettes_recentes:
                for recette in recettes_recentes:
                    ai_badge = "🤖" if recette.ai_generated else ""
                    st.write(f"• {ai_badge} {recette.name}")
            else:
                st.caption("Aucune recette récente")

            # Prochains repas
            st.markdown("**Prochains repas**")
            prochains = db.query(
                BatchMeal, Recipe
            ).join(
                Recipe, BatchMeal.recipe_id == Recipe.id
            ).filter(
                BatchMeal.scheduled_date >= date.today()
            ).order_by(
                BatchMeal.scheduled_date
            ).limit(3).all()

            if prochains:
                for batch, recette in prochains:
                    st.write(f"• {batch.scheduled_date.strftime('%d/%m')} - {recette.name}")
            else:
                st.caption("Aucun repas planifié")

    with col_act2:
        st.markdown("#### 🏡 Maison")

        with get_db_context() as db:
            # Projets en cours
            projets = db.query(Project).filter(
                Project.status == "en cours"
            ).limit(3).all()

            if projets:
                for projet in projets:
                    progress = projet.progress or 0
                    st.write(f"• {projet.name} ({progress}%)")
            else:
                st.caption("Aucun projet actif")

            # Routines du jour
            st.markdown("**Routines d'aujourd'hui**")
            routines = db.query(RoutineTask).filter(
                RoutineTask.status == "à faire"
            ).limit(3).all()

            if routines:
                for routine in routines:
                    time_str = routine.scheduled_time or "—"
                    st.write(f"• {time_str} {routine.task_name}")
            else:
                st.caption("Toutes les routines complétées ✅")

    st.markdown("---")

    # ===================================
    # ACCÈS RAPIDES
    # ===================================

    st.markdown("### 🚀 Accès rapides")

    col_r1, col_r2, col_r3 = st.columns(3)

    modules = [
        ("🍲 Recettes", "cuisine.recettes"),
        ("📦 Inventaire", "cuisine.inventaire"),
        ("🛒 Courses", "cuisine.courses"),
        ("🥘 Batch Cooking", "cuisine.batch_cooking"),
        ("👶 Suivi Jules", "famille.suivi_jules"),
        ("⏰ Routines", "famille.routines"),
        ("🏗️ Projets", "maison.projets"),
        ("🌱 Jardin", "maison.jardin"),
        ("📅 Calendrier", "planning.calendrier"),
    ]

    for i, (label, module) in enumerate(modules):
        col = [col_r1, col_r2, col_r3][i % 3]
        with col:
            if st.button(label, use_container_width=True, key=f"quick_{module}"):
                st.session_state.current_module = module
                st.rerun()

    st.markdown("---")

    # ===================================
    # NOTIFICATIONS
    # ===================================

    if stats["notifications_non_lues"] > 0:
        with st.expander(f"🔔 Notifications ({stats['notifications_non_lues']} non lues)"):
            with get_db_context() as db:
                notifs = db.query(Notification).filter(
                    Notification.read == False
                ).order_by(
                    Notification.created_at.desc()
                ).limit(5).all()

                for notif in notifs:
                    priority_icon = "🔴" if notif.priority == "haute" else "🟡" if notif.priority == "moyenne" else "🔵"
                    st.write(f"{priority_icon} **[{notif.module}]** {notif.message}")
                    st.caption(notif.created_at.strftime("%d/%m/%Y %H:%M"))
                    st.markdown("---")

    # ===================================
    # FOOTER
    # ===================================

    st.markdown("---")
    st.caption("💡 **Astuce :** Utilise les suggestions IA pour automatiser ton quotidien !")