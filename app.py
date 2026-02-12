from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('library.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS books
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT,
                  author TEXT,
                  year TEXT)''')
    conn.close()

init_db()

@app.route('/')
def index():
    conn = sqlite3.connect('library.db')
    books = conn.execute("SELECT * FROM books").fetchall()
    conn.close()
    return render_template('index.html', books=books)

@app.route('/add', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        year = request.form['year']

        conn = sqlite3.connect('library.db')
        conn.execute("INSERT INTO books (title, author, year) VALUES (?, ?, ?)",
                     (title, author, year))
        conn.commit()
        conn.close()
        return redirect('/')

    return render_template('add_book.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_book(id):
    conn = sqlite3.connect('library.db')

    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        year = request.form['year']

        conn.execute("UPDATE books SET title=?, author=?, year=? WHERE id=?",
                     (title, author, year, id))
        conn.commit()
        conn.close()
        return redirect('/')

    book = conn.execute("SELECT * FROM books WHERE id=?", (id,)).fetchone()
    conn.close()
    return render_template('edit_book.html', book=book)

@app.route('/delete/<int:id>')
def delete_book(id):
    conn = sqlite3.connect('library.db')
    conn.execute("DELETE FROM books WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)