"""
Module des fonctions SAMBA pour la gestion des utilisateurs
"""
import streamlit as st
import sys
import os
import logging

# Ajouter le chemin parent pour importer config et utils
sys.path.append('/home/streamlit')
import config

# Import des utilitaires locaux
from .utils import ssh_connection, execute_ssh_command, logger


def get_all_samba_users():
    """Récupère tous les utilisateurs SAMBA directement depuis le serveur"""
    users_list = []
    
    try:
        with ssh_connection(config.SAMBA_SERVER, config.SAMBA_USER, config.SAMBA_PWD) as client:
            if client:
                # Essayer plusieurs approches pour lister les utilisateurs
                commands_to_try = [
                    # Approche 1: LDAP search avec authentification système
                    "sudo -S ldapsearch -Y EXTERNAL -H ldapi:/// -b 'CN=Users,DC=cfa-eleves,DC=lan' '(&(objectClass=user)(!(objectClass=computer)))' sAMAccountName | grep sAMAccountName | cut -d' ' -f2",
                    
                    # Approche 2: LDAP avec différentes bases de recherche
                    "sudo -S ldapsearch -Y EXTERNAL -H ldapi:/// -b 'DC=cfa-eleves,DC=lan' '(&(objectClass=user)(!(objectClass=computer))(!(userAccountControl:1.2.840.113556.1.4.803:=2)))' sAMAccountName | grep sAMAccountName | cut -d' ' -f2",
                    
                    # Approche 3: Via wbinfo (tous les domaines)
                    "wbinfo -u",
                    
                    # Approche 4: getent avec domaine explicite
                    "getent passwd | grep '@cfa-eleves.lan' | cut -d: -f1 | cut -d@ -f1",
                    
                    # Approche 5: SAMBA tool avec authentification admin
                    "sudo -S samba-tool user list --username=Administrator --password=$(cat /etc/samba/admin_password 2>/dev/null)",
                    
                    # Approche 6: LDAP direct avec bind admin
                    "ldapsearch -x -H ldap://localhost:389 -D 'Administrator@cfa-eleves.lan' -w $(cat /etc/samba/admin_password 2>/dev/null) -b 'DC=cfa-eleves,DC=lan' '(&(objectClass=user)(!(objectClass=computer)))' sAMAccountName | grep sAMAccountName | cut -d' ' -f2",
                    
                    # Approche 7: Listing complet via net
                    "net rpc user list -U Administrator%$(cat /etc/samba/admin_password 2>/dev/null) 2>/dev/null",
                    
                    # Approche 8: Fallback basic getent
                    "getent passwd | cut -d: -f1"
                ]
                
                for i, cmd in enumerate(commands_to_try, 1):
                    output, error = execute_ssh_command(client, cmd, config.SAMBA_PWD, timeout=30)
                    
                    temp_users = []
                    if output:
                        # Filtrer les utilisateurs système
                        ignored_users = config.get_ignored_users()
                        
                        for line in output.split('\n'):
                            username = line.strip()
                            
                            # Extraire le nom d'utilisateur du format DOMAIN\username
                            if '\\' in username:
                                username = username.split('\\')[1]
                            
                            if (username and 
                                username.lower() not in [u.lower() for u in ignored_users] and
                                not username.startswith('#') and
                                not username.endswith('$') and
                                not username.startswith('CN=') and
                                username not in ['nobody', 'root', 'daemon', 'bin', 'sys', 'sync', 'halt', 'shutdown', 'mail', 'administrator', 'guest', 'krbtgt']):
                                temp_users.append(username)
                        
                        # Afficher le résultat de chaque approche pour debug
                        if temp_users:
                            st.info(f"🔍 Approche {i}: {len(temp_users)} utilisateurs trouvés")
                            if len(temp_users) > len(users_list):
                                users_list = temp_users
                                st.success(f"✅ Meilleur résultat avec approche {i}: {len(users_list)} utilisateurs")
                    
                    if error and len(temp_users) == 0:
                        st.warning(f"❌ Approche {i} échouée: {error[:100]}...")
                
                if users_list:
                    st.success(f"📋 **TOTAL FINAL: {len(users_list)} utilisateurs SAMBA** trouvés sur le serveur")
                    # Optionnel: afficher quelques exemples
                    if len(users_list) > 5:
                        sample = users_list[:5]
                        st.info(f"👥 Exemples d'utilisateurs: {', '.join(sample)}...")
                
                if not users_list:
                    st.warning("⚠️ Impossible de récupérer la liste des utilisateurs du serveur SAMBA. Utilisation du fichier Excel uniquement.")
                        
    except Exception as e:
        st.error(f"❌ Erreur de connexion SAMBA: {e}")
        
    return users_list


