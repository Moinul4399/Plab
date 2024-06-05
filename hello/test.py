from sqlalchemy import create_engine

try:
    engine = create_engine('postgresql+psycopg2://postgres:Moinul439!!@localhost/pizzadatabase')
    connection = engine.connect()
    print("Verbindung erfolgreich!")
    connection.close()
except Exception as e:
    print(f"Ein Fehler ist aufgetreten: {e}")
