import streamlit as st
import pandas as pd
import plotly.express as px

# -------------------------------
# PAGE CONFIG (POWER BI FEEL)
# -------------------------------
st.set_page_config(
    page_title="SA Mining Executive Dashboard",
    page_icon="⛏️",
    layout="wide"
)

# -------------------------------
# LOAD DATA
# -------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("sa_mining_data.csv")

    # Ensure correct dtypes
    df["Year"] = df["Year"].astype(int)
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

    return df.dropna()

df = load_data()

# -------------------------------
# TOP CONTROL BAR (FILTERS)
# -------------------------------
st.markdown("## ⛏️ South Africa Mining Industry – Executive Overview")

with st.container():
    col1, col2, col3 = st.columns([2, 2, 4])

    with col1:
        year_range = st.slider(
            "Year Range",
            int(df["Year"].min()),
            int(df["Year"].max()),
            (int(df["Year"].min()), int(df["Year"].max()))
        )

    with col2:
        minerals = sorted(df["Mineral"].unique())
        selected_minerals = st.multiselect(
            "Minerals",
            minerals,
            default=minerals
        )

# -------------------------------
# APPLY FILTERS (GLOBAL)
# -------------------------------
filtered_df = df[
    (df["Year"].between(year_range[0], year_range[1])) &
    (df["Mineral"].isin(selected_minerals))
]

# -------------------------------
# KPI SECTION (POWER BI STYLE)
# -------------------------------
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric(
        "Total Production",
        f"{filtered_df['Value'].sum():,.0f}"
    )

with kpi2:
    st.metric(
        "Avg Annual Output",
        f"{filtered_df.groupby('Year')['Value'].sum().mean():,.0f}"
    )

with kpi3:
    st.metric(
        "Number of Minerals",
        filtered_df["Mineral"].nunique()
    )

with kpi4:
    st.metric(
        "Years Covered",
        filtered_df["Year"].nunique()
    )

st.divider()

# -------------------------------
# LINE CHART – TREND ANALYSIS
# -------------------------------
st.markdown("### 📈 Production Trend Over Time")

line_fig = px.line(
    filtered_df.groupby(["Year", "Mineral"], as_index=False)["Value"].sum(),
    x="Year",
    y="Value",
    color="Mineral",
    markers=True
)

line_fig.update_layout(
    height=420,
    legend_title_text="Mineral",
    margin=dict(l=20, r=20, t=40, b=20)
)

st.plotly_chart(line_fig, use_container_width=True)

# -------------------------------
# PIE + BAR (SIDE BY SIDE)
# -------------------------------
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### 🧩 Mineral Contribution Share")

    pie_fig = px.pie(
        filtered_df.groupby("Mineral", as_index=False)["Value"].sum(),
        names="Mineral",
        values="Value",
        hole=0.45
    )

    pie_fig.update_layout(height=400)
    st.plotly_chart(pie_fig, use_container_width=True)

with col_right:
    st.markdown("### 🏆 Top Minerals by Production")

    bar_fig = px.bar(
        filtered_df.groupby("Mineral", as_index=False)["Value"].sum()
        .sort_values("Value", ascending=False),
        x="Mineral",
        y="Value"
    )

    bar_fig.update_layout(height=400)
    st.plotly_chart(bar_fig, use_container_width=True)

# -------------------------------
# DRILL-DOWN TABLE
# -------------------------------
st.markdown("### 📋 Detailed Data View")

st.dataframe(
    filtered_df.sort_values(["Year", "Value"], ascending=[True, False]),
    use_container_width=True,
    height=350
)
