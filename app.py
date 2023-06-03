import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename


app = Flask(__name__)
app.secret_key = '8000'  # Set a secret key for session encryption
app.config['UPLOAD_FOLDER'] = 'static/photos'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
bcrypt = Bcrypt(app)
DATABASE = 'users.db'


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def get_user_folder():
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], session['username'])
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    return user_folder


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.pop('username', None)
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            error = 'Invalid username or password'
            return render_template('login.html', error=error)

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=?", (username,))
            user = cursor.fetchone()

            if user and bcrypt.check_password_hash(user[2], password):
                session['username'] = user[1]
                return redirect(url_for('dashboard'))

        error = 'Invalid username or password'
        return render_template('login.html', error=error)

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=?", (username,))
            existing_user = cursor.fetchone()

            if existing_user:
                return render_template('register.html', error='Username already exists')

            try:
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
                conn.commit()
            except Exception as e:
                return render_template('register.html', error='Error registering user: ' + str(e))

        session['username'] = username
        return redirect(url_for('dashboard'))

    return render_template('register.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        file = request.files['file']
        description = request.form['description']

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            user_folder = get_user_folder()
            file_path = os.path.join(user_folder, filename)
            file.save(file_path)


    user_folder = get_user_folder()
    files = os.listdir(user_folder)
    return render_template('dashboard.html', files=files)


@app.route('/dashboard_file/<filename>')
def dashboard_file(filename):
    user_folder = get_user_folder()
    file_path = os.path.join(user_folder, filename)
    return render_template('dashboard_file.html', filename=filename, file_path=file_path)


if __name__ == '__main__':
    app.run()