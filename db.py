from pymongo import MongoClient
import os

MONGO_URI = os.environ.get("MONGO_URI","mongodb+srv://pocuser:PocUser123@cluster0.jnzsyfy.mongodb.net/?appName=Cluster0")

client = MongoClient(MONGO_URI)
db = client["poc_db"]

products = db["products"]
customers = db["customers"]
customer_prices = db["customer_prices"]
orders = db["orders"]
invoices = db["invoices"]
notifications = db["notifications"]