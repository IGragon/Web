from flask import Flask, session, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import StringField, SubmitField, TextAreaField, \
    PasswordField, BooleanField, SelectField
from wtforms.validators import DataRequired, Email, Length
from PIL import Image
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from random import sample
import os

# Импортируем модули

# Инициализируем приложение
# И настраеваем
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///OnLib_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPPLOAD_FOLDER'] = 'static/files/'
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

# Инициализируем базу данных
db = SQLAlchemy(app)


# форма регистрации
class RegisterForm(FlaskForm):
    username = StringField('Имя', validators=[DataRequired(),
                           Length(1, 120)])
    name = StringField('Настоящее имя', validators=[DataRequired()])
    surname = StringField('Фамилия', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(),
                                             Email()])
    password = PasswordField('Пароль', validators=[DataRequired(),
                             Length(4, 120)])
    about = TextAreaField('О себе', validators=[DataRequired(),
                          Length(1, 1000)])
    submit = SubmitField('Присоединиться!')


# форма авторизации
class LoginForm(FlaskForm):
    login = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


# форма добавления книг
class AddBookForm(FlaskForm):
    title = StringField('Название книги',
                        validators=[DataRequired(),
                                    Length(1, 120)])
    author = StringField('Автор', validators=[DataRequired()])
    about = TextAreaField('О книге', validators=[DataRequired(),
                          Length(100, 1000)])
    date = StringField('Дата публикации',
                       validators=[DataRequired()])
    img = FileField('Обложка', validators=[FileRequired()])
    book = FileField('Загрузить книгу', validators=[FileRequired()])
    check = BooleanField('Я проверил все поля',
                         validators=[DataRequired()])
    submit = SubmitField('Создать')


# форма добавления в избранное
class AddBookToFavourite(FlaskForm):
    submit = SubmitField('')


# форма для комментария
class CommentForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired(),
                        Length(1, 120)])
    rating = SelectField('Оценка', choices=[('★★★★★', '★★★★★'),
                         ('★★★★', '★★★★'),
                         ('★★★', '★★★'),
                         ('★★', '★★'),
                         ('★', '★')],
                         validators=[DataRequired()])
    about = TextAreaField('Комментарий', validators=[DataRequired(),
                          Length(1,
                          1000)])
    submit = SubmitField('Отправить')


# класс пользователя
# раз книжный магазин,
# то почему бы пользователи не были книжными червями
# уникальный id
# ник пользователя
# его имя
# фамилия
# информация введенная пользователем
# электронная почта
# пароль
# список любимых книг
class Bookworm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(80), unique=False, nullable=False)
    surname = db.Column(db.String(80), unique=False, nullable=False)
    about = db.Column(db.String(1000), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), unique=False,
                         nullable=False)
    favourite_books = db.Column(db.String(1000), unique=False,
                                nullable=True)

    def __repr__(self):
        return '<Bookworm {} {} {} {} {}>'.format(
            self.id, self.username, self.name, self.surname,
            self.password)


# класс книг
# уникальный id
# название книги
# её автор
# о книге
# дата публикации
# ссылка на обложку
# ссылка на книгу
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


# класс комментариев
# уникальный id
# заголовок
# выставленный рейтинг
# текст коммента
# привязка к книге
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), unique=False, nullable=False)
    rating = db.Column(db.String(5), unique=False, nullable=False)
    about = db.Column(db.String(1000), unique=False, nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'),
                        nullable=False)
    book = db.relationship('Book', backref=db.backref('Comment',
                                                      lazy=True))

    def __repr__(self):
        return '<Comment {} {} {} {} {}>'.format(
            self.id, self.title, self.rating, self.book_id,
            self.book)


# метод подгона изображения для обложки книги
def resize_image(image):
    im = Image.open('static/img/' + image)
    im = im.resize((286, 429), resample=0, box=None)
    im.save('static/img/' + image)


# главная страница
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


