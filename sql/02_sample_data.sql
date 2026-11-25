-- PeerDesk sample data (SQL Server).
-- These are the same rows the UI screens in InterimDemo_Group_12.pdf show, so the app opens with
-- the data from the screenshots. IDENTITY_INSERT lets us keep the same IDs as the screens
-- (listing 13, slot 104, booking 39 and so on). Afterwards SQL Server continues numbering from the
-- highest ID, so the next booking a client makes becomes Booking #42, as on UI Screen 5.B.

SET IDENTITY_INSERT administrator ON;
INSERT INTO administrator (admin_id, full_name, email, password) VALUES
 (1, 'PeerDesk Admin', 'admin@st.habib.edu.pk', 'admin123');
SET IDENTITY_INSERT administrator OFF;
GO

SET IDENTITY_INSERT tutor ON;
INSERT INTO tutor (tutor_id, full_name, email, password, bio) VALUES
 (1, 'Muhammad Saad Malik', 'mm10357@st.habib.edu.pk', 'saad1234', 'CS student who enjoys reviewing Python code and teaching Calculus.'),
 (2, 'Sara Ahmed', 'sa09812@st.habib.edu.pk', 'sara1234', 'Helps beginners debug their first Python programs.'),
 (3, 'Bilal Raza', 'br09755@st.habib.edu.pk', 'bilal123', 'Data Structures TA.');
SET IDENTITY_INSERT tutor OFF;
GO

SET IDENTITY_INSERT client ON;
INSERT INTO client (client_id, full_name, email, password, batch) VALUES
 (1, 'Ayesha Khan', 'ak09876@st.habib.edu.pk', 'ayesha27', 2027),
 (2, 'Muhammad Hassan Shahid', 'ms10290@st.habib.edu.pk', 'hassan2028', 2028),
 (3, 'Ali Hamza', 'ah10144@st.habib.edu.pk', 'ali2028', 2028);
SET IDENTITY_INSERT client OFF;
GO

SET IDENTITY_INSERT category ON;
INSERT INTO category (category_id, name, type, is_active, admin_id) VALUES
 (1, 'Calculus Tutoring', 'Academic', 1, 1),
 (2, 'UI/UX Design Review', 'Design', 1, 1),
 (3, 'Python Code Review', 'Coding', 1, 1),
 (4, 'Thesis Editing', 'Academic', 0, 1),
 (5, 'Data Structures Tutoring', 'Academic', 1, 1);
SET IDENTITY_INSERT category OFF;
GO

SET IDENTITY_INSERT service_listing ON;
INSERT INTO service_listing (listing_id, title, description, rate_per_hour, is_active, tutor_id, category_id) VALUES
 (11, 'Calculus I Exam Prep', 'Past-paper practice for Calculus I midterms and finals.', 600.00, 1, 1, 1),
 (12, 'Figma Portfolio Feedback', 'Detailed feedback on your Figma portfolio and case studies.', 700.00, 0, 1, 2),
 (13, 'Python Assignment Code Review', 'I review Python assignments line by line, point out bugs and style issues, and explain how to fix them. Best for CS 101/102 and Data Structures.', 800.00, 1, 1, 3),
 (14, 'Intro to Python Debugging', 'Learn to read error messages and use print and the debugger to fix your code.', 500.00, 1, 2, 3),
 (15, 'Python for Data Structures', 'Lists, stacks, queues and linked lists implemented in Python.', 900.00, 1, 3, 5);
SET IDENTITY_INSERT service_listing OFF;
GO

SET IDENTITY_INSERT time_slot ON;
INSERT INTO time_slot (slot_id, day_of_week, start_time, end_time, is_recurring, slot_date, listing_id) VALUES
 (95, 'Tuesday', '14:00', '15:00', 1, NULL, 11),
 (101, 'Monday', '16:00', '17:00', 1, NULL, 13),
 (102, 'Wednesday', '18:00', '19:00', 1, NULL, 13),
 (103, 'Saturday', '11:00', '12:00', 0, '2026-11-14', 13),
 (104, 'Wednesday', '16:00', '17:00', 1, NULL, 13),
 (110, 'Thursday', '15:00', '16:00', 1, NULL, 14);
SET IDENTITY_INSERT time_slot OFF;
GO

SET IDENTITY_INSERT booking ON;
INSERT INTO booking (booking_id, session_date, requirements, duration_hrs, total_price, status, client_id, slot_id) VALUES
 (38, '2026-11-03', 'Limits and continuity revision before my Calculus I midterm.', 1.0, 600.00, 'Completed', 1, 95),
 (39, '2026-11-09', 'Help me find why my recursive factorial function in Python hits the recursion limit.', 1.0, 800.00, 'Confirmed', 3, 101),
 (40, '2026-11-11', 'Review my file-handling assignment (CS 101) for style and bugs.', 1.0, 800.00, 'Confirmed', 1, 102),
 (41, '2026-11-12', 'Debugging a KeyError in my dictionary program.', 1.0, 500.00, 'Confirmed', 2, 110);
SET IDENTITY_INSERT booking OFF;
GO
