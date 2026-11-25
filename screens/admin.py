"""FR2: Configure Service Categories (UI Screen 2.A, Administrator only).

The administrator can add a category, edit it, and deactivate it.
Categories are never deleted, because service listings point to them with a foreign key;
deactivating (is_active = 0) just hides them from tutors creating new listings.
"""
import db
import queries as Q
from screens.common import Screen, clear_message, fill_table, selected_key, setup_table, show_message

# The only values the database accepts for category.type
# (CHECK (type IN ('Academic', 'Design', 'Coding')) in sql/01_create_tables.sql).
DEFAULT_TYPES = ["Academic", "Coding", "Design"]


class AdminCategoriesScreen(Screen):
    """UI Screen 2.A: Admin - Manage Service Categories."""
    ui_file = "admin_categories.ui"

    def __init__(self, app):
        super().__init__(app)

        # ----- Widgets: readable names for the Qt Designer widgets in admin_categories.ui -----
        self.name_input = self.lineEdit_7             # "Category Name"
        self.type_combo = self.comboBox_2             # "Type" drop-down
        self.active_check = self.checkBox_1           # "Active" tick box
        self.add_button = self.pushButton_3           # "Add Category"
        self.update_button = self.pushButton_4        # "Update"
        self.deactivate_button = self.pushButton_5    # "Deactivate"
        self.categories_table = self.tableWidget_1    # columns: ID, Type, Status, Category Name
        self.message_label = self.label_25            # green / red status message

        setup_table(self.categories_table)

        # ----- Connect signals to methods -----
        self.add_button.clicked.connect(self.add_category)
        self.update_button.clicked.connect(self.update_category)
        self.deactivate_button.clicked.connect(self.deactivate_category)
        # Clicking a row in the table loads that category into the form.
        self.categories_table.itemSelectionChanged.connect(self.load_selected)

    def on_show(self, **kwargs):
        self.load_types()
        self.name_input.clear()
        self.active_check.setChecked(True)
        clear_message(self.message_label)
        self.refresh()

    def load_types(self):
        """Fill the Type drop-down."""
        # SQL Query 2.A.5: the types already used in the category table.
        types = [row[0] for row in db.fetch_all(Q.Q_2A5)]
        # Also add any allowed type that no category uses yet (e.g. in an empty database).
        for t in DEFAULT_TYPES:
            if t not in types:
                types.append(t)
        self.type_combo.clear()
        self.type_combo.addItems(sorted(types))

    def refresh(self):
        """Reload the categories table from the database."""
        # SQL Query 2.A.4. The first column (category_id) is shown, so no hidden key is needed.
        fill_table(self.categories_table, db.fetch_all(Q.Q_2A4))

    def selected_id(self):
        """category_id of the selected row as an int, or None if nothing is selected."""
        key = selected_key(self.categories_table)
        return int(key) if key is not None else None

    def load_selected(self):
        """A row was selected: copy that category's values into the form."""
        category_id = self.selected_id()
        if category_id is None:
            return
        # SQL Query 2.A.6: load the selected category.
        row = db.fetch_one(Q.Q_2A6, (category_id,))
        if row:
            _, name, category_type, is_active = row     # "_" = a value we do not need (the ID)
            self.name_input.setText(name)
            self.type_combo.setCurrentText(category_type)
            self.active_check.setChecked(bool(is_active))

    def form_values(self):
        """Read and check the form. Returns (name, type, active), or None if it is invalid."""
        name = self.name_input.text().strip()
        if not name:
            show_message(self.message_label, "Please enter a category name.", ok=False)
            return None
        return name, self.type_combo.currentText(), self.active_check.isChecked()

    def add_category(self):
        """'Add Category' clicked."""
        values = self.form_values()
        if values is None:
            return
        name, category_type, active = values
        try:
            # SQL Query 2.A.1: insert the category, owned by the logged-in administrator.
            new_id = db.execute(Q.Q_2A1, (name, category_type, active, self.app.user["id"]))
        except Exception as err:
            # category.name is UNIQUE, so SQL Server rejects a second category with the same name.
            # We catch that one error and show a friendly message; any other error is re-raised.
            if db.is_unique_violation(err):
                return show_message(self.message_label, f'A category named "{name}" already exists.', ok=False)
            raise
        self.refresh()
        show_message(self.message_label, f'Category "{name}" added (ID {new_id}).')

    def update_category(self):
        """'Update' clicked: save the form into the selected category."""
        category_id = self.selected_id()
        if category_id is None:
            return show_message(self.message_label, "Select a category in the table first.", ok=False)
        values = self.form_values()
        if values is None:
            return
        name, category_type, active = values
        try:
            # SQL Query 2.A.2: save the edits to the selected category.
            db.execute(Q.Q_2A2, (name, category_type, active, category_id))
        except Exception as err:
            if db.is_unique_violation(err):      # renamed to a name another category already has
                return show_message(self.message_label, f'A category named "{name}" already exists.', ok=False)
            raise
        self.refresh()
        show_message(self.message_label, f'Category {category_id} updated.')

    def deactivate_category(self):
        """'Deactivate' clicked: hide the category from tutors (soft delete)."""
        category_id = self.selected_id()
        if category_id is None:
            return show_message(self.message_label, "Select a category in the table first.", ok=False)
        # SQL Query 2.A.3: set is_active = 0 (the row is kept).
        db.execute(Q.Q_2A3, (category_id,))
        self.refresh()
        self.active_check.setChecked(False)
        show_message(self.message_label, f"Category {category_id} deactivated. Tutors can no longer choose it.")
