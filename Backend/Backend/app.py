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

@app.route('/api/store_monthly_revenues')
def store_monthly_revenues():
    try:
        query = text("""
            SELECT
                s.storeid,
                s.city,
                s.latitude,
                s.longitude,
                to_char(o.orderdate_date, 'YYYY-MM') AS month,  -- Get year and month
                SUM(o.total) AS revenue                             -- Calculate total revenue
            FROM
                stores s
            JOIN
                orders o ON s.storeid = o.storeid
            GROUP BY
                s.storeid, s.city, s.latitude, s.longitude, to_char(o.orderdate_date, 'YYYY-MM')
            ORDER BY
                s.city, month; -- Order by city and then by month
        """)

        result = db.session.execute(query)
        data = result.fetchall()

        # Restructure data into a nested format for better frontend use
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
                    'monthly_revenues': {}  # Initialize nested dictionary
                }
            monthly_revenues[store_id]['monthly_revenues'][month] = revenue

        return jsonify({'store_monthly_revenues': list(monthly_revenues.values())})

    except Exception as e:
        return jsonify({'error': f"Error fetching data: {e}"})
    


@app.route('/api/y-achse_revenues')  
def get_revenue_by_store_year():
    sql_query = text("""
            SELECT 
        stores.storeid,
        EXTRACT(YEAR FROM orders.orderdate_date) AS year,
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
        stores.storeid, EXTRACT(YEAR FROM orders.orderdate_date)
        ORDER BY 
        stores.storeid, year;
    """)  

    result = db.session.execute(sql_query)
    revenue_data = [
        {"storeid": row.storeid, "year": row.year, "revenue": row.revenue}
        for row in result
    ]

    return jsonify(revenue_data)

@app.route('/api/x-achse_orders')  
def get_order_count_by_store_year():
    sql_query = text("""
        SELECT
            stores.storeid,
            EXTRACT(YEAR FROM orders.orderdate_date) AS year,
            COUNT(DISTINCT orders.orderid) AS order_count  
        FROM
            stores
        JOIN
            orders ON stores.storeid = orders.storeid
        GROUP BY
            stores.storeid, EXTRACT(YEAR FROM orders.orderdate_date)
        ORDER BY
            stores.storeid, year;
    """) 

    result = db.session.execute(sql_query)
    order_data = [
        {"storeid": row.storeid, "year": row.year, "order_count": row.order_count}
        for row in result
    ]

    return jsonify(order_data)

@app.route('/api/scatterplot')
def get_store_data():
    # Abfrage für Umsatzdaten
    revenue_query = text("""
        SELECT 
            stores.storeid,
            EXTRACT(YEAR FROM orders.orderdate_date) AS year,
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
            stores.storeid, EXTRACT(YEAR FROM orders.orderdate_date)
        ORDER BY 
            stores.storeid, year;
    """)

    # Abfrage für Bestellanzahl
    order_count_query = text("""
        SELECT
            stores.storeid,
            EXTRACT(YEAR FROM orders.orderdate_date) AS year,
            COUNT(DISTINCT orders.orderid) AS order_count  
        FROM
            stores
        JOIN
            orders ON stores.storeid = orders.storeid
        GROUP BY
            stores.storeid, EXTRACT(YEAR FROM orders.orderdate_date)
        ORDER BY
            stores.storeid, year;
    """)

    # Ergebnisse abrufen
    revenue_result = db.session.execute(revenue_query)
    order_count_result = db.session.execute(order_count_query)

    # Daten in Dictionaries umwandeln
    revenue_data = {
        (row.storeid, row.year): row.revenue for row in revenue_result
    }  # Key: (storeid, year)
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
if __name__ == '__main__':
    app.run(debug=True)