def check_user_exists_in_samba(username):
    """Vérifie si un utilisateur existe déjà dans SAMBA"""
    try:
        with ssh_connection(config.SAMBA_SERVER, config.SAMBA_USER, config.SAMBA_PWD) as client:
            if client:
                # Essayer plusieurs méthodes de vérification
                check_commands = [
                    # Approche 1: Via wbinfo avec domaine
                    f"wbinfo -i 'CFA-ELEVES\\{username}' >/dev/null 2>&1 && echo 'exists' || echo 'not found'",
                    
                    # Approche 2: Via getent avec domaine
                    f"getent passwd 'CFA-ELEVES\\{username}' >/dev/null 2>&1 && echo 'exists' || echo 'not found'",
                    
                    # Approche 3: Via wbinfo sans domaine
                    f"wbinfo -i {username} >/dev/null 2>&1 && echo 'exists' || echo 'not found'",
                    
                    # Approche 4: SAMBA tool
                    f"sudo -S samba-tool user show {username} >/dev/null 2>&1 && echo 'exists' || echo 'not found'",
                    
                    # Approche 5: Vérification dans la liste wbinfo
                    f"wbinfo -u | grep -i '^CFA-ELEVES\\\\{username}$' >/dev/null 2>&1 && echo 'exists' || echo 'not found'"
                ]
                
                for cmd in check_commands:
                    output, error = execute_ssh_command(client, cmd, config.SAMBA_PWD, timeout=10)
                    
                    if output and 'exists' in output:
                        logger.info(f"Utilisateur {username} trouvé dans SAMBA")
                        return True
                    elif output and 'not found' in output:
                        # Cette méthode confirme que l'utilisateur n'existe pas
                        logger.info(f"Utilisateur {username} non trouvé dans SAMBA")
                        return False
                    # Sinon continuer avec la méthode suivante
                
                # Si toutes les méthodes échouent, supposer qu'il n'existe pas
                logger.warning(f"Impossible de vérifier l'existence de {username}, supposé inexistant")
                return False
                        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de l'utilisateur {username}: {e}")
        return False  # En cas d'erreur, on suppose qu'il n'existe pas
    
    return False


def get_samba_group_members(group_name):
    """Récupère la liste des membres d'un groupe Samba spécifique"""
    members_list = []
    
    try:
        with ssh_connection(config.SAMBA_SERVER, config.SAMBA_USER, config.SAMBA_PWD) as client:
            if client:
                # Commande pour lister les membres d'un groupe
                cmd = f"sudo -S samba-tool group listmembers {group_name}"
                output, error = execute_ssh_command(client, cmd, config.SAMBA_PWD)
                
                if output and not error:
                    # Filtrer les utilisateurs
                    ignored_users = config.get_ignored_users()
                    
                    for line in output.split('\n'):
                        username = line.strip()
                        if username and username.lower() not in [u.lower() for u in ignored_users]:
                            members_list.append(username)
                    
                    st.info(f"📋 {len(members_list)} membres trouvés dans le groupe '{group_name}'")
                else:
                    if "does not exist" in error.lower():
                        st.warning(f"⚠️ Le groupe '{group_name}' n'existe pas")
                    else:
                        st.error(f"❌ Erreur lors de la récupération du groupe: {error}")
                        
    except Exception as e:
        st.error(f"❌ Erreur de connexion Samba: {e}")
        
    return members_list


def add_students_to_wifi_group_by_description(descriptions_filter, target_group="WIFI"):
    """Ajoute les élèves au groupe WIFI basé sur leurs descriptions (classe)"""
    from .utils import get_existing_users
    
    results = []
    added_count = 0
    
    try:
        # Récupérer la liste des utilisateurs existants
        df_users = get_existing_users()
        
        if df_users.empty:
            st.warning("Aucun utilisateur trouvé dans la base de données")
            return results, 0
            
        # Filtrer les utilisateurs selon leurs descriptions (classes)
        matching_users = []
        for _, user in df_users.iterrows():
            if 'Classe' in df_users.columns:
                user_classe = str(user['Classe']).strip().upper()
                # Vérifier si la classe contient une des descriptions recherchées
                for desc in descriptions_filter:
                    if desc.upper() in user_classe:
                        matching_users.append(user)
                        break
        
        if not matching_users:
            st.info(f"Aucun utilisateur trouvé avec les descriptions : {', '.join(descriptions_filter)}")
            return results, 0
        
        st.info(f"🔍 {len(matching_users)} utilisateurs trouvés correspondant aux critères")
        
        # Connexion SSH et ajout au groupe
        with ssh_connection(config.SAMBA_SERVER, config.SAMBA_USER, config.SAMBA_PWD) as client:
            if client:
                # Créer le groupe WIFI s'il n'existe pas
                create_group_cmd = f"sudo -S samba-tool group add {target_group} || true"
                output, error = execute_ssh_command(client, create_group_cmd, config.SAMBA_PWD)
                
                # Ajouter chaque utilisateur au groupe WIFI
                for user in matching_users:
                    username = user['Login']
                    user_class = user['Classe'] if 'Classe' in user else 'N/A'
                    
                    add_to_group_cmd = f"sudo -S samba-tool group addmembers {target_group} {username}"
                    output, error = execute_ssh_command(client, add_to_group_cmd, config.SAMBA_PWD)
                    
                    if error:
                        if "is already a member" in error.lower():
                            results.append(f"ℹ️ {username} ({user_class}) : Déjà membre du groupe {target_group}")
                        else:
                            results.append(f"❌ {username} ({user_class}) : {error}")
                    else:
                        results.append(f"✅ {username} ({user_class}) : Ajouté au groupe {target_group}")
                        added_count += 1
            else:
                st.error("❌ Impossible de se connecter au serveur Samba")
                
    except Exception as e:
        st.error(f"❌ Erreur lors de l'ajout au groupe WIFI : {e}")
        results.append(f"❌ Erreur générale : {e}")
        
    return results, added_count


