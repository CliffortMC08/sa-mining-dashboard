import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------
# PAGE CONFIG
# ---------------------------
st.set_page_config(page_title="SA Mining Executive Dashboard", layout="wide", page_icon="⛏️")

st.title("⛏️ South Africa Mining Industry Dashboard (2012–2022)")
st.markdown("Interactive executive dashboard with trends, revenue deep dive, employment & productivity, costs & profitability, and provincial analysis.")

# ---------------------------
# LOAD DATA
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

    # Clean mineral names
    df_long['Mineral'] = (
        df_long['mineral'].astype(str)
        .str.replace('Mining of ','',regex=False)
        .str.replace(r'\s*\(.*\)','',regex=True)
        .str.strip().str.title()
    )
    df_long.loc[df_long['code'].astype(str).str.endswith('29999'),'Mineral'] = 'Total Industry'

    # Map metric codes
    metric_map = {'FOPEN':'Opening Stock','FISALES':'Sales Revenue','FINC':'Total Income',
                  'FEXP':'Total Expenditure','FCLOSE':'Closing Stock','FEMPTOT':'Employment (Persons)'}
    df_long['Metric'] = df_long['metric'].map(metric_map).fillna(df_long['metric'])

    # Compute derived metric: Sales per Employee
    sales = df_long[df_long['Metric']=='Sales Revenue']
    employment = df_long[df_long['Metric']=='Employment (Persons)']
    merged = pd.merge(sales, employment, on=['Mineral','Year'], suffixes=('_Sales','_Emp'))
    merged['Sales_per_Employee'] = merged['Value_Sales'] / merged['Value_Emp']
    return df_long, merged

df, df_merged = load_data()

# ---------------------------
# SIDEBAR: PAGE NAVIGATION
# ---------------------------
page = st.sidebar.radio("📄 Select Page", [
    "Executive Overview",
    "Revenue Deep Dive",
    "Employment & Productivity",
    "Costs & Profitability",
    "Provincial View"
])

# ---------------------------
# SIDEBAR: YEAR FILTER
# ---------------------------
years = sorted(df['Year'].unique())
selected_year = st.sidebar.slider("Select Year Range", min_value=min(years), max_value=max(years), value=(min(years), max(years)))

# ---------------------------
# SIDEBAR: METRIC FILTER
# ---------------------------
metrics = sorted(df['Metric'].unique())
selected_metric = st.sidebar.selectbox("Select Metric", metrics, index=metrics.index('Sales Revenue') if 'Sales Revenue' in metrics else 0)

# ---------------------------
# MINERALS FILTER (BUTTON STYLE SLICER)
# ---------------------------
st.sidebar.markdown("### Select Minerals")
all_minerals = sorted(df['Mineral'].unique())
# Initialize selected minerals session state
if "selected_minerals" not in st.session_state:
    st.session_state.selected_minerals = ["Total Industry","Platinum Group Metal Ore","Coal And Lignite"]

def toggle_mineral(mineral):
    if mineral in st.session_state.selected_minerals:
        st.session_state.selected_minerals.remove(mineral)
    else:
        st.session_state.selected_minerals.append(mineral)

# Display buttons in columns
cols = st.sidebar.columns(2)
for i, mineral in enumerate(all_minerals):
    if i%2 == 0:
        if cols[0].button(mineral):
            toggle_mineral(mineral)
    else:
        if cols[1].button(mineral):
            toggle_mineral(mineral)

selected_minerals = st.session_state.selected_minerals

# ---------------------------
# FILTERED DATA
# ---------------------------
filtered_df = df[
    (df['Year'].between(selected_year[0], selected_year[1])) &
    (df['Mineral'].isin(selected_minerals)) &
    (df['Metric'] == selected_metric)
]

