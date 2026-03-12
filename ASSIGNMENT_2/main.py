from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

# -----------------------------
# Sample Data (Products)
# -----------------------------

products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB Hub", "price": 799, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True}
]

feedback = []

# -----------------------------
# Q1 - Filter Products
# -----------------------------

@app.get("/products/filter")
def filter_products(category: Optional[str] = None,
                    max_price: Optional[int] = None,
                    min_price: Optional[int] = None):

    results = []

    for product in products:

        if category and product["category"] != category:
            continue

        if max_price and product["price"] > max_price:
            continue

        if min_price and product["price"] < min_price:
            continue

        results.append(product)

    return results


# -----------------------------
# Q2 - Get Product Price
# -----------------------------

@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):

    for product in products:
        if product["id"] == product_id:
            return {
                "name": product["name"],
                "price": product["price"]
            }

    return {"error": "Product not found"}


# -----------------------------
# Q3 - Customer Feedback
# -----------------------------

class CustomerFeedback(BaseModel):
    customer_name: str = Field(min_length=2)
    product_id: int = Field(gt=0)
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=300)


@app.post("/feedback")
def submit_feedback(data: CustomerFeedback):

    feedback.append(data.dict())

    return {
        "message": "Feedback submitted successfully",
        "feedback": data,
        "total_feedback": len(feedback)
    }


# -----------------------------
# Q4 - Product Summary
# -----------------------------

@app.get("/products/summary")
def product_summary():

    total_products = len(products)

    in_stock_count = sum(1 for p in products if p["in_stock"])
    out_of_stock_count = total_products - in_stock_count

    most_expensive = max(products, key=lambda x: x["price"])
    cheapest = min(products, key=lambda x: x["price"])

    categories = list(set(p["category"] for p in products))

    return {
        "total_products": total_products,
        "in_stock_count": in_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "most_expensive": {
            "name": most_expensive["name"],
            "price": most_expensive["price"]
        },
        "cheapest": {
            "name": cheapest["name"],
            "price": cheapest["price"]
        },
        "categories": categories
    }


# -----------------------------
# Q5 - Bulk Order
# -----------------------------

class OrderItem(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=50)


class BulkOrder(BaseModel):
    company_name: str = Field(min_length=2)
    contact_email: str = Field(min_length=5)
    items: List[OrderItem]


@app.post("/orders/bulk")
def bulk_order(order: BulkOrder):

    confirmed = []
    failed = []
    grand_total = 0

    for item in order.items:

        product = next((p for p in products if p["id"] == item.product_id), None)

        if not product:
            failed.append({
                "product_id": item.product_id,
                "reason": "Product not found"
            })
            continue

        if not product["in_stock"]:
            failed.append({
                "product_id": item.product_id,
                "reason": f"{product['name']} is out of stock"
            })
            continue

        subtotal = product["price"] * item.quantity
        grand_total += subtotal

        confirmed.append({
            "product": product["name"],
            "qty": item.quantity,
            "subtotal": subtotal
        })

    return {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": grand_total
    }


# ==================================================
# ⭐ BONUS — Order Status Tracker
# ==================================================

orders = []
order_counter = 1


# Create Order (status = pending)

@app.post("/orders")
def create_order(product_id: int, quantity: int):

    global order_counter

    order = {
        "order_id": order_counter,
        "product_id": product_id,
        "quantity": quantity,
        "status": "pending"
    }

    orders.append(order)

    order_counter += 1

    return order


# Get Order by ID

@app.get("/orders/{order_id}")
def get_order(order_id: int):

    for order in orders:
        if order["order_id"] == order_id:
            return order

    return {"error": "Order not found"}


# Confirm Order

@app.patch("/orders/{order_id}/confirm")
def confirm_order(order_id: int):

    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = "confirmed"
            return {
                "message": "Order confirmed",
                "order": order
            }

    return {"error": "Order not found"}