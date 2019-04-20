from flask import Flask, session, redirect, render_template, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, SubmitField, TextAreaField, PasswordField, DateField
from wtforms.validators import DataRequired
from PIL import Image
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from random import sample
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///OnLib_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPPLOAD_FOLDER'] = 'static/files/'
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
db = SQLAlchemy(app)


class RegisterForm(FlaskForm):
    name = StringField('Имя пользователя', validators=[DataRequired()])
    content = TextAreaField('О себе', validators=[DataRequired()])
    submit = SubmitField('Добавить')


class LoginForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class AddBookForm(FlaskForm):
    title = StringField('Название книги', validators=[DataRequired()])
    author = StringField('Автор', validators=[DataRequired()])
    about = TextAreaField('О книге', validators=[DataRequired()])
    date = StringField('Дата ниписания(публикации)', validators=[DataRequired()])
    img = FileField('Обложка', validators=[FileRequired()])
    book = FileField('Загрузить книгу', validators=[FileRequired()])
    submit = SubmitField('Создать')


class Bookworm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(80), unique=False, nullable=False)
    surname = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), unique=False, nullable=False)

    def __repr__(self):
        return '<Bookworm {} {} {} {} {}>'.format(
            self.id, self.username, self.name, self.surname, self.password)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), unique=False, nullable=False)
    author = db.Column(db.String(120), unique=False, nullable=False)
    about = db.Column(db.String(1000), unique=False, nullable=False)
    date = db.Column(db.String(80), unique=False, nullable=False)
    img = db.Column(db.String(80), unique=True, nullable=False)
    book = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return '<Book {} {} {} {} {}>'.format(
            self.id, self.title, self.author, self.img, self.book)


def resize_image(image):
    im = Image.open('static/img/' + image)
    im = im.resize((286, 429), resample=0, box=None)
    im.save('static/img/' + image)


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Домашняя страница',
                           session=session,
                           Book=Book,
                           sample=sample)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            if Bookworm.query.filter_by(username=form.login.data).first().password == form.password.data:
                session['username'] = form.login.data
                session['id'] = Bookworm.query.filter_by(username=form.login.data).first().id
                return redirect('/index')
            else:
                return render_template('login.html', form=form, session=session, error='password')
        except Exception:
            return render_template('login.html', form=form, session=session, error='login')
    return render_template('login.html', form=form, session=session, error=False)


@app.route('/logout')
def logout():
    session.pop('username', 0)
    return redirect('/login')


@app.route('/profile')
def profile():
    return render_template('profile.html', session=session, admin=session['id'] == 1)


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    form = AddBookForm()
    if form.validate_on_submit():
        img_f = form.img.data
        img_name = form.title.data + form.author.data + form.date.data + '.' + secure_filename(img_f.filename).split('.')[-1]
        img_f.save('static/img/' + img_name)
        resize_image(img_name)
        book_f = form.book.data
        book_f_name = form.title.data + form.author.data + form.date.data + '.' + secure_filename(book_f.filename).split('.')[-1]
        book_f.save('static/files/' + book_f_name)
        book = Book(title=form.title.data,
                    author=form.author.data,
                    about=form.about.data,
                    date=form.date.data,
                    img=img_name,
                    book=book_f_name)
        db.session.add(book)
        db.session.commit()
        return redirect('/profile')
    return render_template('add_book.html', form=form, session=session)


'''@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Форма регистрации
    """
    form = RegisterForm()
    if form.validate_on_submit():
        # создать пользователя
        users = UsersModel(db.get_connection())
        if form.user_name.data in [u[1] for u in users.get_all()]:
            flash('Такой пользователь уже существует')
        else:
            users.insert(user_name=form.user_name.data, email=form.email.data,
                         password_hash=generate_password_hash(form.password_hash.data))
            # редирект на главную страницу
            return redirect(url_for('index'))
    return render_template("register.html", title='Регистрация пользователя', form=form)'''

if __name__ == '__main__':
    db.create_all()
    app.run(port=8080, host='127.0.0.1')
