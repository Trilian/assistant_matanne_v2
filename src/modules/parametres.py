"""
Module Paramètres
Configuration de l'application
"""

import streamlit as st
from src.core.config import settings
from src.core.database import get_db_info, check_connection


def app():
    """Module Paramètres"""

    st.title("⚙️ Paramètres")
    st.caption("Configuration de l'application")

    # ===================================
    # TABS
    # ===================================

    tab1, tab2, tab3, tab4 = st.tabs([
        "🔧 Général",
        "🤖 Intelligence Artificielle",
        "🗄️ Base de données",
        "ℹ️ À propos"
    ])

    # ===================================
    # TAB 1 : GÉNÉRAL
    # ===================================

    with tab1:
        st.subheader("Paramètres généraux")

        # Informations utilisateur
        st.markdown("### 👤 Profil")

        with st.form("form_profil"):
            nom = st.text_input("Nom", value="Anne")
            email = st.text_input("Email", value="anne@matanne.app")

            col_p1, col_p2 = st.columns(2)

            with col_p1:
                ville = st.text_input("Ville", value="Clermont-Ferrand")

            with col_p2:
                fuseau = st.selectbox("Fuseau horaire", ["Europe/Paris", "Europe/London", "US/Eastern"])

            if st.form_submit_button("💾 Enregistrer"):
                st.success("Profil mis à jour")

        st.markdown("---")

        # Préférences d'affichage
        st.markdown("### 🎨 Affichage")

        theme = st.selectbox(
            "Thème",
            ["Clair", "Sombre", "Auto"],
            help="Le thème de l'application"
        )

        langue = st.selectbox(
            "Langue",
            ["Français", "English"],
            help="Langue de l'interface"
        )

        format_date = st.selectbox(
            "Format de date",
            ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"]
        )

        st.markdown("---")

        # Notifications
        st.markdown("### 🔔 Notifications")

        notif_repas = st.checkbox("Rappels repas planifiés", value=True)
        notif_stock = st.checkbox("Alertes stock bas", value=True)
        notif_projets = st.checkbox("Échéances projets", value=True)
        notif_routines = st.checkbox("Rappels routines", value=True)

        if st.button("💾 Enregistrer les préférences"):
            st.success("Préférences sauvegardées")

    # ===================================
    # TAB 2 : IA
    # ===================================

    with tab2:
        st.subheader("Intelligence Artificielle")

        # Statut IA
        st.markdown("### 🤖 Statut de l'IA")

        if settings.ENABLE_AI:
            st.success("✅ Agent IA activé")

            col_ia1, col_ia2 = st.columns(2)

            with col_ia1:
                st.metric("Modèle", settings.OLLAMA_MODEL)

            with col_ia2:
                st.metric("URL Ollama", settings.OLLAMA_URL)

            # Test connexion
            if st.button("🔍 Tester la connexion Ollama"):
                with st.spinner("Test en cours..."):
                    try:
                        import httpx
                        import asyncio

                        async def test():
                            async with httpx.AsyncClient(timeout=5.0) as client:
                                response = await client.get(f"{settings.OLLAMA_URL}/api/tags")
                                return response.status_code == 200

                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        success = loop.run_until_complete(test())

                        if success:
                            st.success("✅ Ollama accessible")
                        else:
                            st.error("❌ Ollama non accessible")

                    except Exception as e:
                        st.error(f"❌ Erreur : {e}")
        else:
            st.warning("⚠️ Agent IA désactivé")
            st.info("Pour activer l'IA, configure ENABLE_AI=True dans .env")

        st.markdown("---")

        # Paramètres IA
        st.markdown("### ⚙️ Paramètres IA")

        temperature = st.slider(
            "Température",
            0.0, 2.0, 0.7, 0.1,
            help="Créativité de l'IA (0 = précis, 2 = créatif)"
        )

        max_tokens = st.number_input(
            "Tokens max par réponse",
            100, 2000, 500, 50,
            help="Longueur maximale des réponses"
        )

        cache_ttl = st.number_input(
            "Durée cache (secondes)",
            0, 3600, 300, 60,
            help="Durée de mise en cache des réponses IA"
        )

        if st.button("💾 Sauvegarder paramètres IA"):
            st.success("Paramètres IA sauvegardés")

        st.markdown("---")

        # Statistiques utilisation IA
        st.markdown("### 📊 Statistiques d'utilisation")

        with st.spinner("Chargement..."):
            from src.core.database import get_db_context
            from src.core.models import AIInteraction

            with get_db_context() as db:
                total = db.query(AIInteraction).count()
                reussis = db.query(AIInteraction).filter(AIInteraction.success == True).count()

                col_stat1, col_stat2, col_stat3 = st.columns(3)

                with col_stat1:
                    st.metric("Requêtes totales", total)

                with col_stat2:
                    st.metric("Réussies", reussis)

                with col_stat3:
                    taux = (reussis / total * 100) if total > 0 else 0
                    st.metric("Taux de succès", f"{taux:.0f}%")

    # ===================================
    # TAB 3 : BASE DE DONNÉES
    # ===================================

    with tab3:
        st.subheader("Base de données")

        # Statut connexion
        st.markdown("### 🗄️ Statut de la connexion")

        if check_connection():
            st.success("✅ Connecté à la base de données")

            db_info = get_db_info()

            if db_info["status"] == "connected":
                col_db1, col_db2 = st.columns(2)

                with col_db1:
                    st.metric("Base de données", db_info["database"])
                    st.metric("Utilisateur", db_info["user"])

                with col_db2:
                    st.caption("Version PostgreSQL")
                    st.caption(db_info["version"].split(",")[0])
        else:
            st.error("❌ Impossible de se connecter à la base de données")

        st.markdown("---")

        # Actions maintenance
        st.markdown("### 🔧 Maintenance")

        col_maint1, col_maint2 = st.columns(2)

        with col_maint1:
            if st.button("🧹 Nettoyer logs anciens (>90j)", use_container_width=True):
                with st.spinner("Nettoyage..."):
                    from src.core.database import cleanup_old_logs
                    deleted = cleanup_old_logs(90)
                    st.success(f"✅ {deleted} logs supprimés")

            if st.button("📊 Optimiser la base", use_container_width=True):
                with st.spinner("Optimisation..."):
                    from src.core.database import vacuum_database
                    vacuum_database()
                    st.success("✅ Base optimisée")

        with col_maint2:
            if st.button("💾 Sauvegarder", use_container_width=True):
                st.info("Fonctionnalité de sauvegarde à implémenter")

            if st.button("📤 Exporter données", use_container_width=True):
                st.info("Fonctionnalité d'export à implémenter")

        st.markdown("---")

        # Danger zone
        with st.expander("⚠️ Zone dangereuse", expanded=False):
            st.error("**ATTENTION** : Ces actions sont irréversibles")

            if st.button("🗑️ Réinitialiser TOUTE la base", type="secondary"):
                st.warning("Cette fonctionnalité nécessite une confirmation supplémentaire")

    # ===================================
    # TAB 4 : À PROPOS
    # ===================================

    with tab4:
        st.subheader("À propos")

        st.markdown(f"""
        ## 🤖 {settings.APP_NAME}
        
        **Version :** {settings.APP_VERSION}
        
        **Environnement :** {settings.ENV}
        
        ### 📝 Description
        
        Assistant familial intelligent propulsé par l'IA pour faciliter la gestion du quotidien.
        
        ### ✨ Fonctionnalités
        
        - 🍲 **Cuisine** : Recettes, inventaire, batch cooking, courses
        - 👶 **Famille** : Suivi Jules, bien-être, routines
        - 🏡 **Maison** : Projets, jardin, entretien
        - 📅 **Planning** : Calendrier, vue d'ensemble
        - 🤖 **IA** : Agent intelligent intégré partout
        
        ### 🛠️ Technologies
        
        - **Framework** : Streamlit
        - **Base de données** : PostgreSQL
        - **IA** : Ollama (llama2)
        - **Python** : 3.11+
        
        ### 📚 Documentation
        
        - [Guide d'utilisation](https://github.com/ton-repo)
        - [Documentation technique](https://github.com/ton-repo/docs)
        - [Signaler un bug](https://github.com/ton-repo/issues)
        
        ### 👨‍💻 Développé avec ❤️
        
        Par Anne, pour faciliter la vie de famille.
        
        ---
        
        💚 **Merci d'utiliser Assistant MaTanne !**
        """)

        st.markdown("---")

        # Informations système
        with st.expander("🔧 Informations système", expanded=False):
            import sys
            import platform

            st.write(f"**Python** : {sys.version}")
            st.write(f"**Plateforme** : {platform.system()} {platform.release()}")
            st.write(f"**Streamlit** : {st.__version__}")

            # Configuration active
            st.markdown("**Configuration active :**")
            config = settings.to_dict()
            for key, value in config.items():
                st.write(f"• {key}: {value}")