# Prospectius.py (Le Main) - Aligné sur la structure de la BDD
import asyncio
import logging
from typing import Dict, Any, Optional, Tuple, List

# --- Importation des Services ---
try:
    # Services de base et de gestion des comptes
    from Back.dbManager import initialize_db_pool, close_db_pool
    from Back.Account.accountService import (
        authenticate_account, create_account, get_all_accounts,
        update_account_info, update_account_password, delete_account,
        get_account_by_id
    )
    # Services de gestion des prospects
    from Back.Prospect.prospectService import (
        create_prospect, get_prospects_list, get_prospect_by_id,
        update_prospect, delete_prospect
    )
    # Services de gestion des interactions
    from Back.Interaction.interactionService import (
        create_interaction, get_interactions_by_prospect
    )
    # Services de reporting
    from Back.StatsReport.statService import get_prospect_status_distribution, get_conversion_rate
    # from Back.Export.exportService import export_prospects_to_excel
except ImportError as e:
    print(f"Erreur d'importation. Assurez-vous que les fichiers de services sont dans le chemin correct: {e}")
    exit()

# Configuration du Logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ProspectiusApp")

# Variable pour stocker l'utilisateur connecté
CURRENT_USER: Optional[Dict[str, Any]] = None


# ==============================================
#              FONCTIONS UTILITAIRES
# ==============================================

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
        pass

    print("9. Déconnexion")
    print("0. Quitter l'Application")
    print("-" * 60)


# ==============================================
#          LOGIQUE D'AUTHENTIFICATION & COMPTES
# ==============================================

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


async def handle_create_first_account() -> bool:
    """Force la création d'un compte Administrateur si la DB est vide."""
    print("\n" + "*" * 50)
    print(" * AUCUN COMPTE D'UTILISATEUR DÉTECTÉ   *")
    print(" * Veuillez créer le premier Administrateur. *")
    print("*" * 50)

    print("\n--- CRÉATION DU COMPTE ADMINISTRATEUR INITIAL ---")
    nom = input("Nom: ")
    prenom = input("Prénom: ")
    email = input("Email: ")
    username = input("Nom d'utilisateur (unique): ")
    password = input("Mot de passe (8+ caractères): ")
    type_compte = 'Administrateur'

    result = await create_account(nom, prenom, email, username, password, type_compte)

    if result.get('success'):
        print(f"\n✅ {result['message']}")
        print("Veuillez vous connecter avec ce nouveau compte.")
        return True
    else:
        print(f"\n❌ Échec de la création: {result.get('message', 'Erreur inconnue.')}")
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
        print("9. Retour au menu principal")

        choice = input("Votre choix: ")

        if choice == '1':
            await handle_list_accounts()
        elif choice == '2':
            await handle_create_account()
        elif choice == '3':
            await handle_update_account()
        elif choice == '4':
            await handle_delete_account()
        elif choice == '9':
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
    input("Appuyez sur Entrée pour continuer...")


async def handle_create_account():
    """Gère la création d'un nouveau compte (utilisé dans le menu Admin)."""
    print("\n--- CRÉATION DE COMPTE ---")
    nom = input("Nom: ")
    prenom = input("Prénom: ")
    email = input("Email: ")
    username = input("Nom d'utilisateur (unique): ")
    password = input("Mot de passe (8+ caractères): ")
    type_compte = input("Type de compte (Utilisateur, Commercial, Administrateur): ")

    result = await create_account(nom, prenom, email, username, password, type_compte)
    print(result.get('message', 'Erreur inconnue.'))
    input("Appuyez sur Entrée pour continuer...")


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
    print("9. Annuler et Retour")

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
    elif choice == '9':
        print("Modification annulée.")
    else:
        print("Choix invalide.")

    if choice in ['1', '2', '9']:
        input("Appuyez sur Entrée pour continuer...")


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

    input("Appuyez sur Entrée pour continuer...")


# ==============================================
#             LOGIQUE DES PROSPECTS
# ==============================================

async def display_prospects_menu():
    """ Menu de gestion des prospects. """
    while True:
        print("\n--- GESTION DES PROSPECTS ---")
        print("1. Lister / Filtrer les prospects")
        print("2. Ajouter un nouveau prospect")
        print("3. Gérer un prospect (Détails, Interagir, Modifier, Supprimer)")
        print("9. Retour au menu principal")

        choice = input("Votre choix: ")

        if choice == '1':
            await handle_list_prospects()
        elif choice == '2':
            await handle_add_prospect()
        elif choice == '3':
            await handle_prospect_details_menu()
        elif choice == '9':
            break
        else:
            print("Choix invalide.")


