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
        st.title("PostgreSQL-Datenbank mit Streamlit verbinden")

        # SQL-Abfrage ausführen und Daten abrufen
        query = "SELECT * FROM orders;"
        cursor.execute(query)
        data = cursor.fetchall()

        # Daten anzeigen
        st.write("Daten aus der PostgreSQL-Datenbank:")
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
