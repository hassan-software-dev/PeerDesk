"""Every SQL query PeerDesk runs, in SQL Server (T-SQL) syntax.

WHY ALL THE SQL IS IN ONE FILE
------------------------------
Keeping every query here (instead of scattered through the screen code) means you can read
and explain the whole database side of the app in one place. The screen files only say
*which* query to run and *which values* to give it.

NAMING
------
The names match section 6 (SQL) of InterimDemo_Group_12.pdf:
    Q_2A1  =  "SQL Query 2.A.1"  =  UI Screen 2.A, query number 1.
Search the screens folder for "Q_2A1" to find where a query is used.

THE "?" PLACEHOLDERS
--------------------
"?" marks a parameter. The screen passes the actual value (what the user typed) in a tuple,
in the same order as the "?"s appear. pyodbc sends the values separately from the SQL text,
so user input can never change the query itself (no SQL injection).

T-SQL NOTES (differences from the wording in the PDF)
-----------------------------------------------------
* SQL Server has no TRUE/FALSE keywords. BIT columns (is_active, is_recurring) store 1 and 0.
* "OUTPUT INSERTED.<id>" makes an INSERT return the ID that SQL Server generated for the new
  row (the primary keys are IDENTITY columns, so the database numbers rows itself).
* CURRENT_TIMESTAMP is the current date and time; CAST(GETDATE() AS DATE) is today's date.
"""

# ===========================================================================
# FR1  UI Screen 1.A: Sign up
# ===========================================================================
# Clients, tutors and administrators are stored in three separate tables, so each query
# below comes in three versions. They are stored in a dictionary keyed by the role name,
# so the screen can pick the right one with Q_1A1[role].

# 1.A.1  Is this email already registered for the selected role?
#        A count of 0 means the account can be created.
Q_1A1 = {
    "Client": """SELECT COUNT(*) AS existing_accounts
FROM client
WHERE email = ?;""",
    "Tutor": """SELECT COUNT(*) AS existing_accounts
FROM tutor
WHERE email = ?;""",
    "Administrator": """SELECT COUNT(*) AS existing_accounts
FROM administrator
WHERE email = ?;""",
}

# 1.A.2  Create the account in the table of the selected role.
#        Only clients have a "batch" (graduation year), so the Client query has one more "?".
Q_1A2 = {
    "Client": """INSERT INTO client (full_name, email, password, batch, joined_at)
OUTPUT INSERTED.client_id
VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP);""",
    "Tutor": """INSERT INTO tutor (full_name, email, password, joined_at)
OUTPUT INSERTED.tutor_id
VALUES (?, ?, ?, CURRENT_TIMESTAMP);""",
    "Administrator": """INSERT INTO administrator (full_name, email, password)
OUTPUT INSERTED.admin_id
VALUES (?, ?, ?);""",
}

# ===========================================================================
# FR1  UI Screen 1.B: Log in
# ===========================================================================
# 1.B.1  Look for a row with this email AND password in the selected role's table.
#        One row back  -> the login is correct (we get the user's ID and name).
#        No row back   -> wrong email or password.
Q_1B1 = {
    "Client": """SELECT client_id, full_name
FROM client
WHERE email = ?
  AND password = ?;""",
    "Tutor": """SELECT tutor_id, full_name
FROM tutor
WHERE email = ?
  AND password = ?;""",
    "Administrator": """SELECT admin_id, full_name
FROM administrator
WHERE email = ?
  AND password = ?;""",
}

# ===========================================================================
# FR2  UI Screen 2.A: Admin - Manage Service Categories
# ===========================================================================
# 2.A.1  Add Category. admin_id is the logged-in administrator (foreign key to administrator).
#        Parameters: name, type, is_active, admin_id.
Q_2A1 = """INSERT INTO category (name, type, is_active, admin_id)
OUTPUT INSERTED.category_id
VALUES (?, ?, ?, ?);"""

# 2.A.2  Update: save the form (name, type and the Active tick box) to the selected category.
#        Parameters: name, type, is_active, category_id.
Q_2A2 = """UPDATE category
SET name = ?, type = ?, is_active = ?
WHERE category_id = ?;"""

