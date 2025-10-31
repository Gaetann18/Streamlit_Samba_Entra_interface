"""
Module pour l'onglet Sync IMFR/SAMBA
"""
import streamlit as st
import pandas as pd
import sys
import os

# Ajouter les chemins nécessaires
sys.path.append('/home/streamlit')
sys.path.append('/home/streamlit/apps')
sys.path.append('/home/streamlit/apps/gestion_utilisateurs')

import config
from modules.utils import (
    get_existing_users, generate_username, generate_password, 
    normalize_class_name, save_user_to_excel
)
from modules.imfr_functions import compare_imfr_samba
from modules.samba_functions import create_samba_user, check_user_exists_in_samba, get_all_samba_users

# Import du module eleves_utils pour la récupération des élèves
try:
    from eleves_utils import charger_eleves, afficher_bouton_actualisation, get_eleves_dataframe
except ImportError:
    st.error("Module eleves_utils non trouvé")
    charger_eleves = lambda: []
    afficher_bouton_actualisation = lambda key_suffix="": None
    get_eleves_dataframe = lambda: pd.DataFrame()


def render_sync_imfr_samba_tab():
    """Affiche l'onglet de synchronisation IMFR/SAMBA"""
    st.header("Synchronisation IMFR / SAMBA")
    st.markdown("**Comparez et synchronisez automatiquement les listes d'élèves entre IMFR et SAMBA**")
    
    # Section des données actuelles
    st.subheader("📊 État actuel des données")
    
    col_status1, col_status2, col_status3 = st.columns(3)
    
    with col_status1:
        # Récupération automatique des utilisateurs SAMBA
        df_samba = get_existing_users()
        samba_count = len(df_samba) if not df_samba.empty else 0
        st.metric("👥 Utilisateurs SAMBA", samba_count)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("📄 Actualiser Excel", help="Recharge la liste depuis le fichier Excel"):
                st.session_state.pop('samba_data_cached', None)  # Clear cache
                st.rerun()
        
        with col_btn2:
            if st.button("🌐 Vérifier Serveur", help="Vérifie les utilisateurs directement sur le serveur SAMBA"):
                with st.spinner("Vérification des utilisateurs sur le serveur (test de plusieurs méthodes)..."):
                    st.info("🔍 **Analyse des méthodes de récupération SAMBA...**")
                    samba_users_live = get_all_samba_users()
                    st.session_state['samba_users_live'] = samba_users_live
                    
                    if len(samba_users_live) < 200:  # Si moins que prévu
                        st.warning(f"⚠️ **Attention**: Seulement {len(samba_users_live)} utilisateurs trouvés (attendu ~300)")
                        st.info("💡 **Conseil**: Si ce nombre semble faible, vérifiez les permissions d'accès ou contactez l'administrateur système")
                    else:
                        st.success(f"✅ **Excellent!** {len(samba_users_live)} utilisateurs récupérés du serveur")
    
    with col_status2:
        # État des données élèves
        eleves_data = charger_eleves()
        eleves_count = len(eleves_data) if eleves_data else 0
        st.metric("🏫 Élèves JSON", eleves_count)
        
        if st.button("🔄 Actualiser Élèves", help="Recharge la liste depuis le fichier JSON"):
            st.session_state.pop('eleves_data', None)  # Clear cache
            st.rerun()
    
    with col_status3:
        # Statut de synchronisation
        if 'eleves_data' in st.session_state and not df_samba.empty:
            missing_count = _calculate_missing_students(st.session_state['eleves_data'], df_samba)
            st.metric("⚠️ Manquants dans SAMBA", missing_count)
        elif eleves_data and not df_samba.empty:
            df_eleves_temp = get_eleves_dataframe()
            missing_count = _calculate_missing_students(df_eleves_temp, df_samba)
            st.metric("⚠️ Manquants dans SAMBA", missing_count)
        else:
            st.metric("⚠️ Manquants dans SAMBA", "−")
    
    st.markdown("---")
    
    # Section de récupération des élèves
    st.subheader("📥 Données des élèves")
    _render_eleves_section()
    
    st.markdown("---")
    
    # Section de comparaison (toujours visible)
    _render_comparison_section_auto()


