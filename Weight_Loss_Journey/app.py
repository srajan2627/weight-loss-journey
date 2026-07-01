import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime

# 1. Page Configuration
st.set_page_config(page_title="Srajan's Weight Loss Journey", layout="wide", page_icon="💪")

# 2. Title and Intro
st.title("🚀 Srajan's Weight Loss Journey")
st.markdown("Welcome to my interactive fitness tracker! Explore the data to see how steps, sleep, and calories impact my progress.")

# 3. Load and Clean Data from Google Sheets
@st.cache_data(ttl=600)
def load_data():
    # YOUR EXACT GOOGLE SHEET LINK
    sheet_url = "https://docs.google.com/spreadsheets/d/1gga1jNdAy0tIpeHH2rDMZNWtbtEHrKqwKYQcf2c67xU/edit?usp=sharing"
    csv_url = sheet_url.replace('/edit?usp=sharing', '/export?format=csv')
    
    df = pd.read_csv(csv_url)
    
    # Update to the new exact column names
    df = df.dropna(subset=['Actual Weight in Kgs'])
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%y')
    
    # Force Steps and Calories to be numeric (removes commas if Google Sheets formats them as text)
    df['Steps'] = pd.to_numeric(df['Steps'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    df['Calories Burn'] = pd.to_numeric(df['Calories Burn'].astype(str).str.replace(',', ''), errors='coerce').fillna(0)
    
    # Ensure prediction column is treated as numeric to avoid plotting errors
    df['Predicted Total Weight (Kgs)'] = pd.to_numeric(df['Predicted Total Weight (Kgs)'], errors='coerce')
    
    # Calculate rolling metrics on the FULL dataset first
    df['7-Day Avg Weight'] = df['Actual Weight in Kgs'].rolling(window=7, min_periods=1).mean()
    df['Weight Change (kg)'] = df['Actual Weight in Kgs'].diff()
    df['Next Day Weight Change'] = df['Weight Change (kg)'].shift(-1)
    
    return df

df_full = load_data()

# ==========================================
# 4. SIDEBAR: Global Date Filters
# ==========================================
st.sidebar.header("📅 Global Filters")
st.sidebar.markdown("Filter all charts by date range.")

min_date = df_full['Date'].min().date()
max_date = df_full['Date'].max().date()

# Date Range Picker
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Apply Filter safely
if len(date_range) == 2:
    start_date, end_date = date_range
    mask = (df_full['Date'].dt.date >= start_date) & (df_full['Date'].dt.date <= end_date)
    df = df_full.loc[mask]
elif len(date_range) == 1:
    start_date = date_range[0]
    mask = df_full['Date'].dt.date >= start_date
    df = df_full.loc[mask]
else:
    df = df_full.copy()

# ==========================================
# UNIVERSAL MOBILE LAYOUT HELPER
# ==========================================
def apply_mobile_layout(fig, is_heatmap=False):
    """Forces Plotly charts to use 100% of mobile screen width and pushes legends to the bottom."""
    fig.update_layout(
        template='plotly_dark',
        margin=dict(l=10, r=10, b=10, t=40), # Tiny side margins
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5)
    )
    if is_heatmap:
        # Heatmaps use a color bar instead of a legend
        fig.update_layout(coloraxis_colorbar=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5))
    return fig

# ==========================================
# 5. Top Level Metrics
# ==========================================
st.subheader(f"🏆 Quick Stats ({len(df)} Days Tracked)")

# Handle empty data frame if filter is too narrow
if not df.empty:
    initial_weight = df['Actual Weight in Kgs'].iloc[0]
    current_weight = df['Actual Weight in Kgs'].iloc[-1]
    total_loss = current_weight - initial_weight

    col1, col2 = st.columns(2)
    with col1: st.metric("Starting Weight (In Range)", f"{initial_weight} kg")
    with col2: st.metric("Current Weight", f"{current_weight} kg", f"{total_loss:.2f} kg")

    col3, col4 = st.columns(2)
    with col3: st.metric("Avg Daily Steps", f"{int(df['Steps'].mean()):,}")
    with col4: st.metric("Avg Sleep", f"{df['Sleep (Hrs)'].mean():.1f} hrs")
else:
    st.warning("No data available in this date range. Please adjust your filters.")

st.divider()

# ==========================================
# 6. NEW: Week-over-Week Progress
# ==========================================
if not df.empty:
    st.subheader("📊 Week-over-Week Progress")
    st.markdown("Macro-view of your weekly average weight compared to your average weekly steps.")
    
    df_weekly = df.copy()
    # Find the Monday of each week to group by
    df_weekly['Week_Start'] = df_weekly['Date'] - pd.to_timedelta(df_weekly['Date'].dt.dayofweek, unit='d')
    
    wow_df = df_weekly.groupby('Week_Start').agg(
        Avg_Weight=('Actual Weight in Kgs', 'mean'),
        Avg_Steps=('Steps', 'mean')
    ).reset_index()
    
    wow_df['Week_Label'] = wow_df['Week_Start'].dt.strftime('%b %d')

    fig_wow = make_subplots(specs=[[{"secondary_y": True}]])
    # Bar Chart for Steps
    fig_wow.add_trace(go.Bar(x=wow_df['Week_Label'], y=wow_df['Avg_Steps'], name="Avg Weekly Steps", marker_color='rgba(52, 152, 219, 0.7)'), secondary_y=False)
    # Line Chart for Weight
    fig_wow.add_trace(go.Scatter(x=wow_df['Week_Label'], y=wow_df['Avg_Weight'], name="Avg Weekly Weight", mode='lines+markers+text', 
                                 text=[f"{val:.1f} kg" for val in wow_df['Avg_Weight']], textposition="top right",
                                 line=dict(color='#00FFAA', width=4), marker=dict(size=10)), secondary_y=True)

    fig_wow = apply_mobile_layout(fig_wow)
    fig_wow.update_yaxes(title_text="Avg Steps", secondary_y=False)
    fig_wow.update_yaxes(title_text="Avg Weight (kg)", secondary_y=True)
    st.plotly_chart(fig_wow, use_container_width=True)

    st.divider()

