from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from sqlalchemy import text
import plotly.graph_objects as go

app = Flask(__name__)

# Datenbank-Konfiguration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:database123!@localhost/pizzadatabasev2'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

@app.route('/api/top_stores')
def get_top_stores():
    try:
        query = text("""
            SELECT
                s.storeid,
                s.zipcode,
                s.state_abbr,
                s.city,
                s.state,
                SUM(p.price) AS total_revenue
            FROM
                stores s
            JOIN
                orders o ON s.storeid = o.storeid
            JOIN
                orderitems oi ON o.orderid = oi.orderid
            JOIN
                products p ON oi.sku = p.sku
            GROUP BY
                s.storeid,
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
        top_stores = [{'storeid': row[0], 'zipcode': row[1], 'state_abbr': row[2], 'city': row[3], 'state': row[4], 'total_revenue': row[5]} for row in data]
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
        locations = [{'city': row[0], 'avg_latitude': float(row[1]), 'avg_longitude': float(row[2])} for row in data]
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

# Scatterplot
@app.route('/api/scatterplot')
def get_store_data():
    # Abfrage für Umsatzdaten
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

    # Abfrage für Bestellanzahl
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
    
# Tabelle für top n kategories
@app.route('/api/pizza_orders')
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
    
    
# Tabelle top 5 stores Revenue -> noch anpassen
@app.route('/api/top_5_stores')
def top_5_stores():
    try:
        query = text("""
            WITH yearly_sales AS (
                SELECT
                    storeid,
                    EXTRACT(YEAR FROM orderdate) AS year,
                    SUM(total) AS annual_sales
                FROM
                    orders
                WHERE
                    EXTRACT(YEAR FROM orderdate) IN (2020, 2021, 2022)
                GROUP BY
                    storeid,
                    EXTRACT(YEAR FROM orderdate)
            )
            SELECT
                s.storeid,
                s.year,
                s.annual_sales
            FROM (
                SELECT
                    storeid,
                    year,
                    annual_sales,
                    ROW_NUMBER() OVER (PARTITION BY year ORDER BY annual_sales DESC) AS rank
                FROM
                    yearly_sales
            ) s
            WHERE
                s.rank <= 5
            ORDER BY
                s.year,
                s.annual_sales DESC;
        """)
        result = db.session.execute(query)
        data = result.fetchall()
        top_stores = [{'storeid': row[0], 'year': row[1], 'annual_sales': row[2]} for row in data]
        return jsonify({'top_5_stores': top_stores})
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})
    
    
    
    
    
# Tabelle worst 5 stores revenues -> noch anpassen
@app.route('/api/worst_5_stores')
def worst_5_stores():
    try:
        query = text("""
            WITH yearly_sales AS (
                SELECT
                    storeid,
                    EXTRACT(YEAR FROM orderdate) AS year,
                    SUM(total) AS annual_sales
                FROM
                    orders
                WHERE
                    EXTRACT(YEAR FROM orderdate) IN (2020, 2021, 2022)
                GROUP BY
                    storeid,
                    EXTRACT(YEAR FROM orderdate)
            )
            SELECT
                s.storeid,
                s.year,
                s.annual_sales
            FROM (
                SELECT
                    storeid,
                    year,
                    annual_sales,
                    ROW_NUMBER() OVER (PARTITION BY year ORDER BY annual_sales ASC) AS rank
                FROM
                    yearly_sales
            ) s
            WHERE
                s.rank <= 5
            ORDER BY
                s.year,
                s.annual_sales ASC;
        """)
        result = db.session.execute(query)
        data = result.fetchall()
        worst_stores = [{'storeid': row[0], 'year': row[1], 'annual_sales': row[2]} for row in data]
        return jsonify({'worst_5_stores': worst_stores})
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})
    
# Donut Chart
@app.route('/api/revenues_by_pizza_type_2022')
def revenues_by_pizza_type_2022():
    try:
        query = text("""
            SELECT
                p.name AS pizza_name,
                SUM(oi.quantity * p.price) AS total_revenue
            FROM
                orderitems oi
            JOIN
                products p ON oi.sku = p.sku
            JOIN
                orders o ON oi.orderid = o.orderid
            WHERE
                EXTRACT(YEAR FROM o.orderdate) = 2022
            GROUP BY
                p.name
            ORDER BY
                total_revenue DESC;
        """)
        result = db.session.execute(query)
        data = result.fetchall()

        revenues = [{'pizza_name': row[0], 'total_revenue': row[1]} for row in data]
        return jsonify({'revenues_by_pizza_type_2022': revenues})
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})
    

@app.route('/api/store_yearly_avg_orders')
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
def get_store_ids():
    try:
        query = text("""
            SELECT storeid FROM stores;
        """)
        result = db.session.execute(query)
        store_ids = [row[0] for row in result.fetchall()]
        return jsonify({'store_ids': store_ids})
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Store-IDs: {e}"})

 # Anbindung für Pizza-Arten mit Größe
@app.route('/api/scatter_plot_pizzen')
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
            GROUP BY p.name, p.size
        """)
        data= db.session.execute(query)
        
        # Process the Data for Frontend
        data_for_frontend = []
        for row in data:
            data_for_frontend.append({
                'pizza_name': row[0],
                'pizza_size': row[1],
                'total_sold': row[2],
                'total_revenue': row[3]
            })

        return jsonify(data_for_frontend)

    except Exception as e:
        return jsonify({"error": f"Error fetching data: {str(e)}"}), 500

