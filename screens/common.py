"""Helpers shared by all screens: the Screen base class, messages, tables and formatting.

A NOTE ON WIDGET NAMES
----------------------
The screens were drawn in Qt Designer, which gives widgets automatic names such as
"lineEdit_7" or "pushButton_3". At the top of each screen's __init__ there is a
"Widgets" section that gives every widget a readable name, for example:

    self.name_input = self.lineEdit_7        # "Category Name" text box

Both names point to the SAME widget object, so the rest of the code can use the readable
name. To find a widget in Qt Designer, look up its original name in that section.
"""
import datetime
import os

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QAbstractItemView, QTableWidgetItem, QWidget

# Folder that holds the Qt Designer .ui files (one level up from this file, then "ui").
UI_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ui")

# Colours for the status message under each form: green for success, red for an error.
OK_STYLE = "color: #15803d; font-weight: bold;"
ERROR_STYLE = "color: #b91c1c; font-weight: bold;"

# Weekday names in the same order as Python's date.weekday() (Monday = 0 ... Sunday = 6).
# These are also the exact values stored in time_slot.day_of_week.
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class Screen(QWidget):
    """Base class for every screen. Each screen in the app is a subclass of this.

    A subclass only has to set `ui_file` (the Qt Designer file to load) and, if needed,
    override on_show(). Example:

        class LoginScreen(Screen):
            ui_file = "login.ui"

    `app` is the main window (see main.py). Screens use it to:
      * read the logged-in user:   self.app.user["id"], self.app.user["role"]
      * open another screen:       self.app.show_screen("client_booking", listing_id=13)
    """
    ui_file = None   # each subclass sets this to its .ui file name

    def __init__(self, app):
        super().__init__()
        self.app = app
        # loadUi reads the .ui file and creates all its widgets as attributes of this object,
        # e.g. self.lineEdit_7, self.pushButton_3 ... (named exactly as in Qt Designer).
        uic.loadUi(os.path.join(UI_DIR, self.ui_file), self)
        self.setFixedSize(self.size())    # keep the size drawn in Qt Designer

    def on_show(self, **kwargs):
        """Called by main.py every time this screen is opened.

        Screens override this to reload their data from the database, so the user always
        sees up-to-date rows. **kwargs receives any extra values passed to show_screen(),
        e.g. the listing_id when the client opens the booking screen.
        """


# ---------------------------------------------------------------------------
# Status messages
# ---------------------------------------------------------------------------
def show_message(label, text, ok=True):
    """Show a green ✔ success message, or a red ✖ error message when ok=False."""
    label.setStyleSheet(OK_STYLE if ok else ERROR_STYLE)
    if text:
        label.setText(("✔ " if ok else "✖ ") + text)
    else:
        label.setText("")


def clear_message(label):
    label.setText("")


# ---------------------------------------------------------------------------
# Tables (QTableWidget)
# ---------------------------------------------------------------------------
def setup_table(table):
    """Make a table read-only and let the user select one whole row at a time."""
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionMode(QAbstractItemView.SingleSelection)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)


def fill_table(table, rows, key_column=None):
    """Replace everything in a QTableWidget with the given query rows.

    key_column (optional): the index of a value in each row, usually an ID, that should be
    REMEMBERED but NOT SHOWN. Example: the client's search table shows rate, tutor, category
    and title, but the code still needs the listing_id of the row the user selects.

    How the hidden key is stored: every table cell can carry extra data that is not
    displayed. We put the key into the first cell of the row under the role Qt.UserRole
    (Qt's slot for "data the programmer wants to attach"). selected_key() reads it back.
    """
    table.clearSelection()
    table.setRowCount(0)                       # remove the old rows
    for r, row in enumerate(rows):
        table.insertRow(r)
        # The values to display: every column except the hidden key column.
        shown = [value for i, value in enumerate(row) if i != key_column]
        for c, value in enumerate(shown):
            text = value if isinstance(value, str) else fmt(value)
            item = QTableWidgetItem(text)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)   # remove the "editable" flag
            table.setItem(r, c, item)
        if key_column is not None:
            table.item(r, 0).setData(Qt.UserRole, row[key_column])


def selected_key(table):
    """Return the ID of the selected row, or None if no row is selected.

    If the table was filled with a hidden key (see fill_table) that key is returned;
    otherwise the text of the row's first cell (which is then the visible ID column).
    """
    row = table.currentRow()
    if row < 0 or not table.selectionModel().hasSelection():
        return None
    first_cell = table.item(row, 0)
    key = first_cell.data(Qt.UserRole)
    if key is not None:
        return key
    return first_cell.text()


# ---------------------------------------------------------------------------
# Formatting values from the database for display
# ---------------------------------------------------------------------------
def fmt(value):
    """Turn any value pyodbc returns into display text.

    SQL type      ->  Python type          ->  shown as
    NULL          ->  None                 ->  ""
    BIT           ->  bool                 ->  "Yes" / "No"
    DATETIME2     ->  datetime.datetime    ->  "03 Nov 2026 14:00"
    DATE          ->  datetime.date        ->  "Tue 03 Nov 2026"
    TIME          ->  datetime.time        ->  "14:00"
    DECIMAL       ->  decimal.Decimal      ->  "1,400.00"
    anything else ->  str(value)
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    # datetime must be checked before date, because a datetime is also a date in Python.
    if isinstance(value, datetime.datetime):
        return value.strftime("%d %b %Y %H:%M")
    if isinstance(value, datetime.date):
        return fmt_date(value)
    if isinstance(value, datetime.time):
        return value.strftime("%H:%M")
    if isinstance(value, float) or type(value).__name__ == "Decimal":
        return fmt_money(value)
    return str(value)


def fmt_money(value):
    """1400 -> '1,400.00' (comma for thousands, always two decimals)."""
    return f"{float(value or 0):,.2f}"


def fmt_date(value):
    """A date -> 'Wed 11 Nov 2026'."""
    return to_date(value).strftime("%a %d %b %Y")


def fmt_time(value):
    """A TIME value -> '16:00'.

    Newer ODBC drivers return datetime.time; older ones return text like
    '16:00:00.0000000', so in that case we keep the first five characters.
    """
    if isinstance(value, datetime.time):
        return value.strftime("%H:%M")
    return str(value)[:5]


def to_date(value):
    """Accept a datetime, a date, or text 'YYYY-MM-DD...' and return a datetime.date."""
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value
    return datetime.date.fromisoformat(str(value)[:10])


def qdate_to_date(qdate):
    """Convert Qt's QDate (from a date picker) into Python's datetime.date for pyodbc."""
    return datetime.date(qdate.year(), qdate.month(), qdate.day())
