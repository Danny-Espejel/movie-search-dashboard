import streamlit as st
import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore


st.set_page_config(
    page_title="Movie Search Dashboard",
    layout="wide"
)


@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate("firebase_key.json")
        firebase_admin.initialize_app(cred)

    return firestore.client()


@st.cache_data
def load_movies():
    db = init_firebase()
    docs = db.collection("movies").stream()

    movies = []

    for doc in docs:
        record = doc.to_dict()
        record["id"] = doc.id
        movies.append(record)

    return pd.DataFrame(movies)


def search_movies_by_name(df, search_text):
    if search_text.strip() == "":
        return pd.DataFrame()

    return df[df["name"].str.contains(search_text, case=False, na=False)]


def filter_movies_by_director(df, director):
    return df[df["director"] == director]


def insert_movie(company, director, genre, name):
    db = init_firebase()

    movie_data = {
        "company": company,
        "director": director,
        "genre": genre,
        "name": name
    }

    db.collection("movies").add(movie_data)


st.title("Movie Search Dashboard")
st.write("This application retrieves movie records from Firebase Firestore and allows users to search, filter, and insert movie records.")

df = load_movies()

st.sidebar.header("Dashboard Options")

show_all = st.sidebar.checkbox("Show all movies")

if show_all:
    st.header("All Movies")
    st.write(f"Total records: {len(df)}")
    st.dataframe(df[["name", "director", "genre", "company"]], use_container_width=True)


st.sidebar.subheader("Search Movies by Title")

search_text = st.sidebar.text_input("Enter movie title")
search_button = st.sidebar.button("Search by Title")

if search_button:
    search_results = search_movies_by_name(df, search_text)

    st.header("Search Results")
    st.write(f"Total movies found: {len(search_results)}")

    if len(search_results) > 0:
        st.dataframe(search_results[["name", "director", "genre", "company"]], use_container_width=True)
    else:
        st.info("No movies found with the entered title.")


st.sidebar.subheader("Filter Movies by Director")

directors = sorted(df["director"].dropna().unique())

selected_director = st.sidebar.selectbox("Select a director", directors)
filter_button = st.sidebar.button("Filter by Director")

if filter_button:
    director_results = filter_movies_by_director(df, selected_director)

    st.header("Movies by Selected Director")
    st.write(f"Director: {selected_director}")
    st.write(f"Total movies found: {len(director_results)}")

    st.dataframe(director_results[["name", "director", "genre", "company"]], use_container_width=True)


st.sidebar.subheader("Insert New Movie")

with st.sidebar.form("insert_movie_form"):
    new_name = st.text_input("Movie title")
    new_director = st.text_input("Director")
    new_genre = st.text_input("Genre")
    new_company = st.text_input("Company")

    submitted = st.form_submit_button("Insert Movie")

    if submitted:
        if new_name.strip() == "" or new_director.strip() == "":
            st.error("Movie title and director are required.")
        else:
            insert_movie(
                company=new_company,
                director=new_director,
                genre=new_genre,
                name=new_name
            )

            st.success("Movie inserted successfully.")
            st.cache_data.clear()