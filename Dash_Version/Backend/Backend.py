
from functools import cache
from cachetools import Cache
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from sqlalchemy import text
from flask_caching import Cache
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)

# Datenbank-Konfiguration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:database123!@localhost/Database1.1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Engine und Session konfigurieren
engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], pool_size=20, max_overflow=20, pool_timeout=30, pool_recycle=3600)
Session = sessionmaker(bind=engine)
db = SQLAlchemy(app)


# Indexe erstellen
def create_indexes():
    with engine.connect() as connection:
        # Indexe für Tabelle orders
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_orders_orderdate ON orders(orderdate);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_orders_storeid ON orders(storeid);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_orders_customerid ON orders(customerid);"))
        
        # Indexe für Tabelle stores
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_stores_storeid ON stores(storeid);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_stores_latitude ON stores(latitude);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_stores_longitude ON stores(longitude);"))
        
        # Indexe für Tabelle customers
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_customers_customerid ON customers(customerid);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_customers_latitude ON customers(latitude);"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_customers_longitude ON customers(longitude);"))
        
        # Indexe für Tabelle products
        connection.execute(text("CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);"))

create_indexes()

# Cache-Konfiguration
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300
cache = Cache(app)

@app.route('/api/top_5_stores')
@cache.cached(timeout=300)
def get_top_stores():
    try:
        query = text("""
            WITH yearly_sales AS (
                SELECT
                    storeid,
                    EXTRACT(YEAR FROM orderdate) AS year,
                    SUM(total) AS annual_sales
                FROM orders
                WHERE EXTRACT(YEAR FROM orderdate) IN (2020, 2021, 2022)
                GROUP BY storeid, EXTRACT(YEAR FROM orderdate)
            )
            SELECT s.storeid, s.year, s.annual_sales
            FROM (
                SELECT storeid, year, annual_sales,
                       ROW_NUMBER() OVER (PARTITION BY year ORDER BY annual_sales DESC) AS rank
                FROM yearly_sales
            ) s
            WHERE s.rank <= 5
            ORDER BY s.year, s.annual_sales DESC;
        """)
        result = db.session.execute(query)
        data = result.fetchall()
        top_stores = [{'storeid': row[0], 'year': int(row[1]), 'annual_sales': row[2]} for row in data]
        return jsonify({'top_5_stores': top_stores})
    except Exception as e:
        print(f"Fehler beim Abrufen der Daten: {e}")  # Debugging-Ausgabe
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})
    
    
# Worst 5 Stores
@app.route('/api/worst_5_stores')
@cache.cached(timeout=300)
def get_worst_stores():
    try:
        query = text("""
            WITH yearly_sales AS (
                SELECT
                    storeid,
                    EXTRACT(YEAR FROM orderdate) AS year,
                    SUM(total) AS annual_sales
                FROM orders
                WHERE EXTRACT(YEAR FROM orderdate) IN (2020, 2021, 2022)
                GROUP BY storeid, EXTRACT(YEAR FROM orderdate)
            )
            SELECT s.storeid, s.year, s.annual_sales
            FROM (
                SELECT storeid, year, annual_sales,
                       ROW_NUMBER() OVER (PARTITION BY year ORDER BY annual_sales ASC) AS rank
                FROM yearly_sales
            ) s
            WHERE s.rank <= 5
            ORDER BY s.year, s.annual_sales ASC;
        """)
        result = db.session.execute(query)
        data = result.fetchall()
        worst_stores = [{'storeid': row[0], 'year': int(row[1]), 'annual_sales': row[2]} for row in data]
        return jsonify({'worst_5_stores': worst_stores})
    except Exception as e:
        print(f"Fehler beim Abrufen der Daten: {e}")  # Debugging-Ausgabe
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})



# Store Locations
@app.route('/api/store_locations')
@cache.cached(timeout=300)
def store_locations():
    try:
        query = text("""
            SELECT city, AVG(latitude) AS avg_latitude, AVG(longitude) AS avg_longitude
            FROM stores
            GROUP BY city
            ORDER BY city;
        """)
        result = db.session.execute(query)
        data = result.fetchall()
        locations = [{'city': row[0], 'avg_latitude': float(row[1]), 'avg_longitude': float(row[2])} for row in data]
        return jsonify({'store_locations': locations})
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})

