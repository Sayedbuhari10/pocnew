from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from db import products, customers, customer_prices,notifications,orders


from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import os

# ✅ DEFINE BLUEPRINT FIRST
client_bp = Blueprint("client", __name__)
#login page--------------------------------------------------------------------------------
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
# ---------------------------------------------------------------------------------------------
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
    "price": price,
    "image": f"/static/{p['img']}" if p.get("img") else "/static/default.jpg"
})



    return jsonify(product_list)



#clinet notifications------------------------------------------------------------------------------------------
@client_bp.route("/client/notifications/<customer_id>")
def get_notification_page(customer_id):
    return render_template(
        "client_notifications.html",
        customer_id=customer_id
    )
    

@client_bp.route("/client/api/notifications/<customer_id>")
def get_client_notifications(customer_id):
    result = []

    for n in notifications.find({
        "target": "CLIENT",
        "customer_id": ObjectId(customer_id)
    }):
        order = orders.find_one({"_id": ObjectId(n["order_id"])})

        if not order:
            continue

        result.append({
            "notification_id": str(n["_id"]),
            "order_id": str(order["_id"]),
            "order_no": order["order_no"],
            "state": n["state"],
            "arrival_date": order.get("arrival_date"),
            "invoice_id": str(order.get("invoice_id")) if order.get("invoice_id") else None
        })

    return jsonify(result)



#client profile-----------------------------------------------------------------------------------------
@client_bp.route("/client/api/profile/<customer_id>")
def get_client_profile(customer_id):
    customer = customers.find_one({"_id": ObjectId(customer_id)})

    if not customer:
        return jsonify({"error": "Client not found"}), 404

    return jsonify({
        "name": customer["name"],
        "email": customer["email"]
    })


@client_bp.route("/client/api/profile/orders/completed/<customer_id>")
def get_client_completed_orders(customer_id):
    result = []

    for o in orders.find({
        "customer_id": customer_id,
        "status": "COMPLETED"
    }).sort("completed_at", -1):

        total_items = sum(i.get("quantity", 0) for i in o.get("items", []))

        result.append({
            "order_id": str(o["_id"]),
            "order_no": o.get("order_no"),
            "completed_at": o.get("completed_at"),
            "total_items": total_items
        })

    return jsonify(result)


