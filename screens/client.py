"""FR5: Book a Session (Client screens).

UI Screen 5.A  Browse and Search Services: the client searches the active listings.
UI Screen 5.B  Book a Session (the transaction screen): the client picks a date and a free
               slot and confirms. The booking is one INSERT run as one transaction, and the
               UNIQUE (slot_id, session_date) constraint stops double bookings.
"""
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtWidgets import QListWidgetItem

import db
import queries as Q
from screens.common import (DAYS, Screen, clear_message, fill_table, fmt_date, fmt_money, fmt_time,
                            qdate_to_date, selected_key, setup_table, show_message)


class ClientBrowseScreen(Screen):
    """UI Screen 5.A: Client - Browse and Search Services."""
    ui_file = "client_browse.ui"

    def __init__(self, app):
        super().__init__(app)

        # ----- Widgets: readable names for the Qt Designer widgets in client_browse.ui -----
        self.keyword_input = self.lineEdit_9          # "Keyword"
        self.category_combo = self.comboBox_6         # "Category" drop-down
        self.max_rate_input = self.spinBox_2          # "Max rate/hr (PKR)"
        self.search_button = self.pushButton_11       # "Search"
        self.results_label = self.label_50            # "3 services found"
        self.results_table = self.tableWidget_4       # columns: Rate/hr, Tutor, Category, Listing
        self.book_button = self.pushButton_12         # "View & Book Selected"

        setup_table(self.results_table)

        # ----- Connect signals to methods -----
        self.search_button.clicked.connect(self.search)
        self.keyword_input.returnPressed.connect(self.search)           # Enter in the keyword box
        self.book_button.clicked.connect(self.view_and_book)
        self.results_table.doubleClicked.connect(lambda _: self.view_and_book())  # double-click a row

    def on_show(self, **kwargs):
        # SQL Query 5.A.2: fill the Category drop-down.
        # addItem(text, data): the text is shown, the data (category_id) is kept hidden and
        # read back later with currentData(). "All Categories" has data None = no filter.
        self.category_combo.clear()
        self.category_combo.addItem("All Categories", None)
        for category_id, name in db.fetch_all(Q.Q_5A2):
            self.category_combo.addItem(name, category_id)
        self.keyword_input.clear()
        self.max_rate_input.setValue(5000)
        self.search()

    def search(self):
        """Run the search with the current keyword, category and maximum rate."""
        keyword = self.keyword_input.text().strip().lower()
        category_id = self.category_combo.currentData()

        # Build the parameter list in the same order as the "?"s in the final SQL.
        params = []
        category_filter = ""
        if category_id is not None:
            # SQL Query 5.A.3: the same search limited to one category. This adds the line
            # "AND l.category_id = ?" to the query, so its value goes first in params.
            category_filter = Q.Q_5A3_FILTER
            params.append(category_id)
        # "%" is SQL's wildcard: '%python%' matches any title that contains "python".
        params.append(f"%{keyword}%")
        params.append(self.max_rate_input.value())

        # SQL Query 5.A.1: .format() puts the optional filter line into the {category_filter} spot.
        sql = Q.Q_5A1.format(category_filter=category_filter)
        rows = []
        for listing_id, rate, tutor, category, title in db.fetch_all(sql, params):
            rows.append((listing_id, fmt_money(rate), tutor, category, title))

        # key_column=0: listing_id is remembered for each row but not shown in the table.
        fill_table(self.results_table, rows, key_column=0)
        count = len(rows)
        self.results_label.setText(f"{count} service{'s' if count != 1 else ''} found")

    def view_and_book(self):
        """Open the booking screen for the selected listing."""
        listing_id = selected_key(self.results_table)      # the hidden listing_id
        if listing_id is None:
            self.results_label.setText("Select a service in the table first, then click View & Book Selected.")
            return
        # Extra keyword arguments are passed on to ClientBookingScreen.on_show(listing_id=...).
        self.app.show_screen("client_booking", listing_id=listing_id)