# Customer Locations
@app.route('/api/customer_locations')
@cache.cached(timeout=300)
def customer_locations():
    try:
        query = text("""
            SELECT latitude, longitude
            FROM customers
            ORDER BY latitude, longitude;
        """)
        result = db.session.execute(query)
        data = result.fetchall()
        locations = [{'latitude': row[0], 'longitude': row[1]} for row in data]
        return jsonify({'customer_locations': locations})
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})

@app.route('/api/store_annual_revenues')
@cache.cached(timeout=300)
def store_annual_revenues():
    try:
        query = text("""
            SELECT
                s.storeid,
                s.city,
                s.latitude,
                s.longitude,
                SUM(CASE WHEN EXTRACT(YEAR FROM o.orderdate) = 2018 THEN o.total ELSE 0 END) AS revenue_2018,
                SUM(CASE WHEN EXTRACT(YEAR FROM o.orderdate) = 2019 THEN o.total ELSE 0 END) AS revenue_2019,
                SUM(CASE WHEN EXTRACT(YEAR FROM o.orderdate) = 2020 THEN o.total ELSE 0 END) AS revenue_2020,
                SUM(CASE WHEN EXTRACT(YEAR FROM o.orderdate) = 2021 THEN o.total ELSE 0 END) AS revenue_2021,
                SUM(CASE WHEN EXTRACT(YEAR FROM o.orderdate) = 2022 THEN o.total ELSE 0 END) AS revenue_2022
            FROM
                stores s
            JOIN
                orders o ON s.storeid = o.storeid
            GROUP BY
                s.storeid, s.city, s.latitude, s.longitude
            ORDER BY
                s.city;
        """)
        result = db.session.execute(query)
        data = result.fetchall()
        annual_revenues = [{
            'storeid': row[0],
            'city': row[1],
            'latitude': row[2],
            'longitude': row[3],
            'revenue_2018': row[4],
            'revenue_2019': row[5],
            'revenue_2020': row[6],
            'revenue_2021': row[7],
            'revenue_2022': row[8]
        } for row in data]
        return jsonify({'store_annual_revenues': annual_revenues})
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})
    
# Scatter Plot
@app.route('/api/scatterplot')
@cache.cached(timeout=300)
def get_store_data():
    try:
        revenue_query = text("""
            SELECT 
                stores.storeid,
                EXTRACT(YEAR FROM orders.orderdate) AS year,
                SUM(orders.nitems * products.price) AS revenue
            FROM 
                stores
            JOIN 
                orders ON stores.storeid = orders.storeid
            JOIN 
                orderitems ON orders.orderid = orderitems.orderid
            JOIN 
                products ON orderitems.sku = products.sku
            GROUP BY 
                stores.storeid, EXTRACT(YEAR FROM orders.orderdate)
            ORDER BY 
                stores.storeid, year;
        """)

        order_count_query = text("""
            SELECT
                stores.storeid,
                EXTRACT(YEAR FROM orders.orderdate) AS year,
                COUNT(DISTINCT orders.orderid) AS order_count  
            FROM
                stores
            JOIN
                orders ON stores.storeid = orders.storeid
            GROUP BY
                stores.storeid, EXTRACT(YEAR FROM orders.orderdate)
            ORDER BY
                stores.storeid, year;
        """)

        revenue_result = db.session.execute(revenue_query)
        order_count_result = db.session.execute(order_count_query)

        revenue_data = {
            (row.storeid, row.year): row.revenue for row in revenue_result
        }
        order_data = {
            (row.storeid, row.year): row.order_count for row in order_count_result
        }
        combined_data = []
        for (storeid, year), revenue in revenue_data.items():
            order_count = order_data.get((storeid, year), 0)
            combined_data.append({
                "storeid": storeid,
                "year": year,
                "revenue": revenue,
                "order_count": order_count
            })

        return jsonify(combined_data)
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})


