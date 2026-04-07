import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from engine import calculate_bond_metrics
from datetime import date
import io  # Add this to your imports at the top

# --- PAGE CONFIG ---
st.set_page_config(page_title="BVC Analytics Terminal", layout="wide")

# --- DATA LOADING ---
@st.cache_data
def load_data():
    df = pd.read_excel("tes_data.xlsx")
    df['Maturity date'] = pd.to_datetime(df['Maturity date']).dt.date
    return df

df = load_data()

# --- SIDEBAR: MARKET SELECTION ---
st.sidebar.header("Market Selection")
market_type = st.sidebar.selectbox("Category", ["TES COP", "TES UVR", "TCO"])
filtered_df = df[df['TYPE'] == market_type]

# Narrow card-like selection in sidebar
selected_nemo = st.sidebar.radio(
    "Select Instrument",
    filtered_df['PNEMO'].tolist(),
    index=0
)

# --- MAIN DASHBOARD ---
st.title(f"Valuation: {selected_nemo}")
bond = df[df['PNEMO'] == selected_nemo].iloc[0]

# 1. Input Parameters (Top Row)
col1, col2, col3 = st.columns(3)
with col1:
    nominal = st.number_input("Nominal", value=1000000000, step=1000000)
with col2:
    val_date = st.date_input("Valuation Date", value=date(2026, 4, 7))
with col3:
    ytm = st.number_input("YTM (%)", value=12.0, step=0.01)

# 2. Run Calculations
res = calculate_bond_metrics(val_date, bond['Maturity date'], bond['Coupon']/100, ytm/100, bond['Freq'], bond['TYPE'])
user_scale = nominal / (1000000000 if bond['TYPE'] in ['TES COP', 'TCO'] else 1000000)

# 3. KPI Grid (2x3)
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Clean Price", f"$ {(res['clean'] * nominal / 100):,.0f}")
kpi2.metric("Accrued Interest", f"$ {(res['accrued'] * nominal / 100):,.0f}")
kpi3.metric("Dirty Price", f"$ {(res['dirty'] * nominal / 100):,.0f}")

kpi4, kpi5, kpi6 = st.columns(3)
kpi4.metric("Macaulay Dur", f"{res['macaulay']:.2f} Y")
kpi5.metric("Mod Duration", f"{res['mod_dur']:.4f}")
kpi6.metric("Convexity", f"{res['convexity']:.4f}")

# 4. Chart
cff = res['cf_table'].copy()
fig = go.Figure(data=[
    go.Bar(name='Interest', x=cff['Date'], y=cff['Interest'] * user_scale, marker_color='#0d6efd'),
    go.Bar(name='Principal', x=cff['Date'], y=cff['Principal'] * user_scale, marker_color='#198754')
])
fig.update_layout(barmode='stack', margin=dict(t=20, b=20, l=10, r=10), height=350, template="plotly_white")
st.plotly_chart(fig, use_container_width=True)

# --- 5. Data Table & Export ---
st.subheader("Cash Flow Details")
numeric_cols = ['Interest', 'Principal', 'Total CF', 'DCF']
formatted_df = cff.style.format({col: "{:,.2f}" for col in numeric_cols})
st.dataframe(formatted_df, use_container_width=True, height=300)

# Removed @st.cache_data to ensure it updates with every selection change
def convert_to_excel(_df_to_convert):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Convert date objects to strings if needed for Excel compatibility
        temp_df = _df_to_convert.copy()
        temp_df.to_excel(writer, index=False, sheet_name='CashFlows')
    return output.getvalue()

# Process the file for download - this now runs fresh every time cff changes
excel_data = convert_to_excel(cff)

st.download_button(
    label="Export to Excel",
    data=excel_data,
    file_name=f"{selected_nemo}_valuation.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="download-excel" # Added a key to maintain state stability
)