"""
Really Expensive Stuff for Trillionaires – Fake e-commerce API
Updated to include SOAP /list_orders endpoint
"""
import random
from decimal import Decimal as PyDecimal
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, Response
from faker import Faker
from spyne import (
    Application,
    rpc,
    ServiceBase,
    Integer,
    Unicode,
    Decimal as SpyneDecimal,
    Array,
    ComplexModel,
)
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
# --------------------------------------------------------------------------- #
# 1. Generate fake SKUs (100 items)
# --------------------------------------------------------------------------- #
fake = Faker()
SKU_LIST = []
current_time = datetime.now()
for i in range(1, 101):
    created_date = current_time - timedelta(days=random.randint(1, 365))
    sku = {
        "id": i,
        "name": f"{fake.word().capitalize()} {fake.word().capitalize()}",
        "description": fake.sentence(nb_words=12),
        "price": round(random.uniform(100_000, 10_000_000), 2),
        "currency": "USD",
        "quantity_on_hand": random.randint(1, 50),
        "created": created_date.isoformat()
    }
    SKU_LIST.append(sku)
SKU_BY_ID = {sku["id"]: sku for sku in SKU_LIST}
# --------------------------------------------------------------------------- #
# 2. Flask app (REST endpoints)
# --------------------------------------------------------------------------- #
app = Flask(__name__)
@app.route("/items", methods=["GET"])
def get_items():
    return jsonify(SKU_LIST)
@app.route("/order", methods=["POST"])
def order_item():
    data = request.get_json()
    if not data or "id" not in data or "quantity" not in data:
        return jsonify({"error": "Missing required fields"}), 400
    sku_id = int(data["id"])
    qty_requested = int(data["quantity"])
    currency_req = data.get("currency", "USD")
    sku = SKU_BY_ID.get(sku_id)
    if not sku:
        return jsonify({"error": f"SKU id {sku_id} not found"}), 404
    result = {
        "id": sku["id"],
        "name": sku["name"],
        "description": sku["description"],
        "price_per_unit": f"{sku['price']} {sku['currency']}",
        "quantity_requested": qty_requested,
        "total_price": round(sku["price"] * qty_requested, 2),
        "currency": currency_req,
        "created": sku["created"],
        "transaction_date": datetime.now().isoformat()
    }
    return jsonify(result)
@app.route("/orders", methods=["GET"])
def get_orders():
    orders = []
    current_time = datetime.now()
    two_months_ago = current_time - timedelta(days=60)
    seconds_in_range = int((current_time - two_months_ago).total_seconds())
    for i in range(100):
        sku = random.choice(SKU_LIST)
        qty = random.randint(1, 10)
        random_seconds_offset = random.randint(0, seconds_in_range)
        txn_date = current_time - timedelta(seconds=random_seconds_offset)

        order = {
            "id": random.randint(100000, 999999),
            "sku_id": sku["id"],
            "sku_name": sku["name"],
            "quantity": qty,
            "unit_price": sku["price"],
            "total_price": round(sku["price"] * qty, 2),
            "currency": "USD",
            "status": random.choice(["completed", "pending", "shipped", "failed"]),
            "transaction_date": txn_date.isoformat()
        }
        orders.append(order)
    return jsonify(orders)
# --------------------------------------------------------------------------- #
# 3. Spyne SOAP service
# --------------------------------------------------------------------------- #
class SKUSchema(ComplexModel):
    id = Integer
    name = Unicode
    description = Unicode
    price_per_unit = SpyneDecimal
    currency = Unicode
    quantity_on_hand = Integer
    created = Unicode
# 🆕 NEW: Schema for SOAP order responses
class OrderSchema(ComplexModel):
    id = Integer
    sku_id = Integer
    sku_name = Unicode
    quantity = Integer
    unit_price = SpyneDecimal
    total_price = SpyneDecimal
    currency = Unicode
    status = Unicode
    transaction_date = Unicode
class OrderResponse(ComplexModel):
    id = Integer
    name = Unicode
    description = Unicode
    total_price = SpyneDecimal
    currency = Unicode
    quantity_requested = Integer
    created = Unicode
    transaction_date = Unicode
class ECommerceService(ServiceBase):
    @rpc(_returns=Array(SKUSchema))
    def list_items(ctx):
        return [
            SKUSchema(
                id=sku["id"],
                name=sku["name"],
                description=sku["description"],
                price_per_unit=PyDecimal(str(sku["price"])),
                currency=sku["currency"],
                quantity_on_hand=sku["quantity_on_hand"],
                created=sku["created"]
            )
            for sku in SKU_LIST
        ]
    # 🆕 NEW: SOAP endpoint to list orders
    @rpc(_returns=Array(OrderSchema))
    def list_orders(ctx):
        """SOAP operation – return a list of prefilled fake orders."""
        orders = []
        current_time = datetime.now()
        two_months_ago = current_time - timedelta(days=60)
        seconds_in_range = int((current_time - two_months_ago).total_seconds())
        for _ in range(100):
            sku = random.choice(SKU_LIST)
            qty = random.randint(1, 10)
            random_seconds_offset = random.randint(0, seconds_in_range)
            txn_date = current_time - timedelta(seconds=random_seconds_offset)
            orders.append(OrderSchema(
                id=random.randint(100000, 999999),
                sku_id=sku["id"],
                sku_name=sku["name"],
                quantity=qty,
                unit_price=PyDecimal(str(sku["price"])),
                total_price=PyDecimal(str(sku["price"] * qty)),
                currency="USD",
                status=random.choice(["completed", "pending", "shipped", "failed"]),
                transaction_date=txn_date.isoformat()
            ))
        return orders
    @rpc(Integer, Integer, Unicode, _returns=OrderResponse)
    def request_item(ctx, item_id, qty_requested, currency_req):
        sku = SKU_BY_ID.get(item_id)
        if not sku:
            raise ValueError(f"SKU id {item_id} not found")
        total_price = round(sku["price"] * qty_requested, 2)
        txn_date = datetime.now().isoformat()
        return OrderResponse(
            id=sku["id"],
            name=sku["name"],
            description=sku["description"],
            total_price=PyDecimal(str(total_price)),
            currency=currency_req,
            quantity_requested=qty_requested,
            created=sku["created"],
            transaction_date=txn_date
        )
soap_app = Application(
    [ECommerceService],
    tns="http://localhost:5000/service",
    in_protocol=Soap11(validator='lxml'),
    out_protocol=Soap11()
)
wsgi_soap = WsgiApplication(soap_app)
@app.route("/service", methods=["GET", "POST"])
def soap_service():
    status_code = 200
    headers = {}
    def start_response(status, response_headers):
        nonlocal status_code, headers
        status_code = int(status.split(' ')[0])
        headers = dict(response_headers)
    body_iter = wsgi_soap(request.environ, start_response)
    body = b''.join(body_iter).decode()
    return Response(body, status=status_code, headers=headers)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)