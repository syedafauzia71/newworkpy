# app.py
from email.quoprimime import unquote
import re

from flask import Flask, jsonify, redirect, render_template, request, session
import db
from products import get_product_list  # Import from products.py

app = Flask(__name__)
app.secret_key = "saeed-ghani-store"

PER_PAGE = 12
SHIPPING_CHARGE = 250

#@app.context_processor
# def inject_menu():
#     return dict(menu_tree=get_dynamic_menu())
# --------------------------------------------------------------------------

def _slugify(value):
    slug = re.sub(r'[^a-z0-9]+', '-', str(value or '').strip().lower())
    return slug.strip('-')


def _split_category_path(name):
    text = (name or '').strip()
    if not text:
        return []
    parts = re.split(r'\s*(?:»|>|/)\s*', text)
    cleaned = [part.strip() for part in parts if part and part.strip()]
    return cleaned or [text]

def menu_categories():
    menu_data = []
    parents = db.get_parentCategories()  # Fetch parent categories
    parents = [dict(r) for r in parents]

    # 2. Fetch submenus for each parent
    for parent in parents:
        subcategories = db.get_categories(parent["id"])
        subcategories = [dict(r) for r in subcategories]

        # Add submenus list to the main category dict
        parent["submenus"] = subcategories
        menu_data.append(parent)

    return menu_data
   

def search_products(products, query):
    term = (query or '').strip().lower()
    if not term:
        return products
    return [
        product for product in products
        if term in str(product.get('name', '')).lower()
        or term in str(product.get('description', '')).lower()
        or term in str(product.get('category_name', '')).lower()
    ]


def get_cart_count():
    cart = session.get("cart", {})
    return sum(int(item.get("quantity", 0)) for item in cart.values())


def get_cart_items():
    cart = session.get("cart", {})
    items = []
    for name, item in cart.items():
        quantity = int(item.get("quantity", 0))
        price = float(item.get("price", 0.0))
        items.append({"name": name, "quantity": quantity, "price": price, "total": quantity * price})
    return items


@app.route("/")
@app.route("/home")
def home():
    search_term = request.args.get("q", "", type=str)
    if search_term.strip():
        products = search_products(get_product_list(), search_term)
        print('greer')
    else :
      products= db.get_products("featured = 1")
    return render_template(
        "index.html",
        products=products,
        page="home",
        cart_count=get_cart_count(),
        search_query=search_term,
        menu_categories= menu_categories(),
        categories=db.get_categories(),
    )


@app.route("/products")    
def show_products():
    data = []
    search_term = request.args.get("q", "", type=str)
    term = request.args.get("s", "", type=str)

    if search_term.strip():
        # User entered a query -> search products
        data = search_products(get_product_list(), search_term)

    elif term.strip():
        #term = request.args.get("s", "", type=str)
        # No search query -> show ALL products (instead of featured only)
        data = db.get_products(term+'=1')
    
    elif request.query_string:
            # request.query_string gives raw bytes: b'2_Smart%20Toys'
            raw_query = str(request.query_string, 'utf-8')  # Decode bytes to string

            if not raw_query:
                return {'error': 'Missing query parameter'}, 400

            # Split '2_Smart Toys' at the first underscore
            parts = raw_query.split('_', 1)
            category_id = parts[0]
            data = db.get_productsbycategoryid(category_id)
            cats=[]
            cat = any
            cats = db.get_categories(category_id)
            if cats:
                for cat in cats:
                    itms = db.get_productsbycategoryid(cat['id'])
                    data.extend(itms)
                    
                
    else:
         # No search query -> show ALL products (instead of featured only)
         data = db.get_products()   

    #data = search_products(get_product_list(), search_term)
    page = request.args.get("page", 1, type=int)
    total = len(data)
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    page = max(1, min(page, total_pages))
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    paginated_products = data[start:end]


    return render_template(
        "products.html",
        products=paginated_products,
        total=total,
        perpage=PER_PAGE,
        current_page=page,
        total_pages=total_pages,
        prev_page=page - 1 if page > 1 else None,
        next_page=page + 1 if end < total else None,
        cart_count=get_cart_count(),
        search_query=search_term,
        menu_categories= menu_categories(),
    )

