import os
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.collection import Collection


load_dotenv()

def get_database_collections():
    uri = os.getenv("MONGODB_URI")
    client = MongoClient(uri)
    db = client.business_card_db
    users_collection: Collection = db.users
    cards_collection: Collection = db.cards
    return users_collection, cards_collection
