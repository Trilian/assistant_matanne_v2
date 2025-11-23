"""
Module Projets avec Agent IA intégré
Gestion et priorisation intelligente des projets maison
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import asyncio
from typing import List, Dict

from src.core.database import get_db_context
from src.core.models import Project, ProjectTask
from src.core.ai_agent import AgentIA


# ===================================
# HELPERS
# ===================================

def charger_projets(statut: str = None) -> pd.DataFrame:
    """Charge les projets"""
    with get_db_context() as db:
        query = db.query(Project)

        if statut:
            query = query.filter(Project.status == statut)

        projets = query.order_by(Project.priority.desc(), Project.updated_at.desc()).all()

        return pd.DataFrame([{
            "id": p.id,
            "nom": p.name,
            "categorie": p.category or "—",
            "priorite": p.priority,
            "statut": p.status,
            "progres": p.progress,
            "debut": p.start_date,
            "fin": p.end_date,
            "ia_score": p.ai_priority_score or 0,
            "updated": p.updated_at
        } for p in projets])


def charger_taches_projet(project_id: int) -> pd.DataFrame:
    """Charge les tâches d'un projet"""
    with get_db_context() as db:
        tasks = db.query(ProjectTask).filter(
            ProjectTask.project_id == project_id
        ).order_by(ProjectTask.due_date).all()

        return pd.DataFrame([{
            "id": t.id,
            "nom": t.task_name,
            "description": t.description or "",
            "statut": t.status,
            "echeance": t.due_date,
            "duree": t.estimated_duration,
            "completed": t.completed_at
        } for t in tasks])


def creer_projet(
        nom: str,
        description: str,
        categorie: str,
        priorite: str,
        date_debut: date = None,
        date_fin: date = None
) -> int:
    """Crée un nouveau projet"""
    with get_db_context() as db:
        projet = Project(
            name=nom,
            description=description,
            category=categorie,
            priority=priorite,
            start_date=date_debut,
            end_date=date_fin,
            status="à faire",
            progress=0
        )
        db.add(projet)
        db.commit()
        return projet.id


def ajouter_tache_projet(
        project_id: int,
        nom: str,
        description: str = None,
        echeance: date = None,
        duree: int = None
):
    """Ajoute une tâche à un projet"""
    with get_db_context() as db:
        task = ProjectTask(
            project_id=project_id,
            task_name=nom,
            description=description,
            due_date=echeance,
            estimated_duration=duree,
            status="à faire"
        )
        db.add(task)
        db.commit()


def marquer_tache_complete(task_id: int):
    """Marque une tâche comme terminée"""
    with get_db_context() as db:
        task = db.query(ProjectTask).get(task_id)
        if task:
            task.status = "terminé"
            task.completed_at = datetime.now()

            # Mettre à jour le progrès du projet
            project = db.query(Project).get(task.project_id)
            tasks = db.query(ProjectTask).filter(ProjectTask.project_id == project.id).all()

            completed = len([t for t in tasks if t.status == "terminé"])
            total = len(tasks)
            project.progress = int((completed / total) * 100) if total > 0 else 0

            # Mettre à jour le statut du projet
            if project.progress == 100:
                project.status = "terminé"
            elif project.progress > 0:
                project.status = "en cours"

            db.commit()


def supprimer_projet(project_id: int):
    """Supprime un projet"""
    with get_db_context() as db:
        db.query(Project).filter(Project.id == project_id).delete()
        db.commit()


def get_projets_urgents() -> List[Dict]:
    """Détecte les projets urgents ou en retard"""
    urgents = []

    with get_db_context() as db:
        today = date.today()

        # Projets avec échéance proche
        projets = db.query(Project).filter(
            Project.status.in_(["à faire", "en cours"]),
            Project.end_date != None
        ).all()

        for projet in projets:
            if projet.end_date:
                delta = (projet.end_date - today).days

                if delta < 0:
                    urgents.append({
                        "type": "RETARD",
                        "projet": projet.name,
                        "message": f"En retard de {abs(delta)} jours",
                        "id": projet.id
                    })
                elif delta <= 7:
                    urgents.append({
                        "type": "URGENT",
                        "projet": projet.name,
                        "message": f"Échéance dans {delta} jours",
                        "id": projet.id
                    })

    return urgents


# ===================================
# MODULE PRINCIPAL
# ===================================

