"""
Module Recettes avec Agent IA intégré
Suggestions intelligentes, génération automatique, import
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import List, Dict
import asyncio

from src.core.database import get_db_context
from src.core.models import Recipe, Ingredient, RecipeIngredient, InventoryItem
from src.core.ai_agent import AgentIA


# ===================================
# HELPERS
# ===================================

def get_inventaire_disponible() -> List[Dict]:
    """Récupère l'inventaire disponible pour l'IA"""
    with get_db_context() as db:
        items = db.query(
            Ingredient.name,
            InventoryItem.quantity,
            Ingredient.unit
        ).join(
            InventoryItem, Ingredient.id == InventoryItem.ingredient_id
        ).filter(
            InventoryItem.quantity > 0
        ).all()

        return [
            {"nom": item.name, "quantite": item.quantity, "unite": item.unit}
            for item in items
        ]


def sauvegarder_recette(
        nom: str,
        categorie: str,
        instructions: str,
        prep_time: int,
        cook_time: int,
        servings: int,
        ingredients: List[Dict],
        ai_generated: bool = False,
        ai_score: float = None
) -> int:
    """Sauvegarde une recette en base"""
    with get_db_context() as db:
        # Créer la recette
        recette = Recipe(
            name=nom,
            category=categorie,
            instructions=instructions,
            prep_time=prep_time,
            cook_time=cook_time,
            servings=servings,
            ai_generated=ai_generated,
            ai_score=ai_score
        )
        db.add(recette)
        db.flush()

        # Ajouter les ingrédients
        for ing in ingredients:
            # Vérifier si l'ingrédient existe
            ingredient = db.query(Ingredient).filter(
                Ingredient.name == ing["nom"]
            ).first()

            if not ingredient:
                # Créer l'ingrédient
                ingredient = Ingredient(
                    name=ing["nom"],
                    unit=ing.get("unite", "")
                )
                db.add(ingredient)
                db.flush()

            # Lier à la recette
            recipe_ing = RecipeIngredient(
                recipe_id=recette.id,
                ingredient_id=ingredient.id,
                quantity=ing["quantite"],
                unit=ing.get("unite", "")
            )
            db.add(recipe_ing)

        db.commit()
        return recette.id


def charger_recettes(search: str = "", categorie: str = "") -> pd.DataFrame:
    """Charge les recettes avec filtres"""
    with get_db_context() as db:
        query = db.query(Recipe)

        if search:
            query = query.filter(Recipe.name.ilike(f"%{search}%"))

        if categorie:
            query = query.filter(Recipe.category == categorie)

        recettes = query.order_by(Recipe.created_at.desc()).all()

        return pd.DataFrame([{
            "id": r.id,
            "nom": r.name,
            "categorie": r.category,
            "temps_prep": r.prep_time,
            "temps_cuisson": r.cook_time,
            "portions": r.servings,
            "ia": "🤖" if r.ai_generated else "",
            "score_ia": r.ai_score or 0,
            "created_at": r.created_at
        } for r in recettes])


def charger_ingredients_recette(recipe_id: int) -> List[Dict]:
    """Charge les ingrédients d'une recette"""
    with get_db_context() as db:
        ingredients = db.query(
            Ingredient.name,
            RecipeIngredient.quantity,
            RecipeIngredient.unit
        ).join(
            RecipeIngredient, Ingredient.id == RecipeIngredient.ingredient_id
        ).filter(
            RecipeIngredient.recipe_id == recipe_id
        ).all()

        return [
            {"nom": ing.name, "quantite": ing.quantity, "unite": ing.unit}
            for ing in ingredients
        ]


# ===================================
# MODULE PRINCIPAL
# ===================================

