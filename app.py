from flask import Flask, render_template, request, redirect, url_for
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash
from db import products, customers, customer_prices
from client_routes import client_bp
from order_routes import order_bp
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import os
from admin_order import admin_order_bp




app = Flask(__name__)
app.register_blueprint(admin_order_bp)

app.register_blueprint(client_bp)
app.register_blueprint(order_bp)
# -----------------------------
# REGISTER CLIENT BLUEPRINT
# -----------------------------
@app.route("/admin")
def admin_home():
    return render_template("admin.html")


# -----------------------------
# ADMIN DASHBOARD
# -----------------------------
# -----------------------------
# ADMIN HOME
# -----------------------------


# -----------------------------
# ADMIN PRODUCTS
# -----------------------------
@app.route("/admin/products")
def admin_products():
    all_products = list(products.find())
    return render_template(
        "admin_products.html",
        products=all_products
    )


# -----------------------------
# ADMIN CUSTOMERS
# -----------------------------
@app.route("/admin/customers")
def admin_customers():
    all_customers = list(customers.find())
    return render_template(
        "admin_customers.html",
        customers=all_customers
    )


# -----------------------------
# ADMIN ORDERS
# -----------------------------
@app.route("/admin/orders")
def admin_orders():
    return render_template("admin_orders.html")


# -----------------------------
# CREATE PRODUCT
# -----------------------------
@app.route("/admin/product/create", methods=["POST"])
def create_product():
    products.insert_one({
        "name": request.form["name"],
        "base_price": float(request.form["price"])
    })
    return redirect(url_for("admin_products"))


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
    return jsonify({"message": "Product updated"})

# -----------------------------
# DELETE PRODUCT
# -----------------------------
@app.route("/admin/product/delete-multiple", methods=["POST"])
def delete_multiple_products():
    ids = request.form.getlist("product_ids")
    for pid in ids:
        products.delete_one({"_id": ObjectId(pid)})
        customer_prices.delete_many({"product_id": pid})

    return redirect(url_for("admin_products"))


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
    return redirect(url_for("admin_customers"))


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
    return redirect(url_for("admin_customers"))




@app.route("/admin/customer/edit/<id>")
def edit_customer_page(id):
    return render_template("edit_customer.html")


@app.route("/admin/customer/delete-multiple", methods=["POST"])
def delete_multiple_customers():
    ids = request.json.get("customer_ids", [])

    for cid in ids:
        customers.delete_one({"_id": ObjectId(cid)})
        customer_prices.delete_many({"customer_id": cid})
        orders.delete_many({"customer_id": cid})

    return jsonify({"message": "Customers deleted"})

# -----------------------------
# APP ENTRY POINT
# -----------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
