from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# ----------- PRODUCTS DATA -----------

products = {
    1: {"name": "Wireless Mouse", "price": 499, "stock": 10},
    2: {"name": "Notebook", "price": 99, "stock": 20},
    3: {"name": "USB Hub", "price": 299, "stock": 0},
    4: {"name": "Pen Set", "price": 49, "stock": 15},
}

# ----------- CART + ORDERS -----------

cart = []
orders = []
order_id_counter = 1


# ----------- MODELS -----------

class Checkout(BaseModel):
    customer_name: str
    delivery_address: str


# ----------- ADD TO CART -----------

@app.post("/cart/add")
def add_to_cart(product_id: int, quantity: int):

    if product_id not in products:
        raise HTTPException(status_code=404, detail="Product not found")

    product = products[product_id]

    if product["stock"] == 0:
        raise HTTPException(status_code=400, detail=f"{product['name']} is out of stock")

    # check if already in cart
    for item in cart:
        if item["product_id"] == product_id:
            item["quantity"] += quantity
            item["subtotal"] = item["quantity"] * item["unit_price"]

            return {
                "message": "Cart updated",
                "cart_item": item
            }

    cart_item = {
        "product_id": product_id,
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "subtotal": quantity * product["price"]
    }

    cart.append(cart_item)

    return {
        "message": "Added to cart",
        "cart_item": cart_item
    }


# ----------- VIEW CART -----------

@app.get("/cart")
def view_cart():

    if len(cart) == 0:
        return {"message": "Cart is empty"}

    grand_total = sum(item["subtotal"] for item in cart)

    return {
        "items": cart,
        "item_count": len(cart),
        "grand_total": grand_total
    }


# ----------- REMOVE ITEM -----------

@app.delete("/cart/{product_id}")
def remove_item(product_id: int):

    for item in cart:
        if item["product_id"] == product_id:
            cart.remove(item)
            return {"message": f"{item['product_name']} removed from cart"}

    raise HTTPException(status_code=404, detail="Item not in cart")


# ----------- CHECKOUT -----------

@app.post("/cart/checkout")
def checkout(data: Checkout):

    global order_id_counter

    if len(cart) == 0:
        raise HTTPException(status_code=400, detail="CART_EMPTY")

    placed_orders = []
    grand_total = 0

    for item in cart:

        order = {
            "order_id": order_id_counter,
            "customer_name": data.customer_name,
            "product": item["product_name"],
            "quantity": item["quantity"],
            "subtotal": item["subtotal"],
            "delivery_address": data.delivery_address
        }

        orders.append(order)
        placed_orders.append(order)

        grand_total += item["subtotal"]
        order_id_counter += 1

    cart.clear()

    return {
        "orders_placed": placed_orders,
        "grand_total": grand_total
    }


# ----------- VIEW ORDERS -----------

@app.get("/orders")
def view_orders():

    return {
        "orders": orders,
        "total_orders": len(orders)
    }