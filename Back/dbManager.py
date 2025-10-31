# db_manager.py (Version Améliorée)
import asyncio
import logging
import aiomysql
from typing import Optional, Any, Dict, List, Tuple

# Configuration du logger
logger = logging.getLogger("DBManager")
logger.setLevel(logging.INFO)

# Variable globale pour stocker le pool de connexions
_pool: Optional[aiomysql.Pool] = None


# --- Fonctions de Gestion de la Connexion ---

async def initialize_db_pool(
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        max_tentatives: int = 3
) -> Optional[aiomysql.Pool]:
    """
    Tente d'établir un pool de connexions aiomysql avec une logique de nouvelles tentatives.
    """
    global _pool

    for tentative in range(1, max_tentatives + 1):
        try:
            pool = await aiomysql.create_pool(
                host=host,
                port=port,
                user=user,
                password=password,
                db=database,
                # Utilisation de DictCursor pour des résultats plus faciles à manipuler
                cursorclass=aiomysql.cursors.DictCursor,
                autocommit=True,
                maxsize=10
            )
            logger.info("Pool de connexion à la base de données établi avec succès.")
            _pool = pool
            return pool

        except aiomysql.OperationalError as e:
            logger.error(f"Tentative {tentative} - Erreur operationnelle MySQL (paramètres ou serveur) : {e}")
        except aiomysql.InterfaceError as e:
            logger.error(f"Tentative {tentative} - Erreur d'interface MySQL : {e}")
        except Exception as e:
            logger.error(f"Tentative {tentative} - Erreur inconnue lors de la connexion : {e}")

        if tentative < max_tentatives:
            logger.info("Nouvelle tentative dans 5 secondes...")
            await asyncio.sleep(5)
        else:
            logger.error("Impossible de se connecter à la base de données après plusieurs tentatives.")

    return None


async def close_db_pool():
    """Ferme le pool de connexions si il existe."""
    global _pool
    if _pool:
        _pool.close()
        await _pool.wait_closed()
        logger.info("Pool de connexions fermé.")
        _pool = None


# --- Fonction d'Exécution de Requête (celle que les services utiliseront) ---

async def execute_query(sql: str, params: Optional[Tuple] = None, fetch_one: bool = False,
                        fetch_all: bool = False) -> Any:
    """
    Exécute une requête SQL de manière asynchrone en utilisant le pool global.
    """
    if not _pool:
        # Lève une erreur si la BDD n'est pas disponible pour forcer l'arrêt du service
        raise ConnectionError("Le pool de connexions n'est pas initialisé ou a échoué.")

    async with _pool.acquire() as conn:
        async with conn.cursor() as cur:
            # cur est maintenant un DictCursor
            await cur.execute(sql, params or ())

            if fetch_one:
                return await cur.fetchone()
            if fetch_all:
                return await cur.fetchall()

            # Retourne le nombre de lignes affectées pour INSERT/UPDATE/DELETE
            return cur.rowcount