from flask import Flask, request, jsonify, render_template
import pickle
import pandas as pd
import logging
import traceback
import difflib
import os

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# Load data
movies_dict = pickle.load(open('movie_dict.pkl','rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl','rb'))

# prepare titles list
titles = movies['title'].astype(str).tolist()

def find_movie_index(title: str):
    """Return index for exact (case-insensitive) match, else return None."""
    title_norm = title.strip().lower()
    for idx, t in enumerate(titles):
        if t.strip().lower() == title_norm:
            return idx
    return None

def recommend(movie: str):
    idx = find_movie_index(movie)
    if idx is None:
        return None
    distances = similarity[idx]
    top = sorted(list(enumerate(distances)), key=lambda x: x[1], reverse=True)[1:6]
    out = []
    for i, _score in top:
        row = movies.iloc[i]
        out.append({
            "title": str(row.title),
            # keep placeholder or integrate TMDB poster here if you like
            "poster": "https://via.placeholder.com/300x450"
        })
    return out

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/recommend", methods=["GET"])
def recommend_api():
    movie = request.args.get("movie", "")
    if not movie:
        return jsonify({"error": "Missing 'movie' parameter"}), 400

    try:
        results = recommend(movie)
        if results is None:
            # Suggest close matches using difflib
            suggestions = difflib.get_close_matches(movie, titles, n=5, cutoff=0.5)
            return jsonify({"error": "Movie not found", "suggestions": suggestions}), 404
        return jsonify(results)
    except Exception as e:
        logging.exception("Unexpected error in /recommend")
        tb = traceback.format_exc()
        # Return minimal error info to frontend; avoid leaking sensitive data in production
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

if __name__ == "__main__":
    # Ensure we're running from project root
    logging.info("Starting Flask app. CWD: %s", os.getcwd())
    app.run(debug=True)
