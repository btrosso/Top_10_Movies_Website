import os
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['APP_SECRET_KEY']
Bootstrap(app)

# -----------------------API Variables/Functions--------------------#

movie_url = "https://api.themoviedb.org/3/search/movie"
search_params = {
    "api_key": os.environ['TMDB_API_KEY'],
    "language": 'en-US',
    "include_adult": 'false',
    "query": ''
}

def perform_search():
    response = requests.get(movie_url, params=search_params)
    response.raise_for_status()
    data = response.json()
    search_results = []
    for result in data['results']:
        search_results.append(
            {
                "id": result['id'],
                "title": result['title'],
                "release_date": result['release_date']
            }
        )
    return search_results


# --------------------------DB Set Up & Functions------------------------------#
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///top-movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(100))
    img_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f'<Book {self.title}>'


db.create_all()


# --------------------------Set Up Forms---------------------------#
class EditMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")


class AddMovieForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField(label='Submit')

# --------------------------Testing Code---------------------------#

# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
# db.session.add(new_movie)
# db.session.commit()
# -------------------------------------------------------------------#

@app.route("/", methods=['GET'])
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=['GET', 'POST'])
def edit():
    form = EditMovieForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        print(f"This is inside edit: {movie.rating}")
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form=form)


@app.route("/delete", methods=['GET', 'POST'])
def delete():
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=['GET', 'POST'])
def add():
    form = AddMovieForm()

    if form.validate_on_submit():
        title_to_search = form.title.data
        search_params["query"] = title_to_search
        search_results = perform_search()
        return render_template("select.html", choices=search_results)
    return render_template("add.html", form=form)

@app.route("/handle_selection", methods=['GET',' POST'])
def handle_selection():
    movie_id = request.args.get("id")
    if movie_id:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={os.environ['TMDB_API_KEY']}&language=en-US"
        response = requests.get(url)
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"https://www.themoviedb.org/t/p/original{data['poster_path']}",
            description=data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit", id=new_movie.id))

if __name__ == '__main__':
    app.run(debug=True)
