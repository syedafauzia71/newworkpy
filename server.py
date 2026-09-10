from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os

import config
import db

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/index.html')
def index_html():
    return send_from_directory('.', 'index.html')


@app.route('/products')
def products():
    if not config.USE_DATABASE:
        return jsonify({'products': []})
    ok = db.ping()
    if not ok:
        return jsonify({'products': []})
    prods = db.get_products()
    return jsonify({'products': prods})


@app.route('/categories')
def categories():
    if not config.USE_DATABASE:
        return jsonify({'categories': []})
    ok = db.ping()
    if not ok:
        return jsonify({'categories': []})
    cats = db.get_categories()
    return jsonify({'categories': cats})


@app.route('/db/status')
def db_status():
    return jsonify({'db_available': db.ping(), 'database': config.DB_NAME})


@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json(force=True)
    ok = db.insert_order(data)
    return jsonify({'ok': ok})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
import os
import json
import config
import db

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

ORDERS_DIR = 'orders'
ORDERS_FILE = os.path.join(ORDERS_DIR, 'orders.txt')
ORDERS_JSONL = os.path.join(ORDERS_DIR, 'orders.jsonl')
ALL_ORDERS_FILE = os.path.join(ORDERS_DIR, 'all_orders.txt')

def format_order(o):
    lines = []
    lines.append(f"Order ID: {o.get('order_id')}")
    lines.append(f"Date: {o.get('date', datetime.utcnow().isoformat())}")
    lines.append("")
    lines.append("Customer:")
    lines.append(f"Name: {o.get('name','')}")
    lines.append(f"Email: {o.get('email','')}")
    lines.append(f"Address: {o.get('address','')}")
    lines.append("")
    lines.append("Items:")
    for it in o.get('items',[]):
        title = it.get('title')
        qty = it.get('qty',1)
        price = float(it.get('price',0) or 0)
        lines.append(f"- {title} x {qty} @ ${price:.2f} = ${price*qty:.2f}")
    lines.append("")
    lines.append(f"Total: ${float(o.get('total',0)):.2f}")
    lines.append('\n' + ('-'*40) + '\n')
    return '\n'.join(lines)


def append_jsonl(order):
    os.makedirs(ORDERS_DIR, exist_ok=True)
    with open(ORDERS_JSONL, 'a', encoding='utf-8') as jf:
        jf.write(json.dumps(order, ensure_ascii=False) + '\n')


def load_all_orders():
    orders = []
    if not os.path.exists(ORDERS_JSONL):
        return orders
    with open(ORDERS_JSONL, 'r', encoding='utf-8') as jf:
        for line in jf:
            line = line.strip()
            if not line: continue
            try:
                orders.append(json.loads(line))
            except Exception:
                continue
    return orders


@app.route('/orders/export', methods=['GET'])
def export_all_orders():
    orders = load_all_orders()
    try:
        os.makedirs(ORDERS_DIR, exist_ok=True)
        with open(ALL_ORDERS_FILE, 'w', encoding='utf-8') as f:
            for o in orders:
                f.write(format_order(o))
        return send_from_directory(ORDERS_DIR, os.path.basename(ALL_ORDERS_FILE), as_attachment=True)
    except Exception as e:
        return jsonify({'error':'Failed to export', 'detail': str(e)}), 500


@app.route('/orders', methods=['POST'])
def receive_order():
    if not request.is_json:
        return jsonify({'error':'Expected JSON'}), 400
    data = request.get_json()
    if 'order_id' not in data:
        return jsonify({'error':'Missing order_id'}), 400
    data.setdefault('status', 'Pending')
    entry = format_order(data)
    try:
        os.makedirs(ORDERS_DIR, exist_ok=True)
        with open(ORDERS_FILE, 'a', encoding='utf-8') as f:
            f.write(entry)
        append_jsonl(data)
        if config.USE_DATABASE and db.ping():
            saved = db.insert_order(data)
            if not saved:
                app.logger.warning('Failed to save order to DB, kept file fallback')
    except Exception as e:
        return jsonify({'error':'Failed to save order', 'detail': str(e)}), 500
    return jsonify({'status':'saved','order_id': data.get('order_id')}), 201


@app.route('/orders', methods=['GET'])
def list_orders():
    if config.USE_DATABASE and db.ping():
        try:
            orders = db.get_all_orders()
            return jsonify({'orders': orders})
        except Exception:
            pass
    orders = load_all_orders()
    return jsonify({'orders': orders})


@app.route('/orders/<order_id>/status', methods=['POST'])
def update_status(order_id):
    if not request.is_json:
        return jsonify({'error':'Expected JSON'}), 400
    body = request.get_json()
    status = body.get('status')
    if not status:
        return jsonify({'error':'Missing status'}), 400
    if config.USE_DATABASE and db.ping():
        ok = db.update_order_status(order_id, status)
        if ok:
            return jsonify({'status':'updated','order_id': order_id, 'new_status': status})
    orders = load_all_orders()
    changed = False
    for o in orders:
        if o.get('order_id') == order_id:
            o['status'] = status
            changed = True
            break
    if not changed:
        return jsonify({'error':'Order not found'}), 404
    try:
        with open(ORDERS_JSONL, 'w', encoding='utf-8') as jf:
            for o in orders:
                jf.write(json.dumps(o, ensure_ascii=False) + '\n')
    except Exception as e:
        return jsonify({'error':'Failed to update', 'detail': str(e)}), 500
    return jsonify({'status':'updated','order_id': order_id, 'new_status': status})


@app.route('/admin')
def admin_page():
    return send_from_directory('.', 'admin.html')


@app.route('/')
def home_page():
    return send_from_directory('.', 'index.html')


@app.route('/index.html')
def index_page():
    return send_from_directory('.', 'index.html')


@app.route('/db/status')
def db_status():
    ok = config.USE_DATABASE and db.ping()
    return jsonify({'db_available': bool(ok), 'database': config.DB_NAME})


@app.route('/products')
def products_api():
    if config.USE_DATABASE and db.ping():
        try:
            products = db.get_products()
            return jsonify({'products': products})
        except Exception as e:
            app.logger.exception('Failed to fetch products from DB')
            return jsonify({'products': []}), 200
    return jsonify({'products': []})


@app.route('/categories')
def categories_api():
    if config.USE_DATABASE and db.ping():
        try:
            cats = db.get_categories()
            return jsonify({'categories': cats})
        except Exception:
            app.logger.exception('Failed to fetch categories from DB')
            return jsonify({'categories': []}), 200
    return jsonify({'categories': []})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
