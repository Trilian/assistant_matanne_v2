"""
Module Inventaire avec Agent IA intégré
Gestion du stock avec détection automatique et alertes intelligentes
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import asyncio
from typing import List, Dict

from src.core.database import get_db_context
from src.core.models import Ingredient, InventoryItem, ShoppingList
from src.core.ai_agent import AgentIA


# ===================================
# HELPERS
# ===================================

def charger_inventaire(search: str = "", low_stock_only: bool = False) -> pd.DataFrame:
    """Charge l'inventaire avec filtres"""
    with get_db_context() as db:
        query = db.query(
            InventoryItem.id,
            Ingredient.name,
            Ingredient.category,
            InventoryItem.quantity,
            Ingredient.unit,
            InventoryItem.min_quantity,
            InventoryItem.location,
            InventoryItem.expiry_date,
            InventoryItem.last_updated
        ).join(
            Ingredient, InventoryItem.ingredient_id == Ingredient.id
        )

        if search:
            query = query.filter(Ingredient.name.ilike(f"%{search}%"))

        if low_stock_only:
            query = query.filter(InventoryItem.quantity < InventoryItem.min_quantity)

        items = query.order_by(Ingredient.name).all()

        return pd.DataFrame([{
            "id": item.id,
            "nom": item.name,
            "categorie": item.category or "—",
            "quantite": item.quantity,
            "unite": item.unit,
            "seuil": item.min_quantity,
            "emplacement": item.location or "—",
            "peremption": item.expiry_date.strftime("%d/%m/%Y") if item.expiry_date else "—",
            "alerte": "⚠️" if item.quantity < item.min_quantity else "✅",
            "updated": item.last_updated
        } for item in items])


def ajouter_ou_modifier_item(
        nom: str,
        categorie: str,
        quantite: float,
        unite: str,
        seuil: float,
        emplacement: str = None,
        peremption: date = None
) -> int:
    """Ajoute ou met à jour un item d'inventaire"""
    with get_db_context() as db:
        # Vérifier si l'ingrédient existe
        ingredient = db.query(Ingredient).filter(
            Ingredient.name == nom
        ).first()

        if not ingredient:
            ingredient = Ingredient(
                name=nom,
                unit=unite,
                category=categorie
            )
            db.add(ingredient)
            db.flush()

        # Vérifier si l'item existe dans l'inventaire
        item = db.query(InventoryItem).filter(
            InventoryItem.ingredient_id == ingredient.id
        ).first()

        if item:
            # Mise à jour
            item.quantity = quantite
            item.min_quantity = seuil
            item.location = emplacement
            item.expiry_date = peremption
            item.last_updated = datetime.now()
        else:
            # Création
            item = InventoryItem(
                ingredient_id=ingredient.id,
                quantity=quantite,
                min_quantity=seuil,
                location=emplacement,
                expiry_date=peremption
            )
            db.add(item)

        db.commit()
        return item.id


def supprimer_item(item_id: int):
    """Supprime un item de l'inventaire"""
    with get_db_context() as db:
        db.query(InventoryItem).filter(InventoryItem.id == item_id).delete()
        db.commit()


def ajuster_quantite(item_id: int, delta: float):
    """Ajuste la quantité d'un item"""
    with get_db_context() as db:
        item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if item:
            item.quantity = max(0, item.quantity + delta)
            item.last_updated = datetime.now()
            db.commit()


# ===================================
# MODULE PRINCIPAL
# ===================================

