from pymongo import MongoClient
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List
import re
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
# MongoDB Connection
client = MongoClient(MONGO_URI)
db = client["chainexdevdb"]

# --- Stock Quantity Search ---
class ActionStockQuantitySearch(Action):
    def name(self): return "action_stock_quantity_search"
    
    def run(self, dispatcher, tracker, domain):
        item_name = tracker.get_slot("item_name")
        warehouse_name = tracker.get_slot("warehouse_name")
        
        if not item_name:
            dispatcher.utter_message("Please specify the item name to check stock.")
            return []
        
        try:
            # Search for items by name (case-insensitive)
            items = list(db["items"].find({
                "itemName": {"$regex": f".*{re.escape(item_name)}.*", "$options": "i"},
                "status": "ACTIVE"
            }))
            
            if not items:
                dispatcher.utter_message(f"No items found matching '{item_name}'.")
                return []
            
            response_parts = []
            for item in items:
                item_id = item["_id"]
                item_name_found = item.get("itemName", "Unknown")
                
                # Get stock information
                stock_query = {"itemId": item_id}
                if warehouse_name:
                    # Find warehouse by name
                    warehouse = db["warehouses"].find_one({
                        "name": {"$regex": f".*{re.escape(warehouse_name)}.*", "$options": "i"}
                    })
                    if warehouse:
                        stock_query["warehouseId"] = warehouse["_id"]
                
                stocks = list(db["itemstocks"].find(stock_query))
                
                if stocks:
                    for stock in stocks:
                        warehouse_id = stock.get("warehouseId")
                        warehouse = db["warehouses"].find_one({"_id": warehouse_id})
                        warehouse_name_found = warehouse.get("name", "Unknown Warehouse") if warehouse else "Unknown Warehouse"
                        
                        available_stock = stock.get("availableStock", 0)
                        reorder_level = stock.get("reorderLevel", 0)
                        
                        status_icon = "🟢" if available_stock > reorder_level else "🔴" if available_stock > 0 else "⚫"
                        
                        response_parts.append(
                            f"{status_icon} **{item_name_found}** in {warehouse_name_found}: "
                            f"{available_stock} units (Reorder Level: {reorder_level})"
                        )
                else:
                    response_parts.append(f"❌ **{item_name_found}**: No stock information available")
            
            if response_parts:
                dispatcher.utter_message("\n".join(response_parts))
            else:
                dispatcher.utter_message(f"No stock information found for '{item_name}'.")
                
        except Exception as e:
            dispatcher.utter_message(f"Error checking stock: {str(e)}")
            print(f"Error in ActionStockQuantitySearch: {e}")
        
        return []

# --- Order Status ---
class ActionOrderStatus(Action):
    def name(self): return "action_order_status"
    
    def run(self, dispatcher, tracker, domain):
        order_id = tracker.get_slot("order_id")
        status = tracker.get_slot("status")
        
        if not order_id:
            dispatcher.utter_message("Please provide an order ID.")
            return []
        
        try:
            # Search for order by order ID
            order = db["orders"].find_one({
                "$or": [
                    {"or_orderId": str(order_id)},
                    {"cc_salesOrderNo": str(order_id)}
                ]
            })
            
            if not order:
                dispatcher.utter_message(f"Order '{order_id}' not found.")
                return []
            
            # If updating status
            if status:
                update_data = {"cc_orderStatus": status}
                db["orders"].update_one({"_id": order["_id"]}, {"$set": update_data})
                dispatcher.utter_message(f"✅ Order {order_id} status updated to '{status}'.")
                return []
            
            # Get order details
            order_id_found = order.get("or_orderId", order.get("cc_salesOrderNo", "Unknown"))
            order_status = order.get("cc_orderStatus", "Unknown")
            order_date = order.get("or_orderDate", "Unknown")
            client_name = order.get("cc_clientName", "Unknown")
            order_total = order.get("cc_orderTotal", order.get("or_total", "Unknown"))
            
            # Get order items
            order_items = list(db["orderitems"].find({"cc_orderId": order["_id"]}))
            items_info = []
            for item in order_items[:3]:  # Show first 3 items
                item_name = item.get("cc_itemName", "Unknown Item")
                quantity = item.get("cc_quantity", 0)
                items_info.append(f"• {item_name} (Qty: {quantity})")
            
            response = f"📋 **Order {order_id_found}**\n"
            response += f"Status: {order_status}\n"
            response += f"Date: {order_date}\n"
            response += f"Client: {client_name}\n"
            response += f"Total: ${order_total}\n"
            
            if items_info:
                response += f"Items: {', '.join(items_info)}"
                if len(order_items) > 3:
                    response += f" (and {len(order_items) - 3} more items)"
            
            dispatcher.utter_message(response)
            
        except Exception as e:
            dispatcher.utter_message(f"Error checking order status: {str(e)}")
            print(f"Error in ActionOrderStatus: {e}")
        
        return []

