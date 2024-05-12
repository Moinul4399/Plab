import streamlit as st

def main():
    st.title("Textkonverter")

    # Eingabefeld für den Benutzer
    input_text = st.text_input("Geben Sie Ihren Text ein:")

    # Dropdown-Menü für die Auswahl der Konvertierungsmethode
    conversion_method = st.selectbox("Wählen Sie die Konvertierungsmethode aus:", ["Großbuchstaben", "Kleinbuchstaben", "Titel"])

    # Konvertierung basierend auf der Auswahl des Benutzers
    if conversion_method == "Großbuchstaben":
        output_text = input_text.upper()
    elif conversion_method == "Kleinbuchstaben":
        output_text = input_text.lower()
    else:
        output_text = input_text.title()

    # Anzeige des konvertierten Textes
    st.write("Konvertierter Text:", output_text)

if __name__ == "__main__":
    main()
