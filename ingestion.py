# ingestion.py
import requests
import xml.etree.ElementTree as ET
from config import ITEMS_URL, ORDERS_SOAP_URL

# The exact SOAP envelope provided in your instructions
SOAP_XML_PAYLOAD = """<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ser="http://localhost:5000/service">
   <soapenv:Header/>
   <soapenv:Body>
      <ser:list_orders/>
   </soapenv:Body>
</soapenv:Envelope>"""

def fetch_items():
    """Fetches item data from the REST endpoint."""
    print(f"Fetching items from {ITEMS_URL}...")
    response = requests.get(ITEMS_URL, timeout=10)
    response.raise_for_status()
    return response.json()

def fetch_orders_soap():
    """Fetches order data from the SOAP endpoint and parses the XML response."""
    print(f"Fetching orders from {ORDERS_SOAP_URL}...")

    # Send the SOAP request
    response = requests.post(
        ORDERS_SOAP_URL,
        headers={"Content-Type": "text/xml"},
        data=SOAP_XML_PAYLOAD.encode('utf-8'),
        timeout=10
    )
    response.raise_for_status()

    # Parse the XML response
    root = ET.fromstring(response.content)

    # Define namespaces to help the parser find the data
    namespaces = {
        "soapenv": "http://schemas.xmlsoap.org/soap/envelope/",
        "ser": "http://localhost:5000/service"
    }

    # Locate all OrderSchema elements within the response
    orders_xml = root.findall('.//ser:OrderSchema', namespaces)

    orders = []
    for order_elem in orders_xml:
        def get_text(tag):
            elem = order_elem.find(tag, namespaces)
            return elem.text.strip() if elem is not None and elem.text else None

        order = {
            "id": get_text("ser:id"),
            "sku_id": get_text("ser:sku_id"),
            "sku_name": get_text("ser:sku_name"),
            "quantity": get_text("ser:quantity"),
            "unit_price": get_text("ser:unit_price"),
            "total_price": get_text("ser:total_price"),
            "currency": get_text("ser:currency"),
            "status": get_text("ser:status"),
            "transaction_date": get_text("ser:transaction_date")
        }
        orders.append(order)

    return orders