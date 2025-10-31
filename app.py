import streamlit as st
import sys
import os

# Configurer la page (doit être le premier appel Streamlit)
st.set_page_config(page_title="CFA Sorigny - Portail", layout="wide", page_icon="🏫")

# Ajouter le chemin du sous-dossier apps et importer le système d'auth
sys.path.append(os.path.join(os.path.dirname(__file__), 'apps'))
from auth_system import AuthSystem
import config

# URL du logo
logo_url = "https://cfa-sorigny.fr/wp-content/uploads/2024/04/logo-cfa-sorigny-navbar.svg"

# Importer les modules d'applications dynamiquement
modules = {}
for app_id, app_config in config.APPLICATIONS_CONFIG.items():
    try:
        modules[app_id] = __import__(app_config['module'])
    except ImportError as e:
        st.error(f"Erreur d'importation du module {app_config['module']}: {e}")

# L'initialisation de app_choice se fera après l'authentification

# Personnalisation des boutons avec du CSS
st.markdown("""
    <style>
        .sidebar .sidebar-content {
            padding-top: 10px;
        }
        .sidebar button {
            width: 100%;
            background-color: #f1f1f1;
            border: 1px solid #ccc;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
            font-weight: bold;
            color: #333;
            text-align: left;
            transition: all 0.3s ease;
        }
        .sidebar button:hover {
            background-color: #e0e0e0;
        }
        .sidebar button:active {
            background-color: #d0d0d0;
        }
        .sidebar button.selected {
            background-color: #c5c5c5;
            color: #fff;
        }
    </style>
""", unsafe_allow_html=True)

def app():
    # Tentative de connexion automatique basée sur l'URL
    if not AuthSystem.is_authenticated():
        AuthSystem.auto_login_if_url_role()
    
    # Vérifier l'authentification
    if not AuthSystem.is_authenticated():
        AuthSystem.show_login_form()
        return
    
    # Afficher les informations utilisateur dans la sidebar
    AuthSystem.show_user_info()
    
    # Initialiser app_choice si pas déjà fait, en fonction des autorisations de l'utilisateur
    if 'app_choice' not in st.session_state:
        authorized_apps = AuthSystem.get_current_apps()
        if authorized_apps:
            # Prendre la première application autorisée
            st.session_state.app_choice = authorized_apps[0]
        else:
            st.session_state.app_choice = "presentation"  # Fallback
    
    # Créer une barre latérale à gauche avec le logo
    st.sidebar.image(logo_url, width=150)  # Affichage du logo dans la sidebar
    st.sidebar.title('Menu Applications')
    
    # Récupérer les applications autorisées pour l'utilisateur
    current_user = AuthSystem.get_current_user()
    authorized_apps = AuthSystem.get_current_apps()
    
    # Récupérer les catégories organisées depuis config.py
    categories = config.get_categories_for_role(current_user)
    
    # Affichage par catégories
    for category, apps in categories.items():
        st.sidebar.markdown(f"**{category}**")
        
        for app in apps:
            app_name = f"{app['icon']} {app['display_name']}"
            if st.sidebar.button(app_name, key=f"btn_{app['id']}"):
                st.session_state.app_choice = app['id']
        
        st.sidebar.markdown("---")
        

    # Vérifier que l'utilisateur a bien accès à l'application sélectionnée
    current_app = st.session_state.get('app_choice', "presentation")
    authorized_apps = AuthSystem.get_current_apps()
    
    # Si l'utilisateur n'a pas accès à l'app actuelle, rediriger vers la première app autorisée
    if current_app not in authorized_apps:
        if authorized_apps:
            current_app = authorized_apps[0]
            st.session_state.app_choice = current_app
        else:
            # Aucune application autorisée - ne devrait pas arriver
            current_app = "presentation"
            st.session_state.app_choice = current_app
    
    # Afficher le contenu en fonction du choix (avec vérification d'autorisation)
    if current_app in authorized_apps and current_app in modules:
        try:
            # Récupérer le module et la fonction appropriée
            app_module = modules[current_app]
            
            # La plupart des modules ont une fonction run(), sauf presentation
            if current_app == "presentation":
                app_module.show_presentation()
            else:
                app_module.run()
                
        except AttributeError as e:
            st.error(f"🚫 Erreur dans l'application {current_app}: {e}")
            st.info("Veuillez contacter l'administrateur")
    else:
        # App non autorisée ou inexistante
        st.error("🚫 Accès non autorisé à cette application")
        st.info("Veuillez contacter l'administrateur si vous pensez que c'est une erreur")
            

if __name__ == "__main__":
    app()
