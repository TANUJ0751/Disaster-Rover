import streamlit as st
import requests
import plotly.graph_objs as go
from datetime import datetime
import time
import pandas as pd

st.set_page_config(page_title="Live Rover Dashboard", layout="wide")
st.title("📡 Realtime Rover Data")



channel_id = 2917381
read_api_key = "2BOXLEMLP4A0B8S9"
num_results = 100
refresh_rate = 10
fields=["MQ2","MQ7","Temperature","Humidity"]

@st.cache_data(ttl=refresh_rate)
def fetch_all_data():
    url = f"https://api.thingspeak.com/channels/{channel_id}/feeds.json?api_key={read_api_key}&results=8000"
    response = requests.get(url)
    if response.status_code == 200:
        feeds = response.json().get("feeds", [])
        data = {
            "created_at": [],
            "MQ2": [],
            "MQ7": [],
            "Temperature": [],
            "Humidity": []
        }
        for entry in feeds:
            data["created_at"].append(entry["created_at"])
            for i in range(1, 5):
                data[f"{fields[i-1]}"].append(entry.get(f"{fields[i-1]}"))
        df = pd.DataFrame(data)
        df["created_at"] = pd.to_datetime(df["created_at"])
        for i in range(1, 5):
            df[f"{fields[i-1]}"] = pd.to_numeric(df[f"{fields[i-1]}"], errors="coerce")
        return df
    
    return pd.DataFrame()


# Function to fetch data
def fetch_field_data(field_num):
    url = f"https://api.thingspeak.com/channels/{channel_id}/fields/{field_num}.json?api_key={read_api_key}&results={num_results}"
    response = requests.get(url)
    if response.status_code == 200:
        feeds = response.json().get("feeds", [])
        timestamps, values = [], []
        latest_value = None
        for entry in feeds:
            value = entry.get(f'field{field_num}')
            if value:
                timestamps.append(datetime.strptime(entry["created_at"], "%Y-%m-%dT%H:%M:%SZ"))
                values.append(float(value))
                latest_value = float(value)  # Update with the latest value
        return timestamps, values, latest_value
    return [], [], None

# Create placeholders in 2x2 grid
col1, col2 = st.columns(2)
row1_field1 = col1.empty()
row1_field2 = col2.empty()
col3, col4 = st.columns(2)
row2_field3 = col3.empty()
row2_field4 = col4.empty()

placeholders = [row1_field1, row1_field2, row2_field3, row2_field4]

# Start loop to update in real-time
loop_counter = 0
# Download CSV
df_all = fetch_all_data()
csv = df_all.to_csv(index=False)
st.download_button("📥 Download All Data (CSV)", data=csv, file_name="thingspeak_full_data.csv", mime="text/csv")
while True:
    loop_counter += 1

    for idx, placeholder in enumerate(placeholders):
        field_num = idx + 1
        timestamps, values, latest_value = fetch_field_data(field_num)

        with placeholder.container():
            # Display field with latest value in the title
            if latest_value is not None:
                st.markdown(f"#### 📈 {fields[idx]} - Latest Value: {latest_value}")
            else:
                st.markdown(f"#### 📈 {fields[idx]} - No Data")

            if timestamps and values:
                
                fig = go.Figure(
                    data=go.Scatter(x=timestamps, y=values, mode='lines+markers'),
                    layout=go.Layout(
                        xaxis_title="Time",
                        yaxis_title=f"{fields[idx]} Value",
                        margin=dict(t=30),
                        template="plotly_dark",
                        height=350
                    )
                )
                st.plotly_chart(fig, use_container_width=True, key=f"chart_{field_num}_{loop_counter}")
            else:
                st.warning(f"No data for {fields[idx]}")
    

    time.sleep(refresh_rate)