# ==========================================
# 7. Trend Analysis
# ==========================================
st.subheader("📉 True Weight Trajectory")
fig_weight = go.Figure()
fig_weight.add_trace(go.Scatter(x=df['Date'], y=df['Actual Weight in Kgs'], mode='lines+markers', name='Daily Actual', line=dict(color='rgba(0, 255, 170, 0.4)', dash='dot')))
fig_weight.add_trace(go.Scatter(x=df['Date'], y=df['7-Day Avg Weight'], mode='lines', name='7-Day Avg Actual', line=dict(color='#00FFAA', width=4)))
fig_weight = apply_mobile_layout(fig_weight)
st.plotly_chart(fig_weight, use_container_width=True)

st.divider()

# ==========================================
# 8. Predicted vs. Actual Weight
# ==========================================
st.subheader("🎯 Predicted vs. Actual Weight Loss")
st.markdown("Comparing my actual scale weight against the mathematical predictions based on caloric deficit.")
fig_pred = go.Figure()
fig_pred.add_trace(go.Scatter(x=df['Date'], y=df['Actual Weight in Kgs'], mode='lines+markers', name='Actual Weight', line=dict(color='#00FFAA', width=3)))
fig_pred.add_trace(go.Scatter(x=df['Date'], y=df['Predicted Total Weight (Kgs)'], mode='lines', name='Predicted Weight', line=dict(color='#E74C3C', dash='dash', width=3)))
fig_pred = apply_mobile_layout(fig_pred)
st.plotly_chart(fig_pred, use_container_width=True)

st.divider()

# ==========================================
# 9. Effort vs. Output
# ==========================================
st.subheader("🔥 Effort vs. Output")
fig_effort = make_subplots(specs=[[{"secondary_y": True}]])
fig_effort.add_trace(go.Bar(x=df['Date'], y=df['Steps'], name="Steps", marker_color='rgba(52, 152, 219, 0.7)'), secondary_y=False)
fig_effort.add_trace(go.Scatter(x=df['Date'], y=df['Calories Burn'], name="Cals Burned", mode='lines+markers', line=dict(color='#E74C3C', width=3)), secondary_y=True)
fig_effort = apply_mobile_layout(fig_effort)
fig_effort.update_yaxes(title_text="Steps", secondary_y=False)
fig_effort.update_yaxes(title_text="Cals", secondary_y=True)
st.plotly_chart(fig_effort, use_container_width=True)

st.divider()

# ==========================================
# 10. 3D Fitness Matrix
# ==========================================
st.subheader("🌌 3D Fitness Matrix")
fig_3d = px.scatter_3d(
    df, x='Steps', y='Calories Burn', z='Actual Weight in Kgs',
    color='Recovery (%)', size='Sleep (Hrs)',
    hover_name='Date', hover_data=['Strain'],
    color_continuous_scale='Viridis', template='plotly_dark'
)
fig_3d.update_layout(margin=dict(l=0, r=0, b=0, t=0), coloraxis_colorbar=dict(orientation="h", y=-0.2))
st.plotly_chart(fig_3d, use_container_width=True)

st.divider()

# ==========================================
# 11. Habit Correlation Matrix
# ==========================================
st.subheader("🧬 Habit Correlation")
metrics_df = df[['Steps', 'Calories Burn', 'Strain', 'Sleep (Hrs)', 'Recovery (%)', 'Actual Weight in Kgs']]
corr_matrix = metrics_df.corr().round(2)
fig_corr = px.imshow(corr_matrix, text_auto=True, aspect="auto", color_continuous_scale='RdBu_r')
fig_corr = apply_mobile_layout(fig_corr, is_heatmap=True)
st.plotly_chart(fig_corr, use_container_width=True)

st.divider()

# ==========================================
# 12. Deep Dive Analytics
# ==========================================
st.title("🔬 Deep Dive Analytics")

# Sleep vs Recovery
st.subheader("🛌 Sleep vs. Recovery (%)")
fig_sleep = px.scatter(df, x="Sleep (Hrs)", y="Recovery (%)", trendline="ols", color="Strain", color_continuous_scale="reds")
fig_sleep = apply_mobile_layout(fig_sleep, is_heatmap=True)
st.plotly_chart(fig_sleep, use_container_width=True)

# Calorie Burn vs Strain
st.subheader("❤️‍🔥 Calorie Burn vs. Strain")
fig_strain = px.scatter(df, x="Strain", y="Calories Burn", trendline="ols", color="Steps", color_continuous_scale="blues")
fig_strain = apply_mobile_layout(fig_strain, is_heatmap=True)
st.plotly_chart(fig_strain, use_container_width=True)

# Calorie Burn vs Weight Drop
st.subheader("⚖️ Cals Burned vs. Weight Drop")
fig_weight_drop = px.scatter(df, x="Calories Burn", y="Next Day Weight Change", trendline="ols", color="Recovery (%)", color_continuous_scale="greens")
fig_weight_drop.add_hline(y=0, line_dash="dash", line_color="white", annotation_text="No Change")
fig_weight_drop = apply_mobile_layout(fig_weight_drop, is_heatmap=True)
st.plotly_chart(fig_weight_drop, use_container_width=True)