# Metriken Anbindung
@app.route('/api/metrics')
def get_metrics():
    try:
        # Total customers query
        total_customers_query = text("""
            SELECT COUNT(*) FROM customers;
        """)
        total_customers_result = db.session.execute(total_customers_query).scalar()

        # Total revenue query
        total_revenue_query = text("""
            SELECT SUM(o.total) FROM orders o;
        """)
        total_revenue_result = db.session.execute(total_revenue_query).scalar()

        # Average revenue per store query
        average_revenue_per_store_query = text("""
            SELECT AVG(total_revenue) FROM (
                SELECT SUM(o.total) AS total_revenue
                FROM orders o
                GROUP BY o.storeid
            ) AS store_revenues;
        """)
        average_revenue_per_store_result = db.session.execute(average_revenue_per_store_query).scalar()

      # Median revenue from stores in 2022
        median_revenue_from_stores_query = text("""
       WITH StoreRevenues AS (
        SELECT
            o.storeid,
            SUM(p.price * o.nitems) AS total_revenue 
        FROM
            orders o
            JOIN orderitems oi ON o.orderid = oi.orderid
            JOIN products p ON oi.sku = p.sku
        WHERE
            EXTRACT(YEAR FROM o.orderdate) = 2022 
        GROUP BY
            o.storeid
    ),
    RankedRevenues AS (
        SELECT
            storeid,
            total_revenue,
            ROW_NUMBER() OVER (ORDER BY total_revenue) AS row_num,
            COUNT(*) OVER () AS total_rows
        FROM
            StoreRevenues
    )
    SELECT
        AVG(total_revenue) AS median_revenue
    FROM
        RankedRevenues
    WHERE
        row_num IN (FLOOR((total_rows + 1) / 2), CEIL((total_rows + 1) / 2));""")
        median_revenue_from_stores_result = db.session.execute(median_revenue_from_stores_query).scalar()



        # Neukunden 2021 und 2022 query
        new_customers_query = text("""
            WITH first_orders AS (
                SELECT 
                    customerid, 
                    MIN(orderdate) AS first_order_date
                FROM 
                    orders
                GROUP BY 
                    customerid
            ),
            customers_pre_2021 AS (
                SELECT 
                    customerid
                FROM 
                    first_orders
                WHERE 
                    EXTRACT(YEAR FROM first_order_date) < 2021
            ),
            customers_2021 AS (
                SELECT 
                    customerid
                FROM 
                    first_orders
                WHERE 
                    EXTRACT(YEAR FROM first_order_date) = 2021
            ),
            customers_2022 AS (
                SELECT 
                    customerid
                FROM 
                    first_orders
                WHERE 
                    EXTRACT(YEAR FROM first_order_date) = 2022
            ),
            new_customers_2021 AS (
                SELECT 
                    COUNT(DISTINCT customers_2021.customerid) AS count
                FROM 
                    customers_2021
                LEFT JOIN 
                    customers_pre_2021
                ON 
                    customers_2021.customerid = customers_pre_2021.customerid
                WHERE 
                    customers_pre_2021.customerid IS NULL
            ),
            new_customers_2022 AS (
                SELECT 
                    COUNT(DISTINCT customers_2022.customerid) AS count
                FROM 
                    customers_2022
                LEFT JOIN 
                    customers_2021
                ON 
                    customers_2022.customerid = customers_2021.customerid
                WHERE 
                    customers_2021.customerid IS NULL
            )
            SELECT 
                new_customers_2021.count AS new_customers_2021,
                new_customers_2022.count AS new_customers_2022
            FROM 
                new_customers_2021, new_customers_2022;
        """)
        new_customers_result = db.session.execute(new_customers_query).fetchone()

        # Total revenue per year query
        total_revenue_per_year_query = text("""
            SELECT 
                EXTRACT(YEAR FROM orderdate) AS year,
                SUM(total) AS total_revenue
            FROM 
                orders
            WHERE 
                EXTRACT(YEAR FROM orderdate) IN (2021, 2022)
            GROUP BY 
                year
            ORDER BY 
                year;
        """)
        total_revenue_per_year_result = db.session.execute(total_revenue_per_year_query).fetchall()

        # Average revenue per store per year query
        average_revenue_per_store_per_year_query = text("""
            SELECT EXTRACT(YEAR FROM orderdate) AS Jahr, SUM(total) / 32 AS Durchschnittsumsatz_pro_Store
            FROM orders
            WHERE EXTRACT(YEAR FROM orderdate) IN (2021, 2022)
            GROUP BY EXTRACT(YEAR FROM orderdate)
            ORDER BY Jahr;
        """)
        average_revenue_per_store_per_year_result = db.session.execute(average_revenue_per_store_per_year_query).fetchall()

        # Convert results to float and int
        total_customers = int(total_customers_result)
        total_revenue = float(total_revenue_result)
        average_revenue_per_store = float(average_revenue_per_store_result)
        new_customers_2021 = int(new_customers_result[0])
        new_customers_2022 = int(new_customers_result[1])
        median_revenue_from_stores = int(median_revenue_from_stores_result)

        total_revenue_per_year = {row[0]: float(row[1]) for row in total_revenue_per_year_result}
        average_revenue_per_store_per_year = {row[0]: float(row[1]) for row in average_revenue_per_store_per_year_result}

        # Berechnung der prozentualen Veränderung
        total_revenue_2021 = total_revenue_per_year.get(2021, 1)
        total_revenue_2022 = total_revenue_per_year.get(2022, 1)
        total_revenue_change = (total_revenue_2022 - total_revenue_2021) / total_revenue_2021 * 100

        avg_revenue_per_store_2021 = average_revenue_per_store_per_year.get(2021, 1)
        avg_revenue_per_store_2022 = average_revenue_per_store_per_year.get(2022, 1)
        avg_revenue_per_store_change = (avg_revenue_per_store_2022 - avg_revenue_per_store_2021) / avg_revenue_per_store_2021 * 100

        new_customers_change = (new_customers_2022 - new_customers_2021) / new_customers_2021 * 100 if new_customers_2021 else 0

        return jsonify({
    'total_customers': total_customers,
    'total_revenue': total_revenue,
    'average_revenue_per_store': average_revenue_per_store,
    'median_revenue_from_stores_2022': median_revenue_from_stores,  # Korrekte Schlüssel-Name
    'new_customers_2021': new_customers_2021,
    'new_customers_2022': new_customers_2022,
    'total_revenue_2022': total_revenue_2022,
    'total_revenue_change': total_revenue_change,
    'avg_revenue_per_store_2022': avg_revenue_per_store_2022,
    'avg_revenue_per_store_change': avg_revenue_per_store_change,
    'new_customers_change': new_customers_change
})

    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})