async def handle_add_prospect():
    """Gère la création d'un nouveau prospect. ALIGNÉ BDD"""
    print("\n--- AJOUT D'UN NOUVEAU PROSPECT ---")
    nomp = input("Nom: ")
    prenomp = input("Prénom: ")
    email = input("Email: ")
    telephone = input("Téléphone: ")
    adresse = input("Adresse: ")

    type_p = input("Type (particulier, societe, organisation): ").lower()
    if type_p not in ('particulier', 'societe', 'organisation'):
        print("Type invalide. Défaut: particulier.")
        type_p = 'particulier'

    status = "nouveau"

    users = await get_all_accounts()

    if not users:
        print("❌ Impossible d'assigner. Aucun compte utilisateur trouvé.")
        id_assignation = CURRENT_USER['id_compte']
    else:
        print("\n--- CHOIX D'ASSIGNATION ---")
        commercials = [u for u in users if u['type_compte'] in ('Commercial', 'Utilisateur', 'Administrateur')]

        if not commercials:
            print("Aucun commercial trouvé. Assigné à l'utilisateur actuel.")
            id_assignation = CURRENT_USER['id_compte']
        else:
            for c in commercials:
                print(f"[{c['id_compte']:<3}] {c['username']} ({c['type_compte']})")

            id_assignation_str = input(f"ID du commercial à assigner (Défaut: {CURRENT_USER['id_compte']}): ")
            try:
                id_assignation = int(id_assignation_str) if id_assignation_str else CURRENT_USER['id_compte']
            except ValueError:
                print("ID invalide. Assigné à l'utilisateur actuel.")
                id_assignation = CURRENT_USER['id_compte']

    # Le service create_prospect doit accepter les 7 arguments: nomp, prenomp, telephone, email, adresse, type, status, assignation
    result = await create_prospect(nomp, prenomp, telephone, email, adresse, type_p, status, id_assignation)

    print(result.get('message', 'Erreur inconnue lors de la création du prospect.'))
    input("Appuyez sur Entrée pour continuer...")


async def handle_list_prospects():
    """Affiche la liste des prospects avec option de filtrage."""
    print("\n--- LISTE DES PROSPECTS ---")

    if CURRENT_USER['type_compte'] != 'Administrateur':
        assignation_filter = CURRENT_USER['id_compte']
        print(f"Filtre actif: Affichage de vos prospects uniquement (ID assigné: {assignation_filter}).")
    else:
        assignation_filter = None

    status_filter = input("Filtrer par statut (laisser vide pour tout): ").lower() or None

    prospects = await get_prospects_list(assignation_filter, status_filter)

    if not prospects:
        print("\n=> Aucun prospect trouvé avec ces critères.")
        input("Appuyez sur Entrée pour continuer...")
        return

    print(f"\n| {'ID':<4} | {'NOM & PRENOM':<25} | {'TELEPHONE':<15} | {'STATUT':<12} | {'ASSIGNÉ À':<15} |")
    print("|" + "―" * 5 + "|" + "―" * 26 + "|" + "―" * 16 + "|" + "―" * 13 + "|" + "―" * 16 + "|")

    for p in prospects:
        # NOTE: On suppose que le service a renommé 'nomp' et 'prenomp' en 'nom' et 'prenom' pour la simplicité du Dictionnaire retourné.
        assigned_user = p.get('username_assigne', f"ID: {p['assignation']}")
        full_name = f"{p['nom']} {p['prenom']}"  # Si les services renvoient 'nom' et 'prenom'
        # Si les services renvoient 'nomp' et 'prenomp': full_name = f"{p['nomp']} {p['prenomp']}"
        print(
            f"| {p['id_prospect']:<4} | {full_name[:25]:<25} | {p['telephone']:<15} | {p['status']:<12} | {assigned_user:<15} |")

    print("\nTotal prospects affichés:", len(prospects))
    input("Appuyez sur Entrée pour continuer...")


async def handle_prospect_details_menu():
    """Gère le sous-menu de détails/modification/suppression/interaction."""
    prospect_id_str = input("\nEntrez l'ID du prospect à gérer: ")
    try:
        prospect_id = int(prospect_id_str)
    except ValueError:
        print("ID invalide.")
        return

    while True:
        prospect = await get_prospect_by_id(prospect_id)
        if not prospect:
            print(f"❌ Prospect ID {prospect_id} non trouvé.")
            return

        print("\n--- GESTION DU PROSPECT ---")
        # Utilisation des champs renvoyés par la BDD (nomp, prenomp)
        prospect_name = f"{prospect.get('nomp', 'Nom')} {prospect.get('prenomp', 'Prénom')}"
        print(f"Prospect: {prospect_name} | Statut actuel: {prospect['status']}")
        print("-" * 50)
        print("1. Afficher les détails complets")
        print("2. Modifier le prospect")
        print("3. Gérer les interactions (Ajouter/Lister)")
        print("4. Supprimer le prospect")
        print("9. Retour au menu des Prospects")

        choice = input("Votre choix: ")

        if choice == '1':
            await handle_display_prospect_details(prospect)
        elif choice == '2':
            await handle_update_prospect_details(prospect_id, prospect)
        elif choice == '3':
            await handle_interaction_menu(prospect_id)
        elif choice == '4':
            await handle_delete_prospect_item(prospect_id)
            break
        elif choice == '9':
            break
        else:
            print("Choix invalide.")


