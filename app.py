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


def render_main_chart(data: pd.DataFrame) -> None:
    borough_price = (
        data.groupby("neighbourhood_group", observed=False)
        .agg(average_price=("price", "mean"), listings=("id", "count"))
        .reset_index()
        .sort_values("average_price", ascending=False)
    )

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

    render_main_chart(filtered)


if __name__ == "__main__":
    main()
