"""
Module Batch Cooking avec Agent IA intégré
Planification automatique des repas avec suggestions intelligentes
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import asyncio
from typing import List, Dict

from src.core.database import get_db_context
from src.core.models import BatchMeal, Recipe, Ingredient, RecipeIngredient, InventoryItem
from src.core.ai_agent import AgentIA


# ===================================
# HELPERS
# ===================================

def charger_batch_meals(periode: str = "future") -> pd.DataFrame:
    """Charge les repas planifiés"""
    with get_db_context() as db:
        query = db.query(
            BatchMeal.id,
            Recipe.name.label("recette"),
            BatchMeal.scheduled_date,
            BatchMeal.portions,
            BatchMeal.status,
            BatchMeal.ai_planned,
            BatchMeal.notes
        ).join(
            Recipe, BatchMeal.recipe_id == Recipe.id
        )

        today = date.today()

        if periode == "future":
            query = query.filter(BatchMeal.scheduled_date >= today)
        elif periode == "past":
            query = query.filter(BatchMeal.scheduled_date < today)
        elif periode == "week":
            week_end = today + timedelta(days=7)
            query = query.filter(
                BatchMeal.scheduled_date.between(today, week_end)
            )

        meals = query.order_by(BatchMeal.scheduled_date).all()

        return pd.DataFrame([{
            "id": m.id,
            "recette": m.recette,
            "date": m.scheduled_date,
            "portions": m.portions,
            "statut": m.status,
            "ia": "🤖" if m.ai_planned else "",
            "notes": m.notes or ""
        } for m in meals])


def planifier_repas(
        recipe_id: int,
        scheduled_date: date,
        portions: int = 4,
        ai_planned: bool = False,
        notes: str = ""
) -> int:
    """Planifie un repas"""
    with get_db_context() as db:
        batch = BatchMeal(
            recipe_id=recipe_id,
            scheduled_date=scheduled_date,
            portions=portions,
            status="à faire",
            ai_planned=ai_planned,
            notes=notes
        )
        db.add(batch)
        db.commit()
        return batch.id


def verifier_ingredients_disponibles(recipe_id: int) -> Dict:
    """Vérifie si les ingrédients sont disponibles en stock"""
    with get_db_context() as db:
        # Ingrédients nécessaires
        needed = db.query(
            Ingredient.name,
            RecipeIngredient.quantity,
            Ingredient.unit
        ).join(
            RecipeIngredient, Ingredient.id == RecipeIngredient.ingredient_id
        ).filter(
            RecipeIngredient.recipe_id == recipe_id
        ).all()

        manquants = []
        disponibles = []

        for ing_name, qty_needed, unit in needed:
            # Vérifier dans l'inventaire
            inventory = db.query(InventoryItem).join(
                Ingredient
            ).filter(
                Ingredient.name == ing_name
            ).first()

            if not inventory or inventory.quantity < qty_needed:
                qty_dispo = inventory.quantity if inventory else 0
                manquants.append({
                    "nom": ing_name,
                    "besoin": qty_needed,
                    "disponible": qty_dispo,
                    "unite": unit
                })
            else:
                disponibles.append(ing_name)

        return {
            "faisable": len(manquants) == 0,
            "manquants": manquants,
            "disponibles": disponibles
        }


def supprimer_batch(batch_id: int):
    """Supprime un repas planifié"""
    with get_db_context() as db:
        db.query(BatchMeal).filter(BatchMeal.id == batch_id).delete()
        db.commit()


def marquer_complete(batch_id: int):
    """Marque un repas comme terminé"""
    with get_db_context() as db:
        batch = db.query(BatchMeal).filter(BatchMeal.id == batch_id).first()
        if batch:
            batch.status = "terminé"
            db.commit()


# ===================================
# MODULE PRINCIPAL
# ===================================

def app():
    """Module Batch Cooking avec IA intégrée"""

    st.title("🥘 Batch Cooking Intelligent")
    st.caption("Planification automatique des repas avec l'IA")

    # Récupérer l'agent IA
    agent: AgentIA = st.session_state.get("agent_ia")

    # ===================================
    # TABS PRINCIPAUX
    # ===================================

    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 Planning",
        "🤖 Génération Auto IA",
        "➕ Planifier Manuel",
        "📊 Historique"
    ])

    # ===================================
    # TAB 1 : PLANNING ACTUEL
    # ===================================

    with tab1:
        st.subheader("Planning de la semaine")

        # Filtres
        col_p1, col_p2, col_p3 = st.columns([2, 1, 1])

        with col_p1:
            periode = st.selectbox(
                "Période",
                ["Cette semaine", "Tous les repas à venir", "Historique"]
            )

        with col_p2:
            vue = st.radio("Vue", ["📅 Calendrier", "📋 Liste"], horizontal=True)

        with col_p3:
            if st.button("🔄 Rafraîchir", use_container_width=True):
                st.rerun()

        # Charger les données
        if "semaine" in periode:
            df = charger_batch_meals("week")
        elif "venir" in periode:
            df = charger_batch_meals("future")
        else:
            df = charger_batch_meals("past")

        if df.empty:
            st.info("Aucun repas planifié pour cette période. Utilise l'IA pour générer un planning !")

            if st.button("✨ Générer un planning automatique"):
                st.session_state["active_tab"] = 1  # Aller au tab IA
                st.rerun()
        else:
            # Statistiques rapides
            col_s1, col_s2, col_s3 = st.columns(3)

            with col_s1:
                st.metric("Repas planifiés", len(df))

            with col_s2:
                ia_count = len(df[df["ia"] == "🤖"])
                st.metric("Générés par IA", ia_count)

            with col_s3:
                termines = len(df[df["statut"] == "terminé"])
                st.metric("Terminés", termines)

            st.markdown("---")

            # Affichage selon la vue
            if "Calendrier" in vue:
                # Vue calendrier par jour
                st.markdown("### 📆 Vue calendrier")

                # Grouper par date
                for date_val in sorted(df["date"].unique()):
                    jour_df = df[df["date"] == date_val]
                    jour_str = date_val.strftime("%A %d/%m/%Y")

                    with st.expander(f"📅 {jour_str} ({len(jour_df)} repas)", expanded=True):
                        for _, repas in jour_df.iterrows():
                            col_r1, col_r2, col_r3 = st.columns([3, 1, 1])

                            with col_r1:
                                ia_badge = repas["ia"]
                                statut_emoji = "✅" if repas["statut"] == "terminé" else "🍳"
                                st.markdown(f"{statut_emoji} {ia_badge} **{repas['recette']}** ({repas['portions']} portions)")
                                if repas["notes"]:
                                    st.caption(repas["notes"])

                            with col_r2:
                                if repas["statut"] != "terminé" and st.button(
                                        "✅ Terminé",
                                        key=f"done_{repas['id']}"
                                ):
                                    marquer_complete(repas["id"])
                                    st.success("Marqué comme terminé")
                                    st.rerun()

                            with col_r3:
                                if st.button("🗑️", key=f"del_{repas['id']}"):
                                    supprimer_batch(repas["id"])
                                    st.rerun()

            else:
                # Vue liste
                st.dataframe(
                    df[["date", "recette", "portions", "statut", "ia"]],
                    use_container_width=True,
                    column_config={
                        "date": st.column_config.DateColumn("Date", format="DD/MM/YYYY"),
                        "recette": "Recette",
                        "portions": st.column_config.NumberColumn("Portions"),
                        "statut": "Statut",
                        "ia": "IA"
                    }
                )

    # ===================================
    # TAB 2 : GÉNÉRATION AUTOMATIQUE IA
    # ===================================

    with tab2:
        st.subheader("🤖 Génération automatique de planning")

        if not agent:
            st.error("Agent IA non disponible")
        else:
            st.info("💡 L'IA va analyser ton inventaire, tes recettes et générer un planning optimal pour la semaine.")

            # Paramètres
            col_g1, col_g2 = st.columns(2)

            with col_g1:
                nb_jours = st.slider("Nombre de jours à planifier", 3, 14, 7)

                preferences = st.multiselect(
                    "Préférences (optionnel)",
                    ["Végétarien", "Rapide (<30min)", "Économique", "Équilibré", "Varié"]
                )

            with col_g2:
                portions_defaut = st.number_input("Portions par défaut", 2, 8, 4)

                date_debut = st.date_input(
                    "Commencer à partir de",
                    value=date.today()
                )

            generer = st.button(
                "✨ Générer le planning avec l'IA",
                type="primary",
                use_container_width=True
            )

            if generer:
                with st.spinner("🤖 L'IA crée ton planning..."):
                    try:
                        # Récupérer les recettes disponibles
                        with get_db_context() as db:
                            recettes = db.query(Recipe.name).all()
                            recettes_noms = [r.name for r in recettes]

                        if not recettes_noms:
                            st.error("Aucune recette disponible. Ajoute des recettes d'abord.")
                        else:
                            # Appel IA
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)

                            contraintes = {
                                "preferences": preferences,
                                "portions": portions_defaut,
                                "nb_jours": nb_jours
                            }

                            planning = loop.run_until_complete(
                                agent.generer_planning_semaine(
                                    contraintes=contraintes,
                                    recettes_dispo=recettes_noms
                                )
                            )

                            st.session_state["planning_genere"] = planning
                            st.success("✅ Planning généré !")

                    except Exception as e:
                        st.error(f"Erreur IA : {e}")

            # Afficher le planning généré
            if "planning_genere" in st.session_state:
                planning = st.session_state["planning_genere"]

                st.markdown("---")
                st.markdown("### 📋 Planning proposé")

                if "planning" in planning:
                    # Créer un DataFrame
                    planning_df = pd.DataFrame(planning["planning"])

                    if not planning_df.empty:
                        st.dataframe(
                            planning_df,
                            use_container_width=True,
                            column_config={
                                "jour": "Jour",
                                "repas": "Recette",
                                "raison": "Pourquoi cette recette ?"
                            }
                        )

                        # Liste de courses associée
                        if "courses" in planning:
                            st.markdown("### 🛒 Liste de courses suggérée")
                            for item in planning["courses"]:
                                st.write(f"• {item}")

                        # Bouton validation
                        if st.button("✅ Valider et enregistrer ce planning", type="primary"):
                            with get_db_context() as db:
                                # Récupérer les IDs des recettes
                                for i, row in enumerate(planning["planning"]):
                                    recette_nom = row["repas"]

                                    recipe = db.query(Recipe).filter(
                                        Recipe.name.ilike(f"%{recette_nom}%")
                                    ).first()

                                    if recipe:
                                        date_repas = date_debut + timedelta(days=i)

                                        planifier_repas(
                                            recipe_id=recipe.id,
                                            scheduled_date=date_repas,
                                            portions=portions_defaut,
                                            ai_planned=True,
                                            notes=f"Généré par IA : {row.get('raison', '')}"
                                        )

                                db.commit()

                            st.success("🎉 Planning enregistré !")
                            st.balloons()
                            del st.session_state["planning_genere"]
                            st.rerun()
                else:
                    st.json(planning)

    # ===================================
    # TAB 3 : PLANIFIER MANUELLEMENT
    # ===================================

    with tab3:
        st.subheader("➕ Planifier un repas manuellement")

        # Récupérer les recettes
        with get_db_context() as db:
            recettes = db.query(Recipe.id, Recipe.name).order_by(Recipe.name).all()

        if not recettes:
            st.warning("Aucune recette disponible. Va dans le module Recettes pour en ajouter.")
        else:
            with st.form("form_planifier"):
                recette_select = st.selectbox(
                    "Choisir une recette *",
                    [r.name for r in recettes]
                )

                col_f1, col_f2 = st.columns(2)

                with col_f1:
                    date_repas = st.date_input(
                        "Date du repas *",
                        value=date.today()
                    )
                    portions = st.number_input(
                        "Nombre de portions",
                        min_value=1,
                        max_value=12,
                        value=4
                    )

                with col_f2:
                    type_repas = st.selectbox(
                        "Type de repas",
                        ["Déjeuner", "Dîner", "Goûter", "Brunch"]
                    )
                    notes = st.text_area(
                        "Notes (optionnel)",
                        placeholder="Ex: Inviter les grands-parents"
                    )

                # Vérification disponibilité
                recipe_id = next(r.id for r in recettes if r.name == recette_select)

                verif = verifier_ingredients_disponibles(recipe_id)

                if not verif["faisable"]:
                    st.warning("⚠️ Ingrédients manquants :")
                    for ing in verif["manquants"]:
                        manque = ing["besoin"] - ing["disponible"]
                        st.write(f"• {ing['nom']} : il manque {manque} {ing['unite']}")

                submitted = st.form_submit_button(
                    "📅 Planifier ce repas",
                    type="primary"
                )

                if submitted:
                    planifier_repas(
                        recipe_id=recipe_id,
                        scheduled_date=date_repas,
                        portions=portions,
                        notes=f"{type_repas} - {notes}"
                    )

                    st.success(f"✅ {recette_select} planifié pour le {date_repas.strftime('%d/%m/%Y')}")
                    st.balloons()
                    st.rerun()

    # ===================================
    # TAB 4 : HISTORIQUE
    # ===================================

    with tab4:
        st.subheader("📊 Historique et statistiques")

        df_hist = charger_batch_meals("past")

        if df_hist.empty:
            st.info("Pas encore d'historique")
        else:
            # Métriques
            col_h1, col_h2, col_h3 = st.columns(3)

            with col_h1:
                st.metric("Total repas réalisés", len(df_hist))

            with col_h2:
                ia_hist = len(df_hist[df_hist["ia"] == "🤖"])
                st.metric("Planifiés par IA", ia_hist)

            with col_h3:
                portions_total = df_hist["portions"].sum()
                st.metric("Portions totales", int(portions_total))

            # Tableau historique
            st.markdown("### 📋 Historique des repas")

            st.dataframe(
                df_hist[["date", "recette", "portions", "statut"]].sort_values("date", ascending=False),
                use_container_width=True
            )

            # Recettes les plus cuisinées
            st.markdown("### 🔝 Recettes les plus cuisinées")

            top_recettes = df_hist["recette"].value_counts().head(5)

            for recette, count in top_recettes.items():
                st.write(f"• **{recette}** : {count} fois")

            # Export
            st.markdown("---")
            if st.button("📤 Exporter l'historique (CSV)"):
                csv = df_hist.to_csv(index=False)
                st.download_button(
                    "Télécharger",
                    csv,
                    "historique_batch_cooking.csv",
                    "text/csv"
                )