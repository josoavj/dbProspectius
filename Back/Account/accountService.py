import bcrypt
import re
from typing import Dict, Optional, List, Any
from Back.dbManager import execute_query


# --- Fonctions de Hachage et Vérification (Synchrones) ---

def hash_password(password: str) -> str:
    """Hache le mot de passe en utilisant bcrypt et le retourne en chaîne de caractères."""
    hashed_bytes = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())
    return hashed_bytes.decode('utf8')


def check_password(password: str, hashed_password: str) -> bool:
    """Vérifie le mot de passe avec le hachage stocké."""
    try:
        # Les deux arguments doivent être encodés en bytes pour bcrypt.checkpw
        return bcrypt.checkpw(password.encode('utf8'), hashed_password.encode('utf8'))
    except ValueError:
        # Gérer le cas où le hachage stocké est invalide ou corrompu
        return False


# --- Fonctions de Validation des Données (Python) ---

def validate_account_data(nom: str, prenom: str, email: str, username: str, password: str) -> Optional[str]:
    """
    Valide les données côté application avant l'insertion/mise à jour,
    renforçant les triggers MySQL.
    """

    # 1. Longueur des champs obligatoires
    if not nom or not prenom or not username:
        return "Les champs Nom, Prénom et Nom d'utilisateur sont obligatoires."

    # 2. Longueur du mot de passe (doit être >= 8, comme la contrainte MySQL)
    if len(password) < 8:
        return "Le mot de passe doit contenir au moins 8 caractères."

    # 3. Format de l'Email (simple regex, comme le Trigger MySQL)
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return "Format d'email invalide."

    # 4. Vérification que le nom d'utilisateur/prénom/nom n'est pas utilisé comme mot de passe (Sécurité)
    lowered_password = password.lower()
    if lowered_password in (nom.lower(), prenom.lower(), username.lower()):
        return "Le mot de passe ne doit pas être le nom, le prénom ou le nom d'utilisateur."

    return None  # Validation réussie


# --- Fonctions CRUD Asynchrones ---

# C. CREATE (Création de compte)
async def create_account(nom: str, prenom: str, email: str, username: str, password: str, type_compte: str) -> Dict[
    str, Any]:
    """Crée un nouvel utilisateur après validation et hachage."""

    # Validation côté application
    validation_error = validate_account_data(nom, prenom, email, username, password)
    if validation_error:
        return {"success": False, "message": validation_error}

    # Hachage
    hashed_pwd = hash_password(password)

    # Requête SQL
    sql = """
          INSERT INTO Account (nom, prenom, email, username, password, type_compte)
          VALUES (%s, %s, %s, %s, %s, %s)
          """
    params = (nom, prenom, email, username, hashed_pwd, type_compte)

    try:
        # Exécute la requête (execute_query retourne rowcount pour INSERT)
        await execute_query(sql, params)
        # La table Account a un trigger qui gère l'unicité et le compte Admin unique
        return {"success": True, "message": "Compte créé avec succès."}
    except Exception as e:
        # Les erreurs de BDD (doublon d'email/username, trigger Admin) sont gérées ici
        return {"success": False, "message": f"Échec de la création: {e}"}


# R. READ (Lecture et Liste des comptes)
async def get_account_by_id(id_compte: int) -> Optional[Dict]:
    """Récupère les informations d'un compte (sans le mot de passe)."""
    sql = "SELECT id_compte, nom, prenom, email, username, type_compte, date_creation FROM Account WHERE id_compte = %s"
    # fetch_one=True retourne un dictionnaire (si DictCursor est utilisé)
    return await execute_query(sql, (id_compte,), fetch_one=True)


async def get_all_accounts() -> List[Dict]:
    """Récupère la liste complète des comptes (sans mot de passe)."""
    sql = "SELECT id_compte, nom, prenom, email, username, type_compte, date_creation FROM Account ORDER BY nom, prenom"
    # fetch_all=True retourne une liste de dictionnaires
    return await execute_query(sql, fetch_all=True)


