"""
Module Routines avec Agent IA intégré
Gestion des routines quotidiennes avec rappels intelligents
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, time
import asyncio
from typing import List, Dict

from src.core.database import get_db_context
from src.core.models import Routine, RoutineTask, ChildProfile
from src.core.ai_agent import AgentIA


# ===================================
# HELPERS
# ===================================

def charger_routines(actives_uniquement: bool = True) -> pd.DataFrame:
    """Charge toutes les routines"""
    with get_db_context() as db:
        query = db.query(Routine)

        if actives_uniquement:
            query = query.filter(Routine.is_active == True)

        routines = query.order_by(Routine.created_at.desc()).all()

        return pd.DataFrame([{
            "id": r.id,
            "nom": r.name,
            "description": r.description or "",
            "pour": db.query(ChildProfile).get(r.child_id).name if r.child_id else "Famille",
            "frequence": r.frequency,
            "active": r.is_active,
            "ia": "🤖" if r.ai_suggested else "",
            "nb_taches": len(r.tasks)
        } for r in routines])


def charger_taches_routine(routine_id: int) -> pd.DataFrame:
    """Charge les tâches d'une routine"""
    with get_db_context() as db:
        tasks = db.query(RoutineTask).filter(
            RoutineTask.routine_id == routine_id
        ).order_by(RoutineTask.scheduled_time).all()

        return pd.DataFrame([{
            "id": t.id,
            "nom": t.task_name,
            "heure": t.scheduled_time or "—",
            "statut": t.status,
            "completed_at": t.completed_at
        } for t in tasks])


def creer_routine(nom: str, description: str, pour_qui: str, frequence: str) -> int:
    """Crée une nouvelle routine"""
    with get_db_context() as db:
        # Vérifier si c'est pour un enfant
        child_id = None
        if pour_qui != "Famille":
            child = db.query(ChildProfile).filter(ChildProfile.name == pour_qui).first()
            if child:
                child_id = child.id

        routine = Routine(
            name=nom,
            description=description,
            child_id=child_id,
            frequency=frequence,
            is_active=True,
            ai_suggested=False
        )
        db.add(routine)
        db.commit()
        return routine.id


def ajouter_tache(routine_id: int, nom: str, heure: str = None):
    """Ajoute une tâche à une routine"""
    with get_db_context() as db:
        task = RoutineTask(
            routine_id=routine_id,
            task_name=nom,
            scheduled_time=heure,
            status="à faire"
        )
        db.add(task)
        db.commit()


def marquer_complete(task_id: int):
    """Marque une tâche comme terminée"""
    with get_db_context() as db:
        task = db.query(RoutineTask).filter(RoutineTask.id == task_id).first()
        if task:
            task.status = "terminé"
            task.completed_at = datetime.now()
            db.commit()


def reinitialiser_taches_jour():
    """Réinitialise les tâches du jour"""
    with get_db_context() as db:
        tasks = db.query(RoutineTask).filter(
            RoutineTask.status == "terminé"
        ).all()

        for task in tasks:
            task.status = "à faire"
            task.completed_at = None

        db.commit()


def supprimer_routine(routine_id: int):
    """Supprime une routine"""
    with get_db_context() as db:
        db.query(Routine).filter(Routine.id == routine_id).delete()
        db.commit()


def get_taches_en_retard() -> List[Dict]:
    """Détecte les tâches en retard"""
    taches_retard = []
    now = datetime.now().time()

    with get_db_context() as db:
        tasks = db.query(RoutineTask, Routine).join(
            Routine, RoutineTask.routine_id == Routine.id
        ).filter(
            RoutineTask.status == "à faire",
            RoutineTask.scheduled_time != None,
            Routine.is_active == True
        ).all()

        for task, routine in tasks:
            try:
                heure = datetime.strptime(task.scheduled_time, "%H:%M").time()
                if heure < now:
                    taches_retard.append({
                        "routine": routine.name,
                        "tache": task.task_name,
                        "heure": task.scheduled_time,
                        "id": task.id
                    })
            except:
                pass

    return taches_retard


# ===================================
# MODULE PRINCIPAL
# ===================================