def _calculate_missing_students(df_eleves, df_samba):
    """Calcule rapidement le nombre d'élèves manquants dans SAMBA"""
    if df_eleves.empty or df_samba.empty:
        return len(df_eleves) if not df_eleves.empty else 0
    
    missing_count = 0
    for _, eleve in df_eleves.iterrows():
        eleve_nom = str(eleve['Nom']).strip().upper()
        eleve_prenom = str(eleve['Prénom']).strip().title()
        
        # Chercher dans SAMBA
        found = False
        for _, samba_student in df_samba.iterrows():
            samba_nom = str(samba_student.get('Nom', '')).strip().upper()
            samba_prenom = str(samba_student.get('Prénom', '')).strip().title()
            
            if eleve_nom == samba_nom and eleve_prenom == samba_prenom:
                found = True
                break
        
        if not found:
            missing_count += 1
    
    return missing_count


def _render_eleves_section():
    """Affiche la section de récupération des élèves depuis le JSON"""
    
    # Affichage du bouton d'actualisation
    afficher_bouton_actualisation("sync_imfr_samba")
    
    st.markdown("---")
    
    # Chargement des données élèves
    eleves_data = charger_eleves()
    
    if eleves_data:
        df_eleves = get_eleves_dataframe()
        st.success(f"✅ Données élèves chargées : {len(df_eleves)} élèves")
        
        # Aperçu des données
        with st.expander("👁️ Aperçu des données élèves", expanded=False):
            st.dataframe(df_eleves.head(10), hide_index=True, use_container_width=True)
        
        # Sauvegarder dans session state pour la comparaison
        st.session_state['eleves_data'] = df_eleves
    else:
        st.info("🔍 Aucune donnée élève chargée. Actualisez la liste depuis l'application 'Récupération Élèves'")
        st.session_state.pop('eleves_data', None)


def _render_comparison_section_auto():
    """Affiche la section de comparaison automatique"""
    st.subheader("🔍 Comparaison Élèves vs SAMBA")
    
    # Récupérer les données
    df_samba = get_existing_users()
    df_eleves = st.session_state.get('eleves_data', pd.DataFrame())
    
    if df_eleves.empty and df_samba.empty:
        st.warning("⚠️ Aucune donnée disponible pour la comparaison")
        st.info("Récupérez d'abord les données élèves et vérifiez les utilisateurs SAMBA")
        return
    
    if df_eleves.empty:
        st.info("📋 Récupérez d'abord les données élèves pour effectuer la comparaison")
        
        # Affichage des utilisateurs SAMBA seulement
        if not df_samba.empty:
            st.subheader("👥 Utilisateurs actuels dans SAMBA")
            display_columns = ['Nom', 'Prénom', 'Login']
            if 'Classe' in df_samba.columns:
                display_columns.append('Classe')
            
            df_display = df_samba[display_columns].copy() if all(col in df_samba.columns for col in display_columns) else df_samba
            st.dataframe(df_display, hide_index=True, use_container_width=True)
        return
    
    if df_samba.empty:
        st.warning("⚠️ Aucun utilisateur trouvé dans SAMBA")
        st.info("Vérifiez le fichier Excel des utilisateurs SAMBA")
        return
    
    # Comparaison complète
    missing_in_samba, extra_in_samba = compare_imfr_samba(df_eleves, df_samba)
    
    # Statistiques
    col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
    
    with col_stats1:
        st.metric("🏫 Élèves total", len(df_eleves))
    with col_stats2:
        st.metric("👥 Utilisateurs SAMBA", len(df_samba))
    with col_stats3:
        st.metric("⚠️ Manquants SAMBA", len(missing_in_samba))
    with col_stats4:
        st.metric("➕ Excédents SAMBA", len(extra_in_samba))
    
    # Affichage des résultats
    if missing_in_samba:
        _render_missing_students_section(missing_in_samba)
    else:
        st.success("✅ Tous les élèves sont déjà présents dans SAMBA!")
    
    if extra_in_samba:
        _render_extra_students_section(extra_in_samba)