# U. UPDATE (Mise à jour des informations d'un compte)
async def update_account_info(id_compte: int, fields_to_update: Dict[str, Any]) -> Dict[str, Any]:
    """Met à jour les informations du compte (hors mot de passe et type_compte)."""

    if not fields_to_update:
        return {"success": False, "message": "Aucun champ fourni pour la mise à jour."}

    allowed_fields = ['nom', 'prenom', 'email', 'username']
    set_clauses = []
    params = []

    # Construction dynamique de la requête
    for key, value in fields_to_update.items():
        if key in allowed_fields:
            set_clauses.append(f"{key} = %s")
            params.append(value)

    if not set_clauses:
        return {"success": False, "message": "Champs de mise à jour invalides."}

    sql = "UPDATE Account SET " + ", ".join(set_clauses) + " WHERE id_compte = %s"
    params.append(id_compte)

    try:
        rows_affected = await execute_query(sql, tuple(params))
        if rows_affected > 0:
            return {"success": True, "message": "Informations du compte mises à jour."}
        return {"success": False, "message": "Compte non trouvé ou aucune modification effectuée."}
    except Exception as e:
        # Gérer les erreurs de BDD (doublon d'email/username, trigger de validation d'email)
        return {"success": False, "message": f"Échec de la mise à jour: {e}"}


async def update_account_password(id_compte: int, new_password: str) -> Dict[str, Any]:
    """Met à jour uniquement le mot de passe haché."""

    # Vérification de la longueur du mot de passe
    if len(new_password) < 8:
        return {"success": False, "message": "Le nouveau mot de passe doit contenir au moins 8 caractères."}

    hashed_pwd = hash_password(new_password)
    sql = "UPDATE Account SET password = %s WHERE id_compte = %s"

    try:
        rows_affected = await execute_query(sql, (hashed_pwd, id_compte))
        if rows_affected > 0:
            return {"success": True, "message": "Mot de passe mis à jour avec succès."}
        return {"success": False, "message": "Compte non trouvé."}
    except Exception as e:
        return {"success": False, "message": f"Échec de la mise à jour du mot de passe: {e}"}


# D. DELETE (Suppression de compte)
async def delete_account(id_compte: int) -> Dict[str, Any]:
    """Supprime un compte utilisateur."""

    sql = "DELETE FROM Account WHERE id_compte = %s"

    try:
        rows_affected = await execute_query(sql, (id_compte,))
        if rows_affected > 0:
            return {"success": True, "message": "Compte supprimé avec succès."}
        return {"success": False, "message": "Compte non trouvé."}
    except Exception as e:
        # Gérer l'erreur de contrainte (clé étrangère ou suppression du dernier Admin)
        return {"success": False, "message": f"Échec de la suppression (contrainte BDD): {e}"}


# --- Fonction d'Authentification (pour la connexion) ---
async def authenticate_account(username: str, password: str) -> Dict[str, Any]:
    """Authentifie l'utilisateur via le nom d'utilisateur et le mot de passe."""

    # 1. Récupérer le mot de passe haché et les infos du compte par username
    sql = "SELECT id_compte, password, nom, prenom, type_compte FROM Account WHERE username = %s"
    account_data = await execute_query(sql, (username,), fetch_one=True)

    if account_data:
        # 2. Vérifier le mot de passe
        stored_hashed_pwd = account_data['password']

        if check_password(password, stored_hashed_pwd):
            # Succès
            return {
                "authenticated": True,
                "id_compte": account_data['id_compte'],
                "nom": account_data['nom'],
                "prenom": account_data['prenom'],
                "type_compte": account_data['type_compte']
            }

    # Échec de l'authentification (utilisateur non trouvé ou mot de passe incorrect)
    return {"authenticated": False, "message": "Nom d'utilisateur ou mot de passe incorrect."}