from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_bcrypt import Bcrypt
from functools import wraps
import psycopg2
import os
from datetime import datetime
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)
bcrypt = Bcrypt(app)

DB_CONFIG = {
    'host': 'localhost',
    'database': 'agency1',
    'user': 'postgres',
    'password': 'Nikolai',
    'port': '5432'
}

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")
        return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'agent_id' not in session:
            flash('Требуется авторизация', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'agent_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Пожалуйста, введите email и пароль', 'danger')
            return render_template('login.html')

        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT agent_id, password_agent, name_agent FROM Agents WHERE email_agent = %s",
                    (email,)
                )
                agent = cursor.fetchone()

                if agent:
                    agent_id, hashed_password, name_agent = agent

                    print(f"DEBUG: Password from DB for {email}: {hashed_password}")
                    print(f"DEBUG: Password length: {len(hashed_password)}")

                    def extract_valid_bcrypt_hash(dirty_hash):
                        if not dirty_hash:
                            return None

                        prefixes = ['$2a$', '$2b$', '$2y$']

                        for prefix in prefixes:
                            if prefix in dirty_hash:
                                start = dirty_hash.find(prefix)
                                if len(dirty_hash) >= start + 60:
                                    potential_hash = dirty_hash[start:start + 60]
                                    if potential_hash.count('$') == 3:
                                        return potential_hash

                        return None

                    extracted_hash = extract_valid_bcrypt_hash(hashed_password)

                    if extracted_hash:
                        print(f"DEBUG: Extracted hash: {extracted_hash}")
                        print(f"DEBUG: Extracted hash length: {len(extracted_hash)}")

                        try:
                            if bcrypt.check_password_hash(extracted_hash, password):
                                session['agent_id'] = agent_id
                                session['agent_email'] = email
                                session['agent_name'] = name_agent or email.split('@')[0]
                                flash(f'Добро пожаловать, {session["agent_name"]}!', 'success')
                                return redirect(url_for('dashboard'))
                            else:
                                flash('Неверный пароль', 'danger')

                                print("DEBUG: Testing common passwords...")
                                test_passwords = [
                                    'password123',
                                    '123456',
                                    'qwerty',
                                    'admin123',
                                    'morozov',
                                    'smorozov',
                                    'realtor',
                                    'password'
                                ]
                                for test_pwd in test_passwords:
                                    if bcrypt.check_password_hash(extracted_hash, test_pwd):
                                        print(f"DEBUG: Password might be: {test_pwd}")
                                        break

                        except Exception as e:
                            print(f"DEBUG: BCrypt check error: {e}")
                            flash(f'Ошибка проверки пароля', 'danger')
                    else:
                        print(f"DEBUG: No valid bcrypt hash found, trying as plain text")

                        possible_passwords = [
                            hashed_password[:20],
                            hashed_password.split('.')[0] if '.' in hashed_password else hashed_password,
                            'password123',
                            '123456',
                            'qwerty'
                        ]

                        for test_pwd in possible_passwords:
                            if test_pwd == password:
                                new_hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                                cursor.execute(
                                    "UPDATE Agents SET password_agent = %s WHERE agent_id = %s",
                                    (new_hashed_password, agent_id)
                                )
                                conn.commit()

                                session['agent_id'] = agent_id
                                session['agent_email'] = email
                                session['agent_name'] = name_agent or email.split('@')[0]
                                flash('Пароль успешно обновлен. Добро пожаловать!', 'success')
                                return redirect(url_for('dashboard'))

                        flash('Неверный пароль', 'danger')
                else:
                    flash('Пользователь не найден', 'danger')

            except Exception as e:
                flash(f'Ошибка при входе: {str(e)}', 'danger')
                print(f"ERROR: Login error: {e}")
            finally:
                cursor.close()
                conn.close()
        else:
            flash('Не удалось подключиться к базе данных', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    stats = {}

    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM Requests")
        stats['requests'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Properties")
        stats['properties'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Deals")
        stats['deals'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Clients")
        stats['clients'] = cursor.fetchone()[0]

        cursor.execute("""
            SELECT d.deal_id, c1.name_client as seller, p.address_properties, 
                   d.final_price, d.status, d.deal_date
            FROM Deals d
            JOIN Clients c1 ON d.owner_id = c1.client_id
            JOIN Properties p ON d.property_id = p.property_id
            WHERE d.status != 'завершена'
            ORDER BY d.deal_date DESC
            LIMIT 5
        """)
        active_deals = cursor.fetchall()

        cursor.execute("""
            SELECT r.request_id, c.name_client, r.region_request, r.price_request
            FROM Requests r
            JOIN Clients c ON r.client_id = c.client_id
            ORDER BY r.request_id DESC
            LIMIT 5
        """)
        recent_requests = cursor.fetchall()

    except Exception as e:
        flash(f'Ошибка загрузки данных: {str(e)}', 'danger')
        stats = {'requests': 0, 'properties': 0, 'deals': 0, 'clients': 0}
        active_deals = []
        recent_requests = []
    finally:
        if conn:
            cursor.close()
            conn.close()

    return render_template('dashboard.html', stats=stats,
                           active_deals=active_deals, recent_requests=recent_requests)

@app.route('/requests')
@login_required
def view_requests():
    client_filter = request.args.get('client', '')
    region_filter = request.args.get('region', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')

    conn = get_db_connection()
    requests = []
    clients = []
    regions = []

    try:
        cursor = conn.cursor()

        query = """
            SELECT r.request_id, c.name_client, c.phone_number, r.region_request, 
                   r.price_request, r.area_request, r.rooms_count_request,
                   r.funds_request
            FROM Requests r
            LEFT JOIN Clients c ON r.client_id = c.client_id
            WHERE 1=1
        """
        params = []

        if client_filter:
            query += " AND c.name_client ILIKE %s"
            params.append(f'%{client_filter}%')

        if region_filter:
            query += " AND r.region_request ILIKE %s"
            params.append(f'%{region_filter}%')

        if min_price:
            query += " AND r.price_request >= %s"
            params.append(float(min_price))

        if max_price:
            query += " AND r.price_request <= %s"
            params.append(float(max_price))

        query += " ORDER BY r.request_id DESC"

        cursor.execute(query, params)
        requests = cursor.fetchall()

        cursor.execute("""
            SELECT DISTINCT c.name_client 
            FROM Requests r
            JOIN Clients c ON r.client_id = c.client_id
            ORDER BY c.name_client
        """)
        clients = [row[0] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT DISTINCT region_request 
            FROM Requests 
            ORDER BY region_request
        """)
        regions = [row[0] for row in cursor.fetchall()]

    except Exception as e:
        flash(f'Ошибка загрузки запросов: {str(e)}', 'danger')
    finally:
        if conn:
            cursor.close()
            conn.close()

    return render_template('requests/list.html',
                           requests=requests,
                           clients=clients,
                           regions=regions,
                           filters={
                               'client': client_filter,
                               'region': region_filter,
                               'min_price': min_price,
                               'max_price': max_price
                           })

@app.route('/requests/create', methods=['GET', 'POST'])
@login_required
def create_request():
    if request.method == 'POST':
        try:
            data = (
                int(request.form.get('client_id')),
                session['agent_id'],
                float(request.form.get('price_request')),
                request.form.get('region_request'),
                float(request.form.get('area_request')),
                int(request.form.get('rooms_count_request')),
                float(request.form.get('funds_request'))
            )

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Requests (client_id, agent_id, price_request, region_request,
                                     area_request, rooms_count_request, funds_request)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, data)
            conn.commit()
            flash('Запрос успешно создан', 'success')
            return redirect(url_for('view_requests'))

        except Exception as e:
            flash(f'Ошибка при создании запроса: {str(e)}', 'danger')
        finally:
            if conn:
                cursor.close()
                conn.close()

    conn = get_db_connection()
    clients = []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT client_id, name_client FROM Clients ORDER BY name_client")
        clients = cursor.fetchall()
    except Exception as e:
        flash(f'Ошибка загрузки клиентов: {str(e)}', 'danger')
    finally:
        if conn:
            cursor.close()
            conn.close()

    return render_template('requests/create.html', clients=clients)

@app.route('/requests/edit/<int:request_id>', methods=['GET', 'POST'])
@login_required
def edit_request(request_id):
    conn = get_db_connection()

    if request.method == 'POST':
        try:
            data = (
                float(request.form.get('price_request')),
                request.form.get('region_request'),
                float(request.form.get('area_request')),
                int(request.form.get('rooms_count_request')),
                float(request.form.get('funds_request')),
                request_id
            )

            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Requests 
                SET price_request = %s, region_request = %s, area_request = %s,
                    rooms_count_request = %s, funds_request = %s
                WHERE request_id = %s
            """, data)
            conn.commit()
            flash('Запрос успешно обновлен', 'success')
            return redirect(url_for('view_requests'))

        except Exception as e:
            flash(f'Ошибка при обновлении запроса: {str(e)}', 'danger')
        finally:
            if conn:
                cursor.close()
                conn.close()

    request_data = None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM Requests 
            WHERE request_id = %s
        """, (request_id,))
        request_data = cursor.fetchone()

        if not request_data:
            flash('Запрос не найден', 'danger')
            return redirect(url_for('view_requests'))

    except Exception as e:
        flash(f'Ошибка загрузки запроса: {str(e)}', 'danger')
    finally:
        if conn:
            cursor.close()
            conn.close()

    return render_template('requests/edit.html', request=request_data)

@app.route('/requests/delete/<int:request_id>', methods=['POST'])
@login_required
def delete_request(request_id):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM Requests 
            WHERE request_id = %s
        """, (request_id,))
        conn.commit()
        flash('Запрос успешно удален', 'success')
    except Exception as e:
        flash(f'Ошибка при удалении запроса: {str(e)}', 'danger')
    finally:
        if conn:
            cursor.close()
            conn.close()

    return redirect(url_for('view_requests'))

@app.route('/properties')
@login_required
def view_properties():
    address_filter = request.args.get('address', '')
    type_filter = request.args.get('type', '')
    region_filter = request.args.get('region', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    min_area = request.args.get('min_area', '')
    max_area = request.args.get('max_area', '')
    rooms_filter = request.args.get('rooms', '')
    available_filter = request.args.get('available', '')

    conn = get_db_connection()
    properties = []
    property_types = []
    regions = []
    rooms_options = []

    try:
        cursor = conn.cursor()

        query = """
            SELECT p.property_id, p.address_properties, p.property_type, 
                   p.area_properties, p.rooms_count_properties, p.price_properties,
                   p.region_properties, p.lift_properties, p.floor_properties,
                   p.total_floors_properties, p.build_year_properties, p.is_available,
                   c.name_client as owner_name
            FROM Properties p
            LEFT JOIN Clients c ON p.owner_id = c.client_id
            WHERE 1=1
        """
        params = []

        if address_filter:
            query += " AND p.address_properties ILIKE %s"
            params.append(f'%{address_filter}%')

        if type_filter:
            query += " AND p.property_type = %s"
            params.append(type_filter)

        if region_filter:
            query += " AND p.region_properties ILIKE %s"
            params.append(f'%{region_filter}%')

        if min_price:
            query += " AND p.price_properties >= %s"
            params.append(float(min_price))

        if max_price:
            query += " AND p.price_properties <= %s"
            params.append(float(max_price))

        if min_area:
            query += " AND p.area_properties >= %s"
            params.append(float(min_area))

        if max_area:
            query += " AND p.area_properties <= %s"
            params.append(float(max_area))

        if rooms_filter:
            query += " AND p.rooms_count_properties = %s"
            params.append(int(rooms_filter))

        if available_filter == 'available':
            query += " AND p.is_available = true"
        elif available_filter == 'sold':
            query += " AND p.is_available = false"

        query += " ORDER BY p.property_id DESC"

        cursor.execute(query, params)
        properties = cursor.fetchall()

        cursor.execute("SELECT DISTINCT property_type FROM Properties ORDER BY property_type")
        property_types = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT region_properties FROM Properties ORDER BY region_properties")
        regions = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT rooms_count_properties FROM Properties ORDER BY rooms_count_properties")
        rooms_options = [row[0] for row in cursor.fetchall()]

    except Exception as e:
        flash(f'Ошибка загрузки объектов: {str(e)}', 'danger')
    finally:
        if conn:
            cursor.close()
            conn.close()

    return render_template('properties/list.html',
                           properties=properties,
                           property_types=property_types,
                           regions=regions,
                           rooms_options=rooms_options,
                           filters={
                               'address': address_filter,
                               'type': type_filter,
                               'region': region_filter,
                               'min_price': min_price,
                               'max_price': max_price,
                               'min_area': min_area,
                               'max_area': max_area,
                               'rooms': rooms_filter,
                               'available': available_filter
                           })

@app.route('/properties/create', methods=['GET', 'POST'])
@login_required
def create_property():
    if request.method == 'POST':
        try:
            is_available = True if request.form.get('is_available') == 'on' else False

            data = (
                float(request.form.get('price_properties')),
                request.form.get('lift_properties'),
                request.form.get('territory_comfort_properties'),
                float(request.form.get('area_properties')),
                int(request.form.get('build_year_properties')) if request.form.get('build_year_properties') else None,
                int(request.form.get('rooms_count_properties')),
                request.form.get('address_properties'),
                request.form.get('region_properties'),
                request.form.get('legal_aspects_properties'),
                int(request.form.get('floor_properties')),
                int(request.form.get('total_floors_properties')),
                int(request.form.get('owner_id')),
                request.form.get('property_type'),
                is_available
            )

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Properties (price_properties, lift_properties, territory_comfort_properties,
                                       area_properties, build_year_properties, rooms_count_properties,
                                       address_properties, region_properties, legal_aspects_properties,
                                       floor_properties, total_floors_properties, owner_id, property_type, is_available)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, data)
            conn.commit()
            flash('Объект успешно создан', 'success')
            return redirect(url_for('view_properties'))

        except Exception as e:
            flash(f'Ошибка при создании объекта: {str(e)}', 'danger')
        finally:
            if conn:
                cursor.close()
                conn.close()

    conn = get_db_connection()
    owners = []
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT client_id, name_client 
            FROM Clients 
            WHERE client_type IN ('Продавец', 'Арендодатель')
            ORDER BY name_client
        """)
        owners = cursor.fetchall()
    except Exception as e:
        flash(f'Ошибка загрузки владельцев: {str(e)}', 'danger')
    finally:
        if conn:
            cursor.close()
            conn.close()

    return render_template('properties/create.html', owners=owners)

@app.route('/properties/edit/<int:property_id>', methods=['GET', 'POST'])
@login_required
def edit_property(property_id):
    conn = get_db_connection()

    if request.method == 'POST':
        try:
            is_available = True if request.form.get('is_available') == 'on' else False

            data = (
                float(request.form.get('price_properties')),
                request.form.get('lift_properties'),
                request.form.get('territory_comfort_properties'),
                float(request.form.get('area_properties')),
                int(request.form.get('build_year_properties')) if request.form.get('build_year_properties') else None,
                int(request.form.get('rooms_count_properties')),
                request.form.get('address_properties'),
                request.form.get('region_properties'),
                request.form.get('legal_aspects_properties'),
                int(request.form.get('floor_properties')),
                int(request.form.get('total_floors_properties')),
                int(request.form.get('owner_id')),
                request.form.get('property_type'),
                is_available,
                property_id
            )

            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Properties 
                SET price_properties = %s, lift_properties = %s, territory_comfort_properties = %s,
                    area_properties = %s, build_year_properties = %s, rooms_count_properties = %s,
                    address_properties = %s, region_properties = %s, legal_aspects_properties = %s,
                    floor_properties = %s, total_floors_properties = %s, owner_id = %s,
                    property_type = %s, is_available = %s
                WHERE property_id = %s
            """, data)
            conn.commit()
            flash('Объект успешно обновлен', 'success')
            return redirect(url_for('view_properties'))

        except Exception as e:
            flash(f'Ошибка при обновлении объекта: {str(e)}', 'danger')
        finally:
            if conn:
                cursor.close()
                conn.close()

    property_data = None
    owners = []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Properties WHERE property_id = %s", (property_id,))
        property_data = cursor.fetchone()

        if not property_data:
            flash('Объект не найден', 'danger')
            return redirect(url_for('view_properties'))

        cursor.execute("""
            SELECT client_id, name_client 
            FROM Clients 
            WHERE client_type IN ('Продавец', 'Арендодатель')
            ORDER BY name_client
        """)
        owners = cursor.fetchall()

    except Exception as e:
        flash(f'Ошибка загрузки данных: {str(e)}', 'danger')
    finally:
        if conn:
            cursor.close()
            conn.close()

    return render_template('properties/edit.html', property=property_data, owners=owners)

@app.route('/deals')
@login_required
def view_deals():
    seller_filter = request.args.get('seller', '')
    buyer_filter = request.args.get('buyer', '')
    address_filter = request.args.get('address', '')
    type_filter = request.args.get('type', '')
    status_filter = request.args.get('status', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    conn = get_db_connection()
    deals = []
    sellers = []
    buyers = []
    deal_types = []
    statuses = []

    try:
        cursor = conn.cursor()

        query = """
            SELECT d.deal_id, c1.name_client as seller, c2.name_client as buyer,
                   p.address_properties, d.final_price, d.deal_type, d.status,
                   d.deal_date, d.description
            FROM Deals d
            JOIN Clients c1 ON d.owner_id = c1.client_id
            JOIN Clients c2 ON d.buyer_id = c2.client_id
            JOIN Properties p ON d.property_id = p.property_id
            WHERE 1=1
        """
        params = []

        if seller_filter:
            query += " AND c1.name_client ILIKE %s"
            params.append(f'%{seller_filter}%')

        if buyer_filter:
            query += " AND c2.name_client ILIKE %s"
            params.append(f'%{buyer_filter}%')

        if address_filter:
            query += " AND p.address_properties ILIKE %s"
            params.append(f'%{address_filter}%')

        if type_filter:
            query += " AND d.deal_type = %s"
            params.append(type_filter)

        if status_filter:
            query += " AND d.status = %s"
            params.append(status_filter)

        if min_price:
            query += " AND d.final_price >= %s"
            params.append(float(min_price))

        if max_price:
            query += " AND d.final_price <= %s"
            params.append(float(max_price))

        if date_from:
            query += " AND DATE(d.deal_date) >= %s"
            params.append(date_from)

        if date_to:
            query += " AND DATE(d.deal_date) <= %s"
            params.append(date_to)

        query += " ORDER BY d.deal_date DESC"

        cursor.execute(query, params)
        deals = cursor.fetchall()

        cursor.execute("""
            SELECT DISTINCT c1.name_client 
            FROM Deals d
            JOIN Clients c1 ON d.owner_id = c1.client_id
            ORDER BY c1.name_client
        """)
        sellers = [row[0] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT DISTINCT c2.name_client 
            FROM Deals d
            JOIN Clients c2 ON d.buyer_id = c2.client_id
            ORDER BY c2.name_client
        """)
        buyers = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT deal_type FROM Deals ORDER BY deal_type")
        deal_types = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT DISTINCT status FROM Deals ORDER BY status")
        statuses = [row[0] for row in cursor.fetchall()]

    except Exception as e:
        flash(f'Ошибка загрузки сделок: {str(e)}', 'danger')
    finally:
        if conn:
            cursor.close()
            conn.close()

    return render_template('deals/list.html',
                           deals=deals,
                           sellers=sellers,
                           buyers=buyers,
                           deal_types=deal_types,
                           statuses=statuses,
                           filters={
                               'seller': seller_filter,
                               'buyer': buyer_filter,
                               'address': address_filter,
                               'type': type_filter,
                               'status': status_filter,
                               'min_price': min_price,
                               'max_price': max_price,
                               'date_from': date_from,
                               'date_to': date_to
                           })

@app.route('/deals/create', methods=['GET', 'POST'])
@login_required
def create_deal():
    from datetime import datetime

    today = datetime.now().strftime('%Y-%m-%d')

    if request.method == 'POST':
        conn = None
        cursor = None
        try:
            deal_data = (
                int(request.form.get('owner_id')),
                int(request.form.get('buyer_id')),
                int(request.form.get('property_id')),
                session['agent_id'],
                float(request.form.get('final_price')),
                request.form.get('deal_type'),
                request.form.get('status'),
                request.form.get('deal_date') or today,
                request.form.get('description', '')
            )

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Deals (owner_id, buyer_id, property_id, agent_id,
                                 final_price, deal_type, status, deal_date, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, deal_data)
            conn.commit()
            flash('Сделка успешно создана', 'success')
            return redirect(url_for('view_deals'))

        except Exception as e:
            flash(f'Ошибка при создании сделки: {str(e)}', 'danger')
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    conn = get_db_connection()
    data = {'owners': [], 'buyers': [], 'properties': []}
    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT client_id, name_client 
            FROM Clients 
            WHERE client_type IN ('Продавец', 'Арендодатель')
            ORDER BY name_client
        """)
        data['owners'] = cursor.fetchall()

        cursor.execute("""
            SELECT client_id, name_client 
            FROM Clients 
            WHERE client_type IN ('Покупатель', 'Арендатор')
            ORDER BY name_client
        """)
        data['buyers'] = cursor.fetchall()

        cursor.execute("""
            SELECT property_id, address_properties, price_properties 
            FROM Properties 
            WHERE is_available = true
            ORDER BY address_properties
        """)
        data['properties'] = cursor.fetchall()

    except Exception as e:
        flash(f'Ошибка загрузки данных: {str(e)}', 'danger')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return render_template('deals/create.html',
                           owners=data['owners'],
                           buyers=data['buyers'],
                           properties=data['properties'],
                           today=today)

@app.route('/deals/edit/<int:deal_id>', methods=['GET', 'POST'])
@login_required
def edit_deal(deal_id):
    conn = get_db_connection()

    if request.method == 'POST':
        try:
            data = (
                int(request.form.get('owner_id')),
                int(request.form.get('buyer_id')),
                int(request.form.get('property_id')),
                float(request.form.get('final_price')),
                request.form.get('deal_type'),
                request.form.get('status'),
                request.form.get('deal_date'),
                request.form.get('description', ''),
                deal_id
            )

            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Deals 
                SET owner_id = %s, buyer_id = %s, property_id = %s,
                    final_price = %s, deal_type = %s, status = %s,
                    deal_date = %s, description = %s
                WHERE deal_id = %s
            """, data)
            conn.commit()
            flash('Сделка успешно обновлена', 'success')
            return redirect(url_for('view_deals'))

        except Exception as e:
            flash(f'Ошибка при обновлении сделки: {str(e)}', 'danger')
        finally:
            if conn:
                cursor.close()
                conn.close()

    deal_data = None
    owners = []
    buyers = []
    properties = []

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM Deals 
            WHERE deal_id = %s
        """, (deal_id,))
        deal_data = cursor.fetchone()

        if not deal_data:
            flash('Сделка не найдена', 'danger')
            return redirect(url_for('view_deals'))

        cursor.execute("""
            SELECT client_id, name_client 
            FROM Clients 
            WHERE client_type IN ('Продавец', 'Арендодатель')
            ORDER BY name_client
        """)
        owners = cursor.fetchall()

        cursor.execute("""
            SELECT client_id, name_client 
            FROM Clients 
            WHERE client_type IN ('Покупатель', 'Арендатор')
            ORDER BY name_client
        """)
        buyers = cursor.fetchall()

        cursor.execute("""
            SELECT property_id, address_properties 
            FROM Properties 
            ORDER BY address_properties
        """)
        properties = cursor.fetchall()

    except Exception as e:
        flash(f'Ошибка загрузки данных: {str(e)}', 'danger')
    finally:
        if conn:
            cursor.close()
            conn.close()

    return render_template('deals/edit.html',
                           deal=deal_data,
                           owners=owners,
                           buyers=buyers,
                           properties=properties)

@app.route('/clients')
@login_required
def view_clients():
    name_filter = request.args.get('name', '')
    type_filter = request.args.get('type', '')
    phone_filter = request.args.get('phone', '')
    email_filter = request.args.get('email', '')

    conn = get_db_connection()
    clients = []
    client_types = []

    try:
        cursor = conn.cursor()

        query = """
            SELECT client_id, name_client, client_type, phone_number, email
            FROM Clients
            WHERE 1=1
        """
        params = []

        if name_filter:
            query += " AND name_client ILIKE %s"
            params.append(f'%{name_filter}%')

        if type_filter:
            query += " AND client_type = %s"
            params.append(type_filter)

        if phone_filter:
            query += " AND phone_number ILIKE %s"
            params.append(f'%{phone_filter}%')

        if email_filter:
            query += " AND email ILIKE %s"
            params.append(f'%{email_filter}%')

        query += " ORDER BY name_client"

        cursor.execute(query, params)
        clients = cursor.fetchall()

        cursor.execute("SELECT DISTINCT client_type FROM Clients ORDER BY client_type")
        client_types = [row[0] for row in cursor.fetchall()]

    except Exception as e:
        flash(f'Ошибка загрузки клиентов: {str(e)}', 'danger')
    finally:
        if conn:
            cursor.close()
            conn.close()

    return render_template('clients/list.html',
                           clients=clients,
                           client_types=client_types,
                           filters={
                               'name': name_filter,
                               'type': type_filter,
                               'phone': phone_filter,
                               'email': email_filter
                           })

@app.route('/clients/create', methods=['GET', 'POST'])
@login_required
def create_client():
    if request.method == 'POST':
        try:
            data = (
                request.form.get('name_client'),
                request.form.get('client_type'),
                request.form.get('phone_number'),
                request.form.get('email')
            )

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO Clients (name_client, client_type, phone_number, email)
                VALUES (%s, %s, %s, %s)
            """, data)
            conn.commit()
            flash('Клиент успешно создан', 'success')
            return redirect(url_for('view_clients'))

        except Exception as e:
            flash(f'Ошибка при создании клиента: {str(e)}', 'danger')
        finally:
            if conn:
                cursor.close()
                conn.close()

    return render_template('clients/create.html')

@app.route('/clients/edit/<int:client_id>', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    conn = get_db_connection()

    if request.method == 'POST':
        try:
            data = (
                request.form.get('name_client'),
                request.form.get('client_type'),
                request.form.get('phone_number'),
                request.form.get('email'),
                client_id
            )

            cursor = conn.cursor()
            cursor.execute("""
                UPDATE Clients 
                SET name_client = %s, client_type = %s, phone_number = %s, email = %s
                WHERE client_id = %s
            """, data)
            conn.commit()
            flash('Клиент успешно обновлен', 'success')
            return redirect(url_for('view_clients'))

        except Exception as e:
            flash(f'Ошибка при обновлении клиента: {str(e)}', 'danger')
        finally:
            if conn:
                cursor.close()
                conn.close()

    client_data = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Clients WHERE client_id = %s", (client_id,))
        client_data = cursor.fetchone()

        if not client_data:
            flash('Клиент не найден', 'danger')
            return redirect(url_for('view_clients'))

    except Exception as e:
        flash(f'Ошибка загрузки клиента: {str(e)}', 'danger')
    finally:
        if conn:
            cursor.close()
            conn.close()

    return render_template('clients/edit.html', client=client_data)

@app.route('/documents')
@login_required
def view_documents():
    flash('Этот модуль в разработке', 'info')
    return redirect(url_for('dashboard'))

@app.route('/documents/create', methods=['GET', 'POST'])
@login_required
def create_document():
    flash('Этот модуль в разработке', 'info')
    return redirect(url_for('dashboard'))

@app.route('/profile')
@login_required
def profile():
    conn = get_db_connection()
    agent = None
    deals = []
    clients_count = 0

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT agent_id, name_agent, surname_agent, patronymic_agent,
                   work_experience, phone_number_agent, email_agent
            FROM Agents
            WHERE agent_id = %s
        """, (session['agent_id'],))
        agent = cursor.fetchone()

        if agent:
            cursor.execute("""
                SELECT d.deal_id, c1.name_client as seller, p.address_properties, 
                       d.final_price, d.status, d.deal_date
                FROM Deals d
                JOIN Clients c1 ON d.owner_id = c1.client_id
                JOIN Properties p ON d.property_id = p.property_id
                WHERE d.agent_id = %s
                ORDER BY d.deal_date DESC
            """, (session['agent_id'],))
            deals = cursor.fetchall()

            cursor.execute("""
                SELECT COUNT(DISTINCT r.client_id) 
                FROM Requests r
                WHERE r.agent_id = %s
            """, (session['agent_id'],))
            request_clients = cursor.fetchone()[0] or 0

            cursor.execute("""
                SELECT COUNT(DISTINCT d.owner_id) + COUNT(DISTINCT d.buyer_id)
                FROM Deals d
                WHERE d.agent_id = %s
            """, (session['agent_id'],))
            deal_clients_result = cursor.fetchone()
            deal_clients = (deal_clients_result[0] if deal_clients_result else 0) or 0

            clients_count = max(request_clients, deal_clients)

    except Exception as e:
        flash(f'Ошибка загрузки профиля: {str(e)}', 'danger')
    finally:
        if conn:
            cursor.close()
            conn.close()

    return render_template('profile/edit.html',
                           agent=agent,
                           deals=deals,
                           clients_count=clients_count)

if __name__ == '__main__':
    print("Проверяем подключение к PostgreSQL...")
    conn = get_db_connection()
    if conn:
        print("✅ Подключение успешно!")
        conn.close()
    else:
        print("⚠️ Не удалось подключиться к PostgreSQL.")

    app.run(debug=True, host='127.0.0.1', port=5252)