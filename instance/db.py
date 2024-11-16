import sqlite3
import os

# Path ke database
db_path = 'instance/database.db'  # Sesuaikan dengan path ke database yang diinginkan
schema_path = 'schema.sql'         # Path ke file schema.sql

def create_db():
    # Membuat direktori 'instance' jika belum ada
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Menghubungkan ke database SQLite (akan membuat database baru jika belum ada)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Membaca file schema.sql
    with open(schema_path, 'r') as schema_file:
        schema_sql = schema_file.read()

    # Eksekusi schema SQL untuk membuat tabel
    try:
        cursor.executescript(schema_sql)
        print("Database and tables created successfully.")
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        # Commit perubahan dan tutup koneksi
        conn.commit()
        conn.close()

if __name__ == "__main__":
    create_db()
