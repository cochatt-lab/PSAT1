
import streamlit as st
import pandas as pd
from scipy.stats import sem, t
import plotly.graph_objects as go

st.title("Anonymous PSAT Scores Dashboard")

# Load data
df = pd.read_csv("Anonymous and Clean PSAT 8_9 with %.csv")

# Convert columns to numeric
df["Total Score (240-1440)"] = pd.to_numeric(df["Total Score (240-1440)"], errors='coerce')
df["Reading Writing Percentile"] = pd.to_numeric(df["Reading Writing Percentile"].replace({">99": 99}), errors='coerce')
df["Math Percentile"] = pd.to_numeric(df["Math Percentile"], errors='coerce')

# Customized benchmark logic
def classify_benchmark(rw, math):
    if rw >= 75 and math >= 70:
        return "Meets/Exceeds"
    elif rw >= 60 and math >= 60:
        return "Approaching"
    else:
        return "Not Yet Approaching"

df["Benchmark"] = df.apply(lambda row: classify_benchmark(row["Reading Writing Percentile"], row["Math Percentile"]), axis=1)

# Sidebar filters
class_years = sorted(df["Class of"].dropna().unique())
selected_years = st.sidebar.multiselect("Select Class Year(s):", class_years, default=class_years)
benchmarks = sorted(df["Benchmark"].dropna().unique())
selected_benchmarks = st.sidebar.multiselect("Select Benchmark Status:", benchmarks, default=benchmarks)

# Filter data
df_filtered = df[df["Class of"].isin(selected_years) & df["Benchmark"].isin(selected_benchmarks)]

# Function to calculate 95% confidence interval
def confidence_interval(series):
    n = series.count()
    if n < 2:
        return 0
    se = sem(series, nan_policy='omit')
    h = se * t.ppf((1 + 0.95) / 2., n-1)
    return h

# Group by class year and calculate mean and confidence interval
grouped = df_filtered.groupby("Class of").agg({
    "Total Score (240-1440)": ["mean", confidence_interval],
    "Reading Writing Percentile": ["mean", confidence_interval],
    "Math Percentile": ["mean", confidence_interval]
}).reset_index()

# Flatten MultiIndex columns
grouped.columns = ["Class of", "Total Score Mean", "Total Score CI",
                   "RW Percentile Mean", "RW Percentile CI",
                   "Math Percentile Mean", "Math Percentile CI"]

# Display table
st.subheader("Summary Table")
st.dataframe(grouped)

# Create figure with secondary y-axis
fig = go.Figure()
fig.add_trace(go.Bar(
    x=grouped["Class of"],
    y=grouped["Total Score Mean"],
    name="Average Total Score",
    error_y=dict(type='data', array=grouped["Total Score CI"]),
    yaxis="y1"
))
fig.add_trace(go.Bar(
    x=grouped["Class of"],
    y=grouped["RW Percentile Mean"],
    name="Average RW Percentile",
    error_y=dict(type='data', array=grouped["RW Percentile CI"]),
    yaxis="y2"
))
fig.add_trace(go.Bar(
    x=grouped["Class of"],
    y=grouped["Math Percentile Mean"],
    name="Average Math Percentile",
    error_y=dict(type='data', array=grouped["Math Percentile CI"]),
    yaxis="y2"
))

fig.update_layout(
    title="Anonymous PSAT Scores and Percentiles by Class Year with 95% Confidence Intervals",
    xaxis_title="Class Year",
    yaxis=dict(title="Average Total Score", side="left", tickformat=".0f"),
    yaxis2=dict(title="Average Percentile", overlaying="y", side="right"),
    barmode="group"
)

st.plotly_chart(fig)