# Anciennes fonctions supprimées - remplacées par les versions automatiques


def _render_missing_students_section(missing_in_samba):
    """Affiche la section des élèves manquants dans SAMBA"""
    if missing_in_samba:
        st.subheader("➕ Élèves à créer dans SAMBA")
        
        df_missing = pd.DataFrame(missing_in_samba)
        # S'assurer que les colonnes existent
        display_cols = []
        for col in ['Nom', 'Prénom', 'Classe']:
            if col in df_missing.columns:
                display_cols.append(col)
        
        if display_cols:
            st.dataframe(df_missing[display_cols], hide_index=True, use_container_width=True)
        else:
            st.dataframe(df_missing, hide_index=True, use_container_width=True)
        
        # Section de sélection des élèves à exclure
        st.markdown("---")
        st.subheader("🎯 Sélection des élèves à créer")
        
        # Créer la liste des options pour la sélection
        eleves_options = []
        classes_disponibles = set()
        for i, eleve in enumerate(missing_in_samba):
            nom = str(eleve.get('Nom', eleve.get('nom', ''))).strip()
            prenom = str(eleve.get('Prénom', eleve.get('prenom', ''))).strip()
            classe = str(eleve.get('Classe', eleve.get('classe', ''))).strip()
            eleves_options.append(f"{prenom} {nom} ({classe})")
            classes_disponibles.add(classe)
        
        # Filtre par classe
        st.markdown("**🎯 Filtrage par classe (optionnel) :**")
        classes_list = ["Toutes les classes"] + sorted(list(classes_disponibles))
        classe_filtre = st.selectbox(
            "Filtrer par classe",
            options=classes_list,
            help="Sélectionnez une classe pour voir uniquement ses élèves"
        )
        
        # Appliquer le filtre
        if classe_filtre != "Toutes les classes":
            filtered_indices = []
            filtered_options = []
            for i, eleve in enumerate(missing_in_samba):
                classe = str(eleve.get('Classe', eleve.get('classe', ''))).strip()
                if classe == classe_filtre:
                    filtered_indices.append(i)
                    filtered_options.append(eleves_options[i])
        else:
            filtered_indices = list(range(len(eleves_options)))
            filtered_options = eleves_options
        
        # Sélection multiple avec tous sélectionnés par défaut
        st.markdown("**Sélectionnez les élèves à créer :**")
        
        if classe_filtre != "Toutes les classes":
            st.info(f"📚 Affichage filtré : {len(filtered_indices)} élève(s) de la classe **{classe_filtre}**")
        
        # Boutons de sélection rapide
        col_select1, col_select2, col_select3 = st.columns(3)
        with col_select1:
            if st.button("✅ Tout sélectionner", help="Sélectionner tous les élèves (dans le filtre actuel)"):
                st.session_state.selected_students_key = filtered_indices.copy()
                st.rerun()
        
        with col_select2:
            if st.button("❌ Tout désélectionner", help="Désélectionner tous les élèves"):
                st.session_state.selected_students_key = []
                st.rerun()
        
        with col_select3:
            if st.button("🔄 Inverser sélection", help="Inverser la sélection (dans le filtre actuel)"):
                current_selection = st.session_state.get('selected_students_key', [])
                inverted = []
                for idx in filtered_indices:
                    if idx not in current_selection:
                        inverted.append(idx)
                # Garder les sélections en dehors du filtre
                for idx in current_selection:
                    if idx not in filtered_indices:
                        inverted.append(idx)
                st.session_state.selected_students_key = inverted
                st.rerun()
        
        # Multiselect principal - afficher seulement les élèves filtrés
        current_selection = st.session_state.get('selected_students_key', filtered_indices)
        filtered_selection = [idx for idx in current_selection if idx in filtered_indices]
        
        selected_filtered_indices = st.multiselect(
            "Élèves à créer dans SAMBA",
            options=filtered_indices,
            format_func=lambda x: eleves_options[x],
            default=filtered_selection,
            help="Désélectionnez les élèves que vous ne voulez pas créer",
            key="multiselect_students"
        )
        
        # Combiner la sélection filtrée avec les sélections existantes en dehors du filtre
        existing_selection = st.session_state.get('selected_students_key', [])
        outside_filter_selection = [idx for idx in existing_selection if idx not in filtered_indices]
        final_selection = selected_filtered_indices + outside_filter_selection
        
        # Sauvegarder la sélection complète
        st.session_state.selected_students_key = final_selection
        selected_indices = final_selection
        
        # Afficher le résumé de la sélection
        col_summary1, col_summary2 = st.columns(2)
        with col_summary1:
            st.metric("📋 Total manquants", len(missing_in_samba))
        with col_summary2:
            st.metric("✅ Sélectionnés pour création", len(selected_indices))
        
        if len(selected_indices) != len(missing_in_samba):
            excluded_count = len(missing_in_samba) - len(selected_indices)
            st.info(f"ℹ️ {excluded_count} élève(s) exclu(s) de la création")
        
        # Afficher les élèves sélectionnés en dehors du filtre actuel
        if classe_filtre != "Toutes les classes" and outside_filter_selection:
            st.info(f"📋 {len(outside_filter_selection)} élève(s) sélectionné(s) dans d'autres classes")
        
        # Vérification des utilisateurs potentiellement existants
        potentially_existing = []
        
        # Vérifier d'abord avec les utilisateurs du serveur si disponible
        if 'samba_users_live' in st.session_state and st.session_state['samba_users_live']:
            samba_users_live = st.session_state['samba_users_live']
            
            for eleve in [missing_in_samba[i] for i in selected_indices]:
                nom = str(eleve.get('Nom', eleve.get('nom', ''))).strip()
                prenom = str(eleve.get('Prénom', eleve.get('prenom', ''))).strip()
                potential_username = generate_username(prenom, nom)
                
                if potential_username.lower() in [u.lower() for u in samba_users_live]:
                    potentially_existing.append(f"{prenom} {nom} (→ {potential_username})")
        
        # Sinon utiliser les utilisateurs Excel comme fallback
        else:
            df_samba_excel = get_existing_users()
            if not df_samba_excel.empty and 'Login' in df_samba_excel.columns:
                excel_logins = df_samba_excel['Login'].str.lower().tolist()
                
                for eleve in [missing_in_samba[i] for i in selected_indices]:
                    nom = str(eleve.get('Nom', eleve.get('nom', ''))).strip()
                    prenom = str(eleve.get('Prénom', eleve.get('prenom', ''))).strip()
                    potential_username = generate_username(prenom, nom)
                    
                    if potential_username.lower() in excel_logins:
                        potentially_existing.append(f"{prenom} {nom} (→ {potential_username})")
        
        if potentially_existing:
            st.warning(
                f"⚠️ **Attention** : {len(potentially_existing)} élève(s) sélectionné(s) semble(nt) déjà exister :\n\n" +
                "\n".join([f"• {user}" for user in potentially_existing]) +
                "\n\n💡 Ces utilisateurs seront vérifiés et ignorés si existants lors de la création."
            )
        
        # Information sur le format des noms d'utilisateur
        st.info("📝 **Format des noms d'utilisateur** : `prenom.nom` (ex: jean.dupont)")
        
        # Configuration de création
        st.markdown("---")
        col_create1, col_create2 = st.columns(2)
        
        with col_create1:
            groupe_cible = st.selectbox(
                "Groupe SAMBA pour les nouveaux élèves",
                ["Eleves", "WIFI", "Autre"],
                index=0
            )
            
            if groupe_cible == "Autre":
                groupe_cible = st.text_input("Nom du groupe personnalisé", value="Eleves")
        
        with col_create2:
            generate_passwords = st.checkbox("Générer des mots de passe automatiquement", value=True)
            send_to_excel = st.checkbox("Sauvegarder dans le fichier Excel", value=True)
        
        # Bouton de création avec validation
        button_disabled = len(selected_indices) == 0
        button_text = f"🔨 Créer les {len(selected_indices)} élève(s) sélectionné(s)" if selected_indices else "🔨 Aucun élève sélectionné"
        
        if st.button(button_text, type="primary", disabled=button_disabled):
            if selected_indices:
                # Filtrer les élèves sélectionnés
                selected_students = [missing_in_samba[i] for i in selected_indices]
                _create_missing_students(selected_students, groupe_cible, generate_passwords, send_to_excel)
    else:
        st.success("✅ Tous les élèves d'IMFR sont déjà présents dans SAMBA!")