def app():
    """Module Projets avec IA intégrée"""

    st.title("🏗️ Projets Maison")
    st.caption("Gestion et priorisation intelligente des projets")

    # Récupérer l'agent IA
    agent: AgentIA = st.session_state.get("agent_ia")

    # ===================================
    # ALERTES URGENTES
    # ===================================

    urgents = get_projets_urgents()

    if urgents:
        st.warning(f"⚠️ **{len(urgents)} projet(s) nécessitent attention**")

        for urgent in urgents[:3]:
            if urgent["type"] == "RETARD":
                st.error(f"🔴 **{urgent['projet']}** : {urgent['message']}")
            else:
                st.warning(f"🟡 **{urgent['projet']}** : {urgent['message']}")

        st.markdown("---")

    # ===================================
    # STATISTIQUES RAPIDES
    # ===================================

    df_all = charger_projets()

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)

    with col_s1:
        st.metric("Projets totaux", len(df_all))

    with col_s2:
        en_cours = len(df_all[df_all["statut"] == "en cours"])
        st.metric("En cours", en_cours)

    with col_s3:
        termines = len(df_all[df_all["statut"] == "terminé"])
        st.metric("Terminés", termines)

    with col_s4:
        if not df_all.empty:
            avg_progress = df_all["progres"].mean()
            st.metric("Progression moyenne", f"{avg_progress:.0f}%")
        else:
            st.metric("Progression moyenne", "—")

    st.markdown("---")

    # ===================================
    # TABS PRINCIPAUX
    # ===================================

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Mes Projets",
        "🤖 Priorisation IA",
        "➕ Nouveau Projet",
        "📊 Statistiques"
    ])

    # ===================================
    # TAB 1 : LISTE DES PROJETS
    # ===================================

    with tab1:
        st.subheader("Tous mes projets")

        # Filtres
        col_f1, col_f2, col_f3 = st.columns(3)

        with col_f1:
            filtre_statut = st.selectbox(
                "Statut",
                ["Tous", "à faire", "en cours", "terminé", "annulé"]
            )

        with col_f2:
            filtre_priorite = st.selectbox(
                "Priorité",
                ["Toutes", "haute", "moyenne", "basse"]
            )

        with col_f3:
            tri = st.selectbox(
                "Trier par",
                ["Priorité", "Progression", "Date mise à jour", "Échéance"]
            )

        # Appliquer filtres
        df_filtré = df_all.copy()

        if filtre_statut != "Tous":
            df_filtré = df_filtré[df_filtré["statut"] == filtre_statut]

        if filtre_priorite != "Toutes":
            df_filtré = df_filtré[df_filtré["priorite"] == filtre_priorite]

        # Afficher
        if df_filtré.empty:
            st.info("Aucun projet correspondant aux filtres")
        else:
            for _, projet in df_filtré.iterrows():
                with st.expander(
                        f"{'🟢' if projet['priorite'] == 'haute' else '🟡' if projet['priorite'] == 'moyenne' else '⚪'} **{projet['nom']}** — {projet['progres']}%",
                        expanded=False
                ):
                    col_p1, col_p2 = st.columns([2, 1])

                    with col_p1:
                        st.write(f"**Catégorie :** {projet['categorie']}")
                        st.write(f"**Statut :** {projet['statut']}")
                        st.write(f"**Priorité :** {projet['priorite']}")

                        if projet['debut']:
                            st.write(f"**Début :** {projet['debut'].strftime('%d/%m/%Y')}")
                        if projet['fin']:
                            st.write(f"**Échéance :** {projet['fin'].strftime('%d/%m/%Y')}")

                        if projet['ia_score'] > 0:
                            st.info(f"🤖 Score IA : {projet['ia_score']:.0f}/100")

                    with col_p2:
                        # Jauge progression
                        st.progress(projet['progres'] / 100)
                        st.caption(f"{projet['progres']}% complété")

                    # Tâches du projet
                    st.markdown("**📋 Tâches**")

                    df_taches = charger_taches_projet(projet['id'])

                    if df_taches.empty:
                        st.caption("Aucune tâche. Clique sur '➕ Tâche' pour en ajouter.")
                    else:
                        for _, tache in df_taches.iterrows():
                            col_t1, col_t2, col_t3 = st.columns([3, 1, 1])

                            with col_t1:
                                statut_emoji = "✅" if tache['statut'] == "terminé" else "⏳"
                                st.write(f"{statut_emoji} {tache['nom']}")
                                if tache['description']:
                                    st.caption(tache['description'])

                            with col_t2:
                                if tache['echeance']:
                                    st.caption(f"📅 {tache['echeance'].strftime('%d/%m')}")

                            with col_t3:
                                if tache['statut'] != "terminé":
                                    if st.button("✅", key=f"complete_{tache['id']}", use_container_width=True):
                                        marquer_tache_complete(tache['id'])
                                        st.success("Tâche terminée !")
                                        st.rerun()

                    # Actions projet
                    st.markdown("---")

                    col_act1, col_act2, col_act3 = st.columns(3)

                    with col_act1:
                        if st.button("➕ Tâche", key=f"add_task_{projet['id']}", use_container_width=True):
                            st.session_state[f"adding_task_{projet['id']}"] = True
                            st.rerun()

                    with col_act2:
                        if st.button("✏️ Modifier", key=f"edit_{projet['id']}", use_container_width=True):
                            st.info("Fonctionnalité en développement")

                    with col_act3:
                        if st.button("🗑️ Supprimer", key=f"del_{projet['id']}", type="secondary", use_container_width=True):
                            supprimer_projet(projet['id'])
                            st.success("Projet supprimé")
                            st.rerun()

                    # Formulaire ajout tâche
                    if st.session_state.get(f"adding_task_{projet['id']}", False):
                        with st.form(f"form_task_{projet['id']}"):
                            st.markdown("**Nouvelle tâche**")

                            task_name = st.text_input("Nom *")
                            task_desc = st.text_area("Description")

                            col_tf1, col_tf2 = st.columns(2)

                            with col_tf1:
                                task_due = st.date_input("Échéance", value=None)

                            with col_tf2:
                                task_duration = st.number_input("Durée estimée (min)", 0, 480, 60, 15)

                            col_submit1, col_submit2 = st.columns(2)

                            with col_submit1:
                                if st.form_submit_button("✅ Ajouter"):
                                    if task_name:
                                        ajouter_tache_projet(
                                            projet['id'],
                                            task_name,
                                            task_desc,
                                            task_due,
                                            task_duration
                                        )
                                        st.success("Tâche ajoutée")
                                        del st.session_state[f"adding_task_{projet['id']}"]
                                        st.rerun()

                            with col_submit2:
                                if st.form_submit_button("❌ Annuler"):
                                    del st.session_state[f"adding_task_{projet['id']}"]
                                    st.rerun()

    # ===================================
    # TAB 2 : PRIORISATION IA
    # ===================================

    with tab2:
        st.subheader("🤖 Priorisation intelligente")

        if not agent:
            st.error("Agent IA non disponible")
        else:
            st.info("💡 L'IA analyse tes projets et suggère les priorités selon la méthode Eisenhower")

            df_actifs = charger_projets()
            df_actifs = df_actifs[df_actifs["statut"].isin(["à faire", "en cours"])]

            if df_actifs.empty:
                st.warning("Aucun projet actif à prioriser")
            else:
                if st.button("🤖 Analyser et prioriser", type="primary", use_container_width=True):
                    with st.spinner("🤖 Analyse en cours..."):
                        try:
                            # Préparer données
                            projets_data = [
                                {
                                    "nom": row['nom'],
                                    "statut": row['statut'],
                                    "priorite": row['priorite'],
                                    "progres": row['progres'],
                                    "echeance": str(row['fin']) if row['fin'] else None
                                }
                                for _, row in df_actifs.iterrows()
                            ]

                            contraintes = {
                                "nb_projets": len(projets_data),
                                "urgents": len(urgents)
                            }

                            # Appel IA
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)

                            priorisation = loop.run_until_complete(
                                agent.prioriser_projets(projets_data, contraintes)
                            )

                            st.session_state["priorisation_ia"] = priorisation
                            st.success("✅ Priorisation terminée")

                        except Exception as e:
                            st.error(f"Erreur IA : {e}")

                # Afficher résultats
                if "priorisation_ia" in st.session_state:
                    priorisation = st.session_state["priorisation_ia"]

                    st.markdown("---")
                    st.markdown("### 🎯 Ordre de priorité suggéré")

                    for i, item in enumerate(priorisation, 1):
                        priorite_color = {
                            1: "🔴",
                            2: "🟡",
                            3: "🟢"
                        }.get(item.get("priorite", 3), "⚪")

                        st.markdown(f"{priorite_color} **{i}. {item['projet']}**")
                        st.caption(f"💡 {item.get('raison', 'Priorisation IA')}")
                        st.markdown("---")

                    # Appliquer les priorités
                    if st.button("✅ Appliquer ces priorités", type="primary"):
                        with get_db_context() as db:
                            for item in priorisation:
                                projet = db.query(Project).filter(
                                    Project.name == item['projet']
                                ).first()

                                if projet:
                                    if item['priorite'] == 1:
                                        projet.priority = "haute"
                                    elif item['priorite'] == 2:
                                        projet.priority = "moyenne"
                                    else:
                                        projet.priority = "basse"

                                    projet.ai_priority_score = (4 - item['priorite']) * 33

                            db.commit()

                        st.success("✅ Priorités mises à jour")
                        del st.session_state["priorisation_ia"]
                        st.rerun()

    # ===================================
    # TAB 3 : NOUVEAU PROJET
    # ===================================

    with tab3:
        st.subheader("➕ Créer un nouveau projet")

        with st.form("form_nouveau_projet"):
            nom = st.text_input("Nom du projet *", placeholder="Ex: Aménagement jardin")

            description = st.text_area(
                "Description",
                height=100,
                placeholder="Objectifs, détails du projet..."
            )

            col_n1, col_n2 = st.columns(2)

            with col_n1:
                categorie = st.selectbox(
                    "Catégorie",
                    ["Intérieur", "Extérieur", "Rénovation", "Décoration", "Entretien", "Autre"]
                )

                priorite = st.selectbox(
                    "Priorité",
                    ["haute", "moyenne", "basse"]
                )

            with col_n2:
                date_debut = st.date_input("Date de début (optionnel)", value=None)
                date_fin = st.date_input("Date d'échéance (optionnel)", value=None)

            submitted = st.form_submit_button("💾 Créer le projet", type="primary")

            if submitted:
                if not nom:
                    st.error("Le nom est obligatoire")
                else:
                    project_id = creer_projet(
                        nom, description, categorie, priorite,
                        date_debut, date_fin
                    )

                    st.success(f"✅ Projet '{nom}' créé !")
                    st.balloons()
                    st.rerun()

        st.markdown("---")

        # Templates de projets
        st.markdown("### 📋 Templates de projets")

        templates = [
            {
                "nom": "Rénovation chambre",
                "categorie": "Intérieur",
                "taches": ["Choisir couleurs", "Acheter peinture", "Préparer murs", "Peindre"]
            },
            {
                "nom": "Potager",
                "categorie": "Extérieur",
                "taches": ["Préparer sol", "Acheter graines", "Planter", "Installer arrosage"]
            }
        ]

        for template in templates:
            with st.expander(f"✨ {template['nom']}", expanded=False):
                st.write(f"**Catégorie :** {template['categorie']}")
                st.write("**Tâches suggérées :**")
                for tache in template['taches']:
                    st.write(f"• {tache}")

                if st.button(f"➕ Créer depuis ce template", key=f"template_{template['nom']}"):
                    project_id = creer_projet(
                        template['nom'],
                        f"Projet créé depuis template",
                        template['categorie'],
                        "moyenne"
                    )

                    for tache in template['taches']:
                        ajouter_tache_projet(project_id, tache)

                    st.success(f"✅ Projet '{template['nom']}' créé !")
                    st.rerun()

    # ===================================
    # TAB 4 : STATISTIQUES
    # ===================================

    with tab4:
        st.subheader("📊 Statistiques des projets")

        if df_all.empty:
            st.info("Aucun projet à analyser")
        else:
            # Graphiques
            col_g1, col_g2 = st.columns(2)

            with col_g1:
                st.markdown("**Répartition par statut**")
                statut_counts = df_all["statut"].value_counts()
                st.bar_chart(statut_counts)

            with col_g2:
                st.markdown("**Répartition par catégorie**")
                cat_counts = df_all["categorie"].value_counts()
                st.bar_chart(cat_counts)

            st.markdown("---")

            # Projets par priorité
            st.markdown("### 🎯 Par niveau de priorité")

            for priorite in ["haute", "moyenne", "basse"]:
                df_p = df_all[df_all["priorite"] == priorite]
                st.write(f"**{priorite.capitalize()}** : {len(df_p)} projet(s)")

            st.markdown("---")

            # Progression globale
            st.markdown("### 📈 Progression globale")

            if not df_all.empty:
                avg_progress = df_all["progres"].mean()
                st.progress(avg_progress / 100)
                st.write(f"Progression moyenne : {avg_progress:.1f}%")