class ClientBookingScreen(Screen):
    """UI Screen 5.B: Client - Book a Session (Transaction Screen)."""
    ui_file = "client_booking.ui"

    def __init__(self, app):
        super().__init__(app)

        # ----- Widgets: readable names for the Qt Designer widgets in client_booking.ui -----
        self.title_label = self.label_54              # listing title
        self.tutor_label = self.label_55              # "Tutor: ..."
        self.rate_label = self.label_56               # "Rate: PKR ... / hr"
        self.date_input = self.dateEdit_2             # "Session date"
        self.slots_heading = self.label_58            # "Available slots on ..."
        self.slot_list = self.slotList                # list of slots on the chosen date
        self.duration_input = self.doubleSpinBox_2    # "Duration (hours)"
        self.requirements_input = self.textEdit_2     # "Task requirements"
        self.total_label = self.label_62              # "PKR 800.00"
        self.confirm_button = self.pushButton_13      # "Confirm Booking"
        self.message_label = self.label_63            # green / red status message

        # Information about the listing being booked (set in on_show).
        self.listing_id = None
        self.rate = 0.0
        self.tutor_name = ""

        self.date_input.setCalendarPopup(True)        # click the date box to get a calendar

        # ----- Connect signals to methods -----
        self.date_input.dateChanged.connect(self.load_slots)          # new date -> reload slots
        self.duration_input.valueChanged.connect(self.update_total)   # new duration -> new price
        self.confirm_button.clicked.connect(self.confirm_booking)

    def on_show(self, listing_id=None, **kwargs):
        """Opened from the browse screen with the listing_id of the chosen service."""
        if listing_id is not None:
            self.listing_id = listing_id
        clear_message(self.message_label)

        # SQL Query 5.B.1: show the selected service at the top.
        title, self.tutor_name, rate = db.fetch_one(Q.Q_5B1, (self.listing_id,))
        self.rate = float(rate)        # DECIMAL comes back as Decimal; float makes the maths simple
        self.title_label.setText(title)
        self.tutor_label.setText(f"Tutor: {self.tutor_name}")
        self.rate_label.setText(f"Rate: PKR {fmt_money(self.rate)} / hr")

        self.requirements_input.clear()
        self.duration_input.setValue(1.0)
        # Setting the date would send dateChanged and call load_slots once here, and we call
        # load_slots ourselves just below. blockSignals(True) stops that extra call.
        self.date_input.blockSignals(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.blockSignals(False)
        self.load_slots()
        self.update_total()

    def session_date(self):
        """The chosen date as a Python date (what pyodbc needs for a DATE column)."""
        return qdate_to_date(self.date_input.date())

    def load_slots(self):
        """List the listing's slots on the chosen date. Booked slots are greyed out."""
        date = self.session_date()
        weekday = DAYS[date.weekday()]           # e.g. "Wednesday", as stored in time_slot.day_of_week
        self.slots_heading.setText(f"Available slots on {fmt_date(date)}")
        self.slot_list.clear()

        # SQL Query 5.B.2: slots on this date, each marked 'Available' or 'Already booked'.
        for slot_id, start, end, availability in db.fetch_all(Q.Q_5B2, (date, self.listing_id, weekday, date)):
            text = f"Slot {slot_id} · {fmt_time(start)}-{fmt_time(end)}"
            item = QListWidgetItem(text)
            # Remember the slot's details inside the list item (hidden), for confirm_booking().
            item.setData(Qt.UserRole, (slot_id, fmt_time(start), fmt_time(end)))
            if availability != "Available":
                item.setText(text + " (already booked)")
                item.setFlags(Qt.NoItemFlags)    # no flags = greyed out and cannot be selected
            self.slot_list.addItem(item)

        if self.slot_list.count() == 0:
            item = QListWidgetItem("No slots on this day. Try another date.")
            item.setFlags(Qt.NoItemFlags)
            self.slot_list.addItem(item)

    def update_total(self):
        """Show the price as the client changes the duration (rate x hours).

        This is only a preview: the price actually saved is calculated by the database in
        SQL Query 5.B.3, from the listing's rate stored in the database.
        """
        self.total_label.setText(f"PKR {fmt_money(self.rate * self.duration_input.value())}")

    def confirm_booking(self):
        """'Confirm Booking' clicked: check the form, then insert the booking."""
        item = self.slot_list.currentItem()
        # The selected item must be a real, available slot (not greyed out, not the "No slots" line).
        if item is None or not (item.flags() & Qt.ItemIsSelectable) or item.data(Qt.UserRole) is None:
            return show_message(self.message_label, "Select an available slot first.", ok=False)
        requirements = self.requirements_input.toPlainText().strip()
        if not requirements:
            return show_message(self.message_label, "Please describe what you need help with.", ok=False)
        duration = self.duration_input.value()
        if duration <= 0:
            return show_message(self.message_label, "Duration must be more than 0 hours.", ok=False)

        slot_id, start, end = item.data(Qt.UserRole)
        date = self.session_date()
        try:
            # SQL Query 5.B.3: create the booking in one transaction (committed or rolled back
            # as a whole). duration is passed twice: once for duration_hrs, once for the price.
            booking_id = db.execute(Q.Q_5B3, (date, requirements, duration, duration,
                                              self.app.user["id"], slot_id))
        except Exception as err:
            # UNIQUE (slot_id, session_date) rejected it: someone else booked this slot on this
            # date after our list was loaded. The transaction was rolled back, nothing was saved.
            if db.is_unique_violation(err):
                self.load_slots()
                return show_message(self.message_label, f"Sorry, slot {slot_id} was just booked for this date. "
                                    "Please pick another slot.", ok=False)
            raise

        self.load_slots()          # the slot now shows as "(already booked)"
        show_message(self.message_label, f"Booking #{booking_id} confirmed for {fmt_date(date)}, {start}-{end}.\n"
                     f"  Slot {slot_id} is now shown as booked on {self.tutor_name}'s calendar.")
