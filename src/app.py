"""
Application principale Streamlit
Assistant MaTanne v2 avec Agent IA intégré
"""

import streamlit as st
import sys
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import settings
from src.core.database import check_connection, get_db_info, create_all_tables
from src.core.ai_agent import AgentIA
import logging

logger = logging.getLogger(__name__)


# ===================================
# CONFIGURATION STREAMLIT
# ===================================

st.set_page_config(
    page_title=settings.APP_NAME,
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/ton-repo',
        'Report a bug': 'https://github.com/ton-repo/issues',
        'About': f"{settings.APP_NAME} v{settings.APP_VERSION}"
    }
)


# ===================================
# STYLE CSS PERSONNALISÉ
# ===================================

def load_custom_css():
    """Charge le CSS personnalisé pour une interface moderne"""
    st.markdown("""
        <style>
        /* Variables */
        :root {
            --primary-color: #2d4d36;
            --secondary-color: #5e7a6a;
            --accent-color: #4caf50;
            --background: #f6f8f7;
            --card-bg: #ffffff;
        }
        
        /* Header personnalisé */
        .main-header {
            padding: 1rem 0;
            border-bottom: 2px solid var(--accent-color);
            margin-bottom: 2rem;
        }
        
        .main-header h1 {
            color: var(--primary-color);
            font-weight: 700;
            margin: 0;
        }
        
        /* Cards modernes */
        .metric-card {
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #e2e8e5;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
            transition: transform 0.2s;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.08);
        }
        
        /* Boutons AI */
        .ai-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            border: none;
            cursor: pointer;
            font-weight: 600;
        }
        
        /* Status badges */
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.875rem;
            font-weight: 600;
        }
        
        .status-success {
            background: #d4edda;
            color: #155724;
        }
        
        .status-warning {
            background: #fff3cd;
            color: #856404;
        }
        
        .status-error {
            background: #f8d7da;
            color: #721c24;
        }
        
        /* Animation de chargement IA */
        .ai-thinking {
            display: inline-block;
            animation: pulse 1.5s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        /* Sidebar */
        .css-1d391kg {
            background-color: var(--background);
        }
        
        /* Cache le menu hamburger en production */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)


load_custom_css()


# ===================================
# INITIALISATION
# ===================================

def init_app():
    """Initialise l'application au démarrage"""

    # Vérifier la connexion DB
    if not check_connection():
        st.error("❌ Impossible de se connecter à la base de données")
        st.stop()

    # Créer les tables si nécessaire (dev uniquement)
    if settings.is_development:
        try:
            create_all_tables()
        except Exception as e:
            logger.error(f"Erreur création tables: {e}")

    # Initialiser l'agent IA dans la session
    if "agent_ia" not in st.session_state:
        st.session_state.agent_ia = AgentIA()
        logger.info("🤖 Agent IA initialisé")

    # Initialiser l'état de navigation
    if "current_module" not in st.session_state:
        st.session_state.current_module = "Accueil"

    # Historique de chat
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


# Initialiser l'app
init_app()


# ===================================
# HEADER
# ===================================

def render_header():
    """Affiche l'en-tête de l'application"""
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown(f"""
            <div class="main-header">
                <h1>🤖 {settings.APP_NAME}</h1>
                <p style="color: var(--secondary-color); margin: 0;">
                    Assistant intelligent pour le quotidien familial
                </p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        # Status IA
        if settings.ENABLE_AI:
            st.markdown("""
                <div class="status-badge status-success">
                    🤖 IA Active
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="status-badge status-warning">
                    🤖 IA Désactivée
                </div>
            """, unsafe_allow_html=True)

    with col3:
        # Infos environnement (dev uniquement)
        if settings.DEBUG:
            st.caption(f"🔧 {settings.ENV.upper()}")
            db_info = get_db_info()
            if db_info["status"] == "connected":
                st.caption(f"✅ DB: {db_info['database']}")


render_header()


# ===================================
# SIDEBAR - NAVIGATION
# ===================================

def render_sidebar():
    """Affiche la sidebar avec navigation"""

    with st.sidebar:
        st.title("Navigation")

        # Modules principaux
        modules = {
            "🏠 Accueil": "accueil",
            "🍲 Cuisine": {
                "Recettes": "cuisine.recettes",
                "Inventaire": "cuisine.inventaire",
                "Batch Cooking": "cuisine.batch_cooking",
                "Courses": "cuisine.courses",
            },
            "👶 Famille": {
                "Suivi Jules": "famille.suivi_jules",
                "Bien-être": "famille.bien_etre",
                "Routines": "famille.routines",
            },
            "🏡 Maison": {
                "Projets": "maison.projets",
                "Jardin": "maison.jardin",
                "Entretien": "maison.entretien",
            },
            "📅 Planning": {
                "Calendrier": "planning.calendrier",
                "Vue d'ensemble": "planning.vue_ensemble",
            },
            "⚙️ Paramètres": "parametres",
        }

        # Afficher les modules
        for label, value in modules.items():
            if isinstance(value, dict):
                # Sous-menu
                with st.expander(label, expanded=(label == "🍲 Cuisine")):
                    for sub_label, sub_value in value.items():
                        if st.button(
                                sub_label,
                                key=f"btn_{sub_value}",
                                use_container_width=True
                        ):
                            st.session_state.current_module = sub_value
                            st.rerun()
            else:
                # Bouton direct
                if st.button(
                        label,
                        key=f"btn_{value}",
                        use_container_width=True
                ):
                    st.session_state.current_module = value
                    st.rerun()

        # Séparateur
        st.markdown("---")

        # Infos et stats rapides
        st.subheader("📊 Aperçu rapide")

        # TODO: Remplacer par vraies stats
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric("Recettes", "42")
            st.metric("Projets", "5")
        with col_s2:
            st.metric("Stock bas", "3")
            st.metric("Tâches", "12")

        # Bouton urgences IA
        st.markdown("---")
        if st.button("⚡ Actions urgentes IA", type="primary", use_container_width=True):
            st.session_state.current_module = "urgences_ia"
            st.rerun()


render_sidebar()


# ===================================
# ROUTAGE DES MODULES
# ===================================

def load_module(module_name: str):
    """Charge et affiche le module demandé"""
    try:
        # Mapping des modules
        module_map = {
            "accueil": "src.modules.accueil",
            "cuisine.recettes": "src.modules.cuisine.recettes",
            "cuisine.inventaire": "src.modules.cuisine.inventaire",
            "cuisine.batch_cooking": "src.modules.cuisine.batch_cooking",
            "cuisine.courses": "src.modules.cuisine.courses",
            "famille.suivi_jules": "src.modules.famille.suivi_jules",
            "famille.bien_etre": "src.modules.famille.bien_etre",
            "famille.routines": "src.modules.famille.routines",
            "maison.projets": "src.modules.maison.projets",
            "maison.jardin": "src.modules.maison.jardin",
            "maison.entretien": "src.modules.maison.entretien",
            "planning.calendrier": "src.modules.planning.calendrier",
            "planning.vue_ensemble": "src.modules.planning.vue_ensemble",
            "parametres": "src.modules.parametres",
            "urgences_ia": "src.modules.urgences_ia",
        }

        if module_name in module_map:
            import importlib
            module = importlib.import_module(module_map[module_name])

            # Appeler la fonction app() du module
            if hasattr(module, "app"):
                module.app()
            else:
                st.error(f"Le module {module_name} n'a pas de fonction app()")
        else:
            st.error(f"Module '{module_name}' non trouvé")

    except ImportError as e:
        st.error(f"Impossible de charger le module: {e}")
        st.info("Module en cours de développement...")

        # Afficher un placeholder
        st.markdown(f"## 🚧 Module {module_name}")
        st.info("Ce module sera bientôt disponible !")

    except Exception as e:
        st.error(f"Erreur dans le module: {e}")
        if settings.DEBUG:
            st.exception(e)


# Charger le module actuel
current = st.session_state.current_module
load_module(current)


# ===================================
# FOOTER
# ===================================

st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns([2, 1, 1])

with footer_col1:
    st.caption(f"💚 {settings.APP_NAME} v{settings.APP_VERSION}")

with footer_col2:
    if st.button("🐛 Reporter un bug", key="report_bug"):
        st.info("Ouvrir une issue sur GitHub")

with footer_col3:
    if st.button("ℹ️ À propos", key="about"):
        st.info("""
        Assistant familial intelligent propulsé par IA.
        
        Développé avec ❤️ pour réduire la charge mentale.
        """)


# ===================================
# POINT D'ENTRÉE
# ===================================

if __name__ == "__main__":
    # L'application est déjà lancée par Streamlit
    pass