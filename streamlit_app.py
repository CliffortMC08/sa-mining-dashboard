import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="SA Mining Dashboard 2012-2022", layout="wide")
st.title("🇿🇦 South Africa Mining Industry Dashboard (2012–2022)")
st.markdown("Data from Stats SA • All values in current prices (R million or persons)")

@st.cache_data
def load_data():
    df_raw = pd.read_excel("Mining industry from 2012 to 2022.xlsx", header=None)
    
    # Filter rows for key metrics
    mask = df_raw[2].astype(str).str.startswith(('FISALES', 'FINC', 'FEXP', 'FEMPTOT'))
    df = df_raw[mask].copy()
    
    # Set columns properly
    df.columns = ['report', 'industry', 'code', 'mineral', 'sic', 'country', 'prices', 'unit', 
                  'start', 'end', '2012', '2015', '2019', '2022']
    
    # Keep relevant
    df = df[['code', 'mineral', '2012', '2015', '2019', '2022']].dropna(subset=['code'])
    
    # Extract metric prefix
    df['metric'] = df['code'].str.extract('(F[A-Z]+)')[0]
    
    # Melt years
    df_long = df.melt(id_vars=['metric', 'mineral'], 
                      value_vars=['2012', '2015', '2019', '2022'],
                      var_name='year', value_name='value')
    df_long['year'] = df_long['year'].astype(int)
    df_long['value'] = pd.to_numeric(df_long['value'], errors='coerce')
    df_long = df_long.dropna(subset=['value'])
    
    # Clean mineral names
    df_long['mineral_clean'] = df_long['mineral'].str.replace('Mining of ', '', regex=False).str.strip()
    df_long['mineral_clean'] = df_long['mineral_clean'].str.replace(r'\s*\(.*\)', '', regex=True).str.strip()
    df_long.loc[df_long['mineral'].str.contains('All', na=False), 'mineral_clean'] = 'Total Industry'
    
    # Map metrics
    metric_map = {
        'FISALES': 'Sales Revenue',
        'FINC': 'Total Income',
        'FEXP': 'Total Expenditure',
        'FEMPTOT': 'Employment (Persons)'
    }
    df_long['metric_name'] = df_long['metric'].map(metric_map).fillna('Other')
    
    return df_long

df = load_data()

# Sidebar filters
st.sidebar.header("Filters")
available_metrics = sorted(df['metric_name'].unique())
selected_metric = st.sidebar.selectbox("Choose Metric", available_metrics)

# Available minerals for the selected metric
minerals_list = sorted(df[df['metric_name'] == selected_metric]['mineral_clean'].unique())

# Safe defaults: Total + top major ones if available
default_list = ['Total Industry']
top_minerals = ['platinum group metal ore', 'coal and lignite', 'gold and uranium ore', 'iron ore']
for m in top_minerals:
    if m in minerals_list and len(default_list) < 5:
        default_list.append(m)

selected_minerals = st.sidebar.multiselect(
    "Select Minerals for Trend Line",
    options=minerals_list,
    default=default_list
)

selected_year = st.sidebar.selectbox("Year for Bar Chart", options=[2022, 2019, 2015, 2012], index=0)

# Filtered data
filtered_df = df[df['metric_name'] == selected_metric]

# Bar Chart: Top 12 in selected year
bar_df = filtered_df[filtered_df['year'] == selected_year].sort_values('value', ascending=False).head(12)
fig_bar = px.bar(bar_df, x='mineral_clean', y='value',
                 title=f"{selected_metric} by Mineral - {selected_year}",
                 labels={'mineral_clean': 'Mineral', 'value': selected_metric},
                 color='value', text='value')
fig_bar.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
fig_bar.update_layout(xaxis_tickangle=45, showlegend=False)
st.plotly_chart(fig_bar, use_container_width=True)

# Line Chart: Trends
if selected_minerals:
    line_df = filtered_df[filtered_df['mineral_clean'].isin(selected_minerals)]
    fig_line = px.line(line_df, x='year', y='value', color='mineral_clean', markers=True,
                       title=f"{selected_metric} Trends")
    fig_line.update_layout(legend_title="Mineral")
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("Select one or more minerals to view trends.")

# Key Stats
st.markdown("### Overall Industry Highlights (2012 → 2022)")

total_sales_2012 = df[(df['metric_name'] == 'Sales Revenue') & (df['year'] == 2012) & (df['mineral_clean'] == 'Total Industry')]['value'].sum()
total_sales_2022 = df[(df['metric_name'] == 'Sales Revenue') & (df['year'] == 2022) & (df['mineral_clean'] == 'Total Industry')]['value'].sum()
sales_growth = ((total_sales_2022 - total_sales_2012) / total_sales_2012 * 100) if total_sales_2012 else 0

total_emp_2012 = df[(df['metric_name'] == 'Employment (Persons)') & (df['year'] == 2012) & (df['mineral_clean'] == 'Total Industry')]['value'].sum()
total_emp_2022 = df[(df['metric_name'] == 'Employment (Persons)') & (df['year'] == 2022) & (df['mineral_clean'] == 'Total Industry')]['value'].sum()
emp_change = ((total_emp_2022 - total_emp_2012) / total_emp_2012 * 100) if total_emp_2012 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Sales 2012", f"R{total_sales_2012:,.0f}M")
col2.metric("Total Sales 2022", f"R{total_sales_2022:,.0f}M", f"{sales_growth:+.0f}%")
col3.metric("Employment 2012", f"{int(total_emp_2012):,}")
col4.metric("Employment 2022", f"{int(total_emp_2022):,}", f"{emp_change:+.0f}%")

st.success("Dashboard is now fully stable and interactive! Enjoy exploring the data.")
