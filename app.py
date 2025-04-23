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
ch2=2930711
rd2="FWXW0URLYLYP7ZVW"
num_results = 20
refresh_rate = 10
previous_values = [0, 0, 0, 0]
fields=["MQ2","MQ7","Temperature","Humidity"]
maxlevel=[100,150,60,50]
minlevel=[0,0,0,0]

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

def show_gauge(field_num, latest_value,pv, min_val=0, max_val=100):
    if latest_value is None:
        st.warning(f"Field {field_num} has no data to display gauge.")
        return

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=latest_value,
        delta={
        'reference': pv,  # Replace with your actual reference value
        'increasing': {'color': "blue"},
        'decreasing': {'color': "orange"},
        'position': "top"  # optional, can be "top" or "bottom"
        },
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"{fields[field_num-1]} Level", 'font': {'size': 22}},
        gauge={
            'axis': {'range': [min_val, max_val]},
            'steps': [
                {'range': [min_val, max_val * 0.4], 'color': "blue"},
                {'range': [max_val * 0.4, max_val * 0.75], 'color': "orange"},
                {'range': [max_val * 0.75, max_val], 'color': "red"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 6},
                'thickness': 0.75,
                'value': latest_value
            }
        }
    ))

    st.plotly_chart(fig, use_container_width=True, key=f"gauge_{field_num}_{loop_counter}")


# Function to fetch data
def fetch_field_data(field_num,channel_id,read_api_key,num_results):
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
                if field_num<5:
                    values.append(float(value))
                    latest_value = float(value)  # Update with the latest value
                else:
                    values.append(value)
                    latest_value=value
        return timestamps, values, latest_value
    return [], [], None

# Create placeholders in 2x2 grid
col1, col2 = st.columns(2)
row1_field1 = col1.empty()
row1_field2 = col2.empty()
col3, col4 = st.columns(2)
row2_field3 = col3.empty()
row2_field4 = col4.empty()
col5,col6=st.columns(2)
row3_field5=col5.empty()
row3_field6 = col6.empty()

placeholders = [ row2_field3, row2_field4,row3_field5,row3_field6]

# Start loop to update in real-time
loop_counter = 0
# Download CSV
df_all = fetch_all_data()
csv = df_all.to_csv(index=False)
st.download_button("📥 Download All Data (CSV)", data=csv, file_name="thingspeak_full_data.csv", mime="text/csv")
while True:
    loop_counter += 1
    with row1_field1.container():
        mode=fetch_field_data(5,ch2,rd2,1)
        st.write(f"Driving Mode : {mode[-1]}")

    for idx, placeholder in enumerate(placeholders):
        field_num = idx + 1
        timestamps, values, latest_value = fetch_field_data(field_num,channel_id,read_api_key,num_results)
        

        with placeholder.container():
            # Display field with latest value in the title
            show_gauge(field_num, latest_value,previous_values[idx], min_val=minlevel[idx], max_val=maxlevel[idx])
            if latest_value is not None:
                st.markdown(f"#### 📈 {fields[idx]} Graph")
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
            st.write("----------")
        if latest_value is not None:
            previous_values[idx] = latest_value
    

    time.sleep(refresh_rate)