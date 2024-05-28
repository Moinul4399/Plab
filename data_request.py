# David API-endpoints für Cengiz --> customer_location, store_location, store_revenue_month & store_revenue_year

from flask import Flask, request, jsonify    
import json
import psycopg2
from decimal import Decimal # wichtig für store_locatioon

app = Flask(__name__)

#Datenbank Anbindung (wird im Sprint 3 mit ein connection pool ersetzt)
def get_db_connection():
    try:
        conn = psycopg2.connect(         
            database = "pizzadatabase",      #eventuell müsst ihr hier eure datenbank anbinden. 
            user = "postgres",
            host = "localhost",
            password = "1234",
            port = "5432"
    )    
        return conn
    except psycopg2.DatabaseError as e:
        print(f"Error connecting to the database: {e}")
        return None
    

@app.route('/api/customer_location', methods=['GET'])
def get_customer_location():
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """SELECT customerID, latitude, longitude FROM customers"""
    cursor.execute(query)
    data = cursor.fetchall()

    # Create a list to hold the JSON data
    json_data = [] 
    
    # Iterate over the fetched data
    for row in data:
        json_row = {}
        # Iterate over the cursor description to get column names
        for i, column in enumerate(cursor.description):
            column_name = column[0]  # Get the column name
            json_row[column_name] = row[i]
        
        json_data.append(json_row)
    
    # Convert the list of dictionaries to a JSON string
    json_string = json.dumps(json_data)
    
    print(json_string)
    cursor.close()
    conn.close()
    
    # Return the JSON data as a Flask response with cache control headers
    response = jsonify(json_data)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    
    return response


@app.route('/api/store_location', methods=['GET'])
def get_store_location():
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """SELECT storeID, latitude, longitude FROM stores"""
    cursor.execute(query)
    data = cursor.fetchall()

    # Create a list to hold the JSON data
    json_data = []

    # Iterate over the fetched data
    for row in data:
        json_row = {}
        # Iterate over the cursor description to get column names
        for i, column in enumerate(cursor.description):
            column_name = column[0]  # Get the column name
            value = row[i]
            if isinstance(value, Decimal):
                value = float(value)
            json_row[column_name] = value
        
        json_data.append(json_row)
    
    cursor.close()
    conn.close()
    
    # Return the JSON data as a Flask response with cache control headers
    response = jsonify(json_data)
    print(json_data)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.route('/api/store_revenue_month')
def revenue_month_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
            SELECT s.storeid,
            to_char(DATE_TRUNC('month', orderdate_date), 'MM/YYYY') AS month, 
            SUM(nitems * price) AS revenue
            FROM orders o
            JOIN orderitems oi ON o.orderid = oi.orderid
            JOIN products p ON oi.sku = p.sku
            JOIN stores s ON o.storeid = s.storeid
            GROUP BY s.storeid, DATE_TRUNC('month', orderdate_date)
            ORDER BY s.storeid, month;
            """
    cursor.execute(query)
    rows = cursor.fetchall()

    columns = [desc[0] for desc in cursor.description]

    results = []
    for row in rows:
        results.append(dict(zip(columns, row)))  

    conn.close()

    return jsonify(results)

@app.route('/api/store_revenue_year')
def revenue_year_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
            SELECT s.storeid,
            EXTRACT(YEAR FROM orderdate_date) AS year, 
            SUM(nitems * price) AS revenue
            FROM orders o
            JOIN orderitems oi ON o.orderid = oi.orderid
            JOIN products p ON oi.sku = p.sku
            JOIN stores s ON o.storeid = s.storeid
            GROUP BY s.storeid, EXTRACT(YEAR FROM orderdate_date)
            ORDER BY s.storeid, year;
            """

    cursor.execute(query)
    rows = cursor.fetchall()

    columns = [desc[0] for desc in cursor.description]
    results = [dict(zip(columns, row)) for row in rows]

    conn.close()

    return jsonify(results)



if __name__ == '__main__':
    app.run(debug=True, port=5000)
