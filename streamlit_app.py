import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="SA Mining Industry Dashboard 2012-2022", layout="wide")
st.title("🇿🇦 South Africa Mining Industry Dashboard (2012–2022)")
st.markdown("Interactive view of Stats SA mining data • Current prices (R million or persons)")

@st.cache_data
def load_data():
    # Load raw Excel (no header row assumed for data)
    df_raw = pd.read_excel("Mining industry from 2012 to 2022.xlsx", header=None)
    
    # Data rows start from row 1; columns: 2 = code (metric+commodity), 3 = mineral name, 10=Y2012, 11=Y2015, 12=Y2019, 13=Y2022
    df = df_raw.iloc[1:].copy()
    df = df[[2, 3, 10, 11, 12, 13]].dropna(subset=[2])
    df.columns = ['code', 'mineral', '2012', '2015', '2019', '2022']
    
    # Extract metric from code (e.g., FISALES from FISALES21000)
    df['metric'] = df['code'].astype(str).str.extract(r'(F[A-Z]+)')[0]
    
    # Melt to long format
    df_long = df.melt(id_vars=['metric', 'mineral'], 
                      value_vars=['2012', '2015', '2019', '2022'],
                      var_name='year', value_name='value')
    df_long['year'] = df_long['year'].astype(int)
    df_long['value'] = pd.to_numeric(df_long['value'], errors='coerce')
    df_long = df_long.dropna(subset=['value'])
    
    # Clean mineral names
    df_long['mineral_clean'] = df_long['mineral'].astype(str).str.replace('Mining of ', '', regex=False).str.strip()
    df_long['mineral_clean'] = df_long['mineral_clean'].str.replace(r'\s*\(.*\)', '', regex=True).str.strip()
    df_long.loc[df_long['code'].astype(str).str.endswith('29999'), 'mineral_clean'] = 'Total Industry'
    
    # Map human-readable metric names
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

# Sidebar
st.sidebar.header("Filters")
available_metrics = sorted(df['metric_name'].unique())
selected_metric = st.sidebar.selectbox("Select Metric", available_metrics, index=available_metrics.index('Sales Revenue') if 'Sales Revenue' in available_metrics else 0)

# Minerals available for selected metric
minerals_list = sorted(df[df['metric_name'] == selected_metric]['mineral_clean'].unique())

# Dynamic safe defaults
default_minerals = ['Total Industry']
major = ['platinum group metal ore', 'coal and lignite', 'gold and uranium ore', 'iron ore', 'diamonds']
for m in major:
    if m in minerals_list and len(default_minerals) < 6:
        default_minerals.append(m)

selected_minerals = st.sidebar.multiselect(
    "Select Minerals for Trend",
    options=minerals_list,
    default=default_minerals
)

selected_year = st.sidebar.selectbox("Year for Bar Chart", [2022, 2019, 2015, 2012], index=0)

# Filter
filtered = df[df['metric_name'] == selected_metric]

# Bar chart
bar_data = filtered[filtered['year'] == selected_year].sort_values('value', ascending=False).head(15)
fig_bar = px.bar(bar_data, x='mineral_clean', y='value',
                 title=f"{selected_metric} in {selected_year}",
                 color='value', text='value')
fig_bar.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
fig_bar.update_layout(xaxis_tickangle=45, showlegend=False)
st.plotly_chart(fig_bar, use_container_width=True)

# Line chart
if selected_minerals:
    line_data = filtered[filtered['mineral_clean'].isin(selected_minerals)]
    fig_line = px.line(line_data, x='year', y='value', color='mineral_clean', markers=True,
                       title=f"{selected_metric} Trends")
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("Select minerals above to see trends.")

# Key highlights
st.markdown("### Key Highlights (2012 → 2022)")
sales_2012 = df[(df['metric_name']=='Sales Revenue') & (df['year']==2012) & (df['mineral_clean']=='Total Industry')]['value'].sum()
sales_2022 = df[(df['metric_name']=='Sales Revenue') & (df['year']==2022) & (df['mineral_clean']=='Total Industry')]['value'].sum()
sales_growth = ((sales_2022 - sales_2012) / sales_2012 * 100) if sales_2012 > 0 else 0

emp_2012 = df[(df['metric_name']=='Employment (Persons)') & (df['year']==2012) & (df['mineral_clean']=='Total Industry')]['value'].sum()
emp_2022 = df[(df['metric_name']=='Employment (Persons)') & (df['year']==2022) & (df['mineral_clean']=='Total Industry')]['value'].sum()
emp_change = ((emp_2022 - emp_2012) / emp_2012 * 100) if emp_2012 > 0 else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Sales 2012", f"R{sales_2012:,.0f}M")
c2.metric("Sales 2022", f"R{sales_2022:,.0f}M", f"{sales_growth:+.1f}%")
c3.metric("Employment 2012", f"{int(emp_2012):,}")
c4.metric("Employment 2022", f"{int(emp_2022):,}", f"{emp_change:+.1f}%")

st.success("Dashboard loaded successfully! Explore different metrics and minerals.")
