import time
import json
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

class EleveScraper:
    """
    Classe pour récupérer des listes d'élèves depuis des sites web
    Basée sur le code Selenium fourni et étendue pour Streamlit
    """
    
    def __init__(self, headless=True):
        self.driver = None
        self.headless = headless
        
    def setup_driver(self):
        """Configure et initialise le driver Chrome"""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        # Installation automatique du ChromeDriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        return self.driver

    def load_config(self, config_dict=None, config_file="config.json"):
        """
        Charger les informations de connexion depuis un dictionnaire ou fichier JSON
        """
        if config_dict:
            return config_dict
        
        try:
            with open(config_file, "r") as file:
                config = json.load(file)
            return config
        except FileNotFoundError:
            raise FileNotFoundError(f"Fichier de configuration {config_file} non trouvé")

    def login_to_site(self, config):
        """
        Fonction de connexion au site basée sur le code fourni
        """
        if not self.driver:
            self.setup_driver()
        
        # Accéder à l'URL
        self.driver.get(config["url"])
        time.sleep(config.get("wait_time", 2))
        
        # Détecter le type de sélecteur
        login_selector = config["login_selector"]
        password_selector = config["password_selector"]
        
        # Trouver les éléments du formulaire de connexion
        username_field = self._find_element_by_selector(login_selector)
        password_field = self._find_element_by_selector(password_selector)
        
        if not username_field or not password_field:
            raise Exception("Impossible de trouver les champs de connexion")
        
        # Remplir les informations de connexion
        username_field.clear()
        username_field.send_keys(config["username"])
        
        password_field.clear()
        password_field.send_keys(config["password"])
        
        # Soumettre le formulaire
        password_field.send_keys(Keys.RETURN)
        
        # Attendre que la page se charge après la connexion
        time.sleep(config.get("wait_time", 2))
        
        return True

    def _find_element_by_selector(self, selector):
        """
        Trouve un élément par différents types de sélecteurs
        """
        try:
            # Essayer par nom
            if not selector.startswith(('#', '.')):
                return self.driver.find_element(By.NAME, selector)
            # Essayer par ID
            elif selector.startswith('#'):
                return self.driver.find_element(By.ID, selector[1:])
            # Essayer par classe
            elif selector.startswith('.'):
                return self.driver.find_element(By.CLASS_NAME, selector[1:])
            # Sélecteur CSS général
            else:
                return self.driver.find_element(By.CSS_SELECTOR, selector)
        except:
            # Fallback: essayer comme sélecteur CSS
            try:
                return self.driver.find_element(By.CSS_SELECTOR, selector)
            except:
                return None

    def navigate_to_eleves_page(self, navigation_url=None):
        """
        Naviguer vers la page des élèves si une URL spécifique est fournie
        """
        if navigation_url:
            self.driver.get(navigation_url)
            time.sleep(2)
            
    def navigate_to_pdf_excel_module(self, config):
        """
        Navigation spécifique vers le module PDF/Excel de CFA MFEO
        """
        try:
            # Étape 1: Chercher l'icône imprimante
            print_icon_selector = config.get("print_icon_selector", "i.fas.fa-print")
            
            # Attendre que la page soit chargée
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, print_icon_selector))
            )
            
            # Chercher le lien "PDF, Excel, Fusion Word"
            pdf_excel_selector = config.get("pdf_excel_link_selector", "a[href*='imfr_module_publispostage_et_excel.php']")
            
            pdf_excel_link = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, pdf_excel_selector))
            )
            
            # Cliquer sur le lien (ouvre dans un nouvel onglet)
            pdf_excel_link.click()
            
            # Attendre un peu pour que le nouvel onglet s'ouvre
            time.sleep(2)
            
            # Passer au nouvel onglet
            self.switch_to_new_tab()
            
            return True
            
        except Exception as e:
            raise Exception(f"Erreur lors de la navigation vers le module PDF/Excel: {str(e)}")
            
    def find_carnet_adresse_links(self):
        """
        Trouve tous les liens de type 'carnet d'adresse' sur la page du module
        """
        try:
            # Chercher tous les liens contenant 'num_carnet_adresse'
            carnet_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='num_carnet_adresse=']")
            
            links_info = []
            for link in carnet_links:
                href = link.get_attribute('href')
                text = link.text.strip()
                
                # Extraire le numéro de carnet d'adresse
                import re
                match = re.search(r'num_carnet_adresse=(\d+)', href)
                carnet_num = match.group(1) if match else 'inconnu'
                
                links_info.append({
                    'url': href,
                    'text': text,
                    'carnet_num': carnet_num
                })
            
            return links_info
            
        except Exception as e:
            raise Exception(f"Erreur lors de la recherche des carnets d'adresse: {str(e)}")
            
    def extract_excel_data_from_module(self):
        """
        Extrait les données Excel depuis la page du module publispostage
        """
        try:
            # Chercher s'il y a un bouton/lien d'export Excel
            excel_buttons = [
                "a[href*='.xlsx']",
                "a[href*='.xls']", 
                "button[onclick*='excel']",
                "input[value*='Excel']",
                ".btn-excel",
                "[data-export='excel']"
            ]
            
            for selector in excel_buttons:
                try:
                    excel_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    return {
                        'type': 'excel_export',
                        'element': excel_element,
                        'selector': selector
                    }
                except:
                    continue
            
            # Si pas de bouton Excel, chercher des données tabulaires
            tables = self.driver.find_elements(By.CSS_SELECTOR, "table")
            if tables:
                return {
                    'type': 'table_data',
                    'tables': tables,
                    'count': len(tables)
                }
            
            # Chercher des listes d'élèves
            student_lists = [
                ".student", ".eleve", ".etudiant",
                "tr td:contains('nom')", "tr td:contains('prénom')",
                "ul li", "ol li"
            ]
            
            for selector in student_lists:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        return {
                            'type': 'student_list',
                            'elements': elements,
                            'selector': selector,
                            'count': len(elements)
                        }
                except:
                    continue
                    
            return {'type': 'no_data_found'}
            
        except Exception as e:
            raise Exception(f"Erreur lors de l'extraction des données Excel: {str(e)}")

    def switch_to_new_tab(self):
        """
        Fonction pour passer à un nouvel onglet ouvert (basée sur le code fourni)
        """
        # Récupérer tous les onglets ouverts
        original_window = self.driver.current_window_handle
        all_windows = self.driver.window_handles
        
        # Passer au nouvel onglet
        for window in all_windows:
            if window != original_window:
                self.driver.switch_to.window(window)
                break

    def extract_eleves_data(self, classe_selector, eleve_selector, wait_time=3):
        """
        Extrait les données des élèves selon les sélecteurs fournis
        """
        eleves_data = []
        
        try:
            # Attendre que les éléments se chargent
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, eleve_selector))
            )
            
            # Récupérer les classes si sélecteur fourni
            classes = []
            if classe_selector:
                try:
                    classe_elements = self.driver.find_elements(By.CSS_SELECTOR, classe_selector)
                    classes = [elem.text.strip() for elem in classe_elements if elem.text.strip()]
                except:
                    classes = ["Classe non définie"]
            
            # Récupérer les élèves
            eleve_elements = self.driver.find_elements(By.CSS_SELECTOR, eleve_selector)
            
            for idx, elem in enumerate(eleve_elements):
                eleve_text = elem.text.strip()
                if eleve_text:
                    # Tentative de parsing nom/prénom (basique)
                    parts = eleve_text.split()
                    if len(parts) >= 2:
                        nom = parts[0].upper()
                        prenom = " ".join(parts[1:]).title()
                    else:
                        nom = eleve_text.upper()
                        prenom = ""
                    
                    # Assigner une classe (cyclique si plusieurs)
                    classe = classes[idx % len(classes)] if classes else "Non définie"
                    
                    eleves_data.append({
                        'Nom': nom,
                        'Prénom': prenom,
                        'Classe': classe,
                        'Nom_Complet': eleve_text,
                        'Index': idx + 1
                    })
            
            return eleves_data
            
        except Exception as e:
            raise Exception(f"Erreur lors de l'extraction des données: {str(e)}")

    def scrape_eleves_complete(self, config):
        """
        Processus complet de scraping des élèves avec navigation CFA MFEO
        """
        try:
            # Étape 1: Connexion
            self.login_to_site(config)
            
            # Étape 2: Navigation spécifique CFA MFEO vers module PDF/Excel
            self.navigate_to_pdf_excel_module(config)
            
            # Étape 3: Trouver les carnets d'adresse disponibles
            carnet_links = self.find_carnet_adresse_links()
            
            # Étape 4: Extraction des données
            if carnet_links:
                # Prendre le premier carnet d'adresse trouvé
                first_carnet = carnet_links[0]
                self.driver.get(first_carnet['url'])
                time.sleep(config.get("wait_time", 3))
                
                # Extraire les données depuis cette page
                excel_data = self.extract_excel_data_from_module()
                
                if excel_data['type'] == 'table_data':
                    # Extraire depuis les tableaux
                    eleves_data = self.extract_students_from_tables(excel_data['tables'])
                elif excel_data['type'] == 'student_list':
                    # Extraire depuis les listes
                    eleves_data = self.extract_students_from_list(excel_data['elements'])
                else:
                    # Utilisation des sélecteurs par défaut
                    eleves_data = self.extract_eleves_data(
                        config.get("classe_selector", ""),
                        config.get("eleve_selector", "td"),
                        config.get("wait_time", 3)
                    )
                
                # Ajouter les informations de carnet
                for eleve in eleves_data:
                    eleve['Carnet_Adresse'] = first_carnet['carnet_num']
                    eleve['Source'] = first_carnet['text']
                
                return eleves_data
            else:
                # Fallback sur méthode classique
                eleves_data = self.extract_eleves_data(
                    config.get("classe_selector", ""),
                    config.get("eleve_selector", "td"),
                    config.get("wait_time", 3)
                )
                return eleves_data
            
        except Exception as e:
            raise Exception(f"Erreur lors du scraping CFA MFEO: {str(e)}")
        
        finally:
            self.close_driver()
            
    def extract_students_from_tables(self, tables):
        """
        Extrait les données d'élèves depuis des tableaux HTML
        """
        eleves_data = []
        
        for table_idx, table in enumerate(tables):
            try:
                # Récupérer les lignes du tableau
                rows = table.find_elements(By.CSS_SELECTOR, "tr")
                
                # Identifier les en-têtes (première ligne généralement)
                headers = []
                if rows:
                    header_cells = rows[0].find_elements(By.CSS_SELECTOR, "th, td")
                    headers = [cell.text.strip().lower() for cell in header_cells]
                
                # Traiter les lignes de données
                for row_idx, row in enumerate(rows[1:], 1):  # Skip header
                    cells = row.find_elements(By.CSS_SELECTOR, "td")
                    if cells and len(cells) >= 2:
                        row_data = [cell.text.strip() for cell in cells]
                        
                        # Tentative de mapping intelligent
                        eleve_info = {
                            'Table_Index': table_idx,
                            'Row_Index': row_idx
                        }
                        
                        # Mapping basique par position ou header
                        if len(row_data) >= 2:
                            if 'nom' in headers and 'prénom' in headers:
                                nom_idx = headers.index('nom') if 'nom' in headers else 0
                                prenom_idx = headers.index('prénom') if 'prénom' in headers else 1
                                eleve_info['Nom'] = row_data[nom_idx] if nom_idx < len(row_data) else row_data[0]
                                eleve_info['Prénom'] = row_data[prenom_idx] if prenom_idx < len(row_data) else row_data[1]
                            else:
                                eleve_info['Nom'] = row_data[0]
                                eleve_info['Prénom'] = row_data[1] if len(row_data) > 1 else ""
                        
                        # Ajouter les autres colonnes
                        for idx, data in enumerate(row_data):
                            if idx < len(headers):
                                eleve_info[headers[idx].title()] = data
                            else:
                                eleve_info[f'Colonne_{idx+1}'] = data
                        
                        eleves_data.append(eleve_info)
                        
            except Exception as e:
                continue  # Ignorer les erreurs de tableau individuel
        
        return eleves_data
        
    def extract_students_from_list(self, elements):
        """
        Extrait les données d'élèves depuis une liste d'éléments
        """
        eleves_data = []
        
        for idx, element in enumerate(elements):
            try:
                text_content = element.text.strip()
                if text_content:
                    # Tentative de parsing nom/prénom
                    parts = text_content.split()
                    if len(parts) >= 2:
                        nom = parts[0].upper()
                        prenom = " ".join(parts[1:]).title()
                    else:
                        nom = text_content.upper()
                        prenom = ""
                    
                    eleves_data.append({
                        'Nom': nom,
                        'Prénom': prenom,
                        'Texte_Complet': text_content,
                        'Element_Index': idx + 1
                    })
                    
            except Exception as e:
                continue
        
        return eleves_data

    def extract_table_data(self, table_selector="table", wait_time=3):
        """
        Extrait les données d'un tableau HTML
        """
        try:
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, table_selector))
            )
            
            table = self.driver.find_element(By.CSS_SELECTOR, table_selector)
            
            # Récupérer les en-têtes
            headers = []
            try:
                header_elements = table.find_elements(By.CSS_SELECTOR, "thead th")
                if not header_elements:
                    header_elements = table.find_elements(By.CSS_SELECTOR, "tr:first-child th")
                if not header_elements:
                    header_elements = table.find_elements(By.CSS_SELECTOR, "tr:first-child td")
                
                headers = [elem.text.strip() for elem in header_elements]
            except:
                headers = [f"Colonne_{i+1}" for i in range(10)]  # Headers par défaut
            
            # Récupérer les lignes de données
            rows_data = []
            try:
                rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")
                if not rows:
                    rows = table.find_elements(By.CSS_SELECTOR, "tr")[1:]  # Exclure l'en-tête
                
                for row in rows:
                    cells = row.find_elements(By.CSS_SELECTOR, "td")
                    if cells:
                        row_data = [cell.text.strip() for cell in cells]
                        rows_data.append(row_data)
            except:
                pass
            
            return headers, rows_data
            
        except Exception as e:
            raise Exception(f"Erreur lors de l'extraction du tableau: {str(e)}")

    def save_config(self, config, filename="scraper_config.json"):
        """
        Sauvegarde la configuration dans un fichier JSON
        """
        with open(filename, "w") as file:
            json.dump(config, file, indent=4)

    def close_driver(self):
        """
        Ferme le driver Chrome
        """
        if self.driver:
            self.driver.quit()
            self.driver = None

    def get_page_source(self):
        """
        Retourne le code source de la page actuelle
        """
        if self.driver:
            return self.driver.page_source
        return None

    def take_screenshot(self, filename="screenshot.png"):
        """
        Prend une capture d'écran de la page actuelle
        """
        if self.driver:
            return self.driver.save_screenshot(filename)
        return False

    def wait_for_element(self, selector, timeout=10):
        """
        Attend qu'un élément apparaisse sur la page
        """
        if self.driver:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                return element
            except:
                return None
        return None


