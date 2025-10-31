import streamlit as st
import hashlib
import time
import sys
import os

# Ajouter le chemin parent pour importer config
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import config

class AuthSystem:
    """Système d'authentification avec niveaux d'accès"""
    
    # Configuration des niveaux d'accès - centralisée dans config.py
    @staticmethod
    def get_user_roles():
        """Retourne la configuration des rôles depuis config.py"""
        return config.USER_ROLES
    
    @staticmethod
    def hash_password(password):
        """Hash un mot de passe pour plus de sécurité"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def check_password(username, password):
        """Vérifie si le mot de passe est correct"""
        user_roles = AuthSystem.get_user_roles()
        if username in user_roles:
            user_password = user_roles[username]["password"]
            if user_password is None:  # Pas de mot de passe requis
                return True
            return user_password == password
        return False
    
    @staticmethod
    def detect_role_from_url():
        """Détecte le rôle de l'utilisateur basé sur l'URL"""
        try:
            # Récupérer les paramètres de requête Streamlit (nouvelle API)
            query_params = st.query_params
            
            # Vérifier si un rôle est spécifié dans l'URL
            if 'role' in query_params:
                role = query_params['role'].lower()
                if role in AuthSystem.get_user_roles():
                    return role
                    
        except Exception as e:
            # Fallback pour les anciennes versions de Streamlit
            try:
                query_params = st.experimental_get_query_params()
                if 'role' in query_params:
                    role = query_params['role'][0].lower()
                    if role in AuthSystem.get_user_roles():
                        return role
            except:
                pass
        
        return None
    
    @staticmethod 
    def auto_login_if_url_role():
        """Connecte automatiquement l'utilisateur si détecté via URL"""
        role = AuthSystem.detect_role_from_url()
        user_roles = AuthSystem.get_user_roles()
        if role and role in user_roles:
            user_config = user_roles[role]
            if user_config["password"] is None:  # Rôle sans mot de passe
                st.session_state['authenticated'] = True
                st.session_state['current_user'] = role
                st.session_state['login_time'] = time.time()
                st.session_state['url_login'] = True
                return True
        return False
    
    @staticmethod
    def get_user_level(username):
        """Récupère le niveau d'accès d'un utilisateur"""
        user_roles = AuthSystem.get_user_roles()
        if username in user_roles:
            return user_roles[username]["display_name"]
        return None
    
    @staticmethod
    def get_user_apps(username):
        """Récupère la liste des applications autorisées pour un utilisateur"""
        # Utiliser la nouvelle fonction centralisée
        return config.get_apps_for_role(username)
    
    @staticmethod
    def is_authenticated():
        """Vérifie si l'utilisateur est authentifié"""
        return st.session_state.get('authenticated', False)
    
    @staticmethod
    def get_current_user():
        """Récupère l'utilisateur actuellement connecté"""
        return st.session_state.get('current_user', None)
    
    @staticmethod
    def get_current_level():
        """Récupère le niveau de l'utilisateur actuel"""
        user = AuthSystem.get_current_user()
        if user:
            return AuthSystem.get_user_level(user)
        return None
    
    @staticmethod
    def get_current_apps():
        """Récupère les applications autorisées pour l'utilisateur actuel"""
        user = AuthSystem.get_current_user()
        if user:
            return AuthSystem.get_user_apps(user)
        return []
    
    @staticmethod
    def login(username, password):
        """Connecte un utilisateur"""
        if AuthSystem.check_password(username, password):
            st.session_state['authenticated'] = True
            st.session_state['current_user'] = username
            st.session_state['login_time'] = time.time()
            return True
        return False
    
    @staticmethod
    def logout():
        """Déconnecte l'utilisateur"""
        # Supprimer toutes les clés de session liées à l'authentification
        keys_to_remove = ['authenticated', 'current_user', 'login_time', 'app_choice', 'url_login']
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
        
        # Nettoyer les paramètres d'URL
        try:
            st.query_params.clear()
        except:
            # Fallback pour les anciennes versions de Streamlit
            try:
                st.experimental_set_query_params()
            except:
                pass
    
    @staticmethod
    def show_login_form():
        """Affiche la page d'accueil avec présentation et accès"""
        # Page de présentation centrée
        st.markdown("""
        <div style="text-align: center;">
            <h1>Bienvenue StreamLit, l'outil magique du CFA</h1>
            <img src="https://cfa-sorigny.fr/wp-content/uploads/2024/04/logo-cfa-sorigny-navbar.svg" width="150" height="150">
            <h2>Présentation de l'outil</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Texte de présentation centré
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            st.markdown("""
            <div style="text-align: center;">
                <p>Streamlit est un framework open-source en Python qui permet de créer des applications web interactives de manière rapide et simple.</p>
                <p>Au CFA il va être principalement utilisé pour vous faire gagner du temps.</p>
                <p>Des tâches répétitives qui peuvent être automatisées, des calculs fastidieux qui peuvent être simplifiés, des données qui peuvent être visualisées de manière plus claire, Streamlit sera là pour vous aider.</p>
                <p>La seule contrainte est que Gaëtan soit pas trop nul en Python (et sur un bon jour, donc pas trop grincheux).</p>
                <p><strong>L'outil est simple à utiliser et permet de gagner du temps dans le traitement des informations.</strong></p>
            </div>
            """, unsafe_allow_html=True)
        
        # Section des accès - Boutons visibles dès l'arrivée
        st.markdown("""
        <div style="text-align: center;">
            <h2>Accès aux Applications</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Boutons d'accès côte à côte
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Accès Formateur")
            st.write("**Applications disponibles :**")
            # Affichage dynamique des applications selon config.py
            formateur_apps = config.get_apps_for_role("formateur")
            for app_id in formateur_apps:
                app_config = config.get_app_config(app_id)
                if app_config:
                    st.write(f"• **{app_config['display_name']}** - {app_config['description']}")
            if st.button("Accéder en tant que Formateur", key="btn_formateur", type="primary", use_container_width=True):
                st.query_params.role = "formateur"
                st.rerun()
                
        with col2:
            st.markdown("### Accès Secrétariat")
            st.write("**Applications disponibles :**")
            # Affichage dynamique des applications selon config.py
            secretariat_apps = config.get_apps_for_role("secretariat")
            for app_id in secretariat_apps:
                app_config = config.get_app_config(app_id)
                if app_config:
                    st.write(f"• **{app_config['display_name']}** - {app_config['description']}")
            if st.button("Accéder en tant que Secrétariat", key="btn_secretariat", type="primary", use_container_width=True):
                st.query_params.role = "secretariat"
                st.rerun()
        
        # Authentification admin en bas
        st.markdown("""
        <div style="text-align: center;">
            <h2>Accès Administrateur</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Centrer le formulaire admin
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("### Connexion Administrateur")
            # Formulaire de connexion admin
            with st.form("admin_login_form"):
                password = st.text_input("Mot de passe administrateur:", type="password")
                
                submitted = st.form_submit_button("Se connecter", type="secondary", use_container_width=True)
                
                if submitted:
                    if password:
                        if AuthSystem.login("admin", password):
                            st.success("Connexion administrateur réussie !")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Mot de passe administrateur incorrect")
                    else:
                        st.warning("Veuillez saisir le mot de passe administrateur")
            
    @staticmethod
    def show_user_info():
        """Affiche les informations de l'utilisateur connecté"""
        if AuthSystem.is_authenticated():
            user = AuthSystem.get_current_user()
            level = AuthSystem.get_current_level()
            
            # Récupérer l'icône depuis la configuration
            user_roles = AuthSystem.get_user_roles()
            icon = user_roles.get(user, {}).get("icon", "👤")
            
            st.sidebar.markdown(f"""
            ### {icon} Session active
            **Profil:** {level}  
            **Utilisateur:** {user}
            """)
            
            if st.sidebar.button("🚪 Se déconnecter", key="logout_btn"):
                AuthSystem.logout()
                st.success("Déconnexion réussie")
                time.sleep(0.5)
                st.rerun()
            
            st.sidebar.markdown("---")
            
            return True
        return False
    
    @staticmethod
    def require_auth(func):
        """Décorateur pour les fonctions nécessitant une authentification"""
        def wrapper(*args, **kwargs):
            if AuthSystem.is_authenticated():
                return func(*args, **kwargs)
            else:
                AuthSystem.show_login_form()
                return None
        return wrapper