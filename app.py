import sqlite3
from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from functools import wraps
from flask import session, redirect, url_for
import os

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

UPLOAD_FOLDER = 'static/img'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



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

# @app.route('/car_management/', methods=['GET', 'POST'])
# @login_required
# def car_management():
#     if request.method == 'POST':
#         car_name = request.form['carName']
#         driver_phone = request.form['driverPhone']
#         description = request.form['description']
        
#         # Simpan data ke database atau lakukan operasi lain
#         conn = get_db_connection()
#         conn.execute(
#             'INSERT INTO cars (name, driver_phone, description) VALUES (?, ?, ?)',
#             (car_name, driver_phone, description)
#         )
#         conn.commit()
#         conn.close()
        
#         return redirect(url_for('car_management'))  # Redirect untuk menghindari pengiriman ulang data
#     return render_template('car_management.html', username=session['username'])

# @app.route('/car_management/', methods=['GET', 'POST'])
# @login_required
# def car_management():
#     if request.method == 'POST':
#         car_name = request.form['carName']
#         driver_phone = request.form['driverPhone']
#         description = request.form['description']
#         car_image = request.files['carImage']

#         # Validasi file gambar
#         if car_image and allowed_file(car_image.filename):
#             conn = get_db_connection()
#             # Simpan data mobil tanpa gambar dulu untuk mendapatkan ID
#             cur = conn.execute(
#                 'INSERT INTO cars (name, driver_phone, description, image_path) VALUES (?, ?, ?, ?)',
#                 (car_name, driver_phone, description, None)
#             )
#             car_id = cur.lastrowid  # Ambil ID dari record yang baru dimasukkan
#             conn.commit()

#             # Rename gambar sesuai format "id+name"
#             extension = car_image.filename.rsplit('.', 1)[1].lower()
#             new_filename = f"{car_id}_{car_name.replace(' ', '_')}.{extension}"
#             file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)

#             # Simpan file ke folder upload
#             car_image.save(file_path)

#             # Update path gambar ke database
#             conn.execute(
#                 'UPDATE cars SET image_path = ? WHERE id = ?',
#                 (file_path, car_id)
#             )
#             conn.commit()
#             conn.close()

#             return redirect(url_for('car_management'))  # Redirect setelah menyimpan data
        
#     # Ambil semua data mobil
#     conn = get_db_connection()
#     cars = conn.execute("SELECT id, name, driver_phone, description FROM cars").fetchall()
#     conn.close()

#     return render_template('car_management.html', username=session['username'],  cars=cars)

@app.route('/car_management/', methods=['GET', 'POST'])
@login_required
def car_management():
    if request.method == 'POST':
        car_id = request.form.get('carId')  # Ambil ID mobil dari form (jika ada)
        car_name = request.form['carName']
        driver_phone = request.form['driverPhone']
        description = request.form['description']
        car_image = request.files['carImage']

        conn = get_db_connection()

        if car_id:  # Jika ID mobil tersedia, lakukan update
            cur = conn.execute('SELECT name, image_path FROM cars WHERE id = ?', (car_id,))
            existing_car = cur.fetchone()

            if existing_car:
                old_name = existing_car['name']
                old_image_path = existing_car['image_path']

                # Jika nama mobil berubah, rename file gambar jika ada
                if old_name != car_name and old_image_path:
                    old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], old_image_path)
                    extension = old_image_path.rsplit('.', 1)[1].lower()
                    new_filename = f"{car_id}_{car_name.replace(' ', '_')}.{extension}"
                    new_file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)

                    # Rename file di filesystem
                    if os.path.exists(old_file_path):
                        os.rename(old_file_path, new_file_path)

                    # Update path gambar di database
                    conn.execute(
                        'UPDATE cars SET image_path = ? WHERE id = ?',
                        (new_filename, car_id)
                    )

                # Jika ada gambar baru yang diunggah
                if car_image and allowed_file(car_image.filename):
                    # Hapus gambar lama jika ada
                    if old_image_path:
                        old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], old_image_path)
                        if os.path.exists(old_file_path):
                            os.remove(old_file_path)

                    # Simpan gambar baru
                    extension = car_image.filename.rsplit('.', 1)[1].lower()
                    new_filename = f"{car_id}_{car_name.replace(' ', '_')}.{extension}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                    car_image.save(file_path)

                    # Update database dengan data baru
                    conn.execute(
                        'UPDATE cars SET image_path = ? WHERE id = ?',
                        (new_filename, car_id)
                    )

                # Update data lain (nama, no telp, keterangan)
                conn.execute(
                    'UPDATE cars SET name = ?, driver_phone = ?, description = ? WHERE id = ?',
                    (car_name, driver_phone, description, car_id)
                )

        else:  # Jika ID mobil tidak tersedia, tambahkan data baru
            image_path = None
            if car_image and allowed_file(car_image.filename):
                cur = conn.execute(
                    'INSERT INTO cars (name, driver_phone, description, image_path) VALUES (?, ?, ?, ?)',
                    (car_name, driver_phone, description, None)
                )
                car_id = cur.lastrowid
                conn.commit()

                # Rename dan simpan gambar
                extension = car_image.filename.rsplit('.', 1)[1].lower()
                new_filename = f"{car_id}_{car_name.replace(' ', '_')}.{extension}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                car_image.save(file_path)

                # Update path gambar di database
                conn.execute(
                    'UPDATE cars SET image_path = ? WHERE id = ?',
                    (new_filename, car_id)
                )
            else:
                conn.execute(
                    'INSERT INTO cars (name, driver_phone, description) VALUES (?, ?, ?)',
                    (car_name, driver_phone, description)
                )

        conn.commit()
        conn.close()
        return redirect(url_for('car_management'))

    # Ambil data mobil untuk ditampilkan di tabel
    conn = get_db_connection()
    cars = conn.execute('SELECT * FROM cars').fetchall()
    conn.close()

    return render_template('car_management.html', cars=cars, username=session['username'])




@app.route('/delete_car/<int:car_id>', methods=['POST'])
@login_required
def delete_car(car_id):
    conn = get_db_connection()

    # Ambil path gambar sebelum menghapus data
    car = conn.execute('SELECT image_path FROM cars WHERE id = ?', (car_id,)).fetchone()
    if car and car['image_path']:
        image_path = car['image_path']
        # Tentukan path lengkap gambar
        full_image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_path)
        
        # Hapus file gambar jika ada
        if os.path.exists(full_image_path):
            os.remove(full_image_path)

    # Hapus data mobil dari database
    conn.execute('DELETE FROM cars WHERE id = ?', (car_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('car_management'))

@app.route('/get_car/<int:car_id>', methods=['GET'])
@login_required
def get_car(car_id):
    conn = get_db_connection()
    car = conn.execute(
        'SELECT id, name, driver_phone, description, image_path FROM cars WHERE id = ?',
        (car_id,)
    ).fetchone()
    conn.close()
    if car:
        return jsonify({
            'id': car['id'],
            'name': car['name'],
            'driver_phone': car['driver_phone'],
            'description': car['description'],
            'image_path': car['image_path']
        })
    else:
        return jsonify({'error': 'Mobil tidak ditemukan'}), 404



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
