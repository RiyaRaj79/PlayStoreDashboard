"""
Google Play Store Dashboard - Streamlit Version
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
import pytz
import numpy as np

st.set_page_config(page_title="Play Store Dashboard", layout="wide", page_icon="📱")
st.title("📱 Google Play Store Dashboard")
st.markdown("Each chart is available only during its specific IST time window.")

def is_in_time_window(start_hour, end_hour):
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)
    return start_hour <= now.hour < end_hour

def show_time_blocked(start, end):
    st.warning(f"⏰ This chart is only available between {start}:00 IST and {end}:00 IST.")

@st.cache_data
def load_data():
    df = pd.read_csv("googleplaystore.csv")
    df["Installs"] = df["Installs"].astype(str).str.replace(r"[+,]", "", regex=True)
    df["Installs"] = pd.to_numeric(df["Installs"], errors="coerce")
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")
    df["Reviews"] = pd.to_numeric(df["Reviews"], errors="coerce")
    def parse_size(s):
        s = str(s).strip()
        if s.endswith("M"): return float(s[:-1])
        elif s.endswith("k"): return float(s[:-1]) / 1024
        return np.nan
    df["Size_MB"] = df["Size"].apply(parse_size)
    df["Price"] = df["Price"].astype(str).str.replace("$", "", regex=False)
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce").fillna(0)
    df["Last Updated"] = pd.to_datetime(df["Last Updated"], errors="coerce")
    df["Android_Ver_Num"] = df["Android Ver"].astype(str).str.extract(r"(\d+\.\d+|\d+)")[0]
    df["Android_Ver_Num"] = pd.to_numeric(df["Android_Ver_Num"], errors="coerce")
    df = df.dropna(subset=["Category", "Rating", "Installs"])
    df = df.drop_duplicates(subset=["App"])
    return df

@st.cache_data
def load_sentiment():
    return pd.read_csv("googleplaystore_user_reviews.csv")

df = load_data()
ist = pytz.timezone("Asia/Kolkata")
now = datetime.now(ist)

st.sidebar.markdown(f"### 🕐 Current IST Time: `{now.strftime('%H:%M')}`")
st.sidebar.markdown("---")
st.sidebar.markdown("""
**Chart Schedule:**
- Chart 1: 3 PM – 5 PM
- Chart 2: 6 PM – 8 PM
- Chart 3: 1 PM – 2 PM
- Chart 4: 6 PM – 9 PM
- Chart 5: 5 PM – 7 PM
- Chart 6: 4 PM – 6 PM
""")

# CHART 1
st.markdown("---")
st.subheader("📊 Chart 1: Avg Rating & Total Reviews — Top 10 Categories by Installs")
if is_in_time_window(15, 17):
    f1 = df[(df["Rating"] >= 4.0) & (df["Size_MB"] >= 10) & (df["Last Updated"].dt.month == 1)].copy()
    top10 = f1.groupby("Category")["Installs"].sum().nlargest(10).index.tolist()
    f1 = f1[f1["Category"].isin(top10)]
    agg1 = f1.groupby("Category").agg(Avg_Rating=("Rating","mean"), Total_Reviews=("Reviews","sum")).reset_index()
    fig1 = go.Figure(data=[
        go.Bar(name="Avg Rating", x=agg1["Category"], y=agg1["Avg_Rating"], marker_color="steelblue", yaxis="y1"),
        go.Bar(name="Total Reviews", x=agg1["Category"], y=agg1["Total_Reviews"], marker_color="coral", yaxis="y2")
    ])
    fig1.update_layout(barmode="group", xaxis=dict(title="Category", tickangle=30),
        yaxis=dict(title="Avg Rating", side="left"),
        yaxis2=dict(title="Total Reviews", overlaying="y", side="right"), height=500)
    st.plotly_chart(fig1, use_container_width=True)
else:
    show_time_blocked(15, 17)

# CHART 2
st.markdown("---")
st.subheader("🌍 Chart 2: Global Installs by Category (Top 5, Excl. A/C/G/S)")
if is_in_time_window(18, 20):
    f2 = df[~df["Category"].str.upper().str.startswith(("A","C","G","S"))].copy()
    top5 = f2.groupby("Category")["Installs"].sum().nlargest(5).index.tolist()
    f2 = f2[f2["Category"].isin(top5)]
    agg2 = f2.groupby("Category")["Installs"].sum().reset_index()
    cat_country = {"ENTERTAINMENT":"USA","EDUCATION":"IND","HEALTH_AND_FITNESS":"BRA",
        "FINANCE":"DEU","SHOPPING":"CHN","TRAVEL_AND_LOCAL":"AUS",
        "PHOTOGRAPHY":"FRA","PRODUCTIVITY":"GBR","DATING":"JPN","BEAUTY":"ZAF"}
    agg2["Country"] = agg2["Category"].map(cat_country).fillna("USA")
    fig2 = px.choropleth(agg2, locations="Country", locationmode="ISO-3", color="Installs",
        hover_name="Category", color_continuous_scale=px.colors.sequential.YlOrRd)
    hl2 = agg2[agg2["Installs"] > 1_000_000]
    fig2.add_scattergeo(locations=hl2["Country"], locationmode="ISO-3", mode="markers",
        marker=dict(size=14, color="blue", symbol="star"), name="Installs > 1M")
    fig2.update_layout(height=500)
    st.plotly_chart(fig2, use_container_width=True)
else:
    show_time_blocked(18, 20)

# CHART 3
st.markdown("---")
st.subheader("📈 Chart 3: Avg Installs & Revenue — Free vs Paid (Top 3 Categories)")
if is_in_time_window(13, 14):
    f3 = df[(df["Installs"] >= 10_000) & (df["Size_MB"] > 15) & (df["Android_Ver_Num"] > 4.0) &
            (df["Content Rating"] == "Everyone") & (df["App"].str.len() <= 30)].copy()
    f3["Revenue"] = f3["Price"] * f3["Installs"]
    f3 = f3[f3["Revenue"] >= 10_000]
    f3["App_Type"] = f3["Type"].apply(lambda x: "Free" if str(x).strip().upper() == "FREE" else "Paid")
    top3 = f3.groupby("Category")["Installs"].sum().nlargest(3).index.tolist()
    f3 = f3[f3["Category"].isin(top3)]
    agg3 = f3.groupby(["Category","App_Type"]).agg(Avg_Installs=("Installs","mean"), Avg_Revenue=("Revenue","mean")).reset_index()
    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
    colors3 = {"Free":"mediumseagreen","Paid":"tomato"}
    for at in ["Free","Paid"]:
        s = agg3[agg3["App_Type"] == at]
        fig3.add_trace(go.Bar(name=f"Avg Installs ({at})", x=s["Category"], y=s["Avg_Installs"],
            marker_color=colors3[at], opacity=0.8), secondary_y=False)
        fig3.add_trace(go.Scatter(name=f"Avg Revenue ({at})", x=s["Category"], y=s["Avg_Revenue"],
            mode="lines+markers", line=dict(color=colors3[at], dash="dot")), secondary_y=True)
    fig3.update_layout(barmode="group", xaxis_title="Category", height=500)
    fig3.update_yaxes(title_text="Avg Installs", secondary_y=False)
    fig3.update_yaxes(title_text="Avg Revenue ($)", secondary_y=True)
    st.plotly_chart(fig3, use_container_width=True)
else:
    show_time_blocked(13, 14)

# CHART 4
st.markdown("---")
st.subheader("📉 Chart 4: Total Installs Over Time by Category (E/C/B, Translated)")
if is_in_time_window(18, 21):
    T4 = {"BEAUTY":"सौंदर्य","BUSINESS":"வணிகம்","DATING":"Dating (Deutsch)"}
    f4 = df[(~df["App"].str.upper().str.startswith(("X","Y","Z"))) &
            (df["Category"].str.upper().str.startswith(("E","C","B"))) &
            (df["Reviews"] > 500) & (~df["App"].str.upper().str.contains("S"))].copy()
    f4["Month"] = f4["Last Updated"].dt.to_period("M").astype(str)
    f4 = f4.dropna(subset=["Month"])
    f4["Category_Display"] = f4["Category"].apply(lambda c: T4.get(c.upper(), c))
    agg4 = f4.groupby(["Month","Category_Display"])["Installs"].sum().reset_index().sort_values("Month")
    fig4 = go.Figure()
    for cat in agg4["Category_Display"].unique():
        s = agg4[agg4["Category_Display"] == cat].copy()
        s["MoM"] = s["Installs"].pct_change() * 100
        fig4.add_trace(go.Scatter(x=s["Month"], y=s["Installs"], mode="lines+markers", name=cat))
        for i in range(1, len(s)):
            if s["MoM"].iloc[i] > 20:
                fig4.add_vrect(x0=s["Month"].iloc[i-1], x1=s["Month"].iloc[i],
                    fillcolor="rgba(255,215,0,0.2)", layer="below", line_width=0)
    fig4.update_layout(xaxis_title="Month", yaxis_title="Total Installs", height=550, xaxis=dict(tickangle=45))
    st.plotly_chart(fig4, use_container_width=True)
else:
    show_time_blocked(18, 21)

# CHART 5
st.markdown("---")
st.subheader("🫧 Chart 5: App Size vs Rating (Bubble = Installs), Game highlighted Pink")
if is_in_time_window(17, 19):
    ALLOWED = ["GAME","BEAUTY","BUSINESS","COMICS","COMMUNICATION","DATING","ENTERTAINMENT","SOCIAL","EVENTS"]
    T5 = {"BEAUTY":"सौंदर्य","BUSINESS":"வணிகம்","DATING":"Dating (Deutsch)"}
    try:
        sent = load_sentiment()
        sagg = sent.groupby("App")["Sentiment_Subjectivity"].mean().reset_index()
        m5 = df.merge(sagg, on="App", how="left")
    except Exception:
        df["Sentiment_Subjectivity"] = 0.6
        m5 = df.copy()
    f5 = m5[(m5["Rating"] > 3.5) & (m5["Category"].str.upper().isin(ALLOWED)) &
            (m5["Reviews"] > 500) & (~m5["App"].str.upper().str.contains("S")) &
            (m5["Sentiment_Subjectivity"] > 0.5) & (m5["Installs"] > 50_000)].copy()
    f5["Category_Display"] = f5["Category"].apply(lambda c: T5.get(c.upper(), c))
    fig5 = go.Figure()
    for cat in f5["Category_Display"].unique():
        s = f5[f5["Category_Display"] == cat]
        orig = s["Category"].iloc[0].upper()
        color = "hotpink" if orig == "GAME" else None
        fig5.add_trace(go.Scatter(x=s["Size_MB"], y=s["Rating"], mode="markers", name=cat,
            marker=dict(size=np.log1p(s["Installs"])*2, color=color, opacity=0.7,
                        line=dict(width=0.5, color="white")),
            text=s["App"], hovertemplate="<b>%{text}</b><br>Size: %{x} MB<br>Rating: %{y}<extra></extra>"))
    fig5.update_layout(xaxis_title="Size (MB)", yaxis_title="Avg Rating", height=550)
    st.plotly_chart(fig5, use_container_width=True)
else:
    show_time_blocked(17, 19)

# CHART 6
st.markdown("---")
st.subheader("📐 Chart 6: Cumulative Installs Over Time — T & P Categories (Translated)")
if is_in_time_window(16, 18):
    T6 = {"TRAVEL_AND_LOCAL":"Voyage & Local","PRODUCTIVITY":"Productividad","PHOTOGRAPHY":"写真"}
    f6 = df[(df["Rating"] >= 4.2) & (~df["App"].str.contains(r"\d", regex=True)) &
            (df["Category"].str.upper().str.startswith(("T","P"))) &
            (df["Reviews"] > 1_000) & (df["Size_MB"].between(20, 80))].copy()
    f6["Month"] = f6["Last Updated"].dt.to_period("M").astype(str)
    f6 = f6.dropna(subset=["Month"])
    f6["Category_Display"] = f6["Category"].apply(lambda c: T6.get(c.upper(), c))
    agg6 = f6.groupby(["Month","Category_Display"])["Installs"].sum().reset_index().sort_values("Month")
    pivot6 = agg6.pivot(index="Month", columns="Category_Display", values="Installs").fillna(0)
    fig6 = go.Figure()
    colors6 = px.colors.qualitative.Set2
    for i, cat in enumerate(pivot6.columns):
        fig6.add_trace(go.Scatter(x=pivot6.index, y=pivot6[cat], mode="lines", name=cat,
            fill="tonexty" if i > 0 else "tozeroy",
            line=dict(color=colors6[i % len(colors6)], width=2), stackgroup="one"))
    fig6.update_layout(xaxis_title="Month", yaxis_title="Cumulative Installs",
                       height=550, xaxis=dict(tickangle=45))
    st.plotly_chart(fig6, use_container_width=True)
else:
    show_time_blocked(16, 18)
