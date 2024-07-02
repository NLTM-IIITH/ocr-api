from motor.motor_asyncio import AsyncIOMotorClient

from .config import MONGO_DATABASE, MONGO_ENDPOINT


class Database:
	client: AsyncIOMotorClient = None

db = Database()

async def get_database() -> AsyncIOMotorClient:
	return db.client[MONGO_DATABASE]

def get_db():
	return db.client[MONGO_DATABASE]

async def connect_to_mongo():
	print('Connecting to database...')
	db.client = AsyncIOMotorClient(MONGO_ENDPOINT)
	print('Connected!')

async def close_mongo_connection():
	print('Disconnecting from database...')
	db.client.close()
	print('Disconnected!')
