from typing import Dict, Any, List
from Back.dbManager import execute_query
from .statLogic import calculate_status_distribution, calculate_conversion_rate, calculate_user_performance

# --- 1. Distribution des Statuts ---
async def get_prospect_status_distribution() -> List[Dict]:
    """
    Récupère la distribution des prospects par statut et la traite.
    """
    sql = """
    SELECT status, COUNT(id_prospect) as count
    FROM Prospect
    GROUP BY status;
    """
    data = await execute_query(sql, fetch_all=True)
    return calculate_status_distribution(data) # Utilise la logique


# --- 2. Taux de Conversion Global ---
async def get_conversion_rate() -> Dict[str, Any]:
    """
    Calcule le taux de conversion global.
    """
    sql = """
    SELECT
        COUNT(CASE WHEN status = 'converti' THEN 1 END) AS total_converti,
        COUNT(id_prospect) AS total_prospects
    FROM Prospect;
    """
    data = await execute_query(sql, fetch_one=True)
    # Assurez-vous que data n'est pas None
    if data:
        return calculate_conversion_rate(data) # Utilise la logique
    return {"total_converti": 0, "total_prospects": 0, "taux_conversion": "0.00%"}


# --- 3. Performance Commerciale par Utilisateur ---
async def get_user_conversion_performance() -> List[Dict]:
    """
    Calcule le nombre de prospects et le taux de conversion par utilisateur.
    """
    sql = """
    SELECT
        a.username,
        COUNT(p.id_prospect) AS total_prospects,
        COUNT(CASE WHEN p.status = 'converti' THEN 1 END) AS total_converti
    FROM Prospect p
    JOIN Account a ON p.assignation = a.id_compte
    GROUP BY a.username
    ORDER BY total_converti DESC;
    """
    data = await execute_query(sql, fetch_all=True)
    return calculate_user_performance(data)


# --- 4. Historique des Créations de Prospects (Exemple de rapport Temporel) ---
async def get_prospects_created_by_month() -> List[Dict]:
    """
    Compte le nombre de prospects créés par mois/année.
    """
    sql = """
    SELECT 
        DATE_FORMAT(creation, '%Y-%m') AS month_year,
        COUNT(id_prospect) AS total_created
    FROM Prospect
    GROUP BY month_year
    ORDER BY month_year ASC;
    """
    return await execute_query(sql, fetch_all=True)