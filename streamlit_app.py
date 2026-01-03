import streamlit as st
import pandas as pd
import plotly.express as px

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(
    page_title="SA Mining Executive Dashboard",
    page_icon="⛏️",
    layout="wide"
)

st.markdown("## ⛏️ South Africa Mining Industry – Executive Overview")

# -------------------------------
# LOAD EXCEL DATA
# -------------------------------
@st.cache_data
def load_data():
    file = "Mining industry from 2012 to 2022.xlsx"
    
    # Read Excel
    df_raw = pd.read_excel(file, header=None)

    # Select relevant columns: code=2, mineral=3, years=10–13
    df = df_raw.iloc[1:, [2, 3, 10, 11, 12, 13]].dropna(subset=[2])
    df.columns = ['code', 'mineral', '2012', '2015', '2019', '2022']

    # Extract metric code (e.g., FISALES)
    df['metric'] = df['code'].astype(str).str.extract(r'^([A-Z]+)')[0]

    # Melt to long format
    df_long = df.melt(
        id_vars=['code', 'metric', 'mineral'],
        value_vars=['2012', '2015', '2019', '2022'],
        var_name='Year',
        value_name='Value'
    )
    df_long['Year'] = df_long['Year'].astype(int)
    df_long['Value'] = pd.to_numeric(df_long['Value'], errors='coerce')
    df_long = df_long.dropna(subset=['Value'])

    # Clean mineral names
    df_long['Mineral'] = (
        df_long['mineral']
        .astype(str)
        .str.replace('Mining of ', '', regex=False)
        .str.replace(r'\s*\(.*\)', '', regex=True)
        .str.strip()
        .str.title()
    )
    df_long.loc[df_long['code'].astype(str).str.endswith('29999'), 'Mineral'] = 'Total Industry'

    # Map metric codes to human-readable names
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
    df_long['Metric'] = df_long['metric'].map(metric_map).fillna(df_long['metric'])

    return df_long

df = load_data()

# -------------------------------
# FILTER BAR (TOP CONTROL)
# -------------------------------
st.markdown("### Filters")
col1, col2, col3 = st.columns([2, 4, 4])

with col1:
    metric_options = sorted(df['Metric'].unique())
    selected_metric = st.selectbox(
        "Metric",
        metric_options,
        index=metric_options.index('Sales Revenue') if 'Sales Revenue' in metric_options else 0
    )

with col2:
    minerals = sorted(df[df['Metric'] == selected_metric]['Mineral'].unique())
    selected_minerals = st.multiselect(
        "Minerals",
        minerals,
        default=[m for m in ['Total Industry','Platinum Group Metal Ore','Coal And Lignite'] if m in minerals]
    )

with col3:
    years = sorted(df['Year'].unique(), reverse=True)
    selected_year = st.selectbox("Year", years, index=0)

# -------------------------------
# APPLY FILTERS
# -------------------------------
filtered_df = df[
    (df['Metric'] == selected_metric) &
    (df['Mineral'].isin(selected_minerals)) &
    (df['Year'] <= selected_year)
]

# -------------------------------
# KPI CARDS
# -------------------------------
st.markdown("### Executive KPIs")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

total_value = filtered_df['Value'].sum()
avg_value = filtered_df.groupby('Year')['Value'].sum().mean()
num_minerals = filtered_df['Mineral'].nunique()
num_years = filtered_df['Year'].nunique()

kpi1.metric("Total", f"{total_value:,.0f}")
kpi2.metric("Average Annual", f"{avg_value:,.0f}")
kpi3.metric("Minerals", num_minerals)
kpi4.metric("Years", num_years)

st.divider()

# -------------------------------
# LINE CHART
# -------------------------------
st.markdown("### Production Trend Over Time")
line_df = df[
    (df['Metric'] == selected_metric) &
    (df['Mineral'].isin(selected_minerals))
]

line_fig = px.line(
    line_df,
    x='Year',
    y='Value',
    color='Mineral',
    markers=True,
    title=f"{selected_metric} Trend"
)
st.plotly_chart(line_fig, use_container_width=True)

# -------------------------------
# PIE + BAR CHARTS
# -------------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### Contribution by Mineral")
    pie_fig = px.pie(
        filtered_df.groupby('Mineral', as_index=False)['Value'].sum(),
        names='Mineral',
        values='Value',
        hole=0.4
    )
    st.plotly_chart(pie_fig, use_container_width=True)

with col_right:
    st.markdown("### Top Minerals by Value")
    bar_fig = px.bar(
        filtered_df.groupby('Mineral', as_index=False)['Value'].sum()
        .sort_values('Value', ascending=False),
        x='Mineral',
        y='Value'
    )
    st.plotly_chart(bar_fig, use_container_width=True)

# -------------------------------
# DATA TABLE
# -------------------------------
st.markdown("### Detailed Data")
st.dataframe(
    filtered_df.sort_values(['Year','Value'], ascending=[True, False]),
    use_container_width=True,
    height=350
)
