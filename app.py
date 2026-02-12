from flask import Flask, render_template, request, redirect
import os
import psycopg2
from urllib.parse import urlparse
app = Flask(__name__)
def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    result = urlparse(database_url)
    conn = psycopg2.connect(
        dbname=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )
    return conn
conn = get_db_connection()
cur = conn.cursor()
cur.execute('''
CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL
)
''')
conn.commit()
cur.close()
conn.close()



init_db()

@app.route('/')
def index():
   conn = get_db_connection()
   cur = conn.cursor()

    books = conn.execute("SELECT * FROM books").fetchall()
    conn.close()
    return render_template('index.html', books=books)
    cur.close()
    conn.close()


@app.route('/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        year = request.form['year']

         conn = get_db_connection()
         cur = conn.cursor()
        conn.execute("INSERT INTO books (title, author, year) VALUES (?, ?, ?)",
                     (title, author, year))
         cur.close()
         conn.close()

        return redirect('/')

    return render_template('add_book.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_book(id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        year = request.form['year']

        conn.execute("UPDATE books SET title=?, author=?, year=? WHERE id=?",
                     (title, author, year, id))
         cur.close()
         conn.close()
        return redirect('/')

    book = conn.execute("SELECT * FROM books WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template('edit_book.html', book=book)

@app.route('/delete/<int:id>')
def delete_book(id):
    conn = get_db_connection()
    cur = conn.cursor()
    conn.execute("DELETE FROM books WHERE id=?", (id,))
    cur.close()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)