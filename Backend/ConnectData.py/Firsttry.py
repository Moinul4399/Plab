import streamlit as st
import psycopg2

def main():
    # Verbindung zur PostgreSQL-Datenbank herstellen
    try:
        connection = psycopg2.connect(
            host="localhost",
            database="pizzadatabase",
            user="postgres",
            password="Moinul439!!"
        )
        cursor = connection.cursor()

        # Streamlit-App-Layout
        st.title("Top 10 umsatzstärksten Stores")

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

        # Daten anzeigen
        st.write("Top 10 umsatzstärksten Stores:")
        st.table(data)

    except psycopg2.Error as e:
        st.error(f"Fehler beim Verbinden zur PostgreSQL-Datenbank: {e}")

    finally:
        # Verbindung schließen
        if 'connection' in locals():
            cursor.close()
            connection.close()
            st.write("Verbindung zur Datenbank wurde geschlossen.")

if __name__ == "__main__":
    main()
