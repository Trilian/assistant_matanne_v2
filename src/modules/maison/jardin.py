"""
Module Jardin avec Agent IA et Météo intégrés
Gestion du jardin avec suggestions selon saison et météo
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import asyncio
from typing import List, Dict

from src.core.database import get_db_context
from src.core.models import GardenItem, GardenLog
from src.core.ai_agent import AgentIA
from src.core.config import settings


# ===================================
# HELPERS
# ===================================

def charger_plantes() -> pd.DataFrame:
    """Charge toutes les plantes du jardin"""
    with get_db_context() as db:
        items = db.query(GardenItem).order_by(GardenItem.name).all()

        return pd.DataFrame([{
            "id": i.id,
            "nom": i.name,
            "categorie": i.category,
            "plantation": i.planting_date,
            "recolte": i.harvest_date,
            "quantite": i.quantity,
            "emplacement": i.location or "—",
            "arrosage_freq": i.watering_frequency_days,
            "dernier_arrosage": i.last_watered,
            "notes": i.notes or ""
        } for i in items])


def ajouter_plante(
        nom: str,
        categorie: str,
        plantation: date,
        quantite: int,
        emplacement: str,
        freq_arrosage: int,
        recolte: date = None
):
    """Ajoute une plante au jardin"""
    with get_db_context() as db:
        plante = GardenItem(
            name=nom,
            category=categorie,
            planting_date=plantation,
            harvest_date=recolte,
            quantity=quantite,
            location=emplacement,
            watering_frequency_days=freq_arrosage,
            last_watered=date.today()
        )
        db.add(plante)
        db.commit()


def arroser_plante(item_id: int):
    """Marque une plante comme arrosée"""
    with get_db_context() as db:
        plante = db.query(GardenItem).get(item_id)
        if plante:
            plante.last_watered = date.today()

            # Ajouter log
            log = GardenLog(
                item_id=item_id,
                action="Arrosage",
                date=date.today(),
                notes="Arrosage régulier"
            )
            db.add(log)
            db.commit()


def ajouter_log(item_id: int, action: str, notes: str = ""):
    """Ajoute une entrée au journal du jardin"""
    with get_db_context() as db:
        log = GardenLog(
            item_id=item_id,
            action=action,
            date=date.today(),
            notes=notes
        )
        db.add(log)
        db.commit()


def get_plantes_a_arroser() -> List[Dict]:
    """Détecte les plantes qui ont besoin d'eau"""
    a_arroser = []

    with get_db_context() as db:
        today = date.today()
        plantes = db.query(GardenItem).all()

        for plante in plantes:
            if plante.last_watered:
                delta = (today - plante.last_watered).days
                if delta >= plante.watering_frequency_days:
                    a_arroser.append({
                        "id": plante.id,
                        "nom": plante.name,
                        "jours": delta,
                        "urgence": "haute" if delta > plante.watering_frequency_days + 1 else "normale"
                    })

    return a_arroser


def get_recoltes_proches() -> List[Dict]:
    """Détecte les récoltes à venir"""
    recoltes = []

    with get_db_context() as db:
        today = date.today()
        future = today + timedelta(days=14)

        plantes = db.query(GardenItem).filter(
            GardenItem.harvest_date != None,
            GardenItem.harvest_date.between(today, future)
        ).all()

        for plante in plantes:
            delta = (plante.harvest_date - today).days
            recoltes.append({
                "nom": plante.name,
                "date": plante.harvest_date,
                "jours": delta
            })

    return recoltes


def get_meteo_mock() -> Dict:
    """Récupère la météo (mock pour démo)"""
    # TODO: Intégrer vraie API météo
    return {
        "condition": "Ensoleillé",
        "temp": 22,
        "humidity": 65,
        "precipitation": 0
    }


def get_saison() -> str:
    """Détermine la saison actuelle"""
    month = date.today().month

    if month in [3, 4, 5]:
        return "Printemps"
    elif month in [6, 7, 8]:
        return "Été"
    elif month in [9, 10, 11]:
        return "Automne"
    else:
        return "Hiver"


# ===================================
# MODULE PRINCIPAL
# ===================================

