from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from math import ceil

app = FastAPI()

# ----------- PRODUCTS DATA -----------

products = {
    1: {"name": "Wireless Mouse", "price": 499, "stock": 10, "category": "Electronics"},
    2: {"name": "Notebook", "price": 99, "stock": 20, "category": "Stationery"},
    3: {"name": "USB Hub", "price": 799, "stock": 0, "category": "Electronics"},
    4: {"name": "Pen Set", "price": 49, "stock": 15, "category": "Stationery"},
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

    for item in cart:
        if item["product_id"] == product_id:
            item["quantity"] += quantity
            item["subtotal"] = item["quantity"] * item["unit_price"]

            return {"message": "Cart updated", "cart_item": item}

    cart_item = {
        "product_id": product_id,
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "subtotal": quantity * product["price"]
    }

    cart.append(cart_item)

    return {"message": "Added to cart", "cart_item": cart_item}

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
    return {"orders": orders, "total_orders": len(orders)}

# =====================================================
# Q1 — SEARCH PRODUCTS
# =====================================================

@app.get("/products/search")
def search_products(keyword: str):

    product_list = [
        {"product_id": pid, **details}
        for pid, details in products.items()
    ]

    results = [
        p for p in product_list
        if keyword.lower() in p["name"].lower()
    ]

    if not results:
        return {"message": f"No products found for: {keyword}"}

    return {
        "keyword": keyword,
        "total_found": len(results),
        "products": results
    }

# =====================================================
# Q2 — SORT PRODUCTS
# =====================================================

@app.get("/products/sort")
def sort_products(
    sort_by: str = "price",
    order: str = "asc"
):

    if sort_by not in ["price", "name"]:
        return {"error": "sort_by must be 'price' or 'name'"}

    product_list = [
        {"product_id": pid, **details}
        for pid, details in products.items()
    ]

    reverse = True if order == "desc" else False

    sorted_products = sorted(
        product_list,
        key=lambda x: x[sort_by],
        reverse=reverse
    )

    return {
        "sort_by": sort_by,
        "order": order,
        "products": sorted_products
    }

# =====================================================
# Q3 — PAGINATION PRODUCTS
# =====================================================

@app.get("/products/page")
def paginate_products(page: int = 1, limit: int = 2):

    product_list = [
        {"product_id": pid, **details}
        for pid, details in products.items()
    ]

    total_products = len(product_list)
    total_pages = ceil(total_products / limit)

    start = (page - 1) * limit
    end = start + limit

    return {
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "products": product_list[start:end]
    }

# =====================================================
# Q4 — SEARCH ORDERS
# =====================================================

@app.get("/orders/search")
def search_orders(customer_name: str):

    results = [
        order for order in orders
        if customer_name.lower() in order["customer_name"].lower()
    ]

    if not results:
        return {"message": f"No orders found for: {customer_name}"}

    return {
        "customer_name": customer_name,
        "total_found": len(results),
        "orders": results
    }

# =====================================================
# Q5 — SORT BY CATEGORY THEN PRICE
# =====================================================

@app.get("/products/sort-by-category")
def sort_by_category():

    product_list = [
        {"product_id": pid, **details}
        for pid, details in products.items()
    ]

    sorted_products = sorted(
        product_list,
        key=lambda x: (x["category"], x["price"])
    )

    return {"products": sorted_products}

# =====================================================
# Q6 — SEARCH + SORT + PAGINATE
# =====================================================

@app.get("/products/browse")
def browse_products(
    keyword: str = None,
    sort_by: str = "price",
    order: str = "asc",
    page: int = 1,
    limit: int = 4
):

    product_list = [
        {"product_id": pid, **details}
        for pid, details in products.items()
    ]

    # FILTER
    if keyword:
        product_list = [
            p for p in product_list
            if keyword.lower() in p["name"].lower()
        ]

        if not product_list:
            return {"message": f"No products found for: {keyword}"}

    #  SORT
    if sort_by not in ["price", "name"]:
        return {"error": "sort_by must be 'price' or 'name'"}

    reverse = True if order == "desc" else False

    product_list = sorted(
        product_list,
        key=lambda x: x[sort_by],
        reverse=reverse
    )

    # PAGINATION
    total_found = len(product_list)
    total_pages = ceil(total_found / limit) if total_found > 0 else 1

    start = (page - 1) * limit
    end = start + limit

    paginated = product_list[start:end]

    return {
        "keyword": keyword,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "limit": limit,
        "total_found": total_found,
        "total_pages": total_pages,
        "products": paginated
    }

# =====================================================
# BONUS — PAGINATE ORDERS
# =====================================================

@app.get("/orders/page")
def paginate_orders(page: int = 1, limit: int = 3):

    total_orders = len(orders)
    total_pages = ceil(total_orders / limit) if total_orders > 0 else 1

    start = (page - 1) * limit
    end = start + limit

    return {
        "page": page,
        "limit": limit,
        "total_orders": total_orders,
        "total_pages": total_pages,
        "orders": orders[start:end]
    }