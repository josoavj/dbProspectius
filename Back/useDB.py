import asyncio
from Back.settingsDB import DBConnection

# Exemple d'utilisation de la base de données

async def main():
    pool = await DBConnection()
    if pool :
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('SELECT NOW();')
                result = await cursor.fetchone()
                print("Heure actuelle DB: ", result[0])
        pool.close()
        await pool.wait_closed()

asyncio.run(main())
