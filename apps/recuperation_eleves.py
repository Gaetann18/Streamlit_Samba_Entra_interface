import streamlit as st
import pandas as pd
import time
import json
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import pymysql

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import config

def login_to_site(config_data):
    """Fonction de connexion au site"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    driver.get(config_data["url"])
    time.sleep(2)

    username_field = driver.find_element(By.NAME, "login")  
    password_field = driver.find_element(By.NAME, "pwd")
    username_field.send_keys(config_data["username"])
    password_field.send_keys(config_data["password"])
    password_field.send_keys(Keys.RETURN)
    time.sleep(2)

    return driver

def switch_to_new_tab(driver):
    """Fonction pour passer à un nouvel onglet ouvert"""
    original_window = driver.current_window_handle
    all_windows = driver.window_handles
    
    for window in all_windows:
        if window != original_window:
            driver.switch_to.window(window)
            break

def navigate_to_section(driver):
    """Naviguer vers la section des impressions et exports"""
    try:
        impressions_export_menu = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "dropdownMenuButton_15"))
        )
        actions = ActionChains(driver)
        actions.move_to_element(impressions_export_menu).perform()
        pdf_excel_fusion_link = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.LINK_TEXT, "PDF, Excel, Fusion Word"))
        )
        pdf_excel_fusion_link.click()
        switch_to_new_tab(driver)
        st.write("✅ Navigation vers PDF, Excel, Fusion Word réussie")
        
    except Exception as e:
        st.error(f"Erreur lors de la navigation vers la section : {e}")
        raise

def extraire_donnees_eleves(driver):
    """Extrait nom, prénom et classe de tous les élèves"""
    eleves_data = []
    
    try:
        st.write("🔄 Extraction des données des élèves en cours...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tr[id*='checkbox_']"))
        )
        all_rows = driver.find_elements(By.CSS_SELECTOR, "tr")
        st.write(f"📊 {len(all_rows)} lignes trouvées")
        
        classe_actuelle = ""
        
        for i, row in enumerate(all_rows, 1):
            try:
                classe_elements = row.find_elements(By.CSS_SELECTOR, "td[colspan].fusion_bold.fusion_rouge")
                
                if classe_elements:
                    for elem in classe_elements:
                        text = elem.text.strip()
                        if text:
                            classe_text = text.replace('\xa0', ' ').strip()
                            if classe_text and len(classe_text) < 30:
                                classe_actuelle = classe_text
                                break
                    continue
                
                json_elements = row.find_elements(By.CSS_SELECTOR, "input[id*='json_eleve']")
                
                for json_element in json_elements:
                    json_value = json_element.get_attribute("value")
                    
                    if json_value:
                        data = json.loads(json_value)
                        
                        eleve_info = {
                            'nom': data.get('nom', ''),
                            'prenom': data.get('prenom', ''),
                            'classe': classe_actuelle
                        }
                        
                        eleves_data.append(eleve_info)
                        
            except json.JSONDecodeError:
                continue
            except Exception:
                continue
    
    except Exception as e:
        st.write(f"⚠️ Erreur principale lors de l'extraction : {e}")
        st.write("🔄 Tentative avec méthode alternative...")
        try:
            eleves_data = extraire_depuis_structure_alternative(driver)
        except Exception as e2:
            st.error(f"Erreur méthode alternative : {e2}")
    
    st.write(f"✅ Extraction terminée : {len(eleves_data)} élèves trouvés")
    return eleves_data

def extraire_depuis_structure_alternative(driver):
    """Méthode alternative pour extraire nom, prénom et classe"""
    eleves_data = []
    
    try:
        st.write("🔄 Méthode alternative : recherche par colspan et spans")
        all_rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
        
        classe_actuelle = ""
        
        for row in all_rows:
            try:
                classe_cells = row.find_elements(By.CSS_SELECTOR, "td[colspan].fusion_bold.fusion_rouge")
                
                if classe_cells:
                    for cell in classe_cells:
                        classe_text = cell.text.strip()
                        if classe_text:
                            classe_clean = classe_text.replace('\xa0', ' ').strip()
                            if classe_clean and len(classe_clean) < 30:
                                classe_actuelle = classe_clean
                                break
                    continue
                
                spans_email = row.find_elements(By.CSS_SELECTOR, "span[title*='email']")
                
                for span in spans_email:
                    texte_complet = span.text.strip()
                    
                    if texte_complet:
                        parties = texte_complet.split()
                        if len(parties) >= 2:
                            nom = parties[0]
                            prenom = " ".join(parties[1:])
                            
                            eleve_info = {
                                'nom': nom,
                                'prenom': prenom,
                                'classe': classe_actuelle
                            }
                            
                            eleves_data.append(eleve_info)
                            
            except Exception:
                continue
                
    except Exception as e:
        st.error(f"Erreur dans la méthode alternative : {e}")
    
    return eleves_data

def go_to_excel_et_fusion(driver):
    """Naviguer vers la section Excel et fusion et extraire les données"""
    try:
        st.write("🔍 Recherche de la section Excel et fusion...")
        excel_fusion = driver.find_element(By.CSS_SELECTOR, "#TD_dossier_13 > div")
        excel_fusion.click()
        time.sleep(1)
        st.write("✅ Clic sur Excel et fusion réussi")
        
        st.write("🔍 Recherche de 'Liste des élèves'...")
        liste_des_eleves = driver.find_element(By.CSS_SELECTOR, "#nom_impression_pere_43")
        liste_des_eleves.click()
        time.sleep(1)
        st.write("✅ Clic sur Liste des élèves réussi")
        
        st.write("🔍 Configuration du filtre formation...")
        select_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "fusion_filtre_formation"))
        )
        select_formation = Select(select_element)
        select_formation.select_by_value("TOUS_FORMATIONS")
        st.write("✅ Sélection 'Tous par classes' effectuée")
        time.sleep(3)
        
        eleves_data = extraire_donnees_eleves(driver)
        
        if eleves_data:
            # Statistiques
            classes = set(eleve['classe'] for eleve in eleves_data if eleve['classe'])
            st.write(f"📊 **STATISTIQUES:**")
            st.write(f"   • Total élèves: {len(eleves_data)}")
            st.write(f"   • Nombre de classes: {len(classes)}")
            if classes:
                st.write(f"   • Classes: {', '.join(sorted(classes))}")
            
            return eleves_data
        else:
            st.warning("Aucune donnée d'élève extraite")
            return []
        
    except Exception as e:
        st.error(f"Erreur lors de la navigation : {e}")
        import traceback
        st.error(f"Traceback: {traceback.format_exc()}")
        return []

def recuperer_eleves():
    """Récupère la liste d'élèves via Selenium"""
    scraping_config = config.SCRAPING_CONFIG
    
    try:
        st.write("🔄 Connexion au site...")
        driver = login_to_site(scraping_config)
        st.write("✅ Connexion réussie")
        
        st.write("🔄 Navigation vers la section...")
        navigate_to_section(driver)
        time.sleep(2)
        
        st.write("🔄 Extraction des données...")
        eleves_data_raw = go_to_excel_et_fusion(driver)
        
        driver.quit()
        st.write("✅ Navigateur fermé")
        
        if eleves_data_raw:
            # Sauvegarder dans la base de données MySQL
            try:
                st.write("💾 Sauvegarde dans la base de données MySQL...")
                conn = pymysql.connect(**config.MYSQL_CONFIG)
                cursor = conn.cursor()

                # Créer la table si elle n'existe pas
                create_table_query = """
                CREATE TABLE IF NOT EXISTS eleves_imfr (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nom VARCHAR(100) NOT NULL,
                    prenom VARCHAR(100) NOT NULL,
                    classe VARCHAR(50),
                    date_import TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_nom_prenom (nom, prenom),
                    INDEX idx_classe (classe)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
                cursor.execute(create_table_query)

                # Vider la table avant d'insérer les nouvelles données
                cursor.execute("TRUNCATE TABLE eleves_imfr")
                st.write("   🗑️ Table vidée")

                # Insérer les nouvelles données
                insert_query = """
                INSERT INTO eleves_imfr (nom, prenom, classe)
                VALUES (%s, %s, %s)
                """

                count_inserted = 0
                for eleve in eleves_data_raw:
                    cursor.execute(insert_query, (
                        eleve['nom'],
                        eleve['prenom'],
                        eleve['classe']
                    ))
                    count_inserted += 1

                conn.commit()
                cursor.close()
                conn.close()

                st.success(f"✅ {count_inserted} élèves sauvegardés dans MySQL (table: eleves_imfr)")

                # Également sauvegarder en JSON comme backup
                json_file_path = "/home/streamlit/data/eleves.json"
                os.makedirs(os.path.dirname(json_file_path), exist_ok=True)

                eleves_json = []
                for eleve in eleves_data_raw:
                    eleves_json.append({
                        "prenom": eleve['prenom'],
                        "nom": eleve['nom'],
                        "classe": eleve['classe']
                    })

                with open(json_file_path, 'w', encoding='utf-8') as f:
                    json.dump(eleves_json, f, ensure_ascii=False, indent=2)

                st.write(f"💾 Backup JSON: {json_file_path}")

            except Exception as e:
                st.error(f"❌ Erreur lors de la sauvegarde MySQL: {e}")
                import traceback
                st.error(f"Traceback: {traceback.format_exc()}")

            # Créer DataFrame pour affichage
            df = pd.DataFrame({
                'Prénom': [eleve['prenom'] for eleve in eleves_data_raw],
                'Nom': [eleve['nom'] for eleve in eleves_data_raw],
                'Classe': [eleve['classe'] for eleve in eleves_data_raw]
            })
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Erreur lors de la récupération : {e}")
        import traceback
        st.error(f"Traceback complet : {traceback.format_exc()}")
        return pd.DataFrame()

def ensure_table_exists():
    """Crée la table eleves_imfr si elle n'existe pas"""
    try:
        conn = pymysql.connect(**config.MYSQL_CONFIG)
        cursor = conn.cursor()

        create_table_query = """
        CREATE TABLE IF NOT EXISTS eleves_imfr (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nom VARCHAR(100) NOT NULL,
            prenom VARCHAR(100) NOT NULL,
            classe VARCHAR(50),
            date_import TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_nom_prenom (nom, prenom),
            INDEX idx_classe (classe)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        cursor.execute(create_table_query)
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"❌ Erreur lors de la création de la table: {e}")
        return False

@st.cache_data(ttl=60)
def get_eleves_from_db():
    """Récupère les élèves depuis la base de données MySQL"""
    try:
        # S'assurer que la table existe
        ensure_table_exists()

        conn = pymysql.connect(**config.MYSQL_CONFIG)
        query = """
        SELECT
            id,
            nom as 'Nom',
            prenom as 'Prénom',
            classe as 'Classe',
            date_import as 'Date Import'
        FROM eleves_imfr
        ORDER BY classe, nom, prenom
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except pymysql.Error as e:
        if "doesn't exist" in str(e):
            return pd.DataFrame()  # Table n'existe pas encore
        else:
            st.error(f"❌ Erreur de connexion à la base de données: {e}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erreur lors de la récupération depuis la DB: {e}")
        return pd.DataFrame()

