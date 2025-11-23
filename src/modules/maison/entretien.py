"""
Module Entretien Maison
Gestion des tâches d'entretien récurrentes
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
from typing import List, Dict


# Templates de tâches d'entretien
TEMPLATES_ENTRETIEN = {
    "Quotidien": [
        "Vaisselle",
        "Rangement cuisine",
        "Ranger salon",
        "Faire les lits"
    ],
    "Hebdomadaire": [
        "Aspirateur",
        "Serpillère",
        "Nettoyer salle de bain",
        "Changer draps",
        "Sortir poubelles",
        "Lessive"
    ],
    "Mensuel": [
        "Nettoyer vitres",
        "Dépoussiérer",
        "Nettoyer frigo",
        "Nettoyer four",
        "Entretien plantes"
    ],
    "Trimestriel": [
        "Réviser chaudière",
        "Nettoyer VMC",
        "Désencombrer placards",
        "Entretien jardin"
    ],
    "Annuel": [
        "Ramonage",
        "Contrôle électrique",
        "Vidange chauffe-eau",
        "Grand nettoyage printemps"
    ]
}


# ===================================
# HELPERS (mock - à implémenter en DB plus tard)
# ===================================

def get_taches_today() -> List[str]:
    """Retourne les tâches du jour"""
    return TEMPLATES_ENTRETIEN["Quotidien"] + TEMPLATES_ENTRETIEN["Hebdomadaire"][:2]


def get_taches_semaine() -> Dict:
    """Retourne les tâches de la semaine"""
    return {
        "Lundi": ["Lessive", "Aspirateur"],
        "Mardi": ["Ranger"],
        "Mercredi": ["Poubelles"],
        "Jeudi": ["Salle de bain"],
        "Vendredi": ["Serpillère"],
        "Samedi": ["Grand ménage"],
        "Dimanche": ["Repos"]
    }


# ===================================
# MODULE PRINCIPAL
# ===================================

def app():
    """Module Entretien Maison"""

    st.title("🔧 Entretien Maison")
    st.caption("Gestion des tâches d'entretien récurrentes")

    st.warning("⚠️ **Module en développement** - Fonctionnalités à venir")

    # ===================================
    # TABS
    # ===================================

    tab1, tab2, tab3 = st.tabs([
        "📋 Aujourd'hui",
        "📅 Planning Semaine",
        "🗂️ Templates"
    ])

    # ===================================
    # TAB 1 : AUJOURD'HUI
    # ===================================

    with tab1:
        st.subheader("Tâches d'entretien du jour")

        taches = get_taches_today()

        st.info(f"📝 {len(taches)} tâche(s) prévue(s) aujourd'hui")

        # Checklist
        for i, tache in enumerate(taches):
            col1, col2 = st.columns([3, 1])

            with col1:
                checked = st.checkbox(tache, key=f"task_{i}")

            with col2:
                if checked:
                    st.success("✅")

        st.markdown("---")

        # Actions rapides
        st.markdown("### ⚡ Actions rapides")

        col_a1, col_a2 = st.columns(2)

        with col_a1:
            if st.button("✅ Tout marquer comme fait", use_container_width=True):
                st.success("Toutes les tâches marquées !")
                st.balloons()

        with col_a2:
            if st.button("➕ Ajouter tâche ponctuelle", use_container_width=True):
                st.info("Fonctionnalité à venir")

    # ===================================
    # TAB 2 : PLANNING SEMAINE
    # ===================================

    with tab2:
        st.subheader("Planning de la semaine")

        planning = get_taches_semaine()

        today = date.today()

        for i, (jour, taches) in enumerate(planning.items()):
            jour_date = today + timedelta(days=i - today.weekday())
            is_today = jour_date == today

            with st.expander(
                    f"{'🔵 ' if is_today else ''}{jour} {jour_date.strftime('%d/%m')}",
                    expanded=is_today
            ):
                if taches:
                    for tache in taches:
                        st.write(f"• {tache}")
                else:
                    st.caption("Aucune tâche prévue")

    # ===================================
    # TAB 3 : TEMPLATES
    # ===================================

    with tab3:
        st.subheader("Templates de tâches d'entretien")

        st.info("💡 Organise tes tâches par fréquence")

        for frequence, taches in TEMPLATES_ENTRETIEN.items():
            with st.expander(f"📋 {frequence}", expanded=False):
                for tache in taches:
                    st.write(f"• {tache}")

                if st.button(f"➕ Utiliser ce template", key=f"template_{frequence}"):
                    st.success(f"Template '{frequence}' activé !")

        st.markdown("---")

        st.markdown("### 💡 Conseils d'organisation")

        conseils = [
            "🗓️ Répartir les tâches sur la semaine pour éviter la surcharge",
            "⏰ Définir des créneaux fixes (ex: samedi matin = ménage)",
            "👥 Impliquer toute la famille dans les tâches",
            "🎯 Commencer par les tâches rapides pour garder la motivation",
            "📱 Utiliser les rappels pour ne rien oublier"
        ]

        for conseil in conseils:
            st.info(conseil)