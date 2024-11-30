--
-- File generated with SQLiteStudio v3.4.4 on Fri Nov 15 19:57:32 2024
--
-- Text encoding used: System
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: bookings
CREATE TABLE IF NOT EXISTS bookings (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    item_type     TEXT    NOT NULL,-- 'car' or 'room'
    item_id       INTEGER NOT NULL,
    pic_name      TEXT    NOT NULL,
    start_time    TEXT    NOT NULL,
    end_time      TEXT    NOT NULL,
    description   TEXT,
    status        TEXT    DEFAULT 'active',-- 'active' or 'cancelled'
    cancel_reason TEXT    DEFAULT NULL,
    FOREIGN KEY (
        item_id
    )
    REFERENCES cars (id) ON DELETE CASCADE
);


-- Table: cancellations
CREATE TABLE IF NOT EXISTS cancellations (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id    INTEGER NOT NULL,
    cancel_reason TEXT    NOT NULL,
    cancel_time   TEXT    NOT NULL
                          DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (
        booking_id
    )
    REFERENCES bookings (id) ON DELETE CASCADE
);


-- Table: cars
CREATE TABLE IF NOT EXISTS cars (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL,
    driver_phone TEXT,
    description  TEXT,
    image        BLOB
);


-- Table: rooms
CREATE TABLE IF NOT EXISTS rooms (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    description TEXT,
    image       BLOB
);


-- Table: users
CREATE TABLE IF NOT EXISTS users (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT    NOT NULL
                     UNIQUE,
    password TEXT    NOT NULL
);

INSERT INTO users (
                      id,
                      username,
                      password
                  )
                  VALUES (
                      1,
                      'admin',
                      'admin123'
                  );


COMMIT TRANSACTION;
PRAGMA foreign_keys = on;