@app.route('/api/store_monthly_revenues')
@cache.cached(timeout=300)
def store_monthly_revenues():
    try:
        query = text("""
            SELECT
                s.storeid,
                s.city,
                s.latitude,
                s.longitude,
                to_char(o.orderdate, 'YYYY-MM') AS month,  -- Get year and month
                SUM(o.total) AS revenue                             -- Calculate total revenue
            FROM
                stores s
            JOIN
                orders o ON s.storeid = o.storeid
            GROUP BY
                s.storeid, s.city, s.latitude, s.longitude, to_char(o.orderdate, 'YYYY-MM')
            ORDER BY
                s.city, month; -- Order by city and then by month
        """)

        result = db.session.execute(query)
        data = result.fetchall()

        monthly_revenues = {}
        for row in data:
            store_id = row[0]
            city = row[1]
            latitude = row[2]
            longitude = row[3]
            month = row[4]
            revenue = row[5]

            if store_id not in monthly_revenues:
                monthly_revenues[store_id] = {
                    'storeid': store_id,
                    'city': city,
                    'latitude': latitude,
                    'longitude': longitude,
                    'monthly_revenues': {}  
                }
            monthly_revenues[store_id]['monthly_revenues'][month] = revenue

        return jsonify({'store_monthly_revenues': list(monthly_revenues.values())})

    except Exception as e:
        return jsonify({'error': f"Error fetching data: {e}"})


# Tabelle für top n kategories
@app.route('/api/pizza_orders')
@cache.cached(timeout=300)
def pizza_orders():
    try:
        query = text("""
            SELECT
                p.category AS pizza_category,
                EXTRACT(YEAR FROM o.orderdate) AS order_year,
                COUNT(*) AS total_orders
            FROM
                orderitems oi
            JOIN
                products p ON oi.sku = p.sku
            JOIN
                orders o ON oi.orderid = o.orderid
            WHERE
                p.name LIKE '%Pizza%'
                AND EXTRACT(YEAR FROM o.orderdate) IN (2020, 2021, 2022)
            GROUP BY
                p.category, EXTRACT(YEAR FROM o.orderdate)
            ORDER BY
                order_year, total_orders DESC;
        """)
        result = db.session.execute(query)
        data = result.fetchall()

        pizza_orders_by_category = [{'pizza_category': row[0], 'order_year': int(row[1]), 'total_orders': row[2]} for row in data]
        return jsonify({'pizza_orders_by_category': pizza_orders_by_category})
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})


