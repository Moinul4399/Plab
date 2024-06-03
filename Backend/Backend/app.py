from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import plotly.graph_objects as go

app = Flask(__name__)

# Datenbank-Konfiguration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:Moinul439!!@localhost/pizzadatabase'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

@app.route('/api/top_stores')
def get_top_stores():
    try:
        query = text("""
            SELECT
                s.storeID,
                s.zipcode,
                s.state_abbr,
                s.city,
                s.state,
                SUM(p.Price) AS total_revenue
            FROM
                stores s
            JOIN
                orders o ON s.storeID = o.storeID
            JOIN
                orderItems oi ON o.orderID = oi.orderID
            JOIN
                products p ON oi.SKU = p.SKU
            GROUP BY
                s.storeID,
                s.zipcode,
                s.state_abbr,
                s.city,
                s.state
            ORDER BY
                total_revenue DESC
            LIMIT 10;
        """)
        result = db.session.execute(query)
        data = result.fetchall()
        top_stores = [{'storeID': row[0], 'zipcode': row[1], 'state_abbr': row[2], 'city': row[3], 'state': row[4], 'total_revenue': row[5]} for row in data]
        return jsonify({'top_stores': top_stores})
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})

@app.route('/api/store_locations')
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
        locations = [{'city': row[0], 'latitude': float(row[1]), 'longitude': float(row[2])} for row in data]
        return jsonify({'store_locations': locations})
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})

@app.route('/api/customer_locations')
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
def store_annual_revenues():
    try:
        query = text("""
            SELECT
                s.storeid,
                s.city,
                s.latitude,
                s.longitude,
                SUM(CASE WHEN EXTRACT(YEAR FROM o.orderdate_date) = 2018 THEN o.total ELSE 0 END) AS revenue_2018,
                SUM(CASE WHEN EXTRACT(YEAR FROM o.orderdate_date) = 2019 THEN o.total ELSE 0 END) AS revenue_2019,
                SUM(CASE WHEN EXTRACT(YEAR FROM o.orderdate_date) = 2020 THEN o.total ELSE 0 END) AS revenue_2020,
                SUM(CASE WHEN EXTRACT(YEAR FROM o.orderdate_date) = 2021 THEN o.total ELSE 0 END) AS revenue_2021,
                SUM(CASE WHEN EXTRACT(YEAR FROM o.orderdate_date) = 2022 THEN o.total ELSE 0 END) AS revenue_2022
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

@app.route('/api/store_orders_per_hour')
def store_orders_per_hour():
    try:
        query = text("""
            SELECT
                storeid,
                (EXTRACT(DOW FROM orderdate_date) + 6) % 7 AS order_day_of_week,
                EXTRACT(hour FROM orderdate_time) AS order_hour,
                SUM(total_orders) AS total_orders_per_hour
            FROM (
                SELECT
                    storeid,
                    orderdate_date,
                    orderdate_time,
                    COUNT(*) AS total_orders
                FROM
                    orders
                GROUP BY
                    storeid, orderdate_date, orderdate_time
            ) aggregated_orders
            GROUP BY
                storeid,
                (EXTRACT(DOW FROM orderdate_date) + 6) % 7,
                EXTRACT(hour FROM orderdate_time)
            ORDER BY
                storeid, order_day_of_week, order_hour;
        """)
        result = db.session.execute(query)
        data = result.fetchall()
        orders_per_hour = [{
            'storeid': row[0],
            'order_day_of_week': row[1],
            'order_hour': row[2],
            'total_orders_per_hour': row[3]
        } for row in data]
        return jsonify({'store_orders_per_hour': orders_per_hour})
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})

@app.route('/api/revenue_per_weekday')
def revenue_per_weekday():
    try:
        query = text("""
            SELECT
                o.storeid,
                (EXTRACT(DOW FROM o.orderdate_date) + 6) % 7 AS order_day_of_week,  -- Montag als erster Tag der Woche (0=Montag, 6=Sonntag)
                SUM(o.total) AS total_revenue
            FROM
                orders o
            GROUP BY
                o.storeid,
                (EXTRACT(DOW FROM o.orderdate_date) + 6) % 7
            ORDER BY
                o.storeid, order_day_of_week;
        """)
        result = db.session.execute(query)
        data = result.fetchall()
        revenue_data = [{'storeid': row[0], 'order_day_of_week': row[1], 'total_revenue': row[2]} for row in data]
        return jsonify({'revenue_per_weekday': revenue_data})
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})

@app.route('/api/pizza_orders')
def pizza_orders():
    try:
        query = text("""
            SELECT
                p.name AS pizza_name,
                COUNT(*) AS total_orders
            FROM
                orderitems oi
            JOIN
                products p ON oi.sku = p.sku
            WHERE
                p.name LIKE '%Pizza%'
            GROUP BY
                p.name
            ORDER BY
                total_orders DESC;
        """)
        result = db.session.execute(query)
        data = result.fetchall()
        pizza_data = [{'pizza_name': row[0], 'total_orders': row[1]} for row in data]
        return jsonify({'pizza_orders': pizza_data})
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})

if __name__ == '__main__':
    app.run(debug=True)
