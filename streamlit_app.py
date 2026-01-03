import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="SA Mining Dashboard 2012-2022", layout="wide")
st.title("🇿🇦 South Africa Mining Industry Dashboard (2012–2022)")
st.markdown("Data from Stats SA • All values in current prices (R million)")

@st.cache_data
def load_data():
    df = pd.read_excel("Mining industry from 2012 to 2022.xlsx", header=None)
    
    # Filter relevant rows based on code starting with key metrics
    mask = df[2].astype(str).str.startswith(('FISALES', 'FINC', 'FEXP', 'FEMPTOT', 'FEMP'))
    df = df[mask].copy()
    
    # Set columns based on your file structure
    df.columns = ['report', 'industry', 'code', 'mineral', 'sic', 'country', 'prices', 'unit', 'start', 'end', 
                  '2012', '2015', '2019', '2022'] + list(range(14, df.shape[1]))
    
    df = df[['code', 'mineral', '2012', '2015', '2019', '2022']].copy()
    df = df.dropna(subset=['code'])
    
    # Extract metric
    df['metric'] = df['code'].str.extract(r'(F\w+)')[0]
    
    # Melt to long
    df_long = df.melt(id_vars=['metric', 'mineral'], 
                      value_vars=['2012', '2015', '2019', '2022'],
                      var_name='year', value_name='value')
    df_long['year'] = df_long['year'].astype(int)
    df_long['value'] = pd.to_numeric(df_long['value'], errors='coerce')
    df_long = df_long.dropna(subset=['value'])
    
    # Clean mineral names
    df_long['mineral'] = df_long['mineral'].str.replace('Mining of ', '', regex=False).str.strip()
    df_long['mineral'] = df_long['mineral'].str.replace('(including alluvial diamonds)', '', regex=False).str.strip()
    df_long.loc[df_long['mineral'].str.contains('All', na=False), 'mineral'] = 'Total Industry'
    
    # Metric mapping
    metric_map = {
        'FISALES': 'Sales Revenue',
        'FINC': 'Total Income',
        'FEXP': 'Total Expenditure',
        'FEMPTOT': 'Employment (Persons)',
        'FEMP': 'Employment (Persons)'  # in case some are FEMP
    }
    df_long['metric_name'] = df_long['metric'].map(metric_map).fillna('Other')
    
    return df_long

df = load_data()

# Sidebar
st.sidebar.header("Explore the Data")
metric_options = sorted(df['metric_name'].unique())
selected_metric = st.sidebar.selectbox("Choose Metric", metric_options, index=0)

# Get available minerals for this metric
available_minerals = sorted(df[df['metric_name'] == selected_metric]['mineral'].unique())

# Safe defaults: include 'Total Industry' if exists, plus a few major ones if they are available
possible_defaults = ['Total Industry']
major_ones = ['platinum group metal ore', 'coal and lignite', 'gold and uranium ore', 'iron ore']
for m in major_ones:
    if m in available_minerals:
        possible_defaults.append(m)

default_minerals = possible_defaults[:4]  # limit to avoid too many

selected_minerals = st.sidebar.multiselect("Select Minerals (for trend line)", 
                                           available_minerals, 
                                           default=default_minerals)

selected_year = st.sidebar.selectbox("Snapshot Year for Bar Chart", [2022, 2019, 2015, 2012], index=0)

# Filtered data
filtered = df[(df['metric_name'] == selected_metric)]

# Bar chart: Top minerals in selected year
bar_data = filtered[filtered['year'] == selected_year].sort_values('value', ascending=False).head(12)
fig_bar = px.bar(bar_data, x='mineral', y='value', 
                 title=f"{selected_metric} by Mineral in {selected_year}",
                 color='value', text='value')
fig_bar.update_traces(texttemplate='R%{text:,.0f}M', textposition='outside')
fig_bar.update_layout(xaxis_tickangle=45, showlegend=False)
st.plotly_chart(fig_bar, use_container_width=True)

# Line chart: Trends for selected minerals
if selected_minerals:
    line_data = filtered[filtered['mineral'].isin(selected_minerals)]
    fig_line = px.line(line_data, x='year', y='value', color='mineral', markers=True,
                       title=f"{selected_metric} Trends Over Time")
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("Select at least one mineral to view trends.")

# Key Insights
st.markdown("### Key Insights (2012 → 2022)")
if 'Sales Revenue' in df['metric_name'].unique():
    sales_2012 = df[(df['metric_name']=='Sales Revenue') & (df['year']==2012) & (df['mineral']=='Total Industry')]['value'].sum()
    sales_2022 = df[(df['metric_name']=='Sales Revenue') & (df['year']==2022) & (df['mineral']=='Total Industry')]['value'].sum()
    growth = ((sales_2022 - sales_2012) / sales_2012) * 100 if sales_2012 > 0 else 0
else:
    sales_2012 = sales_2022 = growth = 0

if 'Employment (Persons)' in df['metric_name'].unique():
    emp_2012 = df[(df['metric_name']=='Employment (Persons)') & (df['year']==2012) & (df['mineral']=='Total Industry')]['value'].sum()
    emp_2022 = df[(df['metric_name']=='Employment (Persons)') & (df['year']==2022) & (df['mineral']=='Total Industry')]['value'].sum()
    emp_change = ((emp_2022 - emp_2012) / emp_2012) * 100 if emp_2012 > 0 else 0
else:
    emp_2012 = emp_2022 = emp_change = 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Sales 2012", f"R{sales_2012:,.0f}M")
col2.metric("Sales 2022", f"R{sales_2022:,.0f}M", delta=f"{growth:+.0f}%" if growth else None)
col3.metric("Jobs 2012", f"{int(emp_2012):,}")
col4.metric("Jobs 2022", f"{int(emp_2022):,}", delta=f"{emp_change:+.0f}%" if emp_change else None)

st.success("Dashboard fixed and ready! Refresh or redeploy if needed.")
