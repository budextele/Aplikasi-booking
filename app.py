import sqlite3
from flask import Flask, render_template, redirect, url_for, request, session, jsonify
from functools import wraps
from flask import session, redirect, url_for
import os
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'secret_key'  # Ganti dengan secret key yang lebih aman
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # Lokasi file `app.py` atau `.exe`
DATABASE = os.path.join(BASE_DIR, 'instance', 'database.db')  # Gabungkan jalur absolut ke database

#code trial
# TRIAL_END_DATE = datetime.strptime('30/11/2024', '%d/%m/%Y')  # Tanggal akhir trial
#end code trial

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
        
        #code trial
        # if datetime.now() > TRIAL_END_DATE:
        #     session.clear()  # Hapus semua data sesi
        #     return redirect(url_for('login', error='Masa trial berakhir.'))
        #end code trial
        
        return f(*args, **kwargs)
    return decorated_function

# UPLOAD_FOLDER = 'static/picture'
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'picture') 
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



# Halaman login
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None  # Variabel untuk menyimpan pesan kesalahan

    #code trial
    # if datetime.now() > TRIAL_END_DATE:
    #     error = 'Masa trial berakhir.'
    #     return render_template('login.html', error=error)
    #end code trial

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
            error = 'Username atau password salah.'
    
    return render_template('login.html', error=error)
## Batas Akhir Halaman Login

# Halaman utama
@app.route('/main')
def main():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('main.html', username=session['username'])
## Batas Akhir Utama

# Halaman dashboard
@app.route('/dashboard/')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

@app.route('/api/active_bookings', methods=['GET'])
@login_required
def active_bookings():
    conn = get_db_connection()
    today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Query untuk booking ruangan yang masih aktif
    room_bookings = conn.execute('''
        SELECT 
            b.id AS booking_id,
            r.name AS room_name,
            b.pic_name,
            b.start_time,
            b.end_time,
            b.description,
            b.time_booking,
            b.status
        FROM bookings b
        JOIN rooms r ON b.item_id = r.id
        WHERE b.item_type = 'room' AND b.end_time >= ? AND b.status = 'active'
    ''', (today,)).fetchall()
    
    # Query untuk booking mobil yang masih aktif
    car_bookings = conn.execute('''
        SELECT 
            b.id AS booking_id,
            c.name AS car_name,
            c.driver_phone,
            b.pic_name,
            b.start_time,
            b.end_time,
            b.description,
            b.time_booking,
            b.status,
            bl.label AS booking_label
        FROM bookings b
        JOIN cars c ON b.item_id = c.id
        LEFT JOIN bookings_label bl ON b.booking_type = bl.id
        WHERE b.item_type = 'car' AND b.end_time >= ? AND b.status = 'active'
    ''', (today,)).fetchall()
    
    conn.close()

    # Format data untuk dikirim ke frontend
    room_data = [dict(row) for row in room_bookings]
    car_data = [dict(row) for row in car_bookings]

    return jsonify({
        'rooms': room_data,
        'cars': car_data
    })

@app.route('/api/active_booking_count', methods=['GET'])
@login_required
def active_booking_count():
    conn = get_db_connection()
    today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Hitung jumlah booking ruangan aktif
    active_rooms_count = conn.execute('''
        SELECT COUNT(*) AS count
        FROM bookings
        WHERE item_type = 'room' AND end_time >= ? AND status = 'active'
    ''', (today,)).fetchone()['count']
    
    # Hitung jumlah booking mobil aktif
    active_cars_count = conn.execute('''
        SELECT COUNT(*) AS count
        FROM bookings
        WHERE item_type = 'car' AND end_time >= ? AND status = 'active'
    ''', (today,)).fetchone()['count']
    
    conn.close()
    return jsonify({
        'active_rooms_count': active_rooms_count,
        'active_cars_count': active_cars_count
    })

## Batas Akhir Halaman Dashboard

