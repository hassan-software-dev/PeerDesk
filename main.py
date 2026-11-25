"""PeerDesk: peer tutoring, design gigs and code review bookings (CS355 Database Project, Group 12).

Run:  python main.py

HOW THE APP IS PUT TOGETHER
---------------------------
    main.py              the main window: logging in/out, the menu bar, switching screens
    screens/*.py         one class per screen; each loads its layout from a ui/*.ui file
    queries.py           every SQL query the app runs
    db.py                connects to SQL Server and runs the queries

All screens are created once when the app starts and kept in a QStackedWidget,
a container that shows exactly one of its widgets at a time (like a deck of cards
where only the top card is visible). "Opening" a screen means bringing it to the top.
"""
import os
import sys
import traceback

# Make the project folder the current folder and let Python import our own modules
# (db, queries, screens) even when the app is started from somewhere else.
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd())

from PyQt5.QtWidgets import (QAction, QApplication, QMainWindow, QMessageBox, QSizePolicy,
                             QStackedWidget, QToolBar, QWidget)

import db
from screens.admin import AdminCategoriesScreen
from screens.auth import LoginScreen, SignupScreen
from screens.client import ClientBookingScreen, ClientBrowseScreen
from screens.tutor import TutorAvailabilityScreen, TutorBookingsScreen, TutorListingScreen

# Every screen in the app: a short name -> the class that builds it.
# The short name is what the code uses to open a screen, e.g. self.app.show_screen("login").
SCREENS = {
    "signup": SignupScreen,                         # UI Screen 1.A
    "login": LoginScreen,                           # UI Screen 1.B
    "admin_categories": AdminCategoriesScreen,      # UI Screen 2.A
    "tutor_listing": TutorListingScreen,            # UI Screen 3.A
    "tutor_availability": TutorAvailabilityScreen,  # UI Screen 4.A
    "tutor_bookings": TutorBookingsScreen,          # UI Screen 4.B
    "client_browse": ClientBrowseScreen,            # UI Screen 5.A
    "client_booking": ClientBookingScreen,          # UI Screen 5.B
}

# The menu buttons shown at the top after logging in, for each role: (button text, screen name).
# Each role only gets buttons for its own screens.
MENUS = {
    "Administrator": [("Manage Categories", "admin_categories")],
    "Tutor": [("My Listings", "tutor_listing"),
              ("Availability", "tutor_availability"),
              ("My Bookings", "tutor_bookings")],
    "Client": [("Browse Services", "client_browse")],
}

# The first screen each role sees after logging in.
HOME = {"Administrator": "admin_categories", "Tutor": "tutor_listing", "Client": "client_browse"}


class MainWindow(QMainWindow):
    """The application window. Holds every screen, the menu bar and the logged-in user."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PeerDesk")

        # Who is logged in. None until someone logs in; then a dictionary like
        # {"role": "Tutor", "id": 1, "name": "Muhammad Saad Malik"}.
        # Screens read it as self.app.user["id"] to know whose data to load.
        self.user = None

        # Create every screen once and put it in the stack.
        # Each screen gets `self` (this window) so it can call show_screen() and read self.user.
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.screens = {}
        for name, screen_class in SCREENS.items():
            screen = screen_class(self)
            self.screens[name] = screen
            self.stack.addWidget(screen)

        # The menu bar (a toolbar) is hidden until someone logs in.
        self.menu = QToolBar("Menu")
        self.menu.setMovable(False)
        self.menu.setStyleSheet("QToolBar { background: #e5e7eb; border: 0; padding: 2px; spacing: 4px; }"
                                "QToolButton { padding: 4px 10px; }"
                                "QToolButton:checked { background: #2563eb; color: white; border-radius: 3px; }")
        self.addToolBar(self.menu)
        self.menu.hide()
        self.menu_actions = {}      # screen name -> its menu button (filled in by build_menu)

        self.show_screen("login")

    # ----- logging in and out -----
    def log_in(self, role, user_id, name):
        """Called by the login screen after the email and password were checked."""
        self.user = {"role": role, "id": user_id, "name": name}
        self.build_menu()
        self.show_screen(HOME[role])

    def log_out(self):
        self.user = None
        self.menu.hide()
        self.menu_actions = {}
        self.show_screen("login")

    def build_menu(self):
        """Create the menu buttons for the logged-in user's role."""
        self.menu.clear()
        self.menu_actions = {}
        for text, screen_name in MENUS[self.user["role"]]:
            # checkable=True lets the button stay "pressed" (highlighted) for the open screen.
            action = QAction(text, self, checkable=True)
            # The lambda runs later, when the button is clicked. "s=screen_name" saves the
            # CURRENT value of screen_name for this button; without it every button would use
            # the last value of the loop. "_" receives the checked flag Qt passes, which we ignore.
            action.triggered.connect(lambda _, s=screen_name: self.show_screen(s))
            self.menu.addAction(action)
            self.menu_actions[screen_name] = action

        # An empty widget that stretches, pushing the next items to the right-hand side.
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.menu.addWidget(spacer)
        # The user's name (disabled, so it is just text) and the Log out button.
        self.menu.addAction(f"{self.user['name']} ({self.user['role']})").setEnabled(False)
        self.menu.addAction("Log out", self.log_out)
        self.menu.show()

    # ----- switching screens -----
    def show_screen(self, name, **kwargs):
        """Open a screen by its short name.

        Any extra keyword arguments are handed to that screen's on_show(), e.g.
            show_screen("client_booking", listing_id=13)
        calls ClientBookingScreen.on_show(listing_id=13).
        """
        screen = self.screens[name]
        screen.on_show(**kwargs)               # let the screen reload its data first
        self.stack.setCurrentWidget(screen)    # then bring it to the front
        self.stack.setFixedSize(screen.size())

        # Highlight the menu button of the open screen. The booking screen has no button
        # of its own, so "Browse Services" stays highlighted while booking.
        for screen_name, action in self.menu_actions.items():
            is_current = screen_name == name or (screen_name == "client_browse" and name == "client_booking")
            action.setChecked(is_current)

        # Resize the window to fit the new screen (screens have different sizes).
        self.adjustSize()
        self.setFixedSize(self.sizeHint())


def show_error(exc_type, exc, tb):
    """Show any unexpected database or program error in a message box instead of closing the app.

    Python calls sys.excepthook when an error is not caught anywhere. We replace it with this
    function (see main()), so the full error is still printed in the terminal for debugging,
    and the user sees a message box while the app keeps running.
    """
    traceback.print_exception(exc_type, exc, tb)
    QMessageBox.critical(None, "PeerDesk - error", f"{exc_type.__name__}: {exc}")


def main():
    app = QApplication(sys.argv)     # every PyQt program needs exactly one QApplication

    # Connect to the database before showing any screen, so wrong settings in db.py give
    # one clear message instead of errors on every screen.
    try:
        db.connect()
    except Exception as err:
        QMessageBox.critical(None, "PeerDesk - cannot connect to the database",
                             "Could not connect to SQL Server.\n\n"
                             f"{err}\n\n"
                             "Check the server name in db.py, that SQL Server is running, and that "
                             "you ran setup_database.py (or the two scripts in the sql folder) first.")
        return 1

    sys.excepthook = show_error
    window = MainWindow()
    window.show()
    exit_code = app.exec_()     # runs the event loop: waits for clicks/typing until the window closes
    db.close()
    return exit_code


# This block only runs when the file is started directly (python main.py),
# not when another file imports it.
if __name__ == "__main__":
    sys.exit(main())