# Fonction utilitaire pour créer un DataFrame pandas depuis les données scrappées
def create_eleves_dataframe(eleves_data, additional_columns=None):
    """
    Crée un DataFrame pandas depuis les données d'élèves
    """
    if not eleves_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(eleves_data)
    
    # Ajouter des colonnes supplémentaires si spécifiées
    if additional_columns:
        for col, default_value in additional_columns.items():
            df[col] = default_value
    
    return df


# Fonction utilitaire pour valider les sélecteurs
def validate_selectors(driver, selectors_dict):
    """
    Valide que les sélecteurs trouvent des éléments sur la page
    """
    results = {}
    
    for name, selector in selectors_dict.items():
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            results[name] = {
                "found": len(elements) > 0,
                "count": len(elements),
                "first_text": elements[0].text[:50] if elements else ""
            }
        except:
            results[name] = {
                "found": False,
                "count": 0,
                "first_text": ""
            }
    
    return results


# Configuration exemple
EXAMPLE_CONFIG = {
    "url": "https://exemple.com/login",
    "username": "votre_identifiant", 
    "password": "votre_mot_de_passe",
    "login_selector": "login",  # ou "#login-field" ou ".login-input"
    "password_selector": "pwd",  # ou "#password" ou ".password-field"
    "classe_selector": ".classe-item",  # Sélecteur pour les classes
    "eleve_selector": ".eleve-nom",     # Sélecteur pour les noms d'élèves
    "navigation_url": None,  # URL optionnelle pour naviguer vers la page des élèves
    "wait_time": 3  # Temps d'attente en secondes
}


if __name__ == "__main__":
    # Exemple d'utilisation
    scraper = EleveScraper(headless=True)
    
    try:
        # Charger la configuration
        config = EXAMPLE_CONFIG
        
        # Scraper les élèves
        eleves = scraper.scrape_eleves_complete(config)
        
        # Créer un DataFrame
        df = create_eleves_dataframe(eleves)
        
        print(f"Récupération de {len(eleves)} élèves:")
        print(df.head())
        
    except Exception as e:
        print(f"Erreur: {e}")