async def handle_display_prospect_details(prospect: Dict):
    """Affiche tous les détails d'un prospect. ALIGNÉ BDD"""
    print("\n--- DÉTAILS DU PROSPECT ---")

    user_info = await get_account_by_id(prospect['assignation'])
    assigned_user = user_info['username'] if user_info else f"ID Inconnu: {prospect['assignation']}"

    # Affichage des champs BDD
    print(f"ID Prospect: {prospect['id_prospect']}")
    print(f"Nom/Prénom: {prospect.get('nomp')}/{prospect.get('prenomp')}")
    print(f"Email: {prospect['email']}")
    print(f"Téléphone: {prospect['telephone']}")
    print(f"Adresse: {prospect.get('adresse')}")
    print(f"Type (Société/Particulier): {prospect.get('type').upper()}")
    print(f"Statut: {prospect['status'].upper()}")
    print(f"Assigné à: {assigned_user}")
    print(f"Date de Création: {prospect['creation']}")

    input("\nAppuyez sur Entrée pour continuer...")


async def handle_update_prospect_details(prospect_id: int, prospect: Dict):
    """Gère la modification des informations d'un prospect. ALIGNÉ BDD"""
    print("\n--- MODIFICATION DU PROSPECT ---")
    print("Laisser vide pour conserver la valeur actuelle.")

    updates = {}
    updates['nomp'] = input(f"Nom ({prospect.get('nomp')}): ") or None
    updates['prenomp'] = input(f"Prénom ({prospect.get('prenomp')}): ") or None
    updates['email'] = input(f"Email ({prospect['email']}): ") or None
    updates['telephone'] = input(f"Téléphone ({prospect['telephone']}): ") or None
    updates['adresse'] = input(f"Adresse ({prospect.get('adresse')}): ") or None

    # Statut ENUM: nouveau, interesse, negociation, perdu, converti
    current_status = prospect['status']
    valid_statuses = ['nouveau', 'interesse', 'negociation', 'perdu', 'converti']
    new_status = input(f"Statut ({current_status} | {valid_statuses}): ").lower()
    if new_status in valid_statuses:
        updates['status'] = new_status
    elif new_status:
        print("Statut invalide ignoré.")

    # Type ENUM: particulier, societe, organisation
    current_type = prospect['type']
    valid_types = ['particulier', 'societe', 'organisation']
    new_type = input(f"Type ({current_type} | {valid_types}): ").lower()
    if new_type in valid_types:
        updates['type'] = new_type
    elif new_type:
        print("Type invalide ignoré.")

    # Assignation
    user_info = await get_account_by_id(prospect['assignation'])
    current_user = user_info['username'] if user_info else 'Inconnu'

    new_assignation_str = input(f"Assignation (Actuel: {current_user} | ID Compte): ")
    if new_assignation_str:
        try:
            updates['assignation'] = int(new_assignation_str)
        except ValueError:
            print("ID d'assignation invalide ignoré.")

    fields_to_update = {k: v for k, v in updates.items() if v is not None}

    if fields_to_update:
        result = await update_prospect(prospect_id, fields_to_update)
        print(result['message'])
    else:
        print("Aucune modification effectuée.")

    input("Appuyez sur Entrée pour continuer...")


async def handle_delete_prospect_item(prospect_id: int):
    """Gère la suppression d'un prospect."""
    confirmation = input(f"Êtes-vous sûr de vouloir supprimer le prospect ID {prospect_id} ? (O/N): ")
    if confirmation.upper() == 'O':
        result = await delete_prospect(prospect_id)
        print(result['message'])
    else:
        print("Suppression annulée.")
    input("Appuyez sur Entrée pour continuer...")


# ==============================================
#             LOGIQUE DES INTERACTIONS
# ==============================================

