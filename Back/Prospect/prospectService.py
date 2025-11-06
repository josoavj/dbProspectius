from typing import Dict, Optional, List, Any, Tuple
from Back.dbManager import execute_query

# --- Constantes (Types et Status) ---
TYPE_PROSPECT = ('particulier', 'societe', 'organisation')
STATUS_PROSPECT = ('nouveau', 'interesse', 'negociation', 'perdu', 'converti')


# --- C. CREATE (Création d'un Prospect) ---
async def create_prospect(nomp: str, prenomp: str, telephone: str, email: str, adresse: str, type_prospect: str,
                          status_prospect: str, assignation_id: int) -> Dict[str, Any]:
    """
    Ajoute un nouveau prospect à la base de données après validation.

    Correction: Ajout de status_prospect dans la signature pour l'alignement avec la BDD/Front.
    """

    # Validation basique du type et statut de prospect
    if type_prospect not in TYPE_PROSPECT:
        return {"success": False,
                "message": f"Type de prospect invalide. Doit être l'un de: {', '.join(TYPE_PROSPECT)}."}
    if status_prospect not in STATUS_PROSPECT:
        return {"success": False,
                "message": f"Statut de prospect invalide. Doit être l'un de: {', '.join(STATUS_PROSPECT)}."}

    sql = """
          INSERT INTO Prospect (nomp, prenomp, telephone, email, adresse, type, status, assignation)
          VALUES (%s, %s, %s, %s, %s, %s, %s, %s) \
          """
    params: Tuple = (nomp, prenomp, telephone, email, adresse, type_prospect, status_prospect, assignation_id)

    try:
        rows_affected = await execute_query(sql, params)
        if rows_affected > 0:
            # Idéalement, on récupérerait l'ID généré pour le front-end
            return {"success": True, "message": "Prospect créé avec succès."}
        return {"success": False, "message": "Échec de la création du prospect (aucune ligne affectée)."}
    except Exception as e:
        return {"success": False, "message": f"Erreur BDD lors de la création: {e}"}


# --- R. READ (Lecture et Liste des Prospects) ---
async def get_prospect_by_id(id_prospect: int) -> Optional[Dict]:
    """Récupère un prospect spécifique par son ID, y compris le responsable."""

    sql = """
          SELECT p.*,
                 a.username AS username_assigne,
                 a.nom      AS nom_assigne
          FROM Prospect p
                   LEFT JOIN Account a ON p.assignation = a.id_compte
          WHERE p.id_prospect = %s \
          """
    return await execute_query(sql, (id_prospect,), fetch_one=True)


async def get_prospects_list(assignation_filter: Optional[int] = None, status_filter: Optional[str] = None,
                             search_term: Optional[str] = None) -> List[Dict]:
    """
    Récupère la liste des prospects, supportant les filtres et la recherche.

    Correction: Inversion de l'ordre des paramètres optionnels status_filter et assignation_filter
    pour aligner la signature avec la logique de filtrage ci-dessous.
    """

    sql = """
          SELECT p.id_prospect,
                 p.nomp,
                 p.prenomp,
                 p.telephone,
                 p.email,
                 p.status,
                 p.creation,
                 p.date_update,
                 a.username AS username_assigne
          FROM Prospect p
                   LEFT JOIN Account a ON p.assignation = a.id_compte
          WHERE 1 = 1 \
          """
    params: List[Any] = []

    # Vérification de l'assignation en premier (logique Admin/Commercial)
    if assignation_filter:
        sql += " AND p.assignation = %s"
        params.append(assignation_filter)

    # Vérification du statut
    if status_filter and status_filter in STATUS_PROSPECT:
        sql += " AND p.status = %s"
        params.append(status_filter)

    if search_term:
        # Recherche dans le nom, prénom ou email, téléphone
        search_like = f"%{search_term}%"
        sql += " AND (p.nomp LIKE %s OR p.prenomp LIKE %s OR p.email LIKE %s OR p.telephone LIKE %s)"
        params.extend([search_like, search_like, search_like, search_like])

    sql += " ORDER BY p.date_update DESC"

    return await execute_query(sql, tuple(params), fetch_all=True)


# --- U. UPDATE (Mise à jour d'un Prospect) ---
async def update_prospect(id_prospect: int, fields_to_update: Dict[str, Any]) -> Dict[str, Any]:
    """Met à jour un prospect avec un dictionnaire de champs à modifier."""

    if not fields_to_update:
        return {"success": False, "message": "Aucun champ fourni pour la mise à jour."}

    # Liste des champs autorisés à être mis à jour
    # ALIGNÉ BDD
    allowed_fields = ['nomp', 'prenomp', 'telephone', 'email', 'adresse', 'type', 'status', 'assignation']
    set_clauses: List[str] = []
    params: List[Any] = []

    # Validation et construction dynamique de la requête
    for key, value in fields_to_update.items():
        if key in allowed_fields:
            if key == 'type' and value not in TYPE_PROSPECT:
                return {"success": False, "message": f"Type de prospect '{value}' invalide."}
            if key == 'status' and value not in STATUS_PROSPECT:
                return {"success": False, "message": f"Statut de prospect '{value}' invalide."}

            set_clauses.append(f"{key} = %s")
            params.append(value)

    if not set_clauses:
        return {"success": False, "message": "Champs de mise à jour invalides ou non autorisés."}

    sql = "UPDATE Prospect SET " + ", ".join(set_clauses) + " WHERE id_prospect = %s"
    params.append(id_prospect)

    try:
        rows_affected = await execute_query(sql, tuple(params))
        if rows_affected > 0:
            return {"success": True, "message": "Prospect mis à jour avec succès."}
        return {"success": False, "message": "Aucune modification effectuée ou prospect non trouvé."}
    except Exception as e:
        return {"success": False, "message": f"Erreur BDD lors de la mise à jour: {e}"}


# --- D. DELETE (Suppression d'un Prospect) ---
async def delete_prospect(id_prospect: int) -> Dict[str, Any]:
    """
    Supprime un prospect par son ID. Gère la suppression des interactions liées.
    """
    try:
        # 1. Suppression des interactions liées (nécessaire avant la suppression du prospect)
        sql_delete_interactions = "DELETE FROM Interaction WHERE id_prospect = %s"
        await execute_query(sql_delete_interactions, (id_prospect,))

        # 2. Suppression du prospect
        sql_delete_prospect = "DELETE FROM Prospect WHERE id_prospect = %s"
        rows_affected = await execute_query(sql_delete_prospect, (id_prospect,))

        if rows_affected > 0:
            return {"success": True, "message": "Prospect et ses interactions supprimés avec succès."}
        return {"success": False, "message": "Prospect non trouvé."}

    except Exception as e:
        return {"success": False, "message": f"Échec de la suppression du prospect: {e}"}