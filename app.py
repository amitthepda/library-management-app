from flask import Flask, render_template, request, redirect

import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "library.db")

import sqlite3

def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row   # ✅ allows dict-like access
    return conn


app = Flask(__name__)

def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            year TEXT
        )
    ''')
    print("Table created successfully!")

    conn.commit()
    conn.close()



@app.route('/')
def index():
    conn = get_db_connection()
    books = conn.execute("SELECT * FROM books").fetchall()
    conn.close()
    return render_template('index.html', books=books)

@app.route('/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        year = request.form['year']

        conn = get_db_connection()
        conn.execute("INSERT INTO books (title, author, year) VALUES (?, ?, ?)",
                     (title, author, year))
        conn.commit()
        conn.close()
        return redirect('/')

    return render_template('book.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_book(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        year = request.form.get('year')

        cursor.execute(
            "UPDATE books SET title=?, author=?, year=? WHERE id=?",
            (title, author, year, id)
        )

        conn.commit()
        conn.close()

        return redirect('/')

    cursor.execute("SELECT * FROM books WHERE id=?", (id,))
    book = cursor.fetchone()

    print("Book data:", dict(book) if book else None)

    conn.close()

    return render_template('edit.html', book=book)


@app.route('/delete/<int:id>')
def delete_book(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM books WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)