def _render_extra_students_section(extra_in_samba):
    """Affiche la section des élèves en plus dans SAMBA"""
    if extra_in_samba:
        st.markdown("---")
        st.subheader("⚠️ Élèves présents uniquement dans SAMBA")
        st.markdown("*Ces élèves sont dans SAMBA mais pas dans IMFR*")
        
        df_extra = pd.DataFrame(extra_in_samba)
        required_columns = ['Nom', 'Prénom', 'Login']
        display_columns = [col for col in required_columns if col in df_extra.columns]
        
        if 'Classe' in df_extra.columns:
            display_columns.append('Classe')
        
        st.dataframe(df_extra[display_columns], hide_index=True, use_container_width=True)
        
        st.info("💡 Ces comptes peuvent être des anciens élèves ou des comptes créés manuellement.")


def _create_missing_students(missing_in_samba, groupe_cible, generate_passwords, send_to_excel):
    """Crée les élèves manquants dans SAMBA"""
    creation_results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, student in enumerate(missing_in_samba):
        nom = str(student['Nom']).strip()
        prenom = str(student['Prénom']).strip()
        classe = str(student['Classe']).strip()
        
        status_text.text(f"Création de {prenom} {nom}... ({idx+1}/{len(missing_in_samba)})")
        
        # Générer username et password
        username = generate_username(prenom, nom)
        if generate_passwords:
            password = generate_password()
        else:
            import random
            password = f"{nom.lower()}{prenom.lower()[0]}{random.randint(10,99)}"
        
        # Créer l'utilisateur SAMBA
        try:
            # Normaliser la classe
            classe_normalized = normalize_class_name(classe) if classe else ""
            
            success, message = create_samba_user(username, password, prenom, nom, classe_normalized, groupe_cible)
            
            if success:
                result = f"✅ {prenom} {nom} ({classe_normalized}) : Utilisateur créé avec succès"
                creation_results.append(result)
                
                # Sauvegarder dans Excel si demandé
                if send_to_excel:
                    save_user_to_excel(username, prenom, nom, password, classe_normalized, groupe_cible)
            else:
                result = f"❌ {prenom} {nom} : {message}"
                creation_results.append(result)
            
        except Exception as e:
            result = f"❌ {prenom} {nom} : {str(e)}"
            creation_results.append(result)
        
        progress_bar.progress((idx + 1) / len(missing_in_samba))
    
    status_text.text("Création terminée!")
    
    # Afficher les résultats
    st.subheader("Résultats de la création :")
    success_count = sum(1 for r in creation_results if "✅" in r)
    error_count = sum(1 for r in creation_results if "❌" in r)
    
    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.metric("✅ Créés avec succès", success_count)
    with col_res2:
        st.metric("❌ Erreurs", error_count)
    
    # Détails
    st.markdown("**Détails des créations :**")
    for result in creation_results:
        if "✅" in result:
            st.success(result)
        else:
            st.error(result)
    
    if success_count > 0:
        st.success(f"🎉 {success_count} élève(s) créé(s) avec succès dans SAMBA!")
        # Rafraîchir les données
        if st.button("🔄 Actualiser la comparaison"):
            st.rerun()