# Table Top 5 Stores
@app.route('/api/top_5_stores')
@cache.cached(timeout=300)
def top_5_stores():
    try:
        query = text("""
            WITH yearly_sales AS (
                SELECT
                    storeid,
                    EXTRACT(YEAR FROM orderdate) AS year,
                    SUM(total) AS annual_sales
                FROM orders
                WHERE EXTRACT(YEAR FROM orderdate) IN (2020, 2021, 2022)
                GROUP BY storeid, EXTRACT(YEAR FROM orderdate)
            )
            SELECT s.storeid, s.year, s.annual_sales
            FROM (
                SELECT storeid, year, annual_sales,
                       ROW_NUMBER() OVER (PARTITION BY year ORDER BY annual_sales DESC) AS rank
                FROM yearly_sales
            ) s
            WHERE s.rank <= 5
            ORDER BY s.year, s.annual_sales DESC;
        """)
        result = db.session.execute(query)
        data = result.fetchall()
        top_stores = [{'storeid': row[0], 'year': row[1], 'annual_sales': row[2]} for row in data]
        return jsonify({'top_5_stores': top_stores})
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})

@app.route('/api/worst_5_stores')
@cache.cached(timeout=300)
def worst_5_stores():
    try:
        query = text("""
            WITH yearly_sales AS (
                SELECT
                    storeid,
                    EXTRACT(YEAR FROM orderdate) AS year,
                    SUM(total) AS annual_sales
                FROM orders
                WHERE EXTRACT(YEAR FROM orderdate) IN (2020, 2021, 2022)
                GROUP BY storeid, EXTRACT(YEAR FROM orderdate)
            )
            SELECT s.storeid, s.year, s.annual_sales
            FROM (
                SELECT storeid, year, annual_sales,
                       ROW_NUMBER() OVER (PARTITION BY year ORDER BY annual_sales ASC) AS rank
                FROM yearly_sales
            ) s
            WHERE s.rank <= 5
            ORDER BY s.year, s.annual_sales ASC;
        """)
        result = db.session.execute(query)
        data = result.fetchall()
        worst_stores = [{'storeid': row[0], 'year': row[1], 'annual_sales': row[2]} for row in data]
        return jsonify({'worst_5_stores': worst_stores})
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})

# Donut Chart
@app.route('/api/revenues_by_pizza_type')
@cache.cached(timeout=300)
def revenues_by_pizza_type():
    try:
        query = text("""
            WITH oi_summary AS (
                SELECT 
                    oi.sku, 
                    COUNT(oi.sku) AS count_oi,
                    o.orderdate
                FROM 
                    orderitems oi
                JOIN 
                    orders o ON oi.orderid = o.orderid
                WHERE 
                    EXTRACT(YEAR FROM o.orderdate) IN (2020, 2021, 2022)
                GROUP BY 
                    oi.sku, o.orderdate
            )
            SELECT
                p.name AS pizza_name,
                EXTRACT(YEAR FROM oi_summary.orderdate) AS order_year,
                SUM(oi_summary.count_oi * p.price) AS total_revenue
            FROM 
                oi_summary
            JOIN 
                products p ON oi_summary.sku = p.sku
            GROUP BY
                p.name, EXTRACT(YEAR FROM oi_summary.orderdate)
            ORDER BY
                order_year, total_revenue DESC;
        """)
        result = db.session.execute(query)
        data = result.fetchall()
        revenues = [{'pizza_name': row[0], 'order_year': row[1], 'total_revenue': row[2]} for row in data]
        return jsonify({'revenues_by_pizza_type': revenues})
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})


