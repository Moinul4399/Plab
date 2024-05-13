from flask import Flask, jsonify
import psycopg2

app = Flask(__name__)

@app.route('/api/top_stores')
def get_top_stores():
    try:
        # Verbindung zur PostgreSQL-Datenbank herstellen
        connection = psycopg2.connect(
            host="localhost",
            database="pizzadatabase",
            user="postgres",
            password="Moinul439!!"
        )
        cursor = connection.cursor()

        # SQL-Abfrage ausführen und Daten abrufen
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

        # Daten im JSON-Format zurückgeben
        top_stores = []
        for row in data:
            store = {
                'storeID': row[0],
                'zipcode': row[1],
                'state_abbr': row[2],
                'city': row[3],
                'state': row[4],
                'total_revenue': row[5]
            }
            top_stores.append(store)

        return jsonify({'top_stores': top_stores})

    except psycopg2.Error as e:
        return jsonify({'error': f"Fehler beim Verbinden zur PostgreSQL-Datenbank: {e}"})

    finally:
        # Verbindung schließen
        if 'connection' in locals():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    app.run(debug=True)
