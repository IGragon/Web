from flask import Flask, session, redirect, render_template, flash, url_for, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, SubmitField, TextAreaField, PasswordField, DateField, BooleanField
from wtforms.validators import DataRequired, Email, Length
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
    username = StringField('Имя', validators=[DataRequired(), Length(1, 120)])
    name = StringField('Настоящее имя', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(4, 120)])
    about = TextAreaField('О себе', validators=[DataRequired(), Length(1, 1000)])
    submit = SubmitField('Присоединиться!')


class LoginForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class AddBookForm(FlaskForm):
    title = StringField('Название книги', validators=[DataRequired(), Length(1, 120)])
    author = StringField('Автор', validators=[DataRequired()])
    about = TextAreaField('О книги', validators=[DataRequired(), Length(100, 1000)])
    date = StringField('Дата ниписания(публикации)', validators=[DataRequired()])
    img = FileField('Обложка', validators=[FileRequired()])
    book = FileField('Загрузить книгу', validators=[FileRequired()])
    check = BooleanField('Я проверил все поля', validators=[DataRequired()])
    submit = SubmitField('Создать')


class AddBookToFavourite(FlaskForm):
    submit = SubmitField('')


class Bookworm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(80), unique=False, nullable=False)
    surname = db.Column(db.String(80), unique=False, nullable=False)
    about = db.Column(db.String(1000), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), unique=False, nullable=False)
    favourite_books = db.Column(db.String(1000), unique=False, nullable=True)

    def __repr__(self):
        return '<Bookworm {} {} {} {} {}>'.format(
            self.id, self.username, self.name, self.surname, self.password)


class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), unique=True, nullable=False)
    author = db.Column(db.String(120), unique=False, nullable=False)
    about = db.Column(db.String(1000), unique=False, nullable=False)
    date = db.Column(db.String(80), unique=False, nullable=False)
    img = db.Column(db.String(80), unique=True, nullable=False)
    book = db.Column(db.String(200), unique=True, nullable=False)

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
    n = 3 if len(Book.query.all()) >= 3 else len(Book.query.all())
    return render_template('index.html',
                           title='Домашняя страница',
                           session=session,
                           Book=Book,
                           sample=sample,
                           n=n,
                           len=len,
                           none=None)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'id' in session:
        return redirect('/index')
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user_password = Bookworm.query.filter_by(username=form.login.data).first().password
            password = form.password.data
            if check_password_hash(user_password, password):
                session['username'] = form.login.data
                session['id'] = Bookworm.query.filter_by(username=form.login.data).first().id
                return redirect('/index')
            else:
                return render_template('login.html',
                                       form=form,
                                       session=session,
                                       error='password')
        except Exception:
            return render_template('login.html',
                                   form=form,
                                   session=session,
                                   error='login')
    return render_template('login.html',
                           form=form,
                           session=session,
                           error=False)


@app.route('/logout')
def logout():
    if 'id' not in session:
        return redirect('/index')
    session.pop('username', 0)
    session.pop('id', 0)
    return redirect('/login')


@app.route('/profile')
def profile():
    if 'id' not in session:
        return redirect('/index')
    user = Bookworm.query.filter_by(username=session['username']).first()
    books = list(map(lambda x: Book.query.filter_by(id=x).first(), map(int, user.favourite_books.split())))
    print(books)
    return render_template('profile.html',
                           session=session,
                           admin=session['id'] == 1,
                           user=user,
                           books=books,
                           len=len)


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'id' not in session:
        return redirect('/index')
    if session['id'] != 1:
        return redirect('/index')
    form = AddBookForm()
    if form.validate_on_submit():
        img_f = form.img.data
        img_name = form.title.data + form.author.data + form.date.data + '.' + \
                   secure_filename(img_f.filename).split('.')[-1]
        img_f.save('static/img/' + img_name)
        resize_image(img_name)
        book_f = form.book.data
        book_f_name = form.title.data + form.author.data + form.date.data + '.' + \
                      secure_filename(book_f.filename).split('.')[-1]
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
    return render_template('add_book.html',
                           form=form,
                           session=session,
                           title='Добавление книги')


