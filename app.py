from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


DATA_PATH = Path(__file__).with_name("airbnb_listings.csv")


st.set_page_config(
    page_title="Airbnb Listing Price Analysis",
    layout="wide",
)


@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    data = pd.read_csv(path)
    numeric_columns = [
        "price",
        "minimum_nights",
        "number_of_reviews",
        "reviews_per_month",
        "availability_365",
    ]
    for column in numeric_columns:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    data["price_band"] = pd.cut(
        data["price"],
        bins=[0, 100, 200, 300, 450, float("inf")],
        labels=["Under $100", "$100-$199", "$200-$299", "$300-$449", "$450+"],
        include_lowest=True,
    )
    return data.dropna(subset=["price"])


@st.cache_data
def make_summary(data: pd.DataFrame) -> pd.DataFrame:
    return (
        data.groupby(["neighbourhood_group", "neighbourhood"], observed=False)
        .agg(
            listings=("id", "count"),
            average_price=("price", "mean"),
            median_price=("price", "median"),
            average_reviews=("number_of_reviews", "mean"),
            average_availability=("availability_365", "mean"),
        )
        .reset_index()
        .sort_values(["listings", "average_price"], ascending=[False, False])
    )


def format_money(value: float) -> str:
    return f"${value:,.0f}"


def sidebar_filters(data: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")

    boroughs = sorted(data["neighbourhood_group"].unique())
    selected_boroughs = st.sidebar.multiselect(
        "Borough",
        boroughs,
        default=boroughs,
    )

    neighbourhood_options = sorted(
        data.loc[data["neighbourhood_group"].isin(selected_boroughs), "neighbourhood"].unique()
    )
    selected_neighbourhoods = st.sidebar.multiselect(
        "Neighbourhood",
        neighbourhood_options,
        default=neighbourhood_options,
    )

    room_types = sorted(data["room_type"].unique())
    selected_room_types = st.sidebar.multiselect(
        "Room type",
        room_types,
        default=room_types,
    )

    min_price, max_price = int(data["price"].min()), int(data["price"].max())
    selected_price = st.sidebar.slider(
        "Price range",
        min_value=min_price,
        max_value=max_price,
        value=(min_price, max_price),
        step=10,
    )

    min_nights = st.sidebar.slider(
        "Maximum minimum-night requirement",
        min_value=int(data["minimum_nights"].min()),
        max_value=int(data["minimum_nights"].max()),
        value=int(data["minimum_nights"].max()),
    )

    availability = st.sidebar.slider(
        "Minimum yearly availability",
        min_value=int(data["availability_365"].min()),
        max_value=int(data["availability_365"].max()),
        value=int(data["availability_365"].min()),
    )

    return data[
        data["neighbourhood_group"].isin(selected_boroughs)
        & data["neighbourhood"].isin(selected_neighbourhoods)
        & data["room_type"].isin(selected_room_types)
        & data["price"].between(selected_price[0], selected_price[1])
        & (data["minimum_nights"] <= min_nights)
        & (data["availability_365"] >= availability)
    ].copy()


def metric_row(data: pd.DataFrame) -> None:
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Listings", f"{len(data):,}")
    col2.metric("Median price", format_money(data["price"].median()))
    col3.metric("Average price", format_money(data["price"].mean()))
    col4.metric("Avg reviews", f"{data['number_of_reviews'].mean():.1f}")
    col5.metric("Avg availability", f"{data['availability_365'].mean():.0f} days")


def render_market_charts(data: pd.DataFrame) -> None:
    borough_price = (
        data.groupby("neighbourhood_group", observed=False)
        .agg(average_price=("price", "mean"), listings=("id", "count"))
        .reset_index()
        .sort_values("average_price", ascending=False)
    )
    room_mix = data["room_type"].value_counts().reset_index()
    room_mix.columns = ["room_type", "listings"]

    left, right = st.columns(2)
    with left:
        fig = px.bar(
            borough_price,
            x="neighbourhood_group",
            y="average_price",
            color="neighbourhood_group",
            text=borough_price["average_price"].map(format_money),
            title="Average price by borough",
            labels={"neighbourhood_group": "Borough", "average_price": "Average price"},
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False, yaxis_tickprefix="$")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        fig = px.pie(
            room_mix,
            names="room_type",
            values="listings",
            hole=0.45,
            title="Listing mix by room type",
        )
        st.plotly_chart(fig, use_container_width=True)


def render_price_analysis(data: pd.DataFrame) -> None:
    left, right = st.columns(2)
    with left:
        fig = px.histogram(
            data,
            x="price",
            color="room_type",
            nbins=40,
            marginal="box",
            title="Price distribution by room type",
            labels={"price": "Price", "room_type": "Room type"},
        )
        fig.update_layout(yaxis_title="Listings", xaxis_tickprefix="$")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        fig = px.box(
            data,
            x="neighbourhood_group",
            y="price",
            color="room_type",
            points=False,
            title="Price spread by borough and room type",
            labels={"neighbourhood_group": "Borough", "price": "Price"},
        )
        fig.update_layout(yaxis_tickprefix="$")
        st.plotly_chart(fig, use_container_width=True)


def render_neighbourhood_analysis(data: pd.DataFrame) -> None:
    max_neighbourhood_count = max(10, int(data["neighbourhood"].value_counts().max()))
    min_listings = st.slider(
        "Minimum listings required for neighbourhood ranking",
        min_value=10,
        max_value=max_neighbourhood_count,
        value=min(100, max_neighbourhood_count),
        step=10,
    )

    neighbourhood_summary = make_summary(data)
    ranked = neighbourhood_summary[neighbourhood_summary["listings"] >= min_listings]

    left, right = st.columns(2)
    with left:
        top_price = ranked.nlargest(15, "median_price").sort_values("median_price")
        fig = px.bar(
            top_price,
            x="median_price",
            y="neighbourhood",
            color="neighbourhood_group",
            orientation="h",
            title="Top neighbourhoods by median price",
            labels={"median_price": "Median price", "neighbourhood": "Neighbourhood"},
        )
        fig.update_layout(xaxis_tickprefix="$")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        top_supply = neighbourhood_summary.nlargest(15, "listings").sort_values("listings")
        fig = px.bar(
            top_supply,
            x="listings",
            y="neighbourhood",
            color="neighbourhood_group",
            orientation="h",
            title="Top neighbourhoods by listing count",
            labels={"listings": "Listings", "neighbourhood": "Neighbourhood"},
        )
        st.plotly_chart(fig, use_container_width=True)


def render_demand_analysis(data: pd.DataFrame) -> None:
    scatter_sample = data.sample(min(len(data), 5000), random_state=7)
    fig = px.scatter(
        scatter_sample,
        x="availability_365",
        y="price",
        color="room_type",
        size="number_of_reviews",
        hover_data=["name", "neighbourhood_group", "neighbourhood", "minimum_nights"],
        opacity=0.55,
        title="Price, availability, and review activity",
        labels={
            "availability_365": "Availability in next 365 days",
            "price": "Price",
            "number_of_reviews": "Reviews",
        },
    )
    fig.update_layout(yaxis_tickprefix="$")
    st.plotly_chart(fig, use_container_width=True)

    demand = (
        data.groupby(["neighbourhood_group", "room_type"], observed=False)
        .agg(
            listings=("id", "count"),
            median_price=("price", "median"),
            avg_reviews_per_month=("reviews_per_month", "mean"),
            avg_availability=("availability_365", "mean"),
        )
        .reset_index()
        .sort_values("avg_reviews_per_month", ascending=False)
    )
    st.dataframe(
        demand,
        use_container_width=True,
        hide_index=True,
        column_config={
            "median_price": st.column_config.NumberColumn("Median price", format="$%d"),
            "avg_reviews_per_month": st.column_config.NumberColumn("Avg reviews/month", format="%.2f"),
            "avg_availability": st.column_config.NumberColumn("Avg availability", format="%.0f days"),
        },
    )


def render_listing_table(data: pd.DataFrame) -> None:
    sort_column = st.selectbox(
        "Sort listings by",
        ["price", "number_of_reviews", "reviews_per_month", "availability_365", "minimum_nights"],
    )
    sort_order = st.radio("Sort order", ["Descending", "Ascending"], horizontal=True)

    table = data.sort_values(sort_column, ascending=sort_order == "Ascending")[
        [
            "name",
            "neighbourhood_group",
            "neighbourhood",
            "room_type",
            "price",
            "minimum_nights",
            "number_of_reviews",
            "reviews_per_month",
            "availability_365",
        ]
    ]
    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "price": st.column_config.NumberColumn("Price", format="$%d"),
            "reviews_per_month": st.column_config.NumberColumn("Reviews/month", format="%.2f"),
            "availability_365": st.column_config.NumberColumn("Availability", format="%d days"),
        },
    )


def main() -> None:
    st.title("Airbnb Listing Price Analysis")
    st.caption("Interactive analysis of pricing, supply, room types, review activity, and availability.")

    if not DATA_PATH.exists():
        st.error(f"Dataset not found: {DATA_PATH.name}")
        st.stop()

    data = load_data(DATA_PATH)
    filtered = sidebar_filters(data)

    if filtered.empty:
        st.warning("No listings match the selected filters.")
        st.stop()

    metric_row(filtered)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Market overview", "Price analysis", "Neighbourhoods", "Demand signals", "Listings"]
    )
    with tab1:
        render_market_charts(filtered)
    with tab2:
        render_price_analysis(filtered)
    with tab3:
        render_neighbourhood_analysis(filtered)
    with tab4:
        render_demand_analysis(filtered)
    with tab5:
        render_listing_table(filtered)


if __name__ == "__main__":
    main()