# страница авторизации
@app.route('/login', methods=['GET', 'POST'])
def login():
    # проверяем на авторизованного пользователя
    # если уже авторизован, посылаем на славную страницу
    if 'id' in session:
        return redirect('/index')
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user_password = Bookworm.query. \
                filter_by(username=form.
                          login.data).first().password
            password = form.password.data
            if check_password_hash(user_password, password):
                session['username'] = form.login.data
                session['id'] = Bookworm.query. \
                    filter_by(username=form.
                              login.data).first().id
                return redirect('/index')
            else:
                return render_template('login.html',
                                       form=form,
                                       session=session,
                                       error='password',
                                       title='Логин')
        except Exception:
            return render_template('login.html',
                                   form=form,
                                   session=session,
                                   error='login',
                                   title='Логин')
    return render_template('login.html',
                           form=form,
                           session=session,
                           error=False,
                           title='Логин')


# выход из аккаунта
@app.route('/logout')
def logout():
    # проверяем на авторизованного пользователя
    # если не авторизован, посылаем на славную страницу
    if 'id' not in session:
        return redirect('/index')
    session.pop('username', 0)
    session.pop('id', 0)
    return redirect('/login')


# страница профиля
@app.route('/profile')
def profile():
    # проверяем на авторизованного пользователя
    # если не авторизован, посылаем на славную страницу
    if 'id' not in session:
        return redirect('/index')
    user = Bookworm.query.filter_by(username=session['username']). \
        first()
    books = list(map(lambda x: Book.query.filter_by(id=x).first(),
                     map(int,
                         user.favourite_books.split()))) if \
        user.favourite_books else []
    return render_template('profile.html',
                           session=session,
                           admin=session['id'] == 1,
                           user=user,
                           books=books,
                           len=len,
                           title='Профиль')


# добавление книги
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    # проверяем на авторизованного администратора
    # если не админ, посылаем на славную страницу
    if 'id' not in session:
        return redirect('/index')
    if session['id'] != 1:
        return redirect('/index')
    form = AddBookForm()
    if form.validate_on_submit():
        img_f = form.img.data
        img_name = form.title.data + form.author.data + \
            form.date.data + '.' + \
            secure_filename(img_f.filename).split('.')[-1]
        img_f.save('static/img/' + img_name)
        resize_image(img_name)
        book_f = form.book.data
        book_f_name = form.title.data + form.author.data + \
            form.date.data + '.' + \
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


# удаление книги
@app.route('/del_book', methods=['GET', 'POST'])
def del_book():
    # проверяем на авторизованного администратора
    # если не админ, посылаем на славную страницу
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


# изменение книги
@app.route('/change_book', methods=['GET', 'POST'])
def change_book():
    # проверяем на авторизованного администратора
    # если не админ, посылаем на славную страницу
    if session['id'] != 1:
        return redirect('/index')
    if request.method == 'GET':
        return render_template('change_book.html', Book=Book,
                               book=0, choose=True)
    elif request.method == 'POST':
        if request.form.get('confirm_book'):
            book_title = request.form.get('book')
            book = Book.query.filter_by(title=book_title).first()
            return render_template('change_book.html', Book=Book,
                                   cur_book=book, choose=False)
        elif request.form.get('change_book'):
            book_id = request.form.get('book_id')
            title = request.form.get('title')
            author = request.form.get('author')
            book_about = request.form.get('about')
            date = request.form.get('date')
            book = Book.query.filter_by(id=book_id).first()

            book.title = title
            book.author = author
            book.about = book_about
            book.date = date
            db.session.commit()
            return redirect('/profile')


# регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    # проверяем на авторизованного пользователя
    # если уже авторизован, посылаем на славную страницу
    if 'id' in session:
        return redirect('/index')
    form = RegisterForm()
    if form.validate_on_submit():
        users = Bookworm.query.all()
        if form.username.data in [u.username for u in users]:
            render_template("register.html",
                            title='Регистрация пользователя',
                            form=form, error=True)
        else:
            user = Bookworm(username=form.username.data,
                            name=form.name.data,
                            surname=form.surname.data,
                            email=form.email.data,
                            password=generate_password_hash(form.
                                                            password
                                                            .data),
                            about=form.about.data)
            db.session.add(user)
            db.session.commit()
            session['username'] = form.username.data
            session['id'] = Bookworm.query. \
                filter_by(username=session['username']).first().id
            return redirect('/index')
    return render_template("register.html",
                           title='Регистрация пользователя',
                           form=form)


