import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    df = df.dropna(subset=['Weight in Kgs'])
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%y')
    
    df['Steps'] = df['Steps'].fillna(0)
    df['Calories Burn'] = df['Calories Burn'].fillna(0)
    
    df['7-Day Avg Weight'] = df['Weight in Kgs'].rolling(window=7, min_periods=1).mean()
    df['Weight Change (kg)'] = df['Weight in Kgs'].diff()
    df['Next Day Weight Change'] = df['Weight Change (kg)'].shift(-1)
    
    return df

df = load_data()

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
# 4. Top Level Metrics (Changed to 2x2 Grid for Mobile)
# ==========================================
st.subheader("🏆 Quick Stats")
initial_weight = df['Weight in Kgs'].iloc[0]
current_weight = df['Weight in Kgs'].iloc[-1]
total_loss = current_weight - initial_weight

# Row 1
col1, col2 = st.columns(2)
with col1: st.metric("Starting Weight", f"{initial_weight} kg")
with col2: st.metric("Current Weight", f"{current_weight} kg", f"{total_loss:.2f} kg")

# Row 2
col3, col4 = st.columns(2)
with col3: st.metric("Avg Daily Steps", f"{int(df['Steps'].mean()):,}")
with col4: st.metric("Avg Sleep", f"{df['Sleep (Hrs)'].mean():.1f} hrs")

st.divider()

# ==========================================
# 5. Trend Analysis
# ==========================================
st.subheader("📉 True Weight Trajectory")
fig_weight = go.Figure()
fig_weight.add_trace(go.Scatter(x=df['Date'], y=df['Weight in Kgs'], mode='lines+markers', name='Daily', line=dict(color='rgba(0, 255, 170, 0.4)', dash='dot')))
fig_weight.add_trace(go.Scatter(x=df['Date'], y=df['7-Day Avg Weight'], mode='lines', name='7-Day Avg', line=dict(color='#00FFAA', width=4)))
fig_weight = apply_mobile_layout(fig_weight)
st.plotly_chart(fig_weight, use_container_width=True)

st.divider()

# ==========================================
# 6. Effort vs. Output
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
# 7. 3D Fitness Matrix
# ==========================================
st.subheader("🌌 3D Fitness Matrix")
fig_3d = px.scatter_3d(
    df, x='Steps', y='Calories Burn', z='Weight in Kgs',
    color='Recovery (%)', size='Sleep (Hrs)',
    hover_name='Date', hover_data=['Strain'],
    color_continuous_scale='Viridis', template='plotly_dark'
)
# 3D plots need completely zero margins to render well on mobile
fig_3d.update_layout(margin=dict(l=0, r=0, b=0, t=0), coloraxis_colorbar=dict(orientation="h", y=-0.2))
st.plotly_chart(fig_3d, use_container_width=True)

st.divider()

# ==========================================
# 8. Habit Correlation Matrix
# ==========================================
st.subheader("🧬 Habit Correlation")
metrics_df = df[['Steps', 'Calories Burn', 'Strain', 'Sleep (Hrs)', 'Recovery (%)', 'Weight in Kgs']]
corr_matrix = metrics_df.corr().round(2)
fig_corr = px.imshow(corr_matrix, text_auto=True, aspect="auto", color_continuous_scale='RdBu_r')
fig_corr = apply_mobile_layout(fig_corr, is_heatmap=True)
st.plotly_chart(fig_corr, use_container_width=True)

st.divider()

# ==========================================
# 9. Deep Dive Analytics
# ==========================================
st.title("🔬 Deep Dive Analytics")

# Sleep vs Recovery
st.subheader("🛌 Sleep vs. Recovery (%)")
fig_sleep = px.scatter(df, x="Sleep (Hrs)", y="Recovery (%)", trendline="ols", color="Strain", color_continuous_scale="reds")
fig_sleep = apply_mobile_layout(fig_sleep, is_heatmap=True) # Treats colorbar like heatmap
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