@app.route("/products/<category_slug>")
def productsbyCategory(category_slug):
    try:
        # Splits '4_remote-control' into ['4', 'remote-control']
        category_id = int(category_slug.split('_')[0]) 
    except (ValueError, IndexError):
        return "Invalid Category Format", 400
    # Pass the isolated integer ID to your db function
    data = db.get_productsbycategoryid(category_id)
    page = request.args.get("page", 1, type=int)
    total = len(data)
    total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    page = max(1, min(page, total_pages))
    start = (page - 1) * PER_PAGE
    end = start + PER_PAGE
    paginated_products = data[start:end]
    return render_template(
            "products.html",
            products=paginated_products,
            current_page=page,
            total_pages=total_pages,
            prev_page=page - 1 if page > 1 else None,
            next_page=page + 1 if end < total else None,
            cart_count=get_cart_count(),
            menu_categories= menu_categories(),
    )
    
@app.route("/product/<int:product_id>")
def product_detail(product_id):
    # Fetch all products and find the matching item
    products = db.get_products()
    product = next((p for p in products if p['id'] == product_id), None)
    
    if not product:
        return "Product not found", 404

    return render_template(
        "product_detail.html",
        product=product,
        cart_count=get_cart_count(),
        menu_categories= menu_categories(),
    )

# @app.route("/add_to_cart", methods=["POST"])
@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    product_name = request.form.get("product_name")
    product_price = request.form.get("product_price")
    # Retrieve submitted quantity, default to 1 if missing or empty
    raw_qty = request.form.get("quantity")
    qty_to_add = int(raw_qty) if raw_qty and raw_qty.isdigit() else 1

    next_url = request.form.get("next") or "/products"

    if not product_name:
        return redirect(next_url)

    cart = session.get("cart", {})
    product = cart.get(product_name, {"quantity": 0, "price": 0.0})

    # Increment quantity by the requested amount instead of hardcoded 1
    product["quantity"] = int(product.get("quantity", 0)) + qty_to_add
    product["price"] = float(product_price or product.get("price", 0.0))
    
    cart[product_name] = product
    session["cart"] = cart

    return redirect(next_url)
# def add_to_cart():
#     product_name = request.form.get("product_name")
#     product_price = request.form.get("product_price")
#     product_qty = request.form.get("quantity")
#     next_url = request.form.get("next") or "/products"

#     if not product_name:
#         return redirect(next_url)

#     cart = session.get("cart", {})
#     product = cart.get(product_name, {"quantity": 0, "price": 0.0})
#     product["quantity"] = int(product.get("quantity", 0)) + 1
#     product["price"] = float(product_price or product.get("price", 0.0))
#     cart[product_name] = product
#     session["cart"] = cart

#     return redirect(next_url)


@app.route("/cart")
def cart_page():
    items = get_cart_items()
    subtotal = sum(item["total"] for item in items)
    shipping_charge = 0 if subtotal > 5000 else (SHIPPING_CHARGE if subtotal > 0 else 0)
    total = subtotal + shipping_charge
    return render_template(
        "cart.html",
        cart_items=items,
        subtotal=subtotal,
        shipping_charge=shipping_charge,
        cart_total=total,
        cart_count=get_cart_count(),
        menu_categories=menu_categories(),
    )


@app.route("/update_cart_quantity", methods=["POST"])
def update_cart_quantity():
    product_name = request.form.get("product_name")
    change = request.form.get("change")

    if not product_name:
        return redirect("/cart")

    cart = session.get("cart", {})
    if product_name not in cart:
        return redirect("/cart")

    current_quantity = int(cart[product_name].get("quantity", 0))

    if change == "increase":
        cart[product_name]["quantity"] = current_quantity + 1
    elif change == "decrease":
        cart[product_name]["quantity"] = current_quantity - 1
        if cart[product_name]["quantity"] <= 0:
            del cart[product_name]

    session["cart"] = cart
    return redirect("/cart")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)