# 2.A.3  Deactivate: a "soft delete". The row stays (old listings still point to it through
#        their foreign key) but is_active = 0 hides it from tutors creating new listings.
Q_2A3 = """UPDATE category
SET is_active = 0
WHERE category_id = ?;"""

# 2.A.4  Refresh the categories table. CASE turns the BIT 1/0 into the words Active/Inactive.
Q_2A4 = """SELECT category_id, type,
  CASE WHEN is_active = 1 THEN 'Active' ELSE 'Inactive' END AS status,
  name
FROM category
ORDER BY category_id;"""

# 2.A.5  Fill the Type drop-down. DISTINCT removes repeated values.
Q_2A5 = """SELECT DISTINCT type
FROM category
ORDER BY type;"""

# 2.A.6  A row was selected in the table: load that category into the form.
Q_2A6 = """SELECT category_id, name, type, is_active
FROM category
WHERE category_id = ?;"""

# ===========================================================================
# FR3  UI Screen 3.A: Tutor - Create a New Service Listing
# ===========================================================================
# 3.A.1  Fill the Category drop-down with ACTIVE categories only.
Q_3A1 = """SELECT category_id, name
FROM category
WHERE is_active = 1
ORDER BY name;"""

# 3.A.2  Save Listing: insert a new listing for the logged-in tutor.
#        Parameters: title, description, rate_per_hour, is_active, tutor_id, category_id.
Q_3A2 = """INSERT INTO service_listing
  (title, description, rate_per_hour, is_active, created_at, tutor_id, category_id)
OUTPUT INSERTED.listing_id
VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?);"""

# 3.A.3  Deactivate Selected. "AND tutor_id = ?" makes sure a tutor can only change
#        their OWN listings, even if they somehow pass another tutor's listing_id.
Q_3A3 = """UPDATE service_listing
SET is_active = 0
WHERE listing_id = ? AND tutor_id = ?;"""

# 3.A.4  Refresh the My Listings table. The JOIN brings in the category's name
#        (service_listing only stores category_id, the foreign key).
Q_3A4 = """SELECT l.listing_id, l.rate_per_hour,
  CASE WHEN l.is_active = 1 THEN 'Active' ELSE 'Inactive' END AS status,
  c.name AS category, l.title
FROM service_listing l
JOIN category c ON c.category_id = l.category_id
WHERE l.tutor_id = ?
ORDER BY l.listing_id;"""

# 3.A.5  Edit Selected: load the listing into the form (again only the tutor's own listing).
Q_3A5 = """SELECT l.listing_id, l.category_id, c.name AS category, l.rate_per_hour,
  l.is_active, l.title, l.description
FROM service_listing l
JOIN category c ON c.category_id = l.category_id
WHERE l.listing_id = ? AND l.tutor_id = ?;"""

# 3.A.6  Save Listing while editing: UPDATE the existing row instead of inserting a new one.
#        Parameters: category_id, rate, is_active, title, description, listing_id, tutor_id.
Q_3A6 = """UPDATE service_listing
SET category_id = ?, rate_per_hour = ?, is_active = ?,
  title = ?, description = ?
WHERE listing_id = ? AND tutor_id = ?;"""

# ===========================================================================
# FR4  UI Screen 4.A: Tutor - Manage Availability
# ===========================================================================
# 4.A.1  Fill the Service listing drop-down with the tutor's ACTIVE listings.
Q_4A1 = """SELECT listing_id, title
FROM service_listing
WHERE tutor_id = ? AND is_active = 1
ORDER BY title DESC;"""

# 4.A.2  Add Slot. There are two kinds of slot:
#          recurring (weekly): is_recurring = 1, day_of_week = 'Monday', slot_date = NULL
#          one-off:            is_recurring = 0, slot_date = '2026-11-14' (day_of_week also set)
#        Parameters: day_of_week, start_time, end_time, is_recurring, slot_date, listing_id.
Q_4A2 = """INSERT INTO time_slot
  (day_of_week, start_time, end_time, is_recurring, slot_date, listing_id)
OUTPUT INSERTED.slot_id
VALUES (?, ?, ?, ?, ?, ?);"""

