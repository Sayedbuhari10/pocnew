from datetime import datetime
from bson.objectid import ObjectId
from db import notifications

def create_notification(order_id, state, target, cu_id=None):
    order_oid = ObjectId(order_id)

    # 🔴 STEP 1: DELETE EXISTING NOTIFICATIONS FOR THIS ORDER
    notifications.delete_many({
        "order_id": order_oid
    })

    # 🔴 STEP 2: CREATE NEW NOTIFICATION
    doc = {
        "order_id": order_oid,
        "state": state,
        "target": target,
        "created_at": datetime.utcnow()
    }

    if target == "CLIENT":
        doc["customer_id"] = ObjectId(cu_id)

    notifications.insert_one(doc)
def delete_notification(order_id,state):
    notifications.delete_one({"order_id": ObjectId(order_id),"state":state})

