import sqlite3
from flask import Flask, render_template, redirect, url_for, request, session
from functools import wraps
from flask import session, redirect, url_for

app = Flask(__name__)
app.secret_key = 'secret_key'  # Ganti dengan secret key yang lebih aman
DATABASE = 'instance/database.db'


# Fungsi untuk koneksi database
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Memungkinkan akses hasil query seperti dictionary
    return conn

# Decorator untuk memastikan pengguna sudah login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):  # Cek apakah sesi login ada
            return redirect(url_for('login'))  # Redirect ke halaman login jika belum login
        return f(*args, **kwargs)
    return decorated_function


# Halaman login
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None  # Variabel untuk menyimpan pesan kesalahan
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                            (username, password)).fetchone()
        conn.close()
        
        if user:
            session['logged_in'] = True
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid Credentials, Please try again.'
    
    return render_template('login.html', error=error)



# Halaman utama
@app.route('/main')
def main():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('main.html', username=session['username'])


# Halaman dashboard
@app.route('/dashboard/')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

# @app.route('/car_management/')
# def car_management():
#     if not session.get('logged_in'):
#         return redirect(url_for('login'))
#     return render_template('car_management.html', username=session['username'])

@app.route('/car_management/', methods=['GET', 'POST'])
@login_required
def car_management():
    if request.method == 'POST':
        car_name = request.form['carName']
        driver_phone = request.form['driverPhone']
        description = request.form['description']
        
        # Simpan data ke database atau lakukan operasi lain
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO cars (name, driver_phone, description) VALUES (?, ?, ?)',
            (car_name, driver_phone, description)
        )
        conn.commit()
        conn.close()
        
        return redirect(url_for('car_management'))  # Redirect untuk menghindari pengiriman ulang data
    return render_template('car_management.html', username=session['username'])


@app.route('/room_management/')
def room_management():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('room_management.html', username=session['username'])

@app.route('/car_booking/')
def car_booking():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('car_booking.html', username=session['username'])

@app.route('/room_booking/')
def room_booking():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('room_booking.html', username=session['username'])

@app.route('/report/')
def report():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('report.html', username=session['username'])

# Logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
