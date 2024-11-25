PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Hapus tabel jika sudah ada
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS cars;
DROP TABLE IF EXISTS rooms;
DROP TABLE IF EXISTS bookings;

-- Users Table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);

-- Cars Table
CREATE TABLE cars (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    driver_phone TEXT,
    description TEXT,
    image_path TEXT -- Menyimpan path file gambar mobil
);

-- Rooms Table
CREATE TABLE rooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    image_path TEXT -- Menyimpan path file gambar ruangan
);

-- Bookings Table
CREATE TABLE bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_type TEXT NOT NULL CHECK (item_type IN ('car', 'room')), -- Hanya 'car' atau 'room'
    item_id INTEGER NOT NULL,
    pic_name TEXT NOT NULL,       -- Nama PIC
    start_time TEXT NOT NULL,     -- Waktu mulai
    end_time TEXT NOT NULL,       -- Waktu berakhir
    description TEXT,             -- Keterangan tambahan
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'cancelled')), -- Validasi status
    cancel_reason TEXT DEFAULT NULL, -- Alasan pembatalan (jika ada)
    FOREIGN KEY (item_id)
        REFERENCES cars (id) ON DELETE CASCADE -- Validasi secara dinamis
        DEFERRABLE INITIALLY DEFERRED
);

-- Tambahkan user admin
INSERT INTO users (username, password)
VALUES ('admin', 'admin123');

COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
