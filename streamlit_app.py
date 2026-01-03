import streamlit as st
import pandas as pd
import plotly.express as px

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="SA Mining Industry Dashboard (2012–2022)",
    layout="wide"
)

st.title("🇿🇦 South Africa Mining Industry Dashboard (2012–2022)")
st.caption("Power BI–style analytical dashboard • Stats SA data • Current prices")

# --------------------------------------------------
# DATA LOADING
# --------------------------------------------------
@st.cache_data
def load_data():
    df_raw = pd.read_excel("Mining industry from 2012 to 2022.xlsx", header=None)

    df = df_raw.iloc[1:].copy()
    df = df[[2, 3, 10, 11, 12, 13]].dropna(subset=[2])
    df.columns = ['code', 'mineral', '2012', '2015', '2019', '2022']

    df['metric'] = df['code'].astype(str).str.extract(r'^([A-Z]+)')[0]

    df_long = df.melt(
        id_vars=['code', 'metric', 'mineral'],
        value_vars=['2012', '2015', '2019', '2022'],
        var_name='year',
        value_name='value'
    )

    df_long['year'] = df_long['year'].astype(int)
    df_long['value'] = pd.to_numeric(df_long['value'], errors='coerce')
    df_long = df_long.dropna(subset=['value'])

    df_long['mineral_clean'] = (
        df_long['mineral']
        .astype(str)
        .str.replace('Mining of ', '', regex=False)
        .str.replace(r'\s*\(.*\)', '', regex=True)
        .str.strip()
        .str.lower()
    )

    df_long.loc[
        df_long['code'].astype(str).str.endswith('29999'),
        'mineral_clean'
    ] = 'total industry'

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
# SIDEBAR FILTERS
# --------------------------------------------------
st.sidebar.header("Filters")

metrics = sorted(df['metric_name'].unique())
selected_metric = st.sidebar.selectbox(
    "Metric",
    metrics,
    index=metrics.index('Sales Revenue') if 'Sales Revenue' in metrics else 0
)

minerals = sorted(df[df['metric_name'] == selected_metric]['mineral_clean'].unique())

default_minerals = [m for m in [
    'total industry',
    'coal and lignite',
    'platinum group metal ore'
] if m in minerals]

selected_minerals = st.sidebar.multiselect(
    "Minerals",
    minerals,
    default=default_minerals
)

selected_year = st.sidebar.selectbox(
    "Year",
    [2022, 2019, 2015, 2012],
    index=0
)

filtered = df[df['metric_name'] == selected_metric]

# --------------------------------------------------
# KPI CALCULATIONS
# --------------------------------------------------
sales_2012 = filtered.query(
    "year == 2012 and mineral_clean == 'total industry'"
)['value'].sum()

sales_2022 = filtered.query(
    "year == 2022 and mineral_clean == 'total industry'"
)['value'].sum()

sales_growth = ((sales_2022 - sales_2012) / sales_2012 * 100) if sales_2012 else 0

emp_2012 = df.query(
    "metric_name == 'Employment (Persons)' and year == 2012 and mineral_clean == 'total industry'"
)['value'].sum()

emp_2022 = df.query(
    "metric_name == 'Employment (Persons)' and year == 2022 and mineral_clean == 'total industry'"
)['value'].sum()

emp_change = ((emp_2022 - emp_2012) / emp_2012 * 100) if emp_2012 else 0

# --------------------------------------------------
# EXECUTIVE KPI STRIP
# --------------------------------------------------
st.markdown("## Executive Overview")

k1, k2, k3, k4 = st.columns(4)

k1.metric("Total Sales (2022)", f"R{sales_2022:,.0f}M", f"{sales_growth:+.1f}% vs 2012")
k2.metric("Total Sales (2012)", f"R{sales_2012:,.0f}M")
k3.metric("Employment (2022)", f"{int(emp_2022):,}", f"{emp_change:+.1f}% vs 2012")
k4.metric("Employment (2012)", f"{int(emp_2012):,}")

st.divider()

# --------------------------------------------------
# POWER BI–STYLE TABS
# --------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Trends", "🧱 Mineral Breakdown"])

with tab1:
    st.subheader(f"{selected_metric} – Top Minerals ({selected_year})")

    bar_data = (
        filtered[filtered['year'] == selected_year]
        .sort_values('value', ascending=True)
        .tail(12)
    )

    fig = px.bar(
        bar_data,
        x='value',
        y='mineral_clean',
        orientation='h',
        text='value'
    )

    fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
    fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title=None)

    st.plotly_chart(fig, use_container_width=True)

with tab2:
    if selected_minerals:
        trend_data = filtered[filtered['mineral_clean'].isin(selected_minerals)]
        fig = px.line(trend_data, x='year', y='value', color='mineral_clean', markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Select minerals to view trends.")

with tab3:
    pivot = (
        filtered
        .pivot_table(index='mineral_clean', columns='year', values='value', aggfunc='sum')
        .sort_values(by=selected_year, ascending=False)
        .head(10)
    )

    st.dataframe(pivot.style.format("{:,.0f}"), use_container_width=True)

st.success("Dashboard loaded successfully.")
