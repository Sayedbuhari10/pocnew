from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from bson.objectid import ObjectId
from werkzeug
@client_bp.route("/login")
def login_page():
    return render_template("login.html")

# -----------------------------
# LOGIN PROCESS
# -----------------------------
@client_bp.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    customer = customers.find_one({"email": email})

    if not customer or not check_password_hash(customer["password"], password):
        return render_template("login.html", error="Invalid email or password")

    return redirect(
        url_for("client.client_page", customer_id=str(customer["_id"]))
    )

# -----------------------------
# CLIENT PAGE
# -----------------------------
@client_bp.route("/client/<customer_id>")
def client_page(customer_id):
    customer = customers.find_one({"_id": ObjectId(customer_id)})
    if not customer:
        return "Unauthorized", 401

    return render_template(
        "client.html",
        customer_name=customer["name"],
        customer_id=customer_id
    )

# -----------------------------
# SHOP API (PRODUCTS + PRICE)
# -----------------------------
@client_bp.route("/api/shop/<customer_id>")
def shop(customer_id):
    customer = customers.find_one({"_id": ObjectId(customer_id)})
    if not customer:
        return jsonify({"error": "Unauthorized"}), 401

    product_list = []
    for p in products.find():
        price_doc = customer_prices.find_one({
            "customer_id": customer_id,
            "product_id": str(p["_id"])
        })
        price = price_doc["price"] if price_doc else p["base_price"]

        product_list.append({
            "id": str(p["_id"]),
            "name": p["name"],
            "price": price
        })

    return jsonify(product_list)