# --- Shipment Information ---
class ActionShipmentInfo(Action):
    def name(self): return "action_shipment_info"
    
    def run(self, dispatcher, tracker, domain):
        order_id = tracker.get_slot("order_id")
        
        if not order_id:
            dispatcher.utter_message("Please provide an order ID to check shipment.")
            return []
        
        try:
            # Find order first
            order = db["orders"].find_one({
                "$or": [
                    {"or_orderId": str(order_id)},
                    {"cc_salesOrderNo": str(order_id)}
                ]
            })
            
            if not order:
                dispatcher.utter_message(f"Order '{order_id}' not found.")
                return []
            
            # Find shipment information
            shipment = db["shipments"].find_one({"cc_orderId": order["_id"]})
            
            if shipment:
                shipments_data = shipment.get("shipments", [])
                if shipments_data:
                    response = f"🚚 **Shipment Information for Order {order_id}**\n"
                    for ship in shipments_data:
                        courier = ship.get("courier", "Unknown")
                        tracking_id = ship.get("trackingId", "Not assigned")
                        status = ship.get("status", "Unknown")
                        response += f"Courier: {courier}\nTracking ID: {tracking_id}\nStatus: {status}\n"
                else:
                    response = f"📦 Order {order_id} has shipment record but no shipment details available."
            else:
                response = f"❌ No shipment information found for order {order_id}."
            
            dispatcher.utter_message(response)
            
        except Exception as e:
            dispatcher.utter_message(f"Error checking shipment: {str(e)}")
            print(f"Error in ActionShipmentInfo: {e}")
        
        return []

# --- Invoice Information ---
class ActionInvoiceInfo(Action):
    def name(self): return "action_invoice_info"
    
    def run(self, dispatcher, tracker, domain):
        order_id = tracker.get_slot("order_id")
        
        if not order_id:
            dispatcher.utter_message("Please provide an order ID to check invoice.")
            return []
        
        try:
            # Find order first
            order = db["orders"].find_one({
                "$or": [
                    {"or_orderId": str(order_id)},
                    {"cc_salesOrderNo": str(order_id)}
                ]
            })
            
            if not order:
                dispatcher.utter_message(f"Order '{order_id}' not found.")
                return []
            
            # Find invoice information
            invoice = db["invoices"].find_one({"cc_orderId": order["_id"]})
            
            if invoice:
                invoices_data = invoice.get("ff_invoices", [])
                if invoices_data:
                    response = f"🧾 **Invoice Information for Order {order_id}**\n"
                    for inv in invoices_data:
                        invoice_id = inv.get("ff_invoiceId", "Unknown")
                        invoice_type = inv.get("ff_invoiceType", "Unknown")
                        invoice_status = inv.get("ff_invoiceStatus", "Unknown")
                        gross_amount = inv.get("ff_grossAmount", 0)
                        due_amount = inv.get("ff_dueAmount", 0)
                        currency = inv.get("cc_currency", "USD")
                        
                        response += f"Invoice ID: {invoice_id}\n"
                        response += f"Type: {invoice_type}\n"
                        response += f"Status: {'✅ Paid' if invoice_status else '❌ Unpaid'}\n"
                        response += f"Amount: {currency} {gross_amount}\n"
                        response += f"Due Amount: {currency} {due_amount}\n"
                else:
                    response = f"📄 Order {order_id} has invoice record but no invoice details available."
            else:
                response = f"❌ No invoice information found for order {order_id}."
            
            dispatcher.utter_message(response)
            
        except Exception as e:
            dispatcher.utter_message(f"Error checking invoice: {str(e)}")
            print(f"Error in ActionInvoiceInfo: {e}")
        
        return []

# --- Client Information ---
class ActionClientInfo(Action):
    def name(self): return "action_client_info"
    
    def run(self, dispatcher, tracker, domain):
        client_name = tracker.get_slot("client_name")
        
        if not client_name:
            dispatcher.utter_message("Please specify the client name.")
            return []
        
        try:
            # Search for client by name
            clients = list(db["clients"].find({
                "clientName": {"$regex": f".*{re.escape(client_name)}.*", "$options": "i"},
                "status": "ACTIVE"
            }))
            
            if not clients:
                dispatcher.utter_message(f"No active clients found matching '{client_name}'.")
                return []
            
            response_parts = []
            for client in clients:
                client_name_found = client.get("clientName", "Unknown")
                client_id = client.get("clientId", "Unknown")
                email = client.get("email", "Not provided")
                website = client.get("website", "Not provided")
                
                response_parts.append(
                    f"🏢 **{client_name_found}** (ID: {client_id})\n"
                    f"Email: {email}\n"
                    f"Website: {website}"
                )
            
            dispatcher.utter_message("\n\n".join(response_parts))
            
        except Exception as e:
            dispatcher.utter_message(f"Error checking client information: {str(e)}")
            print(f"Error in ActionClientInfo: {e}")
        
        return []

# --- Warehouse Information ---
class ActionWarehouseInfo(Action):
    def name(self): return "action_warehouse_info"
    
    def run(self, dispatcher, tracker, domain):
        warehouse_name = tracker.get_slot("warehouse_name")
        
        try:
            if warehouse_name:
                # Search for specific warehouse
                warehouses = list(db["warehouses"].find({
                    "name": {"$regex": f".*{re.escape(warehouse_name)}.*", "$options": "i"},
                    "status": "ACTIVE"
                }))
            else:
                # Get all warehouses
                warehouses = list(db["warehouses"].find({"status": "ACTIVE"}))
            
            if not warehouses:
                dispatcher.utter_message(f"No warehouses found matching '{warehouse_name}'." if warehouse_name else "No active warehouses found.")
                return []
            
            response_parts = []
            for warehouse in warehouses:
                name = warehouse.get("name", "Unknown")
                warehouse_id = warehouse.get("warehouseId", "Unknown")
                city = warehouse.get("city", "Unknown")
                state = warehouse.get("state", "Unknown")
                country = warehouse.get("country", "Unknown")
                
                response_parts.append(
                    f"🏭 **{name}** (ID: {warehouse_id})\n"
                    f"Location: {city}, {state}, {country}"
                )
            
            dispatcher.utter_message("\n\n".join(response_parts))
            
        except Exception as e:
            dispatcher.utter_message(f"Error checking warehouse information: {str(e)}")
            print(f"Error in ActionWarehouseInfo: {e}")
        
        return []
