import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from datetime import datetime
from openpyxl import Workbook
from flask import send_file
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from flask import send_file

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
            title TEXT,
            author TEXT,
            year TEXT,
            status TEXT DEFAULT 'Available'
        )
    ''')

    cur.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)", 
                ('admin', 'admin123'))

    conn.commit()
    conn.close()

create_user_table()
def update_books_table():
    conn = sqlite3.connect('library.db')
    cur = conn.cursor()

    #cur.execute("ALTER TABLE books ADD COLUMN issue_date TEXT")
    #cur.execute("ALTER TABLE books ADD COLUMN return_date TEXT")
    
    #cur.execute("UPDATE books SET status='Returned' WHERE return_date IS NOT NULL;")


    conn.commit()
    conn.close()
update_books_table()

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

@app.route('/issue/<int:id>', methods=['GET', 'POST'])
def issue_book(id):
    if 'user' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        student = request.form['student']

        issue_date = datetime.now().strftime("%Y-%m-%d")

        conn = get_db_connection()
        conn.execute("""
            UPDATE books 
            SET status='Issued', student_name=?, issue_date=?, return_date=NULL 
            WHERE id=?
        """, (student, issue_date, id))

        conn.commit()
        conn.close()

        return redirect('/')

    return render_template('issue.html', id=id)
@app.route('/monthly_report')
def monthly_report():
    conn = get_db_connection()

    # 📊 Issue count per month
    issue_data = conn.execute("""
        SELECT substr(issue_date, 1, 7) as month, COUNT(*) as total
        FROM books
        WHERE issue_date IS NOT NULL
        GROUP BY month
    """).fetchall()

    # 📊 Return count per month
    return_data = conn.execute("""
        SELECT substr(return_date, 1, 7) as month, COUNT(*) as total
        FROM books
        WHERE return_date IS NOT NULL
        GROUP BY month
    """).fetchall()

    conn.close()

    # Convert to dict
    issue_dict = {row['month']: row['total'] for row in issue_data}
    return_dict = {row['month']: row['total'] for row in return_data}

    all_months = sorted(set(issue_dict.keys()) | set(return_dict.keys()))

    issue_counts = [issue_dict.get(m, 0) for m in all_months]
    return_counts = [return_dict.get(m, 0) for m in all_months]

    # 📈 Graph
    plt.figure()
    plt.plot(all_months, issue_counts, marker='o', label="Issued")
    plt.plot(all_months, return_counts, marker='o', label="Returned")
    plt.xlabel("Month")
    plt.ylabel("Books")
    plt.title("Monthly Report")
    plt.legend()

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(BASE_DIR, "static", "monthly.png")

    plt.savefig(file_path)
    plt.close()

    return render_template(
        "monthly.html",
        months=all_months,
        issue=issue_counts,
        returned=return_counts
    )
    
@app.route('/export_pdf')
def export_pdf():
    conn = get_db_connection()
    books = conn.execute("SELECT * FROM books").fetchall()
    conn.close()

    file_path = "library_report.pdf"

    pdf = SimpleDocTemplate(file_path)

    # Table data
    data = []
    data.append([
        "ID", "Title", "Author", "Year",
        "Status", "Student", "Issue Date", "Return Date"
    ])

    for book in books:
        data.append([
            book['id'],
            book['title'],
            book['author'],
            book['year'],
            book['status'],
            book['student_name'],
            book['issue_date'],
            book['return_date']
        ])

    table = Table(data)

    # Styling
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ])

    table.setStyle(style)

    elements = []
    elements.append(table)

    pdf.build(elements)

    return send_file(file_path, as_attachment=True)

@app.route('/return/<int:id>')
def return_book(id):
    from datetime import datetime

    return_date = datetime.now().strftime("%Y-%m-%d")

    conn = get_db_connection()
    conn.execute("""
        UPDATE books 
        SET status='Returned', return_date=? 
        WHERE id=?
    """, (return_date, id))

    conn.commit()
    conn.close()

    return redirect('/')

@app.route('/issued_pdf')
def issued_pdf():
    conn = get_db_connection()

    # ONLY ISSUED BOOKS
    books = conn.execute("""
        SELECT * FROM books 
        WHERE status = 'Issued'
    """).fetchall()

    conn.close()

    file_path = "issued_books.pdf"
    pdf = SimpleDocTemplate(file_path)

    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("Issued Books Report", styles['Title']))

    # Table Data
    data = []
    data.append([
        "ID", "Title", "Author",
        "Student", "Issue Date"
    ])

    for book in books:
        data.append([
            book['id'],
            book['title'],
            book['author'],
            book['student_name'],
            book['issue_date']
        ])

    table = Table(data)

    # Styling
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ])

    table.setStyle(style)

    elements.append(table)

    pdf.build(elements)

    return send_file(file_path, as_attachment=True)

@app.route('/export_excel')
def export_excel():
    conn = get_db_connection()
    books = conn.execute("SELECT * FROM books").fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Library Report"

    # Header
    ws.append([
        "ID", "Title", "Author", "Year",
        "Status", "Student", "Issue Date", "Return Date"
    ])

    # Data
    for book in books:
        ws.append([
            book['id'],
            book['title'],
            book['author'],
            book['year'],
            book['status'],
            book['student_name'],
            book['issue_date'],
            book['return_date']
        ])

    file_path = "library_report.xlsx"
    wb.save(file_path)

    return send_file(file_path, as_attachment=True)


   
@app.route('/logout')
def logout():
    session.pop('user', None)   # remove user from session
    return redirect('/login')

# ---------------- HOME ----------------
@app.route('/graph')
def graph():
    conn = get_db_connection()

    data = conn.execute("""
        SELECT student_name, COUNT(*) as total
        FROM books
        GROUP BY student_name
    """).fetchall()

    conn.close()

    students = [row['student_name'] for row in data if row['student_name']]
    counts = [row['total'] for row in data if row['student_name']]

    plt.figure()
    plt.bar(students, counts)
    plt.xlabel("Students")
    plt.ylabel("Books Issued")
    plt.title("Student-wise Book Issue")


    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(BASE_DIR, "static", "graph.png")

    plt.savefig(file_path)
    plt.close()

    return render_template("graph.html")

@app.route('/')
def index():
    if 'user' not in session:
        return redirect('/login')

    conn = get_db_connection()
    books = conn.execute("SELECT * FROM books").fetchall()
    conn.close()

    return render_template('index.html', books=books)
@app.route('/report')
def report():
    if 'user' not in session:
        return redirect('/login')

    conn = get_db_connection()

    books = conn.execute("""
    SELECT student_name,title,issue_date,return_date,status
    from books where student_name is not null order by student_name
     """).fetchall()
    
    conn.close()

    return render_template('report.html', books=books)


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
