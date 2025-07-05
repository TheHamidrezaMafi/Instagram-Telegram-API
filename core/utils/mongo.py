from decouple import config
from pymongo import MongoClient
from pymongo import ASCENDING


MONGO_URI = config("ATLAS_URI")
MONGO_DB_NAME = config("DB_NAME")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]

users_collection = db['user_login']
chats_collection = db['user_chats']

db['user_chats'].create_index([('telegram_id', ASCENDING), ('thread_id', ASCENDING)], unique=True)

print("MongoDB connection established.")