@app.route('/api/store_yearly_avg_orders')
@cache.cached(timeout=300)
def store_yearly_avg_orders():
    try:
        query = text("""
            SELECT
                s.storeid,
                s.city, 
                EXTRACT(YEAR FROM o.orderdate) AS order_year,
                ROUND(COUNT(DISTINCT o.orderid)::numeric / COUNT(DISTINCT o.customerid)::numeric, 2) AS avg_orders_per_customer
            FROM stores s
            JOIN orders o ON s.storeid = o.storeid
            GROUP BY s.storeid, s.city, EXTRACT(YEAR FROM o.orderdate);
        """)
        result = db.session.execute(query)
        store_data = []
        for row in result:
            storeid = row[0]
            city = row[1]
            year = int(row[2])
            avg_orders = float(row[3])
            store_data.append({
                'storeid': storeid,
                'city': city,
                'year': year,
                'avg_orders_per_customer': avg_orders
            })
        return jsonify(store_data)
    except Exception as e:
        app.logger.error(f"Error fetching data: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/store_ids')
@cache.cached(timeout=300)
def get_store_ids():
    try:
        query = text("SELECT storeid FROM stores;")
        result = db.session.execute(query)
        store_ids = [row[0] for row in result.fetchall()]
        return jsonify({'store_ids': store_ids})
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Store-IDs: {e}"})

# Scatter Plot Pizza
@app.route('/api/scatter_plot_pizzen')
@cache.cached(timeout=300)
def scatterplot_data():
    try:
        query = text("""
            SELECT
                p.name AS pizza_name,
                p.size AS pizza_size,
                SUM(o.nitems) AS total_sold,
                SUM(o.nitems * p.price) AS total_revenue
            FROM products p
            JOIN orderitems oi ON p.sku = oi.sku
            JOIN orders o ON oi.orderid = o.orderid
            GROUP BY p.name, p.size;
        """)
        data = db.session.execute(query)
        data_for_frontend = [{'pizza_name': row[0], 'pizza_size': row[1], 'total_sold': row[2], 'total_revenue': row[3]} for row in data]
        return jsonify(data_for_frontend)
    except Exception as e:
        return jsonify({"error": f"Error fetching data: {str(e)}"}), 500

@app.route('/api/store_orders_per_hour')
@cache.cached(timeout=300)
def store_orders_per_hour():
    try:
        query = text("""
            SELECT
                storeid,
                EXTRACT(hour FROM (orderdate AT TIME ZONE 'UTC' AT TIME ZONE 'America/Los_Angeles')) AS order_hour,
                EXTRACT(YEAR FROM orderdate) AS order_year,
                COUNT(*) AS total_orders_per_hour
            FROM orders
            WHERE EXTRACT(YEAR FROM orderdate) IN (2020, 2021, 2022)
            GROUP BY
                storeid,
                EXTRACT(hour FROM (orderdate AT TIME ZONE 'UTC' AT TIME ZONE 'America/Los_Angeles')),
                EXTRACT(YEAR FROM orderdate)
            ORDER BY
                storeid,
                order_year,
                order_hour;
        """)
        result = db.session.execute(query)
        data = result.fetchall()
        orders_per_hour = [{
            'storeid': row[0],
            'order_hour': row[1],
            'order_year': row[2],  # Add this line to include order_year
            'total_orders_per_hour': row[3]
        } for row in data]
        return jsonify({'store_orders_per_hour': orders_per_hour})
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})


@app.route('/api/revenue_per_weekday')
@cache.cached(timeout=300)
def revenue_per_weekday():
    try:
        query = text("""
            SELECT
                o.storeid,
                (EXTRACT(DOW FROM o.orderdate) + 6) % 7 AS order_day_of_week,  -- Montag als erster Tag der Woche (0=Montag, 6=Sonntag)
                EXTRACT(YEAR FROM o.orderdate) AS order_year,
                SUM(o.total) AS total_revenue
            FROM orders o
            WHERE EXTRACT(YEAR FROM o.orderdate) IN (2020, 2021, 2022)
            GROUP BY o.storeid, (EXTRACT(DOW FROM o.orderdate) + 6) % 7, EXTRACT(YEAR FROM o.orderdate)
            ORDER BY o.storeid, order_year, order_day_of_week;
        """)
        result = db.session.execute(query)
        data = result.fetchall()
        revenue_data = [{'storeid': row[0], 'order_day_of_week': row[1], 'order_year': row[2], 'total_revenue': row[3]} for row in data]
        return jsonify({'revenue_per_weekday': revenue_data})
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})

