import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="Amazon Prime Dashboard", layout="wide")
st.title("Amazon Prime Video Analysis Dashboard")

# --- Load data from one or two CSV files ---
def load_combined_data():
    uploaded_files = st.sidebar.file_uploader("Upload one or two CSV files (e.g., titles.csv, credits.csv)", accept_multiple_files=True, type="csv")
    if not uploaded_files:
        st.warning("Please upload at least one CSV file.")
        return None

    if len(uploaded_files) == 1:
        df = pd.read_csv(uploaded_files[0])
    elif len(uploaded_files) == 2:
        df1 = pd.read_csv(uploaded_files[0])
        df2 = pd.read_csv(uploaded_files[1])
        common_cols = list(set(df1.columns).intersection(set(df2.columns)))
        if 'id' in common_cols:
            df = pd.merge(df1, df2, on='id', how='left')
        elif 'title' in common_cols:
            df = pd.merge(df1, df2, on='title', how='left')
        else:
            st.warning("No common column ('id' or 'title') found to merge. Using the first file only.")
            df = df1
    else:
        st.warning("Please upload only one or two CSV files.")
        return None

    return df

amazon_prime = load_combined_data()
if amazon_prime is None:
    st.stop()

# --- Sidebar Filters ---
if amazon_prime is not None:
    st.sidebar.header("Filter Content")

    # Filter by Type
    if 'type' in amazon_prime.columns:
        selected_types = st.sidebar.multiselect(
            "Select Content Type:",
            options=amazon_prime['type'].dropna().unique(),
            default=amazon_prime['type'].dropna().unique()
        )
    else:
        selected_types = []
        st.sidebar.info("No 'type' column found in uploaded file(s).")

    # Filter by Actor/Role (in 'cast')
    if 'role' in amazon_prime.columns:
        all_cast = amazon_prime['role'].dropna().astype(str).str.split(',').explode().str.strip().unique()
        selected_cast = st.sidebar.multiselect(
            "Filter by Actor/Role:",
            options=sorted(all_cast),
            default=[]
        )
    else:
        selected_cast = []
        st.sidebar.info("No 'cast' column found in uploaded file(s).")

    # Filter by Release Year
    if 'release_year' in amazon_prime.columns:
        years = amazon_prime['release_year'].dropna().astype(int).unique().tolist()
        selected_years = st.sidebar.multiselect(
            "Filter by Release Year:",
            options=sorted(years),
            default=sorted(years)
        )
    else:
        selected_years = []
        st.sidebar.info("No 'release_year' column found in uploaded file(s).")


# --- Apply Filters ---
filtered_df = amazon_prime[
    amazon_prime['type'].isin(selected_types) &
    amazon_prime['release_year'].isin(selected_years)
]

if selected_cast and 'cast' in amazon_prime.columns:
    filtered_df = filtered_df[filtered_df['cast'].fillna('').apply(
        lambda x: any(actor.strip() in x for actor in selected_cast)
    )]

# --- IMDb Votes vs Score Scatter Plot ---
st.subheader("IMDb Votes vs Score (Log Scale)")
fig1 = px.scatter(
    filtered_df,
    x='imdb_votes',
    y='imdb_score',
    log_x=True,
    title='IMDb Votes vs Score (log scale)',
    labels={'imdb_votes': 'Votes', 'imdb_score': 'Score'}
)
fig1.update_traces(marker=dict(size=10, color='#1f77b4', line=dict(width=1.5, color='gray'), opacity=0.85))
st.plotly_chart(fig1, use_container_width=True)

# --- Top 10 Most Popular Movies (TMDB Popularity) ---
st.subheader("Top 10 Most Popular Movies (TMDB)")
top_popular = filtered_df.dropna(subset=['tmdb_popularity']).drop_duplicates('title')
top_popular = top_popular[top_popular['type'].str.upper() == 'MOVIE']
top_popular = top_popular.sort_values(by='tmdb_popularity', ascending=False).head(10)
fig2 = px.bar(top_popular, x='tmdb_popularity', y='title', orientation='h', title='Top 10 Most Popular Movies',
              labels={'tmdb_popularity': 'Popularity', 'title': 'Title'}, text='tmdb_popularity')
fig2.update_layout(yaxis={'categoryorder': 'total ascending'})
st.plotly_chart(fig2, use_container_width=True)

# --- Top 10 Most Voted Titles (IMDb Votes) ---
st.subheader("Top 10 Most Voted Titles on IMDb")
top_voted = filtered_df.dropna(subset=['imdb_votes']).drop_duplicates('title')
top_voted = top_voted.sort_values(by='imdb_votes', ascending=False).head(10)
fig3 = px.bar(top_voted, x='imdb_votes', y='title', orientation='h',
              title='Top 10 Most Voted Titles', labels={'imdb_votes': 'Votes', 'title': 'Title'}, text='imdb_votes')
fig3.update_layout(yaxis={'categoryorder': 'total ascending'})
st.plotly_chart(fig3, use_container_width=True)