async def handle_interaction_menu(prospect_id: int):
    """Sous-menu de gestion des interactions pour un prospect donné."""
    while True:
        prospect = await get_prospect_by_id(prospect_id)

        print("\n--- GESTION DES INTERACTIONS ---")
        prospect_name = f"{prospect.get('nomp', 'Nom')} {prospect.get('prenomp', 'Prénom')}"
        print(f"Prospect: {prospect_name}")
        print("-" * 50)
        print("1. Lister les interactions")
        print("2. Ajouter une nouvelle interaction")
        print("9. Retour à la gestion du Prospect")

        choice = input("Votre choix: ")

        if choice == '1':
            await handle_display_interactions(prospect_id)
        elif choice == '2':
            await handle_add_interaction(prospect_id)
        elif choice == '9':
            break
        else:
            print("Choix invalide.")


async def handle_display_interactions(prospect_id: int):
    """Affiche la liste des interactions pour un prospect."""
    print("\n--- HISTORIQUE DES INTERACTIONS ---")
    interactions = await get_interactions_by_prospect(prospect_id)

    if not interactions:
        print("Aucune interaction enregistrée pour ce prospect.")
        input("Appuyez sur Entrée pour continuer...")
        return

    print(f"| {'ID':<4} | {'TYPE':<15} | {'DATE':<19} | {'NOTE':<40} |")
    print("|" + "―" * 5 + "|" + "―" * 16 + "|" + "―" * 20 + "|" + "―" * 41 + "|")

    for i in interactions:
        note_display = i['note'][:37] + '...' if len(i['note']) > 40 else i['note']
        date_str = str(i['date_interaction']).split('.')[0]

        print(
            f"| {i['id_interaction']:<4} | {i['type']:<15} | {date_str:<19} | {note_display:<40} |")  # Clé 'type' alignée BDD

    input("\nAppuyez sur Entrée pour continuer...")


async def handle_add_interaction(prospect_id: int):
    """Ajoute une nouvelle interaction au prospect. ALIGNÉ BDD"""
    print("\n--- AJOUT D'UNE INTERACTION ---")

    # Types d'interaction ENUM: email, appel, sms, reunion
    valid_types = ['appel', 'email', 'sms', 'reunion']
    type_inter = input(f"Type d'interaction ({valid_types}): ").lower()

    if type_inter not in valid_types:
        print("Type d'interaction invalide. Annulation.")
        return

    note = input("Note de l'interaction (détails importants): ")

    id_compte = CURRENT_USER['id_compte']

    # Le service doit accepter la clé 'type' au lieu de 'type_inter' si il a été codé avec les noms BDD
    result = await create_interaction(prospect_id, id_compte, type_inter, note)

    print(result.get('message', 'Erreur inconnue lors de l\'enregistrement de l\'interaction.'))
    input("Appuyez sur Entrée pour continuer...")


# ==============================================
#             LOGIQUE DE REPORTING (STUBS)
# ==============================================

async def handle_reporting_menu():
    """ Menu stub pour le reporting et l'export. """
    while True:
        print("\n--- REPORTING & EXPORT ---")
        print("1. Statistiques de distribution par statut")
        print("2. Taux de conversion global")
        print("3. Exporter la liste complète (Excel)")
        print("9. Retour au menu principal")

        choice = input("Votre choix: ")

        if choice == '1':
            print("Logique d'affichage des statistiques de statut non implémentée (appel à statService).")
        elif choice == '2':
            print("Logique d'affichage du taux de conversion non implémentée (appel à statService).")
        elif choice == '3':
            print("Logique d'export non implémentée.")
        elif choice == '9':
            break
        else:
            print("Choix invalide.")


# ==============================================
#             BOUCLE PRINCIPALE DE L'APPLICATION
# ==============================================

async def application_loop():
    """Boucle principale de l'application, gérant les menus."""
    global CURRENT_USER

    while True:
        if not CURRENT_USER:
            # Étape 1: Pré-authentification et vérification des comptes
            accounts = await get_all_accounts()

            if not accounts:
                # CAS 1: Base de données vide -> Création forcée du premier compte
                if not await handle_create_first_account():
                    if input("Quitter l'application ? (O/N): ").upper() == 'O':
                        break
                    continue

            # CAS 2: Des comptes existent ou un compte vient d'être créé -> Tentative de Connexion
            success = await handle_login()
            if success:
                continue

                # Échoue la connexion
            if input("Quitter l'application ? (O/N): ").upper() == 'O':
                break
            continue

        # Étape 2: Menu principal (après connexion)
        display_user_menu()
        choice = input("Votre choix: ")

        if choice == '1':
            await display_prospects_menu()
        elif choice == '2':
            await handle_reporting_menu()
        elif choice == '3':
            if CURRENT_USER['type_compte'] == 'Administrateur':
                await display_account_management_menu()
            else:
                print("Accès non autorisé.")
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
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nApplication arrêtée par l'utilisateur.")
    except Exception as e:
        logger.critical(f"Erreur inattendue au lancement: {e}")