# страница со всеми книгами
@app.route('/books/<sort>')
def books(sort):
    # проверяем на авторизованного пользователя
    # если не авторизован, посылаем на славную страницу
    if 'username' not in session:
        return redirect('/login')
    if sort == 'default':  # изначально сортировки нет
        books_list = [Book.query.all()[i: i + 3 if
                      i + 3 < len(Book.query.all()) else None] for i in
                      range(0, len(Book.query.all()), 3)]
        return render_template('books.html',
                               books=books_list,
                               session=session,
                               title='Все книги',
                               sort=False)
    elif sort == 'abc_sorting':  # сортировка по алфавиту
        books_list = [
            sorted(Book.query.all(),
                   key=lambda x: x.title)[i: i + 3 if
            i + 3 < len(Book.query.all()) else None] for i
            in
            range(0, len(Book.query.all()), 3)]
        return render_template('books.html',
                               books=books_list,
                               session=session,
                               title='Все книги',
                               sort=True)
    elif sort == 'author_sorting':  # сортировка по имени автора
        books_list = [
            sorted(Book.query.all(),
                   key=lambda x: (x.author,
                                  x.title))[i: i + 3 if
            i + 3 < len(Book.query.all()) else None] for i
            in
            range(0, len(Book.query.all()), 3)]
        return render_template('books.html',
                               books=books_list,
                               session=session,
                               title='Все книги',
                               sort=True)


# страница для определенной книги
@app.route('/book/<int:book_id>', methods=['GET', 'POST'])
def book(book_id):
    # проверяем на авторизованного пользователя
    # если не авторизован, посылаем на славную страницу
    if 'username' not in session:
        return redirect('/login')
    user = Bookworm.query.filter_by(id=session['id']).first()
    favourite_books = user.favourite_books
    comment_form = CommentForm()
    if comment_form.validate_on_submit():  # добавление комментария
        comment = Comment(title=comment_form.title.data,
                          rating=comment_form.rating.data,
                          about=comment_form.about.data)
        book = Book.query.filter_by(id=int(book_id)).first()
        book.Comment.append(comment)
        db.session.commit()
        return redirect('/book/{}'.format(book_id))
    if request.method == 'POST':  # добавить/удалить из избранного
        if not favourite_books:
            user.favourite_books = str(book_id)
        else:
            favourite_books = favourite_books.split()
            if str(book_id) in favourite_books:
                favourite_books.remove(str(book_id))
            else:
                favourite_books.append(str(book_id))
            user.favourite_books = ' '.join(sorted(favourite_books,
                                                   key=lambda x:
                                                   Book.query.
                                                   filter_by
                                                   (id=int(x)).
                                                   first().title))
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
                                 str(book_id) not
                                 in favourite_books.split()) \
            else ('Удалить из избранного',
                  'danger')
        comments = book.Comment
        comments = sorted(comments, key=lambda x: (-len(x.rating),
                                                   x.title))
        return render_template('book.html', title=title,
                               author=author,
                               about=about,
                               date=date,
                               img=img,
                               file=file,
                               button=button,
                               comment=comment_form,
                               comments=comments,
                               session=session)


# удаление комментария
@app.route('/delete_comment/<int:comment_id>')
def delete_comment(comment_id):
    # проверяем на авторизованного администратора
    # если не админ, посылаем на славную страницу
    if 'id' not in session or session['id'] != 1:
        return redirect('/index')
    comment = Comment.query.filter_by(id=comment_id).first()
    book_id = comment.book_id
    db.session.commit()
    db.session.delete(comment)
    db.session.commit()
    return redirect('/book/{}'.format(book_id))


# о проекте
@app.route('/about')
def about():
    if 'username' not in session:
        return redirect('/login')
    return render_template('about.html', session=session,
                           title='О нас')


# страничка с "пожертвованиями"
@app.route('/donate')
def donate():
    if 'username' not in session:
        return redirect('/login')
    return render_template('donate.html', session=session,
                           title='Поддержка')


if __name__ == '__main__':
    db.create_all()
    app.run(port=8080, host='127.0.0.1')