def app():
    """Module Routines avec IA intégrée"""

    st.title("⏰ Routines Quotidiennes")
    st.caption("Gestion intelligente des routines familiales")

    # Récupérer l'agent IA
    agent: AgentIA = st.session_state.get("agent_ia")

    # ===================================
    # HEURE ACTUELLE & ALERTES
    # ===================================

    now = datetime.now()
    st.info(f"🕐 **{now.strftime('%H:%M')}** — {now.strftime('%A %d %B %Y')}")

    # Tâches en retard
    taches_retard = get_taches_en_retard()

    if taches_retard:
        st.warning(f"⚠️ **{len(taches_retard)} tâche(s) en retard**")

        for tache in taches_retard[:3]:
            col_r1, col_r2 = st.columns([3, 1])

            with col_r1:
                st.write(f"• **{tache['routine']}** : {tache['tache']} (prévu {tache['heure']})")

            with col_r2:
                if st.button("✅ Fait", key=f"late_{tache['id']}", use_container_width=True):
                    marquer_complete(tache['id'])
                    st.success("Terminé !")
                    st.rerun()

    st.markdown("---")

    # ===================================
    # TABS PRINCIPAUX
    # ===================================

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Mes Routines",
        "🤖 Rappels IA",
        "➕ Créer Routine",
        "📊 Suivi"
    ])

    # ===================================
    # TAB 1 : LISTE DES ROUTINES
    # ===================================

    with tab1:
        st.subheader("Routines actives")

        # Actions rapides
        col_a1, col_a2 = st.columns([2, 1])

        with col_a1:
            if st.button("🔄 Rafraîchir", use_container_width=True):
                st.rerun()

        with col_a2:
            if st.button("🔄 Réinitialiser jour", use_container_width=True):
                reinitialiser_taches_jour()
                st.success("Tâches réinitialisées")
                st.rerun()

        # Charger routines
        df_routines = charger_routines(actives_uniquement=True)

        if df_routines.empty:
            st.info("Aucune routine active. Crée-en une ou utilise l'IA pour générer des suggestions !")
        else:
            # Liste des routines
            for _, routine in df_routines.iterrows():
                with st.expander(
                        f"{routine['ia']} **{routine['nom']}** — {routine['pour']} ({routine['nb_taches']} tâches)",
                        expanded=True
                ):
                    st.caption(routine['description'])
                    st.caption(f"📅 Fréquence : {routine['frequence']}")

                    # Charger les tâches
                    df_taches = charger_taches_routine(routine['id'])

                    if not df_taches.empty:
                        st.markdown("**Tâches :**")

                        for _, tache in df_taches.iterrows():
                            col_t1, col_t2, col_t3 = st.columns([2, 1, 1])

                            with col_t1:
                                statut_emoji = "✅" if tache['statut'] == "terminé" else "⏳"
                                st.write(f"{statut_emoji} **{tache['heure']}** — {tache['nom']}")

                            with col_t2:
                                if tache['statut'] == "à faire":
                                    if st.button(
                                            "✅ Terminé",
                                            key=f"done_{tache['id']}",
                                            use_container_width=True
                                    ):
                                        marquer_complete(tache['id'])
                                        st.success("Tâche terminée !")
                                        st.rerun()
                                else:
                                    st.caption(f"Fait à {tache['completed_at'].strftime('%H:%M')}" if tache['completed_at'] else "")

                            with col_t3:
                                if st.button("➕ Tâche", key=f"add_{routine['id']}", use_container_width=True):
                                    st.session_state["adding_task_to"] = routine['id']

                        # Ajouter tâche (si activé)
                        if st.session_state.get("adding_task_to") == routine['id']:
                            with st.form(f"form_add_task_{routine['id']}"):
                                new_task_name = st.text_input("Nom de la tâche")
                                new_task_time = st.time_input("Heure (optionnel)")

                                col_f1, col_f2 = st.columns(2)

                                with col_f1:
                                    if st.form_submit_button("✅ Ajouter"):
                                        if new_task_name:
                                            time_str = new_task_time.strftime("%H:%M") if new_task_time else None
                                            ajouter_tache(routine['id'], new_task_name, time_str)
                                            st.success("Tâche ajoutée")
                                            del st.session_state["adding_task_to"]
                                            st.rerun()

                                with col_f2:
                                    if st.form_submit_button("❌ Annuler"):
                                        del st.session_state["adding_task_to"]
                                        st.rerun()

                    # Actions routine
                    col_act1, col_act2 = st.columns(2)

                    with col_act1:
                        if st.button("⏸️ Désactiver", key=f"disable_{routine['id']}", use_container_width=True):
                            with get_db_context() as db:
                                r = db.query(Routine).get(routine['id'])
                                r.is_active = False
                                db.commit()
                            st.success("Routine désactivée")
                            st.rerun()

                    with col_act2:
                        if st.button("🗑️ Supprimer", key=f"del_{routine['id']}", type="secondary", use_container_width=True):
                            supprimer_routine(routine['id'])
                            st.success("Routine supprimée")
                            st.rerun()

    # ===================================
    # TAB 2 : RAPPELS IA
    # ===================================

    with tab2:
        st.subheader("🤖 Rappels intelligents")

        if not agent:
            st.error("Agent IA non disponible")
        else:
            st.info("💡 L'IA analyse tes routines et te rappelle les tâches importantes")

            heure_actuelle = datetime.now().strftime("%H:%M")

            if st.button("🤖 Demander rappels IA", type="primary", use_container_width=True):
                with st.spinner("🤖 Analyse des routines..."):
                    try:
                        # Récupérer toutes les tâches
                        with get_db_context() as db:
                            tasks = db.query(RoutineTask, Routine).join(
                                Routine, RoutineTask.routine_id == Routine.id
                            ).filter(
                                RoutineTask.status == "à faire",
                                Routine.is_active == True
                            ).all()

                            routines_data = [
                                {
                                    "nom": routine.name,
                                    "heure": task.scheduled_time or "—",
                                    "tache": task.task_name
                                }
                                for task, routine in tasks
                            ]

                        # Appel IA
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                        rappels = loop.run_until_complete(
                            agent.rappeler_routines(routines_data, heure_actuelle)
                        )

                        st.session_state["rappels_ia"] = rappels
                        st.success("✅ Rappels générés")

                    except Exception as e:
                        st.error(f"Erreur IA : {e}")

            # Afficher rappels
            if "rappels_ia" in st.session_state:
                rappels = st.session_state["rappels_ia"]

                if not rappels:
                    st.success("✅ Aucune routine urgente ! Tout est sous contrôle.")
                else:
                    st.markdown("---")
                    st.markdown("### 🔔 Rappels à l'instant")

                    for rappel in rappels:
                        priorite = rappel.get("priorite", "moyenne")

                        if priorite == "haute":
                            st.error(f"🔴 **{rappel['routine']}** : {rappel['message']}")
                        elif priorite == "moyenne":
                            st.warning(f"🟡 **{rappel['routine']}** : {rappel['message']}")
                        else:
                            st.info(f"🟢 **{rappel['routine']}** : {rappel['message']}")

            # Suggestions de routines
            st.markdown("---")
            st.markdown("### 💡 Routines suggérées par l'IA")

            suggestions_base = [
                {
                    "nom": "Routine du matin",
                    "taches": ["Réveil", "Petit-déjeuner", "Préparation", "Départ"]
                },
                {
                    "nom": "Routine du soir (Jules)",
                    "taches": ["Bain", "Dîner", "Brossage dents", "Histoire", "Dodo"]
                },
                {
                    "nom": "Routine coucher (adultes)",
                    "taches": ["Préparation lendemain", "Rangement", "Lecture", "Coucher"]
                },
                {
                    "nom": "Routine weekend",
                    "taches": ["Grasse matinée", "Activité famille", "Repas ensemble", "Détente"]
                }
            ]

            for sugg in suggestions_base[:2]:
                with st.expander(f"✨ {sugg['nom']}", expanded=False):
                    st.write("**Tâches suggérées :**")
                    for tache in sugg['taches']:
                        st.write(f"• {tache}")

                    if st.button(f"➕ Créer cette routine", key=f"create_{sugg['nom']}"):
                        routine_id = creer_routine(
                            sugg['nom'],
                            f"Routine suggérée par l'IA",
                            "Famille",
                            "quotidien"
                        )

                        for tache in sugg['taches']:
                            ajouter_tache(routine_id, tache)

                        st.success(f"✅ Routine '{sugg['nom']}' créée !")
                        st.rerun()

    # ===================================
    # TAB 3 : CRÉER ROUTINE
    # ===================================

    with tab3:
        st.subheader("➕ Créer une nouvelle routine")

        with st.form("form_create_routine"):
            nom = st.text_input("Nom de la routine *", placeholder="Ex: Routine du soir")

            col_c1, col_c2 = st.columns(2)

            with col_c1:
                description = st.text_area(
                    "Description",
                    placeholder="Objectif de cette routine..."
                )

            with col_c2:
                # Pour qui
                with get_db_context() as db:
                    children = db.query(ChildProfile).all()
                    personnes = ["Famille"] + [c.name for c in children]

                pour_qui = st.selectbox("Pour qui ?", personnes)

                frequence = st.selectbox(
                    "Fréquence",
                    ["quotidien", "semaine", "weekend", "occasionnel"]
                )

            # Tâches
            st.markdown("**Tâches de la routine**")

            nb_taches = st.number_input("Nombre de tâches", 1, 20, 3, key="nb_tasks_create")

            taches = []
            for i in range(int(nb_taches)):
                col_t1, col_t2 = st.columns([2, 1])

                with col_t1:
                    tache_nom = st.text_input(
                        f"Tâche {i+1}",
                        placeholder=f"Ex: Brossage de dents",
                        key=f"task_name_{i}"
                    )

                with col_t2:
                    tache_heure = st.time_input(
                        f"Heure {i+1}",
                        value=None,
                        key=f"task_time_{i}"
                    )

                if tache_nom:
                    taches.append({
                        "nom": tache_nom,
                        "heure": tache_heure.strftime("%H:%M") if tache_heure else None
                    })

            submitted = st.form_submit_button("💾 Créer la routine", type="primary")

            if submitted:
                if not nom:
                    st.error("Le nom est obligatoire")
                elif not taches:
                    st.error("Ajoute au moins une tâche")
                else:
                    # Créer routine
                    routine_id = creer_routine(nom, description, pour_qui, frequence)

                    # Ajouter tâches
                    for tache in taches:
                        ajouter_tache(routine_id, tache['nom'], tache['heure'])

                    st.success(f"✅ Routine '{nom}' créée avec {len(taches)} tâches !")
                    st.balloons()
                    st.rerun()

    # ===================================
    # TAB 4 : SUIVI
    # ===================================

    with tab4:
        st.subheader("📊 Suivi des routines")

        df_all = charger_routines(actives_uniquement=False)

        if df_all.empty:
            st.info("Aucune routine à analyser")
        else:
            # Métriques
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)

            with col_m1:
                st.metric("Routines totales", len(df_all))

            with col_m2:
                actives = len(df_all[df_all["active"] == True])
                st.metric("Actives", actives)

            with col_m3:
                ia_count = len(df_all[df_all["ia"] == "🤖"])
                st.metric("Suggérées IA", ia_count)

            with col_m4:
                # Taux de complétion aujourd'hui
                with get_db_context() as db:
                    tasks_today = db.query(RoutineTask).filter(
                        RoutineTask.completed_at >= datetime.now().replace(hour=0, minute=0)
                    ).count()

                st.metric("Complétées aujourd'hui", tasks_today)

            st.markdown("---")

            # Statistiques par routine
            st.markdown("### 📈 Détails par routine")

            for _, routine in df_all.iterrows():
                df_taches = charger_taches_routine(routine['id'])

                if not df_taches.empty:
                    terminees = len(df_taches[df_taches["statut"] == "terminé"])
                    total = len(df_taches)
                    pct = (terminees / total) * 100 if total > 0 else 0

                    col_stat1, col_stat2, col_stat3 = st.columns([2, 1, 1])

                    with col_stat1:
                        st.write(f"**{routine['nom']}**")

                    with col_stat2:
                        st.progress(pct / 100)

                    with col_stat3:
                        st.write(f"{terminees}/{total} ({pct:.0f}%)")

            # Historique (mock pour demo)
            st.markdown("---")
            st.markdown("### 📅 Historique de la semaine")

            st.info("Fonctionnalité en développement : graphique d'historique sur 7 jours")