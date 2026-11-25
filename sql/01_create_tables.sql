-- PeerDesk (CS355 Group 12): CREATE TABLE statements for Microsoft SQL Server.
-- Same tables, columns, keys and constraints as the relational schema in InterimDemo_Group_12.pdf.
-- Primary keys use IDENTITY(1,1) so the database numbers new rows itself
-- (the INSERT queries in the app leave the ID out).
-- Tables are created parents-first so every foreign key points to a table that already exists.

-- Three separate account tables, one per role. email is UNIQUE so an email can only
-- register once per role (the Sign up screen checks this first with SQL Query 1.A.1).
CREATE TABLE administrator (
    admin_id INT IDENTITY(1,1) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(50) NOT NULL
);
GO

CREATE TABLE tutor (
    tutor_id INT IDENTITY(1,1) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(50) NOT NULL,
    bio VARCHAR(MAX),
    joined_at DATETIME2 DEFAULT CURRENT_TIMESTAMP
);
GO

CREATE TABLE client (
    client_id INT IDENTITY(1,1) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(50) NOT NULL,
    batch INT,
    joined_at DATETIME2 DEFAULT CURRENT_TIMESTAMP
);
GO

-- A category is created by an administrator (foreign key admin_id).
-- name is UNIQUE (no two categories with the same name); the CHECK constraint only allows
-- three types. is_active is a BIT (1 = active, 0 = deactivated); rows are never deleted.
CREATE TABLE category (
    category_id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    type VARCHAR(20) NOT NULL CHECK (type IN ('Academic', 'Design', 'Coding')),
    is_active BIT NOT NULL DEFAULT 1,
    admin_id INT NOT NULL,
    CONSTRAINT fk_category_admin FOREIGN KEY (admin_id) REFERENCES administrator(admin_id)
);
GO

-- A service a tutor offers, in one category. Each listing belongs to exactly one tutor and
-- one category (two foreign keys). CHECK stops a zero or negative rate.
CREATE TABLE service_listing (
    listing_id INT IDENTITY(1,1) PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    description VARCHAR(MAX),
    rate_per_hour DECIMAL(8, 2) NOT NULL CHECK (rate_per_hour > 0),
    is_active BIT NOT NULL DEFAULT 1,
    created_at DATETIME2 DEFAULT CURRENT_TIMESTAMP,
    tutor_id INT NOT NULL,
    category_id INT NOT NULL,
    CONSTRAINT fk_listing_tutor FOREIGN KEY (tutor_id) REFERENCES tutor(tutor_id),
    CONSTRAINT fk_listing_category FOREIGN KEY (category_id) REFERENCES category(category_id)
);
GO

-- A time a tutor is available for one listing. Two kinds of slot:
--   recurring: is_recurring = 1, day_of_week = 'Monday', slot_date = NULL (every week)
--   one-off:   is_recurring = 0, slot_date = a single date
-- chk_slot_times makes sure a slot ends after it starts.
CREATE TABLE time_slot (
    slot_id INT IDENTITY(1,1) PRIMARY KEY,
    day_of_week VARCHAR(10),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_recurring BIT NOT NULL,
    slot_date DATE,
    listing_id INT NOT NULL,
    CONSTRAINT chk_slot_times CHECK (end_time > start_time),
    CONSTRAINT fk_slot_listing FOREIGN KEY (listing_id) REFERENCES service_listing(listing_id)
);
GO

-- A client booking one slot on one date. total_price = rate_per_hour x duration_hrs,
-- worked out by the INSERT in SQL Query 5.B.3. status is 'Confirmed' or 'Completed'.
-- uq_slot_date: the same slot cannot be booked twice on the same date. This is what
-- prevents double bookings, even if two clients click Confirm at the same moment.
CREATE TABLE booking (
    booking_id INT IDENTITY(1,1) PRIMARY KEY,
    session_date DATE NOT NULL,
    requirements VARCHAR(MAX),
    duration_hrs DECIMAL(3, 1) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Confirmed',
    created_at DATETIME2 DEFAULT CURRENT_TIMESTAMP,
    client_id INT NOT NULL,
    slot_id INT NOT NULL,
    CONSTRAINT uq_slot_date UNIQUE (slot_id, session_date),
    CONSTRAINT fk_booking_client FOREIGN KEY (client_id) REFERENCES client(client_id),
    CONSTRAINT fk_booking_slot FOREIGN KEY (slot_id) REFERENCES time_slot(slot_id)
);
GO
