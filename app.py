from flask import Flask, render_template, request
import pandas as pd
import folium
import os
import random

app = Flask(__name__)

# create static folder if not exists
os.makedirs("static", exist_ok=True)

# load dataset
data = pd.read_csv("uber_final_cleaned.csv")


# 🔹 HOME PAGE
@app.route('/')
def home():
    return render_template("home.html")


# 🔹 FORM PAGE (WITH MAP)
@app.route('/form')
def form():
    generate_map()   # 🔥 generate map before loading
    locations = sorted(data['PULocationID'].unique())
    return render_template("index.html", locations=locations)


# 🔹 RESULT PAGE
@app.route('/result', methods=['POST'])
def result():
    try:
        location = int(request.form['location'])
        hour = int(request.form['hour'])

        df = data[
            (data['PULocationID'] == location) &
            (data['hour'] >= max(0, hour - 1)) &
            (data['hour'] <= min(23, hour + 1))
        ]

        if df.empty:
            return "<h2>No data found</h2>"

        # 🔥 CALCULATIONS
        demand = len(df)

        avg_price = df['total_amount'].mean()
        if pd.isna(avg_price):
            avg_price = 100

        surge = 1 + (demand / 5000)

        uber = avg_price * 0.6 * surge
        rapido = avg_price * 0.55 * (1 + demand / 6000)

        # Discounts
        if demand < 200:
            u_disc, r_disc = 25, 15
        elif demand < 800:
            u_disc, r_disc = 15, 12
        else:
            u_disc, r_disc = 5, 3

        uber *= (1 - u_disc / 100)
        rapido *= (1 - r_disc / 100)

        savings = abs(uber - rapido)

        # wait time
        if demand > 1000:
            wait = "2-3 min"
        elif demand > 300:
            wait = "5-7 min"
        else:
            wait = "8-10 min"

        # best option
        better = "Uber" if uber < rapido else "Rapido"

        # demand level
        if demand > 1000:
            demand_level = "High"
        elif demand > 300:
            demand_level = "Moderate"
        else:
            demand_level = "Low"

        return render_template(
            "result.html",
            demand=demand,
            demand_level=demand_level,
            uber=round(uber, 2),
            rapido=round(rapido, 2),
            savings=round(savings, 2),
            wait=wait,
            better=better
        )

    except Exception as e:
        return f"<h2>Error: {e}</h2>"


# 🔥 UPDATED MAP FUNCTION (YOUR CODE)
def generate_map():
    location_data = data.groupby('PULocationID').size().reset_index(name='demand')

    m = folium.Map(location=[40.7128, -74.0060], zoom_start=11)

    # fake names
    location_names = {
        1: "Manhattan",
        2: "Brooklyn",
        3: "Queens",
        4: "Bronx",
        5: "Harlem",
        6: "Midtown",
        7: "Chelsea",
        8: "SoHo",
        9: "Upper East Side",
        10: "Wall Street"
    }

    for _, row in location_data.iterrows():
        loc_id = int(row['PULocationID'])
        demand = row['demand']

        avg_price = data[data['PULocationID'] == loc_id]['total_amount'].mean()
        if pd.isna(avg_price):
            avg_price = 100

        surge = 1 + (demand / 5000)

        uber = avg_price * 0.6 * surge
        rapido = avg_price * 0.55 * (1 + demand / 6000)

        # color
        if demand > 1000:
            color = "red"
        elif demand > 300:
            color = "orange"
        else:
            color = "green"

        lat = 40.7128 + random.uniform(-0.08, 0.08)
        lon = -74.0060 + random.uniform(-0.08, 0.08)

        name = location_names.get(loc_id, f"Area {loc_id}")

        popup_text = f"""
        <b>{name}</b><br>
        Area ID: {loc_id}<br>
        Demand: {demand}<br>
        Uber: ₹{round(uber,2)}<br>
        Rapido: ₹{round(rapido,2)}
        """

        folium.CircleMarker(
            location=[lat, lon],
            radius=7,
            color=color,
            fill=True,
            fill_opacity=0.7,
            popup=popup_text
        ).add_to(m)

    m.save("static/map.html")


# 🔹 RUN APP
if __name__ == '__main__':
    app.run(debug=True)