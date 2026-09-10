from urllib import request

import mysql.connector
from mysql.connector import errorcode
from contextlib import contextmanager
import config

def get_conn():
    return mysql.connector.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        autocommit=True
    )

@contextmanager
def cursor():
    conn = None
    cur = None
    try:
        conn = get_conn()
        cur = conn.cursor(dictionary=True)
        yield cur
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def ping():
    try:
        with cursor() as cur:
            cur.execute('SELECT 1')
            return True
    except Exception:
        return False

def find_or_create_customer(name, email, address='', phone=None):
    first = ''
    last = ''
    if name:
        parts = name.split(None, 1)
        first = parts[0]
        last = parts[1] if len(parts) > 1 else ''
    with cursor() as cur:
        cur.execute('SELECT id FROM customers WHERE email=%s LIMIT 1', (email,))
        row = cur.fetchone()
        if row:
            return row['id']
        cur.execute('INSERT INTO customers (first_name,last_name,email,address,phone) VALUES (%s,%s,%s,%s,%s)',
                    (first, last, email, address, phone))
        return cur.lastrowid

def find_or_create_product_by_name(name, unit_price=0.0):
    with cursor() as cur:
        cur.execute('SELECT id FROM products WHERE name=%s LIMIT 1', (name,))
        row = cur.fetchone()
        if row:
            return row['id']
        sku = 'KTX-UNK-' + str(abs(hash(name)) % 100000)
        cur.execute('INSERT INTO products (sku,name,description,price,stock) VALUES (%s,%s,%s,%s,%s)',
                    (sku, name, name, unit_price, 0))
        return cur.lastrowid

def insert_order(order):
    cust_id = None
    try:
        cust_id = find_or_create_customer(order.get('name',''), order.get('email',''), order.get('address',''))
        subtotal = float(order.get('total', 0))
        with cursor() as cur:
            cur.execute('INSERT INTO orders (order_ref, customer_id, status, subtotal, shipping, total) VALUES (%s,%s,%s,%s,%s,%s)',
                        (order.get('order_id'), cust_id, order.get('status','Pending'), subtotal, 0.00, subtotal))
            oid = cur.lastrowid
            for it in order.get('items', []):
                title = it.get('title') or 'Item'
                qty = int(it.get('qty',1) or 1)
                price = float(it.get('price') or 0)
                pid = find_or_create_product_by_name(title, price)
                cur.execute('INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (%s,%s,%s,%s)',
                            (oid, pid, qty, price))
        return True
    except mysql.connector.Error as e:
        print('DB error inserting order:', e)
        return False

def get_all_orders():
    orders = []
    with cursor() as cur:
        cur.execute('SELECT o.id,o.order_ref,o.status,o.subtotal,o.shipping,o.total,o.created_at,c.first_name,c.last_name,c.email,c.address FROM orders o LEFT JOIN customers c ON o.customer_id=c.id ORDER BY o.created_at DESC')
        rows = cur.fetchall()
        for r in rows:
            cur.execute('SELECT oi.quantity, oi.unit_price, p.name FROM order_items oi LEFT JOIN products p ON oi.product_id=p.id WHERE oi.order_id=%s', (r['id'],))
            items = []
            for it in cur.fetchall():
                items.append({ 'title': it.get('name'), 'qty': it.get('quantity'), 'price': float(it.get('unit_price') or 0) })
            orders.append({
                'order_id': r.get('order_ref'),
                'date': r.get('created_at').isoformat() if r.get('created_at') else None,
                'name': (r.get('first_name') or '') + (' ' + (r.get('last_name') or '') if r.get('last_name') else ''),
                'email': r.get('email'),
                'address': r.get('address'),
                'items': items,
                'total': float(r.get('total') or 0),
                'status': r.get('status')
            })
    return orders

def update_order_status(order_ref, status):
    with cursor() as cur:
        cur.execute('UPDATE orders SET status=%s WHERE order_ref=%s', (status, order_ref))
        return cur.rowcount > 0


