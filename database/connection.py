from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    client: AsyncIOMotorClient = None
    database = None

db = Database()

async def get_database():
    return db.database

async def connect_to_mongo():
    """Crear conexión a MongoDB Atlas"""
    mongodb_url = os.getenv("MONGODB_URL")
    if not mongodb_url:
        raise Exception("MONGODB_URL no está configurada en las variables de entorno")

    db.client = AsyncIOMotorClient(
        mongodb_url,
        server_api=ServerApi('1')
    )

    db_name = os.getenv("DATABASE_NAME", "mnemosine")
    db.database = db.client[db_name]

    print(f"Conectado a MongoDB Atlas - Base de datos: {db_name}")

async def close_mongo_connection():
    """Cerrar conexión a MongoDB"""
    if db.client:
        db.client.close()
        print("Conexión a MongoDB cerrada")

# Funciones para obtener colecciones
async def get_users_collection():
    database = await get_database()
    return database.users

async def get_armarios_collection():
    database = await get_database()
    return database.armarios

async def get_cajas_collection():
    database = await get_database()
    return database.cajas

async def get_cajitas_collection():
    database = await get_database()
    return database.cajitas

async def get_notas_collection():
    database = await get_database()
    return database.notas