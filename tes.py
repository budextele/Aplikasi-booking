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
                    'INSERT INTO rooms (name, description, image_path) VALUES (?, ?, ?)',
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
    rooms = conn.execute('SELECT * FROM rooms').fetchall()
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
    conn.execute('DELETE FROM rooms WHERE id = ?', (room_id,))
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