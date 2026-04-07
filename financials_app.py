import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Financial Executive View", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for professional spacing
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 800; color: #2c3e50; }
    .stProgress > div > div > div > div { background-color: #2ecc71; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA CONNECTION ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1Bm5WIq19vWpNmVHir40eU3zl5Yx36EDdGCS0xEdCA5Y"

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=SHEET_URL, ttl=0)
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

# --- 3. THE "STRICT" CLEANER ---
def force_clean_numeric(val):
    if pd.isna(val) or val == "":
        return 0.0
    try:
        clean_str = "".join(c for c in str(val) if c.isdigit() or c == '.')
        if clean_str == "." or not clean_str:
            return 0.0
        return float(clean_str)
    except:
        return 0.0

cols_to_fix = ['Cash Collected', 'DD Collected', 'Cash Due', 'DD Due']
for col in cols_to_fix:
    if col in df.columns:
        df[col] = df[col].apply(force_clean_numeric)

# --- 4. SIDEBAR NAVIGATION ---
if not df.empty:
    st.sidebar.header("Navigation")
    month_list = df['Month'].unique().tolist()
    selected_month = st.sidebar.selectbox("Select Billing Month", month_list)
    m_data = df[df['Month'] == selected_month].iloc[0]
else:
    st.warning("No data found. Check your Google Sheet sync.")
    st.stop()

# --- 5. HEADER ---
st.title(f"📊 Financial Performance: {selected_month}")
st.markdown(f"**Live Dashboard** | Aggregating Collection vs. Outstanding Debt")
st.divider()

# --- 6. KPI METRICS (D21 - D24) ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Cash Collected", f"£{m_data['Cash Collected']:,.2f}")
c2.metric("DD Collected", f"£{m_data['DD Collected']:,.2f}")
c3.metric("Cash Due (O/S)", f"£{m_data['Cash Due']:,.2f}")
c4.metric("DD Due (O/S)", f"£{m_data['DD Due']:,.2f}")

st.divider()

# --- 7. ANALYTICS ---
left_col, right_col = st.columns([1, 1])

# Data extract for math
c_coll = m_data['Cash Collected']
c_due = m_data['Cash Due']
d_coll = m_data['DD Collected']
d_due = m_data['DD Due']

with left_col:
    st.subheader("Collection Breakdown")
    # Stacked bar shows the ratio of 'Collected' relative to the 'Total Potential'
    fig = go.Figure(data=[
        go.Bar(name='Collected', x=['Cash', 'Direct Debit'], y=[c_coll, d_coll], marker_color='#2ecc71'),
        go.Bar(name='Outstanding', x=['Cash', 'Direct Debit'], y=[c_due, d_due], marker_color='#e74c3c')
    ])
    fig.update_layout(
        barmode='stack', 
        height=450, 
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=0, b=0, l=0, r=0)
    )
    st.plotly_chart(fig, use_container_width=True)

with right_col:
    st.subheader("Collection Efficiency %")
    
    # Efficiency = Collected / (Collected + Due) * 100
    cash_total = c_coll + c_due
    dd_total = d_coll + d_due
    
    cash_eff = (c_coll / cash_total * 100) if cash_total > 0 else 0
    dd_eff = (d_coll / dd_total * 100) if dd_total > 0 else 0
    
    st.write(f"**Cash Collection Ratio:** {cash_eff:.1f}%")
    st.progress(cash_eff / 100)
    
    st.write(f"**Direct Debit Ratio:** {dd_eff:.1f}%")
    st.progress(dd_eff / 100)
    
    # Overall calculation
    total_banked = c_coll + d_coll
    total_expected = cash_total + dd_total
    overall_eff = (total_banked / total_expected * 100) if total_expected > 0 else 0
    
    st.info(f"💡 **Total Portfolio Efficiency for {selected_month} is {overall_eff:.1f}%**")

# --- 8. AUDIT DATA (OPTIONAL) ---
with st.expander("View Monthly Data Table"):
    st.table(df)
