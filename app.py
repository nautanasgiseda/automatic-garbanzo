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


def get_user_folder(username):
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    return user_folder


@app.route('/', methods=['GET', 'POST'])
def login():
    if 'username' in session:
        return redirect(url_for('dashboard'))

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
    if 'username' in session:
        return redirect(url_for('dashboard'))

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
    if 'username' in session:
        username = session['username']
        user_folder = get_user_folder(username)

        if request.method == 'POST':
            file = request.files['file']
            description = request.form['description']

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(user_folder, filename))
                # You can store the image filename and description in the database for persistent storage

        user_files = os.listdir(user_folder)
        return render_template('dashboard.html', files=user_files)

    return redirect(url_for('login'))


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run()