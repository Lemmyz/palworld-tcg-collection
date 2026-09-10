"""Qt widgets: catalogue, card editor, collection ledger, and record details."""
from decimal import Decimal
from urllib.parse import urlencode

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QKeySequence, QShortcut, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView, QButtonGroup, QCheckBox, QComboBox, QDialog,
    QDialogButtonBox, QFormLayout, QFrame, QGridLayout, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QMainWindow, QMessageBox,
    QProgressBar, QPushButton, QScrollArea, QSizePolicy, QSpinBox,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QStackedWidget,
)

from .repository import COLOURS, CONDITIONS, TYPES, ValidationError
from .card_reference import artwork_for, reference_for


def label(text, style=None, wrap=False):
    widget = QLabel(str(text))
    widget.setTextFormat(Qt.TextFormat.PlainText)
    if style:
        widget.setObjectName(style)
    widget.setWordWrap(wrap)
    return widget


def button(text, action, style=None):
    widget = QPushButton(text)
    if style:
        widget.setObjectName(style)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    widget.clicked.connect(action)
    return widget


def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()
        elif item.layout():
            clear_layout(item.layout())


class CardEditor(QDialog):
    def __init__(self, repo, parent, card=None):
        super().__init__(parent)
        self.repo, self.card = repo, card or {}
        self.setWindowTitle("Edit card" if card else "Add catalogue card")
        self.setMinimumWidth(490)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.addWidget(label(self.windowTitle(), "heading"))
        layout.addWidget(label("Catalogue records describe a card. Add owned copies separately.", "muted", True))
        form = QFormLayout()
        form.setSpacing(14)
        self.fields = {}
        self.sets = QComboBox()
        for row in repo.sets():
            self.sets.addItem(f"{row['SetCode']} · {row['SetName']}", row["SetID"])
        if card:
            self.sets.setCurrentIndex(self.sets.findData(card["SetID"]))
        form.addRow("Set", self.sets)
        for key, title, choices, limit in (
            ("CardNumber", "Card number", None, 20), ("CardName", "Card name", None, 100),
            ("CardType", "Card type", TYPES, 30), ("CardColour", "Colour", COLOURS, 30),
            ("Rarity", "Rarity", ("C", "U", "R", "RR", "SR", "OSR", "SP", "SSP"), 20),
            ("Variant", "Variant", ("Standard", "Parallel"), 50),
        ):
            if choices:
                field = QComboBox()
                field.setEditable(True)
                field.addItems(choices)
                field.lineEdit().setMaxLength(limit)
                if card:
                    field.setCurrentText(str(card.get(key) or ""))
            else:
                field = QLineEdit(str(self.card.get(key) or ""))
                field.setMaxLength(limit)
            field.setAccessibleName(title)
            self.fields[key] = field
            form.addRow(title, field)
        layout.addLayout(form)
        controls = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        controls.accepted.connect(self.save)
        controls.rejected.connect(self.reject)
        layout.addWidget(controls)

    def save(self):
        values = {key: field.currentText() if isinstance(field, QComboBox) else field.text() for key, field in self.fields.items()}
        values["SetID"] = self.sets.currentData()
        try:
            self.repo.save_card(values, self.card.get("CardID"))
        except ValidationError as error:
            QMessageBox.warning(self, "Check card details", str(error))
            return
        except Exception:
            QMessageBox.critical(self, "Card not saved", "The database could not save this card. Check the connection and whether the record already exists.")
            return
        self.accept()


