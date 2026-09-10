from app import app, build_menu_from_categories


def test_products_page_renders_product_cards():
    client = app.test_client()
    response = client.get('/')

    assert response.status_code == 200
    assert b'Classic Cotton Kurta' in response.data
    assert b'product-card' in response.data


def test_build_menu_from_categories_handles_hierarchical_db_names():
    categories = [
        {'name': 'Kids Toys'},
        {'name': 'Kids Toys » Sports » Indoor'},
        {'name': 'Kids Toys » Remote Control » Robots'},
        {'name': 'Drones'},
    ]

    menu = build_menu_from_categories(categories)

    assert menu[0]['name'] == 'Kids Toys'
    assert menu[0]['children'][0]['name'] == 'Sports'
    assert menu[0]['children'][0]['children'][0]['name'] == 'Indoor'
    assert any(item['name'] == 'Drones' for item in menu)


def test_add_to_cart_updates_session():
    client = app.test_client()
    with client.session_transaction() as session:
        session.clear()

    response = client.post(
        '/add_to_cart',
        data={
            'product_name': 'Classic Cotton Kurta',
            'product_price': '2299.0',
            'next': '/',
        },
        follow_redirects=False,
    )

    assert response.status_code == 302
    with client.session_transaction() as session:
        assert session['cart']['Classic Cotton Kurta']['quantity'] == 1
        assert session['cart']['Classic Cotton Kurta']['price'] == 2299.0


def test_cart_quantity_controls_update_session():
    client = app.test_client()
    with client.session_transaction() as session:
        session.clear()
        session['cart'] = {
            'Classic Cotton Kurta': {'quantity': 1, 'price': 2299.0}
        }

    increase = client.post(
        '/update_cart_quantity',
        data={'product_name': 'Classic Cotton Kurta', 'change': 'increase'},
        follow_redirects=False,
    )
    assert increase.status_code == 302
    with client.session_transaction() as session:
        assert session['cart']['Classic Cotton Kurta']['quantity'] == 2

    decrease = client.post(
        '/update_cart_quantity',
        data={'product_name': 'Classic Cotton Kurta', 'change': 'decrease'},
        follow_redirects=False,
    )
    assert decrease.status_code == 302
    with client.session_transaction() as session:
        assert session['cart']['Classic Cotton Kurta']['quantity'] == 1

    final_decrease = client.post(
        '/update_cart_quantity',
        data={'product_name': 'Classic Cotton Kurta', 'change': 'decrease'},
        follow_redirects=False,
    )
    assert final_decrease.status_code == 302
    with client.session_transaction() as session:
        assert 'Classic Cotton Kurta' not in session['cart']