# Halaman Car Management
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
                    'INSERT INTO cars (name, driver_phone, description, image_path, status) VALUES (?, ?, ?, ?, "active")',
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
    cars = conn.execute('SELECT * FROM cars WHERE status = "active"').fetchall()
    conn.close()

    return render_template('car_management.html', cars=cars, username=session['username'])

#tombol delete
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
    conn.execute('UPDATE cars SET status = "deleted" WHERE id = ?', (car_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('car_management'))

#tombol select
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
## batas akhir Halaman Car Management

# Halaman Room Management
@app.route('/room_management/', methods=['GET', 'POST'])
@login_required
def room_management():
    if request.method == 'POST':
        room_id = request.form.get('roomId')  # Ambil ID ruangan dari form (jika ada)
        room_name = request.form['roomName']
        description = request.form['description']
        room_image = request.files['roomImage']

        conn = get_db_connection()

        if room_id:  # Jika ID ruangan tersedia, lakukan update
            cur = conn.execute('SELECT name, image_path FROM rooms WHERE id = ?', (room_id,))
            existing_room = cur.fetchone()

            if existing_room:
                old_name = existing_room['name']
                old_image_path = existing_room['image_path']

                # Jika nama ruangan berubah, rename file gambar jika ada
                if old_name != room_name and old_image_path:
                    old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], old_image_path)
                    extension = old_image_path.rsplit('.', 1)[1].lower()
                    new_filename = f"{room_id}_{room_name.replace(' ', '_')}.{extension}"
                    new_file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)

                    # Rename file di filesystem
                    if os.path.exists(old_file_path):
                        os.rename(old_file_path, new_file_path)

                    # Update path gambar di database
                    conn.execute(
                        'UPDATE rooms SET image_path = ? WHERE id = ?',
                        (new_filename, room_id)
                    )

                # Jika ada gambar baru yang diunggah
                if room_image and allowed_file(room_image.filename):
                    # Hapus gambar lama jika ada
                    if old_image_path:
                        old_file_path = os.path.join(app.config['UPLOAD_FOLDER'], old_image_path)
                        if os.path.exists(old_file_path):
                            os.remove(old_file_path)

                    # Simpan gambar baru
                    extension = room_image.filename.rsplit('.', 1)[1].lower()
                    new_filename = f"{room_id}_{room_name.replace(' ', '_')}.{extension}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                    room_image.save(file_path)

                    # Update database dengan data baru
                    conn.execute(
                        'UPDATE rooms SET image_path = ? WHERE id = ?',
                        (new_filename, room_id)
                    )

                # Update data lain (nama, keterangan)
                conn.execute(
                    'UPDATE rooms SET name = ?, description = ? WHERE id = ?',
                    (room_name, description, room_id)
                )

        else:  # Jika ID ruangan tidak tersedia, tambahkan data baru
            image_path = None
            if room_image and allowed_file(room_image.filename):
                cur = conn.execute(
                    'INSERT INTO rooms (name, description, image_path, status) VALUES (?, ?, ?, "active")',
                    (room_name, description, None)
                )
                room_id = cur.lastrowid
                conn.commit()

                # Rename dan simpan gambar
                extension = room_image.filename.rsplit('.', 1)[1].lower()
                new_filename = f"{room_id}_{room_name.replace(' ', '_')}.{extension}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                room_image.save(file_path)

                # Update path gambar di database
                conn.execute(
                    'UPDATE rooms SET image_path = ? WHERE id = ?',
                    (new_filename, room_id)
                )
            else:
                conn.execute(
                    'INSERT INTO rooms (name, description) VALUES (?, ?)',
                    (room_name, description)
                )

        conn.commit()
        conn.close()
        return redirect(url_for('room_management'))

    # Ambil data ruangan untuk ditampilkan di tabel
    conn = get_db_connection()
    rooms = conn.execute('SELECT * FROM rooms WHERE status = "active"').fetchall()
    conn.close()

    return render_template('room_management.html', rooms=rooms, username=session['username'])