@app.route('/api/boxplot_metrics')
@cache.cached(timeout=300)
def boxplot_data_metrics():
    try:
        query = text("""
            SELECT customers.customerid, products.name AS pizza_name, COUNT(*) AS order_count
            FROM customers
            JOIN orders ON customers.customerid = orders.customerid
            JOIN orderitems ON orders.orderid = orderitems.orderid
            JOIN products ON orderitems.sku = products.sku
            GROUP BY customers.customerid, products.name
            HAVING COUNT(*) > 1 
            ORDER BY order_count DESC;
        """)
        data = db.session.execute(query)
        df = pd.DataFrame(data, columns=["customerid", "pizza_name", "order_count"])
        boxplot_data = {}
        for pizza in df["pizza_name"].unique():
            pizza_orders = df[df["pizza_name"] == pizza]["order_count"]
            desc = pizza_orders.describe()
            iqr = desc["75%"] - desc["25%"]
            boxplot_data[pizza] = {
                "min": float(desc["min"]),
                "lower_whisker": float(max(desc["min"], desc["25%"] - 1.5 * iqr)),
                "q1": float(desc["25%"]),
                "median": float(desc["50%"]),
                "q3": float(desc["75%"]),
                "upper_whisker": float(min(desc["max"], desc["75%"] + 1.5 * iqr)),
                "max": float(desc["max"]),
                "iqr": float(iqr)
            }
        return jsonify(boxplot_data) 
    except Exception as e:
        return jsonify({"error": f"Error fetching data: {str(e)}"}), 500
    
def calculate_rfm_for_2022_by_store(df):
    rfm_results = {}
    
    for store_id in df['storeid'].unique():
        store_df = df[df['storeid'] == store_id].copy()
        store_df['orderdate'] = pd.to_datetime(store_df['orderdate'])
        store_df['total_amount'] = store_df['total_amount'].astype(float)
        current_date = store_df['orderdate'].max() + pd.DateOffset(1)
        
        rfm = store_df.groupby('customerid').agg({
            'orderdate': lambda x: (current_date - x.max()).days,
            'orderid': 'count',
            'total_amount': 'sum'
        }).reset_index()
        
        rfm.columns = ['customerid', 'recency', 'frequency', 'monetary']
        rfm['r_score'] = pd.qcut(rfm['recency'], 4, labels=['1', '2', '3', '4'])
        rfm['f_score'] = pd.qcut(rfm['frequency'].rank(method='first'), 4, labels=['4', '3', '2', '1'])
        rfm['m_score'] = pd.qcut(rfm['monetary'], 4, labels=['4', '3', '2', '1'])
        rfm['rfm_score'] = rfm['r_score'].astype(str) + rfm['f_score'].astype(str) + rfm['m_score'].astype(str)
        
        # Segment customers into four groups based on RFM score
        rfm['segment'] = pd.qcut(rfm['rfm_score'].rank(method='first'), 4, labels=['1', '2', '3', '4'])
        
        # Aggregate the data by segment
        segment_agg = rfm.groupby('segment').agg({
            'customerid': 'count',
            'recency': 'mean',
            'frequency': 'mean',
            'monetary': 'mean'
        }).reset_index()
        
        segment_agg.columns = ['segment', 'customer_count', 'avg_recency', 'avg_frequency', 'avg_monetary']
        rfm_results[store_id] = segment_agg
    
    return rfm_results

@app.route('/api/rfm_segments')
@cache.cached(timeout=300)
def get_rfm_segments():
    try:
        store_id = request.args.get('store_id')
        
        query = text("""
            SELECT
                s.storeid,
                o.customerid,
                o.orderid,
                o.orderdate,
                SUM(p.price * o.nitems) as total_amount
            FROM
                stores s
            JOIN
                orders o ON s.storeid = o.storeid
            JOIN
                orderitems oi ON o.orderid = oi.orderid
            JOIN
                products p ON oi.sku = p.sku
            WHERE
                EXTRACT(YEAR FROM o.orderdate) = 2022
            GROUP BY
                s.storeid, o.customerid, o.orderid, o.orderdate
            ORDER BY
                s.storeid, o.customerid, o.orderdate;
        """)
        result = db.session.execute(query)
        data = result.fetchall()

        # Convert the data to a DataFrame
        df = pd.DataFrame(data, columns=['storeid', 'customerid', 'orderid', 'orderdate', 'total_amount'])

        # Calculate RFM Scores for 2022 by Store
        rfm_scores = calculate_rfm_for_2022_by_store(df)

        # Prepare the response in the desired structure
        rfm_response = []
        for storeid, rfm_df in rfm_scores.items():
            store_rfm_data = {
                'storeid': storeid,
                'rfm_data': rfm_df.to_dict(orient='records')
            }
            rfm_response.append(store_rfm_data)

        return jsonify({'rfm_segments': rfm_response})
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})


if __name__ == '__main__':
    app.run(debug=True)