def app():
    """Module Inventaire avec IA intégrée"""

    st.title("📦 Inventaire Intelligent")
    st.caption("Gestion du stock avec détection automatique et alertes IA")

    # Récupérer l'agent IA
    agent: AgentIA = st.session_state.get("agent_ia")

    # ===================================
    # TABS PRINCIPAUX
    # ===================================

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Mon Stock",
        "🤖 Analyse IA",
        "➕ Ajouter/Modifier",
        "📊 Statistiques"
    ])

    # ===================================
    # TAB 1 : LISTE INVENTAIRE
    # ===================================

    with tab1:
        st.subheader("Stock actuel")

        # Filtres
        col_f1, col_f2, col_f3 = st.columns([2, 1, 1])

        with col_f1:
            search = st.text_input("🔍 Rechercher", placeholder="Nom d'ingrédient...")

        with col_f2:
            low_stock_only = st.checkbox("⚠️ Stock bas uniquement")

        with col_f3:
            if st.button("🔄 Rafraîchir", use_container_width=True):
                st.rerun()

        # Charger et afficher
        df = charger_inventaire(search, low_stock_only)

        if df.empty:
            st.info("Aucun article dans l'inventaire. Commence par en ajouter !")
        else:
            # Alertes globales
            stock_bas = len(df[df["alerte"] == "⚠️"])
            if stock_bas > 0:
                st.warning(f"⚠️ {stock_bas} article(s) en stock bas !")

            # Items proche péremption
            if "peremption" in df.columns:
                today = date.today()
                proche_peremption = []

                for _, row in df.iterrows():
                    if row["peremption"] != "—":
                        try:
                            exp_date = datetime.strptime(row["peremption"], "%d/%m/%Y").date()
                            if exp_date <= today + timedelta(days=7):
                                proche_peremption.append(row["nom"])
                        except:
                            pass

                if proche_peremption:
                    st.error(f"🗓️ Péremption proche : {', '.join(proche_peremption)}")

            # Tableau
            st.dataframe(
                df[["alerte", "nom", "categorie", "quantite", "unite", "seuil", "emplacement", "peremption"]],
                use_container_width=True,
                column_config={
                    "alerte": st.column_config.TextColumn("État", width="small"),
                    "nom": "Article",
                    "categorie": "Catégorie",
                    "quantite": st.column_config.NumberColumn("Quantité", format="%.1f"),
                    "unite": "Unité",
                    "seuil": st.column_config.NumberColumn("Seuil", format="%.1f"),
                    "emplacement": "Emplacement",
                    "peremption": "Péremption"
                }
            )

            # Actions rapides sur un article
            st.markdown("### ⚡ Actions rapides")

            article_select = st.selectbox(
                "Sélectionner un article",
                df["nom"].tolist(),
                key="select_article_action"
            )

            if article_select:
                item_id = int(df[df["nom"] == article_select].iloc[0]["id"])

                col_a1, col_a2, col_a3, col_a4 = st.columns(4)

                with col_a1:
                    if st.button("➕ Ajouter 1", use_container_width=True):
                        ajuster_quantite(item_id, 1)
                        st.success(f"+1 {article_select}")
                        st.rerun()

                with col_a2:
                    if st.button("➖ Retirer 1", use_container_width=True):
                        ajuster_quantite(item_id, -1)
                        st.success(f"-1 {article_select}")
                        st.rerun()

                with col_a3:
                    if st.button("🛒 → Courses", use_container_width=True):
                        # Ajouter à la liste de courses
                        with get_db_context() as db:
                            ingredient_id = db.query(InventoryItem).filter(
                                InventoryItem.id == item_id
                            ).first().ingredient_id

                            shopping = ShoppingList(
                                ingredient_id=ingredient_id,
                                needed_quantity=1,
                                ai_suggested=False
                            )
                            db.add(shopping)
                            db.commit()

                        st.success(f"{article_select} ajouté aux courses")

                with col_a4:
                    if st.button("🗑️ Supprimer", use_container_width=True, type="secondary"):
                        supprimer_item(item_id)
                        st.success(f"{article_select} supprimé")
                        st.rerun()

    # ===================================
    # TAB 2 : ANALYSE IA
    # ===================================

    with tab2:
        st.subheader("🤖 Analyse intelligente de ton stock")

        if not agent:
            st.error("Agent IA non disponible")
        else:
            # Récupérer l'inventaire pour l'IA
            with get_db_context() as db:
                items = db.query(
                    Ingredient.name,
                    InventoryItem.quantity,
                    Ingredient.unit
                ).join(
                    InventoryItem, Ingredient.id == InventoryItem.ingredient_id
                ).all()

                inventaire = [
                    {"nom": item.name, "quantite": item.quantity, "unite": item.unit}
                    for item in items
                ]

            if not inventaire:
                st.warning("Inventaire vide. Ajoute des articles d'abord.")
            else:
                col_ia1, col_ia2 = st.columns([2, 1])

                with col_ia1:
                    st.markdown("**Analyses disponibles**")

                    analyse_type = st.radio(
                        "Que veux-tu analyser ?",
                        [
                            "🗑️ Détection de gaspillage",
                            "🛒 Optimisation des courses",
                            "📊 État général du stock"
                        ]
                    )

                with col_ia2:
                    st.write("")
                    st.write("")
                    analyser = st.button(
                        "🚀 Analyser",
                        type="primary",
                        use_container_width=True
                    )

                if analyser:
                    with st.spinner("🤖 Analyse en cours..."):
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)

                            if "gaspillage" in analyse_type:
                                result = loop.run_until_complete(
                                    agent.detecter_gaspillage(inventaire)
                                )

                                st.markdown("### 🗑️ Analyse anti-gaspillage")

                                if result["statut"] == "OK":
                                    st.success(result["message"])
                                else:
                                    st.warning(f"**Statut :** {result['statut']}")

                                    if "items_risque" in result:
                                        st.markdown("**Articles à utiliser rapidement :**")
                                        for item in result["items_risque"]:
                                            st.write(f"• {item}")

                                    if "recettes_urgentes" in result:
                                        st.markdown("**Recettes suggérées :**")
                                        for recette in result["recettes_urgentes"]:
                                            st.info(recette)

                                    if "conseil" in result:
                                        st.markdown(f"**💡 Conseil :** {result['conseil']}")

                            elif "courses" in analyse_type:
                                # Récupérer recettes planifiées
                                with get_db_context() as db:
                                    from src.core.models import Recipe, BatchMeal

                                    recettes = db.query(Recipe.name).join(
                                        BatchMeal, Recipe.id == BatchMeal.recipe_id
                                    ).filter(
                                        BatchMeal.scheduled_date >= date.today()
                                    ).limit(5).all()

                                    recettes_noms = [r.name for r in recettes]

                                result = loop.run_until_complete(
                                    agent.optimiser_courses(inventaire, recettes_noms)
                                )

                                st.markdown("### 🛒 Optimisation courses")

                                if "par_rayon" in result:
                                    st.markdown("**Liste organisée par rayon :**")
                                    for rayon, items in result["par_rayon"].items():
                                        with st.expander(f"🏪 {rayon}"):
                                            for item in items:
                                                st.write(f"• {item}")

                                if "budget_estime" in result:
                                    st.metric("Budget estimé", f"{result['budget_estime']}€")

                            else:  # État général
                                st.markdown("### 📊 État général du stock")

                                col_st1, col_st2, col_st3 = st.columns(3)

                                total = len(inventaire)
                                bas = len([i for i in inventaire if i["quantite"] < 2])
                                ok = total - bas

                                with col_st1:
                                    st.metric("Total articles", total)

                                with col_st2:
                                    st.metric("Stock OK", ok, delta_color="normal")

                                with col_st3:
                                    st.metric("Stock bas", bas, delta_color="inverse")

                                # Suggestions
                                st.info("💡 **Conseil IA :** Réapprovisionne les articles en stock bas et utilise rapidement ceux proche de la péremption.")

                        except Exception as e:
                            st.error(f"Erreur IA : {e}")

    # ===================================
    # TAB 3 : AJOUTER/MODIFIER
    # ===================================

    with tab3:
        st.subheader("➕ Ajouter ou modifier un article")

        mode = st.radio("Mode", ["➕ Ajouter nouveau", "✏️ Modifier existant"])

        if mode.startswith("✏️"):
            # Mode modification
            df_all = charger_inventaire()

            if df_all.empty:
                st.info("Aucun article à modifier")
            else:
                article_edit = st.selectbox(
                    "Article à modifier",
                    df_all["nom"].tolist()
                )

                item_data = df_all[df_all["nom"] == article_edit].iloc[0]

                with st.form("form_edit"):
                    nom = st.text_input("Nom", value=item_data["nom"])

                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        categorie = st.text_input("Catégorie", value=item_data["categorie"])
                        quantite = st.number_input(
                            "Quantité",
                            min_value=0.0,
                            value=float(item_data["quantite"]),
                            step=0.1
                        )
                        emplacement = st.text_input("Emplacement", value=item_data["emplacement"])

                    with col_e2:
                        unite = st.text_input("Unité", value=item_data["unite"])
                        seuil = st.number_input(
                            "Seuil d'alerte",
                            min_value=0.0,
                            value=float(item_data["seuil"]),
                            step=0.1
                        )

                        try:
                            peremption_date = datetime.strptime(item_data["peremption"], "%d/%m/%Y").date() \
                                if item_data["peremption"] != "—" else None
                        except:
                            peremption_date = None

                        peremption = st.date_input(
                            "Date de péremption (optionnel)",
                            value=peremption_date
                        )

                    submitted = st.form_submit_button("💾 Enregistrer", type="primary")

                    if submitted:
                        ajouter_ou_modifier_item(
                            nom, categorie, quantite, unite, seuil,
                            emplacement, peremption
                        )
                        st.success(f"✅ {nom} mis à jour")
                        st.rerun()

        else:
            # Mode ajout
            with st.form("form_add"):
                nom = st.text_input("Nom de l'article *", placeholder="Ex: Tomates")

                col_a1, col_a2 = st.columns(2)

                with col_a1:
                    categorie = st.selectbox(
                        "Catégorie",
                        ["Légumes", "Fruits", "Féculents", "Protéines", "Laitier", "Épices", "Autre"]
                    )
                    quantite = st.number_input("Quantité *", min_value=0.0, value=1.0, step=0.1)
                    emplacement = st.selectbox(
                        "Emplacement",
                        ["Frigo", "Congélateur", "Placard", "Cave", "Autre"]
                    )

                with col_a2:
                    unite = st.selectbox(
                        "Unité *",
                        ["pcs", "kg", "g", "L", "mL", "sachets", "boîtes"]
                    )
                    seuil = st.number_input(
                        "Seuil d'alerte",
                        min_value=0.0,
                        value=1.0,
                        step=0.1,
                        help="Quantité minimum avant alerte"
                    )
                    peremption = st.date_input(
                        "Date de péremption (optionnel)",
                        value=None
                    )

                submitted = st.form_submit_button("➕ Ajouter à l'inventaire", type="primary")

                if submitted:
                    if not nom:
                        st.error("Le nom est obligatoire")
                    else:
                        ajouter_ou_modifier_item(
                            nom, categorie, quantite, unite, seuil,
                            emplacement, peremption
                        )
                        st.success(f"✅ {nom} ajouté à l'inventaire")
                        st.balloons()
                        st.rerun()

    # ===================================
    # TAB 4 : STATISTIQUES
    # ===================================

    with tab4:
        st.subheader("📊 Statistiques de l'inventaire")

        df_stats = charger_inventaire()

        if df_stats.empty:
            st.info("Pas de statistiques sans articles")
        else:
            # Métriques
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)

            with col_m1:
                st.metric("Total articles", len(df_stats))

            with col_m2:
                categories = df_stats["categorie"].nunique()
                st.metric("Catégories", categories)

            with col_m3:
                stock_bas = len(df_stats[df_stats["alerte"] == "⚠️"])
                st.metric("Stock bas", stock_bas, delta_color="inverse")

            with col_m4:
                emplacements = df_stats["emplacement"].nunique()
                st.metric("Emplacements", emplacements)

            # Graphiques
            st.markdown("### 📈 Répartition par catégorie")

            cat_counts = df_stats["categorie"].value_counts().reset_index()
            cat_counts.columns = ["Catégorie", "Nombre"]

            st.bar_chart(cat_counts.set_index("Catégorie"))

            # Top articles
            st.markdown("### 🔝 Articles les plus stockés")

            top10 = df_stats.nlargest(10, "quantite")[["nom", "quantite", "unite"]]
            st.dataframe(top10, use_container_width=True)

            # Export
            st.markdown("---")
            if st.button("📤 Exporter l'inventaire (CSV)"):
                csv = df_stats.to_csv(index=False)
                st.download_button(
                    "Télécharger",
                    csv,
                    "inventaire.csv",
                    "text/csv"
                )