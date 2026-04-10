"""
Google Play Store Dashboard - All 6 Chart Tasks
Requires: pandas, plotly, pytz
Install: pip install pandas plotly pytz
Dataset: googleplaystore.csv + googleplaystore_user_reviews.csv
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
import pytz
import re
import numpy as np

# ─────────────────────────────────────────────
# UTILITY: Check current IST time window
# ─────────────────────────────────────────────
def is_in_time_window(start_hour, end_hour):
    """Returns True if current IST time is within [start_hour, end_hour)."""
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    return start_hour <= now.hour < end_hour

def time_blocked_message(start, end):
    fig = go.Figure()
    fig.add_annotation(
        text=f"⏰ This chart is only available between {start}:00 IST and {end}:00 IST.",
        xref="paper", yref="paper", x=0.5, y=0.5,
        showarrow=False, font=dict(size=18, color="red"),
        align="center"
    )
    fig.update_layout(title="Chart Unavailable Outside Time Window", height=300)
    fig.show()

# ─────────────────────────────────────────────
# LOAD & CLEAN DATA
# ─────────────────────────────────────────────
def load_data():
    df = pd.read_csv("googleplaystore.csv")

    # Clean installs
    df["Installs"] = df["Installs"].astype(str).str.replace(r"[+,]", "", regex=True)
    df["Installs"] = pd.to_numeric(df["Installs"], errors="coerce")

    # Clean rating
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")

    # Clean reviews
    df["Reviews"] = pd.to_numeric(df["Reviews"], errors="coerce")

    # Clean size (convert M to float MB, ignore "Varies with device")
    def parse_size(s):
        s = str(s).strip()
        if s.endswith("M"):
            return float(s[:-1])
        elif s.endswith("k"):
            return float(s[:-1]) / 1024
        return np.nan
    df["Size_MB"] = df["Size"].apply(parse_size)

    # Clean price
    df["Price"] = df["Price"].astype(str).str.replace("$", "", regex=False)
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce").fillna(0)

    # Last Updated as datetime
    df["Last Updated"] = pd.to_datetime(df["Last Updated"], errors="coerce")

    # Android Version - extract numeric
    df["Android_Ver_Num"] = df["Android Ver"].astype(str).str.extract(r"(\d+\.\d+|\d+)")[0]
    df["Android_Ver_Num"] = pd.to_numeric(df["Android_Ver_Num"], errors="coerce")

    # Drop rows without key fields
    df = df.dropna(subset=["Category", "Rating", "Installs"])
    df = df.drop_duplicates(subset=["App"])

    return df

# ─────────────────────────────────────────────
# CHART 1: Grouped Bar Chart
# Time: 3 PM – 5 PM IST
# ─────────────────────────────────────────────
def chart1_grouped_bar(df):
    if not is_in_time_window(15, 17):
        time_blocked_message(15, 17)
        return

    # Filters
    filtered = df[
        (df["Rating"] >= 4.0) &
        (df["Size_MB"] >= 10) &
        (df["Last Updated"].dt.month == 1)
    ].copy()

    # Top 10 categories by installs
    top10 = (
        filtered.groupby("Category")["Installs"]
        .sum()
        .nlargest(10)
        .index.tolist()
    )
    filtered = filtered[filtered["Category"].isin(top10)]

    agg = filtered.groupby("Category").agg(
        Avg_Rating=("Rating", "mean"),
        Total_Reviews=("Reviews", "sum")
    ).reset_index()

    fig = go.Figure(data=[
        go.Bar(name="Avg Rating", x=agg["Category"], y=agg["Avg_Rating"],
               marker_color="steelblue", yaxis="y1"),
        go.Bar(name="Total Reviews", x=agg["Category"], y=agg["Total_Reviews"],
               marker_color="coral", yaxis="y2")
    ])

    fig.update_layout(
        title="📊 Chart 1: Avg Rating & Total Reviews — Top 10 Categories by Installs",
        barmode="group",
        xaxis=dict(title="Category", tickangle=30),
        yaxis=dict(title="Avg Rating", side="left"),
        yaxis2=dict(title="Total Reviews", overlaying="y", side="right"),
        legend=dict(x=0.01, y=0.99),
        height=550
    )
    fig.show()

# ─────────────────────────────────────────────
# CHART 2: Choropleth Map
# Time: 6 PM – 8 PM IST
# ─────────────────────────────────────────────
def chart2_choropleth(df):
    if not is_in_time_window(18, 20):
        time_blocked_message(18, 20)
        return

    # Exclude categories starting with A, C, G, S
    filtered = df[~df["Category"].str.upper().str.startswith(("A", "C", "G", "S"))].copy()

    # Top 5 categories by installs
    top5 = (
        filtered.groupby("Category")["Installs"]
        .sum()
        .nlargest(5)
        .index.tolist()
    )
    filtered = filtered[filtered["Category"].isin(top5)]

    # Aggregate installs per category
    agg = filtered.groupby("Category")["Installs"].sum().reset_index()
    agg["Highlight"] = agg["Installs"] > 1_000_000

    # Map categories to ISO country codes (simulated mapping for demo)
    category_country_map = {
        "ENTERTAINMENT": "USA",
        "EDUCATION": "IND",
        "HEALTH_AND_FITNESS": "BRA",
        "FINANCE": "DEU",
        "SHOPPING": "CHN",
        "TRAVEL_AND_LOCAL": "AUS",
        "PHOTOGRAPHY": "FRA",
        "PRODUCTIVITY": "GBR",
        "DATING": "JPN",
        "BEAUTY": "ZAF",
    }
    agg["Country"] = agg["Category"].map(category_country_map).fillna("USA")

    fig = px.choropleth(
        agg,
        locations="Country",
        locationmode="ISO-3",
        color="Installs",
        hover_name="Category",
        color_continuous_scale=px.colors.sequential.YlOrRd,
        title="🌍 Chart 2: Global Installs by Category (Top 5, Excl. A/C/G/S)",
    )

    # Highlight categories > 1M installs
    highlight = agg[agg["Installs"] > 1_000_000]
    fig.add_scattergeo(
        locations=highlight["Country"],
        locationmode="ISO-3",
        mode="markers",
        marker=dict(size=14, color="blue", symbol="star"),
        name="Installs > 1M"
    )

    fig.update_layout(height=550)
    fig.show()

# ─────────────────────────────────────────────
# CHART 3: Dual-Axis Chart (Free vs Paid)
# Time: 1 PM – 2 PM IST
# ─────────────────────────────────────────────
def chart3_dual_axis(df):
    if not is_in_time_window(13, 14):
        time_blocked_message(13, 14)
        return

    # Filters
    filtered = df[
        (df["Installs"] >= 10_000) &
        (df["Size_MB"] > 15) &
        (df["Android_Ver_Num"] > 4.0) &
        (df["Content Rating"] == "Everyone") &
        (df["App"].str.len() <= 30)
    ].copy()

    # Revenue estimate = Price * Installs
    filtered["Revenue"] = filtered["Price"] * filtered["Installs"]
    filtered = filtered[filtered["Revenue"] >= 10_000]

    filtered["App_Type"] = filtered["Type"].apply(
        lambda x: "Free" if str(x).strip().upper() == "FREE" else "Paid"
    )

    # Top 3 categories by total installs
    top3 = (
        filtered.groupby("Category")["Installs"]
        .sum()
        .nlargest(3)
        .index.tolist()
    )
    filtered = filtered[filtered["Category"].isin(top3)]

    agg = filtered.groupby(["Category", "App_Type"]).agg(
        Avg_Installs=("Installs", "mean"),
        Avg_Revenue=("Revenue", "mean")
    ).reset_index()

    categories = agg["Category"].unique().tolist()
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    colors = {"Free": "mediumseagreen", "Paid": "tomato"}
    for app_type in ["Free", "Paid"]:
        subset = agg[agg["App_Type"] == app_type]
        fig.add_trace(
            go.Bar(name=f"Avg Installs ({app_type})", x=subset["Category"],
                   y=subset["Avg_Installs"], marker_color=colors[app_type],
                   opacity=0.8),
            secondary_y=False
        )
        fig.add_trace(
            go.Scatter(name=f"Avg Revenue ({app_type})", x=subset["Category"],
                       y=subset["Avg_Revenue"], mode="lines+markers",
                       line=dict(color=colors[app_type], dash="dot")),
            secondary_y=True
        )

    fig.update_layout(
        title="📈 Chart 3: Avg Installs & Revenue — Free vs Paid (Top 3 Categories)",
        barmode="group",
        xaxis_title="Category",
        height=550
    )
    fig.update_yaxes(title_text="Avg Installs", secondary_y=False)
    fig.update_yaxes(title_text="Avg Revenue ($)", secondary_y=True)
    fig.show()

# ─────────────────────────────────────────────
# CHART 4: Time Series Line Chart
# Time: 6 PM – 9 PM IST
# ─────────────────────────────────────────────
def chart4_time_series(df):
    if not is_in_time_window(18, 21):
        time_blocked_message(18, 21)
        return

    TRANSLATIONS = {
        "BEAUTY": "सौंदर्य",       # Hindi
        "BUSINESS": "வணிகம்",      # Tamil
        "DATING": "Dating (Deutsch)"  # German
    }

    # Filters
    filtered = df[
        (~df["App"].str.upper().str.startswith(("X", "Y", "Z"))) &
        (df["Category"].str.upper().str.startswith(("E", "C", "B"))) &
        (df["Reviews"] > 500) &
        (~df["App"].str.upper().str.contains("S"))
    ].copy()

    filtered["Month"] = filtered["Last Updated"].dt.to_period("M").astype(str)
    filtered = filtered.dropna(subset=["Month"])

    # Translate category names
    filtered["Category_Display"] = filtered["Category"].apply(
        lambda c: TRANSLATIONS.get(c.upper(), c)
    )

    agg = filtered.groupby(["Month", "Category_Display"])["Installs"].sum().reset_index()
    agg = agg.sort_values("Month")

    fig = go.Figure()
    for cat in agg["Category_Display"].unique():
        subset = agg[agg["Category_Display"] == cat].copy()
        subset["MoM_Change"] = subset["Installs"].pct_change() * 100

        fig.add_trace(go.Scatter(
            x=subset["Month"], y=subset["Installs"],
            mode="lines+markers", name=cat
        ))

        # Shade areas where growth > 20% MoM
        for i in range(1, len(subset)):
            if subset["MoM_Change"].iloc[i] > 20:
                fig.add_vrect(
                    x0=subset["Month"].iloc[i - 1],
                    x1=subset["Month"].iloc[i],
                    fillcolor="rgba(255,215,0,0.2)",
                    layer="below", line_width=0
                )

    fig.update_layout(
        title="📉 Chart 4: Total Installs Over Time by Category (E/C/B, Translated)",
        xaxis_title="Month",
        yaxis_title="Total Installs",
        height=600,
        xaxis=dict(tickangle=45)
    )
    fig.show()

# ─────────────────────────────────────────────
# CHART 5: Bubble Chart
# Time: 5 PM – 7 PM IST
# ─────────────────────────────────────────────
def chart5_bubble(df):
    if not is_in_time_window(17, 19):
        time_blocked_message(17, 19)
        return

    ALLOWED_CATEGORIES = [
        "GAME", "BEAUTY", "BUSINESS", "COMICS", "COMMUNICATION",
        "DATING", "ENTERTAINMENT", "SOCIAL", "EVENTS"
    ]
    TRANSLATIONS = {
        "BEAUTY": "सौंदर्य",
        "BUSINESS": "வணிகம்",
        "DATING": "Dating (Deutsch)"
    }

    # Load sentiment data
    try:
        sentiment_df = pd.read_csv("googleplaystore_user_reviews.csv")
        sentiment_agg = sentiment_df.groupby("App")["Sentiment_Subjectivity"].mean().reset_index()
        merged = df.merge(sentiment_agg, on="App", how="left")
    except FileNotFoundError:
        print("⚠️  googleplaystore_user_reviews.csv not found. Skipping sentiment filter.")
        df["Sentiment_Subjectivity"] = 0.6  # default to pass filter
        merged = df.copy()

    # Filters
    filtered = merged[
        (merged["Rating"] > 3.5) &
        (merged["Category"].str.upper().isin(ALLOWED_CATEGORIES)) &
        (merged["Reviews"] > 500) &
        (~merged["App"].str.upper().str.contains("S")) &
        (merged["Sentiment_Subjectivity"] > 0.5) &
        (merged["Installs"] > 50_000)
    ].copy()

    filtered["Category_Display"] = filtered["Category"].apply(
        lambda c: TRANSLATIONS.get(c.upper(), c)
    )

    # Color: pink for GAME, others auto
    def get_color(cat):
        if cat.upper() == "GAME":
            return "hotpink"
        return None

    fig = go.Figure()
    for cat in filtered["Category_Display"].unique():
        subset = filtered[filtered["Category_Display"] == cat]
        orig_cat = subset["Category"].iloc[0].upper()
        color = "hotpink" if orig_cat == "GAME" else None
        fig.add_trace(go.Scatter(
            x=subset["Size_MB"],
            y=subset["Rating"],
            mode="markers",
            name=cat,
            marker=dict(
                size=np.log1p(subset["Installs"]) * 2,
                color=color,
                opacity=0.7,
                line=dict(width=0.5, color="white")
            ),
            text=subset["App"],
            hovertemplate="<b>%{text}</b><br>Size: %{x} MB<br>Rating: %{y}<extra></extra>"
        ))

    fig.update_layout(
        title="🫧 Chart 5: App Size vs Rating (Bubble = Installs), Game highlighted Pink",
        xaxis_title="Size (MB)",
        yaxis_title="Avg Rating",
        height=600
    )
    fig.show()

# ─────────────────────────────────────────────
# CHART 6: Stacked Area Chart
# Time: 4 PM – 6 PM IST
# ─────────────────────────────────────────────
def chart6_stacked_area(df):
    if not is_in_time_window(16, 18):
        time_blocked_message(16, 18)
        return

    TRANSLATIONS = {
        "TRAVEL_AND_LOCAL": "Voyage & Local",   # French
        "PRODUCTIVITY": "Productividad",         # Spanish
        "PHOTOGRAPHY": "写真"                    # Japanese
    }

    # Filters
    filtered = df[
        (df["Rating"] >= 4.2) &
        (~df["App"].str.contains(r"\d", regex=True)) &
        (df["Category"].str.upper().str.startswith(("T", "P"))) &
        (df["Reviews"] > 1_000) &
        (df["Size_MB"].between(20, 80))
    ].copy()

    filtered["Month"] = filtered["Last Updated"].dt.to_period("M").astype(str)
    filtered = filtered.dropna(subset=["Month"])

    filtered["Category_Display"] = filtered["Category"].apply(
        lambda c: TRANSLATIONS.get(c.upper(), c)
    )

    agg = filtered.groupby(["Month", "Category_Display"])["Installs"].sum().reset_index()
    agg = agg.sort_values("Month")

    pivot = agg.pivot(index="Month", columns="Category_Display", values="Installs").fillna(0)

    fig = go.Figure()
    colors = px.colors.qualitative.Set2

    for i, cat in enumerate(pivot.columns):
        series = pivot[cat]
        pct_change = series.pct_change() * 100

        # Boost color intensity for months with >25% MoM growth
        marker_colors = []
        for j, val in enumerate(pct_change):
            if pd.notna(val) and val > 25:
                marker_colors.append("rgba(255,50,50,0.9)")   # highlight
            else:
                marker_colors.append(colors[i % len(colors)])

        fig.add_trace(go.Scatter(
            x=pivot.index,
            y=series,
            mode="lines",
            name=cat,
            fill="tonexty" if i > 0 else "tozeroy",
            line=dict(color=colors[i % len(colors)], width=2),
            stackgroup="one"
        ))

    fig.update_layout(
        title="📐 Chart 6: Cumulative Installs Over Time — T & P Categories (Translated)",
        xaxis_title="Month",
        yaxis_title="Cumulative Installs",
        height=600,
        xaxis=dict(tickangle=45)
    )
    fig.show()

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("Loading data...")
    df = load_data()
    print(f"✅ Loaded {len(df)} rows\n")

    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    print(f"🕐 Current IST Time: {now.strftime('%H:%M')}\n")

    print("─── Chart 1: Grouped Bar Chart (3 PM – 5 PM IST) ───")
    chart1_grouped_bar(df)

    print("─── Chart 2: Choropleth Map (6 PM – 8 PM IST) ───")
    chart2_choropleth(df)

    print("─── Chart 3: Dual-Axis Chart (1 PM – 2 PM IST) ───")
    chart3_dual_axis(df)

    print("─── Chart 4: Time Series Line Chart (6 PM – 9 PM IST) ───")
    chart4_time_series(df)

    print("─── Chart 5: Bubble Chart (5 PM – 7 PM IST) ───")
    chart5_bubble(df)

    print("─── Chart 6: Stacked Area Chart (4 PM – 6 PM IST) ───")
    chart6_stacked_area(df)
