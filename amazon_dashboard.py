
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

# Page config
st.set_page_config(page_title="Amazon Movies & Shows Dashboard", layout="wide")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("amazon.csv")
    return df

df = load_data()

st.title("🎬 Amazon Movies & Shows Dashboard")

# Sidebar filters
st.sidebar.header("🔎 Filters")
min_year, max_year = int(df['release_year'].min()), int(df['release_year'].max())
year_range = st.sidebar.slider("Select Release Year Range", min_year, max_year, (2000, 2022))
content_type = st.sidebar.multiselect("Select Type", options=df['type'].dropna().unique(), default=['MOVIE', 'SHOW'])

# Filter data
filtered_df = df[
    (df['release_year'].between(year_range[0], year_range[1])) &
    (df['type'].isin(content_type))
]

# Row 1 - IMDb score over time & content type pie chart
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("IMDb Score Over Years")
    ratings_by_year = filtered_df.groupby('release_year')['imdb_score'].mean().reset_index()
    fig1, ax1 = plt.subplots()
    sns.lineplot(data=ratings_by_year, x='release_year', y='imdb_score', ax=ax1)
    ax1.set_title("Average IMDb Score by Year")
    ax1.set_xlabel("Release Year")
    ax1.set_ylabel("IMDb Score")
    st.pyplot(fig1)

with col2:
    st.subheader("Movies vs Shows")
    type_counts = filtered_df['type'].value_counts().reset_index()
    type_counts.columns = ['Type', 'Count']
    fig2 = px.pie(type_counts, names='Type', values='Count', title='Type Distribution')
    st.plotly_chart(fig2, use_container_width=True)

# Row 2 - Top 10 Popular Titles & IMDb Distribution
col3, col4 = st.columns(2)

with col3:
    st.subheader("Top 10 Most Popular Titles (TMDB)")
    top_popular = (
        filtered_df[['title', 'tmdb_popularity']]
        .dropna()
        .drop_duplicates('title')
        .sort_values(by='tmdb_popularity', ascending=False)
        .head(10)
    )
    fig3 = px.bar(top_popular, x='tmdb_popularity', y='title', orientation='h',
                  labels={'tmdb_popularity': 'Popularity', 'title': 'Title'})
    fig3.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("IMDb Score Distribution")
    fig4, ax4 = plt.subplots()
    sns.histplot(filtered_df['imdb_score'].dropna(), bins=20, kde=True, ax=ax4)
    ax4.set_title("Distribution of IMDb Scores")
    ax4.set_xlabel("Score")
    ax4.set_ylabel("Count")
    st.pyplot(fig4)

# Row 3 - Votes vs IMDb Score
st.subheader("IMDb Votes vs Score")
fig5 = px.scatter(filtered_df, x='imdb_votes', y='imdb_score', log_x=True,
                  title='IMDb Votes vs Score',
                  labels={'imdb_votes': 'Votes', 'imdb_score': 'Score'})
st.plotly_chart(fig5, use_container_width=True)

# Optional: Season distribution for shows
if "SHOW" in content_type:
    st.subheader("Show Season Count Distribution")
    show_df = filtered_df[(filtered_df['type'] == 'SHOW') & (filtered_df['seasons'].notnull())]
    fig6, ax6 = plt.subplots()
    sns.histplot(show_df['seasons'], bins=30, kde=True, ax=ax6)
    ax6.set_title("Season Count for Shows")
    ax6.set_xlabel("Seasons")
    ax6.set_ylabel("Count")
    st.pyplot(fig6)
