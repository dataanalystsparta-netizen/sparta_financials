import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection


# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Financial Executive View", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for high-contrast visibility and professional spacing
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 800; color: #2c3e50; }
    .stProgress > div > div > div > div { background-color: #2ecc71; }
    .css-1kyx60l { background-color: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA CONNECTION ---
# Using your specific Sheet ID
SHEET_URL = "https://docs.google.com/spreadsheets/d/1Bm5WIq19vWpNmVHir40eU3zl5Yx36EDdGCS0xEdCA5Y"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=SHEET_URL, ttl=0) # ttl=0 forces a fresh pull every refresh
except Exception as e:
    st.error(f"Failed to connect to Google Sheets: {e}")
    st.stop()

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.header("Navigation")
if not df.empty:
    month_list = df['Month'].unique().tolist()
    selected_month = st.sidebar.selectbox("Select Billing Month", month_list)
    
    # Filter for the selected month
    m_data = df[df['Month'] == selected_month].iloc[0]
else:
    st.warning("No data found in Google Sheets. Please run the sync script first.")
    st.stop()

# --- 4. HEADER ---
st.title(f"📊 Financial Performance: {selected_month}")
st.markdown(f"**Source:** Master File Billing (Network Drive) | **Status:** Live Sync")
st.divider()

# --- 5. KPI METRICS (D21 - D24) ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Cash Collected", f"£{m_data['Cash Collected']:,.2f}")
with col2:
    st.metric("DD Collected", f"£{m_data['DD Collected']:,.2f}")
with col3:
    st.metric("Cash Due", f"£{m_data['Cash Due']:,.2f}")
with col4:
    st.metric("DD Due", f"£{m_data['DD Due']:,.2f}")

st.divider()

# --- 6. VISUAL ANALYTICS ---
left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("Collection vs. Target")
    fig = go.Figure(data=[
        go.Bar(name='Collected', x=['Cash', 'Direct Debit'], 
               y=[m_data['Cash Collected'], m_data['DD Collected']], marker_color='#2ecc71'),
        go.Bar(name='Outstanding Due', x=['Cash', 'Direct Debit'], 
               y=[m_data['Cash Due'], m_data['DD Due']], marker_color='#e74c3c')
    ])
    fig.update_layout(barmode='group', height=400, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)


with right_col:
    st.subheader("Collection Efficiency %")
    
    # Calculations
    cash_efficiency = (m_data['Cash Collected'] / m_data['Cash Due'] * 100) if m_data['Cash Due'] > 0 else 0
    dd_efficiency = (m_data['DD Collected'] / m_data['DD Due'] * 100) if m_data['DD Due'] > 0 else 0
    
    # Display Cash Progress (Capped at 1.0 for the UI bar)
    st.write(f"**Cash Collection Ratio:** {cash_efficiency:.1f}%")
    st.progress(min(cash_efficiency / 100, 1.0)) # <--- min() added here
    
    # Display DD Progress (Capped at 1.0 for the UI bar)
    st.write(f"**Direct Debit Ratio:** {dd_efficiency:.1f}%")
    st.progress(min(dd_efficiency / 100, 1.0))   # <--- min() added here
    
    # Summary Card
    total_col = m_data['Cash Collected'] + m_data['DD Collected']
    total_due = m_data['Cash Due'] + m_data['DD Due']
    overall_eff = (total_col / total_due * 100) if total_due > 0 else 0
    
    if overall_eff > 100:
        st.success(f"⭐ **Exceptional Performance! Overall Efficiency: {overall_eff:.1f}%**")
    else:
        st.info(f"💡 **Overall Collection Efficiency for {selected_month} is {overall_eff:.1f}%**")


# --- 7. HISTORICAL TREND ---
st.divider()
st.subheader("Historical Comparison")
# Simple line chart showing Total Collection over time
df['Total Collected'] = df['Cash Collected'] + df['DD Collected']
st.line_chart(df.set_index('Month')['Total Collected'])

with st.expander("View Raw Data Table"):
    st.table(df)
