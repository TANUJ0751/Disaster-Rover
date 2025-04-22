import streamlit as st
import requests
import plotly.graph_objs as go
from datetime import datetime
import time
import pandas as pd

st.set_page_config(page_title="Live ThingSpeak Dashboard", layout="wide")
st.title("📡 Live ThingSpeak Data (4 Fields, Real-Time)")



channel_id = 2917381
read_api_key = "2BOXLEMLP4A0B8S9"
num_results = 100
refresh_rate = 10
fields=["MQ2","MQ7","Temprature","Humidity"]
all_data = []

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
                # Add data to all_data list for CSV generation
                all_data.append([f'Field {field_num}'] + timestamps + values)

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
    

# Display the CSV download button
    if st.button(f"Download CSV", key=f"download_csv_{loop_counter}"):
        # Create DataFrame from all_data
        df = pd.DataFrame(all_data, columns=['Field', 'Timestamp', 'Value'])
        
        # Convert DataFrame to CSV
        csv = df.to_csv(index=False)
        
        # Convert CSV to a download link
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="thingspeak_data.csv",
            mime="text/csv",
            key=f"csv_button_{loop_counter}"  # Unique key for each CSV button
        )
    time.sleep(refresh_rate)