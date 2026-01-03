import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="SA Mining Dashboard 2012-2022", layout="wide")
st.title("🇿🇦 South Africa Mining Industry Dashboard (2012–2022)")
st.markdown("Data from Stats SA • All values in current prices (R million)")

@st.cache_data
def load_data():
    # Load the raw sheet
    df = pd.read_excel("Mining industry from 2012 to 2022.xlsx", header=None)
    
    # Extract relevant rows: those with FISALES, FINC, FEMPTOT, etc.
    df = df[df[2].str.startswith(('FISALES', 'FINC', 'FEMP', 'FEXP'), na=False)].copy()
    
    # Clean column names based on your file structure
    df.columns = ['report', 'industry', 'code', 'mineral', 'sic', 'country', 'prices', 'unit', 'start', 'end', 
                  '2012', '2015', '2019', '2022']
    
    # Keep only needed columns
    df = df[['code', 'mineral', '2012', '2015', '2019', '2022']].copy()
    
    # Extract metric and commodity
    df['metric'] = df['code'].str.extract(r'(F\w+)')[0]
    df['commodity'] = df['code'].str.extract(r'\d+([A-Za-z0-9]+)')[0]
    
    # Melt to long format
    df_long = df.melt(id_vars=['metric', 'commodity', 'mineral'], 
                      value_vars=['2012', '2015', '2019', '2022'],
                      var_name='year', value_name='value')
    df_long['year'] = df_long['year'].astype(int)
    df_long['value'] = pd.to_numeric(df_long['value'], errors='coerce')
    
    # Clean mineral names
    df_long['mineral'] = df_long['mineral'].str.replace('Mining of ', '').str.strip()
    df_long.loc[df_long['mineral'].str.contains('All', na=False), 'mineral'] = 'Total Industry'
    
    # Metric mapping
    metric_map = {
        'FISALES': 'Sales Revenue',
        'FINC': 'Total Income',
        'FEXP': 'Total Expenditure',
        'FEMPTOT': 'Employment (Persons)'
    }
    df_long['metric_name'] = df_long['metric'].map(metric_map).fillna('Other')
    
    return df_long

df = load_data()

# Sidebar
st.sidebar.header("Explore the Data")
metric = st.sidebar.selectbox("Choose Metric", 
                              ['Sales Revenue', 'Total Income', 'Total Expenditure', 'Employment (Persons)'])

minerals = sorted(df[df['metric_name'] == metric]['mineral'].unique())
selected_minerals = st.sidebar.multiselect("Select Minerals", minerals, 
                                           default=['Total Industry', 'platinum group metal ore', 'coal and lignite'])

year = st.sidebar.selectbox("Snapshot Year", [2022, 2019, 2015, 2012], index=0)

# Filter
filtered = df[(df['metric_name'] == metric) & 
              (df['mineral'].isin(selected_minerals))]

# Charts
col1, col2 = st.columns(2)

with col1:
    # Bar chart for selected year
    bar_data = df[(df['metric_name'] == metric) & (df['year'] == year)].nlargest(12, 'value')
    fig_bar = px.bar(bar_data, x='mineral', y='value', title=f"{metric} in {year}",
                     color='value', text='value')
    fig_bar.update_traces(texttemplate='R%{text:,.0f}M', textposition='outside')
    fig_bar.update_layout(xaxis_tickangle=45, showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    # Line trend for selected minerals
    if len(selected_minerals) > 0:
        line_data = filtered
        fig_line = px.line(line_data, x='year', y='value', color='mineral', markers=True,
                           title="Trend Over Time")
        fig_line.update_traces(textposition='top center')
        st.plotly_chart(fig_line, use_container_width=True)

# Key highlights
st.markdown("### Key Insights (2012 → 2022)")
sales_2012 = df[(df['metric_name']=='Sales Revenue') & (df['year']==2012) & (df['mineral']=='Total Industry')]['value'].iloc[0]
sales_2022 = df[(df['metric_name']=='Sales Revenue') & (df['year']==2022) & (df['mineral']=='Total Industry')]['value'].iloc[0]
growth = ((sales_2022 - sales_2012) / sales_2012) * 100

emp_2012 = df[(df['metric_name']=='Employment (Persons)') & (df['year']==2012) & (df['mineral']=='Total Industry')]['value'].iloc[0]
emp_2022 = df[(df['metric_name']=='Employment (Persons)') & (df['year']==2022) & (df['mineral']=='Total Industry')]['value'].iloc[0]
emp_change = ((emp_2022 - emp_2012) / emp_2012) * 100

c1, c2, c3, c4 = st.columns(4)
c1.metric("Sales 2012", f"R{sales_2012:,.0f}M")
c2.metric("Sales 2022", f"R{sales_2022:,.0f}M", f"+{growth:.0f}%")
c3.metric("Jobs 2012", f"{emp_2012:,}")
c4.metric("Jobs 2022", f"{emp_2022:,}", f"{emp_change:+.0f}%")

st.success("Dashboard deployed successfully! Share this link with anyone.")
