"""FR1: Register and Log in (UI Screens 1.A Sign up and 1.B Log in).

HOW BUTTONS WORK IN PyQt (signals and slots)
--------------------------------------------
A widget sends a *signal* when something happens, e.g. a button sends `clicked`.
We *connect* the signal to one of our methods (the *slot*), and Qt calls that method
every time the signal is sent:

    self.create_button.clicked.connect(self.create_account)
    # -> clicking "Create Account" calls self.create_account()

Note: we pass the method itself (self.create_account), we do NOT call it (no brackets).
"""
from PyQt5.QtWidgets import QLineEdit

import db
import queries as Q
from screens.common import Screen, clear_message, show_message


def make_link(label, before, link_text):
    """Turn a plain label like 'New here? Sign up' into text with a clickable blue link.

    The label then sends the `linkActivated` signal when the link is clicked.
    """
    label.setText(f'{before} <a href="#" style="color:#2563eb;">{link_text}</a>')
    label.setOpenExternalLinks(False)    # do not open a web browser; we handle the click ourselves


class SignupScreen(Screen):
    """UI Screen 1.A: Sign up (create a Client, Tutor or Administrator account)."""
    ui_file = "signup.ui"

    def __init__(self, app):
        super().__init__(app)

        # ----- Widgets: readable names for the Qt Designer widgets in signup.ui -----
        self.client_radio = self.radioButton_1        # "Client"
        self.tutor_radio = self.radioButton_2         # "Tutor"
        self.admin_radio = self.radioButton_3         # "Administrator"
        self.name_input = self.lineEdit_1             # "Full Name"
        self.email_input = self.lineEdit_2            # "University Email"
        self.password_input = self.lineEdit_3         # "Password"
        self.confirm_input = self.lineEdit_4          # "Confirm Password"
        self.batch_input = self.spinBox_1             # "Batch (Clients only)"
        self.create_button = self.pushButton_1        # "Create Account"
        self.login_link = self.label_10               # "Already have an account? Log in"
        self.message_label = self.label_11            # green / red status message

        # Show dots instead of the typed password.
        self.password_input.setEchoMode(QLineEdit.Password)
        self.confirm_input.setEchoMode(QLineEdit.Password)

        # ----- Connect signals to methods -----
        make_link(self.login_link, "Already have an account?", "Log in")
        # linkActivated passes the link's URL as an argument; "lambda _:" accepts and ignores it.
        self.login_link.linkActivated.connect(lambda _: self.app.show_screen("login"))
        self.create_button.clicked.connect(self.create_account)
        # When any role button is switched, enable/disable the Batch box.
        for radio in (self.client_radio, self.tutor_radio, self.admin_radio):
            radio.toggled.connect(self.update_batch_field)

    def on_show(self, **kwargs):
        """Start with an empty form every time the screen opens."""
        for field in (self.name_input, self.email_input, self.password_input, self.confirm_input):
            field.clear()
        self.client_radio.setChecked(True)
        self.batch_input.setValue(2028)
        clear_message(self.message_label)
        self.update_batch_field()

    def role(self):
        """Which role is chosen. These names are the keys of the dictionaries in queries.py."""
        if self.tutor_radio.isChecked():
            return "Tutor"
        if self.admin_radio.isChecked():
            return "Administrator"
        return "Client"

    def update_batch_field(self):
        """Only clients have a batch (graduation year), so the box is greyed out for other roles."""
        self.batch_input.setEnabled(self.role() == "Client")

    def create_account(self):
        """'Create Account' clicked: check the form, then insert the new user."""
        role = self.role()
        name = self.name_input.text().strip()          # strip() removes spaces at both ends
        email = self.email_input.text().strip().lower()
        password = self.password_input.text()

        # 1) Check the form in Python first, so obvious mistakes never reach the database.
        #    "return show_message(...)" shows the error and stops the method here.
        if not name or not email or not password:
            return show_message(self.message_label, "Please fill in your name, email and password.", ok=False)
        if "@" not in email:
            return show_message(self.message_label, "Please enter a valid university email.", ok=False)
        if password != self.confirm_input.text():
            return show_message(self.message_label, "The two passwords do not match.", ok=False)

        # 2) SQL Query 1.A.1: is this email already registered for this role?
        #    The query returns one row with one column (the count). "(existing,) = ..."
        #    unpacks that one-value row into the variable `existing`.
        (existing,) = db.fetch_one(Q.Q_1A1[role], (email,))
        if existing > 0:
            return show_message(self.message_label,
                                f"A {role.lower()} account with this email already exists.", ok=False)

        # 3) SQL Query 1.A.2: create the account in the table of the selected role.
        #    The Client version of the query has one extra "?" for the batch.
        if role == "Client":
            params = (name, email, password, self.batch_input.value())
        else:
            params = (name, email, password)
        db.execute(Q.Q_1A2[role], params)
        show_message(self.message_label, f"Account created for {name} ({role}). Please log in.")


class LoginScreen(Screen):
    """UI Screen 1.B: Log in."""
    ui_file = "login.ui"

    def __init__(self, app):
        super().__init__(app)

        # ----- Widgets: readable names for the Qt Designer widgets in login.ui -----
        self.role_combo = self.comboBox_1             # "Log in as" (Client / Tutor / Administrator)
        self.email_input = self.lineEdit_5            # "University Email"
        self.password_input = self.lineEdit_6         # "Password"
        self.login_button = self.pushButton_2         # "Log In"
        self.signup_link = self.label_18              # "New here? Sign up"
        self.message_label = self.label_19            # green / red status message

        self.password_input.setEchoMode(QLineEdit.Password)

        # ----- Connect signals to methods -----
        make_link(self.signup_link, "New here?", "Sign up")
        self.signup_link.linkActivated.connect(lambda _: self.app.show_screen("signup"))
        self.login_button.clicked.connect(self.log_in)
        self.password_input.returnPressed.connect(self.log_in)   # pressing Enter also logs in

    def on_show(self, **kwargs):
        self.password_input.clear()
        clear_message(self.message_label)
        self.email_input.setFocus()

    def log_in(self):
        """'Log In' clicked: look the user up in the table of the chosen role."""
        role = self.role_combo.currentText()     # "Client", "Tutor" or "Administrator"
        email = self.email_input.text().strip().lower()
        password = self.password_input.text()
        if not email or not password:
            return show_message(self.message_label, "Please enter your email and password.", ok=False)

        # SQL Query 1.B.1: one row back means the email and password are correct.
        row = db.fetch_one(Q.Q_1B1[role], (email, password))
        if row is None:
            return show_message(self.message_label, "Wrong email or password for this role.", ok=False)

        user_id, full_name = row
        show_message(self.message_label, f"Welcome back, {full_name}!")
        # Tell the main window who logged in; it builds the menu and opens the home screen.
        self.app.log_in(role, user_id, full_name)
