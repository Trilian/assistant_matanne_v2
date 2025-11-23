"""
Module Courses avec Agent IA intégré
Gestion et optimisation intelligente des listes de courses
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import asyncio
from typing import List, Dict

from src.core.database import get_db_context
from src.core.models import (
    ShoppingList, Ingredient, InventoryItem, Recipe,
    RecipeIngredient, BatchMeal
)
from src.core.ai_agent import AgentIA


# ===================================
# HELPERS
# ===================================

def charger_liste_courses() -> pd.DataFrame:
    """Charge la liste de courses"""
    with get_db_context() as db:
        items = db.query(
            ShoppingList.id,
            Ingredient.name,
            ShoppingList.needed_quantity,
            Ingredient.unit,
            ShoppingList.priority,
            ShoppingList.purchased,
            ShoppingList.ai_suggested,
            ShoppingList.store_section,
            ShoppingList.created_at
        ).join(
            Ingredient, ShoppingList.ingredient_id == Ingredient.id
        ).order_by(
            ShoppingList.purchased,
            ShoppingList.priority.desc()
        ).all()

        return pd.DataFrame([{
            "id": item.id,
            "nom": item.name,
            "quantite": item.needed_quantity,
            "unite": item.unit,
            "priorite": item.priority,
            "achete": item.purchased,
            "ia": "🤖" if item.ai_suggested else "",
            "rayon": item.store_section or "—",
            "date": item.created_at
        } for item in items])


def ajouter_a_courses(nom: str, quantite: float, unite: str, priorite: str = "moyenne"):
    """Ajoute un article à la liste de courses"""
    with get_db_context() as db:
        # Vérifier si l'ingrédient existe
        ingredient = db.query(Ingredient).filter(Ingredient.name == nom).first()

        if not ingredient:
            ingredient = Ingredient(name=nom, unit=unite)
            db.add(ingredient)
            db.flush()

        # Vérifier si déjà dans la liste
        existing = db.query(ShoppingList).filter(
            ShoppingList.ingredient_id == ingredient.id,
            ShoppingList.purchased == False
        ).first()

        if existing:
            existing.needed_quantity += quantite
        else:
            item = ShoppingList(
                ingredient_id=ingredient.id,
                needed_quantity=quantite,
                priority=priorite,
                ai_suggested=False
            )
            db.add(item)

        db.commit()


def marquer_achete(item_id: int):
    """Marque un article comme acheté"""
    with get_db_context() as db:
        item = db.query(ShoppingList).filter(ShoppingList.id == item_id).first()
        if item:
            item.purchased = True
            item.purchased_at = datetime.now()

            # Ajouter à l'inventaire si pas déjà présent
            inventory = db.query(InventoryItem).filter(
                InventoryItem.ingredient_id == item.ingredient_id
            ).first()

            if inventory:
                inventory.quantity += item.needed_quantity
            else:
                inventory = InventoryItem(
                    ingredient_id=item.ingredient_id,
                    quantity=item.needed_quantity,
                    min_quantity=1.0
                )
                db.add(inventory)

            db.commit()


def supprimer_item(item_id: int):
    """Supprime un article de la liste"""
    with get_db_context() as db:
        db.query(ShoppingList).filter(ShoppingList.id == item_id).delete()
        db.commit()


def nettoyer_achetes():
    """Supprime tous les articles achetés"""
    with get_db_context() as db:
        db.query(ShoppingList).filter(ShoppingList.purchased == True).delete()
        db.commit()


def generer_depuis_stock_bas() -> int:
    """Génère automatiquement depuis le stock bas"""
    with get_db_context() as db:
        items_bas = db.query(
            Ingredient.id,
            Ingredient.name,
            InventoryItem.min_quantity,
            InventoryItem.quantity,
            Ingredient.unit
        ).join(
            InventoryItem, Ingredient.id == InventoryItem.ingredient_id
        ).filter(
            InventoryItem.quantity < InventoryItem.min_quantity
        ).all()

        count = 0
        for ing_id, nom, seuil, qty_actuelle, unite in items_bas:
            # Vérifier si pas déjà dans la liste
            existing = db.query(ShoppingList).filter(
                ShoppingList.ingredient_id == ing_id,
                ShoppingList.purchased == False
            ).first()

            if not existing:
                manque = max(seuil - qty_actuelle, seuil)
                item = ShoppingList(
                    ingredient_id=ing_id,
                    needed_quantity=manque,
                    priority="haute",
                    ai_suggested=True
                )
                db.add(item)
                count += 1

        db.commit()
        return count


def generer_depuis_recettes() -> int:
    """Génère depuis les recettes planifiées"""
    with get_db_context() as db:
        # Récupérer les repas planifiés à venir
        today = date.today()
        repas = db.query(
            Recipe.id,
            Recipe.name
        ).join(
            BatchMeal, Recipe.id == BatchMeal.recipe_id
        ).filter(
            BatchMeal.scheduled_date >= today,
            BatchMeal.status == "à faire"
        ).all()

        count = 0
        for recipe_id, recipe_name in repas:
            # Récupérer les ingrédients nécessaires
            ingredients = db.query(
                RecipeIngredient.ingredient_id,
                RecipeIngredient.quantity,
                Ingredient.unit
            ).join(
                Ingredient, RecipeIngredient.ingredient_id == Ingredient.id
            ).filter(
                RecipeIngredient.recipe_id == recipe_id
            ).all()

            for ing_id, qty_needed, unit in ingredients:
                # Vérifier le stock
                inventory = db.query(InventoryItem).filter(
                    InventoryItem.ingredient_id == ing_id
                ).first()

                qty_dispo = inventory.quantity if inventory else 0

                if qty_dispo < qty_needed:
                    manque = qty_needed - qty_dispo

                    # Ajouter ou mettre à jour la liste
                    existing = db.query(ShoppingList).filter(
                        ShoppingList.ingredient_id == ing_id,
                        ShoppingList.purchased == False
                    ).first()

                    if existing:
                        existing.needed_quantity = max(existing.needed_quantity, manque)
                    else:
                        item = ShoppingList(
                            ingredient_id=ing_id,
                            needed_quantity=manque,
                            priority="moyenne",
                            ai_suggested=True
                        )
                        db.add(item)
                        count += 1

        db.commit()
        return count


# ===================================
# MODULE PRINCIPAL
# ===================================

def app():
    """Module Courses avec IA intégrée"""

    st.title("🛒 Liste de Courses Intelligente")
    st.caption("Optimisation et génération automatique par IA")

    # Récupérer l'agent IA
    agent: AgentIA = st.session_state.get("agent_ia")

    # ===================================
    # TABS PRINCIPAUX
    # ===================================

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Ma Liste",
        "🤖 Génération Auto",
        "➕ Ajouter",
        "📊 Historique"
    ])

    # ===================================
    # TAB 1 : LISTE DE COURSES
    # ===================================

    with tab1:
        st.subheader("Ma liste de courses")

        # Actions rapides
        col_a1, col_a2, col_a3, col_a4 = st.columns(4)

        with col_a1:
            if st.button("🔄 Rafraîchir", use_container_width=True):
                st.rerun()

        with col_a2:
            if st.button("🗑️ Nettoyer achetés", use_container_width=True):
                nettoyer_achetes()
                st.success("Liste nettoyée")
                st.rerun()

        with col_a3:
            if st.button("⬇️ Stock bas", use_container_width=True):
                count = generer_depuis_stock_bas()
                st.success(f"{count} article(s) ajouté(s)")
                st.rerun()

        with col_a4:
            if st.button("📅 Depuis repas", use_container_width=True):
                count = generer_depuis_recettes()
                st.success(f"{count} article(s) ajouté(s)")
                st.rerun()

        # Charger la liste
        df = charger_liste_courses()

        if df.empty:
            st.info("📝 Liste vide. Ajoute des articles ou génère automatiquement !")
        else:
            # Séparer achetés et non achetés
            df_actif = df[df["achete"] == False]
            df_achete = df[df["achete"] == True]

            # Statistiques
            col_s1, col_s2, col_s3 = st.columns(3)

            with col_s1:
                st.metric("Articles à acheter", len(df_actif))

            with col_s2:
                prioritaire = len(df_actif[df_actif["priorite"] == "haute"])
                st.metric("Prioritaires", prioritaire, delta_color="inverse")

            with col_s3:
                ia_count = len(df_actif[df_actif["ia"] == "🤖"])
                st.metric("Suggérés IA", ia_count)

            st.markdown("---")

            # Liste active
            if not df_actif.empty:
                st.markdown("### 🛍️ À acheter")

                for _, row in df_actif.iterrows():
                    col_item1, col_item2, col_item3 = st.columns([3, 1, 1])

                    with col_item1:
                        priority_color = {
                            "haute": "🔴",
                            "moyenne": "🟡",
                            "basse": "🟢"
                        }.get(row["priorite"], "⚪")

                        st.markdown(f"{priority_color} {row['ia']} **{row['nom']}** — {row['quantite']} {row['unite']}")
                        if row["rayon"] != "—":
                            st.caption(f"📍 {row['rayon']}")

                    with col_item2:
                        if st.button("✅ Acheté", key=f"buy_{row['id']}", use_container_width=True):
                            marquer_achete(row['id'])
                            st.success(f"{row['nom']} acheté")
                            st.rerun()

                    with col_item3:
                        if st.button("🗑️", key=f"del_{row['id']}", use_container_width=True):
                            supprimer_item(row['id'])
                            st.rerun()

                    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

            # Liste achetés (collapsé)
            if not df_achete.empty:
                with st.expander(f"✅ Achetés ({len(df_achete)})", expanded=False):
                    for _, row in df_achete.iterrows():
                        st.write(f"• {row['nom']} — {row['quantite']} {row['unite']}")

    # ===================================
    # TAB 2 : GÉNÉRATION AUTOMATIQUE IA
    # ===================================

    with tab2:
        st.subheader("🤖 Génération intelligente")

        if not agent:
            st.error("Agent IA non disponible")
        else:
            st.info("💡 L'IA analyse ton inventaire et tes repas planifiés pour optimiser ta liste")

            # Options
            col_g1, col_g2 = st.columns(2)

            with col_g1:
                inclure_stock = st.checkbox("📦 Inclure stock bas", value=True)
                inclure_repas = st.checkbox("📅 Inclure repas planifiés", value=True)
                optimiser_rayon = st.checkbox("🏪 Organiser par rayon", value=True)

            with col_g2:
                magasin = st.selectbox(
                    "Magasin",
                    ["Auchan", "Carrefour", "Leclerc", "Intermarché", "Autre"]
                )

                budget_max = st.number_input(
                    "Budget max (€)",
                    min_value=0,
                    max_value=500,
                    value=100,
                    step=10
                )

            generer = st.button(
                "✨ Générer avec l'IA",
                type="primary",
                use_container_width=True
            )

            if generer:
                with st.spinner("🤖 L'IA optimise ta liste..."):
                    try:
                        # Récupérer données
                        with get_db_context() as db:
                            # Inventaire
                            inv_items = db.query(
                                Ingredient.name,
                                InventoryItem.quantity,
                                Ingredient.unit
                            ).join(
                                InventoryItem, Ingredient.id == InventoryItem.ingredient_id
                            ).all()

                            inventaire = [
                                {"nom": i.name, "quantite": i.quantity, "unite": i.unit}
                                for i in inv_items
                            ]

                            # Recettes planifiées
                            recettes = db.query(Recipe.name).join(
                                BatchMeal, Recipe.id == BatchMeal.recipe_id
                            ).filter(
                                BatchMeal.scheduled_date >= date.today(),
                                BatchMeal.status == "à faire"
                            ).limit(7).all()

                            recettes_noms = [r.name for r in recettes]

                        # Appel IA
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                        result = loop.run_until_complete(
                            agent.optimiser_courses(inventaire, recettes_noms)
                        )

                        st.session_state["courses_optimisees"] = result
                        st.success("✅ Liste optimisée générée !")

                    except Exception as e:
                        st.error(f"Erreur IA : {e}")

            # Afficher le résultat
            if "courses_optimisees" in st.session_state:
                result = st.session_state["courses_optimisees"]

                st.markdown("---")
                st.markdown("### 📋 Liste optimisée")

                if "par_rayon" in result:
                    for rayon, items in result["par_rayon"].items():
                        with st.expander(f"🏪 {rayon}", expanded=True):
                            for item in items:
                                col_opt1, col_opt2 = st.columns([3, 1])

                                with col_opt1:
                                    st.write(f"• {item}")

                                with col_opt2:
                                    if st.button("➕", key=f"add_{rayon}_{item}", use_container_width=True):
                                        ajouter_a_courses(item, 1.0, "pcs", "moyenne")
                                        st.success(f"{item} ajouté")

                if "budget_estime" in result:
                    st.metric("Budget estimé", f"{result['budget_estime']}€")

                # Bouton validation
                if st.button("✅ Ajouter tout à ma liste", type="primary"):
                    count = 0
                    if "par_rayon" in result:
                        for items in result["par_rayon"].values():
                            for item in items:
                                ajouter_a_courses(item, 1.0, "pcs", "moyenne")
                                count += 1

                    st.success(f"✅ {count} articles ajoutés !")
                    del st.session_state["courses_optimisees"]
                    st.rerun()

    # ===================================
    # TAB 3 : AJOUTER MANUELLEMENT
    # ===================================

    with tab3:
        st.subheader("➕ Ajouter un article")

        with st.form("form_add_course"):
            nom = st.text_input("Nom de l'article *", placeholder="Ex: Lait")

            col_f1, col_f2 = st.columns(2)

            with col_f1:
                quantite = st.number_input("Quantité *", min_value=0.1, value=1.0, step=0.1)
                unite = st.selectbox("Unité", ["pcs", "kg", "g", "L", "mL", "sachets", "boîtes"])

            with col_f2:
                priorite = st.selectbox("Priorité", ["basse", "moyenne", "haute"])
                rayon = st.text_input("Rayon (optionnel)", placeholder="Ex: Frais")

            submitted = st.form_submit_button("➕ Ajouter", type="primary")

            if submitted:
                if not nom:
                    st.error("Le nom est obligatoire")
                else:
                    ajouter_a_courses(nom, quantite, unite, priorite)
                    st.success(f"✅ {nom} ajouté à la liste")
                    st.balloons()
                    st.rerun()

        st.markdown("---")

        # Ajout rapide depuis l'inventaire
        st.markdown("### ⚡ Ajout rapide depuis l'inventaire")

        with get_db_context() as db:
            stock_bas = db.query(
                Ingredient.name,
                InventoryItem.quantity,
                InventoryItem.min_quantity,
                Ingredient.unit
            ).join(
                InventoryItem, Ingredient.id == InventoryItem.ingredient_id
            ).filter(
                InventoryItem.quantity < InventoryItem.min_quantity
            ).limit(5).all()

            if stock_bas:
                st.info(f"⚠️ {len(stock_bas)} article(s) en stock bas")

                for ing_name, qty, seuil, unit in stock_bas:
                    col_sb1, col_sb2 = st.columns([3, 1])

                    with col_sb1:
                        st.write(f"• **{ing_name}** : {qty} / {seuil} {unit}")

                    with col_sb2:
                        if st.button("➕", key=f"quick_{ing_name}", use_container_width=True):
                            manque = max(seuil - qty, 1.0)
                            ajouter_a_courses(ing_name, manque, unit, "haute")
                            st.success(f"{ing_name} ajouté")
                            st.rerun()
            else:
                st.success("✅ Pas de stock bas")

    # ===================================
    # TAB 4 : HISTORIQUE
    # ===================================

    with tab4:
        st.subheader("📊 Historique des courses")

        df_all = charger_liste_courses()
        df_achete = df_all[df_all["achete"] == True]

        if df_achete.empty:
            st.info("Pas encore d'historique")
        else:
            # Métriques
            col_h1, col_h2, col_h3 = st.columns(3)

            with col_h1:
                st.metric("Total acheté", len(df_achete))

            with col_h2:
                ia_achete = len(df_achete[df_achete["ia"] == "🤖"])
                st.metric("Suggérés IA achetés", ia_achete)

            with col_h3:
                # Articles les plus achetés
                top_item = df_achete["nom"].mode()
                if not top_item.empty:
                    st.metric("Plus acheté", top_item.iloc[0])

            # Tableau
            st.markdown("### 📋 Historique récent")

            st.dataframe(
                df_achete[["nom", "quantite", "unite", "ia", "date"]].sort_values("date", ascending=False).head(20),
                use_container_width=True
            )

            # Export
            st.markdown("---")
            if st.button("📤 Exporter l'historique (CSV)"):
                csv = df_achete.to_csv(index=False)
                st.download_button(
                    "Télécharger",
                    csv,
                    "historique_courses.csv",
                    "text/csv"
                )