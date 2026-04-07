import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Financial Executive View", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for high-contrast visibility
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
    # ttl=0 ensures we don't cache bad data
    df = conn.read(spreadsheet=SHEET_URL, ttl=0)
except Exception as e:
    st.error(f"Connection Error: {e}")
    st.stop()

# --- 3. THE "STRICT" CLEANER ---
def force_clean_numeric(val):
    """Deep cleans strings, currency symbols, and commas."""
    if pd.isna(val) or val == "":
        return 0.0
    try:
        # Convert to string and strip everything except numbers and dots
        clean_str = "".join(c for c in str(val) if c.isdigit() or c == '.')
        # If the result is just a dot or empty, return 0
        if clean_str == "." or not clean_str:
            return 0.0
        return float(clean_str)
    except:
        return 0.0

# Apply strict cleaning to the key financial columns
cols_to_fix = ['Cash Collected', 'DD Collected', 'Cash Due', 'DD Due']
for col in cols_to_fix:
    if col in df.columns:
        df[col] = df[col].apply(force_clean_numeric)

# --- 4. SIDEBAR & DATA SELECTION ---
st.sidebar.header("Navigation")
if not df.empty:
    month_list = df['Month'].unique().tolist()
    selected_month = st.sidebar.selectbox("Select Billing Month", month_list)
    m_data = df[df['Month'] == selected_month].iloc[0]
else:
    st.error("Sheet is empty. Check your Sync Script.")
    st.stop()

# --- 5. HEADER ---
st.title(f"📊 Financial Performance: {selected_month}")
st.markdown(f"**Source:** Master File Billing | **Status:** Live Sync")
st.divider()

# --- 6. KPI METRICS ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Cash Collected", f"£{m_data['Cash Collected']:,.2f}")
c2.metric("DD Collected", f"£{m_data['DD Collected']:,.2f}")
c3.metric("Cash Due", f"£{m_data['Cash Due']:,.2f}")
c4.metric("DD Due", f"£{m_data['DD Due']:,.2f}")

st.divider()

# --- 7. ANALYTICS ---
left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("Collection vs. Target")
    fig = go.Figure(data=[
        go.Bar(name='Collected', x=['Cash', 'Direct Debit'], 
               y=[m_data['Cash Collected'], m_data['DD Collected']], marker_color='#2ecc71'),
        go.Bar(name='Outstanding Due', x=['Cash', 'Direct Debit'], 
               y=[m_data['Cash Due'], m_data['DD Due']], marker_color='#e74c3c')
    ])
    fig.update_layout(barmode='group', height=400, margin=dict(t=20, b=20, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

with right_col:
    st.subheader("Collection Efficiency %")
    
    # Calculation Logic
    # We use (Collected / Due) * 100. 
    # If the number is still huge, check if 'Due' is 1.0 (representing 100%) in the sheet.
    cash_eff = (m_data['Cash Collected'] / m_data['Cash Due'] * 100) if m_data['Cash Due'] > 0 else 0
    dd_eff = (m_data['DD Collected'] / m_data['DD Due'] * 100) if m_data['DD Due'] > 0 else 0
    
    st.write(f"**Cash Collection:** {cash_eff:.1f}%")
    st.progress(min(cash_eff / 100, 1.0))
    
    st.write(f"**Direct Debit:** {dd_eff:.1f}%")
    st.progress(min(dd_eff / 100, 1.0))
    
    # Overall
    total_col = m_data['Cash Collected'] + m_data['DD Collected']
    total_due = m_data['Cash Due'] + m_data['DD Due']
    overall_eff = (total_col / total_due * 100) if total_due > 0 else 0
    
    if overall_eff > 100:
        st.success(f"⭐ **Efficiency: {overall_eff:.1f}%** (Over Target)")
    else:
        st.info(f"💡 **Overall Efficiency: {overall_eff:.1f}%**")

# --- 8. HISTORICAL ---
st.divider()
st.subheader("Total Collection Trend")
df['Total'] = df['Cash Collected'] + df['DD Collected']
st.line_chart(df.set_index('Month')['Total'])

with st.expander("Audit Raw Values"):
    st.write(df[['Month', 'Cash Collected', 'Cash Due', 'DD Collected', 'DD Due']])