def get_products(str=None):
    qry=""
    if(str!=None):
        qry = 'SELECT p.id,p.featured,p.newarr,p.age,p.sku,p.name,p.description,p.price,p.category_id,p.image_url,p.image2_url,p.image3_url,p.image4_url,p.stock,p.created_at,c.name AS category_name FROM products p LEFT JOIN categories c ON p.category_id=c.id WHERE '+str+' ORDER BY p.created_at DESC'
    else:
        qry = 'SELECT p.id,p.featured,p.newarr,p.age,p.sku,p.name,p.description,p.price,p.category_id,p.image_url,p.image2_url,p.image3_url,p.image4_url,p.stock,p.created_at,c.name AS category_name FROM products p LEFT JOIN categories c ON p.category_id=c.id ORDER BY p.created_at DESC'

    products = []
    with cursor() as cur:
        cur.execute(qry)
        for r in cur.fetchall():
            products.append({
                'id': r.get('id'),
                'featured':r.get('featured'),
                'newarr':r.get('newarr'),
                'age':r.get('age'),
                'sku': r.get('sku'),
                'name': r.get('name'),
                'description': r.get('description'),
                'price': float(r.get('price') or 0),
                'category_id': r.get('category_id'),
                'category_name': r.get('category_name'),
                'image_url': r.get('image_url'),
                'image2_url': r.get('image2_url'),
                'image3_url': r.get('image3_url'),
                'image4_url': r.get('image4_url'),
                'stock': int(r.get('stock') or 0),
                'created_at': r.get('created_at').isoformat() if r.get('created_at') else None,
            })
    return products

def get_productsbycategoryid(id):
    products = []
    with cursor() as cur:
        # Ensure 'query' and 'cur.execute' start at the exact same column position
        query = '''SELECT 
            p.id, p.featured, p.newarr, p.age, p.sku, p.name, p.description,
            p.price, p.category_id, p.image_url,p.image2_url,p.image3_url,p.image4_url, p.stock,
            p.created_at, c.name AS category_name  
        FROM products p 
        LEFT JOIN categories c ON p.category_id = c.id 
        WHERE p.category_id = %s 
        ORDER BY p.created_at DESC'''

        cur.execute(query, (id,))


        for r in cur.fetchall():
            products.append({
                'id': r.get('id'),
                'featured':r.get('featured'),
                'newarr':r.get('newarr'),
                'age':r.get('age'),
                'sku': r.get('sku'),
                'name': r.get('name'),
                'description': r.get('description'),
                'price': float(r.get('price') or 0),
                'category_id': r.get('category_id'),
                'category_name': r.get('category_name'),
                'image_url': r.get('image_url'),
                'image2_url': r.get('image2_url'),
                'image3_url': r.get('image3_url'),
                'image4_url': r.get('image4_url'),
                'stock': int(r.get('stock') or 0),
                'created_at': r.get('created_at').isoformat() if r.get('created_at') else None,
            })
    return products


def get_categories(id=None):
    cats = []
    with cursor() as cur:
        if id is not None:
            query = 'SELECT * FROM categories WHERE parent_id = %s'
            cur.execute(query, (id,))
        else:
            query = 'SELECT * FROM categories WHERE parent_id = 1'
            cur.execute(query)

        for r in cur.fetchall():
            row = dict(r)
            name = row.get('name') or row.get('title') or row.get('category_name')
            if name:
                row['name'] = name
            row.setdefault('slug', (name.lower().replace(' ', '-') if name else ''))
            if row.get('created_at') and hasattr(row.get('created_at'), 'isoformat'):
                row['created_at'] = row['created_at'].isoformat()
                row['id']= str(row['id'])
            cats.append(row)
           
    return cats

def get_parentCategories():
    cats = []
    with cursor() as cur:
        query = 'SELECT * FROM categories WHERE parent_id = 1'
        cur.execute(query)
        
        for r in cur.fetchall():
            row = dict(r)
            name = row.get('name') or row.get('title') or row.get('category_name')
            if name:
                row['name'] = name
            row.setdefault('slug', (name.lower().replace(' ', '-') if name else ''))
            if row.get('created_at') and hasattr(row.get('created_at'), 'isoformat'):
                row['created_at'] = row['created_at'].isoformat()
                row['id']= str(row['id'])
            cats.append(row)
           
    return cats
