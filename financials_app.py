import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Financial Executive View", layout="wide", initial_sidebar_state="expanded")

# --- 2. THEME & UI CUSTOMIZATION ---
st.sidebar.header("Settings")
theme_mode = st.sidebar.radio("Dashboard Theme", ["Light", "Dark"])

# Dynamic CSS based on theme selection
if theme_mode == "Dark":
    bg_color = "#0e1117"
    card_color = "#1d2129"
    text_color = "#ffffff"
    plot_bg = "rgba(0,0,0,0)"
else:
    bg_color = "#f4f7f9"
    card_color = "#ffffff"
    text_color = "#2c3e50"
    plot_bg = "#f4f7f9"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg_color}; color: {text_color}; }}
    div[data-testid="stMetricValue"] {{ font-size: 28px; font-weight: 800; color: {text_color}; }}
    .stProgress > div > div > div > div {{ background-color: #2ecc71; }}
    /* Metric Card Styling */
    [data-testid="stMetric"] {{
        background-color: {card_color};
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA CONNECTION ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1Bm5WIq19vWpNmVHir40eU3zl5Yx36EDdGCS0xEdCA5Y"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=SHEET_URL, ttl=0)
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

# --- 4. DATA CLEANER ---
def force_clean_numeric(val):
    if pd.isna(val) or val == "": return 0.0
    try:
        clean_str = "".join(c for c in str(val) if c.isdigit() or c == '.')
        return float(clean_str) if clean_str and clean_str != "." else 0.0
    except: return 0.0

cols_to_fix = ['Cash Collected', 'DD Collected', 'Cash Due', 'DD Due']
for col in cols_to_fix:
    if col in df.columns:
        df[col] = df[col].apply(force_clean_numeric)

# --- 5. SIDEBAR NAVIGATION ---
if not df.empty:
    month_list = df['Month'].unique().tolist()
    selected_month = st.sidebar.selectbox("Select Billing Month", month_list)
    m_data = df[df['Month'] == selected_month].iloc[0]
else:
    st.warning("No data found.")
    st.stop()

# --- 6. HEADER ---
st.title(f"📊 Financial Performance: {selected_month}")
st.divider()

# --- 7. KPI METRICS ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Cash Collected", f"£{m_data['Cash Collected']:,.2f}")
c2.metric("DD Collected", f"£{m_data['DD Collected']:,.2f}")
c3.metric("Cash Due (O/S)", f"£{m_data['Cash Due']:,.2f}")
c4.metric("DD Due (O/S)", f"£{m_data['DD Due']:,.2f}")

st.divider()

# --- 8. ANALYTICS ---
left_col, right_col = st.columns([1, 1])

c_coll, c_due = m_data['Cash Collected'], m_data['Cash Due']
d_coll, d_due = m_data['DD Collected'], m_data['DD Due']

with left_col:
    st.subheader("Collection Breakdown")
    fig = go.Figure(data=[
        go.Bar(name='Collected', x=['Cash', 'Direct Debit'], y=[c_coll, d_coll], marker_color='#2ecc71'),
        go.Bar(name='Outstanding', x=['Cash', 'Direct Debit'], y=[c_due, d_due], marker_color='#e74c3c')
    ])
    fig.update_layout(
        barmode='stack', height=450,
        paper_bgcolor=plot_bg,
        plot_bgcolor=plot_bg,
        font=dict(color=text_color),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=0, b=0, l=0, r=0)
    )
    st.plotly_chart(fig, use_container_width=True)

with right_col:
    st.subheader("Collection Efficiency %")
    
    cash_total, dd_total = (c_coll + c_due), (d_coll + d_due)
    cash_eff = (c_coll / cash_total * 100) if cash_total > 0 else 0
    dd_eff = (d_coll / dd_total * 100) if dd_total > 0 else 0
    
    st.write(f"**Cash Collection Ratio:** {cash_eff:.1f}%")
    st.progress(cash_eff / 100)
    
    st.write(f"**Direct Debit Ratio:** {dd_eff:.1f}%")
    st.progress(dd_eff / 100)
    
    overall_eff = ((c_coll + d_coll) / (cash_total + dd_total) * 100) if (cash_total + dd_total) > 0 else 0
    st.info(f"💡 **Total Portfolio Efficiency: {overall_eff:.1f}%**")

# --- 9. AUDIT DATA ---
with st.expander("View Monthly Data Table"):
    st.table(df)
