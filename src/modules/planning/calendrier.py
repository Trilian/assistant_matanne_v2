"""
Module Calendrier avec Agent IA intégré
Vue d'ensemble du planning familial
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar
from typing import List, Dict

from src.core.database import get_db_context
from src.core.models import CalendarEvent, BatchMeal, Recipe, Project, RoutineTask, Routine
from src.core.ai_agent import AgentIA


# ===================================
# HELPERS
# ===================================

def charger_evenements(date_debut: date, date_fin: date) -> pd.DataFrame:
    """Charge tous les événements sur une période"""
    with get_db_context() as db:
        events = db.query(CalendarEvent).filter(
            CalendarEvent.start_date >= datetime.combine(date_debut, datetime.min.time()),
            CalendarEvent.start_date <= datetime.combine(date_fin, datetime.max.time())
        ).order_by(CalendarEvent.start_date).all()

        return pd.DataFrame([{
            "id": e.id,
            "titre": e.title,
            "description": e.description or "",
            "debut": e.start_date,
            "fin": e.end_date,
            "lieu": e.location or "",
            "categorie": e.category or "Autre",
            "ia": e.ai_generated
        } for e in events])


def charger_repas_planifies(date_debut: date, date_fin: date) -> pd.DataFrame:
    """Charge les repas planifiés sur une période"""
    with get_db_context() as db:
        meals = db.query(
            BatchMeal, Recipe
        ).join(
            Recipe, BatchMeal.recipe_id == Recipe.id
        ).filter(
            BatchMeal.scheduled_date >= date_debut,
            BatchMeal.scheduled_date <= date_fin
        ).order_by(BatchMeal.scheduled_date).all()

        return pd.DataFrame([{
            "date": meal.scheduled_date,
            "titre": f"🍽️ {recipe.name}",
            "type": "repas",
            "details": f"{meal.portions} portions"
        } for meal, recipe in meals])


def charger_projets_echeances(date_debut: date, date_fin: date) -> pd.DataFrame:
    """Charge les échéances de projets"""
    with get_db_context() as db:
        projects = db.query(Project).filter(
            Project.end_date >= date_debut,
            Project.end_date <= date_fin,
            Project.status.in_(["à faire", "en cours"])
        ).all()

        return pd.DataFrame([{
            "date": p.end_date,
            "titre": f"🏗️ {p.name}",
            "type": "projet",
            "details": f"Échéance ({p.progress}% complété)"
        } for p in projects])


def charger_routines_jour(date_jour: date) -> pd.DataFrame:
    """Charge les routines pour un jour donné"""
    with get_db_context() as db:
        tasks = db.query(
            RoutineTask, Routine
        ).join(
            Routine, RoutineTask.routine_id == Routine.id
        ).filter(
            Routine.is_active == True,
            RoutineTask.status == "à faire"
        ).all()

        return pd.DataFrame([{
            "heure": task.scheduled_time or "—",
            "titre": f"⏰ {routine.name}",
            "type": "routine",
            "details": task.task_name
        } for task, routine in tasks])


def creer_evenement(
        titre: str,
        debut: datetime,
        fin: datetime = None,
        description: str = "",
        lieu: str = "",
        categorie: str = "Autre"
):
    """Crée un nouvel événement"""
    with get_db_context() as db:
        event = CalendarEvent(
            title=titre,
            start_date=debut,
            end_date=fin,
            description=description,
            location=lieu,
            category=categorie,
            ai_generated=False
        )
        db.add(event)
        db.commit()


def supprimer_evenement(event_id: int):
    """Supprime un événement"""
    with get_db_context() as db:
        db.query(CalendarEvent).filter(CalendarEvent.id == event_id).delete()
        db.commit()


def get_vue_semaine(date_debut: date) -> Dict:
    """Génère une vue semaine avec tous les événements"""
    date_fin = date_debut + timedelta(days=6)

    # Charger tous les types d'événements
    df_events = charger_evenements(date_debut, date_fin)
    df_repas = charger_repas_planifies(date_debut, date_fin)
    df_projets = charger_projets_echeances(date_debut, date_fin)

    # Combiner
    vue = {}

    for i in range(7):
        jour = date_debut + timedelta(days=i)
        vue[jour] = {
            "events": [],
            "repas": [],
            "projets": [],
            "routines": []
        }

        # Événements
        if not df_events.empty:
            events_jour = df_events[df_events["debut"].dt.date == jour]
            vue[jour]["events"] = events_jour.to_dict('records')

        # Repas
        if not df_repas.empty:
            repas_jour = df_repas[df_repas["date"] == jour]
            vue[jour]["repas"] = repas_jour.to_dict('records')

        # Projets
        if not df_projets.empty:
            projets_jour = df_projets[df_projets["date"] == jour]
            vue[jour]["projets"] = projets_jour.to_dict('records')

    return vue


# ===================================
# MODULE PRINCIPAL
# ===================================

def app():
    """Module Calendrier avec IA intégrée"""

    st.title("📅 Calendrier Familial")
    st.caption("Vue d'ensemble du planning avec suggestions IA")

    # Récupérer l'agent IA
    agent: AgentIA = st.session_state.get("agent_ia")

    # ===================================
    # NAVIGATION DATE
    # ===================================

    if "current_week_start" not in st.session_state:
        # Début de semaine (lundi)
        today = date.today()
        st.session_state.current_week_start = today - timedelta(days=today.weekday())

    col_nav1, col_nav2, col_nav3 = st.columns([1, 2, 1])

    with col_nav1:
        if st.button("⬅️ Semaine précédente", use_container_width=True):
            st.session_state.current_week_start -= timedelta(days=7)
            st.rerun()

    with col_nav2:
        week_start = st.session_state.current_week_start
        week_end = week_start + timedelta(days=6)
        st.markdown(f"### {week_start.strftime('%d/%m')} — {week_end.strftime('%d/%m/%Y')}")

    with col_nav3:
        if st.button("Semaine suivante ➡️", use_container_width=True):
            st.session_state.current_week_start += timedelta(days=7)
            st.rerun()

    st.markdown("---")

    # ===================================
    # TABS PRINCIPAUX
    # ===================================

    tab1, tab2, tab3 = st.tabs([
        "📅 Vue Semaine",
        "➕ Nouvel Événement",
        "📊 Vue Mois"
    ])

    # ===================================
    # TAB 1 : VUE SEMAINE
    # ===================================

    with tab1:
        st.subheader("Planning de la semaine")

        vue = get_vue_semaine(st.session_state.current_week_start)

        # Afficher par jour
        for jour, contenu in vue.items():
            jour_nom = calendar.day_name[jour.weekday()]

            # Highlight aujourd'hui
            is_today = jour == date.today()

            with st.expander(
                    f"{'🔵 ' if is_today else ''}{jour_nom} {jour.strftime('%d/%m')}",
                    expanded=is_today
            ):
                # Événements du calendrier
                if contenu["events"]:
                    st.markdown("**📅 Événements**")
                    for event in contenu["events"]:
                        heure = event["debut"].strftime("%H:%M")
                        st.write(f"• {heure} — **{event['titre']}**")
                        if event['lieu']:
                            st.caption(f"📍 {event['lieu']}")

                # Repas planifiés
                if contenu["repas"]:
                    st.markdown("**🍽️ Repas**")
                    for repas in contenu["repas"]:
                        st.write(f"• {repas['titre']}")
                        st.caption(repas['details'])

                # Échéances projets
                if contenu["projets"]:
                    st.markdown("**🏗️ Projets**")
                    for projet in contenu["projets"]:
                        st.write(f"• {projet['titre']}")
                        st.caption(projet['details'])

                # Si rien
                if not any([contenu["events"], contenu["repas"], contenu["projets"]]):
                    st.caption("Aucun événement prévu")

        st.markdown("---")

        # Statistiques semaine
        st.markdown("### 📊 Résumé de la semaine")

        total_events = sum([len(c["events"]) for c in vue.values()])
        total_repas = sum([len(c["repas"]) for c in vue.values()])
        total_projets = sum([len(c["projets"]) for c in vue.values()])

        col_s1, col_s2, col_s3 = st.columns(3)

        with col_s1:
            st.metric("Événements", total_events)

        with col_s2:
            st.metric("Repas planifiés", total_repas)

        with col_s3:
            st.metric("Échéances projets", total_projets)

    # ===================================
    # TAB 2 : NOUVEL ÉVÉNEMENT
    # ===================================

    with tab2:
        st.subheader("➕ Créer un événement")

        with st.form("form_event"):
            titre = st.text_input("Titre *", placeholder="Ex: RDV médecin")

            col_e1, col_e2 = st.columns(2)

            with col_e1:
                date_event = st.date_input("Date *", value=date.today())
                heure_debut = st.time_input("Heure de début", value=datetime.now().time())

            with col_e2:
                categorie = st.selectbox(
                    "Catégorie",
                    ["Famille", "Santé", "Travail", "Loisirs", "Social", "Autre"]
                )
                heure_fin = st.time_input("Heure de fin (optionnel)", value=None)

            lieu = st.text_input("Lieu (optionnel)", placeholder="Ex: Cabinet Dr. Dupont")

            description = st.text_area(
                "Description (optionnel)",
                placeholder="Détails, rappels, préparation..."
            )

            submitted = st.form_submit_button("💾 Créer l'événement", type="primary")

            if submitted:
                if not titre:
                    st.error("Le titre est obligatoire")
                else:
                    debut = datetime.combine(date_event, heure_debut)
                    fin = datetime.combine(date_event, heure_fin) if heure_fin else None

                    creer_evenement(titre, debut, fin, description, lieu, categorie)
                    st.success(f"✅ Événement '{titre}' créé")
                    st.balloons()
                    st.rerun()

        st.markdown("---")

        # Événements récurrents (suggestions)
        st.markdown("### 🔁 Créer événements récurrents")

        st.info("💡 Fonctionnalité à venir : Ajouter des événements répétitifs (hebdomadaires, mensuels)")

    # ===================================
    # TAB 3 : VUE MOIS
    # ===================================

    with tab3:
        st.subheader("📅 Vue mensuelle")

        # Sélection mois
        col_m1, col_m2 = st.columns([2, 1])

        with col_m1:
            today = date.today()
            mois_select = st.selectbox(
                "Mois",
                list(calendar.month_name)[1:],
                index=today.month - 1
            )
            mois_num = list(calendar.month_name).index(mois_select)

        with col_m2:
            annee = st.number_input("Année", 2020, 2030, today.year)

        # Générer calendrier
        cal = calendar.monthcalendar(annee, mois_num)

        st.markdown(f"### {mois_select} {annee}")

        # Charger événements du mois
        premier_jour = date(annee, mois_num, 1)
        dernier_jour = date(annee, mois_num, calendar.monthrange(annee, mois_num)[1])

        df_events_mois = charger_evenements(premier_jour, dernier_jour)
        df_repas_mois = charger_repas_planifies(premier_jour, dernier_jour)

        # Afficher calendrier
        cols_jours = st.columns(7)
        jours_semaine = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]

        for i, col in enumerate(cols_jours):
            col.markdown(f"**{jours_semaine[i]}**")

        for semaine in cal:
            cols = st.columns(7)

            for i, jour in enumerate(semaine):
                if jour == 0:
                    cols[i].write("")
                else:
                    date_jour = date(annee, mois_num, jour)

                    # Compter événements
                    nb_events = 0
                    if not df_events_mois.empty:
                        nb_events += len(df_events_mois[df_events_mois["debut"].dt.date == date_jour])
                    if not df_repas_mois.empty:
                        nb_events += len(df_repas_mois[df_repas_mois["date"] == date_jour])

                    # Highlight aujourd'hui
                    style = "🔵" if date_jour == date.today() else ""

                    if nb_events > 0:
                        cols[i].markdown(f"{style} **{jour}** ({nb_events})")
                    else:
                        cols[i].write(f"{style} {jour}")

        st.markdown("---")

        # Légende
        st.caption("🔵 = Aujourd'hui | (nombre) = Événements du jour")