class EntryEditor(QDialog):
    def __init__(self, repo, parent, card, entry=None):
        super().__init__(parent)
        self.repo, self.card, self.entry = repo, card, entry or {}
        self.setWindowTitle("Edit owned copies" if entry else "Add to collection")
        self.setMinimumWidth(460)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.addWidget(label(self.windowTitle(), "heading"))
        layout.addWidget(label(card["CardName"], "muted", True))
        form = QFormLayout()
        form.setSpacing(14)
        self.quantity = QSpinBox()
        self.quantity.setRange(1, 999999)
        self.quantity.setValue(self.entry.get("Quantity", 1))
        self.condition = QComboBox()
        self.condition.addItems(CONDITIONS)
        self.condition.setCurrentText(self.entry.get("CardCondition", "Near Mint"))
        self.price = QLineEdit(str(self.entry.get("PurchasePricePerCard") or ""))
        self.price.setPlaceholderText("Optional, e.g. 2.50")
        self.acquired = QLineEdit(str(self.entry.get("DateAcquired") or ""))
        self.acquired.setPlaceholderText("Optional · YYYY-MM-DD")
        self.location = QLineEdit(str(self.entry.get("StorageLocation") or ""))
        self.location.setMaxLength(100)
        self.location.setPlaceholderText("e.g. Red binder · page 01")
        self.trade = QCheckBox("Available for trade")
        self.trade.setChecked(bool(self.entry.get("IsForTrade")))
        for title, field in (("Quantity", self.quantity), ("Condition", self.condition),
                             ("Price per card (£)", self.price), ("Date acquired", self.acquired),
                             ("Storage location", self.location)):
            field.setAccessibleName(title)
            form.addRow(title, field)
        form.addRow("", self.trade)
        layout.addLayout(form)
        layout.addWidget(label("Each entry groups copies with the same condition and purchase details.", "muted", True))
        controls = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        controls.accepted.connect(self.save)
        controls.rejected.connect(self.reject)
        layout.addWidget(controls)

    def save(self):
        try:
            self.repo.save_entry(self.card["CardID"], {
                "Quantity": self.quantity.value(), "CardCondition": self.condition.currentText(),
                "PurchasePricePerCard": self.price.text().strip(), "DateAcquired": self.acquired.text().strip(),
                "StorageLocation": self.location.text(), "IsForTrade": self.trade.isChecked(),
            }, self.entry.get("CollectionEntryID"))
        except ValidationError as error:
            QMessageBox.warning(self, "Check collection details", str(error))
            return
        except Exception:
            QMessageBox.critical(self, "Entry not saved", "The database could not save this entry. Check the connection and refresh the collection.")
            return
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self, repo, mode):
        super().__init__()
        self.repo, self.mode = repo, mode
        self.view, self.selected_id = "catalogue", None
        self.all_cards, self.all_entries = [], []
        self.setWindowTitle("Palvault — Palworld TCG Collection")
        self.resize(1420, 910)
        self.setMinimumSize(1060, 720)
        shell = QWidget()
        self.pages = QStackedWidget()
        self.setCentralWidget(self.pages)
        self.pages.addWidget(shell)
        root = QHBoxLayout(shell)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(202)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(20, 32, 20, 22)
        nav.setSpacing(12)
        nav.addWidget(label("P / V", "eyebrow"))
        nav.addWidget(label("PALVAULT", "heading"))
        nav.addWidget(label("PALWORLD TCG", "number"))
        nav.addSpacing(38)
        nav.addWidget(button("Start menu", self.show_start_menu, "nav"))
        nav.addWidget(label("YOUR ARCHIVE", "eyebrow"))
        group = QButtonGroup(self)
        self.nav_buttons = {}
        for key, title in (("catalogue", "Card catalogue"), ("collection", "My collection")):
            item = button(title, lambda checked=False, k=key: self.switch_view(k), "nav")
            item.setCheckable(True)
            group.addButton(item)
            self.nav_buttons[key] = item
            nav.addWidget(item)
        self.nav_buttons["catalogue"].setChecked(True)
        nav.addStretch()
        nav.addWidget(label("CONNECTED TO", "eyebrow"))
        nav.addWidget(label(mode, "muted", True))
        nav.addSpacing(14)
        nav.addWidget(button("Project on GitHub", lambda: QDesktopServices.openUrl(QUrl("https://github.com/Lemmyz/palworld-tcg-collection"))))
        nav.addWidget(label("Unofficial fan project\nNot affiliated with Pocketpair.", "muted", True))
        root.addWidget(sidebar)

        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(28, 28, 28, 22)
        layout.setSpacing(20)
        header = QHBoxLayout()
        titles = QVBoxLayout()
        titles.addWidget(label("COLLECTION MANAGER / 01", "eyebrow"))
        self.title = label("Card catalogue", "title")
        titles.addWidget(self.title)
        header.addLayout(titles)
        header.addStretch()
        header.addWidget(button("+ New card", self.new_card, "primary"))
        layout.addLayout(header)
        self.stat_layout = QHBoxLayout()
        self.stat_layout.setSpacing(12)
        layout.addLayout(self.stat_layout)
        controls = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search card name or number…")
        self.search.setAccessibleName("Search card name or number")
        self.search.textChanged.connect(self.render)
        controls.addWidget(self.search, 1)
        self.colour = QComboBox()
        self.colour.setAccessibleName("Filter by colour")
        self.colour.addItems(["All colours", *COLOURS])
        self.colour.currentTextChanged.connect(self.render)
        controls.addWidget(self.colour)
        self.ownership = QComboBox()
        self.ownership.setAccessibleName("Filter by ownership")
        self.ownership.addItems(["All cards", "Owned", "Missing"])
        self.ownership.currentTextChanged.connect(self.render)
        controls.addWidget(self.ownership)
        controls.addWidget(button("Refresh", self.refresh))
        layout.addLayout(controls)
        self.result_label = label("", "muted")
        layout.addWidget(self.result_label)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 8, 0)
        scroll.setWidget(self.content)
        layout.addWidget(scroll, 1)
        root.addWidget(workspace, 1)

        detail_scroll = QScrollArea()
        detail_scroll.setWidgetResizable(True)
        detail_scroll.setFixedWidth(320)
        self.detail = QFrame()
        self.detail.setObjectName("detail")
        self.detail_layout = QVBoxLayout(self.detail)
        self.detail_layout.setContentsMargins(24, 30, 24, 24)
        self.detail_layout.setSpacing(16)
        detail_scroll.setWidget(self.detail)
        root.addWidget(detail_scroll)
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self.search.setFocus)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.new_card)
        QShortcut(QKeySequence("F5"), self, activated=self.refresh)
        self.refresh()
        self.pages.addWidget(self.build_start_menu())
        self.show_start_menu()

    def build_start_menu(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        page = QWidget()
        scroll.setWidget(page)
        outer = QVBoxLayout(page)
        outer.setContentsMargins(48, 36, 48, 36)
        outer.setSpacing(22)
        top = QHBoxLayout()
        top.addWidget(label("P / V     PALVAULT", "eyebrow"))
        top.addStretch()
        top.addWidget(label(self.mode, "badge"))
        outer.addLayout(top)
        outer.addStretch(1)
        outer.addWidget(label("Your cards. All in one place.", "title", True))
        outer.addWidget(label("Palvault is your personal Palworld trading card collection manager. Browse card information, keep track of what you own, and organise every copy.", "muted", True))
        columns = QHBoxLayout()
        columns.setSpacing(24)
        for eyebrow, heading, sections in (
            ("EXPLORE YOUR COLLECTION", "What you can do", (
                ("Browse and discover", "Search the catalogue, filter cards, and view card details. The three starter cards include artwork and gameplay stats."),
                ("Build your collection", "Add cards you own and record their quantity, condition, purchase price, storage location, and trade status."),
                ("Keep it up to date", "Edit your records, remove copies, and see your total cards and recorded spend."),
            )),
            ("A QUICK START", "How to use Palvault", (
                ("01  Choose a card", "Open the card catalogue and select View card. Use New card if your card is not listed yet."),
                ("02  Add your owned copies", "Select Add to collection, enter the details, then Save. You can add separate entries for different purchases or conditions."),
                ("03  Manage your collection", "Open My collection, select an entry, then edit or remove it. Removing owned copies keeps the catalogue card available."),
            )),
        ):
            panel = QFrame()
            panel.setObjectName("panel")
            content = QVBoxLayout(panel)
            content.setContentsMargins(26, 24, 26, 24)
            content.setSpacing(14)
            content.addWidget(label(eyebrow, "eyebrow"))
            content.addWidget(label(heading, "heading", True))
            for title, description in sections:
                content.addWidget(label(title))
                content.addWidget(label(description, "muted", True))
            content.addStretch()
            columns.addWidget(panel, 1)
        outer.addLayout(columns)
        outer.addWidget(label("Your changes are saved when you select Save. Return to this guide at any time using Start menu in the sidebar.", "muted", True))
        actions = QHBoxLayout()
        self.start_catalogue = button("Open card catalogue", lambda: self.switch_view("catalogue"), "primary")
        self.start_collection = button("Open my collection", lambda: self.switch_view("collection"))
        actions.addWidget(self.start_catalogue)
        actions.addWidget(self.start_collection)
        actions.addStretch()
        actions.addWidget(button("Exit", self.close))
        outer.addLayout(actions)
        outer.addStretch(1)
        outer.addWidget(label("Demo and SQL Server collections are separate. The active collection is shown above.\nUnofficial fan project · Not affiliated with Pocketpair or Bushiroad.", "muted", True))
        return scroll

    def show_start_menu(self):
        self.pages.setCurrentIndex(1)
        self.statusBar().showMessage("Welcome to Palvault · Choose a catalogue or collection to get started")

    def refresh(self):
        try:
            self.all_cards = self.repo.cards()
            self.all_entries = self.repo.entries()
            stats = self.repo.stats()
        except Exception:
            QMessageBox.critical(self, "Unable to load collection", "Check the database connection and setup scripts, then select Refresh. Your saved data has not been changed.")
            return
        clear_layout(self.stat_layout)
        for value, title in ((f"{stats['copies']:,}", "Cards owned"),
                             (f"{stats['unique']} / {stats['catalogue']}", "Catalogue collected"),
                             (f"£{stats['spent']:,.2f}", "Recorded spend")):
            panel = QFrame()
            panel.setObjectName("panel")
            inside = QVBoxLayout(panel)
            inside.setContentsMargins(16, 16, 16, 16)
            inside.addWidget(label(value, "value"))
            inside.addWidget(label(title, "muted"))
            self.stat_layout.addWidget(panel)
        if not any(c["CardID"] == self.selected_id for c in self.all_cards):
            self.selected_id = self.all_cards[0]["CardID"] if self.all_cards else None
        self.render()
        self.render_detail()
        self.statusBar().showMessage(f"{self.mode}  ·  Changes save automatically after confirmation  ·  Ctrl+F search  /  Ctrl+N new card")

    def switch_view(self, key):
        self.pages.setCurrentIndex(0)
        self.view = key
        self.nav_buttons[key].setChecked(True)
        self.title.setText("Card catalogue" if key == "catalogue" else "My collection")
        self.render()

    def filtered_cards(self):
        term = self.search.text().strip().casefold()
        return [c for c in self.all_cards
                if (not term or term in f"{c['CardName']} {c['CardNumber']}".casefold())
                and (self.colour.currentIndex() == 0 or c["CardColour"] == self.colour.currentText())
                and (self.ownership.currentIndex() == 0 or (c["Owned"] > 0) == (self.ownership.currentText() == "Owned"))]

    def render(self, *_):
        clear_layout(self.content_layout)
        cards = self.filtered_cards()
        if self.view == "collection":
            self.render_collection(cards)
            return
        self.result_label.setText(f"{len(cards)} cards  ·  Select a record to view details")
        if not cards:
            self.content_layout.addWidget(label("No cards match. Clear the filters or add a new card.", "muted", True))
        grid = QGridLayout()
        grid.setSpacing(16)
        for index, card in enumerate(cards):
            tile = QFrame()
            tile.setObjectName("card")
            tile.setMinimumWidth(200)
            tile_layout = QVBoxLayout(tile)
            tile_layout.setContentsMargins(20, 18, 20, 18)
            tile_layout.setSpacing(12)
            top = QHBoxLayout()
            top.addWidget(label(card["CardNumber"], "number"))
            top.addStretch()
            top.addWidget(label(card["Rarity"], "badge"))
            tile_layout.addLayout(top)
            stripe = QFrame()
            stripe.setFixedHeight(4)
            colour_map = {"Red": "#ed8b7d", "Blue": "#70b8eb", "Green": "#73d5ae", "Yellow": "#e3c96b", "Purple": "#b899e7"}
            stripe.setStyleSheet(f"background: {colour_map.get(card['CardColour'], '#91a6bb')}; border-radius: 2px;")
            tile_layout.addWidget(stripe)
            artwork = artwork_for(card)
            if artwork:
                thumbnail = QLabel()
                thumbnail.setAlignment(Qt.AlignmentFlag.AlignCenter)
                thumbnail.setAccessibleName(f"Artwork for {card['CardName']}")
                thumbnail.setPixmap(QPixmap(str(artwork)).scaledToHeight(180, Qt.TransformationMode.SmoothTransformation))
                tile_layout.addWidget(thumbnail)
            name, _, subtitle = card["CardName"].partition(" - ")
            tile_layout.addWidget(label(name, "heading", True))
            tile_layout.addWidget(label(subtitle or card["Variant"], "muted", True))
            tile_layout.addSpacing(12)
            tile_layout.addWidget(label(f"{card['CardColour'] or 'Unspecified'} / {card['CardType']} / {card['Variant']}", "muted", True))
            tile_layout.addWidget(label(f"{card['Owned']} owned" if card["Owned"] else "Not collected", "badge"))
            tile_layout.addStretch()
            tile_layout.addWidget(button("View card", lambda checked=False, c=card: self.select_card(c["CardID"])))
            grid.addWidget(tile, index // 2, index % 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        self.content_layout.addLayout(grid)
        self.content_layout.addStretch()

    def render_collection(self, cards):
        ids = {c["CardID"] for c in cards}
        entries = [e for e in self.all_entries if e["CardID"] in ids]
        self.result_label.setText(f"{len(entries)} collection entries  ·  Select an entry to edit or remove it")
        if not entries:
            self.content_layout.addWidget(label("No owned copies here yet.", "heading"))
            self.content_layout.addWidget(label("Choose a card in the catalogue, then select Add to collection. Entries appear here once saved.", "muted", True))
            self.content_layout.addStretch()
            return
        table = QTableWidget(len(entries), 4)
        table.setHorizontalHeaderLabels(["Card", "Qty", "Condition", "Location"])
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setAlternatingRowColors(True)
        table.verticalHeader().hide()
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in (1, 2, 3):
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        for row, entry in enumerate(entries):
            for col, value in enumerate((entry["CardNumber"], entry["Quantity"], entry["CardCondition"], entry["StorageLocation"] or "—")):
                item = QTableWidgetItem(str(value))
                item.setToolTip(entry["CardName"])
                table.setItem(row, col, item)
            table.setRowHeight(row, 48)
        table.setMinimumHeight(270)
        table.itemSelectionChanged.connect(lambda: self.select_card(entries[table.currentRow()]["CardID"]) if table.currentRow() >= 0 else None)
        self.content_layout.addWidget(table)
        actions = QHBoxLayout()
        edit = button("Edit selected entry", lambda: self.edit_entry(entries[table.currentRow()]) if table.currentRow() >= 0 else None)
        remove = button("Remove selected entry", lambda: self.remove_entry(entries[table.currentRow()]) if table.currentRow() >= 0 else None, "danger")
        edit.setEnabled(False)
        remove.setEnabled(False)
        table.itemSelectionChanged.connect(lambda: (edit.setEnabled(table.currentRow() >= 0), remove.setEnabled(table.currentRow() >= 0)))
        actions.addWidget(edit)
        actions.addWidget(remove)
        actions.addStretch()
        self.content_layout.addLayout(actions)

    def select_card(self, card_id):
        self.selected_id = card_id
        self.render_detail()

    def selected_card(self):
        return next((c for c in self.all_cards if c["CardID"] == self.selected_id), None)

    def render_detail(self):
        clear_layout(self.detail_layout)
        self.detail_layout.addWidget(label("CARD INSPECTOR", "eyebrow"))
        card = self.selected_card()
        if not card:
            self.detail_layout.addWidget(label("Select a card to see its details.", "muted", True))
            self.detail_layout.addStretch()
            return
        self.detail_layout.addWidget(label(card["CardNumber"], "number"))
        self.detail_layout.addWidget(label(card["CardName"], "heading", True))
        self.detail_layout.addWidget(label(f"{card['Rarity']}  ·  {card['Variant']}", "badge", True))
        reference = reference_for(card)
        if reference:
            self.detail_layout.addWidget(label(f"COST {reference['cost']}    POWER {reference['power']}    STRIKE {reference['strike']}", "badge", True))
            self.detail_layout.addWidget(label(f"{reference['element']} · {reference['subtype']}", "muted", True))
        for title, value in (("SET", card["SetName"]), ("RELEASE DATE", card["ReleaseDate"] or "Not recorded"),
                             ("TYPE / COLOUR", f"{card['CardType']} / {card['CardColour'] or 'Unspecified'}"),
                             ("IN YOUR COLLECTION", f"{card['Owned']} copies")):
            self.detail_layout.addWidget(label(title, "number"))
            self.detail_layout.addWidget(label(value, None, True))
        self.detail_layout.addWidget(button("+ Add to collection", lambda: self.add_entry(card), "primary"))
        self.detail_layout.addWidget(button("Edit card details", lambda: self.edit_card(card)))
        self.detail_layout.addWidget(button("Official card information", lambda: self.open_official(card)))
        self.detail_layout.addWidget(label("Open the official catalogue for artwork, abilities, and current card rulings.", "muted", True))
        entries = [e for e in self.all_entries if e["CardID"] == card["CardID"]]
        if entries:
            self.detail_layout.addWidget(label("OWNED COPIES", "eyebrow"))
        for entry in entries:
            frame = QFrame()
            frame.setObjectName("panel")
            box = QVBoxLayout(frame)
            box.addWidget(label(f"{entry['Quantity']} × {entry['CardCondition']}", None, True))
            price = "Price not recorded" if entry["PurchasePricePerCard"] is None else f"£{Decimal(str(entry['PurchasePricePerCard'])):.2f} each"
            box.addWidget(label(price, "muted"))
            box.addWidget(label(entry["StorageLocation"] or "No storage location", "muted", True))
            if entry["DateAcquired"]:
                box.addWidget(label(f"Acquired {entry['DateAcquired']}", "muted"))
            if entry["IsForTrade"]:
                box.addWidget(label("Available for trade", "badge"))
            box.addWidget(button("Edit copies", lambda checked=False, e=entry: self.edit_entry(e)))
            self.detail_layout.addWidget(frame)
        self.detail_layout.addStretch()
        self.detail_layout.addWidget(button("Delete catalogue record", lambda: self.remove_card(card), "danger"))

    def new_card(self):
        if CardEditor(self.repo, self).exec():
            self.refresh()

    def edit_card(self, card):
        if CardEditor(self.repo, self, card).exec():
            self.refresh()

    def add_entry(self, card):
        if EntryEditor(self.repo, self, card).exec():
            self.refresh()

    def edit_entry(self, entry):
        card = next(c for c in self.all_cards if c["CardID"] == entry["CardID"])
        if EntryEditor(self.repo, self, card, entry).exec():
            self.refresh()

    def remove_entry(self, entry):
        response = QMessageBox.question(self, "Remove owned copies?", f"Remove this entry of {entry['Quantity']} copies of {entry['CardNumber']}? The catalogue card will remain.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel)
        if response == QMessageBox.StandardButton.Yes:
            self.mutate(lambda: self.repo.delete_entry(entry["CollectionEntryID"]))

    def remove_card(self, card):
        response = QMessageBox.question(self, "Delete catalogue record?", f"Delete {card['CardNumber']} ({card['Variant']}) from the catalogue? This cannot be undone.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel)
        if response == QMessageBox.StandardButton.Yes:
            self.mutate(lambda: self.repo.delete_card(card["CardID"]))

    def mutate(self, action):
        try:
            action()
        except ValidationError as error:
            QMessageBox.warning(self, "Cannot make this change", str(error))
        except Exception:
            QMessageBox.critical(self, "Change not saved", "The database could not complete this change. Refresh the app and try again.")
        self.refresh()

    @staticmethod
    def open_official(card):
        query = urlencode({"keyword": card["CardNumber"]})
        QDesktopServices.openUrl(QUrl("https://en.palworld-official-cardgame.com/cardlist/searchresults/?" + query))
