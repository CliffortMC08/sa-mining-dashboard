import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------------------------------
# App configuration
# --------------------------------------------------
st.set_page_config(
    page_title="SA Mining Industry Dashboard 2012–2022",
    layout="wide"
)

st.title("🇿🇦 South Africa Mining Industry Dashboard (2012–2022)")
st.markdown("Interactive view of Stats SA mining data • Current prices (R million or persons)")

# --------------------------------------------------
# Data loading
# --------------------------------------------------
@st.cache_data
def load_data():
    df_raw = pd.read_excel("Mining industry from 2012 to 2022.xlsx", header=None)

    df = df_raw.iloc[1:].copy()
    df = df[[2, 3, 10, 11, 12, 13]].dropna(subset=[2])
    df.columns = ['code', 'mineral', '2012', '2015', '2019', '2022']

    # Extract metric safely
    df['metric'] = df['code'].astype(str).str.extract(r'^([A-Z]+)')[0]

    # 🔴 FIX: keep 'code' during melt
    df_long = df.melt(
        id_vars=['code', 'metric', 'mineral'],
        value_vars=['2012', '2015', '2019', '2022'],
        var_name='year',
        value_name='value'
    )

    df_long['year'] = df_long['year'].astype(int)
    df_long['value'] = pd.to_numeric(df_long['value'], errors='coerce')
    df_long = df_long.dropna(subset=['value'])

    # Clean mineral names
    df_long['mineral_clean'] = (
        df_long['mineral']
        .astype(str)
        .str.replace('Mining of ', '', regex=False)
        .str.replace(r'\s*\(.*\)', '', regex=True)
        .str.strip()
        .str.lower()
    )

    # Identify Total Industry rows (now works)
    df_long.loc[
        df_long['code'].astype(str).str.endswith('29999'),
        'mineral_clean'
    ] = 'total industry'

    # Metric mapping
    metric_map = {
        'FOPEN': 'Opening Stock',
        'FISALES': 'Sales Revenue',
        'FINC': 'Total Income',
        'FEXP': 'Total Expenditure',
        'FCLOSE': 'Closing Stock',
        'FEMPTOT': 'Employment (Persons)',
        'FOTHIN': 'Other Income',
        'FPURCH': 'Purchases',
        'FSUB': 'Subsidies',
        'FSAL': 'Salaries & Wages',
        'FUTILITIES': 'Utilities',
        'FLBROKER': 'Broker Fees',
        'FOTHEX': 'Other Expenses'
    }

    df_long['metric_name'] = df_long['metric'].map(metric_map).fillna(df_long['metric'])

    return df_long


df = load_data()

# --------------------------------------------------
# Sidebar filters
# --------------------------------------------------
st.sidebar.header("Filters")

available_metrics = sorted(df['metric_name'].unique())
selected_metric = st.sidebar.selectbox(
    "Select Metric",
    available_metrics,
    index=available_metrics.index('Sales Revenue')
    if 'Sales Revenue' in available_metrics else 0
)

minerals = sorted(
    df[df['metric_name'] == selected_metric]['mineral_clean'].unique()
)

preferred_defaults = [
    'total industry',
    'platinum group metal ore',
    'coal and lignite',
    'gold and uranium ore',
    'iron ore',
    'diamonds'
]

default_minerals = [m for m in preferred_defaults if m in minerals]

selected_minerals = st.sidebar.multiselect(
    "Select Minerals for Trend",
    options=minerals,
    default=default_minerals
)

selected_year = st.sidebar.selectbox(
    "Year for Bar Chart",
    [2022, 2019, 2015, 2012],
    index=0
)

# --------------------------------------------------
# Visuals
# --------------------------------------------------
filtered = df[df['metric_name'] == selected_metric]

bar_data = (
    filtered[filtered['year'] == selected_year]
    .sort_values('value', ascending=False)
    .head(15)
)

fig_bar = px.bar(
    bar_data,
    x='mineral_clean',
    y='value',
    color='value',
    text='value',
    title=f"{selected_metric} in {selected_year}"
)

fig_bar.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
fig_bar.update_layout(xaxis_tickangle=45, showlegend=False)

st.plotly_chart(fig_bar, use_container_width=True)

if selected_minerals:
    line_data = filtered[filtered['mineral_clean'].isin(selected_minerals)]
    fig_line = px.line(
        line_data,
        x='year',
        y='value',
        color='mineral_clean',
        markers=True,
        title=f"{selected_metric} Trends"
    )
    st.plotly_chart(fig_line, use_container_width=True)

st.success("Dashboard loaded successfully.")