# Anbindung für Nadims Diagram   
@app.route('/api/store_orders_per_hour')
def store_orders_per_hour():
    try:
        query = text("""
            SELECT
                storeid,
                EXTRACT(hour FROM (orderdate AT TIME ZONE 'UTC' AT TIME ZONE 'America/Los_Angeles')) AS order_hour,
                COUNT(*) AS total_orders_per_hour
            FROM
                orders
            GROUP BY
                storeid, EXTRACT(hour FROM (orderdate AT TIME ZONE 'UTC' AT TIME ZONE 'America/Los_Angeles'))
            ORDER BY
                storeid, order_hour;
        """)
        result = db.session.execute(query)
        data = result.fetchall()
        orders_per_hour = [{
            'storeid': row[0],
            'order_hour': row[1],
            'total_orders_per_hour': row[2]
        } for row in data]
        return jsonify({'store_orders_per_hour': orders_per_hour})
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})

# Anbindung für Nadims Liniendiagramm 
@app.route('/api/revenue_per_weekday')
def revenue_per_weekday():
    try:
        query = text("""
            SELECT
                o.storeid,
                (EXTRACT(DOW FROM o.orderdate) + 6) % 7 AS order_day_of_week,  -- Montag als erster Tag der Woche (0=Montag, 6=Sonntag)
                SUM(o.total) AS total_revenue
            FROM
                orders o
            GROUP BY
                o.storeid,
                (EXTRACT(DOW FROM o.orderdate) + 6) % 7
            ORDER BY
                o.storeid, order_day_of_week;
        """)
        result = db.session.execute(query)
        data = result.fetchall()
        revenue_data = [{'storeid': row[0], 'order_day_of_week': row[1], 'total_revenue': row[2]} for row in data]
        return jsonify({'revenue_per_weekday': revenue_data})
    except Exception as e:
        return jsonify({'error': f"Fehler beim Abrufen der Daten: {e}"})

# Boxplot Diagram    
@app.route('/api/boxplot_metrics')
def boxplot_data_metrics ():
    try:
        # 1. Datenabfrage
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

        # 2. Daten in DataFrame konvertieren
        df = pd.DataFrame(data, columns=["customerid", "pizza_name", "order_count"])

        # 3. Daten für den Boxplot vorbereiten
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

if __name__ == '__main__':
    app.run(debug=True)
