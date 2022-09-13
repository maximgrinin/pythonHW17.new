# Импортируем необходимые классы и библиотеки
from flask import Flask, request
from flask_restx import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields

# Создаем экземпляр класса приложения и меняем конфигурационные настройки
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['RESTX_JSON'] = {'ensure_ascii': False, 'indent': 2}

# Создаем экземпляр БД
db = SQLAlchemy(app)

# Создаем API и неймспейсы
api = Api(app)
movies_ns = api.namespace('movies')
directors_ns = api.namespace('directors')
genres_ns = api.namespace('genres')


# Модель для фильмов
class Movie(db.Model):
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.String(255))
    trailer = db.Column(db.String(255))
    year = db.Column(db.Integer)
    rating = db.Column(db.Float)
    genre_id = db.Column(db.Integer, db.ForeignKey("genre.id"))
    genre = db.relationship("Genre")
    director_id = db.Column(db.Integer, db.ForeignKey("director.id"))
    director = db.relationship("Director")


# Модель для режиссеров
class Director(db.Model):
    __tablename__ = 'director'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


# Модель для жанров
class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


# Схема для сериализации Режиссера
class DirectorSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()


# Схема для сериализации Жанра
class GenreSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()


# Схема для сериализации Фильма
class MovieSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str()
    description = fields.Str()
    trailer = fields.Str()
    year = fields.Int()
    rating = fields.Float()
    genre = fields.Pluck(GenreSchema, 'name')
    director = fields.Pluck(DirectorSchema, 'name')


# Создаем экземпляры схем сериализации для одной и нескольких сущностей
movie_schema = MovieSchema()
movies_schema = MovieSchema(many=True)
genre_schema = GenreSchema()
genres_schema = GenreSchema(many=True)
director_schema = DirectorSchema()
directors_schema = DirectorSchema(many=True)


# Функции API для фильмов - /movies/
@movies_ns.route('/')
class MoviesView(Resource):
    def get(self):
        genre_id = request.args.get("genre_id")
        director_id = request.args.get("director_id")
        # Обрабатываем возможность получения жанра в параметрах запроса /movies/?genre_id=1
        # Обрабатываем возможность получения режиссера в параметрах запроса /movies/?director_id=1
        # Если никаких дополнительных параметров в запросе не получили - возвращаем все фильмы
        if genre_id and director_id:
            query_result = db.session.query(Movie).filter(Movie.genre_id == genre_id, Movie.director_id == director_id).all()
        elif genre_id:
            query_result = db.session.query(Movie).filter(Movie.genre_id == genre_id).all()
        elif director_id:
            query_result = db.session.query(Movie).filter(Movie.director_id == director_id).all()
        else:
            query_result = db.session.query(Movie).all()
        # Если результаты запроса - пустые - говорим что данные не найдены
        if not query_result:
            return f'Результаты запроса не найдены', 404
        return movies_schema.dump(query_result), 200

    def post(self):
        req_json = request.json
        if not req_json:
            return 'Ошибка при получении информации о новом фильме', 404
        new_movie = Movie(**req_json)
        db.session.add(new_movie)
        db.session.commit()
        return "", 201


# Функции API для единичного экземпляра - фильма - /movies/<int:uid>
@movies_ns.route('/<int:uid>')
class MovieView(Resource):
    def get(self, uid):
        try:
            movie = db.session.query(Movie).filter(Movie.id == uid).one()
            return movie_schema.dump(movie), 200
        except Exception as e:
            return f'Фильм по указанному id = {uid} не найден - {str(e)}', 404

    def put(self, uid):
        try:
            movie = db.session.query(Movie).filter(Movie.id == uid).one()
            req_json = request.json
            [setattr(movie, key, value) for key, value in req_json.items()]
            db.session.add(movie)
            db.session.commit()
            return "", 204
        except Exception as e:
            return f'Фильм по указанному id = {uid} не найден - {str(e)}', 404

    def patch(self, uid):
        try:
            movie = db.session.query(Movie).filter(Movie.id == uid).one()
            req_json = request.json
            [setattr(movie, key, value) for key, value in req_json.items()]
            db.session.add(movie)
            db.session.commit()
            return "", 204
        except Exception as e:
            return f'Фильм по указанному id = {uid} не найден - {str(e)}', 404

    def delete(self, uid):
        try:
            movie = db.session.query(Movie).filter(Movie.id == uid).one()
            db.session.delete(movie)
            db.session.commit()
        except Exception as e:
            return f'Фильм по указанному id = {uid} не найден - {str(e)}', 404