def app():
    """Module Jardin avec IA et Météo intégrées"""

    st.title("🌱 Jardin Intelligent")
    st.caption("Gestion du jardin avec météo et conseils IA")

    # Récupérer l'agent IA
    agent: AgentIA = st.session_state.get("agent_ia")

    # ===================================
    # MÉTÉO & SAISON
    # ===================================

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)

    meteo = get_meteo_mock()
    saison = get_saison()

    with col_m1:
        st.metric("🌤️ Météo", meteo['condition'])

    with col_m2:
        st.metric("🌡️ Température", f"{meteo['temp']}°C")

    with col_m3:
        st.metric("💧 Humidité", f"{meteo['humidity']}%")

    with col_m4:
        st.metric("🌸 Saison", saison)

    st.markdown("---")

    # ===================================
    # ALERTES ARROSAGE
    # ===================================

    a_arroser = get_plantes_a_arroser()

    if a_arroser:
        urgentes = [p for p in a_arroser if p['urgence'] == 'haute']

        if urgentes:
            st.error(f"💧 **{len(urgentes)} plante(s) à arroser URGENT**")
        else:
            st.warning(f"💧 **{len(a_arroser)} plante(s) à arroser aujourd'hui**")

        for plante in a_arroser[:3]:
            col_a1, col_a2 = st.columns([3, 1])

            with col_a1:
                emoji = "🔴" if plante['urgence'] == 'haute' else "🟡"
                st.write(f"{emoji} **{plante['nom']}** — Dernier arrosage il y a {plante['jours']} jours")

            with col_a2:
                if st.button("💧 Arrosé", key=f"water_{plante['id']}", use_container_width=True):
                    arroser_plante(plante['id'])
                    st.success("Arrosage noté !")
                    st.rerun()

        st.markdown("---")

    # Récoltes proches
    recoltes = get_recoltes_proches()

    if recoltes:
        st.info(f"🌾 **{len(recoltes)} récolte(s) à venir dans les 2 semaines**")
        for recolte in recoltes:
            st.write(f"• **{recolte['nom']}** : dans {recolte['jours']} jours ({recolte['date'].strftime('%d/%m')})")
        st.markdown("---")

    # ===================================
    # TABS PRINCIPAUX
    # ===================================

    tab1, tab2, tab3, tab4 = st.tabs([
        "🌿 Mon Jardin",
        "🤖 Conseils IA",
        "➕ Ajouter Plante",
        "📊 Journal"
    ])

    # ===================================
    # TAB 1 : MON JARDIN
    # ===================================

    with tab1:
        st.subheader("Mes plantes")

        df = charger_plantes()

        if df.empty:
            st.info("Ton jardin est vide. Commence par ajouter des plantes !")
        else:
            # Filtres
            col_f1, col_f2 = st.columns(2)

            with col_f1:
                categories = ["Toutes"] + sorted(df["categorie"].unique().tolist())
                filtre_cat = st.selectbox("Catégorie", categories)

            with col_f2:
                filtre_emplacement = st.selectbox(
                    "Emplacement",
                    ["Tous"] + sorted([e for e in df["emplacement"].unique() if e != "—"])
                )

            # Appliquer filtres
            df_filtre = df.copy()

            if filtre_cat != "Toutes":
                df_filtre = df_filtre[df_filtre["categorie"] == filtre_cat]

            if filtre_emplacement != "Tous":
                df_filtre = df_filtre[df_filtre["emplacement"] == filtre_emplacement]

            # Afficher plantes
            for _, plante in df_filtre.iterrows():
                with st.expander(
                        f"🌱 **{plante['nom']}** ({plante['quantite']}x) — {plante['categorie']}",
                        expanded=False
                ):
                    col_p1, col_p2 = st.columns([2, 1])

                    with col_p1:
                        st.write(f"**Emplacement :** {plante['emplacement']}")
                        st.write(f"**Planté le :** {plante['plantation'].strftime('%d/%m/%Y')}")

                        if plante['recolte']:
                            st.write(f"**Récolte prévue :** {plante['recolte'].strftime('%d/%m/%Y')}")

                        st.write(f"**Arrosage :** tous les {plante['arrosage_freq']} jours")

                        if plante['dernier_arrosage']:
                            delta = (date.today() - plante['dernier_arrosage']).days
                            st.write(f"**Dernier arrosage :** il y a {delta} jours")

                        if plante['notes']:
                            st.caption(f"Notes : {plante['notes']}")

                    with col_p2:
                        # Actions rapides
                        if st.button("💧 Arroser", key=f"arroser_{plante['id']}", use_container_width=True):
                            arroser_plante(plante['id'])
                            st.success("Arrosage noté")
                            st.rerun()

                        if st.button("🌾 Récolter", key=f"harvest_{plante['id']}", use_container_width=True):
                            ajouter_log(plante['id'], "Récolte", f"Récolte de {plante['quantite']}x {plante['nom']}")
                            st.success("Récolte notée")
                            st.rerun()

                        if st.button("✂️ Tailler", key=f"prune_{plante['id']}", use_container_width=True):
                            ajouter_log(plante['id'], "Taille", "Taille d'entretien")
                            st.success("Taille notée")
                            st.rerun()

                        if st.button("📝 Log", key=f"log_{plante['id']}", use_container_width=True):
                            st.session_state[f"logging_{plante['id']}"] = True

                    # Formulaire log personnalisé
                    if st.session_state.get(f"logging_{plante['id']}", False):
                        with st.form(f"form_log_{plante['id']}"):
                            action = st.selectbox(
                                "Action",
                                ["Arrosage", "Taille", "Fertilisation", "Récolte", "Observation", "Autre"]
                            )
                            notes_log = st.text_area("Notes")

                            col_l1, col_l2 = st.columns(2)

                            with col_l1:
                                if st.form_submit_button("✅ Enregistrer"):
                                    ajouter_log(plante['id'], action, notes_log)
                                    st.success("Log enregistré")
                                    del st.session_state[f"logging_{plante['id']}"]
                                    st.rerun()

                            with col_l2:
                                if st.form_submit_button("❌ Annuler"):
                                    del st.session_state[f"logging_{plante['id']}"]
                                    st.rerun()

    # ===================================
    # TAB 2 : CONSEILS IA
    # ===================================

    with tab2:
        st.subheader("🤖 Conseils jardinage intelligents")

        if not agent:
            st.error("Agent IA non disponible")
        else:
            st.info(f"💡 Conseils adaptés à la saison ({saison}) et à la météo actuelle")

            if st.button("🤖 Demander conseils IA", type="primary", use_container_width=True):
                with st.spinner("🤖 L'IA analyse ton jardin..."):
                    try:
                        # Préparer données
                        df_jardin = charger_plantes()
                        plantes_actuelles = df_jardin["nom"].tolist() if not df_jardin.empty else []

                        # Appel IA
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                        conseils = loop.run_until_complete(
                            agent.suggerer_jardin(saison, meteo, plantes_actuelles)
                        )

                        st.session_state["conseils_jardin"] = conseils
                        st.success("✅ Conseils générés")

                    except Exception as e:
                        st.error(f"Erreur IA : {e}")

            # Afficher conseils
            if "conseils_jardin" in st.session_state:
                conseils = st.session_state["conseils_jardin"]

                st.markdown("---")

                # Actions du jour
                if "actions_jour" in conseils and conseils["actions_jour"]:
                    st.markdown("### 🎯 Actions recommandées aujourd'hui")
                    for action in conseils["actions_jour"]:
                        st.success(f"✅ {action}")

                # Plantations suggérées
                if "plantations" in conseils and conseils["plantations"]:
                    st.markdown("### 🌱 Plantations de saison")
                    for plante in conseils["plantations"]:
                        st.info(f"🌿 {plante}")

                # Entretien
                if "entretien" in conseils and conseils["entretien"]:
                    st.markdown("### 🔧 Entretien recommandé")
                    for task in conseils["entretien"]:
                        st.info(f"🔨 {task}")

                # Alertes
                if "alertes" in conseils and conseils["alertes"]:
                    st.markdown("### ⚠️ Alertes météo")
                    for alerte in conseils["alertes"]:
                        st.warning(f"⚠️ {alerte}")

            # Calendrier des plantations
            st.markdown("---")
            st.markdown("### 📅 Calendrier des plantations par saison")

            calendrier = {
                "Printemps": ["Tomates", "Courgettes", "Salades", "Radis", "Carottes"],
                "Été": ["Haricots verts", "Concombres", "Aubergines", "Poivrons"],
                "Automne": ["Épinards", "Mâche", "Oignons", "Ail", "Choux"],
                "Hiver": ["Fèves", "Petits pois", "Échalotes"]
            }

            with st.expander(f"🌸 Plantations {saison}", expanded=True):
                for plante in calendrier.get(saison, []):
                    st.write(f"• {plante}")

    # ===================================
    # TAB 3 : AJOUTER PLANTE
    # ===================================

    with tab3:
        st.subheader("➕ Ajouter une plante au jardin")

        with st.form("form_add_plante"):
            nom = st.text_input("Nom de la plante *", placeholder="Ex: Tomates cerises")

            col_a1, col_a2 = st.columns(2)

            with col_a1:
                categorie = st.selectbox(
                    "Catégorie",
                    ["Légume", "Fruit", "Aromatique", "Fleur", "Arbuste", "Autre"]
                )

                quantite = st.number_input("Quantité", 1, 100, 1)

                emplacement = st.selectbox(
                    "Emplacement",
                    ["Potager", "Jardinière", "Serre", "Balcon", "Pleine terre", "Autre"]
                )

            with col_a2:
                plantation = st.date_input("Date de plantation", value=date.today())

                recolte = st.date_input(
                    "Date de récolte prévue (optionnel)",
                    value=None
                )

                freq_arrosage = st.number_input(
                    "Fréquence d'arrosage (jours)",
                    1, 14, 2
                )

            notes = st.text_area("Notes (optionnel)", placeholder="Variété, exposition, particularités...")

            submitted = st.form_submit_button("🌱 Ajouter au jardin", type="primary")

            if submitted:
                if not nom:
                    st.error("Le nom est obligatoire")
                else:
                    ajouter_plante(
                        nom, categorie, plantation, quantite,
                        emplacement, freq_arrosage, recolte
                    )
                    st.success(f"✅ {nom} ajouté au jardin !")
                    st.balloons()
                    st.rerun()

        st.markdown("---")

        # Suggestions rapides
        st.markdown("### ⚡ Ajouts rapides")

        suggestions = [
            {"nom": "Tomates cerises", "cat": "Légume", "freq": 2},
            {"nom": "Basilic", "cat": "Aromatique", "freq": 1},
            {"nom": "Fraisiers", "cat": "Fruit", "freq": 2},
            {"nom": "Courgettes", "cat": "Légume", "freq": 3}
        ]

        col_s1, col_s2 = st.columns(2)

        for i, sugg in enumerate(suggestions):
            col = col_s1 if i % 2 == 0 else col_s2

            with col:
                if st.button(
                        f"🌱 {sugg['nom']}",
                        use_container_width=True,
                        key=f"quick_{sugg['nom']}"
                ):
                    ajouter_plante(
                        sugg['nom'],
                        sugg['cat'],
                        date.today(),
                        1,
                        "Potager",
                        sugg['freq']
                    )
                    st.success(f"{sugg['nom']} ajouté !")
                    st.rerun()

    # ===================================
    # TAB 4 : JOURNAL
    # ===================================

    with tab4:
        st.subheader("📊 Journal du jardin")

        df = charger_plantes()

        if df.empty:
            st.info("Aucune plante dans le jardin")
        else:
            # Statistiques
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

            with col_stat1:
                st.metric("Plantes totales", len(df))

            with col_stat2:
                categories = df["categorie"].nunique()
                st.metric("Catégories", categories)

            with col_stat3:
                a_arroser_count = len(get_plantes_a_arroser())
                st.metric("À arroser", a_arroser_count, delta_color="inverse")

            with col_stat4:
                recoltes_count = len(get_recoltes_proches())
                st.metric("Récoltes à venir", recoltes_count)

            st.markdown("---")

            # Historique des actions
            st.markdown("### 📋 Dernières actions")

            with get_db_context() as db:
                logs = db.query(GardenLog, GardenItem).join(
                    GardenItem, GardenLog.item_id == GardenItem.id
                ).order_by(
                    GardenLog.date.desc()
                ).limit(20).all()

                if logs:
                    for log, plante in logs:
                        col_log1, col_log2 = st.columns([3, 1])

                        with col_log1:
                            st.write(f"**{log.date.strftime('%d/%m/%Y')}** — {log.action} : {plante.name}")
                            if log.notes:
                                st.caption(log.notes)

                        with col_log2:
                            st.caption(f"🌱 {plante.name}")
                else:
                    st.info("Aucune action enregistrée encore")

            # Export
            st.markdown("---")
            if st.button("📤 Exporter le jardin (CSV)"):
                csv = df.to_csv(index=False)
                st.download_button(
                    "Télécharger",
                    csv,
                    f"jardin_{date.today().strftime('%Y%m%d')}.csv",
                    "text/csv"
                )