def app():
    """Application Recettes avec IA intégrée"""

    st.title("🍲 Recettes Intelligentes")
    st.caption("Gestion des recettes avec suggestions IA")

    # Récupérer l'agent IA
    agent: AgentIA = st.session_state.get("agent_ia")
    if not agent:
        st.error("Agent IA non initialisé")
        return

    # ===================================
    # TABS PRINCIPAUX
    # ===================================

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Mes Recettes",
        "✨ Suggestions IA",
        "➕ Ajouter",
        "📊 Statistiques"
    ])

    # ===================================
    # TAB 1 : LISTE DES RECETTES
    # ===================================

    with tab1:
        st.subheader("Toutes mes recettes")

        # Filtres
        col_search, col_cat, col_action = st.columns([2, 1, 1])

        with col_search:
            search = st.text_input("🔍 Rechercher", placeholder="Nom de recette...")

        with col_cat:
            categories = ["", "Entrée", "Plat", "Dessert", "Petit-déjeuner", "Snack"]
            categorie = st.selectbox("Catégorie", categories)

        with col_action:
            if st.button("🔄 Rafraîchir", use_container_width=True):
                st.rerun()

        # Charger les recettes
        df = charger_recettes(search, categorie)

        if df.empty:
            st.info("Aucune recette trouvée. Commence par en ajouter ou demande des suggestions à l'IA !")
        else:
            # Afficher le tableau
            st.dataframe(
                df[["nom", "categorie", "temps_prep", "temps_cuisson", "portions", "ia", "score_ia"]],
                use_container_width=True,
                column_config={
                    "nom": "Recette",
                    "categorie": "Catégorie",
                    "temps_prep": st.column_config.NumberColumn("Préparation (min)"),
                    "temps_cuisson": st.column_config.NumberColumn("Cuisson (min)"),
                    "portions": st.column_config.NumberColumn("Portions"),
                    "ia": st.column_config.TextColumn("IA"),
                    "score_ia": st.column_config.ProgressColumn(
                        "Score IA",
                        format="%.0f%%",
                        min_value=0,
                        max_value=100
                    )
                }
            )

            # Détails d'une recette
            st.markdown("### 🔍 Voir une recette")

            recette_selectionnee = st.selectbox(
                "Sélectionner une recette",
                df["nom"].tolist(),
                key="select_recette_detail"
            )

            if recette_selectionnee:
                recette_id = int(df[df["nom"] == recette_selectionnee].iloc[0]["id"])

                with get_db_context() as db:
                    recette = db.query(Recipe).filter(Recipe.id == recette_id).first()

                    if recette:
                        col_detail1, col_detail2 = st.columns([2, 1])

                        with col_detail1:
                            st.markdown(f"#### {recette.name}")
                            st.markdown(f"**Catégorie :** {recette.category}")
                            st.markdown(f"**⏱️ Préparation :** {recette.prep_time} min")
                            st.markdown(f"**🔥 Cuisson :** {recette.cook_time} min")
                            st.markdown(f"**👥 Portions :** {recette.servings}")

                            if recette.ai_generated:
                                st.info(f"🤖 Générée par IA (score: {recette.ai_score:.0f}%)")

                            st.markdown("**📝 Instructions :**")
                            st.text_area(
                                "Instructions",
                                recette.instructions,
                                height=200,
                                disabled=True,
                                label_visibility="collapsed"
                            )

                        with col_detail2:
                            st.markdown("**🥘 Ingrédients**")
                            ingredients = charger_ingredients_recette(recette_id)

                            for ing in ingredients:
                                st.write(f"• {ing['quantite']} {ing['unite']} {ing['nom']}")

                            st.markdown("---")

                            # Actions
                            if st.button("📅 Planifier", key=f"plan_{recette_id}"):
                                st.info("→ Va dans Batch Cooking pour planifier")

                            if st.button("✏️ Modifier", key=f"edit_{recette_id}"):
                                st.session_state["edit_recette_id"] = recette_id
                                st.rerun()

                            if st.button("🗑️ Supprimer", key=f"del_{recette_id}", type="secondary"):
                                with get_db_context() as db_del:
                                    db_del.query(Recipe).filter(Recipe.id == recette_id).delete()
                                    db_del.commit()
                                st.success("Recette supprimée")
                                st.rerun()

    # ===================================
    # TAB 2 : SUGGESTIONS IA
    # ===================================

    with tab2:
        st.subheader("✨ Suggestions intelligentes basées sur ton inventaire")

        # Vérifier si l'inventaire est vide
        inventaire = get_inventaire_disponible()

        if not inventaire:
            st.warning("⚠️ Ton inventaire est vide ! Ajoute des ingrédients d'abord.")
            if st.button("➕ Aller à l'inventaire"):
                st.session_state.current_module = "cuisine.inventaire"
                st.rerun()
        else:
            # Afficher l'inventaire disponible
            with st.expander("📦 Inventaire disponible", expanded=False):
                col1, col2, col3 = st.columns(3)
                for i, item in enumerate(inventaire):
                    col = [col1, col2, col3][i % 3]
                    col.write(f"• **{item['nom']}** : {item['quantite']} {item['unite']}")

            # Paramètres de suggestion
            col_nb, col_pref, col_gen = st.columns([1, 2, 1])

            with col_nb:
                nb_suggestions = st.slider("Nombre de suggestions", 1, 5, 3)

            with col_pref:
                preferences = st.multiselect(
                    "Préférences (optionnel)",
                    ["Végétarien", "Sans gluten", "Rapide (<30min)", "Économique", "Enfants"]
                )

            with col_gen:
                st.write("")  # Espace
                st.write("")
                generer = st.button(
                    "🤖 Générer suggestions",
                    type="primary",
                    use_container_width=True
                )

            # Générer les suggestions
            if generer:
                with st.spinner("🤖 L'IA analyse ton inventaire..."):
                    try:
                        # Appel asynchrone
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        suggestions = loop.run_until_complete(
                            agent.suggerer_recettes(
                                inventaire=inventaire,
                                preferences=preferences,
                                nb_suggestions=nb_suggestions
                            )
                        )

                        st.session_state["suggestions_recettes"] = suggestions
                        st.success(f"✅ {len(suggestions)} suggestions générées !")

                    except Exception as e:
                        st.error(f"Erreur IA : {e}")
                        suggestions = []

            # Afficher les suggestions
            if "suggestions_recettes" in st.session_state:
                suggestions = st.session_state["suggestions_recettes"]

                st.markdown("### 🎯 Recettes suggérées")

                for i, sugg in enumerate(suggestions):
                    with st.expander(
                            f"🍽️ {sugg.get('nom', 'Recette')} — Faisabilité: {sugg.get('faisabilite', 0)}%",
                            expanded=True
                    ):
                        col_sugg1, col_sugg2 = st.columns([2, 1])

                        with col_sugg1:
                            st.markdown(f"**Ingrédients:** {', '.join(sugg.get('ingredients', []))}")
                            st.info(f"💡 {sugg.get('raison', 'Suggestion IA')}")

                            if "temps_preparation" in sugg:
                                st.caption(f"⏱️ Temps de préparation : {sugg['temps_preparation']} min")

                        with col_sugg2:
                            # Barre de faisabilité
                            faisabilite = sugg.get('faisabilite', 0)
                            st.metric("Faisabilité", f"{faisabilite}%")

                            # Boutons d'action
                            if st.button(
                                    "💾 Sauvegarder cette recette",
                                    key=f"save_sugg_{i}",
                                    use_container_width=True
                            ):
                                # Préparer les ingrédients
                                ingredients = [
                                    {"nom": ing, "quantite": 1.0, "unite": "portion"}
                                    for ing in sugg.get('ingredients', [])
                                ]

                                # Sauvegarder
                                recipe_id = sauvegarder_recette(
                                    nom=sugg['nom'],
                                    categorie="Suggestion IA",
                                    instructions="Recette générée par IA. Instructions à compléter.",
                                    prep_time=sugg.get('temps_preparation', 30),
                                    cook_time=20,
                                    servings=4,
                                    ingredients=ingredients,
                                    ai_generated=True,
                                    ai_score=faisabilite
                                )

                                st.success(f"✅ Recette '{sugg['nom']}' sauvegardée !")
                                st.balloons()

                            if st.button(
                                    "📅 Planifier",
                                    key=f"plan_sugg_{i}",
                                    use_container_width=True
                            ):
                                st.info("→ Va dans Batch Cooking")

    # ===================================
    # TAB 3 : AJOUTER UNE RECETTE
    # ===================================

    with tab3:
        st.subheader("➕ Ajouter une nouvelle recette")

        with st.form("form_ajout_recette"):
            col_form1, col_form2 = st.columns([2, 1])

            with col_form1:
                nom = st.text_input("Nom de la recette *", placeholder="Ex: Gratin dauphinois")
                categorie_form = st.selectbox(
                    "Catégorie *",
                    ["Entrée", "Plat", "Dessert", "Petit-déjeuner", "Snack"]
                )
                instructions = st.text_area(
                    "Instructions *",
                    height=200,
                    placeholder="1. Étape 1\n2. Étape 2\n..."
                )

            with col_form2:
                prep_time = st.number_input("Temps de préparation (min)", min_value=0, value=30)
                cook_time = st.number_input("Temps de cuisson (min)", min_value=0, value=30)
                servings = st.number_input("Nombre de portions", min_value=1, value=4)

            # Ingrédients
            st.markdown("### 🥘 Ingrédients")

            ingredients_text = st.text_area(
                "Liste des ingrédients (un par ligne)",
                height=150,
                placeholder="Format: quantité unité nom\nEx:\n300 g pâtes\n200 ml crème\n100 g fromage",
                help="Format: quantité unité nom (séparés par espaces)"
            )

            submitted = st.form_submit_button("💾 Enregistrer la recette", type="primary")

            if submitted:
                if not nom or not instructions:
                    st.error("Le nom et les instructions sont obligatoires !")
                else:
                    # Parser les ingrédients
                    ingredients = []
                    for ligne in ingredients_text.split("\n"):
                        ligne = ligne.strip()
                        if ligne:
                            parties = ligne.split(maxsplit=2)
                            if len(parties) >= 3:
                                try:
                                    quantite = float(parties[0])
                                    unite = parties[1]
                                    nom_ing = parties[2]
                                    ingredients.append({
                                        "nom": nom_ing,
                                        "quantite": quantite,
                                        "unite": unite
                                    })
                                except ValueError:
                                    st.warning(f"Ligne ignorée (format invalide) : {ligne}")

                    if not ingredients:
                        st.error("Ajoute au moins un ingrédient !")
                    else:
                        # Sauvegarder
                        recipe_id = sauvegarder_recette(
                            nom=nom,
                            categorie=categorie_form,
                            instructions=instructions,
                            prep_time=prep_time,
                            cook_time=cook_time,
                            servings=servings,
                            ingredients=ingredients
                        )

                        st.success(f"✅ Recette '{nom}' enregistrée avec succès !")
                        st.balloons()
                        st.rerun()

    # ===================================
    # TAB 4 : STATISTIQUES
    # ===================================

    with tab4:
        st.subheader("📊 Statistiques de tes recettes")

        df_stats = charger_recettes()

        if df_stats.empty:
            st.info("Pas encore de statistiques. Ajoute des recettes d'abord !")
        else:
            # Métriques principales
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)

            with col_m1:
                st.metric("📚 Total recettes", len(df_stats))

            with col_m2:
                nb_ia = len(df_stats[df_stats["ia"] == "🤖"])
                st.metric("🤖 Générées par IA", nb_ia)

            with col_m3:
                avg_prep = df_stats["temps_prep"].mean()
                st.metric("⏱️ Temps moyen", f"{avg_prep:.0f} min")

            with col_m4:
                categories_count = df_stats["categorie"].nunique()
                st.metric("🏷️ Catégories", categories_count)

            # Graphiques
            st.markdown("### 📈 Répartition par catégorie")

            cat_counts = df_stats["categorie"].value_counts().reset_index()
            cat_counts.columns = ["Catégorie", "Nombre"]

            st.bar_chart(cat_counts.set_index("Catégorie"))

            # Temps de préparation
            st.markdown("### ⏱️ Distribution des temps de préparation")
            st.bar_chart(df_stats[["nom", "temps_prep"]].set_index("nom").head(10))

            # Recettes IA les mieux notées
            if nb_ia > 0:
                st.markdown("### 🌟 Top recettes IA")
                top_ia = df_stats[df_stats["ia"] == "🤖"].sort_values(
                    "score_ia", ascending=False
                ).head(5)

                st.dataframe(
                    top_ia[["nom", "score_ia", "categorie"]],
                    use_container_width=True
                )