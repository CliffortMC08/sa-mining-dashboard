# ===============================
# DASHBOARD UI (POWER BI STYLE)
# ===============================

st.markdown("## Executive Overview")

# -------------------------------
# KPI STRIP
# -------------------------------
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric(
    label="Total Sales (2022)",
    value=f"R{sales_2022:,.0f}M",
    delta=f"{sales_growth:+.1f}% vs 2012"
)

kpi2.metric(
    label="Total Sales (2012)",
    value=f"R{sales_2012:,.0f}M"
)

kpi3.metric(
    label="Employment (2022)",
    value=f"{int(emp_2022):,}",
    delta=f"{emp_change:+.1f}% vs 2012"
)

kpi4.metric(
    label="Employment (2012)",
    value=f"{int(emp_2012):,}"
)

st.divider()

# -------------------------------
# TABS (Power BI style pages)
# -------------------------------
tab1, tab2, tab3 = st.tabs([
    "📊 Overview",
    "📈 Trends",
    "🧱 Mineral Breakdown"
])

# ===============================
# TAB 1: OVERVIEW
# ===============================
with tab1:
    st.subheader(f"{selected_metric} – Top Minerals ({selected_year})")

    bar_data = (
        filtered[filtered['year'] == selected_year]
        .sort_values('value', ascending=True)
        .tail(12)
    )

    fig_overview = px.bar(
        bar_data,
        x='value',
        y='mineral_clean',
        orientation='h',
        title=None,
        text='value'
    )

    fig_overview.update_traces(
        texttemplate='%{text:,.0f}',
        textposition='outside'
    )

    fig_overview.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10)
    )

    st.plotly_chart(fig_overview, use_container_width=True)

# ===============================
# TAB 2: TRENDS
# ===============================
with tab2:
    st.subheader(f"{selected_metric} Trends Over Time")

    if selected_minerals:
        trend_data = filtered[filtered['mineral_clean'].isin(selected_minerals)]

        fig_trends = px.line(
            trend_data,
            x='year',
            y='value',
            color='mineral_clean',
            markers=True
        )

        fig_trends.update_layout(
            xaxis_title="Year",
            yaxis_title=None,
            legend_title_text="Mineral",
            margin=dict(l=10, r=10, t=10, b=10)
        )

        st.plotly_chart(fig_trends, use_container_width=True)
    else:
        st.info("Select at least one mineral to view trends.")

# ===============================
# TAB 3: MINERAL BREAKDOWN
# ===============================
with tab3:
    st.subheader("Mineral Contribution Analysis")

    pivot = (
        filtered
        .pivot_table(
            index='mineral_clean',
            columns='year',
            values='value',
            aggfunc='sum'
        )
        .dropna()
        .sort_values(by=selected_year, ascending=False)
        .head(10)
    )

    st.dataframe(
        pivot.style.format("{:,.0f}"),
        use_container_width=True
    )

    st.caption(
        "Top 10 minerals by selected metric. Values shown across years for comparative analysis."
    )

st.success("Dashboard ready for executive analysis.")
