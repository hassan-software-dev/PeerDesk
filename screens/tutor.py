"""Tutor screens.

FR3  UI Screen 3.A  Service Listings: create, edit and deactivate the tutor's listings.
FR4  UI Screen 4.A  Manage Availability: add and remove time slots for a listing.
FR4  UI Screen 4.B  My Bookings: see bookings on the tutor's slots and mark them Completed.

Every query here includes the logged-in tutor's ID (self.tutor_id), so a tutor only ever
sees and changes their own listings, slots and bookings.
"""
from PyQt5.QtCore import QDate, QTime

import db
import queries as Q
from screens.common import (DAYS, Screen, clear_message, fill_table, fmt_date, fmt_money, fmt_time,
                            qdate_to_date, selected_key, setup_table, show_message)


class TutorListingScreen(Screen):
    """UI Screen 3.A: Tutor - Create a New Service Listing (also edits and deactivates listings).

    The same form is used for two jobs:
      * creating a new listing   (self.editing_id is None)       -> INSERT, SQL Query 3.A.2
      * editing an existing one  (self.editing_id = listing ID)  -> UPDATE, SQL Query 3.A.6
    """
    ui_file = "tutor_listing.ui"

    def __init__(self, app):
        super().__init__(app)

        # ----- Widgets: readable names for the Qt Designer widgets in tutor_listing.ui -----
        self.form_title = self.label_28               # "Create a New Service Listing" / "Edit ..."
        self.category_combo = self.comboBox_3         # "Category" drop-down
        self.rate_input = self.doubleSpinBox_1        # "Rate per hour (PKR)"
        self.active_check = self.checkBox_2           # "Active" tick box
        self.title_input = self.lineEdit_8            # "Title"
        self.description_input = self.textEdit_1      # "Description"
        self.save_button = self.pushButton_6          # "Save Listing" / "Save Changes"
        self.edit_button = self.pushButton_7          # "Edit Selected"
        self.deactivate_button = self.pushButton_8    # "Deactivate Selected"
        self.listings_table = self.tableWidget_2      # columns: Rate/hr, Status, Category, Title
        self.message_label = self.label_34            # green / red status message

        setup_table(self.listings_table)
        self.editing_id = None     # None = creating a new listing; otherwise the ID being edited

        # ----- Connect signals to methods -----
        self.save_button.clicked.connect(self.save_listing)
        self.edit_button.clicked.connect(self.edit_selected)
        self.deactivate_button.clicked.connect(self.deactivate_selected)

    @property
    def tutor_id(self):
        """The logged-in tutor's ID. @property lets us write self.tutor_id without brackets."""
        return self.app.user["id"]

    def on_show(self, **kwargs):
        clear_message(self.message_label)
        self.reset_form()
        self.refresh()

    def load_categories(self):
        # SQL Query 3.A.1: fill the Category drop-down with active categories only.
        # The category name is shown; its category_id is kept as hidden data (currentData()).
        self.category_combo.clear()
        for category_id, name in db.fetch_all(Q.Q_3A1):
            self.category_combo.addItem(name, category_id)

    def reset_form(self):
        """Empty the form and switch it back to 'create a new listing' mode."""
        self.editing_id = None
        self.form_title.setText("Create a New Service Listing")
        self.save_button.setText("Save Listing")
        self.load_categories()
        self.rate_input.setValue(500.0)
        self.active_check.setChecked(True)
        self.title_input.clear()
        self.description_input.clear()

    def refresh(self):
        """Reload the My Listings table."""
        # SQL Query 3.A.4. listing_id (column 0) is kept hidden in the row (key_column=0).
        rows = []
        for listing_id, rate, status, category, title in db.fetch_all(Q.Q_3A4, (self.tutor_id,)):
            rows.append((listing_id, fmt_money(rate), status, category, title))
        fill_table(self.listings_table, rows, key_column=0)

    def selected_id(self):
        """listing_id of the selected row, or None."""
        return selected_key(self.listings_table)

    def save_listing(self):
        """'Save Listing' / 'Save Changes' clicked."""
        title = self.title_input.text().strip()
        description = self.description_input.toPlainText().strip()
        category_id = self.category_combo.currentData()
        rate = round(self.rate_input.value(), 2)       # DECIMAL(8, 2) in the database
        active = self.active_check.isChecked()

        # Check the form before touching the database.
        if category_id is None:
            return show_message(self.message_label,
                                "There is no active category to choose. Ask the admin to add one.", ok=False)
        if not title:
            return show_message(self.message_label, "Please enter a title for the listing.", ok=False)
        if rate <= 0:      # the database also has CHECK (rate_per_hour > 0)
            return show_message(self.message_label, "The rate per hour must be more than 0.", ok=False)

        if self.editing_id is None:
            # SQL Query 3.A.2: insert a new listing for the logged-in tutor.
            new_id = db.execute(Q.Q_3A2, (title, description, rate, active, self.tutor_id, category_id))
            message = f'Listing "{title}" saved (ID {new_id}).'
        else:
            # SQL Query 3.A.6: save the changes to the listing being edited.
            db.execute(Q.Q_3A6, (category_id, rate, active, title, description, self.editing_id, self.tutor_id))
            message = f'Listing "{title}" updated (ID {self.editing_id}).'
        self.reset_form()
        self.refresh()
        show_message(self.message_label, message)

    def edit_selected(self):
        """'Edit Selected' clicked: load the selected listing into the form for editing."""
        listing_id = self.selected_id()
        if listing_id is None:
            return show_message(self.message_label, "Select one of your listings in the table first.", ok=False)

        # SQL Query 3.A.5: load the selected listing.
        row = db.fetch_one(Q.Q_3A5, (listing_id, self.tutor_id))
        if row is None:
            return
        _, category_id, category, rate, is_active, title, description = row

        # Choose the listing's category in the drop-down. findData() returns -1 if the
        # category is not in the list, which happens when the admin has deactivated it.
        # In that case we add it with "(inactive)" so the form still shows the right value.
        self.load_categories()
        index = self.category_combo.findData(category_id)
        if index < 0:
            self.category_combo.addItem(category + " (inactive)", category_id)
            index = self.category_combo.count() - 1
        self.category_combo.setCurrentIndex(index)

        self.rate_input.setValue(float(rate))
        self.active_check.setChecked(bool(is_active))
        self.title_input.setText(title)
        self.description_input.setPlainText(description or "")    # description can be NULL

        # Switch the form to "edit" mode; save_listing() will now run an UPDATE.
        self.editing_id = listing_id
        self.form_title.setText(f"Edit Service Listing (ID {listing_id})")
        self.save_button.setText("Save Changes")
        show_message(self.message_label, f'Editing "{title}". Change the fields and click Save Changes.')

    def deactivate_selected(self):
        """'Deactivate Selected' clicked: hide the listing from clients (it is not deleted)."""
        listing_id = self.selected_id()
        if listing_id is None:
            return show_message(self.message_label, "Select one of your listings in the table first.", ok=False)
        # SQL Query 3.A.3: deactivate one of the tutor's own listings.
        db.execute(Q.Q_3A3, (listing_id, self.tutor_id))
        self.refresh()
        show_message(self.message_label, f"Listing {listing_id} deactivated. Clients will no longer see it.")


