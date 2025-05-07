import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Constants
PASSWORD = "Station Groningen"
DATA_FILE = "responses.csv"
DEADLINE = "2025-07-07T07:00:00"  # JavaScript ISO format

# Initialize file if it doesn't exist
if not os.path.exists(DATA_FILE):
    df = pd.DataFrame(columns=["timestamp", "name"])
    df.to_csv(DATA_FILE, index=False)

st.title("Senaat der Senaten")

# JavaScript live countdown with custom style
st.components.v1.html(f"""
<div id="countdown" style="
    font-size: 60px;
    font-family: 'Palace Script MT', cursive;
    color: navy;
    text-align: center;
    margin-top: 20px;
    font-weight: bold;
"></div>
<script>
var deadline = new Date("{DEADLINE}").getTime();
var x = setInterval(function() {{
    var now = new Date().getTime();
    var t = deadline - now;
    if (t > 0) {{
        var days = Math.floor(t / (1000 * 60 * 60 * 24));
        var hours = Math.floor((t % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        var minutes = Math.floor((t % (1000 * 60 * 60)) / (1000 * 60));
        var seconds = Math.floor((t % (1000 * 60)) / 1000);
        document.getElementById("countdown").innerHTML = 
            days + " dagen " + hours + " uur " 
            + minutes + " minuten " + seconds + " seconden ";
    }} else {{
        document.getElementById("countdown").innerHTML = "De deadline is verstreken!";
        clearInterval(x);
    }}
}}, 1000);
</script>
""", height=150)

# Riddle input
st.write("Als je interesse hebt in de Senaat der Senaten, voer dan het goede antwoord in:")

password_input = st.text_input("Antwoord:", type="password")

if password_input:
    if password_input.strip() == PASSWORD:
        st.success("Was ook niet heel moeilijk... Voer je naam in om te laten zien dat je interesse hebt:")
        name_input = st.text_input("Jouw naam:")

        if st.button("Verzend"):
            if name_input.strip():
                # Save the response
                df = pd.read_csv(DATA_FILE)
                new_entry = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                             "name": name_input.strip()}
                df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.success("Je naam is opgeslagen!")
            else:
                st.error("Vul alsjeblieft je naam in voordat je verzendt.")
    else:
        st.error("Ongeldig antwoord. Probeer opnieuw.")
