import asyncio
import logging
from venv import logger
import aiomysql

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def DBConnection():
    host = input("Hôte de la base de données : ") or "localhost"
    port_str = input("Port de la base de données : ")
    if port_str:
        try:
            port = int(port_str)
        except ValueError:
            print("Port invalide. Utilisation du port par défaut 3306.")
            port = 3306
    else:
        port = 3306

    user = input("Nom d'utilisateur : ")
    password = input("Mot de passe : ")
    database = input("Nom de la base de données : ") or 'Prospectius'

    # Créer le pool de connexions
    # Tentative de connexion
    max_tentatives = 3
    for tentative in range (1, max_tentatives + 1):
        try:
            pool = await aiomysql.create_pool(
            host=host,
            port=port,
            user=user,
            password=password,
            db=database,
            autocommit=True,
            maxsize=10
            )
            logger.info("Pool de connexion à la base de données établie")
            return pool

        except aiomysql.OperationalError as e:
            logger.error(f"Tentative {tentative} - Erreur operationnelle MySQL : {e}")
        except aiomysql.InterfaceError as e:
            logger.error(f"Tentative {tentative} - Erreur d'interface MySQL : {e}")
        except Exception as e:
            logger.error(f"Tentative {tentative} - Erreur inconnue: {e}")
        if tentative < max_tentatives:
            logger.info("Nouvelle tentative dans 5 secondes...")
            await asyncio.sleep(5)
        else:
            logger.error("Impossible de se connecter à la base de données après plusieurs tentatives")