# Функции API для режиссеров - /directors/
@directors_ns.route('/')
class DirectorsView(Resource):
    def get(self):
        query_result = db.session.query(Director).all()
        # Если результаты запроса - пустые - говорим что данные не найдены
        if not query_result:
            return f'Результаты запроса не найдены', 404
        return directors_schema.dump(query_result), 200

    def post(self):
        req_json = request.json
        if not req_json:
            return 'Ошибка при получении информации о новом режиссере', 404
        new_director = Director(**req_json)
        db.session.add(new_director)
        db.session.commit()
        return "", 201


# Функции API для единичного экземпляра - режиссера - /directors/<int:uid>
@directors_ns.route('/<int:uid>')
class DirectorView(Resource):
    def get(self, uid):
        try:
            director = db.session.query(Director).filter(Director.id == uid).one()
            return director_schema.dump(director), 200
        except Exception as e:
            return f'Режиссер по указанному id = {uid} не найден - {str(e)}', 404

    def put(self, uid):
        try:
            director = db.session.query(Director).filter(Director.id == uid).one()
            req_json = request.json
            [setattr(director, key, value) for key, value in req_json.items()]
            db.session.add(director)
            db.session.commit()
            return "", 204
        except Exception as e:
            return f'Режиссер по указанному id = {uid} не найден - {str(e)}', 404

    def patch(self, uid):
        try:
            director = db.session.query(Director).filter(Director.id == uid).one()
            req_json = request.json
            [setattr(director, key, value) for key, value in req_json.items()]
            db.session.add(director)
            db.session.commit()
            return "", 204
        except Exception as e:
            return f'Режиссер по указанному id = {uid} не найден - {str(e)}', 404

    def delete(self, uid):
        try:
            director = db.session.query(Director).filter(Director.id == uid).one()
            db.session.delete(director)
            db.session.commit()
        except Exception as e:
            return f'Режиссер по указанному id = {uid} не найден - {str(e)}', 404


# Функции API для жанров - /genres/
@genres_ns.route('/')
class GenresView(Resource):
    def get(self):
        query_result = db.session.query(Genre).all()
        # Если результаты запроса - пустые - говорим что данные не найдены
        if not query_result:
            return f'Результаты запроса не найдены', 404
        return genres_schema.dump(query_result), 200

    def post(self):
        req_json = request.json
        if not req_json:
            return 'Ошибка при получении информации о новом жанре', 404
        new_genre = Genre(**req_json)
        db.session.add(new_genre)
        db.session.commit()
        return "", 201


# Функции API для единичного экземпляра - жанра - /directors/<int:uid>
@genres_ns.route('/<int:uid>')
class DirectorView(Resource):
    def get(self, uid):
        try:
            genre = db.session.query(Genre).filter(Genre.id == uid).one()
            return genre_schema.dump(genre), 200
        except Exception as e:
            return f'Жанр по указанному id = {uid} не найден - {str(e)}', 404

    def put(self, uid):
        try:
            genre = db.session.query(Genre).filter(Genre.id == uid).one()
            req_json = request.json
            [setattr(genre, key, value) for key, value in req_json.items()]
            db.session.add(genre)
            db.session.commit()
            return "", 204
        except Exception as e:
            return f'Жанр по указанному id = {uid} не найден - {str(e)}', 404

    def patch(self, uid):
        try:
            genre = db.session.query(Genre).filter(Genre.id == uid).one()
            req_json = request.json
            [setattr(genre, key, value) for key, value in req_json.items()]
            db.session.add(genre)
            db.session.commit()
            return "", 204
        except Exception as e:
            return f'Жанр по указанному id = {uid} не найден - {str(e)}', 404

    def delete(self, uid):
        try:
            genre = db.session.query(Genre).filter(Genre.id == uid).one()
            db.session.delete(genre)
            db.session.commit()
        except Exception as e:
            return f'Жанр по указанному id = {uid} не найден - {str(e)}', 404


if __name__ == '__main__':
    app.run(debug=True)