def run():
    st.title("📋 Récupération Liste des Élèves")

    st.markdown("""
    Cette application récupère automatiquement la liste des élèves depuis IMFR
    et la sauvegarde dans la base de données MySQL.
    """)

    # Afficher les données actuelles en base
    st.subheader("📊 Données actuelles en base de données")

    df_db = get_eleves_from_db()

    if not df_db.empty:
        # Statistiques
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total élèves", len(df_db))
        with col2:
            nb_classes = df_db['Classe'].nunique() if 'Classe' in df_db.columns else 0
            st.metric("Nombre de classes", nb_classes)
        with col3:
            if 'Date Import' in df_db.columns and len(df_db) > 0:
                derniere_maj = df_db['Date Import'].max()
                st.metric("Dernière mise à jour", derniere_maj.strftime("%d/%m/%Y %H:%M") if pd.notna(derniere_maj) else "N/A")
            else:
                st.metric("Dernière mise à jour", "N/A")

        # Filtres
        st.markdown("---")
        col_filter1, col_filter2 = st.columns(2)

        with col_filter1:
            # Filtre par classe
            if 'Classe' in df_db.columns:
                classes = ['Toutes'] + sorted(df_db['Classe'].unique().tolist())
                classe_selectionnee = st.selectbox("Filtrer par classe", classes)

        with col_filter2:
            # Recherche
            recherche = st.text_input("Rechercher (nom ou prénom)", "")

        # Appliquer les filtres
        df_filtered = df_db.copy()

        if 'Classe' in df_db.columns and classe_selectionnee != 'Toutes':
            df_filtered = df_filtered[df_filtered['Classe'] == classe_selectionnee]

        if recherche:
            mask = (
                df_filtered['Nom'].str.contains(recherche, case=False, na=False) |
                df_filtered['Prénom'].str.contains(recherche, case=False, na=False)
            )
            df_filtered = df_filtered[mask]

        # Affichage
        st.dataframe(
            df_filtered.drop(columns=['id'] if 'id' in df_filtered.columns else []),
            use_container_width=True,
            hide_index=True
        )

        st.info(f"📋 Affichage de {len(df_filtered)} élève(s) sur {len(df_db)} total")

    else:
        st.info("ℹ️ Aucune donnée en base. Cliquez sur 'Actualiser la liste' pour récupérer les élèves depuis IMFR.")

    # Bouton de récupération
    st.markdown("---")
    st.subheader("🔄 Récupération depuis IMFR")

    st.warning("⚠️ Cette opération va remplacer toutes les données actuelles en base de données.")

    if st.button("🔄 Actualiser la liste depuis IMFR", type="primary"):
        with st.spinner("Récupération en cours depuis IMFR..."):
            df_eleves = recuperer_eleves()

        if not df_eleves.empty:
            st.success(f"🎉 {len(df_eleves)} élèves récupérés avec succès !")
            st.balloons()
            # Forcer le rechargement des données
            st.cache_data.clear()
            st.rerun()
        else:
            st.error("⚠️ Aucun élève trouvé ou erreur lors de la récupération")

    # Section d'aide
    with st.expander("ℹ️ Aide et informations"):
        st.markdown("""
        ### Comment utiliser cette application ?

        1. **Consulter les données** : Les élèves déjà récupérés sont affichés automatiquement
        2. **Filtrer** : Utilisez les filtres pour trouver une classe ou un élève spécifique
        3. **Actualiser** : Cliquez sur "Actualiser la liste" pour récupérer les données à jour depuis IMFR

        ### Où sont stockées les données ?

        - **Base de données MySQL** : Table `eleves_imfr` (configurée dans config.py)
        - **Backup JSON** : Fichier local de sauvegarde

        ### Fréquence de mise à jour

        Les données ne sont pas mises à jour automatiquement. Vous devez cliquer sur "Actualiser"
        pour récupérer les dernières informations depuis IMFR.

        ### Structure de la table

        ```sql
        CREATE TABLE eleves_imfr (
            id INT PRIMARY KEY AUTO_INCREMENT,
            nom VARCHAR(100),
            prenom VARCHAR(100),
            classe VARCHAR(50),
            date_import TIMESTAMP
        )
        ```
        """)

if __name__ == "__main__":
    run()