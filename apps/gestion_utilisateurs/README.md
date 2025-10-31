# Gestion des Utilisateurs - Structure Modulaire

## 📁 Structure du projet

```
gestion_utilisateurs/
├── __init__.py
├── README.md
├── modules/                    # Modules utilitaires
│   ├── __init__.py
│   ├── utils.py               # Fonctions utilitaires communes
│   ├── samba_functions.py     # Fonctions spécifiques à SAMBA
│   └── imfr_functions.py      # Fonctions spécifiques à IMFR
└── tabs/                       # Modules des onglets
    ├── __init__.py
    ├── groupes.py             # Onglet gestion des groupes
    └── sync_imfr_samba.py     # Onglet synchronisation IMFR/SAMBA
```

## 📋 Description des modules

### `modules/utils.py`
Fonctions utilitaires communes :
- `generate_username()` - Génération de noms d'utilisateur
- `generate_password()` - Génération de mots de passe
- `normalize_class_name()` - Normalisation des noms de classe
- `get_existing_users()` - Récupération des utilisateurs Excel
- `save_user_to_excel()` - Sauvegarde dans Excel
- `ssh_connection()` - Context manager SSH
- `execute_ssh_command()` - Exécution de commandes SSH

### `modules/samba_functions.py`
Fonctions spécifiques à SAMBA :
- `get_samba_group_members()` - Liste les membres d'un groupe
- `add_students_to_wifi_group_by_description()` - Ajout au groupe WIFI
- `create_samba_user()` - Création d'utilisateur SAMBA
- `delete_samba_user()` - Suppression d'utilisateur
- `reset_samba_password()` - Reset mot de passe

### `modules/imfr_functions.py`
Fonctions spécifiques à IMFR :
- `get_imfr_students()` - Récupération des élèves IMFR
- `compare_imfr_samba()` - Comparaison IMFR vs SAMBA
- `validate_imfr_data()` - Validation des données IMFR

### `tabs/groupes.py`
Interface de gestion des groupes :
- `render_groupes_tab()` - Affichage de l'onglet
- Gestion du groupe WIFI par description

### `tabs/sync_imfr_samba.py`
Interface de synchronisation IMFR/SAMBA :
- `render_sync_imfr_samba_tab()` - Affichage de l'onglet
- Configuration IMFR
- Comparaison et synchronisation
- Création des utilisateurs manquants

## 🔧 Utilisation

L'application principale `sync_ad_samba.py` importe et utilise ces modules modulaires.

### Exemple d'import :

```python
from modules.utils import generate_username, get_existing_users
from modules.samba_functions import create_samba_user
from modules.imfr_functions import get_imfr_students
from tabs.sync_imfr_samba import render_sync_imfr_samba_tab
```

## ✅ Avantages de cette structure

1. **Maintenabilité** - Code organisé et facile à maintenir
2. **Réutilisabilité** - Fonctions réutilisables entre modules
3. **Lisibilité** - Séparation claire des responsabilités
4. **Extensibilité** - Facilité d'ajout de nouveaux modules/onglets
5. **Tests** - Tests unitaires plus faciles à implémenter

## 🔄 Migration

Le fichier original `sync_ad_samba.py` a été sauvegardé dans `sync_ad_samba_backup.py` et remplacé par la version modulaire.