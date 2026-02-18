from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- USER TABLE ----------------
def create_user_table():
    conn = sqlite3.connect('library.db')
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')

    cur.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", 
                ('admin', 'admin123'))

    conn.commit()
    conn.close()

create_user_table()

# ---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session['user'] = username
            return redirect('/')
        else:
            return "Invalid Username or Password"

    return render_template('login.html')
@app.route('/logout')
def logout():
    session.pop('user', None)   # remove user from session
    return redirect('/login')

# ---------------- HOME ----------------
@app.route('/')
def index():
    if 'user' not in session:
        return redirect('/login')

    conn = get_db_connection()
    books = conn.execute("SELECT * FROM books").fetchall()
    conn.close()

    return render_template('index.html', books=books)

# ---------------- ADD BOOK ----------------
@app.route('/add', methods=['GET', 'POST'])
def add_book():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        year = request.form['year']

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO books (title, author, year) VALUES (?, ?, ?)",
            (title, author, year)
        )
        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('book.html')

# ---------------- EDIT BOOK ----------------
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_book(id):
    if 'user' not in session:
        return redirect('/login')

    conn = get_db_connection()

    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        year = request.form.get('year')

        conn.execute(
            "UPDATE books SET title=?, author=?, year=? WHERE id=?",
            (title, author, year, id)
        )
        conn.commit()
        conn.close()

        return redirect('/')

    book = conn.execute("SELECT * FROM books WHERE id=?", (id,)).fetchone()
    conn.close()

    return render_template('edit.html', book=book)

# ---------------- DELETE ----------------
@app.route('/delete/<int:id>')
def delete_book(id):
    if 'user' not in session:
        return redirect('/login')

    conn = get_db_connection()
    conn.execute("DELETE FROM books WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect('/')

# ---------------- SEARCH ----------------
@app.route("/search")
def search():
    if 'user' not in session:
        return redirect('/login')

    query = request.args.get("query")

    conn = get_db_connection()
    books = conn.execute(
        "SELECT * FROM books WHERE title LIKE ? OR author LIKE ?",
        ('%' + query + '%', '%' + query + '%')
    ).fetchall()
    conn.close()

    return render_template("index.html", books=books)

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)