# --- Line Chart: Avg IMDb Score by Year (Movies) ---
st.subheader("Average IMDb Score by Year (Movies)")
amazon_filtered = filtered_df[(filtered_df['imdb_score'].notnull()) &
                               (filtered_df['type'].str.upper() == 'MOVIE')].copy()
amazon_filtered['release_year'] = pd.to_numeric(amazon_filtered['release_year'], errors='coerce')
amazon_filtered.dropna(subset=['release_year'], inplace=True)
ratings_by_year = amazon_filtered.groupby('release_year')['imdb_score'].mean().reset_index()
fig4, ax = plt.subplots(figsize=(10, 5))
sns.lineplot(data=ratings_by_year, x='release_year', y='imdb_score', marker='o', ax=ax, color='teal')
ax.set_title('Average IMDb Score by Year (Movies)')
ax.set_xlabel('Release Year')
ax.set_ylabel('Average IMDb Score')
ax.grid(True, linestyle='--', alpha=0.5)
st.pyplot(fig4)

# --- Heatmap: Avg IMDb Score by Genre ---
st.subheader("IMDb Score by Genre (Dropdown)")

def make_pivot(data):
    grouped = data.groupby(['genres'])['imdb_score'].mean().round(2)
    return grouped.reset_index().sort_values('imdb_score', ascending=False).head(15)

df = filtered_df[['type', 'genres', 'imdb_score']].dropna()
df['type'] = df['type'].str.upper().str.strip()
df['genres'] = df['genres'].astype(str).str.split(',')
df = df.explode('genres')
df['genres'] = df['genres'].str.strip()

heatmap_type = st.selectbox("Select Content Type", ["All", "MOVIE", "SHOW"], key="heatmap")

if heatmap_type == "All":
    data = make_pivot(df)
    x_val = ['All'] * len(data)
elif heatmap_type == "MOVIE":
    data = make_pivot(df[df['type'] == 'MOVIE'])
    x_val = ['Movie'] * len(data)
else:
    data = make_pivot(df[df['type'] == 'SHOW'])
    x_val = ['Show'] * len(data)

fig5 = go.Figure(data=go.Heatmap(
    z=data['imdb_score'],
    x=x_val,
    y=data['genres'],
    text=data['imdb_score'],
    texttemplate="%{text}",
    hovertemplate='Genre: %{y}<br>Avg IMDb Score: %{z}<extra></extra>',
    colorscale='Viridis',
    colorbar=dict(title='Score')
))
fig5.update_layout(title=f"Avg IMDb Score by Genre ({heatmap_type})",
                   xaxis_title="Content Type",
                   yaxis_title="Genre",
                   margin=dict(t=80, l=100, r=40, b=60))
st.plotly_chart(fig5, use_container_width=True)

# --- Pie Chart: Content Type Distribution ---
st.subheader("Distribution of Content Types")
type_counts = filtered_df['type'].value_counts().reset_index()
type_counts.columns = ['Type', 'Count']
fig6 = px.pie(type_counts, names='Type', values='Count', hole=0.4,
              title='Dominance of Content Types on Amazon Prime Video',
              color_discrete_sequence=px.colors.qualitative.Set3)
fig6.update_traces(textinfo='label+percent', textposition='inside')
st.plotly_chart(fig6, use_container_width=True)

# --- Bar Chart: Top Genres by Type (with dropdown) ---
st.subheader("Top Genres by Content Type")
amazon_genre = filtered_df[['type', 'genres']].dropna()
amazon_genre['type'] = amazon_genre['type'].str.upper().str.strip()
amazon_genre['genres'] = amazon_genre['genres'].astype(str)

def get_genre_counts(df, content_type=None):
    if content_type:
        df = df[df['type'] == content_type]
    genres = df['genres'].str.split(',').explode().str.strip()
    return genres.value_counts().head(10)

all_counts = get_genre_counts(amazon_genre)
movie_counts = get_genre_counts(amazon_genre, 'MOVIE')
show_counts = get_genre_counts(amazon_genre, 'SHOW')

fig7 = go.Figure()
fig7.add_trace(go.Bar(x=all_counts.index, y=all_counts.values, name='All', text=all_counts.values, textposition='auto'))
fig7.add_trace(go.Bar(x=movie_counts.index, y=movie_counts.values, name='Movies', visible=False, text=movie_counts.values, textposition='auto'))
fig7.add_trace(go.Bar(x=show_counts.index, y=show_counts.values, name='Shows', visible=False, text=show_counts.values, textposition='auto'))

fig7.update_layout(
    updatemenus=[
        dict(
            buttons=list([
                dict(label="All", method="update", args=[{"visible": [True, False, False]}, {"title": "Top Genres (All Content)"}]),
                dict(label="Movies", method="update", args=[{"visible": [False, True, False]}, {"title": "Top Genres in Movies"}]),
                dict(label="Shows", method="update", args=[{"visible": [False, False, True]}, {"title": "Top Genres in Shows"}]),
            ]),
            direction="down",
            showactive=True
        )
    ],
    title="Top Genres on Amazon Prime Video",
    xaxis_title="Genre",
    yaxis_title="Count",
    showlegend=False
)
st.plotly_chart(fig7, use_container_width=True)
