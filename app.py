from flask import Flask, render_template, request, redirect, url_for
from bson.objectid import ObjectId
from db import products, customers, customer_prices
from flask import Flask, render_template, jsonify
from pymongo import MongoClient
import os


app = Flask(__name__)

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
# CREATE CUSTOMER
# -----------------------------
@app.route("/admin/customer/create", methods=["POST"])
def create_customer():
    customers.insert_one({
        "name": request.form["name"],
        "email": request.form["email"]
    })
    return redirect(url_for("admin_dashboard"))

# -----------------------------
# SET CUSTOMER-SPECIFIC PRICE
# -----------------------------
@app.route("/admin/price/set", methods=["POST"])
def set_customer_price():
    customer_id = request.form["customer_id"]
    product_id = request.form["product_id"]
    price = float(request.form["price"])

    customer_prices.update_one(
        {
            "customer_id": customer_id,
            "product_id": product_id
        },
        {"$set": {"price": price}},
        upsert=True
    )
    return redirect(url_for("admin_dashboard"))
@app.route("/login")
def login_page():
    return render_template("login.html")
@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    name = request.form["name"]

    customer = customers.find_one({
        "email": email,
        "name": name
    })

    if not customer:
        return render_template(
            "login.html",
            error="Invalid name or email"
        )

    # Redirect with customer_id (stateless)
    return redirect(
        url_for("client_page", customer_id=str(customer["_id"]))
    )




# SAME MongoDB connection

@app.route("/client/<customer_id>")
def client_page(customer_id):
    customer = customers.find_one({"_id": ObjectId(customer_id)})

    if not customer:
        return "Unauthorized", 401

    return render_template(
        "client.html",
        customer_name=customer["name"],
        customer_id=customer_id
    )

@app.route("/api/product-names/<customer_id>")
def product_names(customer_id):
    customer = customers.find_one({"_id": ObjectId(customer_id)})

    if not customer:
        return jsonify({"error": "Unauthorized"}), 401

    docs = products.find({}, {"_id": 0, "name": 1})
    names = [d["name"] for d in docs]
    return jsonify(names)




if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


