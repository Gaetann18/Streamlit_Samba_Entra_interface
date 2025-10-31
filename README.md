# 🎓 Streamlit SAMBA Entra Sync

[English](#english) | [Français](#français)

---

## English

Streamlit application for managing and synchronizing user accounts between SAMBA, Microsoft Entra ID (Azure AD), and IMFR database.

### 📋 Table of Contents

- [Screenshots](#screenshots)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Technologies](#technologies)
- [Security](#security)

### 📸 Screenshots

<details>


screenshots available in the [screenshots](screenshots/) folder

</details>

### ✨ Features

#### 👥 User Management

- **SAMBA User Creation**: Interface to create user accounts individually
- **CSV Bulk Import**: Batch account creation from CSV file
- **Password Modification**: Change passwords for existing users
- **User Deletion**: Individual or bulk deletion (Eleves group)
- **Group Management**: SAMBA group assignment and management

#### 🔄 Synchronization

- **IMFR/SAMBA Sync**:
  - Automatic student retrieval from IMFR via web scraping
  - Automatic user loading from MySQL
  - IMFR vs SAMBA comparison
  - Automatic creation of missing accounts
  - Selective student exclusion during creation
  - MySQL storage (`utilisateurs` table)

#### 🕷️ Data Retrieval

- **IMFR Scraping**: Automatic student list retrieval from IMFR portal
- **SAMBA Synchronization**: MySQL table update from SAMBA via SSH (samba-tool)

#### 🔧 Tools

- **Class Mapping Table**: Automatic class name mapping
- **Microsoft 365 Licenses**: View available licenses in Entra ID
- **Entra ID Groups**: List and verify Azure AD groups
- **System Diagnostics**: Kerberos/SAMBA diagnostic tools
- **Connection Tests**: Configuration validation

### 🔧 Prerequisites

#### Required Software

- Python 3.8+
- MySQL/MariaDB
- SAMBA Server (SSH access)
- Chrome/Chromium (for Selenium)
- ChromeDriver (compatible with your Chrome version)

#### External Services

- **IMFR**: Account with access to training management portal
- **Microsoft Entra ID**: Azure AD application with permissions:
  - `User.ReadWrite.All`
  - `Group.ReadWrite.All`
  - `Directory.ReadWrite.All`
  - `Organization.Read.All`

### 📦 Installation

#### 1. Clone the repository

```bash
git clone git@github.com:Gaetann18/Streamlit_Samba_Entra_interface.git
cd Streamlit_Samba_Entra_interface
```

#### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

#### 3. Install dependencies

```bash
pip install -r requirements.txt
```

#### 4. MySQL Database Setup

```sql
-- Create database
CREATE DATABASE Streamlit CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user
CREATE USER 'streamlit_user'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON Streamlit.* TO 'streamlit_user'@'%';
FLUSH PRIVILEGES;

-- Create tables
USE Streamlit;

-- Users table
CREATE TABLE utilisateurs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Login VARCHAR(50) UNIQUE,
    Nom VARCHAR(50),
    Prénom VARCHAR(50),
    Mot_de_passe VARCHAR(50),
    Classe VARCHAR(50),
    Groupe VARCHAR(50),
    Dernière_modification VARCHAR(50),
    ID_Unique VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_login (Login)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- IMFR students table
CREATE TABLE eleves_imfr (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    classe VARCHAR(50),
    date_import TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_nom_prenom (nom, prenom),
    INDEX idx_classe (classe)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### ⚙️ Configuration

#### 1. Copy configuration file

```bash
cp config.py.example config.py
```

#### 2. Edit config.py

Fill in the information in `config.py`:

**MySQL Database**

```python
MYSQL_CONFIG = {
    'host': 'your-mysql-server',
    'user': 'streamlit_user',
    'password': 'your_password',
    'database': 'Streamlit',
    'charset': 'utf8mb4',
    'port': 3306
}
```

**SAMBA Server**

```python
SAMBA_SERVER = "your-samba-server"
SAMBA_USER = "your_username"
SAMBA_PWD = "your_password"
```

**IMFR**

```python
IMFR_CONFIG = {
    "url": "https://your-imfr.fr",
    "username": "your_login",
    "password": "your_password",
    # ... other parameters
}
```

**Microsoft Entra ID**

```python
CLIENT_ID = "your-client-id"
CLIENT_SECRET = "your-client-secret"
TENANT_ID = "your-tenant-id"
```

### 🚀 Usage

#### Launch the application

```bash
streamlit run app.py --server.port 8502 --server.address 0.0.0.0
```

#### Access the interface

Open a browser and navigate to:
- http://localhost:8502 (local)
- http://your-server:8502 (remote)

#### Authentication

The application offers 3 access levels:
- **Trainer**: Access via URL `/formateur` (no password)
- **Secretariat**: Access via URL `/secretariat` (no password)
- **Administrator**: Access via password (configured in `config.py`)

### 📁 Project Structure

```
.
├── app.py                          # Main entry point
├── config.py.example               # Configuration template
├── requirements.txt                # Python dependencies
├── README.md                       # Documentation
│
├── apps/                           # Application modules
│   ├── auth_system.py             # Authentication system
│   ├── sync_ad_samba.py           # SAMBA user management
│   ├── recuperation_eleves.py     # IMFR scraping
│   ├── mots_de_passe.py           # Password management
│   ├── selenium_scraper.py        # Scraping engine
│   ├── run_sync.py                # Sync script
│   └── gestion_utilisateurs/      # Modular user management
│       ├── modules/               # Core functions
│       └── tabs/                  # UI tabs
```

### 🛠️ Technologies

**Backend**
- Python 3.8+, Streamlit, PyMySQL, Paramiko (SSH), Selenium, MSAL, pandas

**Frontend**
- Streamlit reactive interface

**Infrastructure**
- MySQL/MariaDB, SAMBA, Microsoft Entra ID

### 🔐 Security

**Best Practices**
1. Never commit config.py (contains sensitive information)
2. Use strong passwords for MySQL, SAMBA, and admin
3. Limit permissions: Azure AD app with minimal permissions
4. Regular backups of database and configuration
5. Use HTTPS in production with reverse proxy (nginx/apache)

### 📄 License

This project is licensed under the MIT License.

### 👨‍💻 Author

**Gaëtan Paviot**
- GitHub: [@Gaetann18](https://github.com/Gaetann18)

### 🙏 Acknowledgments

- [Streamlit](https://streamlit.io/) for the framework
- [SAMBA](https://www.samba.org/) for Active Directory integration
- [Microsoft](https://microsoft.com/) for Entra ID
- [@sfonteneau](https://github.com/tranquilit) for [AzureADConnect_Samba4](https://github.com/tranquilit/AzureADConnect_Samba4) which this project is based on

---

## Français

Application Streamlit pour la gestion et la synchronisation des comptes utilisateurs entre SAMBA, Microsoft Entra ID (Azure AD) et la base de données IMFR.

### 📋 Table des matières

- [Captures d'écran](#captures-décran)
- [Fonctionnalités](#fonctionnalités)
- [Prérequis](#prérequis)
- [Installation](#installation-1)
- [Configuration](#configuration-1)
- [Utilisation](#utilisation-1)
- [Structure du projet](#structure-du-projet)
- [Technologies utilisées](#technologies-utilisées)
- [Sécurité](#sécurité)

### 📸 Captures d'écran

<details>

Captures d'écran disponibles dans le dossier [screenshots](screenshots/)

</details>

### ✨ Fonctionnalités

#### 👥 Gestion des utilisateurs

- **Création d'utilisateurs SAMBA** : Interface pour créer des comptes utilisateurs individuellement
- **Import CSV en masse** : Création de comptes en batch depuis un fichier CSV
- **Modification de mots de passe** : Changement de mot de passe pour les utilisateurs existants
- **Suppression d'utilisateurs** : Suppression individuelle ou en masse (groupe Eleves)
- **Gestion des groupes** : Attribution et gestion des groupes SAMBA

#### 🔄 Synchronisation

- **Sync IMFR/SAMBA** :
  - Récupération automatique des élèves depuis IMFR via web scraping
  - Chargement automatique des utilisateurs depuis MySQL
  - Comparaison IMFR vs SAMBA
  - Création automatique des comptes manquants
  - Exclusion sélective d'élèves lors de la création
  - Sauvegarde dans MySQL (table `utilisateurs`)

#### 🕷️ Récupération des données

- **Scraping IMFR** : Récupération automatique de la liste des élèves depuis le portail IMFR
- **Synchronisation SAMBA** : Mise à jour de la table MySQL depuis SAMBA via SSH (samba-tool)

#### 🔧 Outils

- **Tableau de correspondance des classes** : Mapping automatique des noms de classes
- **Licences Microsoft 365** : Consultation des licences disponibles dans Entra ID
- **Groupes Entra ID** : Liste et vérification des groupes Azure AD
- **Diagnostics système** : Outils de diagnostic Kerberos/SAMBA
- **Tests de connexion** : Validation de la configuration

### 🔧 Prérequis

#### Logiciels requis

- Python 3.8+
- MySQL/MariaDB
- Serveur SAMBA (accès SSH)
- Chrome/Chromium (pour Selenium)
- ChromeDriver (compatible avec votre version de Chrome)

#### Services externes

- **IMFR** : Compte avec accès au portail de gestion des formations
- **Microsoft Entra ID** : Application Azure AD avec les permissions :
  - `User.ReadWrite.All`
  - `Group.ReadWrite.All`
  - `Directory.ReadWrite.All`
  - `Organization.Read.All`

### 📦 Installation

#### 1. Cloner le repository

```bash
git clone git@github.com:Gaetann18/Streamlit_Samba_Entra_interface.git
cd Streamlit_Samba_Entra_interface
```

#### 2. Créer un environnement virtuel

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

#### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

#### 4. Configuration de la base de données MySQL

```sql
-- Créer la base de données
CREATE DATABASE Streamlit CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Créer l'utilisateur
CREATE USER 'streamlit_user'@'%' IDENTIFIED BY 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON Streamlit.* TO 'streamlit_user'@'%';
FLUSH PRIVILEGES;

-- Créer les tables
USE Streamlit;

-- Table des utilisateurs
CREATE TABLE utilisateurs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Login VARCHAR(50) UNIQUE,
    Nom VARCHAR(50),
    Prénom VARCHAR(50),
    Mot_de_passe VARCHAR(50),
    Classe VARCHAR(50),
    Groupe VARCHAR(50),
    Dernière_modification VARCHAR(50),
    ID_Unique VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_login (Login)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table des élèves IMFR
CREATE TABLE eleves_imfr (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    classe VARCHAR(50),
    date_import TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_nom_prenom (nom, prenom),
    INDEX idx_classe (classe)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### ⚙️ Configuration

#### 1. Copier le fichier de configuration

```bash
cp config.py.example config.py
```

#### 2. Éditer config.py

Remplir les informations dans `config.py` :

**Base de données MySQL**

```python
MYSQL_CONFIG = {
    'host': 'votre-serveur-mysql',
    'user': 'streamlit_user',
    'password': 'votre_mot_de_passe',
    'database': 'Streamlit',
    'charset': 'utf8mb4',
    'port': 3306
}
```

**Serveur SAMBA**

```python
SAMBA_SERVER = "votre-serveur-samba"
SAMBA_USER = "votre_utilisateur"
SAMBA_PWD = "votre_mot_de_passe"
```

**IMFR**

```python
IMFR_CONFIG = {
    "url": "https://votre-imfr.fr",
    "username": "votre_login",
    "password": "votre_mot_de_passe",
    # ... autres paramètres
}
```

**Microsoft Entra ID**

```python
CLIENT_ID = "votre-client-id"
CLIENT_SECRET = "votre-client-secret"
TENANT_ID = "votre-tenant-id"
```

### 🚀 Utilisation

#### Lancement de l'application

```bash
streamlit run app.py --server.port 8502 --server.address 0.0.0.0
```

#### Accès à l'interface

Ouvrir un navigateur et accéder à :
- http://localhost:8502 (local)
- http://votre-serveur:8502 (distant)

#### Authentification

L'application propose 3 niveaux d'accès :
- **Formateur** : Accès via URL `/formateur` (pas de mot de passe)
- **Secrétariat** : Accès via URL `/secretariat` (pas de mot de passe)
- **Administrateur** : Accès via mot de passe (configuré dans `config.py`)

### 📁 Structure du projet

```
.
├── app.py                          # Point d'entrée principal
├── config.py.example               # Template de configuration
├── requirements.txt                # Dépendances Python
├── README.md                       # Documentation
│
├── apps/                           # Modules d'application
│   ├── auth_system.py             # Système d'authentification
│   ├── sync_ad_samba.py           # Gestion utilisateurs SAMBA
│   ├── recuperation_eleves.py     # Scraping IMFR
│   ├── mots_de_passe.py           # Gestion des mots de passe
│   ├── selenium_scraper.py        # Moteur de scraping
│   ├── run_sync.py                # Script de synchronisation
│   └── gestion_utilisateurs/      # Gestion utilisateurs modulaire
│       ├── modules/               # Fonctions principales
│       └── tabs/                  # Onglets d'interface
```

### 🛠️ Technologies utilisées

**Backend**
- Python 3.8+, Streamlit, PyMySQL, Paramiko (SSH), Selenium, MSAL, pandas

**Frontend**
- Interface Streamlit réactive

**Infrastructure**
- MySQL/MariaDB, SAMBA, Microsoft Entra ID

### 🔐 Sécurité

**Bonnes pratiques**
1. Ne jamais commiter config.py (contient des informations sensibles)
2. Utiliser des mots de passe forts pour MySQL, SAMBA, et l'admin
3. Limiter les permissions : Application Azure AD avec permissions minimales
4. Sauvegarder régulièrement la base de données et la configuration
5. Utiliser HTTPS en production avec reverse proxy (nginx/apache)

### 📄 Licence

Ce projet est sous licence MIT.

### 👨‍💻 Auteur

**Gaëtan Paviot**
- GitHub: [@Gaetann18](https://github.com/Gaetann18)

### 🙏 Remerciements

- [Streamlit](https://streamlit.io/) pour le framework
- [SAMBA](https://www.samba.org/) pour l'intégration Active Directory
- [Microsoft](https://microsoft.com/) pour Entra ID
- [@sfonteneau](https://github.com/tranquilit) pour [AzureADConnect_Samba4](https://github.com/tranquilit/AzureADConnect_Samba4) sur lequel ce projet s'est appuyé

---

**Note** : Cette application est conçue pour un usage interne dans un établissement de formation. Adapter la configuration selon vos besoins spécifiques.

**Note**: This application is designed for internal use in a training institution. Adapt the configuration to your specific needs.
