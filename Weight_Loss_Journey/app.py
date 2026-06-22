import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. Page Configuration
st.set_page_config(page_title="Srajan's Weight Loss Journey", layout="wide", page_icon="💪")

# 2. Title and Intro
st.title("🚀 Srajan's Weight Loss Journey Dashboard")
st.markdown("Welcome to my interactive fitness tracker! Explore the data to see how steps, sleep, and calories impact my progress.")

# 3. Load and Clean Data from Google Sheets
@st.cache_data(ttl=600)
def load_data():
    # YOUR EXACT GOOGLE SHEET LINK
    sheet_url = "https://docs.google.com/spreadsheets/d/1gga1jNdAy0tIpeHH2rDMZNWtbtEHrKqwKYQcf2c67xU/edit?usp=sharing"
    csv_url = sheet_url.replace('/edit?usp=sharing', '/export?format=csv')
    
    df = pd.read_csv(csv_url)
    df = df.dropna(subset=['Weight in Kgs'])
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%y')
    
    df['Steps'] = df['Steps'].fillna(0)
    df['Calories Burn'] = df['Calories Burn'].fillna(0)
    
    # Calculate 7-Day Moving Average for weight
    df['7-Day Avg Weight'] = df['Weight in Kgs'].rolling(window=7, min_periods=1).mean()
    
    # Calculate daily weight change (Current Day - Previous Day)
    df['Weight Change (kg)'] = df['Weight in Kgs'].diff()
    # Shift it backward so we compare Today's Calorie Burn with Tomorrow's Weight Change
    df['Next Day Weight Change'] = df['Weight Change (kg)'].shift(-1)
    
    return df

df = load_data()

# 4. Top Level Metrics
st.subheader("🏆 Quick Stats")
col1, col2, col3, col4 = st.columns(4)

initial_weight = df['Weight in Kgs'].iloc[0]
current_weight = df['Weight in Kgs'].iloc[-1]
total_loss = current_weight - initial_weight

with col1:
    st.metric("Starting Weight", f"{initial_weight} kg")
with col2:
    st.metric("Current Weight", f"{current_weight} kg", f"{total_loss:.2f} kg")
with col3:
    st.metric("Avg Daily Steps", f"{int(df['Steps'].mean()):,}")
with col4:
    st.metric("Avg Sleep", f"{df['Sleep (Hrs)'].mean():.1f} hrs")

st.divider()

# 5. Trend Analysis: True Weight Loss Trajectory
st.subheader("📉 True Weight Trajectory (7-Day Moving Average)")
fig_weight = go.Figure()
fig_weight.add_trace(go.Scatter(x=df['Date'], y=df['Weight in Kgs'], mode='lines+markers', 
                                name='Daily Weight', line=dict(color='rgba(0, 255, 170, 0.4)', dash='dot')))
fig_weight.add_trace(go.Scatter(x=df['Date'], y=df['7-Day Avg Weight'], mode='lines', 
                                name='7-Day Average', line=dict(color='#00FFAA', width=4)))

fig_weight.update_layout(template='plotly_dark', hovermode="x unified", margin=dict(l=0, r=0, b=0, t=30))
st.plotly_chart(fig_weight, use_container_width=True)

st.divider()

# 6. Deep Dive: Effort vs. Output
st.subheader("🔥 Effort vs. Output: Steps & Calories")
fig_effort = make_subplots(specs=[[{"secondary_y": True}]])
fig_effort.add_trace(go.Bar(x=df['Date'], y=df['Steps'], name="Steps", marker_color='rgba(52, 152, 219, 0.7)'), secondary_y=False)
fig_effort.add_trace(go.Scatter(x=df['Date'], y=df['Calories Burn'], name="Calories Burned", mode='lines+markers', line=dict(color='#E74C3C', width=3)), secondary_y=True)

fig_effort.update_layout(template='plotly_dark', hovermode="x unified", margin=dict(l=0, r=0, b=0, t=30))
fig_effort.update_yaxes(title_text="Total Steps", secondary_y=False)
fig_effort.update_yaxes(title_text="Calories Burned", secondary_y=True)
st.plotly_chart(fig_effort, use_container_width=True)

st.divider()

# 7. Advanced 3D Interactive Visualization
st.subheader("🌌 3D Analysis: The Fitness Matrix")
st.markdown("Rotate, zoom, and hover over the data points. *Size of the bubble = Sleep Hours | Color = Recovery %*")

fig_3d = px.scatter_3d(
    df, x='Steps', y='Calories Burn', z='Weight in Kgs',
    color='Recovery (%)', size='Sleep (Hrs)',
    hover_name='Date', hover_data=['Strain'],
    color_continuous_scale='Viridis', template='plotly_dark'
)
fig_3d.update_layout(margin=dict(l=0, r=0, b=0, t=0))
st.plotly_chart(fig_3d, use_container_width=True)

st.divider()

# 8. Data Science: Habit Correlation Matrix
st.subheader("🧬 Data Science: What Drives Your Progress?")
st.markdown("This heatmap shows how your habits correlate. A score close to **1.0** or **-1.0** means a strong connection.")

# Select only numeric columns for correlation
metrics_df = df[['Steps', 'Calories Burn', 'Strain', 'Sleep (Hrs)', 'Recovery (%)', 'Weight in Kgs']]
corr_matrix = metrics_df.corr().round(2)

fig_corr = px.imshow(
    corr_matrix, 
    text_auto=True, 
    aspect="auto",
    color_continuous_scale='RdBu_r',
    template='plotly_dark'
)
fig_corr.update_layout(margin=dict(l=0, r=0, b=0, t=30))
st.plotly_chart(fig_corr, use_container_width=True)

st.divider()

# 9. Deep Dive Analytics
st.title("🔬 Deep Dive Analytics")

# Sleep vs Recovery
st.subheader("🛌 1. Sleep vs. Recovery (%)")
fig_sleep = px.scatter(
    df, x="Sleep (Hrs)", y="Recovery (%)", trendline="ols",
    hover_data=["Date", "Strain"], color="Strain", color_continuous_scale="reds",
    template="plotly_dark"
)
st.plotly_chart(fig_sleep, use_container_width=True)

# Calorie Burn vs Strain
st.subheader("❤️‍🔥 2. Calorie Burn vs. Strain")
fig_strain = px.scatter(
    df, x="Strain", y="Calories Burn", trendline="ols",
    hover_data=["Date", "Steps"], color="Steps", color_continuous_scale="blues",
    template="plotly_dark"
)
st.plotly_chart(fig_strain, use_container_width=True)

# Calorie Burn vs Weight Drop
st.subheader("⚖️ 3. Calorie Burn vs. Next-Day Weight Drop")
st.markdown("*(Negative numbers on the left mean you lost weight).*")
fig_weight_drop = px.scatter(
    df, x="Calories Burn", y="Next Day Weight Change", trendline="ols",
    hover_data=["Date", "Strain"], color="Recovery (%)", color_continuous_scale="greens",
    template="plotly_dark"
)
fig_weight_drop.add_hline(y=0, line_dash="dash", line_color="white", annotation_text="No Weight Change")
st.plotly_chart(fig_weight_drop, use_container_width=True)