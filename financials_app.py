import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_gsheets import GSheetsConnection

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="Financial Executive View", layout="wide", initial_sidebar_state="expanded")

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

# --- 4. DATA SELECTION ---
if not df.empty:
    month_list = df['Month'].unique().tolist()
    selected_month = st.sidebar.selectbox("Select Billing Month", month_list)
    m_data = df[df['Month'] == selected_month].iloc[0]
else:
    st.stop()

# --- 5. HEADER ---
st.title(f"📊 Financial Performance: {selected_month}")
st.divider()

# --- 6. KPI METRICS ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Cash Collected", f"£{m_data['Cash Collected']:,.2f}")
c2.metric("DD Collected", f"£{m_data['DD Collected']:,.2f}")
c3.metric("Cash Due (O/S)", f"£{m_data['Cash Due']:,.2f}")
c4.metric("DD Due (O/S)", f"£{m_data['DD Due']:,.2f}")

st.divider()

# --- 7. ANALYTICS (UPDATED FORMULA) ---
left_col, right_col = st.columns([1, 1])

# Extract values for readability
c_coll = m_data['Cash Collected']
c_due = m_data['Cash Due']
d_coll = m_data['DD Collected']
d_due = m_data['DD Due']

with left_col:
    st.subheader("Collection vs. Outstanding")
    fig = go.Figure(data=[
        go.Bar(name='Collected', x=['Cash', 'Direct Debit'], y=[c_coll, d_coll], marker_color='#2ecc71'),
        go.Bar(name='Still Due', x=['Cash', 'Direct Debit'], y=[c_due, d_due], marker_color='#e74c3c')
    ])
    fig.update_layout(barmode='stack', height=400) # Changed to 'stack' for a better visual of the "Total"
    st.plotly_chart(fig, use_container_width=True)

with right_col:
    st.subheader("Collection Efficiency %")
    
    # NEW FORMULAS PER YOUR REQUIREMENT:
    # Efficiency = Collected / (Collected + Due) * 100
    
    cash_total_potential = c_coll + c_due
    dd_total_potential = d_coll + d_due
    
    cash_eff = (c_coll / cash_total_potential * 100) if cash_total_potential > 0 else 0
    dd_eff = (d_coll / dd_total_potential * 100) if dd_total_potential > 0 else 0
    
    st.write(f"**Cash Collection Ratio:** {cash_eff:.1f}%")
    st.progress(cash_eff / 100)
    
    st.write(f"**Direct Debit Ratio:** {dd_eff:.1f}%")
    st.progress(dd_eff / 100)
    
    # Overall Efficiency
    grand_total_coll = c_coll + d_coll
    grand_total_potential = cash_total_potential + dd_total_potential
    overall_eff = (grand_total_coll / grand_total_potential * 100) if grand_total_potential > 0 else 0
    
    st.info(f"💡 **Total Portfolio Collection: {overall_eff:.1f}%**")

# --- 8. TREND ---
st.divider()
df['Total Portfolio'] = (df['Cash Collected'] + df['Cash Due'] + df['DD Collected'] + df['DD Due'])
st.subheader("Total Billing Volume Trend")
st.line_chart(df.set_index('Month')['Total Portfolio'])