@app.route('/del_book', methods=['GET', 'POST'])
def del_book():
    if 'id' not in session:
        return redirect('/index')
    if session['id'] != 1:
        return redirect('/index')
    if request.method == 'GET':
        return render_template('delete_book.html',
                               Book=Book,
                               title='Удаление книги',
                               session=session)
    book_title = request.form.get('book')
    book = Book.query.filter_by(title=book_title).first()
    try:
        os.remove('static/img/{}'.format(book.img))
    except FileNotFoundError:
        pass
    try:
        os.remove('static/files/{}'.format(book.book))
    except FileNotFoundError:
        pass
    db.session.delete(book)
    db.session.commit()
    return redirect('/profile')


'''@app.route('/change_book', methods=['GET', 'POST'])
def change_book():
    if session['id'] != 1:
        return redirect('/index')
    if request.method == 'GET':
        return render_template('delete_book.html', Book=Book)
    book_title = request.form.get('book')
    book = Book.query.filter_by(title=book_title).first()
    db.session.delete(book)
    db.session.commit()
    return redirect('/profile')'''


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'id' in session:
        return redirect('/index')
    form = RegisterForm()
    if form.validate_on_submit():
        users = Bookworm.query.all()
        if form.username.data in [u.username for u in users]:
            render_template("register.html", title='Регистрация пользователя', form=form, error=True)
        else:
            user = Bookworm(username=form.username.data,
                            name=form.name.data,
                            surname=form.surname.data,
                            email=form.email.data,
                            password=generate_password_hash(form.password.data),
                            about=form.about.data)
            db.session.add(user)
            db.session.commit()
            session['username'] = form.username.data
            session['id'] = Bookworm.query.filter_by(username=session['username']).first().id
            return redirect('/index')
    return render_template("register.html",
                           title='Регистрация пользователя',
                           form=form)


@app.route('/books/<sort>')
def books(sort):
    if 'username' not in session:
        return redirect('/login')
    if sort == 'default':
        books_list = [Book.query.all()[i: i + 3 if i + 3 < len(Book.query.all()) else None] for i in
                      range(0, len(Book.query.all()), 3)]
        return render_template('books.html',
                               books=books_list,
                               session=session,
                               title='Все книги',
                               sort=False)
    elif sort == 'abc_sorting':
        books_list = [
            sorted(Book.query.all(), key=lambda x: x.title)[i: i + 3 if i + 3 < len(Book.query.all()) else None] for i
            in
            range(0, len(Book.query.all()), 3)]
        return render_template('books.html',
                               books=books_list,
                               session=session,
                               title='Все книги',
                               sort=True)


@app.route('/book/<int:book_id>', methods=['GET', 'POST'])
def book(book_id):
    if 'username' not in session:
        return redirect('/login')
    user = Bookworm.query.filter_by(id=session['id']).first()
    favourite_books = user.favourite_books
    if request.method == 'POST':
        if not favourite_books:
            user.favourite_books = str(book_id)
        else:
            favourite_books = favourite_books.split()
            if str(book_id) in favourite_books:
                favourite_books.remove(str(book_id))
            else:
                favourite_books.append(str(book_id))
            user.favourite_books = ' '.join(sorted(favourite_books,
                                                   key=lambda x: Book.query.filter_by(id=int(x)).first().title))
        db.session.commit()
        return redirect('/book/{}'.format(book_id))
    elif request.method == 'GET':
        book = Book.query.filter_by(id=book_id).first()
        title = book.title
        author = book.author
        about = book.about
        date = book.date
        img = book.img
        file = book.book
        button = ('Добавить в избранное',
                  'warning') if (not favourite_books or
                                 str(book_id) not in favourite_books.split()) else ('Удалить из избранного',
                                                                                    'danger')
        return render_template('book.html', title=title,
                               author=author,
                               about=about,
                               date=date,
                               img=img,
                               file=file,
                               button=button)


if __name__ == '__main__':
    db.create_all()
    app.run(port=8080, host='127.0.0.1')
