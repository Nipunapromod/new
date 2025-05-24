from flask import Flask, render_template, request, redirect, session
import sqlite3
import bcrypt

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Create DB tables if not exist
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password BLOB,
        role TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_username TEXT,
        subject TEXT,
        marks INTEGER
    )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    if 'username' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=?", (session['username'],))
    role = c.fetchone()[0]
    conn.close()

    if role == 'admin':
        return redirect('/admin')
    else:
        return redirect('/student')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')
        role = request.form['role']
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                      (username, hashed, role))
            conn.commit()
            return redirect('/login')
        except sqlite3.IntegrityError:
            return "Username already exists."
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username=?", (username,))
        result = c.fetchone()
        conn.close()

        if result and bcrypt.checkpw(password, result[0]):
            session['username'] = username
            return redirect('/')
        else:
            return "Invalid credentials!"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

# Admin dashboard
@app.route('/admin')
def admin():
    if 'username' not in session:
        return redirect('/login')
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=?", (session['username'],))
    role = c.fetchone()[0]
    conn.close()
    if role != 'admin':
        return "Access denied"
    return render_template('admin.html')

# Student dashboard
@app.route('/student')
def student():
    if 'username' not in session:
        return redirect('/login')
    return render_template('student.html')

# Add record (admin only)
@app.route('/add_record', methods=['GET', 'POST'])
def add_record():
    if 'username' not in session:
        return redirect('/login')

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=?", (session['username'],))
    role = c.fetchone()[0]
    if role != 'admin':
        return "Access denied"
    
    if request.method == 'POST':
        student_username = request.form['student_username']
        subject = request.form['subject']
        marks = int(request.form['marks'])
        c.execute("INSERT INTO records (student_username, subject, marks) VALUES (?, ?, ?)",
                  (student_username, subject, marks))
        conn.commit()
        conn.close()
        return redirect('/view_records')
    conn.close()
    return render_template('add_record.html')

# View all records (admin only)
@app.route('/view_records')
def view_records():
    if 'username' not in session:
        return redirect('/login')

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=?", (session['username'],))
    role = c.fetchone()[0]
    if role != 'admin':
        return "Access denied"

    c.execute("SELECT id, student_username, subject, marks FROM records")
    records = c.fetchall()
    conn.close()
    return render_template('view_records.html', records=records)

# Edit record (admin only)
@app.route('/edit_record/<int:record_id>', methods=['GET', 'POST'])
def edit_record(record_id):
    if 'username' not in session:
        return redirect('/login')

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=?", (session['username'],))
    role = c.fetchone()[0]
    if role != 'admin':
        return "Access denied"

    if request.method == 'POST':
        subject = request.form['subject']
        marks = int(request.form['marks'])
        c.execute("UPDATE records SET subject=?, marks=? WHERE id=?", (subject, marks, record_id))
        conn.commit()
        conn.close()
        return redirect('/view_records')

    c.execute("SELECT student_username, subject, marks FROM records WHERE id=?", (record_id,))
    record = c.fetchone()
    conn.close()
    if not record:
        return "Record not found"
    return render_template('edit_record.html', record_id=record_id, record=record)

# Delete record (admin only)
@app.route('/delete_record/<int:record_id>')
def delete_record(record_id):
    if 'username' not in session:
        return redirect('/login')

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT role FROM users WHERE username=?", (session['username'],))
    role = c.fetchone()[0]
    if role != 'admin':
        return "Access denied"

    c.execute("DELETE FROM records WHERE id=?", (record_id,))
    conn.commit()
    conn.close()
    return redirect('/view_records')

# Student view their own records
@app.route('/my_records')
def my_records():
    if 'username' not in session:
        return redirect('/login')

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT subject, marks FROM records WHERE student_username=?", (session['username'],))
    records = c.fetchall()
    conn.close()
    return render_template('my_records.html', records=records)

if __name__ == '__main__':
    app.run(debug=True)