# ---------------------------
# PAGE FUNCTIONS
# ---------------------------
def executive_overview():
    st.header("📊 Executive Overview")
    
    # KPI Cards
    kpi_sales_2012 = df[(df['Metric']=='Sales Revenue') & (df['Year']==2012) & (df['Mineral']=='Total Industry')]['Value'].sum()
    kpi_sales_2022 = df[(df['Metric']=='Sales Revenue') & (df['Year']==2022) & (df['Mineral']=='Total Industry')]['Value'].sum()
    sales_growth = ((kpi_sales_2022 - kpi_sales_2012)/kpi_sales_2012*100) if kpi_sales_2012>0 else 0

    kpi_emp_2012 = df[(df['Metric']=='Employment (Persons)') & (df['Year']==2012) & (df['Mineral']=='Total Industry')]['Value'].sum()
    kpi_emp_2022 = df[(df['Metric']=='Employment (Persons)') & (df['Year']==2022) & (df['Mineral']=='Total Industry')]['Value'].sum()
    emp_change = ((kpi_emp_2022 - kpi_emp_2012)/kpi_emp_2012*100) if kpi_emp_2012>0 else 0

    sales_per_emp_2012 = kpi_sales_2012 / kpi_emp_2012 if kpi_emp_2012>0 else 0
    sales_per_emp_2022 = kpi_sales_2022 / kpi_emp_2022 if kpi_emp_2022>0 else 0

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Sales 2012", f"R{kpi_sales_2012:,.0f}")
    c2.metric("Sales 2022", f"R{kpi_sales_2022:,.0f}", f"{sales_growth:+.1f}%")
    c3.metric("Employment 2022", f"{int(kpi_emp_2022):,}", f"{emp_change:+.1f}%")
    c4.metric("Sales per Employee 2022", f"R{sales_per_emp_2022:,.0f}")

    st.markdown("---")
    st.markdown("### Total Sales, Income, Expenditure Trend")
    trend_df = df[df['Metric'].isin(['Sales Revenue','Total Income','Total Expenditure'])]
    trend_df = trend_df[trend_df['Mineral']=='Total Industry']
    fig = px.line(trend_df, x='Year', y='Value', color='Metric', markers=True)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Top Minerals Contribution to Sales (Stacked Column)")
    top_minerals_df = df[(df['Metric']=='Sales Revenue') & (df['Mineral']!='Total Industry')]
    top_minerals_df = top_minerals_df.groupby(['Year','Mineral'], as_index=False)['Value'].sum()
    fig2 = px.bar(top_minerals_df, x='Year', y='Value', color='Mineral', title="Top Minerals Sales Contribution", text='Value')
    st.plotly_chart(fig2, use_container_width=True)

def revenue_deep_dive():
    st.header("💰 Revenue Deep Dive")
    # Treemap
    rev_df = df[(df['Metric']=='Sales Revenue') & (df['Year']==2022)]
    fig = px.treemap(rev_df, path=['Mineral'], values='Value', title='2022 Revenue Share by Mineral', height=600)
    st.plotly_chart(fig, use_container_width=True)

def employment_productivity():
    st.header("👷 Employment & Productivity")
    emp_df = df[(df['Metric']=='Employment (Persons)') & (df['Mineral'].isin(selected_minerals))]
    fig = px.line(emp_df, x='Year', y='Value', color='Mineral', markers=True, title="Employment Trend by Mineral")
    st.plotly_chart(fig, use_container_width=True)

    # Sales per Employee
    merged = df_merged[df_merged['Mineral'].isin(selected_minerals)]
    fig2 = px.line(merged, x='Year', y='Sales_per_Employee', color='Mineral', markers=True, title="Sales per Employee")
    st.plotly_chart(fig2, use_container_width=True)

def costs_profitability():
    st.header("💹 Costs & Profitability")
    costs_df = df[df['Metric'].isin(['Total Expenditure','Salaries & Wages','Utilities'])]
    costs_df = costs_df[costs_df['Mineral'].isin(selected_minerals)]
    fig = px.bar(costs_df, x='Year', y='Value', color='Metric', barmode='stack', title="Expenditure Breakdown")
    st.plotly_chart(fig, use_container_width=True)

def provincial_view():
    st.header("📍 Provincial Sales Overview")
    st.markdown("Currently placeholder. Map visualization can be added if province data exists.")
    st.dataframe(filtered_df)

# ---------------------------
# PAGE DISPATCH
# ---------------------------
page_dict = {
    "Executive Overview": executive_overview,
    "Revenue Deep Dive": revenue_deep_dive,
    "Employment & Productivity": employment_productivity,
    "Costs & Profitability": costs_profitability,
    "Provincial View": provincial_view
}

page_dict[page]()
