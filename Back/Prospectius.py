# Prospectius.py (Le Main)
import asyncio
import logging
from typing import Dict, Any, Optional, Tuple

# --- Importation des Services ---
try:
    from Back.dbManager import initialize_db_pool, close_db_pool
    from Back.Account.accountService import authenticate_account, create_account, get_all_accounts, update_account_info, \
    update_account_password, delete_account, get_account_by_id
    from Back.Prospect.prospectService import create_prospect, get_prospects_list, get_prospect_by_id, update_prospect, \
        delete_prospect
    from Back.Interaction.interactionService import (create_interaction, get_interactions_by_prospect)
    #from  import get_prospect_status_distribution, get_conversion_rate
    #from export_service import export_prospects_to_excel
except ImportError as e:
    print(f"Erreur d'importation. Assurez-vous que les fichiers de services sont dans le chemin correct: {e}")
    exit()

# Configuration du Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ProspectiusApp")

# Variable pour stocker l'utilisateur connecté
CURRENT_USER: Optional[Dict[str, Any]] = None


# ----------------------------------------------
#              FONCTIONS UTILITAIRES
# ----------------------------------------------

async def collect_db_params() -> Tuple[str, int, str, str, str]:
    """Collecte les paramètres de la DB via l'entrée utilisateur."""
    print("\n--- Configuration de la Base de Données ---")
    host = input("Hôte de la base de données (localhost): ") or "localhost"
    port_str = input("Port de la base de données (3306): ")
    port = int(port_str) if port_str and port_str.isdigit() else 3306
    user = input("Nom d'utilisateur MySQL: ")
    password = input("Mot de passe MySQL: ")
    database = input("Nom de la base de données (Prospectius): ") or 'Prospectius'
    return host, port, user, password, database


def display_user_menu():
    """Affiche le menu principal de l'application."""
    if not CURRENT_USER: return

    print("\n" + "=" * 60)
    print(
        f" BIENVENUE DANS PROSPECTIUS | Utilisateur: {CURRENT_USER['username']} | Rôle: {CURRENT_USER['type_compte']}")
    print("=" * 60)
    print("1. Gestion des Prospects")
    print("2. Reporting & Export")

    if CURRENT_USER['type_compte'] == 'Administrateur':
        print("3. Gestion des Comptes Utilisateurs (Admin)")
    else:
        # Option 3 désactivée ou non affichée pour les non-administrateurs
        pass

    print("9. Déconnexion")
    print("0. Quitter l'Application")
    print("-" * 60)


# ----------------------------------------------
#             LOGIQUE D'AUTHENTIFICATION & COMPTES
# ----------------------------------------------

async def handle_login():
    """Gère l'écran de connexion initial."""
    global CURRENT_USER
    print("\n--- ÉCRAN DE CONNEXION ---")
    username = input("Nom d'utilisateur: ")
    password = input("Mot de passe: ")

    result = await authenticate_account(username, password)

    if result.get("authenticated"):
        CURRENT_USER = result
        CURRENT_USER['username'] = username
        print(f"\n✅ Connexion réussie. Bienvenue, {username}!")
        return True
    else:
        print(f"\n❌ Échec de la connexion: {result.get('message', 'Nom d\'utilisateur ou mot de passe incorrect.')}")
        return False


async def display_account_management_menu():
    """Menu pour la gestion des comptes (Administrateurs uniquement)."""
    if CURRENT_USER['type_compte'] != 'Administrateur':
        print("\nAccès refusé. Réservé aux administrateurs.")
        return

    while True:
        print("\n--- GESTION DES COMPTES (ADMIN) ---")
        print("1. Lister tous les comptes")
        print("2. Créer un nouveau compte")
        print("3. Modifier un compte existant")
        print("4. Supprimer un compte")
        print("5. Retour au menu principal")

        choice = input("Votre choix: ")

        if choice == '1':
            await handle_list_accounts()
        elif choice == '2':
            await handle_create_account()
        elif choice == '3':
            await handle_update_account()
        elif choice == '4':
            await handle_delete_account()
        elif choice == '5':
            break
        else:
            print("Choix invalide.")


async def handle_list_accounts():
    """Affiche tous les comptes utilisateurs."""
    print("\n--- LISTE DES COMPTES ---")
    accounts = await get_all_accounts()

    if not accounts:
        print("Aucun compte trouvé.")
        return

    for a in accounts:
        print(f"[{a['id_compte']:<3}] {a['nom']} {a['prenom']} ({a['username']}) | Rôle: {a['type_compte']}")
    print("-" * 50)


