from flask import Flask, jsonify
import psycopg2

app = Flask(__name__)

@app.route('/api/top_stores')
def get_top_stores():
    try:
        connection = psycopg2.connect(
            host="localhost",
            database="pizzadatabase",
            user="postgres",
            password="Moinul439!!"
        )
        cursor = connection.cursor()
        query = """
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
        """
        cursor.execute(query)
        data = cursor.fetchall()
        top_stores = [{'storeID': row[0], 'zipcode': row[1], 'state_abbr': row[2], 'city': row[3], 'state': row[4], 'total_revenue': row[5]} for row in data]
        return jsonify({'top_stores': top_stores})
    except psycopg2.Error as e:
        return jsonify({'error': f"Fehler beim Verbinden zur PostgreSQL-Datenbank: {e}"})
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

@app.route('/api/unique_pizza_ingredients')
def unique_pizza_ingredients():
    try:
        connection = psycopg2.connect(
            host="localhost",
            database="pizzadatabase",
            user="postgres",
            password="Moinul439!!"
        )
        cursor = connection.cursor()
        query = """
            SELECT DISTINCT name, ingredients
            FROM products
            ORDER BY name;
        """
        cursor.execute(query)
        data = cursor.fetchall()
        unique_ingredients = [{'name': row[0], 'ingredients': row[1]} for row in data]
        return jsonify({'unique_pizza_ingredients': unique_ingredients})
    except psycopg2.Error as e:
        return jsonify({'error': f"Fehler beim Verbinden zur PostgreSQL-Datenbank: {e}"})
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    app.run(debug=True)
