from pymongo import MongoClient
import os

MONGO_URI = os.environ.get("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["poc_db"]

products = db["products"]
customers = db["customers"]
customer_prices = db["customer_prices"]
orders = db["orders"]