class TutorAvailabilityScreen(Screen):
    """UI Screen 4.A: Tutor - Manage Availability.

    A tutor adds time slots to one of their listings. A slot is either
      * recurring: every week on a weekday (e.g. every Monday 16:00-17:00), or
      * one-off:   on a single date (e.g. Sat 14 Nov 2026 11:00-12:00).
    """
    ui_file = "tutor_availability.ui"

    def __init__(self, app):
        super().__init__(app)

        # ----- Widgets: readable names for the Qt Designer widgets in tutor_availability.ui -----
        self.listing_combo = self.comboBox_4          # "Service listing" drop-down
        self.calendar = self.calendarWidget_1         # calendar (clicking a day fills the form)
        self.recurring_radio = self.radioButton_4     # "Recurring (weekly)"
        self.one_off_radio = self.radioButton_5       # "One-off"
        self.day_combo = self.comboBox_5              # "Day of week" (for recurring slots)
        self.date_input = self.dateEdit_1             # "Date (one-off)"
        self.start_input = self.timeEdit_1            # "Start time"
        self.end_input = self.timeEdit_2              # "End time"
        self.add_button = self.pushButton_9           # "Add Slot"
        self.remove_button = self.pushButton_10       # "Remove Selected"
        self.slots_table = self.tableWidget_3         # columns: Slot ID, Start, End, Recurring, Day / Date
        self.message_label = self.label_43            # green / red status message
        self.bookings_button = self.myBookingsButton  # "View My Bookings →"

        setup_table(self.slots_table)

        # ----- Connect signals to methods -----
        self.listing_combo.currentIndexChanged.connect(self.refresh)   # another listing -> its slots
        self.recurring_radio.toggled.connect(self.update_mode)
        self.calendar.clicked.connect(self.date_clicked)
        self.add_button.clicked.connect(self.add_slot)
        self.remove_button.clicked.connect(self.remove_selected)
        self.bookings_button.clicked.connect(lambda: self.app.show_screen("tutor_bookings"))

    def on_show(self, **kwargs):
        """Reset the form to sensible defaults and load the tutor's listings."""
        clear_message(self.message_label)
        today = QDate.currentDate()
        self.calendar.setSelectedDate(today)
        self.date_input.setDate(today)
        self.start_input.setTime(QTime(16, 0))
        self.end_input.setTime(QTime(17, 0))
        self.recurring_radio.setChecked(True)
        self.update_mode()
        self.load_listings()

    def load_listings(self):
        """Fill the Service listing drop-down, then show the slots of the first listing."""
        # Adding items to the combo box sends currentIndexChanged, which would call refresh()
        # once per item. blockSignals(True) stops that; we call refresh() once at the end.
        self.listing_combo.blockSignals(True)
        self.listing_combo.clear()
        # SQL Query 4.A.1: the tutor's active listings.
        for listing_id, title in db.fetch_all(Q.Q_4A1, (self.app.user["id"],)):
            self.listing_combo.addItem(title, listing_id)
        self.listing_combo.blockSignals(False)
        self.refresh()

    def update_mode(self):
        """Recurring slots need a weekday; one-off slots need a date. Enable only the one in use."""
        recurring = self.recurring_radio.isChecked()
        self.day_combo.setEnabled(recurring)
        self.date_input.setEnabled(not recurring)

    def date_clicked(self, qdate):
        """A day was clicked on the calendar: fill in both the date and its weekday."""
        self.date_input.setDate(qdate)
        # Qt numbers weekdays 1 (Monday) to 7 (Sunday); the combo box index starts at 0.
        self.day_combo.setCurrentIndex(qdate.dayOfWeek() - 1)

    def refresh(self):
        """Reload the slots table for the selected listing."""
        listing_id = self.listing_combo.currentData()
        rows = []
        if listing_id is not None:
            # SQL Query 4.A.3: slots of the selected listing.
            for slot_id, start, end, recurring, day, slot_date in db.fetch_all(Q.Q_4A3, (listing_id,)):
                when = f"Every {day}" if recurring else fmt_date(slot_date)
                rows.append((str(slot_id), fmt_time(start), fmt_time(end), "Yes" if recurring else "No", when))
        # The Slot ID is the visible first column, so no hidden key is needed.
        fill_table(self.slots_table, rows)

    def add_slot(self):
        """'Add Slot' clicked."""
        listing_id = self.listing_combo.currentData()
        if listing_id is None:
            return show_message(self.message_label, "You have no active listing. Create one first.", ok=False)
        start = self.start_input.time()
        end = self.end_input.time()
        if end <= start:       # the database also has CHECK (end_time > start_time)
            return show_message(self.message_label, "The end time must be after the start time.", ok=False)
        start_text, end_text = start.toString("HH:mm"), end.toString("HH:mm")

        if self.recurring_radio.isChecked():
            # Recurring: store the weekday, no date.
            day = self.day_combo.currentText()
            slot_date = None
            when = f"every {day}"
        else:
            # One-off: store the date (and its weekday too).
            slot_date = qdate_to_date(self.date_input.date())
            day = DAYS[slot_date.weekday()]
            when = fmt_date(slot_date)
        is_recurring = slot_date is None     # True for weekly slots, False for one-off slots

        # SQL Query 4.A.2: insert the slot.
        new_id = db.execute(Q.Q_4A2, (day, start_text, end_text, is_recurring, slot_date, listing_id))
        self.refresh()
        show_message(self.message_label, f"Slot added: {when} {start_text}-{end_text} (Slot {new_id}).")

    def remove_selected(self):
        """'Remove Selected' clicked: delete the slot unless it has bookings."""
        key = selected_key(self.slots_table)
        if key is None:
            return show_message(self.message_label, "Select a slot in the table first.", ok=False)
        slot_id = int(key)
        # SQL Query 4.A.4: delete the slot only if nobody has booked it.
        # db.execute returns the number of rows deleted: 0 means the slot has bookings.
        deleted = db.execute(Q.Q_4A4, (slot_id, slot_id))
        if deleted == 0:
            return show_message(self.message_label,
                                f"Slot {slot_id} has bookings, so it cannot be removed.", ok=False)
        self.refresh()
        show_message(self.message_label, f"Slot {slot_id} removed.")


