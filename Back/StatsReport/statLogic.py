from typing import List, Dict, Any, Tuple


## --- 1. Statistiques Basiques de Distribution ---

def calculate_status_distribution(data: List[Dict]) -> List[Dict]:
    """
    Calcule la distribution des prospects par statut.

    Args:
        data: Liste des dictionnaires [{'status': 'nouveau', 'count': 45}, ...]
    Returns:
        La liste triée des statuts et de leurs comptes.
    """
    # Ici, la BDD fait déjà le travail (GROUP BY), nous retournons juste le résultat.
    # On peut ajouter un tri si la BDD ne le fait pas.
    return sorted(data, key=lambda x: x['count'], reverse=True)


## --- 2. Statistiques de Taux de Conversion ---

def calculate_conversion_rate(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcule le taux de conversion (Prospect -> Converti).

    Args:
        data: Dictionnaire contenant 'total_converti' et 'total_prospects'.
    Returns:
        Dictionnaire avec les totaux et le taux calculé.
    """
    total_converti = data.get('total_converti', 0)
    total_prospects = data.get('total_prospects', 0)

    rate = 0.0
    if total_prospects > 0:
        rate = (total_converti / total_prospects) * 100

    return {
        "total_converti": total_converti,
        "total_prospects": total_prospects,
        "taux_conversion": f"{rate:.2f}%"
    }


## --- 3. Statistiques de Performance Commerciale (par Utilisateur) ---

def calculate_user_performance(data: List[Dict]) -> List[Dict]:
    """
    Calcule le nombre de prospects et le taux de conversion par utilisateur assigné.

    Args:
        data: Liste des dictionnaires de la DB (doit contenir count, converted_count, username).
    Returns:
        Liste enrichie avec le taux de conversion par commercial.
    """
    results = []
    for item in data:
        total = item['total_prospects']
        converted = item['total_converti']
        rate = 0.0

        if total > 0:
            rate = (converted / total) * 100

        results.append({
            "username": item['username'],
            "total_prospects": total,
            "total_converti": converted,
            "taux_conversion": f"{rate:.2f}%"
        })

    return sorted(results, key=lambda x: float(x['taux_conversion'].strip('%')), reverse=True)