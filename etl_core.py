# etl_core.py
import hashlib
import json
import datetime
from ingestion import fetch_items, fetch_orders_soap
from models import Session, UnifiedRecord

# Code for this unified site; prepended to every sku_id during transformation
SKU_PREFIX = "SPTBG-"

def normalize_item(item):
    return {
        "source_type": "items",
        # CHANGED: integer from the source API -> string with prefix, e.g. 1 -> "SPTBG-1"
        "sku_id": SKU_PREFIX + str(item.get("id")),
        "sku_name": item.get("name"),
        "quantity": item.get("quantity_on_hand"),
        "unit_price": float(item.get("price")),
        "total_price": float(item.get("price")),
        "currency": item.get("currency"),
        "status": "available",
        "transaction_date": datetime.datetime.fromisoformat(item.get("created")),
        "raw_payload_hash": hashlib.md5(json.dumps(item, sort_keys=True).encode()).hexdigest()
    }

def normalize_order(order):
    # Convert string values from XML into proper data types
    try:
        txn_date = datetime.datetime.fromisoformat(order.get("transaction_date", "")) if order.get("transaction_date") else None
    except ValueError:
        txn_date = None

    return {
        "source_type": "orders",
        # CHANGED: XML text -> int (cleans it) -> string with prefix, e.g. "74" -> "SPTBG-74"
        "sku_id": SKU_PREFIX + str(int(order.get("sku_id", 0))),
        "sku_name": order.get("sku_name", ""),
        "quantity": int(order.get("quantity", 0)),
        "unit_price": float(order.get("unit_price", 0.0)),
        "total_price": float(order.get("total_price", 0.0)),
        "currency": order.get("currency", "USD"),
        "status": order.get("status", "unknown"),
        "transaction_date": txn_date,
        "raw_payload_hash": hashlib.md5(json.dumps(order, sort_keys=True).encode()).hexdigest()
    }

def load_to_db(records):
    session = Session()
    try:
        for payload in records:
            record = UnifiedRecord(**payload)
            session.add(record)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Database load failed: {e}")
    finally:
        session.close()

def run_etl():
    print("--- Starting ETL Pipeline ---")

    # 1. Ingest Items (JSON)
    items = fetch_items()
    item_records = [normalize_item(i) for i in items]

    # 2. Ingest Orders (SOAP/XML)
    orders = fetch_orders_soap()
    order_records = [normalize_order(o) for o in orders]

    # 3. Load to Database
    print("Loading to relational model...")
    load_to_db(item_records + order_records)
    print("--- ETL Pipeline Complete ---\n")