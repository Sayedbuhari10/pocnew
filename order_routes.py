from flask import Blueprint, request, jsonify, render_template
from bson.objectid import ObjectId
from datetime import datetime
from db import orders, invoices


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
from datetime import datetime

@order_bp.route("/api/order/place", methods=["POST"])
def place_order():
    data = request.json
    customer_id = data["customer_id"]



    
    order_no = get_next_order_no(customer_id)

    orders.insert_one({
        "order_no": order_no,
        "customer_id": customer_id,

        "items": data["items"],

        "status": "PLACED",

        "created_at": datetime.utcnow(),

        "accepted_at": None,
        "arrival_date": None,
        "delivered_at": None,

        "invoice_sent": False,
        "invoice_id": None
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
    "created_at": o["created_at"],
    "invoice_sent": o.get("invoice_sent", False)   # ✅ ADD THIS
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
#@order_bp.route("/invoice/<order_id>")

@order_bp.route("/invoice/<order_id>")
def invoice_page(order_id):
    print("INVOICE ROUTE HIT")

    order = orders.find_one({"_id": ObjectId(order_id)})
    if not order:
        return "Order not found", 404

    invoice_id = order.get("invoice_id")
    if not invoice_id:
        return "Invoice not available", 403

    invoice = invoices.find_one({"_id": invoice_id})
    if not invoice:
        return "Invoice not found", 404

    return render_template(
        "invoice.html",
        order=order,
        invoice=invoice
    )


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



@order_bp.route("/api/invoice/pay/<invoice_id>", methods=["POST"])
def pay_invoice(invoice_id):
    invoices.update_one(
        {"_id": ObjectId(invoice_id)},
        {
            "$set": {
                "paid": True,
                "paid_at": datetime.utcnow()
            }
        }
    )

    orders.update_one(
        {"invoice_id": ObjectId(invoice_id)},
        {
            "$set": {
                "status": "COMPLETED",
                "completed_at": datetime.utcnow()
            }
        }
    )

    return jsonify({"message": "Invoice paid"})