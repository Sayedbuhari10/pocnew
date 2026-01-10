from flask import Blueprint, jsonify, request
from bson.objectid import ObjectId
from datetime import datetime

from db import orders, customers, invoices
from notification_service import create_notification,delete_notification

# Admin Orders Blueprint
admin_order_bp = Blueprint("admin_orders", __name__)

# -------------------------------------------------
# GET ALL PLACED ORDERS (ADMIN)
# ---------------------------------------------------------------------------------------------------------------


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

@admin_order_bp.route("/admin/api/order/save-delivery/<order_id>", methods=["POST"])
def save_delivery_date(order_id):
    data = request.get_json()
    delivery_date = data.get("arrival_date")

    orders.update_one(
        {"_id": ObjectId(order_id), "status": "PLACED"},
        {"$set": {"arrival_date": delivery_date}}
    )

    return jsonify({"message": "Delivery date saved"})


# order details from the total order
@admin_order_bp.route("/admin/api/order/details/<order_id>")
def get_order_details(order_id):
    order = orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        return jsonify({"error": "Order not found"}), 404

    return jsonify({
        "order_no": order["order_no"],
        "items": order["items"],
        "customer_name": customers.find_one({"_id": ObjectId(order["customer_id"])})["name"], # Fetch customer name
        "created_at": order["created_at"],
        "accepted_at": order.get("accepted_at"),
        "delivered_at": order.get("delivered_at"),
        "completed_at": order.get("completed_at"),
    })



# -------------------------------------------------
# ACCEPT ORDER (ADMIN)
# -------------------------------------------------
#@admin_order_bp.route("/admin/api/order/accept/<order_id>", methods=["POST"])
@admin_order_bp.route("/admin/api/order/accept/<order_id>", methods=["POST"])
def accept_order(order_id):
    data = request.get_json()
    delivery_date = data.get("arrival_date")

    order = orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        return jsonify({"error": "Order not found"}), 404

    orders.update_one(
        {"_id": ObjectId(order_id), "status": "PLACED"},
        {"$set": {
            "status": "ACCEPTED",
            "arrival_date": delivery_date,
            "accepted_at": datetime.utcnow()
        }}
    )

    # ✅ CLIENT NOTIFICATION
    create_notification(
        order["_id"],
        "ACCEPTED",
        "CLIENT",
        order["customer_id"]
    )

    return jsonify({"message": "Order accepted"})

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


#accepted orders ------------------------------------------------------------------------------
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
#edit deleivery---------------------------
@admin_order_bp.route("/admin/api/order/edit-delivery/<order_id>", methods=["POST"])
def edit_delivery_date(order_id):
    new_date = request.json.get("arrival_date")

    orders.update_one(
        {"_id": ObjectId(order_id), "status": "ACCEPTED"},
        {"$set": {"arrival_date": new_date}}
    )

    return jsonify({"message": "Delivery date updated"})


# -----------------------------
# MARK AS DELIVERED
# -----------------------------


@admin_order_bp.route("/admin/api/order/deliver/<order_id>", methods=["POST"])
def mark_as_delivered(order_id):

    order = orders.find_one({
        "_id": ObjectId(order_id),
        "status": "ACCEPTED"
    })

    if not order:
        return jsonify({"error": "Invalid order state"}), 400

    orders.update_one(
        {"_id": ObjectId(order_id)},
        {
            "$set": {
                "status": "DELIVERED",
                "delivered_at": datetime.utcnow()
            }
        }
    )

    # ✅ CREATE ADMIN NOTIFICATION FOR DELIVERED ORDER
    create_notification(
        order["_id"],
        "DELIVERED",
        "ADMIN",
        order["customer_id"]
    )

    return jsonify({"message": "Order delivered"})










#deliverd orders--------------------------------------------------------------------------------
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


#send invoice ----------------

@admin_order_bp.route("/admin/api/invoice/send/<order_id>", methods=["POST"])
def send_invoice(order_id):

    order = orders.find_one({
        "_id": ObjectId(order_id),
        "status": "DELIVERED"
    })

    if not order:
        return jsonify({"error": "Order not delivered"}), 400

    normalized_items = []
    total_amount = 0

    for item in order["items"]:
        price = item.get("price", 0)
        quantity = item.get("quantity", 0)

        item_total = price * quantity
        total_amount += item_total

        normalized_items.append({
            "name": item["name"],
            "price": price,               # ✅ GUARANTEED
            "quantity": quantity,
            "total": item_total
        })

    invoice = {
        "order_id": order["_id"],
        "customer_id": order["customer_id"],
        "items": normalized_items,       # ✅ CLEAN DATA
        "total_amount": total_amount,
        "created_at": datetime.utcnow(),
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

    create_notification(
        order["_id"],
        "INVOICE",
        "CLIENT",
        order["customer_id"]
    )

    return jsonify({"message": "Invoice sent"})

#ivoice  paying invoice from invoce page -update----------
@admin_order_bp.route("/admin/api/invoice/paid/<invoice_id>", methods=["POST"])
def mark_invoice_paid(invoice_id):
    invoice = invoices.find_one({"_id": ObjectId(invoice_id)})
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404

    paid_time = datetime.utcnow()

    invoices.update_one(
        {"_id": invoice["_id"]},
        {"$set": {"paid": True, "paid_at": paid_time}}
    )

    orders.update_one(
        {"_id": invoice["order_id"]},
        {"$set": {
            "status": "COMPLETED",
            "completed_at": paid_time
        }}
    )

    return jsonify({"message": "Invoice paid"})

    
    
# get invoice ---------------------
@admin_order_bp.route("/admin/api/invoice/by-order/<order_id>")
def get_invoice_by_order(order_id):

    invoice = invoices.find_one({"order_id": ObjectId(order_id)})
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404

    return jsonify({
        "items": invoice["items"],              # ✅ already normalized
        "total": invoice["total_amount"],
        "paid": invoice.get("paid", False),
        "paid_at": invoice.get("paid_at"),
        "created_at": invoice.get("created_at")
    })

    
#view details --------
@admin_order_bp.route("/admin/api/order/<order_id>")
def get_single_order(order_id):
    order = orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        return jsonify({"error": "Order not found"}), 404

    customer = customers.find_one({"_id": ObjectId(order["customer_id"])})

    invoice = None
    if order.get("invoice_id"):
        invoice = invoices.find_one({"_id": order["invoice_id"]})

    items = []
    grand_total = 0

    for i in order.get("items", []):
        price = i.get("price", 0)
        qty = i.get("quantity", 0)
        item_total = price * qty
        grand_total += item_total

        items.append({
            "name": i["name"],
            "quantity": qty,
            "price": price,
            "total": item_total
        })

    return jsonify({
        "order_no": order["order_no"],
        "customer_name": customer["name"] if customer else "Unknown",
        "items": items,
        "grand_total": grand_total,

        "created_at": order.get("created_at"),
        "accepted_at": order.get("accepted_at"),
        "delivered_at": order.get("delivered_at"),
        "invoice_paid_at": invoice.get("paid_at") if invoice else None
    })

    
#completed orders------------------------------------------------------------------------------------  
@admin_order_bp.route("/admin/api/orders/completed")
def get_completed_orders():
    result = []

    for o in orders.find({"status": "COMPLETED"}):
        customer = customers.find_one({"_id": ObjectId(o["customer_id"])})

        result.append({
            "id": str(o["_id"]),
            "order_no": o["order_no"],
            "customer_name": customer["name"] if customer else "Unknown",
            "status": o["status"]          # ✅ ADD THIS
        })

    return jsonify(result)








