"""
Module pour l'onglet Groupes
"""
import streamlit as st
import pandas as pd
import sys
import os

# Ajouter les chemins nécessaires
sys.path.append('/home/streamlit')
sys.path.append('/home/streamlit/apps')
sys.path.append('/home/streamlit/apps/gestion_utilisateurs')

from modules.utils import get_existing_users
from modules.samba_functions import add_students_to_wifi_group_by_description


def render_groupes_tab():
    """Affiche l'onglet de gestion des groupes"""
    st.header("Gestion des groupes")
    
    # Section Gestion du groupe WIFI
    st.subheader("📶 Gestion du groupe WIFI")
    st.markdown("**Ajoutez automatiquement des élèves au groupe WIFI selon leur classe/description**")
    
    # Interface pour sélectionner les descriptions
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Descriptions à rechercher :**")
        descriptions_input = st.text_area(
            "Entrez les descriptions (une par ligne)",
            value="TBAC\nBTS\nTFP",
            height=100,
            help="Entrez les mots-clés à rechercher dans les classes (ex: TBAC, BTS, TFP, etc.)"
        )
        
        # Nom du groupe cible
        target_group = st.text_input(
            "Nom du groupe cible",
            value="WIFI",
            help="Le groupe Samba où ajouter les élèves"
        )
    
    with col2:
        # Aperçu des utilisateurs qui correspondent
        if descriptions_input:
            descriptions_list = [desc.strip() for desc in descriptions_input.split('\n') if desc.strip()]
            
            if descriptions_list:
                st.markdown("**Aperçu des utilisateurs correspondants :**")
                
                # Récupérer les utilisateurs pour l'aperçu
                try:
                    df_users = get_existing_users()
                    if not df_users.empty and 'Classe' in df_users.columns:
                        matching_preview = []
                        for _, user in df_users.iterrows():
                            user_classe = str(user['Classe']).strip().upper()
                            for desc in descriptions_list:
                                if desc.upper() in user_classe:
                                    matching_preview.append({
                                        "Login": user['Login'],
                                        "Nom": user.get('Nom', 'N/A'),
                                        "Prénom": user.get('Prénom', 'N/A'),
                                        "Classe": user['Classe']
                                    })
                                    break
                        
                        if matching_preview:
                            df_preview = pd.DataFrame(matching_preview)
                            st.dataframe(df_preview, hide_index=True, use_container_width=True)
                            st.info(f"🔍 {len(matching_preview)} utilisateurs trouvés")
                        else:
                            st.warning("Aucun utilisateur trouvé avec ces descriptions")
                    else:
                        st.warning("Aucun utilisateur dans la base de données")
                except Exception as e:
                    st.error(f"Erreur lors de l'aperçu : {e}")
    
    # Bouton d'exécution
    if st.button("📶 Ajouter au groupe WIFI", type="primary"):
        if descriptions_input and target_group:
            descriptions_list = [desc.strip() for desc in descriptions_input.split('\n') if desc.strip()]
            
            if descriptions_list:
                with st.spinner(f"Ajout des utilisateurs au groupe {target_group}..."):
                    results, added_count = add_students_to_wifi_group_by_description(descriptions_list, target_group)
                
                # Affichage des résultats
                if results:
                    col_res1, col_res2 = st.columns(2)
                    with col_res1:
                        st.metric("✅ Ajoutés avec succès", added_count)
                    with col_res2:
                        total_processed = len(results)
                        st.metric("📊 Total traité", total_processed)
                    
                    # Détail des résultats
                    st.markdown("**Détails des opérations :**")
                    for result in results:
                        if "✅" in result:
                            st.success(result)
                        elif "ℹ️" in result:
                            st.info(result)
                        else:
                            st.error(result)
                    
                    if added_count > 0:
                        st.success(f"🎉 {added_count} utilisateur(s) ajouté(s) au groupe {target_group} avec succès!")
                    else:
                        st.info("Aucun nouvel utilisateur ajouté (tous déjà membres ou erreurs)")
                else:
                    st.warning("Aucun résultat retourné")
            else:
                st.error("Veuillez saisir au moins une description")
        else:
            st.error("Veuillez remplir tous les champs requis")