from flask import Flask, render_template, request, redirect, url_for
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash
from db import products, customers, customer_prices
from client_routes import client_bp
from order_routes import order_bp
import os

app = Flask(__name__)

app.register_blueprint(client_bp)
app.register_blueprint(order_bp)
# -----------------------------
# REGISTER CLIENT BLUEPRINT
# -----------------------------


# -----------------------------
# ADMIN DASHBOARD
# -----------------------------
@app.route("/admin")
def admin_dashboard():
    all_products = list(products.find())
    all_customers = list(customers.find())
    return render_template(
        "admin.html",
        products=all_products,
        customers=all_customers
    )

# -----------------------------
# CREATE PRODUCT
# -----------------------------
@app.route("/admin/product/create", methods=["POST"])
def create_product():
    products.insert_one({
        "name": request.form["name"],
        "base_price": float(request.form["price"])
    })
    return redirect(url_for("admin_dashboard"))

# -----------------------------
# UPDATE PRODUCT
# -----------------------------
@app.route("/admin/product/update/<id>", methods=["POST"])
def update_product(id):
    products.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "name": request.form["name"],
            "base_price": float(request.form["price"])
        }}
    )
    return redirect(url_for("admin_dashboard"))

# -----------------------------
# DELETE PRODUCT
# -----------------------------
@app.route("/admin/product/delete/<id>")
def delete_product(id):
    products.delete_one({"_id": ObjectId(id)})
    customer_prices.delete_many({"product_id": id})
    return redirect(url_for("admin_dashboard"))

# -----------------------------
# CREATE CUSTOMER (ADMIN SETS PASSWORD)
# -----------------------------
@app.route("/admin/customer/create", methods=["POST"])
def create_customer():
    customers.insert_one({
        "name": request.form["name"],
        "email": request.form["email"],
        "password": generate_password_hash(request.form["password"])
    })
    return redirect(url_for("admin_dashboard"))

# -----------------------------
# SET CUSTOMER-SPECIFIC PRICE
# -----------------------------
@app.route("/admin/price/set", methods=["POST"])
def set_customer_price():
    customer_prices.update_one(
        {
            "customer_id": request.form["customer_id"],
            "product_id": request.form["product_id"]
        },
        {"$set": {"price": float(request.form["price"])}},
        upsert=True
    )
    return redirect(url_for("admin_dashboard"))

# -----------------------------
# APP ENTRY POINT
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