class TutorBookingsScreen(Screen):
    """UI Screen 4.B: Tutor - My Bookings."""
    ui_file = "tutor_bookings.ui"

    def __init__(self, app):
        super().__init__(app)

        # ----- Widgets: readable names for the Qt Designer widgets in tutor_bookings.ui -----
        # (Some widgets in this .ui file were already given readable names in Qt Designer.)
        self.listing_combo = self.listingCombo        # "Listing" filter
        self.status_combo = self.statusCombo          # "Status" filter: All / Confirmed / Completed
        self.show_button = self.showButton            # "Show"
        self.bookings_table = self.bookingsTable      # columns: Booking #, Session, Client, Listing, Total, Status
        self.summary_label = self.label_6             # "Upcoming sessions: ...  Earned ..."
        self.details_label = self.label_7             # "Booking #39 · Ali Hamza · email"
        self.requirements_text = self.requirementsText
        self.complete_button = self.markCompletedButton   # "Mark Completed"
        self.message_label = self.label_9             # green / red status message

        setup_table(self.bookings_table)
        self.requirements_text.setReadOnly(True)

        # ----- Connect signals to methods -----
        self.show_button.clicked.connect(self.refresh)
        self.bookings_table.itemSelectionChanged.connect(self.show_selected)
        self.complete_button.clicked.connect(self.mark_completed)

    @property
    def tutor_id(self):
        """The logged-in tutor's ID."""
        return self.app.user["id"]

    def on_show(self, **kwargs):
        clear_message(self.message_label)
        # SQL Query 4.B.1: fill the Listing drop-down. "All my listings" (data None) = no filter.
        self.listing_combo.clear()
        self.listing_combo.addItem("All my listings", None)
        for listing_id, title in db.fetch_all(Q.Q_4B1, (self.tutor_id,)):
            self.listing_combo.addItem(title, listing_id)
        self.status_combo.setCurrentIndex(0)      # "All"
        self.refresh()

    def refresh(self):
        """Reload the bookings table using the two optional filters."""
        # Start with the part that is always there (WHERE l.tutor_id = ?), then add one
        # filter line and one parameter for each filter the tutor chose.
        filters = ""
        params = [self.tutor_id]
        chosen_listing = self.listing_combo.currentData()
        if chosen_listing is not None:
            filters += Q.Q_4B2_LISTING_FILTER
            params.append(chosen_listing)
        chosen_status = self.status_combo.currentText()
        if chosen_status != "All":
            filters += Q.Q_4B2_STATUS_FILTER
            params.append(chosen_status)

        # SQL Query 4.B.2: bookings on the tutor's slots (with the filters put in place).
        sql = Q.Q_4B2.format(filters=filters)
        rows = []
        for booking_id, date, start, end, client, listing, hours, total, status in db.fetch_all(sql, params):
            session = f"{fmt_date(date)}, {fmt_time(start)}-{fmt_time(end)}"
            rows.append((str(booking_id), session, client, listing, fmt_money(total), status))
        fill_table(self.bookings_table, rows)
        self.clear_details()
        self.refresh_summary()

    def refresh_summary(self):
        # SQL Query 4.B.5: number of upcoming sessions and money earned.
        # SUM returns NULL (None) when the tutor has no bookings yet, hence "or 0".
        upcoming, earned = db.fetch_one(Q.Q_4B5, (self.tutor_id,))
        self.summary_label.setText(f"Upcoming sessions: {upcoming or 0}        "
                                   f"Earned from completed sessions: PKR {fmt_money(earned)}")

    def clear_details(self):
        self.details_label.setText("Select a booking in the table to see its details.")
        self.requirements_text.clear()

    def selected_id(self):
        """booking_id of the selected row as an int, or None."""
        key = selected_key(self.bookings_table)
        return int(key) if key is not None else None

    def show_selected(self):
        """A booking was selected: show the client's details and requirements below the table."""
        booking_id = self.selected_id()
        if booking_id is None:
            return self.clear_details()
        # SQL Query 4.B.3: client's email and task requirements.
        row = db.fetch_one(Q.Q_4B3, (booking_id,))
        if row:
            _, name, email, requirements = row
            self.details_label.setText(f"Booking #{booking_id}  ·  {name}  ·  {email}")
            self.requirements_text.setPlainText(requirements or "")

    def mark_completed(self):
        """'Mark Completed' clicked."""
        booking_id = self.selected_id()
        if booking_id is None:
            return show_message(self.message_label, "Select a booking in the table first.", ok=False)
        # SQL Query 4.B.4: the rules (still Confirmed, date has arrived, tutor's own booking)
        # are in the query's WHERE clause. 0 rows changed means one of the rules failed.
        changed = db.execute(Q.Q_4B4, (booking_id, self.tutor_id))
        if changed == 0:
            return show_message(self.message_label, f"Booking #{booking_id} can't be completed: it is already "
                                "completed or its date hasn't come yet.", ok=False)
        self.refresh()
        show_message(self.message_label,
                     f"Booking #{booking_id} marked as Completed. It now counts towards your earnings.")
