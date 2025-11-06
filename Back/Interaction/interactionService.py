from typing import Dict, Optional, List, Any, Tuple
from Back.dbManager import execute_query

# --- Constantes (Types d'Interaction) ---
TYPE_INTERACTION = ('email', 'appel', 'sms', 'reunion')


# --- C. CREATE (Ajout d'une Interaction) ---
async def create_interaction(id_prospect: int, id_compte: int, type_interaction: str, note: str) -> Dict[str, Any]:
    """
    Ajoute une nouvelle interaction à la base de données et met à jour
    l'horodatage de modification ('date_update') du Prospect.
    """

    # Validation du type d'interaction
    if type_interaction not in TYPE_INTERACTION:
        return {"success": False,
                "message": f"Type d'interaction invalide. Doit être l'un de: {', '.join(TYPE_INTERACTION)}."}

    # 1. Insertion de l'interaction
    sql_insert = """
                 INSERT INTO Interaction (id_prospect, id_compte, type, note)
                 VALUES (%s, %s, %s, %s) \
                 """
    # NOTE: date_interaction est géré par DEFAULT CURRENT_TIMESTAMP dans la BDD
    params: Tuple = (id_prospect, id_compte, type_interaction, note)

    try:
        # Exécuter l'insertion
        await execute_query(sql_insert, params)

        # 2. Mise à jour de la colonne de dernière modification du Prospect
        # ALIGNÉ BDD: Utilisation de la colonne 'date_update'
        sql_update_prospect = "UPDATE Prospect SET date_update = NOW() WHERE id_prospect = %s"
        await execute_query(sql_update_prospect, (id_prospect,))

        return {"success": True, "message": "Interaction ajoutée et prospect mis à jour avec succès."}
    except Exception as e:
        # Gérer les erreurs de clés étrangères (prospect ou compte invalide)
        return {"success": False, "message": f"Échec de l'ajout de l'interaction: {e}"}


# --- R. READ (Historique par Prospect) ---
async def get_interactions_by_prospect(id_prospect: int) -> List[Dict]:
    """
    Récupère l'historique de toutes les interactions pour un prospect donné,
    y compris le nom de l'utilisateur qui a créé l'interaction.
    """
    # Jointure avec Account pour afficher le nom/username de l'auteur de l'interaction
    sql = """
          SELECT i.id_interaction,
                 i.type,
                 i.note,
                 i.date_interaction,
                 a.username AS createur_username,
                 a.nom      AS createur_nom,
                 a.prenom   AS createur_prenom
          FROM Interaction i
                   JOIN Account a ON i.id_compte = a.id_compte
          WHERE i.id_prospect = %s
          ORDER BY i.date_interaction DESC \
          """
    return await execute_query(sql, (id_prospect,), fetch_all=True)


# --- D. DELETE (Suppression d'une Interaction) ---
async def delete_interaction(id_interaction: int) -> Dict[str, Any]:
    """
    Supprime une interaction spécifique.

    NOTE: Une logique métier plus avancée devrait recalcule la date_update du Prospect
    si la dernière interaction est supprimée. Pour l'instant, on se contente de la suppression simple.
    """

    sql = "DELETE FROM Interaction WHERE id_interaction = %s"

    try:
        rows_affected = await execute_query(sql, (id_interaction,))
        if rows_affected > 0:
            return {"success": True, "message": "Interaction supprimée avec succès."}
        return {"success": False, "message": "Interaction non trouvée."}
    except Exception as e:
        return {"success": False, "message": f"Échec de la suppression: {e}"}