# 4.A.3  Refresh the slots table for the selected listing.
Q_4A3 = """SELECT slot_id, start_time, end_time, is_recurring,
  day_of_week, slot_date
FROM time_slot
WHERE listing_id = ?
ORDER BY slot_id;"""

# 4.A.4  Remove Selected: delete a slot ONLY if no booking uses it.
#        NOT EXISTS (subquery) is true when the subquery returns no rows. If a booking exists,
#        nothing is deleted (0 rows changed) and the screen shows an error. This protects the
#        booking's foreign key to time_slot. slot_id is passed twice (once for each "?").
Q_4A4 = """DELETE FROM time_slot
WHERE slot_id = ?
  AND NOT EXISTS (SELECT 1 FROM booking b WHERE b.slot_id = ?);"""

# ===========================================================================
# FR4  UI Screen 4.B: Tutor - My Bookings
# ===========================================================================
# 4.B.1  Fill the Listing drop-down with ALL the tutor's listings (inactive ones too,
#        because old bookings can belong to a listing that has since been deactivated).
Q_4B1 = """SELECT listing_id, title
FROM service_listing
WHERE tutor_id = ?
ORDER BY title;"""

# 4.B.2  Show every booking on this tutor's slots.
#        A booking only knows its slot, so we JOIN booking -> time_slot -> service_listing
#        to reach the tutor_id, and JOIN client to get the client's name.
#
#        {filters} is NOT SQL. It is a Python placeholder that the screen replaces with
#        str.format() before running the query: either nothing, or one or both of the
#        optional filter lines below (each adds one more "?" parameter).
#        Only these fixed strings are ever inserted, never user text, so this is still safe.
Q_4B2 = """SELECT b.booking_id, b.session_date, s.start_time, s.end_time,
  cl.full_name AS client, l.title AS listing,
  b.duration_hrs, b.total_price, b.status
FROM booking b
JOIN time_slot s ON s.slot_id = b.slot_id
JOIN service_listing l ON l.listing_id = s.listing_id
JOIN client cl ON cl.client_id = b.client_id
WHERE l.tutor_id = ?
{filters}ORDER BY b.session_date, s.start_time;"""
Q_4B2_LISTING_FILTER = "  AND l.listing_id = ?\n"   # used when one listing is chosen
Q_4B2_STATUS_FILTER = "  AND b.status = ?\n"        # used when Confirmed/Completed is chosen

# 4.B.3  A booking was selected: show the client's email and the task requirements.
Q_4B3 = """SELECT b.booking_id, cl.full_name, cl.email, b.requirements
FROM booking b
JOIN client cl ON cl.client_id = b.client_id
WHERE b.booking_id = ?;"""

# 4.B.4  Mark Completed. The WHERE clause enforces the business rules in the database:
#          * the booking is still 'Confirmed' (cannot complete it twice),
#          * the session date has arrived (cannot complete a future session),
#          * the booking is on one of THIS tutor's slots (subquery with IN).
#        If any rule fails, 0 rows are updated and the screen shows an error.
#        Parameters: booking_id, tutor_id.
Q_4B4 = """UPDATE booking
SET status = 'Completed'
WHERE booking_id = ?
  AND status = 'Confirmed'
  AND session_date <= CAST(GETDATE() AS DATE)
  AND slot_id IN (SELECT s.slot_id
    FROM time_slot s
    JOIN service_listing l ON l.listing_id = s.listing_id
    WHERE l.tutor_id = ?);"""

