from flask import Blueprint, jsonify, request
from bson.objectid import ObjectId
from datetime import datetime

from db import orders, customers, invoices


# Admin Orders Blueprint
admin_order_bp = Blueprint("admin_orders", __name__)

# -------------------------------------------------
# GET ALL PLACED ORDERS (ADMIN)
# -------------------------------------------------


# -----------------------------
# MARK AS DELIVERED
# -----------------------------
@admin_order_bp.route("/admin/api/order/deliver/<order_id>", methods=["POST"])
def mark_as_delivered(order_id):
    orders.update_one(
        {"_id": ObjectId(order_id), "status": "ACCEPTED"},
        {
            "$set": {
                "status": "DELIVERED",
                "delivered_at": datetime.utcnow()
            }
        }
    )
    return jsonify({"message": "Order delivered"})


@admin_order_bp.route("/admin/api/orders/placed")
def get_placed_orders():
    result = []

    for o in orders.find({"status": "PLACED"}):
        customer = customers.find_one({"_id": ObjectId(o["customer_id"])})

        result.append({
            "id": str(o["_id"]),
            "order_no": o.get("order_no"),
            "customer_name": customer["name"] if customer else "Unknown",
            "items": o["items"],
            "created_at": o["created_at"]
        })

    return jsonify(result)


# -------------------------------------------------
# CANCEL ORDER (ADMIN)
# -------------------------------------------------
@admin_order_bp.route("/admin/api/order/cancel/<order_id>", methods=["POST"])
def cancel_order(order_id):
    orders.update_one(
        {"_id": ObjectId(order_id), "status": "PLACED"},
        {"$set": {"status": "CANCELLED"}}
    )

    return jsonify({"message": "Order cancelled"})


# -------------------------------------------------
# ACCEPT ORDER (ADMIN)
# -------------------------------------------------
#@admin_order_bp.route("/admin/api/order/accept/<order_id>", methods=["POST"])
@admin_order_bp.route("/admin/api/order/accept/<order_id>", methods=["POST"])
def accept_order(order_id):
    data = request.get_json()
    delivery_date = data.get("arrival_date")  # ✅ FIX

    orders.update_one(
        {"_id": ObjectId(order_id), "status": "PLACED"},
        {
            "$set": {
                "status": "ACCEPTED",
                "arrival_date": delivery_date,
                "accepted_at": datetime.utcnow()
            }
        }
    )

    return jsonify({"message": "Order accepted"})

#accepted orders 
@admin_order_bp.route("/admin/api/orders/accepted")
def get_accepted_orders():
    result = []
    for o in orders.find({"status": "ACCEPTED"}):
        customer = customers.find_one({"_id": ObjectId(o["customer_id"])})
        result.append({
            "id": str(o["_id"]),
            "order_no": o["order_no"],
            "customer_name": customer["name"],
            "arrival_date": o["arrival_date"]
        })
    return jsonify(result)

@admin_order_bp.route("/admin/api/order/edit-delivery/<order_id>", methods=["POST"])
def edit_delivery_date(order_id):
    new_date = request.json.get("arrival_date")

    orders.update_one(
        {"_id": ObjectId(order_id), "status": "ACCEPTED"},
        {"$set": {"arrival_date": new_date}}
    )

    return jsonify({"message": "Delivery date updated"})

#deliverd orders
@admin_order_bp.route("/admin/api/orders/delivered")
def get_delivered_orders():
    result = []
    for o in orders.find({"status": "DELIVERED"}):
        customer = customers.find_one({"_id": ObjectId(o["customer_id"])})
        result.append({
            "id": str(o["_id"]),
            "order_no": o["order_no"],
            "customer_name": customer["name"],
            "invoice_sent": o.get("invoice_sent", False)
        })
    return jsonify(result)
#@admin_order_bp.route("/admin/api/invoice/send/<order_id>", methods=["POST"])
@admin_order_bp.route("/admin/api/invoice/send/<order_id>", methods=["POST"])
def send_invoice(order_id):
    order = orders.find_one({
        "_id": ObjectId(order_id),
        "status": "DELIVERED"
    })

    if not order:
        return jsonify({"error": "Order not delivered"}), 400

    invoice = {
        "order_id": order["_id"],
        "customer_id": order["customer_id"],
        "items": order["items"],
        "total_amount": sum(i["price"] * i["quantity"] for i in order["items"]),
        "sent_at": datetime.utcnow(),
        "paid": False
    }

    invoice_id = invoices.insert_one(invoice).inserted_id

    orders.update_one(
        {"_id": order["_id"]},
        {"$set": {
            "invoice_id": invoice_id,
            "invoice_sent": True
        }}
    )

    return jsonify({"message": "Invoice created"})



@admin_order_bp.route("/admin/api/invoice/paid/<invoice_id>", methods=["POST"])
def mark_invoice_paid(invoice_id):
    invoice = invoices.find_one({"_id": ObjectId(invoice_id)})
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404

    invoices.update_one(
        {"_id": invoice["_id"]},
        {"$set": {"paid": True}}
    )

    orders.update_one(
        {"_id": invoice["order_id"]},
        {"$set": {"status": "COMPLETED"}}
    )

    return jsonify({"message": "Invoice paid"})

@admin_order_bp.route("/admin/api/order/<order_id>")
def get_single_order(order_id):
    order = orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        return jsonify({"error": "Order not found"}), 404

    customer = customers.find_one({"_id": ObjectId(order["customer_id"])})

    return jsonify({
        "id": str(order["_id"]),
        "order_no": order["order_no"],
        "customer_name": customer["name"],
        "items": order["items"],
        "created_at": order["created_at"],
        "accepted_at": order.get("accepted_at"),
        "delivered_at": order.get("delivered_at"),
        "arrival_date": order.get("arrival_date"),
        "invoice_sent": order.get("invoice_sent", False),
        "invoice_id": str(order["invoice_id"]) if order.get("invoice_id") else None
    })
    
    
    

@admin_order_bp.route("/admin/api/invoice/by-order/<order_id>")
def get_invoice_by_order(order_id):
    invoice = invoices.find_one({"order_id": ObjectId(order_id)})
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404

    return jsonify({
        "items": invoice["items"],
        "total": invoice["total_amount"],
        "sent_at": invoice["sent_at"],
        "paid": invoice["paid"]
    })
    
    
@admin_order_bp.route("/admin/api/orders/completed")
def get_completed_orders():
    result = []

    for o in orders.find({"status": "COMPLETED"}):
        customer = customers.find_one({"_id": ObjectId(o["customer_id"])})

        result.append({
            "id": str(o["_id"]),
            "order_no": o["order_no"],
            "customer_name": customer["name"],
        })

    return jsonify(result)


@admin_order_bp.route("/admin/api/order/details/<order_id>")
def get_order_details(order_id):
    order = orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        return jsonify({"error": "Order not found"}), 404

    return jsonify({
        "order_no": order["order_no"],
        "items": order["items"],
        "created_at": order["created_at"],
        "accepted_at": order.get("accepted_at"),
        "delivered_at": order.get("delivered_at"),
        "completed_at": order.get("completed_at"),
    })