async def handle_create_account():
    """Gère la création d'un nouveau compte."""
    print("\n--- CRÉATION DE COMPTE ---")
    nom = input("Nom: ")
    prenom = input("Prénom: ")
    email = input("Email: ")
    username = input("Nom d'utilisateur (unique): ")
    password = input("Mot de passe (8+ caractères): ")
    type_compte = input("Type de compte (Utilisateur, Commercial, Administrateur): ")

    result = await create_account(nom, prenom, email, username, password, type_compte)
    print(result.get('message', 'Erreur inconnue.'))


async def handle_update_account():
    """Gère la modification/suppression d'un compte."""
    id_compte_str = input("Entrez l'ID du compte à modifier: ")
    try:
        id_compte = int(id_compte_str)
    except ValueError:
        print("ID invalide.")
        return

    account = await get_account_by_id(id_compte)
    if not account:
        print("Compte non trouvé.")
        return

    print(f"\nModification de {account['username']}")
    print("1. Modifier les informations (Nom/Email/Username)")
    print("2. Changer le mot de passe")

    choice = input("Votre choix: ")
    if choice == '1':
        updates = {}
        updates['nom'] = input(f"Nouveau Nom ({account['nom']}): ") or None
        updates['email'] = input(f"Nouvel Email ({account['email']}): ") or None
        updates['username'] = input(f"Nouveau Username ({account['username']}): ") or None

        fields_to_update = {k: v for k, v in updates.items() if v}
        if fields_to_update:
            result = await update_account_info(id_compte, fields_to_update)
            print(result['message'])
        else:
            print("Aucune modification effectuée.")
    elif choice == '2':
        new_pwd = input("Nouveau mot de passe (8+ caractères): ")
        result = await update_account_password(id_compte, new_pwd)
        print(result['message'])
    else:
        print("Choix invalide.")


async def handle_delete_account():
    """Gère la suppression d'un compte."""
    id_compte_str = input("Entrez l'ID du compte à supprimer: ")
    try:
        id_compte = int(id_compte_str)
    except ValueError:
        print("ID invalide.")
        return

    confirmation = input(f"Êtes-vous sûr de vouloir supprimer le compte {id_compte} ? (O/N): ")
    if confirmation.upper() == 'O':
        result = await delete_account(id_compte)
        print(result['message'])
    else:
        print("Suppression annulée.")


# ----------------------------------------------
#             LOGIQUE DES PROSPECTS
# ----------------------------------------------
# (Les fonctions handle_list_prospects, handle_add_prospect, handle_prospect_details,
# handle_update_prospect, handle_interaction_menu, handle_display_interactions,
# et handle_add_interaction sont déjà dans la réponse précédente et non répétées ici
# pour la concision, mais elles doivent être incluses dans le fichier final.)

# ----------------------------------------------
#             LOGIQUE DE REPORTING ET EXPORT
# ----------------------------------------------
# (Les fonctions handle_reporting_menu, display_status_stats, display_conversion_stats,
# et handle_export_excel sont déjà dans la réponse précédente et non répétées ici.)


# ----------------------------------------------
#             BOUCLE PRINCIPALE DE L'APPLICATION
# ----------------------------------------------

async def application_loop():
    """Boucle principale de l'application, gérant les menus."""
    global CURRENT_USER

    while True:
        if not CURRENT_USER:
            # Étape 1: Authentification
            success = await handle_login()
            if success:
                continue  # Aller au menu principal

            # Offrir l'option de quitter si la connexion échoue
            if input("Quitter l'application ? (O/N): ").upper() == 'O':
                break
            continue

        # Étape 2: Menu principal (après connexion)
        display_user_menu()
        choice = input("Votre choix: ")

        if choice == '1':
            await display_prospects_menu()  # Gestion des Prospects
        elif choice == '2':
            await handle_reporting_menu()  # Reporting & Export
        elif choice == '3':
            await display_account_management_menu()  # Gestion des Comptes (Admin)
        elif choice == '9':
            CURRENT_USER = None
            print("\nDéconnexion réussie.")
        elif choice == '0':
            print("\nFermeture de l'application.")
            break
        else:
            print("\nChoix invalide. Veuillez réessayer.")


async def main():
    """Initialise l'application et lance la boucle."""

    # 1. Connexion à la DB
    host, port, user, password, database = await collect_db_params()
    pool = await initialize_db_pool(host, port, user, password, database, max_tentatives=3)

    if not pool:
        logger.error("Démarrage impossible sans connexion DB.")
        return

    # 2. Lancement de l'application
    try:
        await application_loop()
    except Exception as e:
        logger.critical(f"Erreur fatale dans la boucle principale: {e}")
    finally:
        # 3. Fermeture du pool à la fin
        await close_db_pool()


if __name__ == "__main__":
    try:
        # Nécessaire pour pouvoir utiliser les fonctions 'input' dans le contexte asynchrone
        # La boucle 'main' inclut tous les appels aux fonctions asynchrones.
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication arrêtée par l'utilisateur.")
    except Exception as e:
        logger.critical(f"Erreur inattendue au lancement: {e}")