# 4.B.5  Summary line. SUM(CASE ...) is "conditional aggregation": it counts / adds up only
#        the rows that match each condition, so one query gives two different totals.
#          upcoming = number of Confirmed bookings
#          earned   = total price of Completed bookings
Q_4B5 = """SELECT
  SUM(CASE WHEN b.status = 'Confirmed' THEN 1 ELSE 0 END) AS upcoming,
  SUM(CASE WHEN b.status = 'Completed' THEN b.total_price ELSE 0 END) AS earned
FROM booking b
JOIN time_slot s ON s.slot_id = b.slot_id
JOIN service_listing l ON l.listing_id = s.listing_id
WHERE l.tutor_id = ?;"""

# ===========================================================================
# FR5  UI Screen 5.A: Client - Browse and Search Services
# ===========================================================================
# 5.A.1  Search: active listings in active categories whose title contains the keyword
#        and whose rate is at most the maximum the client entered.
#        LIKE '%python%' matches any title containing "python"; LOWER() makes it ignore case.
#
#        5.A.3 is the same search limited to one category. {category_filter} is a Python
#        placeholder (like {filters} in Q_4B2): the screen replaces it with Q_5A3_FILTER
#        when a category is chosen, or with nothing for "All Categories".
#        Parameters: [category_id,] keyword pattern, max rate.
Q_5A1 = """SELECT l.listing_id, l.rate_per_hour, t.full_name AS tutor,
  c.name AS category, l.title AS listing
FROM service_listing l
JOIN tutor t ON t.tutor_id = l.tutor_id
JOIN category c ON c.category_id = l.category_id
WHERE l.is_active = 1
  AND c.is_active = 1
{category_filter}  AND LOWER(l.title) LIKE ?
  AND l.rate_per_hour <= ?
ORDER BY l.listing_id;"""
Q_5A3_FILTER = "  AND l.category_id = ?\n"

# 5.A.2  Fill the Category drop-down ("All Categories" is added first by the screen).
Q_5A2 = """SELECT category_id, name
FROM category
WHERE is_active = 1
ORDER BY category_id;"""

# ===========================================================================
# FR5  UI Screen 5.B: Client - Book a Session (Transaction Screen)
# ===========================================================================
# 5.B.1  Show the selected service at the top of the screen.
Q_5B1 = """SELECT l.title, t.full_name AS tutor, l.rate_per_hour
FROM service_listing l
JOIN tutor t ON t.tutor_id = l.tutor_id
WHERE l.listing_id = ?;"""

# 5.B.2  All slots of this listing on the chosen date, marking the ones already booked.
#        A slot happens on the chosen date if it is recurring on that weekday, OR it is a
#        one-off slot on exactly that date.
#        LEFT JOIN keeps every slot even when it has no booking on that date; for those
#        slots b.booking_id is NULL, which the CASE turns into 'Available'.
#        Parameters: date, listing_id, weekday name, date.
Q_5B2 = """SELECT s.slot_id, s.start_time, s.end_time,
  CASE WHEN b.booking_id IS NULL THEN 'Available'
    ELSE 'Already booked' END AS availability
FROM time_slot s
LEFT JOIN booking b
  ON b.slot_id = s.slot_id AND b.session_date = ?
WHERE s.listing_id = ?
  AND ((s.is_recurring = 1 AND s.day_of_week = ?)
    OR s.slot_date = ?)
ORDER BY s.start_time;"""

# 5.B.3  Confirm Booking: one INSERT, run as one transaction (see db.execute).
#        INSERT ... SELECT lets the database work out total_price = rate_per_hour x duration
#        itself, using the listing's current rate, so the client cannot send a wrong price.
#        The UNIQUE (slot_id, session_date) constraint on booking rejects a second booking of
#        the same slot on the same date, even if two clients click Confirm at the same moment.
#        Parameters: date, requirements, duration, duration, client_id, slot_id.
Q_5B3 = """INSERT INTO booking (session_date, requirements, duration_hrs,
  total_price, status, created_at, client_id, slot_id)
OUTPUT INSERTED.booking_id
SELECT ?, ?, ?, l.rate_per_hour * ?, 'Confirmed', CURRENT_TIMESTAMP, ?, s.slot_id
FROM time_slot s
JOIN service_listing l ON l.listing_id = s.listing_id
WHERE s.slot_id = ?;"""
