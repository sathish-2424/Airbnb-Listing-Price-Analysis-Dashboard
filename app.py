from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


DATA_PATH = Path(__file__).with_name("airbnb_listings.csv")

PRICE_BINS = [0, 100, 200, 300, 450, float("inf")]
PRICE_LABELS = ["Under $100", "$100-$199", "$200-$299", "$300-$449", "$450+"]


st.set_page_config(
    page_title="Airbnb Listing Price Analysis Dashboard",
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

    data = data.dropna(subset=["price", "minimum_nights", "availability_365"]).copy()
    data["reviews_per_month"] = data["reviews_per_month"].fillna(0)
    data["price_band"] = pd.cut(
        data["price"],
        bins=PRICE_BINS,
        labels=PRICE_LABELS,
        include_lowest=True,
    )
    return data


def format_money(value: float) -> str:
    if pd.isna(value):
        return "$0"
    return f"${value:,.0f}"


def sidebar_filters(data: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.title("Dashboard Filters")
    st.sidebar.caption("Refine the listings used in every metric and chart.")

    boroughs = sorted(data["neighbourhood_group"].dropna().unique())
    selected_boroughs = st.sidebar.multiselect(
        "Neighborhood group",
        boroughs,
        default=boroughs,
    )

    neighbourhood_options = sorted(
        data.loc[
            data["neighbourhood_group"].isin(selected_boroughs), "neighbourhood"
        ]
        .dropna()
        .unique()
    )
    selected_neighbourhoods = st.sidebar.multiselect(
        "Neighborhood",
        neighbourhood_options,
        default=neighbourhood_options,
    )

    room_types = sorted(data["room_type"].dropna().unique())
    selected_room_types = st.sidebar.multiselect(
        "Room type",
        room_types,
        default=room_types,
    )

    min_price = int(data["price"].min())
    max_price = int(data["price"].max())
    selected_price = st.sidebar.slider(
        "Nightly price",
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


def render_metrics(data: pd.DataFrame) -> None:
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Listings", f"{len(data):,}")
    col2.metric("Median price", format_money(data["price"].median()))
    col3.metric("Average price", format_money(data["price"].mean()))
    col4.metric("Avg reviews", f"{data['number_of_reviews'].mean():.1f}")
    col5.metric("Avg availability", f"{data['availability_365'].mean():.0f} days")


def render_price_analysis(data: pd.DataFrame) -> None:
    borough_price = (
        data.groupby("neighbourhood_group", observed=False)
        .agg(
            average_price=("price", "mean"),
            median_price=("price", "median"),
            listings=("id", "count"),
        )
        .reset_index()
        .sort_values("average_price", ascending=False)
    )

    room_price = (
        data.groupby("room_type", observed=False)
        .agg(average_price=("price", "mean"), listings=("id", "count"))
        .reset_index()
        .sort_values("average_price", ascending=False)
    )

    price_band = (
        data.groupby(["price_band", "room_type"], observed=False)
        .size()
        .reset_index(name="listings")
    )

    col1, col2 = st.columns((1.15, 1))

    with col1:
        fig = px.bar(
            borough_price,
            x="neighbourhood_group",
            y="average_price",
            color="neighbourhood_group",
            text=borough_price["average_price"].map(format_money),
            hover_data={"median_price": ":$.0f", "listings": ":,"},
            title="Average Price by Neighborhood Group",
            labels={
                "neighbourhood_group": "Neighborhood group",
                "average_price": "Average price",
                "median_price": "Median price",
                "listings": "Listings",
            },
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False, yaxis_tickprefix="$")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            room_price,
            x="room_type",
            y="average_price",
            color="room_type",
            text=room_price["average_price"].map(format_money),
            hover_data={"listings": ":,"},
            title="Average Price by Room Type",
            labels={"room_type": "Room type", "average_price": "Average price"},
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(showlegend=False, yaxis_tickprefix="$")
        st.plotly_chart(fig, use_container_width=True)

    fig = px.bar(
        price_band,
        x="price_band",
        y="listings",
        color="room_type",
        barmode="group",
        title="Listings by Price Band and Room Type",
        labels={
            "price_band": "Price band",
            "listings": "Listings",
            "room_type": "Room type",
        },
    )
    st.plotly_chart(fig, use_container_width=True)


def render_availability_analysis(data: pd.DataFrame) -> None:
    availability = (
        data.groupby("neighbourhood_group", observed=False)
        .agg(
            average_availability=("availability_365", "mean"),
            median_minimum_nights=("minimum_nights", "median"),
            listings=("id", "count"),
        )
        .reset_index()
        .sort_values("average_availability", ascending=False)
    )

    fig = px.scatter(
        availability,
        x="average_availability",
        y="median_minimum_nights",
        size="listings",
        color="neighbourhood_group",
        hover_name="neighbourhood_group",
        title="Availability vs. Minimum-Night Requirements",
        labels={
            "average_availability": "Average availability in days",
            "median_minimum_nights": "Median minimum nights",
            "listings": "Listings",
            "neighbourhood_group": "Neighborhood group",
        },
    )
    st.plotly_chart(fig, use_container_width=True)


def render_geographic_distribution(data: pd.DataFrame) -> None:
    neighbourhoods = (
        data.groupby(["neighbourhood_group", "neighbourhood"], observed=False)
        .agg(
            listings=("id", "count"),
            average_price=("price", "mean"),
            median_price=("price", "median"),
            average_availability=("availability_365", "mean"),
        )
        .reset_index()
        .sort_values("listings", ascending=False)
    )

    top_neighbourhoods = neighbourhoods.head(15)
    col1, col2 = st.columns((1, 1.1))

    with col1:
        fig = px.bar(
            top_neighbourhoods.sort_values("listings"),
            x="listings",
            y="neighbourhood",
            color="neighbourhood_group",
            orientation="h",
            title="Top Neighborhoods by Listing Count",
            hover_data={"average_price": ":$.0f", "average_availability": ":.0f"},
            labels={
                "listings": "Listings",
                "neighbourhood": "Neighborhood",
                "neighbourhood_group": "Neighborhood group",
                "average_price": "Average price",
                "average_availability": "Average availability",
            },
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.treemap(
            neighbourhoods,
            path=["neighbourhood_group", "neighbourhood"],
            values="listings",
            color="average_price",
            color_continuous_scale="Blues",
            title="Geographic Distribution by Neighborhood",
            hover_data={"average_price": ":$.0f", "median_price": ":$.0f"},
            labels={
                "listings": "Listings",
                "average_price": "Average price",
                "median_price": "Median price",
            },
        )
        st.plotly_chart(fig, use_container_width=True)


def render_listing_explorer(data: pd.DataFrame) -> None:
    st.subheader("Listing Explorer")
    st.caption("Sort and scan the listings behind the current filter selection.")

    table = data[
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
    ].sort_values("price", ascending=False)

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "price": st.column_config.NumberColumn("Price", format="$%d"),
            "minimum_nights": "Minimum nights",
            "number_of_reviews": "Reviews",
            "reviews_per_month": st.column_config.NumberColumn(
                "Reviews/month",
                format="%.2f",
            ),
            "availability_365": "Availability",
            "neighbourhood_group": "Neighborhood group",
            "room_type": "Room type",
        },
    )


def main() -> None:
    st.title("Airbnb Listing Price Analysis Dashboard")

    if not DATA_PATH.exists():
        st.error(f"Dataset not found: {DATA_PATH.name}")
        st.stop()

    data = load_data(DATA_PATH)
    filtered = sidebar_filters(data)

    if filtered.empty:
        st.warning("No listings match the selected filters.")
        st.stop()

    render_metrics(filtered)

    st.divider()
    st.subheader("Pricing Patterns")
    render_price_analysis(filtered)

    st.divider()
    st.subheader("Availability Trends")
    render_availability_analysis(filtered)

    st.divider()
    st.subheader("Neighborhood Distribution")
    render_geographic_distribution(filtered)

    st.divider()
    render_listing_explorer(filtered)


if __name__ == "__main__":
    main()
