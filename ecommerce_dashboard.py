import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings("ignore")

# Configure Streamlit page
st.set_page_config(
    page_title="E-Commerce Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .section-header {
        font-size: 1.8rem;
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
        margin: 1.5rem 0;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    .stSelectbox > div > div {
        background-color: #f8f9fa;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    """Load and cache the e-commerce data with proper encoding handling"""

    def load_csv_with_encoding(filename):
        encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252", "utf-8-sig"]
        for encoding in encodings:
            try:
                return pd.read_csv(filename, encoding=encoding)
            except UnicodeDecodeError:
                continue
        raise Exception(f"Could not load {filename} with any encoding")

    try:
        # Load all datasets
        customer_dim = load_csv_with_encoding("customer_dim.csv")
        item_dim = load_csv_with_encoding("item_dim.csv")
        store_dim = load_csv_with_encoding("store_dim.csv")
        time_dim = load_csv_with_encoding("time_dim.csv")
        trans_dim = load_csv_with_encoding("Trans_dim.csv")
        fact_table = load_csv_with_encoding("fact_table.csv")

        # Data cleaning and preprocessing
        # Convert date column
        time_dim["date"] = pd.to_datetime(
            time_dim["date"], format="%d-%m-%Y %H:%M", errors="coerce"
        )

        # Clean item data
        item_dim["main_category"] = item_dim["desc"].apply(
            lambda x: (
                x.split(" - ")[0].strip()
                if pd.notna(x) and " - " in x
                else str(x).strip()
            )
        )

        # Handle missing values
        trans_dim["bank_name"] = trans_dim["bank_name"].replace("None", np.nan)

        # Create comprehensive dataset
        comprehensive_data = (
            fact_table.merge(
                customer_dim[["coustomer_key", "name"]], on="coustomer_key", how="left"
            )
            .merge(
                item_dim[
                    [
                        "item_key",
                        "item_name",
                        "main_category",
                        "man_country",
                        "supplier",
                    ]
                ],
                on="item_key",
                how="left",
            )
            .merge(store_dim, on="store_key", how="left")
            .merge(
                time_dim[["time_key", "date", "year", "month", "quarter"]],
                on="time_key",
                how="left",
            )
            .merge(trans_dim, on="payment_key", how="left")
        )

        # Add derived metrics
        comprehensive_data["profit_margin"] = (
            (
                comprehensive_data["total_price"]
                - (comprehensive_data["unit_price"] * 0.7)
            )
            / comprehensive_data["total_price"]
            * 100
        )
        comprehensive_data["month_name"] = pd.to_datetime(
            comprehensive_data["date"]
        ).dt.strftime("%B")
        comprehensive_data["weekday"] = pd.to_datetime(
            comprehensive_data["date"]
        ).dt.day_name()

        return {
            "comprehensive": comprehensive_data,
            "customer_dim": customer_dim,
            "item_dim": item_dim,
            "store_dim": store_dim,
            "time_dim": time_dim,
            "trans_dim": trans_dim,
            "fact_table": fact_table,
        }
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None


def create_kpi_metrics(data):
    """Create KPI metrics cards"""
    col1, col2, col3, col4, col5 = st.columns(5)

    total_revenue = data["total_price"].sum()
    total_orders = len(data)
    avg_order_value = data["total_price"].mean()
    total_customers = data["coustomer_key"].nunique()
    total_products = data["item_key"].nunique()

    with col1:
        st.markdown(
            f"""
        <div class="metric-card">
            <h3>💰 Total Revenue</h3>
            <h2>${total_revenue:,.0f}</h2>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
        <div class="metric-card">
            <h3>📦 Total Orders</h3>
            <h2>{total_orders:,}</h2>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
        <div class="metric-card">
            <h3>🛒 Avg Order Value</h3>
            <h2>${avg_order_value:.2f}</h2>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
        <div class="metric-card">
            <h3>👥 Total Customers</h3>
            <h2>{total_customers:,}</h2>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col5:
        st.markdown(
            f"""
        <div class="metric-card">
            <h3>🏷️ Products Sold</h3>
            <h2>{total_products:,}</h2>
        </div>
        """,
            unsafe_allow_html=True,
        )


def create_revenue_trends(data):
    """Create animated revenue trend charts"""
    st.markdown(
        '<p class="section-header">📈 Revenue Trends & Performance</p>',
        unsafe_allow_html=True,
    )

    # Monthly revenue trend with animation
    monthly_data = (
        data.groupby([data["date"].dt.to_period("M"), "division"])["total_price"]
        .sum()
        .reset_index()
    )
    monthly_data["date"] = monthly_data["date"].astype(str)
    monthly_data = monthly_data.sort_values("date")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Animated line chart
        fig_trend = px.line(
            monthly_data,
            x="date",
            y="total_price",
            color="division",
            title="Monthly Revenue Trends by Division",
            labels={"total_price": "Revenue ($)", "date": "Month"},
            template="plotly_white",
        )

        fig_trend.update_traces(
            mode="lines+markers", line=dict(width=3), marker=dict(size=8)
        )
        fig_trend.update_layout(
            height=400, title_font_size=20, showlegend=True, hovermode="x unified"
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with col2:
        # Revenue by quarter pie chart
        quarterly_revenue = data.groupby("quarter")["total_price"].sum().reset_index()
        fig_pie = px.pie(
            quarterly_revenue,
            values="total_price",
            names="quarter",
            title="Quarterly Revenue Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )

        fig_pie.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Revenue: $%{value:,.0f}<extra></extra>",
        )
        fig_pie.update_layout(height=400, title_font_size=16)
        st.plotly_chart(fig_pie, use_container_width=True)


def create_geographic_analysis(data):
    """Create geographic performance dashboard"""
    st.markdown(
        '<p class="section-header">🗺️ Geographic Performance Analysis</p>',
        unsafe_allow_html=True,
    )

    # Division performance
    division_stats = (
        data.groupby("division")
        .agg(
            {
                "total_price": ["sum", "mean"],
                "quantity": "sum",
                "coustomer_key": "nunique",
            }
        )
        .round(2)
    )
    division_stats.columns = [
        "Total Revenue",
        "Avg Order Value",
        "Total Quantity",
        "Unique Customers",
    ]
    division_stats = division_stats.reset_index()

    col1, col2 = st.columns(2)

    with col1:
        # Animated bar chart for divisions
        fig_div = px.bar(
            division_stats,
            x="division",
            y="Total Revenue",
            title="Revenue by Division",
            color="Total Revenue",
            color_continuous_scale="viridis",
            template="plotly_white",
        )

        fig_div.update_traces(texttemplate="$%{y:,.0f}", textposition="outside")
        fig_div.update_layout(height=400, showlegend=False, title_font_size=18)
        st.plotly_chart(fig_div, use_container_width=True)

    with col2:
        # Treemap for districts
        district_data = (
            data.groupby(["division", "district"])["total_price"].sum().reset_index()
        )
        fig_treemap = px.treemap(
            district_data,
            path=[px.Constant("Bangladesh"), "division", "district"],
            values="total_price",
            title="Revenue Distribution by Districts",
            color="total_price",
            color_continuous_scale="RdYlBu",
        )

        fig_treemap.update_layout(height=400, title_font_size=18)
        st.plotly_chart(fig_treemap, use_container_width=True)


def create_customer_analysis(data):
    """Create customer behavior analysis"""
    st.markdown(
        '<p class="section-header">👥 Customer Behavior Analytics</p>',
        unsafe_allow_html=True,
    )

    # Customer segmentation
    customer_metrics = (
        data.groupby("coustomer_key")
        .agg({"total_price": ["sum", "mean", "count"], "quantity": "sum"})
        .round(2)
    )
    customer_metrics.columns = [
        "Total Spent",
        "Avg Order Value",
        "Order Count",
        "Total Quantity",
    ]

    # Customer segmentation logic
    def segment_customers(row):
        if row["Order Count"] >= 5 and row["Total Spent"] >= customer_metrics[
            "Total Spent"
        ].quantile(0.75):
            return "VIP Customers"
        elif row["Order Count"] >= 3 and row["Total Spent"] >= customer_metrics[
            "Total Spent"
        ].quantile(0.50):
            return "Loyal Customers"
        elif row["Order Count"] >= 2:
            return "Regular Customers"
        else:
            return "One-time Buyers"

    customer_metrics["Segment"] = customer_metrics.apply(segment_customers, axis=1)

    col1, col2, col3 = st.columns(3)

    with col1:
        # Customer segments
        segment_counts = customer_metrics["Segment"].value_counts()
        fig_segments = px.pie(
            values=segment_counts.values,
            names=segment_counts.index,
            title="Customer Segmentation",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )

        fig_segments.update_traces(textposition="inside", textinfo="percent+label")
        fig_segments.update_layout(height=350, title_font_size=16)
        st.plotly_chart(fig_segments, use_container_width=True)

    with col2:
        # Order frequency distribution
        fig_freq = px.histogram(
            customer_metrics,
            x="Order Count",
            title="Order Frequency Distribution",
            nbins=20,
            color_discrete_sequence=["#FF6B6B"],
        )

        fig_freq.update_layout(height=350, title_font_size=16, showlegend=False)
        st.plotly_chart(fig_freq, use_container_width=True)

    with col3:
        # Customer value scatter
        fig_scatter = px.scatter(
            customer_metrics,
            x="Order Count",
            y="Total Spent",
            color="Segment",
            size="Avg Order Value",
            title="Customer Value Analysis",
            template="plotly_white",
        )

        fig_scatter.update_layout(height=350, title_font_size=16)
        st.plotly_chart(fig_scatter, use_container_width=True)


def create_product_analysis(data):
    """Create product performance analysis"""
    st.markdown(
        '<p class="section-header">🛍️ Product Performance Analytics</p>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        # Top categories by revenue
        category_revenue = (
            data.groupby("main_category")["total_price"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )

        fig_cat = px.bar(
            x=category_revenue.values,
            y=category_revenue.index,
            orientation="h",
            title="Top 10 Categories by Revenue",
            color=category_revenue.values,
            color_continuous_scale="viridis",
            template="plotly_white",
        )

        fig_cat.update_traces(texttemplate="$%{x:,.0f}", textposition="outside")
        fig_cat.update_layout(height=400, showlegend=False, title_font_size=18)
        st.plotly_chart(fig_cat, use_container_width=True)

    with col2:
        # Country performance
        country_data = (
            data.groupby("man_country")
            .agg({"total_price": "sum", "quantity": "sum"})
            .sort_values("total_price", ascending=False)
            .head(10)
            .reset_index()
        )

        fig_country = px.scatter(
            country_data,
            x="quantity",
            y="total_price",
            size="total_price",
            color="man_country",
            title="Product Performance by Manufacturing Country",
            hover_name="man_country",
            template="plotly_white",
        )

        fig_country.update_layout(height=400, title_font_size=18, showlegend=False)
        st.plotly_chart(fig_country, use_container_width=True)


def create_time_analysis(data):
    """Create time-based analysis"""
    st.markdown(
        '<p class="section-header">⏰ Temporal Analytics</p>', unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        # Weekday performance
        weekday_revenue = (
            data.groupby("weekday")["total_price"]
            .sum()
            .reindex(
                [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday",
                ]
            )
        )

        fig_weekday = px.bar(
            x=weekday_revenue.index,
            y=weekday_revenue.values,
            title="Revenue by Day of Week",
            color=weekday_revenue.values,
            color_continuous_scale="plasma",
            template="plotly_white",
        )

        fig_weekday.update_traces(texttemplate="$%{y:,.0f}", textposition="outside")
        fig_weekday.update_layout(height=400, showlegend=False, title_font_size=18)
        fig_weekday.update_xaxes(tickangle=45)
        st.plotly_chart(fig_weekday, use_container_width=True)

    with col2:
        # Hourly heatmap
        data["hour"] = pd.to_datetime(data["date"]).dt.hour
        hourly_data = (
            data.groupby(["weekday", "hour"])["total_price"].sum().reset_index()
        )

        # Pivot for heatmap
        heatmap_data = hourly_data.pivot(
            index="weekday", columns="hour", values="total_price"
        )
        heatmap_data = heatmap_data.reindex(
            [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
        )

        fig_heatmap = px.imshow(
            heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            color_continuous_scale="viridis",
            title="Revenue Heatmap: Day vs Hour",
            aspect="auto",
        )

        fig_heatmap.update_layout(height=400, title_font_size=18)
        fig_heatmap.update_xaxes(title="Hour of Day")
        fig_heatmap.update_yaxes(title="Day of Week")
        st.plotly_chart(fig_heatmap, use_container_width=True)


def create_payment_analysis(data):
    """Create payment method analysis"""
    st.markdown(
        '<p class="section-header">💳 Payment Analytics</p>', unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        # Payment method distribution
        payment_stats = (
            data.groupby("trans_type")
            .agg({"total_price": ["sum", "count", "mean"]})
            .round(2)
        )
        payment_stats.columns = [
            "Total Revenue",
            "Transaction Count",
            "Avg Transaction",
        ]
        payment_stats = payment_stats.reset_index()

        fig_payment = px.sunburst(
            payment_stats,
            path=["trans_type"],
            values="Total Revenue",
            title="Payment Method Revenue Distribution",
            color="Total Revenue",
            color_continuous_scale="viridis",
        )

        fig_payment.update_layout(height=400, title_font_size=18)
        st.plotly_chart(fig_payment, use_container_width=True)

    with col2:
        # Bank performance for card payments
        bank_data = data[data["trans_type"] == "card"].dropna(subset=["bank_name"])
        if not bank_data.empty:
            bank_revenue = (
                bank_data.groupby("bank_name")["total_price"]
                .sum()
                .sort_values(ascending=False)
                .head(8)
            )

            fig_bank = px.pie(
                values=bank_revenue.values,
                names=bank_revenue.index,
                title="Top Banks by Revenue (Card Payments)",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )

            fig_bank.update_traces(textposition="inside", textinfo="percent+label")
            fig_bank.update_layout(height=400, title_font_size=18)
            st.plotly_chart(fig_bank, use_container_width=True)


def main():
    # Main header
    st.markdown(
        '<h1 class="main-header">🚀 E-Commerce Analytics Dashboard</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="text-align: center; font-size: 1.2rem; color: #7f8c8d;">CEO Executive Summary & Business Intelligence</p>',
        unsafe_allow_html=True,
    )

    # Load data
    with st.spinner("Loading data... Please wait"):
        data_dict = load_data()

    if data_dict is None:
        st.error(
            "Failed to load data. Please check if all CSV files are in the correct directory."
        )
        return

    data = data_dict["comprehensive"]

    # Sidebar filters
    st.sidebar.image(
        "https://via.placeholder.com/300x100/667eea/ffffff?text=Analytics+Dashboard",
        use_column_width=True,
    )
    st.sidebar.markdown("## 🎛️ Dashboard Controls")

    # Date range filter
    date_range = st.sidebar.date_input(
        "Select Date Range",
        value=[data["date"].min().date(), data["date"].max().date()],
        min_value=data["date"].min().date(),
        max_value=data["date"].max().date(),
    )

    # Division filter
    divisions = st.sidebar.multiselect(
        "Select Divisions",
        options=data["division"].unique(),
        default=data["division"].unique(),
    )

    # Payment method filter
    payment_methods = st.sidebar.multiselect(
        "Select Payment Methods",
        options=data["trans_type"].unique(),
        default=data["trans_type"].unique(),
    )

    # Apply filters
    if len(date_range) == 2:
        data = data[
            (data["date"].dt.date >= date_range[0])
            & (data["date"].dt.date <= date_range[1])
        ]

    if divisions:
        data = data[data["division"].isin(divisions)]

    if payment_methods:
        data = data[data["trans_type"].isin(payment_methods)]

    # Display filtered data info
    st.sidebar.markdown(f"**Filtered Data:** {len(data):,} transactions")
    st.sidebar.markdown(
        f"**Date Range:** {data['date'].min().strftime('%Y-%m-%d')} to {data['date'].max().strftime('%Y-%m-%d')}"
    )

    # Main dashboard content
    if len(data) > 0:
        # KPI Metrics
        create_kpi_metrics(data)

        # Revenue trends
        create_revenue_trends(data)

        # Geographic analysis
        create_geographic_analysis(data)

        # Customer analysis
        create_customer_analysis(data)

        # Product analysis
        create_product_analysis(data)

        # Time analysis
        create_time_analysis(data)

        # Payment analysis
        create_payment_analysis(data)

        # Executive Summary
        st.markdown(
            '<p class="section-header">📋 Executive Summary</p>', unsafe_allow_html=True
        )

        summary_col1, summary_col2, summary_col3 = st.columns(3)

        with summary_col1:
            st.info(
                f"""
            **🎯 Key Insights:**
            • Total Revenue: ${data['total_price'].sum():,.0f}
            • Top Division: {data.groupby('division')['total_price'].sum().idxmax()}
            • Peak Sales Day: {data.groupby('weekday')['total_price'].sum().idxmax()}
            """
            )

        with summary_col2:
            top_category = data.groupby("main_category")["total_price"].sum().idxmax()
            best_customer_segment = (
                data.groupby("coustomer_key")["total_price"].sum().quantile(0.9)
            )
            st.success(
                f"""
            **📈 Growth Opportunities:**
            • Best Category: {top_category}
            • VIP Customer Threshold: ${best_customer_segment:,.0f}
            • Payment Preference: {data['trans_type'].mode()[0].title()}
            """
            )

        with summary_col3:
            st.warning(
                f"""
            **🔮 Recommendations:**
            • Focus on top-performing regions
            • Enhance customer loyalty programs
            • Optimize inventory for peak hours
            """
            )

    else:
        st.error(
            "No data available for the selected filters. Please adjust your selection."
        )


if __name__ == "__main__":
    main()
