"""
Module des fonctions IMFR pour la récupération des élèves
"""
import pandas as pd
import sys
import os
import logging

# Ajouter le chemin parent pour importer config et les modules
sys.path.append('/home/streamlit')
sys.path.append('/home/streamlit/apps')
import config

# Import des utilitaires locaux
from .utils import logger


def get_imfr_students(config_dict=None):
    """Récupère la liste des élèves depuis IMFR en utilisant selenium_scraper"""
    try:
        # Import de la classe EleveScraper
        from selenium_scraper import EleveScraper
        
        # Utiliser la configuration fournie ou celle par défaut
        if config_dict is None:
            if hasattr(config, 'IMFR_CONFIG'):
                config_dict = config.IMFR_CONFIG
            else:
                raise Exception("Configuration IMFR non trouvée. Veuillez fournir les paramètres de connexion.")
        
        # Initialiser le scraper
        scraper = EleveScraper(headless=True)
        
        # Effectuer le scraping complet
        eleves_data = scraper.scrape_eleves_complete(config_dict)
        
        # Fermer le driver
        if scraper.driver:
            scraper.driver.quit()
        
        # Convertir en DataFrame
        if eleves_data:
            df_eleves = pd.DataFrame(eleves_data)
            
            # Normaliser les colonnes pour correspondre au format attendu
            if 'Nom_Complet' in df_eleves.columns and 'Nom' not in df_eleves.columns:
                # Essayer de séparer nom et prénom depuis Nom_Complet
                def split_nom_prenom(nom_complet):
                    parts = str(nom_complet).strip().split()
                    if len(parts) >= 2:
                        nom = parts[0].upper()
                        prenom = " ".join(parts[1:]).title()
                    else:
                        nom = str(nom_complet).upper()
                        prenom = ""
                    return pd.Series([nom, prenom])
                
                df_eleves[['Nom', 'Prénom']] = df_eleves['Nom_Complet'].apply(split_nom_prenom)
            
            # Assurer que les colonnes nécessaires existent
            required_columns = ['Nom', 'Prénom', 'Classe']
            for col in required_columns:
                if col not in df_eleves.columns:
                    df_eleves[col] = 'Non défini'
            
            # Nettoyer les données
            df_eleves['Nom'] = df_eleves['Nom'].astype(str).str.strip().str.upper()
            df_eleves['Prénom'] = df_eleves['Prénom'].astype(str).str.strip().str.title()
            df_eleves['Classe'] = df_eleves['Classe'].astype(str).str.strip()
            
            # Supprimer les lignes vides
            df_eleves = df_eleves[
                (df_eleves['Nom'] != '') & 
                (df_eleves['Nom'] != 'NAN') & 
                (df_eleves['Nom'].notna())
            ].copy()
            
            logger.info(f"IMFR: {len(df_eleves)} élèves récupérés avec succès")
            return df_eleves
        else:
            logger.warning("IMFR: Aucune donnée récupérée")
            return pd.DataFrame(columns=['Nom', 'Prénom', 'Classe'])
            
    except ImportError:
        raise Exception("Module selenium_scraper non trouvé. Veuillez vérifier l'installation.")
    except Exception as e:
        logger.error(f"Erreur lors de la récupération IMFR: {e}")
        raise Exception(f"Erreur lors de la récupération des données IMFR: {str(e)}")


def compare_imfr_samba(df_imfr, df_samba):
    """Compare les données IMFR et SAMBA et retourne les différences"""
    missing_in_samba = []
    extra_in_samba = []
    
    # Trouver les élèves manquants dans SAMBA
    for _, imfr_student in df_imfr.iterrows():
        imfr_nom = str(imfr_student['Nom']).strip().upper()
        imfr_prenom = str(imfr_student['Prénom']).strip().title()
        
        # Chercher dans SAMBA
        found = False
        for _, samba_student in df_samba.iterrows():
            samba_nom = str(samba_student.get('Nom', '')).strip().upper()
            samba_prenom = str(samba_student.get('Prénom', '')).strip().title()
            
            if imfr_nom == samba_nom and imfr_prenom == samba_prenom:
                found = True
                break
        
        if not found:
            missing_in_samba.append(imfr_student)
    
    # Trouver les élèves en plus dans SAMBA
    for _, samba_student in df_samba.iterrows():
        samba_nom = str(samba_student.get('Nom', '')).strip().upper()
        samba_prenom = str(samba_student.get('Prénom', '')).strip().title()
        
        # Chercher dans IMFR
        found = False
        for _, imfr_student in df_imfr.iterrows():
            imfr_nom = str(imfr_student['Nom']).strip().upper()
            imfr_prenom = str(imfr_student['Prénom']).strip().title()
            
            if samba_nom == imfr_nom and samba_prenom == imfr_prenom:
                found = True
                break
        
        if not found:
            extra_in_samba.append(samba_student)
    
    return missing_in_samba, extra_in_samba


def validate_imfr_data(df_imfr):
    """Valide les données IMFR récupérées"""
    if df_imfr.empty:
        return False, "Aucune donnée IMFR trouvée"
    
    required_columns = ['Nom', 'Prénom', 'Classe']
    missing_columns = [col for col in required_columns if col not in df_imfr.columns]
    
    if missing_columns:
        return False, f"Colonnes manquantes: {missing_columns}"
    
    # Vérifier qu'il y a des données valides
    valid_rows = df_imfr[
        (df_imfr['Nom'].notna()) & 
        (df_imfr['Nom'] != '') & 
        (df_imfr['Prénom'].notna()) & 
        (df_imfr['Prénom'] != '')
    ]
    
    if valid_rows.empty:
        return False, "Aucune ligne de données valide trouvée"
    
    return True, f"Données IMFR valides: {len(valid_rows)} élèves"