from flask import Flask, jsonify, redirect, render_template, request, session

import db

PER_PAGE = 12


app = Flask(__name__)
app.secret_key = "saeed-ghani-store"


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


DEFAULT_PRODUCTS = [
    {
        'id': 1,
        'sku': 'SG-001',
        'name': 'Classic Cotton Kurta',
        'description': 'Soft cotton finish for daily comfort and festive styling.',
        'price': 2299.0,
        'category_name': 'Women',
        'image_url': 'https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=900&q=80',
        'stock': 12,
    },
    {
        'id': 2,
        'sku': 'SG-002',
        'name': 'Elegant Festive Suit',
        'description': 'Premium festivewear with elevated detailing and a tailored fit.',
        'price': 3499.0,
        'category_name': 'Men',
        'image_url': 'https://images.unsplash.com/photo-1529139574466-a303027c1d8b?auto=format&fit=crop&w=900&q=80',
        'stock': 9,
    },
    {
        'id': 3,
        'sku': 'SG-003',
        'name': 'Handcrafted Dupatta',
        'description': 'Lightweight dupatta with graceful texture and rich color.',
        'price': 1799.0,
        'category_name': 'Accessories',
        'image_url': 'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=900&q=80',
        'stock': 15,
    },
    {
        'id': 4,
        'sku': 'SG-004',
        'name': 'Luxury Gift Set',
        'description': 'A premium gifting collection that feels elegant and personal.',
        'price': 4299.0,
        'category_name': 'Gifts',
        'image_url': 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=900&q=80',
        'stock': 7,
    },
]

def get_product_list():
    try:
        products = db.get_products()
        if products:
            return products
    except Exception:
        pass
    return DEFAULT_PRODUCTS


def render_products_html(products):
    cards = []
    for p in products:
        name = str(p.get('name', 'Product'))
        description = str(p.get('description', 'Premium selection for your collection.'))
        price = float(p.get('price') or 0)
        image = str(p.get('image_url') or 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=900&q=80')
        tag = str(p.get('category_name') or 'Featured').title()
        cards.append(
            """
            <article class="product-card">
              <div class="product-media">
                <span class="tag">{tag}</span>
                <img src="{image}" alt="{name}" />
              </div>
              <div class="product-body">
                <h3>{name}</h3>
                <div class="rating">★★★★★</div>
                <p>{description}</p>
                <div class="price-row">
                  <div class="price">
                    <strong>PKR {price}</strong>
                  </div>
                  <button class="cart-btn" aria-label="Add {name} to cart">+</button>
                </div>
              </div>
            </article>
            """.format(
                tag=tag,
                image=image,
                name=name,
                description=description,
                price=f'{price:,.0f}',
            )
        )

    card_html = '\n'.join(cards)
    style = """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@400;500;600;700;800&display=swap');
      body { margin: 0; font-family: "Inter", sans-serif; background: #f8f1eb; color: #1d1716; }
      .sg-shop { padding: 28px 0; }
      .sg-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 24px; width: min(1200px, calc(100% - 32px)); margin: 0 auto; }
      .product-card { background: rgba(255,255,255,0.9); border: 1px solid rgba(29,23,22,0.08); border-radius: 24px; overflow: hidden; box-shadow: 0 14px 24px rgba(30, 16, 14, 0.04); }
      .product-media { position: relative; height: 260px; overflow: hidden; }
      .product-media img { width: 100%; height: 100%; object-fit: cover; display: block; }
      .tag { position: absolute; top: 14px; left: 14px; background: rgba(140, 29, 29, 0.92); color: white; border-radius: 999px; padding: 6px 10px; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; }
      .product-body { padding: 18px; }
      .product-body h3 { margin: 0 0 8px; font-size: 1.2rem; font-weight: 700; }
      .rating { color: #d0aa73; letter-spacing: 0.08em; margin-bottom: 8px; }
      .product-body p { margin: 0 0 14px; color: #645d5a; font-size: 0.92rem; line-height: 1.7; }
      .price-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
      .price strong { color: #5f0f14; font-size: 1.3rem; font-weight: 800; }
      .cart-btn { border: none; background: #f7e6d0; color: #8c1d1d; border-radius: 999px; width: 42px; height: 42px; font-size: 1.2rem; font-weight: 700; cursor: pointer; }
      @media (max-width: 980px) { .sg-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
      @media (max-width: 640px) { .sg-grid { grid-template-columns: 1fr; } }
    </style>
    """

    return style + '<div class="sg-shop"><div class="sg-grid">' + card_html + '</div></div>'



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)