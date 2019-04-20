from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, render_template, redirect
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired
import os
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
db = SQLAlchemy(app)
db.create_all()

class AddUserForm(FlaskForm):
    name = StringField('Имя пользователя', validators=[DataRequired()])
    content = TextAreaField('О себе', validators=[DataRequired()])
    submit = SubmitField('Добавить')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    info = db.Column(db.String(255))

    def __repr__(self):
        return '<User {} {} {}>'.format(
            self.id, self.username, self.info)

@app.route('/user', methods=['GET', 'POST'])
def user():
    form = AddUserForm()
    if form.validate_on_submit():
        try:
            user = User(username=form.name.data,
                        info=form.content.data)
            db.session.add(user)
            db.session.commit()
            print(1233)
            return redirect('/success')
        except Exception as e:
            render_template('user.html', form=form, error=e)
    return render_template('user.html', form=form, error=False)

@app.route('/success')
def success():
    print('1123')
    return 'Vse ok!.'

if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
