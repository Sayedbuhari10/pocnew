from flask import Blueprint, request, jsonify, render_template
from bson.objectid import ObjectId
from datetime import datetime
from db import orders

order_bp = Blueprint("orders", __name__)
def get_next_order_no(customer_id):
    last_order = orders.find_one(
        {"customer_id": customer_id},
        sort=[("created_at", -1)]
    )

    if not last_order:
        return 1

    return 1 if last_order["order_no"] == 100 else last_order["order_no"] + 1


# -----------------------------
# PLACE ORDER
# -----------------------------
@order_bp.route("/api/order/place", methods=["POST"])
def place_order():
    data = request.json

    order_no = get_next_order_no(data["customer_id"])

    orders.insert_one({
        "customer_id": data["customer_id"],
        "order_no": order_no,
        "items": data["items"],
        "status": "PLACED",
        "arrival_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "created_at": datetime.utcnow()
    })

    return jsonify({"message": "Order placed"})

# -----------------------------
# GET ORDERS (ACTIVE / COMPLETED)
# -----------------------------


@order_bp.route("/api/orders/<customer_id>/<order_type>")
def get_orders(customer_id, order_type):
    query = {"customer_id": customer_id}

    # ACTIVE = everything except COMPLETED
    if order_type == "active":
        query["status"] = {"$ne": "COMPLETED"}
    else:
        query["status"] = "COMPLETED"

    result = []
    for o in orders.find(query).sort("created_at", -1):
        result.append({
            "id": str(o["_id"]),
            "order_no": o["order_no"],
            "status": o["status"],
            "arrival_date": o.get("arrival_date"),
            "items": o["items"],
            "created_at": o["created_at"]
        })

    return jsonify(result)


# -----------------------------
# DELETE ORDER (PLACED ONLY)
# -----------------------------
@order_bp.route("/api/order/delete/<order_id>", methods=["DELETE"])
def delete_order(order_id):
    orders.delete_one({
        "_id": ObjectId(order_id),
        "status": "PLACED"
    })
    return jsonify({"message": "Order deleted"})


# -----------------------------
# INVOICE VIEW
# -----------------------------
@order_bp.route("/invoice/<order_id>")
def invoice(order_id):
    order = orders.find_one({
        "_id": ObjectId(order_id),
        "status": "DELIVERED"
    })

    if not order:
        return "Invoice not available", 403

    return render_template("invoice.html", order=order)



@order_bp.route("/api/order/update/<order_id>", methods=["POST"])
def update_order(order_id):
    data = request.json
    items = data.get("items", [])

    # If user removed all items → delete order
    if not items:
        orders.delete_one({
            "_id": ObjectId(order_id),
            "status": "PLACED"
        })
        return jsonify({"message": "Order deleted"})

    # Update items only if order is PLACED
    orders.update_one(
        {"_id": ObjectId(order_id), "status": "PLACED"},
        {"$set": {"items": items}}
    )

    return jsonify({"message": "Order updated"})

