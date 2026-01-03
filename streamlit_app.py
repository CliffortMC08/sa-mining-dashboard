import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------
# Page Config
# ---------------------------
st.set_page_config(page_title="SA Mining Story Dashboard", layout="wide", page_icon="⛏️")

# ---------------------------
# Load Data
# ---------------------------
@st.cache_data
def load_data():
    df_raw = pd.read_excel("Mining industry from 2012 to 2022.xlsx", header=None)
    df = df_raw.iloc[1:, [2,3,10,11,12,13]].dropna(subset=[2])
    df.columns = ['code','mineral','2012','2015','2019','2022']
    df['metric'] = df['code'].astype(str).str.extract(r'^([A-Z]+)')[0]
    df_long = df.melt(id_vars=['code','metric','mineral'], value_vars=['2012','2015','2019','2022'],
                      var_name='Year', value_name='Value')
    df_long['Year'] = df_long['Year'].astype(int)
    df_long['Value'] = pd.to_numeric(df_long['Value'], errors='coerce')
    df_long['Mineral'] = df_long['mineral'].astype(str).str.replace('Mining of ','',regex=False).str.replace(r'\s*\(.*\)','',regex=True).str.strip().str.title()
    df_long.loc[df_long['code'].astype(str).str.endswith('29999'),'Mineral'] = 'Total Industry'
    metric_map = {'FOPEN':'Opening Stock','FISALES':'Sales Revenue','FINC':'Total Income','FEXP':'Total Expenditure',
                  'FCLOSE':'Closing Stock','FEMPTOT':'Employment (Persons)'}
    df_long['Metric'] = df_long['metric'].map(metric_map).fillna(df_long['metric'])
    return df_long

df = load_data()

# ---------------------------
# Sidebar Navigation
# ---------------------------
page = st.sidebar.radio("Select Page", [
    "Executive Overview",
    "Revenue Deep Dive",
    "Employment & Productivity",
    "Costs & Profitability",
    "Provincial View"
])

# ---------------------------
# Common Filters
# ---------------------------
years = sorted(df['Year'].unique())
selected_year = st.sidebar.slider("Year Range", min_value=min(years), max_value=max(years), value=(min(years), max(years)))

minerals = sorted(df['Mineral'].unique())
selected_minerals = st.sidebar.multiselect("Minerals", minerals, default=['Total Industry','Platinum Group Metal Ore','Coal And Lignite'])

metrics = sorted(df['Metric'].unique())
selected_metric = st.sidebar.selectbox("Metric", metrics, index=metrics.index('Sales Revenue') if 'Sales Revenue' in metrics else 0)

filtered_df = df[
    (df['Year'].between(selected_year[0], selected_year[1])) &
    (df['Mineral'].isin(selected_minerals)) &
    (df['Metric']==selected_metric)
]

# ---------------------------
# Page Functions
# ---------------------------
def executive_overview():
    st.markdown("### Key KPIs")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    total_value = filtered_df['Value'].sum()
    avg_value = filtered_df.groupby('Year')['Value'].sum().mean()
    num_minerals = filtered_df['Mineral'].nunique()
    num_years = filtered_df['Year'].nunique()
    kpi1.metric("Total", f"{total_value:,.0f}")
    kpi2.metric("Average Annual", f"{avg_value:,.0f}")
    kpi3.metric("Minerals", num_minerals)
    kpi4.metric("Years", num_years)

    st.markdown("### Trend Chart")
    line_fig = px.line(filtered_df, x='Year', y='Value', color='Mineral', markers=True)
    st.plotly_chart(line_fig, use_container_width=True)

def revenue_deep_dive():
    st.markdown("Revenue Deep Dive - Treemap Example")
    treemap_df = filtered_df.groupby('Mineral', as_index=False)['Value'].sum()
    fig = px.treemap(treemap_df, path=['Mineral'], values='Value', title='2022 Revenue Share')
    st.plotly_chart(fig, use_container_width=True)

def employment_productivity():
    st.markdown("Employment & Productivity - Sample")
    emp_df = df[(df['Metric']=='Employment (Persons)') & (df['Mineral'].isin(selected_minerals))]
    fig = px.line(emp_df, x='Year', y='Value', color='Mineral', markers=True, title="Employment Trend")
    st.plotly_chart(fig, use_container_width=True)

def costs_profitability():
    st.markdown("Costs & Profitability - Placeholder")
    st.write(filtered_df.head())

def provincial_view():
    st.markdown("Provincial Sales Map - Placeholder")
    st.write(filtered_df.head())

# ---------------------------
# Page Dispatcher
# ---------------------------
pages = {
    "Executive Overview": executive_overview,
    "Revenue Deep Dive": revenue_deep_dive,
    "Employment & Productivity": employment_productivity,
    "Costs & Profitability": costs_profitability,
    "Provincial View": provincial_view
}

pages[page]()