#tombol delete
@app.route('/delete_room/<int:room_id>', methods=['POST'])
@login_required
def delete_room(room_id):
    conn = get_db_connection()

    # Ambil path gambar sebelum menghapus data
    room = conn.execute('SELECT image_path FROM rooms WHERE id = ?', (room_id,)).fetchone()
    if room and room['image_path']:
        image_path = room['image_path']
        # Tentukan path lengkap gambar
        full_image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_path)
        
        # Hapus file gambar jika ada
        if os.path.exists(full_image_path):
            os.remove(full_image_path)

    # Hapus data ruangan dari database
    conn.execute('UPDATE rooms SET status = "deleted" WHERE id = ?', (room_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('room_management'))

#tombol select
@app.route('/get_room/<int:room_id>', methods=['GET'])
@login_required
def get_room(room_id):
    conn = get_db_connection()
    room = conn.execute(
        'SELECT id, name, description, image_path FROM rooms WHERE id = ?',
        (room_id,)
    ).fetchone()
    conn.close()
    if room:
        return jsonify({
            'id': room['id'],
            'name': room['name'],
            'description': room['description'],
            'image_path': room['image_path']
        })
    else:
        return jsonify({'error': 'Ruangan tidak ditemukan'}), 404
## Batas akhir Halaman Room Management

# Validasi: Periksa jadwal booking mobil bentrok dengan booking lain
def is_schedule_conflicting(conn, car_id, start_time, end_time, booking_id=None):
    """
    Memeriksa apakah jadwal baru bentrok dengan jadwal yang sudah ada.
    Mengembalikan detail booking yang bertabrakan jika ditemukan, atau None jika tidak ada bentrok.
    """
    query = """
        SELECT b.id, b.start_time, b.end_time
        FROM bookings b
        WHERE b.item_id = ? AND b.item_type = 'car'
          AND (
            (b.start_time < ? AND b.end_time > ?) OR  -- Overlap sebagian
            (b.start_time >= ? AND b.end_time <= ?) OR  -- Overlap penuh
            (b.start_time <= ? AND b.end_time >= ?)    -- Overlap luar
          )
    """
    params = (car_id, end_time, start_time, start_time, end_time, start_time, end_time)

    # Jika ini update, abaikan jadwal dengan booking_id yang sama
    if booking_id:
        query += " AND b.id != ?"
        params += (booking_id,)

    conflicting_booking = conn.execute(query, params).fetchone()
    return conflicting_booking  # Mengembalikan data booking yang bertabrakan (sqlite3.Row) atau None


# Halaman Car Booking
@app.route('/car_booking', methods=['GET', 'POST'])
def car_booking():
    conn = get_db_connection()
    cars = conn.execute('SELECT id, name, driver_phone, image_path FROM cars WHERE status = "active"').fetchall()  # Ambil data mobil
    bookings_label = conn.execute('SELECT id, label FROM bookings_label').fetchall()  # Ambil data bookings label

    # Ambil semua data booking mobil
    bookings_raw = conn.execute(
        """
        SELECT 
            b.id, 
            b.time_booking, 
            c.name AS car_name, 
            b.pic_name, 
            c.driver_phone, 
            b.start_time, 
            b.end_time, 
            b.description, 
            bl.label AS booking_label
        FROM bookings b
        JOIN cars c ON b.item_id = c.id
        LEFT JOIN bookings_label bl ON b.booking_type = bl.id
        WHERE b.item_type = 'car' 
        AND b.status = 'active';
        """
    ).fetchall()

    # Konversi data menjadi list of dictionaries dan format waktu
    bookings = []
    for row in bookings_raw:
        booking = dict(row)  # Ubah sqlite3.Row menjadi dictionary
        booking['time_booking'] = datetime.strptime(booking['time_booking'], "%Y-%m-%d %H:%M:%S").strftime("%d %B %Y, %H:%M")
        booking['start_time'] = datetime.strptime(booking['start_time'], "%Y-%m-%dT%H:%M").strftime("%d %B %Y, %H:%M")
        booking['end_time'] = datetime.strptime(booking['end_time'], "%Y-%m-%dT%H:%M").strftime("%d %B %Y, %H:%M")
        bookings.append(booking)

    # Handle POST request (insert/update booking)
    if request.method == 'POST':
        # Ambil data dari form
        booking_id = request.form.get('bookingId')  # Nilai akan kosong jika data baru
        car_id = request.form['carName']
        pic_name = request.form['namaPIC']
        booking_type_id = request.form['bookingType']
        start_time = request.form['waktuMulai']
        end_time = request.form['waktuSelesai']
        description = request.form.get('description', '')

        # Validasi bentrok jadwal
        conflicting_booking = is_schedule_conflicting(conn, car_id, start_time, end_time, booking_id)
        if conflicting_booking:  # Jika ada jadwal yang bentrok
            overlap_start = conflicting_booking['start_time']
            overlap_end = conflicting_booking['end_time']
            message = f"Jadwal bentrok dengan booking ID {conflicting_booking['id']}: {overlap_start} - {overlap_end}"
            conn.close()
            return jsonify({
                'status': 'error',
                'message': message,
            }), 400  # HTTP status code 400 untuk error validasi

        if booking_id:
            # Update data booking jika bookingId tidak kosong
            conn.execute(
                """
                UPDATE bookings
                SET item_id = ?, pic_name = ?, start_time = ?, end_time = ?, description = ?, booking_type = ?
                WHERE id = ?
                """,
                (car_id, pic_name, start_time, end_time, description, booking_type_id, booking_id)
            )
            success_message = "Booking berhasil diperbarui."
        else:
            # Insert data booking baru jika bookingId kosong
            conn.execute(
                """
                INSERT INTO bookings (item_type, item_id, pic_name, start_time, end_time, description, booking_type, status)
                VALUES ('car', ?, ?, ?, ?, ?, ?, 'active')
                """,
                (car_id, pic_name, start_time, end_time, description, booking_type_id)
            )
            success_message = "Booking berhasil disimpan."

        conn.commit()
        conn.close()

        # # Redirect atau tampilkan pesan sukses
        # return render_template('car_booking.html', cars=cars, bookings=bookings, success=success_message)
        # Kembalikan respons JSON untuk sukses
        return jsonify({
            'status': 'success',
            'message': success_message,
        }), 200  # HTTP status code 200 untuk sukses

    conn.close()
    return render_template('car_booking.html', cars=cars, bookings=bookings, bookings_label=bookings_label)

#cancel booking mobil
@app.route('/cancel_booking', methods=['POST'])
def cancel_booking():
    booking_id = request.form.get('bookingId')
    cancel_reason = request.form.get('cancelReason')

    # Validasi data
    if not booking_id or not cancel_reason:
        return jsonify({"success": False, "message": "ID atau alasan pembatalan tidak valid."}), 400

    # Perbarui status booking menjadi "cancelled" dan tambahkan alasan pembatalan
    conn = get_db_connection()
    conn.execute(
        """
        UPDATE bookings 
        SET status = 'cancelled', cancel_reason = ? 
        WHERE id = ?
        """,
        (cancel_reason, booking_id)
    )
    conn.commit()
    conn.close()

    # return jsonify({"success": True, "message": "Pembatalan berhasil dilakukan."})
    return jsonify({
        'status': 'success',
        'message': f'Booking dengan ID {booking_id} berhasil dibatalkan.'
    })

# Select booking
@app.route('/get_booking/<int:booking_id>', methods=['GET'])
@login_required
def get_booking(booking_id):
    conn = get_db_connection()
    # Ambil data booking berdasarkan ID booking
    booking = conn.execute(
        '''
        SELECT 
            b.id AS booking_id, 
            c.id AS car_id, 
            c.name AS car_name, 
            c.driver_phone, 
            b.pic_name, 
            b.start_time, 
            b.end_time, 
            b.description, 
            c.image_path,
            bl.id AS booking_label_id, 
            bl.label AS booking_label
        FROM bookings b
        JOIN cars c ON b.item_id = c.id
        LEFT JOIN bookings_label bl ON b.booking_type = bl.id
        WHERE b.id = ? 
        AND b.item_type = 'car'
        ''',
        (booking_id,)
    ).fetchone()
    conn.close()

    #Debugging: Cetak hasil query
    if booking:
        # print("Hasil Query:", dict(booking))  # Debugging untuk memastikan hasil query
        return jsonify({
            "booking_id": booking['booking_id'],  # ID booking
            "car_id": booking['car_id'],         # ID mobil
            "car_name": booking['car_name'],     # Nama mobil
            "driver_phone": booking['driver_phone'],  # No. telepon driver
            "pic_name": booking['pic_name'] or '',    # Nama PIC
            "start_time": booking['start_time'] or '',  # Waktu mulai
            "end_time": booking['end_time'] or '',      # Waktu selesai
            "description": booking['description'] or '',  # Keterangan
            "image_path": booking['image_path'] or '',  # Path gambar
            "booking_label_id": booking['booking_label_id'] or '', #id booking labels
            "booking_label": booking['booking_label'] or '', #label
            "error": None
        })
    else:
        # Jika data booking tidak ditemukan
        # print("Error: Data booking tidak ditemukan untuk ID:", booking_id)  # Debugging
        return jsonify({'error': 'Data booking tidak ditemukan'}), 404
## Batas akhir Halaman Car Booking

# Validasi: Periksa jadwal booking ruangan bentrok dengan booking lain
def is_schedule_conflicting2(conn, room_id, start_time, end_time, booking_id=None):
    """
    Memeriksa apakah jadwal baru bentrok dengan jadwal yang sudah ada.
    Mengembalikan detail booking yang bertabrakan jika ditemukan, atau None jika tidak ada bentrok.
    """
    query = """
        SELECT b.id, b.start_time, b.end_time
        FROM bookings b
        WHERE b.item_id = ? AND b.item_type = 'room'
          AND (
            (b.start_time < ? AND b.end_time > ?) OR  -- Overlap sebagian
            (b.start_time >= ? AND b.end_time <= ?) OR  -- Overlap penuh
            (b.start_time <= ? AND b.end_time >= ?)    -- Overlap luar
          )
    """
    params = (room_id, end_time, start_time, start_time, end_time, start_time, end_time)

    # Jika ini update, abaikan jadwal dengan booking_id yang sama
    if booking_id:
        query += " AND b.id != ?"
        params += (booking_id,)

    conflicting_booking = conn.execute(query, params).fetchone()
    return conflicting_booking  # Mengembalikan data booking yang bertabrakan (sqlite3.Row) atau None

# Halaman Room Booking
@app.route('/room_booking/', methods=['GET', 'POST'])
def room_booking():
    # if not session.get('logged_in'):
    #     return redirect(url_for('login'))
    # return render_template('room_booking.html', username=session['username'])
    conn = get_db_connection()
    rooms = conn.execute('SELECT id, name, image_path FROM rooms WHERE status = "active"').fetchall()  # Ambil data ruangan

    # Ambil semua data booking ruangan
    bookings_raw = conn.execute(
        """
        SELECT 
            b.id, 
            b.time_booking, 
            r.name AS room_name, 
            b.pic_name,  
            b.start_time, 
            b.end_time, 
            b.description 
        FROM bookings b
        JOIN rooms r ON b.item_id = r.id
        WHERE b.item_type = 'room' AND b.status = 'active'
        """
    ).fetchall()

    # Konversi data menjadi list of dictionaries dan format waktu
    bookings = []
    for row in bookings_raw:
        booking = dict(row)  # Ubah sqlite3.Row menjadi dictionary
        booking['time_booking'] = datetime.strptime(booking['time_booking'], "%Y-%m-%d %H:%M:%S").strftime("%d %B %Y, %H:%M")
        booking['start_time'] = datetime.strptime(booking['start_time'], "%Y-%m-%dT%H:%M").strftime("%d %B %Y, %H:%M")
        booking['end_time'] = datetime.strptime(booking['end_time'], "%Y-%m-%dT%H:%M").strftime("%d %B %Y, %H:%M")
        bookings.append(booking)

    # Handle POST request (insert/update booking)
    if request.method == 'POST':
        # Ambil data dari form
        booking_id = request.form.get('bookingId')  # Nilai akan kosong jika data baru
        room_id = request.form['roomName']
        pic_name = request.form['namaPIC']
        start_time = request.form['waktuMulai']
        end_time = request.form['waktuSelesai']
        description = request.form.get('description', '')

        # Validasi bentrok jadwal
        conflicting_booking = is_schedule_conflicting2(conn, room_id, start_time, end_time, booking_id)
        if conflicting_booking:  # Jika ada jadwal yang bentrok
            overlap_start = conflicting_booking['start_time']
            overlap_end = conflicting_booking['end_time']
            message = f"Jadwal bentrok dengan booking ID {conflicting_booking['id']}: {overlap_start} - {overlap_end}"
            conn.close()
            return jsonify({
                'status': 'error',
                'message': message,
            }), 400  # HTTP status code 400 untuk error validasi
        
        if booking_id:
            # Update data booking jika bookingId tidak kosong
            conn.execute(
                """
                UPDATE bookings
                SET item_id = ?, pic_name = ?, start_time = ?, end_time = ?, description = ?
                WHERE id = ?
                """,
                (room_id, pic_name, start_time, end_time, description, booking_id)
            )
            success_message = "Booking berhasil diperbarui."
        else:
            # Insert data booking baru jika bookingId kosong
            conn.execute(
                """
                INSERT INTO bookings (item_type, item_id, pic_name, start_time, end_time, description, status)
                VALUES ('room', ?, ?, ?, ?, ?, 'active')
                """,
                (room_id, pic_name, start_time, end_time, description)
            )
            success_message = "Booking berhasil disimpan."

        conn.commit()
        conn.close()

        return jsonify({
            'status': 'success',
            'message': success_message,
        }), 200  # HTTP status code 200 untuk sukses
    
    conn.close()
    return render_template('room_booking.html', rooms=rooms, bookings=bookings)

#cancel booking ruangan
@app.route('/cancel_booking2', methods=['POST'])
def cancel_booking2():
    booking_id = request.form.get('bookingId')
    cancel_reason = request.form.get('cancelReason')

    # Validasi data
    if not booking_id or not cancel_reason:
        return jsonify({"success": False, "message": "ID atau alasan pembatalan tidak valid."}), 400

    # Perbarui status booking menjadi "cancelled" dan tambahkan alasan pembatalan
    conn = get_db_connection()
    conn.execute(
        """
        UPDATE bookings 
        SET status = 'cancelled', cancel_reason = ? 
        WHERE id = ?
        """,
        (cancel_reason, booking_id)
    )
    conn.commit()
    conn.close()

    # return jsonify({"success": True, "message": "Pembatalan berhasil dilakukan."})
    return jsonify({
        'status': 'success',
        'message': f'Booking dengan ID {booking_id} berhasil dibatalkan.'
    })

# Select booking ruangan
@app.route('/get_booking2/<int:booking_id>', methods=['GET'])
@login_required
def get_booking2(booking_id):
    conn = get_db_connection()
    # Ambil data booking berdasarkan ID booking
    booking = conn.execute(
        '''
        SELECT 
            b.id AS booking_id, 
            r.id AS room_id, 
            r.name AS room_name,  
            b.pic_name, 
            b.start_time, 
            b.end_time, 
            b.description, 
            r.image_path 
        FROM bookings b
        JOIN rooms r ON b.item_id = r.id
        WHERE b.id = ? AND b.item_type = 'room'
        ''',
        (booking_id,)
    ).fetchone()
    conn.close()

    #Debugging: Cetak hasil query
    if booking:
        # print("Hasil Query:", dict(booking))  # Debugging untuk memastikan hasil query
        return jsonify({
            "booking_id": booking['booking_id'],  # ID booking
            "room_id": booking['room_id'],         # ID ruangan
            "room_name": booking['room_name'],     # Nama ruangan
            "pic_name": booking['pic_name'] or '',    # Nama PIC
            "start_time": booking['start_time'] or '',  # Waktu mulai
            "end_time": booking['end_time'] or '',      # Waktu selesai
            "description": booking['description'] or '',  # Keterangan
            "image_path": booking['image_path'] or '',  # Path gambar
            "error": None
        })
    else:
        # Jika data booking tidak ditemukan
        # print("Error: Data booking tidak ditemukan untuk ID:", booking_id)  # Debugging
        return jsonify({'error': 'Data booking tidak ditemukan'}), 404
## Batas akhir Room Booking


# Halaman Report
@app.route('/report/')
def report():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('report.html', username=session['username'])

@app.route('/api/reports', methods=['GET'])
def get_reports():
    # Ambil parameter dari URL
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    report_type = request.args.get('report_type')

    if not (start_date and end_date and report_type):
        return jsonify({"error": "Semua parameter harus diisi"}), 400

    try:
        # Validasi format tanggal
        start_of_day = f"{start_date} 00:00:00"
        end_of_day = f"{end_date} 23:59:59"
        datetime.strptime(start_of_day, "%Y-%m-%d %H:%M:%S")
        datetime.strptime(end_of_day, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return jsonify({"error": "Format tanggal tidak valid"}), 400

    # Buat query SQL berdasarkan tipe laporan
    if report_type == 'mobil':
        query = f"""
        SELECT 
            b.id, b.time_booking, c.name AS car_name, c.driver_phone, b.pic_name,
            b.start_time, b.end_time, b.status, b.cancel_reason, b.description, bl.label AS booking_label
        FROM bookings b
        JOIN cars c ON b.item_id = c.id
        LEFT JOIN bookings_label bl ON b.booking_type = bl.id
        WHERE b.item_type = 'car' AND (
            (DATETIME(b.start_time) BETWEEN ? AND ?) OR
            (DATETIME(b.end_time) BETWEEN ? AND ?) OR
            (DATETIME(b.start_time) <= ? AND DATETIME(b.end_time) >= ?)
        )
        """
    elif report_type == 'ruangan':
        query = f"""
        SELECT 
            b.id, b.time_booking, r.name AS room_name, b.pic_name,
            b.start_time, b.end_time, b.status, b.cancel_reason, b.description
        FROM bookings b
        JOIN rooms r ON b.item_id = r.id
        WHERE b.item_type = 'room' AND (
            (DATETIME(b.start_time) BETWEEN ? AND ?) OR
            (DATETIME(b.end_time) BETWEEN ? AND ?) OR
            (DATETIME(b.start_time) <= ? AND DATETIME(b.end_time) >= ?)
        )
        """
    else:
        return jsonify({"error": "Tipe laporan tidak valid"}), 400

    params = [start_of_day, end_of_day, start_of_day, end_of_day, start_of_day, end_of_day]

    # Eksekusi query
    try:
        conn = get_db_connection()
        cursor = conn.execute(query, params)
        data = cursor.fetchall()
    except sqlite3.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

    # Ubah hasil query ke format JSON
    result = [dict(row) for row in data]
    return jsonify(result)
## Batas akhir Halaman Report

#......................................................................

# Logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
