def run():
    import streamlit as st
    import pandas as pd
    import numpy as np
    import pymysql
    import sys
    import os

    # Importer la configuration depuis config.py
    sys.path.insert(0, '/home/streamlit')
    from config import MYSQL_CONFIG

    # Configuration - Utiliser MySQL au lieu d'Excel
    USE_MYSQL = True
    PASSWORD_EXCEL_FILE = "mots_de_passe_utilisateurs.xlsx"  # Gardé pour compatibilité
    
    def get_username_column(df):
        """Détecte la colonne username/login dans le DataFrame"""
        for col in ['Login', 'Username', 'login', 'username']:
            if col in df.columns:
                return col
        return None

    # ========================= Fonctions de gestion Excel =========================
    def init_password_excel():
        """Initialise le fichier Excel des mots de passe s'il n'existe pas"""
        if not os.path.exists(PASSWORD_EXCEL_FILE):
            wb = Workbook()
            ws = wb.active
            ws.title = "Mots de passe"
            
            # En-têtes - Utiliser 'Login' pour correspondre avec sync_ad_samba.py
            headers = ["Login", "Prénom", "Nom", "Mot de passe", "Classe", "Groupe", "Date création", "ID Unique"]
            for col, header in enumerate(headers, 1):
                ws.cell(row=1, column=col, value=header)
            
            # Style des en-têtes
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            
            for cell in ws[1]:
                cell.font = header_font
                cell.fill = header_fill
                
            # Ajuster la largeur des colonnes
            column_widths = [15, 15, 15, 20, 12, 12, 20, 12]
            for i, width in enumerate(column_widths, 1):
                ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = width
                
            wb.save(PASSWORD_EXCEL_FILE)
            return True
        return False

    @st.cache_data(ttl=60)
    def get_all_users_from_mysql():
        """Récupère tous les utilisateurs depuis MySQL"""
        try:
            conn = pymysql.connect(**MYSQL_CONFIG)
            query = """
            SELECT
                Login,
                Prénom,
                Nom,
                Mot_de_passe as 'Mot de passe',
                Classe,
                Groupe,
                Dernière_modification as 'Date création',
                ID_Unique as 'ID Unique'
            FROM utilisateurs
            ORDER BY Nom, Prénom
            """
            df = pd.read_sql(query, conn)
            conn.close()

            # Remplacer les NaN par des chaînes vides pour éviter les erreurs
            df = df.fillna('')
            return df
        except Exception as e:
            st.error(f"❌ Erreur de connexion à la base de données MySQL: {e}")
            return pd.DataFrame()

    def get_all_users_excel():
        """Récupère tous les utilisateurs - avec support MySQL"""
        if USE_MYSQL:
            return get_all_users_from_mysql()
        else:
            # Ancienne méthode Excel (gardée comme fallback)
            if not os.path.exists(PASSWORD_EXCEL_FILE):
                init_password_excel()
                return pd.DataFrame()

            try:
                df = pd.read_excel(PASSWORD_EXCEL_FILE)
                # Remplacer les NaN par des chaînes vides pour éviter les erreurs
                df = df.fillna('')
                return df
            except Exception as e:
                st.error(f"Erreur lors de la lecture du fichier Excel: {e}")
                return pd.DataFrame()

    def search_user_password(search_term):
        """Recherche un utilisateur et son mot de passe"""
        df = get_all_users_excel()
        if df.empty:
            return []
        
        # Détecter la colonne username/login disponible
        username_col = None
        for col in ['Username', 'Login', 'username', 'login']:
            if col in df.columns:
                username_col = col
                break
        
        if not username_col:
            st.error("❌ Colonne username/login non trouvée dans le fichier Excel")
            return []
            
        # Recherche dans username/login, prénom, nom
        mask = df[username_col].str.contains(search_term, case=False, na=False)
        
        # Ajouter recherche dans prénom/nom si les colonnes existent
        if 'Prénom' in df.columns:
            mask = mask | df['Prénom'].str.contains(search_term, case=False, na=False)
        if 'Nom' in df.columns:
            mask = mask | df['Nom'].str.contains(search_term, case=False, na=False)
        
        return df[mask].to_dict('records')

    def delete_user_from_excel(username):
        """Supprime un utilisateur du fichier Excel"""
        if not os.path.exists(PASSWORD_EXCEL_FILE):
            return False
            
        df = get_all_users_excel()
        if df.empty:
            return False
        
        username_col = get_username_column(df)
        if not username_col:
            return False
            
        # Filtrer pour supprimer l'utilisateur
        df_filtered = df[df[username_col] != username]
        
        if len(df_filtered) < len(df):
            # Réécrire le fichier Excel
            wb = Workbook()
            ws = wb.active
            ws.title = "Mots de passe"
            
            # En-têtes
            headers = list(df.columns)
            for col, header in enumerate(headers, 1):
                ws.cell(row=1, column=col, value=header)
            
            # Style des en-têtes
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            
            for cell in ws[1]:
                cell.font = header_font
                cell.fill = header_fill
            
            # Données
            for row_idx, (_, row) in enumerate(df_filtered.iterrows(), 2):
                for col_idx, value in enumerate(row, 1):
                    ws.cell(row=row_idx, column=col_idx, value=value)
            
            # Ajuster la largeur des colonnes
            column_widths = [15, 15, 15, 20, 12, 12, 20, 12]
            for i, width in enumerate(column_widths, 1):
                if i <= len(headers):
                    ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = width
            
            wb.save(PASSWORD_EXCEL_FILE)
            return True
        return False

    def update_user_password(username, new_password):
        """Met à jour le mot de passe d'un utilisateur"""
        if not os.path.exists(PASSWORD_EXCEL_FILE):
            return False
            
        wb = openpyxl.load_workbook(PASSWORD_EXCEL_FILE)
        ws = wb.active
        
        # Trouver l'utilisateur et mettre à jour son mot de passe
        # Colonne 1 est soit Login soit Username selon le fichier
        for row in range(2, ws.max_row + 1):
            if ws.cell(row=row, column=1).value == username:  # Colonne Login/Username
                ws.cell(row=row, column=4, value=new_password)  # Colonne Mot de passe
                wb.save(PASSWORD_EXCEL_FILE)
                return True
        return False

    # ========================= Interface Streamlit =========================
    st.title("🔐 Gestion des Mots de Passe Utilisateurs")

    # Afficher la source des données
    if USE_MYSQL:
        st.info("🗄️ Données chargées depuis MySQL", icon="ℹ️")
    else:
        # Initialiser le fichier Excel si nécessaire (seulement si on n'utilise pas MySQL)
        if init_password_excel():
            st.success("📁 Fichier Excel des mots de passe initialisé")

    # Onglets
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Recherche", "📊 Liste complète", "✏️ Modification", "📊 Statistiques"])
    
    # ========================= Onglet Recherche =========================
    with tab1:
        st.header("Recherche Rapide")
        
        search_term = st.text_input(
            "Rechercher un utilisateur (nom, prénom ou username):", 
            placeholder="Ex: martin, dupont, mdupont, dup...",
            key="search_input"
        )
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🔍 Rechercher", type="primary"):
                if search_term:
                    results = search_user_password(search_term)
                    if results:
                        st.success(f"✅ {len(results)} utilisateur(s) trouvé(s):")
                        
                        for user in results:
                            # Détecter la colonne username/login
                            username_key = 'Login' if 'Login' in user else 'Username' if 'Username' in user else 'login'
                            username_value = user.get(username_key, 'N/A')
                            
                            with st.expander(f"{username_value} - {user['Prénom']} {user['Nom']}", expanded=True):
                                # Informations utilisateur sans colonnes imbriquées
                                st.write(f"**Login INFO & WIFI:** `{username_value}`")                                
                                st.write(f"**Compte O365:** {username_value} @xxx-xxx")
                                st.write(f"**Nom complet:** {user['Prénom']} {user['Nom']}")
                                st.write(f"**Classe:** {user['Classe']} | **Groupe:** {user['Groupe']}")
                                if 'Date création' in user and pd.notna(user['Date création']) and user['Date création'] != '':
                                    st.write(f"**Créé le:** {user['Date création']}")
                                st.write(f"**ID:** {user['ID Unique']}")
                                
                                # Mot de passe en évidence
                                st.markdown("### Mot de passe:")
                                st.code(user['Mot de passe'], language="text")
                                        
                    else:
                        st.warning("❌ Aucun utilisateur trouvé")
                        st.info("💡 Essayez avec une partie du nom, prénom ou username")
                else:
                    st.error("⚠️ Veuillez saisir un terme de recherche")
        
        with col2:
            st.info("**💡 Astuces de recherche:**\n- Tapez juste une partie du nom\n- La recherche ignore les majuscules\n- Ex: 'dup' trouve 'Dupont'")

    # ========================= Onglet Liste complète =========================
    with tab2:
        st.header("Liste Complète des Utilisateurs")
        st.info("Utilisez les filtres différents filtres pour affiner la classe", icon="ℹ️")
        
        df_users = get_all_users_excel()
        
        if not df_users.empty:
            # Filtres
            col_filter1, col_filter2, col_filter3 = st.columns(3)
            
            with col_filter1:
                # Nettoyer les valeurs vides pour les groupes
                groupe_options = []
                if 'Groupe' in df_users.columns:
                    groupe_options = [g for g in df_users['Groupe'].unique() if g != '']
                
                selected_groups = st.multiselect(
                    "Filtrer par groupe:",
                    options=groupe_options,
                    default=groupe_options
                )
            
            with col_filter2:
                # Nettoyer les valeurs vides pour les classes
                classe_options = []
                if 'Classe' in df_users.columns:
                    classe_options = sorted([c for c in df_users['Classe'].unique() if c != ''])
                
                selected_classes = st.multiselect(
                    "Filtrer par classe:",
                    options=classe_options,
                    default=None
                )
            
            with col_filter3:
                show_passwords = st.checkbox("🔓 Afficher les mots de passe", value=False)
            
            # Appliquer les filtres
            df_filtered = df_users.copy()
            if selected_groups:
                # Filtrer en tenant compte des valeurs vides
                df_filtered = df_filtered[df_filtered['Groupe'].isin(selected_groups) & (df_filtered['Groupe'] != '')]
            if selected_classes:
                # Filtrer en tenant compte des valeurs vides
                df_filtered = df_filtered[df_filtered['Classe'].isin(selected_classes) & (df_filtered['Classe'] != '')]
            
            # Masquer/Afficher les mots de passe
            if not show_passwords and 'Mot de passe' in df_filtered.columns:
                df_display = df_filtered.copy()
                df_display['Mot de passe'] = '••••••••'
            else:
                df_display = df_filtered.copy()
            
            st.write(f"**📋 {len(df_filtered)} utilisateur(s) affiché(s) sur {len(df_users)} total**")
            
            # Affichage du tableau
            st.dataframe(
                df_display, 
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Login": st.column_config.TextColumn("Login", width="medium"),
                    "Username": st.column_config.TextColumn("Username", width="medium"),  # Au cas où
                    "Prénom": st.column_config.TextColumn("Prénom", width="medium"),
                    "Nom": st.column_config.TextColumn("Nom", width="medium"),
                    "Mot de passe": st.column_config.TextColumn("Mot de passe", width="large"),
                    "Classe": st.column_config.TextColumn("Classe", width="small"),
                    "Groupe": st.column_config.TextColumn("Groupe", width="medium"),
                    "Date création": st.column_config.DatetimeColumn("Créé le", width="medium"),
                    "ID Unique": st.column_config.TextColumn("ID", width="small")
                }
            )
            
            # Boutons d'export
            col_export1, col_export2 = st.columns(2)
            
            with col_export1:
                csv_data = df_filtered.to_csv(index=False)
                st.download_button(
                    label="Télécharger CSV",
                    data=csv_data,
                    file_name=f"utilisateurs_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    type="primary"
                )
            
            with col_export2:
                # Export Excel (création d'un buffer temporaire)
                import io
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_filtered.to_excel(writer, index=False, sheet_name='Utilisateurs')
                excel_data = output.getvalue()
                    
                st.download_button(
                    label="Télécharger Excel",
                    data=excel_data,
                    file_name=f"utilisateurs_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
        else:
            st.info("📭 Aucun utilisateur dans la base de données")
            st.markdown("👉 Créez des utilisateurs depuis l'onglet principal")

    # ========================= Onglet Modification =========================
    with tab3:
        st.header("✏️ Modification des Utilisateurs")
        st.info("Fonction en cours de développement...")
        """
        df_users = get_all_users_excel()
        
        if not df_users.empty:
            username_col = get_username_column(df_users)
            if not username_col:
                st.error("❌ Colonne username/login non trouvée")
                return
                
            # Sélection d'utilisateur
            user_list = [f"{row[username_col]} - {row['Prénom']} {row['Nom']}" for _, row in df_users.iterrows()]
            selected_user_display = st.selectbox("Choisir un utilisateur à modifier:", [""] + user_list)
            
            if selected_user_display:
                username = selected_user_display.split(" - ")[0]
                user_data = df_users[df_users[username_col] == username].iloc[0]
                
                st.subheader(f"👤 Modification de {user_data['Prénom']} {user_data['Nom']}")
                
                # Affichage des infos actuelles
                st.write("**📋 Informations actuelles:**")
                st.write(f"• Login: `{user_data[username_col]}`")
                st.write(f"• Classe: {user_data['Classe']} | • Groupe: {user_data['Groupe']}")
                
                st.write("**🔑 Mot de passe actuel:**")
                st.code(user_data['Mot de passe'])
                
                # Modification du mot de passe
                st.markdown("---")
                new_password = st.text_input("🔑 Nouveau mot de passe:", type="password", key="new_pwd")
                
                # Actions sans colonnes imbriquées
                if st.button("💾 Modifier le mot de passe", type="primary"):
                    if new_password:
                        if update_user_password(username, new_password):
                            st.success("✅ Mot de passe modifié avec succès!")
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de la modification")
                    else:
                        st.error("⚠️ Veuillez saisir un nouveau mot de passe")
                
                st.markdown("---")
                
                if st.button("🗑️ Supprimer l'utilisateur", type="secondary"):
                    if st.session_state.get('confirm_delete', False):
                        if delete_user_from_excel(username):
                            st.success("✅ Utilisateur supprimé!")
                            st.session_state['confirm_delete'] = False
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de la suppression")
                    else:
                        st.session_state['confirm_delete'] = True
                        st.warning("⚠️ Cliquez à nouveau pour confirmer la suppression")
        else:
            st.info("📭 Aucun utilisateur à modifier")
"""
    # ========================= Onglet Statistiques =========================
    with tab4:
        st.header("Statistiques")
        
        df_users = get_all_users_excel()
        
        if not df_users.empty:
            # Métriques générales
            col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
            
            with col_metric1:
                st.metric("Total utilisateurs", len(df_users))
            
            with col_metric2:
                if 'Groupe' in df_users.columns:
                    unique_groups = len([g for g in df_users['Groupe'].unique() if g != ''])
                    st.metric("Groupes", unique_groups)
            
            with col_metric3:
                if 'Classe' in df_users.columns:
                    unique_classes = len([c for c in df_users['Classe'].unique() if c != ''])
                    st.metric("Classes", unique_classes)
                    
            with col_metric4:
                if 'Date création' in df_users.columns:
                    recent_users = len(df_users[pd.to_datetime(df_users['Date création']) > pd.Timestamp.now() - pd.Timedelta(days=7)])
                    st.metric("Cette semaine", recent_users)
            
            # Graphiques
            col_chart1, col_chart2 = st.columns(2)
            
            with col_chart1:
                if 'Groupe' in df_users.columns:
                    st.subheader("Répartition par groupe")
                    group_counts = df_users[df_users['Groupe'] != '']['Groupe'].value_counts()
                    if not group_counts.empty:
                        st.bar_chart(group_counts)
                    else:
                        st.info("Aucune donnée de groupe à afficher")
            
            with col_chart2:
                if 'Classe' in df_users.columns:
                    st.subheader("Répartition par classe")
                    class_counts = df_users[df_users['Classe'] != '']['Classe'].value_counts()
                    if not class_counts.empty:
                        st.bar_chart(class_counts)
                    else:
                        st.info("Aucune donnée de classe à afficher")
            
    # Footer
    st.markdown("---")
 