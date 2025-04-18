from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField
from wtforms.validators import DataRequired
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bookcrossing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Папка для сохранения обложек
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}  # Разрешённые форматы

# Создаём папку для загрузок, если её нет
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

def allowed_file(filename):
    """Проверяет, разрешён ли формат файла.

    Args:
        filename (str): Имя файла.

    Returns:
        bool: True, если расширение файла разрешено, иначе False.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

class User(UserMixin, db.Model):
    """Модель пользователя для хранения данных об аккаунте."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        """Хэширует и сохраняет пароль пользователя.

        Args:
            password (str): Пароль в виде строки.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Проверяет, совпадает ли введённый пароль с хэшированным.

        Args:
            password (str): Пароль для проверки.

        Returns:
            bool: True, если пароль совпадает, иначе False.
        """
        return check_password_hash(self.password_hash, password)

class Book(db.Model):
    """Модель книги для хранения информации о книгах."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    cover = db.Column(db.String(200))  # Имя файла обложки
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Кто добавил
    available = db.Column(db.Boolean, default=True)
    taken_by = db.Column(db.Integer, db.ForeignKey('user.id'))  # Кто забрал

@login_manager.user_loader
def load_user(user_id):
    """Загружает пользователя по ID для Flask-Login.

    Args:
        user_id (str): ID пользователя в виде строки.

    Returns:
        User: Объект пользователя, если найден, иначе None.
    """
    return User.query.get(int(user_id))

class RegisterForm(FlaskForm):
    """Форма для регистрации нового пользователя."""
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')

class LoginForm(FlaskForm):
    """Форма для входа пользователя в систему."""
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class BookForm(FlaskForm):
    """Форма для добавления новой книги."""
    title = StringField('Название', validators=[DataRequired()])
    author = StringField('Автор', validators=[DataRequired()])
    cover = FileField('Обложка')
    submit = SubmitField('Добавить')

@app.route('/')
def index():
    """Отображает главную страницу сайта.

    Returns:
        str: HTML-страница главной страницы.
    """
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Обрабатывает регистрацию нового пользователя.

    Если пользователь с таким email уже существует, отображается сообщение об ошибке.
    После успешной регистрации пользователь перенаправляется на страницу входа.

    Returns:
        str: HTML-страница регистрации или перенаправление на страницу входа.
    """
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Обрабатывает вход пользователя в систему.

    Проверяет email и пароль пользователя. При успешном входе перенаправляет
    в личный кабинет, иначе отображает сообщение об ошибке.

    Returns:
        str: HTML-страница входа или перенаправление в личный кабинет.
    """
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Неверный email или пароль!')
    return render_template('login.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    """Отображает личный кабинет пользователя.

    Показывает список книг, добавленных текущим пользователем, и книг, которые он забрал.

    Returns:
        str: HTML-страница личного кабинета.
    """
    added_books = Book.query.filter_by(user_id=current_user.id).all()
    taken_books = Book.query.filter_by(taken_by=current_user.id).all()
    return render_template('dashboard.html', added_books=added_books, taken_books=taken_books)

@app.route('/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    """Обрабатывает добавление новой книги.

    Сохраняет загруженную обложку в папку static/uploads и записывает только имя файла
    в базу данных. Если обложка не загружена, используется default.jpg.
    После успешного добавления пользователь перенаправляется в личный кабинет.

    Returns:
        str: HTML-страница добавления книги или перенаправление в личный кабинет.
    """
    form = BookForm()
    if form.validate_on_submit():
        cover_filename = 'default.jpg'  # Имя файла по умолчанию
        if form.cover.data and allowed_file(form.cover.data.filename):
            filename = secure_filename(form.cover.data.filename)
            # Сохраняем файл в папку static/uploads
            form.cover.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cover_filename = filename  # Сохраняем только имя файла

        # Создаём новую книгу с данными из формы
        book = Book(
            title=form.title.data,
            author=form.author.data,
            cover=cover_filename,
            user_id=current_user.id
        )
        db.session.add(book)
        db.session.commit()
        flash('Книга добавлена!')
        return redirect(url_for('dashboard'))
    return render_template('add_book.html', form=form)

@app.route('/books')
def books():
    """Отображает список доступных книг.

    Показывает только книги, которые ещё не забрали (available=True).

    Returns:
        str: HTML-страница со списком доступных книг.
    """
    available_books = Book.query.filter_by(available=True).all()
    return render_template('books.html', books=available_books)

@app.route('/take_book/<int:book_id>')
@login_required
def take_book(book_id):
    """Обрабатывает взятие книги пользователем.

    Если книга доступна и не принадлежит текущему пользователю, её статус меняется
    на недоступную, и записывается ID пользователя, который её забрал.

    Args:
        book_id (int): ID книги, которую пользователь хочет взять.

    Returns:
        str: Перенаправление на страницу со списком книг.
    """
    book = Book.query.get_or_404(book_id)
    if book.available and book.user_id != current_user.id:
        book.available = False
        book.taken_by = current_user.id
        db.session.commit()
        flash('Книга успешно забрана!')
    else:
        flash('Книга недоступна или принадлежит вам!')
    return redirect(url_for('books'))

@app.route('/logout')
@login_required
def logout():
    """Обрабатывает выход пользователя из системы.

    После выхода пользователь перенаправляется на главную страницу.

    Returns:
        str: Перенаправление на главную страницу.
    """
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Создаёт таблицы в базе данных
    app.run(debug=True)