def create_samba_user(username, password, prenom, nom, classe_normalized, groupe_cible):
    """Crée un utilisateur SAMBA avec les paramètres donnés"""
    try:
        # Nettoyer et échapper les paramètres
        username_clean = str(username).strip()
        password_clean = str(password).replace("'", "\\'")  # Échapper les apostrophes
        prenom_clean = str(prenom).strip().replace("'", "\\'")
        nom_clean = str(nom).strip().replace("'", "\\'")
        classe_clean = str(classe_normalized).strip().replace("'", "\\'")
        groupe_clean = str(groupe_cible).strip()
        
        # Vérifier d'abord si l'utilisateur existe déjà
        if check_user_exists_in_samba(username_clean):
            logger.info(f"Utilisateur {username_clean} existe déjà dans SAMBA")
            return True, f"Utilisateur {username_clean} existe déjà (ignoré)"
        
        # Commande de création d'utilisateur
        create_cmd = (
            f"sudo -S samba-tool user create '{username_clean}' '{password_clean}' "
            f"--given-name='{prenom_clean}' --surname='{nom_clean}' "
            f"--description='{classe_clean}'"
        )
        
        # Commande d'ajout au groupe
        group_cmd = f"sudo -S samba-tool group addmembers '{groupe_clean}' '{username_clean}'"
        
        # Exécuter les commandes
        with ssh_connection(config.SAMBA_SERVER, config.SAMBA_USER, config.SAMBA_PWD) as client:
            if client is None:
                return False, "Impossible de se connecter au serveur SAMBA"
            
            # Créer l'utilisateur
            output, error = execute_ssh_command(client, create_cmd, config.SAMBA_PWD, timeout=60)
            
            if error and not any(msg in error.lower() for msg in ["user already exists", "utilisateur existe déjà", "entry already exists", "entrée existe déjà"]):
                return False, f"Erreur création utilisateur: {error}"
            elif error and any(msg in error.lower() for msg in ["user already exists", "utilisateur existe déjà", "entry already exists", "entrée existe déjà"]):
                logger.info(f"Utilisateur {username_clean} existe déjà dans SAMBA")
                return True, f"Utilisateur {username_clean} existe déjà (non créé)"
            
            # Ajouter au groupe
            output, error = execute_ssh_command(client, group_cmd, config.SAMBA_PWD, timeout=30)
            
            if error and not any(msg in error.lower() for msg in ["is already a member", "est déjà membre"]):
                # Ne pas échouer complètement pour les problèmes de groupe
                logger.warning(f"Avertissement groupe pour {username_clean}: {error}")
            
            return True, f"Utilisateur {username_clean} créé avec succès"
                
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'utilisateur {username}: {e}")
        return False, f"Erreur générale: {str(e)}"


def delete_samba_user(username):
    """Supprime un utilisateur SAMBA"""
    try:
        cmd_delete = f"sudo -S samba-tool user delete {username}"
        
        with ssh_connection(config.SAMBA_SERVER, config.SAMBA_USER, config.SAMBA_PWD) as client:
            if client:
                output, error = execute_ssh_command(client, cmd_delete, config.SAMBA_PWD)
                if error:
                    return False, error
                else:
                    return True, f"Utilisateur {username} supprimé avec succès"
            else:
                return False, "Impossible de se connecter au serveur Samba"
    except Exception as e:
        return False, str(e)


def reset_samba_password(username, new_password):
    """Remet à zéro le mot de passe d'un utilisateur SAMBA"""
    try:
        cmd_reset = f"sudo -S samba-tool user setpassword {username} --newpassword='{new_password}'"
        
        with ssh_connection(config.SAMBA_SERVER, config.SAMBA_USER, config.SAMBA_PWD) as client:
            if client:
                output, error = execute_ssh_command(client, cmd_reset, config.SAMBA_PWD)
                if error:
                    return False, error
                else:
                    return True, f"Mot de passe de {username} mis à jour"
            else:
                return False, "Impossible de se connecter au serveur Samba"
    except Exception as e:
        return False, str(e)