from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookcrossing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Модель пользователя
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        """Устанавливает хэш пароля."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Проверяет пароль."""
        return check_password_hash(self.password_hash, password)

# Модель книги
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    cover = db.Column(db.String(200))  # Путь к обложке
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    available = db.Column(db.Boolean, default=True)

@login_manager.user_loader
def load_user(user_id):
    """Загружает пользователя по ID."""
    return User.query.get(int(user_id))

# Форма регистрации
class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')

# Форма входа
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

# Форма добавления книги
class BookForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    author = StringField('Автор', validators=[DataRequired()])
    cover = FileField('Обложка')
    submit = SubmitField('Добавить')

# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('Этот email уже зарегистрирован!')
            return redirect(url_for('register'))
        user = User(email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна! Войдите в систему.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# Вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Неверный email или пароль!')
    return render_template('login.html', form=form)

# Личный кабинет
@app.route('/dashboard')
@login_required
def dashboard():
    books = Book.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', books=books)

# Добавление книги
@app.route('/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    form = BookForm()
    if form.validate_on_submit():
        book = Book(
            title=form.title.data,
            author=form.author.data,
            user_id=current_user.id
        )
        db.session.add(book)
        db.session.commit()
        flash('Книга добавлена!')
        return redirect(url_for('dashboard'))
    return render_template('add_book.html', form=form)

# Просмотр доступных книг
@app.route('/books')
def books():
    available_books = Book.query.filter_by(available=True).all()
    return render_template('books.html', books=available_books)

# Забрать книгу
@app.route('/take_book/<int:book_id>')
@login_required
def take_book(book_id):
    book = Book.query.get_or_404(book_id)
    if book.available and book.user_id != current_user.id:
        book.available = False
        db.session.commit()
        flash('Книга успешно забрана!')
    else:
        flash('Книга недоступна или принадлежит вам!')
    return redirect(url_for('books'))

# Выход
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создаёт таблицы в базе данных
    app.run(debug=True)