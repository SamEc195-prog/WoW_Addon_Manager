import sys
import re
import webbrowser
import urllib.parse
from PyQt6.QtWidgets import QDialog
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout,
                             QWidget, QLabel, QScrollArea, QFrame, QFileDialog, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, QTimer

from config import ConfigManager
from workers import UpdateWorker, ScanWorker
from installer import download_and_install_addon, install_local_addon

class AddonRowWidget(QFrame):
    from PyQt6.QtCore import pyqtSignal
    update_requested = pyqtSignal(str, str)
    manual_requested = pyqtSignal(str) # NEU: Signal für manuelle Installation

    def __init__(self, name, local_version, online_version, update_url=""):
        super().__init__()
        self.addon_name = name
        self.update_url = update_url
        
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.layout = QHBoxLayout(self)
        
        self.name_label = QLabel(f"<b>{name}</b>")
        self.layout.addWidget(self.name_label, 2)

        # 2. Spalte: Lokale Version (NEU)
        self.local_v_label = QLabel(f"<span style='color:#666;'>{local_version}</span>")
        self.local_v_label.setFixedWidth(100)
        self.local_v_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.local_v_label)

        # 3. Spalte: Neueste Version
        self.version_label = QLabel(online_version)
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_label.setFixedWidth(100)
        self.layout.addWidget(self.version_label)
        
        # 4. Spalte: Aktion (Button oder Status)
        action_container = QWidget()
        action_layout = QHBoxLayout(action_container)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_container.setFixedWidth(130)

        self.update_button = None
        self.status_label = None

        if update_url:
            self.update_button = QPushButton("Update")
            self.update_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.update_button.clicked.connect(self.on_update_clicked)
            action_layout.addWidget(self.update_button)
        elif online_version == "Fehler" or online_version == "-":
            # NEU: Ein Button statt einem Label
            self.manual_button = QPushButton("Suchen")
            self.manual_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.manual_button.setStyleSheet("color: #d35400; font-weight: bold;") # Etwas Farbe, um aufzufallen
            self.manual_button.clicked.connect(self.on_manual_clicked)
            action_layout.addWidget(self.manual_button)
        else:
            self.status_label = QLabel("<b>Up to date</b>")
            action_layout.addWidget(self.status_label)
            
        self.layout.addWidget(action_container, 0) 

    def on_update_clicked(self):
        if self.update_url:
            self.update_button.setEnabled(False)
            self.update_button.setText("Lädt...") 
            self.update_requested.emit(self.addon_name, self.update_url)

    def on_manual_clicked(self):
        # Wir senden den Addon-Namen zurück, damit die Hauptklasse weiß, welches Addon manuell gesucht werden soll
        self.manual_requested.emit(self.addon_name)

class DragDropDialog(QDialog):
    def __init__(self, addon_name, parent=None):
        super().__init__(parent)
        self.addon_name = addon_name
        self.zip_path = None

        self.setWindowTitle(f"Manuelles Update: {addon_name}")
        self.setFixedSize(400, 200)
        
        # Das ist das Wichtigste: Wir erlauben Drop-Events!
        self.setAcceptDrops(True) 

        layout = QVBoxLayout(self)

        self.label = QLabel(
            f"Der Browser wurde geöffnet.<br><br>"
            f"Ziehe die heruntergeladene .zip Datei für<br>"
            f"<b>{addon_name}</b><br>"
            f"hier in dieses Fenster."
        )
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Ein bisschen CSS, damit es wie eine "Drop-Zone" aussieht
        self.label.setStyleSheet("border: 2px dashed #aaa; border-radius: 10px; padding: 20px; font-size: 14px;")
        layout.addWidget(self.label)

    # Wenn eine Datei über das Fenster gezogen wird
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept() # Akzeptiere die Aktion
        else:
            event.ignore()

    # Wenn die Datei losgelassen wird
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            
            # Sicherheitsprüfung: Ist es wirklich ein ZIP?
            if file_path.endswith(".zip"):
                self.zip_path = file_path
                self.accept() # Schließt den Dialog erfolgreich (exec() gibt True zurück)
            else:
                self.label.setText("<span style='color:red;'>Bitte nur eine .zip Datei ablegen!</span>")


class AddonManagerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WoW Addon Manager v2.1 (Smart Sort)")
        self.setMinimumSize(750, 500)
        self.available_updates = {}
        self.config = ConfigManager()
        
        # NEU: Unsere interne Liste, um zu wissen, wo wir Widgets einfügen müssen
        self.addon_widgets_data = [] 
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # --- Obere Leiste ---
        self.header_layout = QHBoxLayout()
        self.status_label = QLabel("Bereit zum Scannen.")
        self.header_layout.addWidget(self.status_label)
        self.header_layout.addStretch()
        
        self.path_button = QPushButton("WoW-Pfad ändern")
        self.path_button.clicked.connect(self.change_wow_path)
        self.header_layout.addWidget(self.path_button)
        
        self.scan_button = QPushButton("Nach Updates suchen")
        self.scan_button.clicked.connect(self.check_for_updates)
        self.header_layout.addWidget(self.scan_button)
        
        self.update_button = QPushButton("Alle aktualisieren")
        self.update_button.clicked.connect(self.start_update_thread) 
        self.update_button.setEnabled(False)
        self.header_layout.addWidget(self.update_button)
        main_layout.addLayout(self.header_layout)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide() 
        main_layout.addWidget(self.progress_bar)
        
        # --- Spaltenüberschriften ---
        columns_layout = QHBoxLayout()
        columns_layout.setContentsMargins(15, 0, 30, 0) 
        
        columns_layout.addWidget(QLabel("<b>Addon</b>"), 2) # Gleicher Stretch wie oben
        
        local_v_col = QLabel("<b>Lokal</b>")
        local_v_col.setFixedWidth(100)
        local_v_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        columns_layout.addWidget(local_v_col)
        
        online_v_col = QLabel("<b>Online</b>")
        online_v_col.setFixedWidth(100)
        online_v_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        columns_layout.addWidget(online_v_col)
        
        action_col = QLabel("<b>Aktion</b>")
        action_col.setFixedWidth(130)
        action_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        columns_layout.addWidget(action_col)
        
        main_layout.addLayout(columns_layout)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop) 
        self.scroll.setWidget(self.list_container)
        main_layout.addWidget(self.scroll)

        QTimer.singleShot(100, self.check_for_updates)

    def clear_list(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # NEU: Wir müssen unsere Sortier-Liste auch leeren!
        self.addon_widgets_data.clear()

    def change_wow_path(self):
        start_dir = self.config.get_wow_path() or str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "Wähle deinen WoW 'AddOns' Ordner", start_dir)
        if folder: 
            self.config.set_wow_path(folder) 
            self.check_for_updates()

    def validate_wow_path(self):
        if not self.config.is_path_valid():
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("WoW-Pfad benötigt")
            msg.setText("Der WoW-Addon-Ordner ist nicht konfiguriert oder existiert nicht mehr.")
            msg.setInformativeText("Bitte wähle nun deinen 'AddOns'-Ordner aus.")
            msg.exec()
            self.change_wow_path()
            if not self.config.is_path_valid():
                return False
        return True

    def check_for_updates(self):
        if not self.validate_wow_path():
            self.status_label.setText("Warte auf gültigen WoW-Pfad...")
            self.clear_list()
            return

        self.scan_button.setEnabled(False)
        self.update_button.setEnabled(False)
        self.clear_list()
        self.available_updates.clear()
        
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        
        self.scan_worker = ScanWorker(self.config.get_wow_path())
        self.scan_worker.status_update.connect(self.status_label.setText)
        self.scan_worker.progress_update.connect(self.update_progress)
        self.scan_worker.addon_scanned.connect(self.add_scanned_addon) 
        self.scan_worker.finished.connect(self.on_scan_finished)
        self.scan_worker.start()

    def update_progress(self, current, total):
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)

    # ==========================================
    # NEU: Live Insertion-Sort
    # ==========================================
    def add_scanned_addon(self, name, local_v, online_v, update_url):
        if update_url:
            self.available_updates[name] = update_url
            
        row = AddonRowWidget(name, local_v, online_v, update_url)
        row.update_requested.connect(self.start_single_update)

        # NEU: Das Signal mit der neuen Funktion für manuelle Suche verbinden
        row.manual_requested.connect(self.open_manual_search)
        
        # 1. Wir vergeben eine Priorität (0 = Update, 1 = Kein Update)
        priority = 0 if update_url else 1
        
        # 2. Unser Sortier-Schlüssel (Tupel: Erst Prio, dann Name)
        sort_key = (priority, name.lower())
        
        # 3. Wir suchen den exakten Index, an dem das neue Element eingefügt werden muss
        insert_index = 0
        for i, (existing_key, _) in enumerate(self.addon_widgets_data):
            # Sobald unser neuer Schlüssel kleiner ist als der existierende, haben wir den Platz!
            if sort_key < existing_key:
                break
            insert_index = i + 1
            
        # 4. In unsere Datenliste einfügen...
        self.addon_widgets_data.insert(insert_index, (sort_key, row))
        
        # 5. ...und in das visuelle Layout exakt an dieser Stelle einfügen!
        self.list_layout.insertWidget(insert_index, row)

    def on_scan_finished(self):
        self.progress_bar.hide()
        self.scan_button.setEnabled(True)
        self.update_button.setEnabled(len(self.available_updates) > 0)
        
        if not self.available_updates and self.list_layout.count() == 0:
            self.status_label.setText("Keine Addons in diesem Ordner gefunden.")
        else:
            self.status_label.setText(f"Scan beendet. {len(self.available_updates)} Updates verfügbar.")

    def start_update_thread(self):
        self.scan_button.setEnabled(False)
        self.update_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        
        self.worker = UpdateWorker(self.available_updates, self.config.get_wow_path())
        self.worker.status_update.connect(self.status_label.setText)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.finished.connect(self.on_updates_finished)
        self.worker.start()

    def start_single_update(self, name, url):
        self.scan_button.setEnabled(False)
        self.update_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(1)
        self.progress_bar.show()
        
        self.worker = UpdateWorker({name: url}, self.config.get_wow_path())
        self.worker.status_update.connect(self.status_label.setText)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.finished.connect(self.on_updates_finished)
        self.worker.start()

    def on_updates_finished(self):
        self.progress_bar.hide()
        self.check_for_updates() 

    def open_manual_search(self, addon_name):
        """
        Öffnet den Browser und zeigt den Drag & Drop Dialog.
        """
        safe_name = urllib.parse.quote(addon_name)
        search_url = f"https://www.curseforge.com/wow/addons/search?search={safe_name}"
        webbrowser.open(search_url)
        
        # 1. Dialog erstellen und anzeigen
        dialog = DragDropDialog(addon_name, self)
        
        # .exec() pausiert den Code hier, bis der Dialog geschlossen wird
        if dialog.exec(): 
            zip_path = dialog.zip_path
            
            if zip_path:
                self.status_label.setText(f"Installiere manuelles Update für {addon_name}...")
                QApplication.processEvents() # Zwingt die GUI, das Label-Update sofort zu zeichnen
                
                # 2. Die lokale Installation starten
                success, message = install_local_addon(zip_path, self.config.get_wow_path(), addon_name)
                
                if success:
                    QMessageBox.information(self, "Erfolg", f"{addon_name} wurde manuell aktualisiert!")
                    # 3. Liste neu laden, um die neue Version in der .toc zu erkennen!
                    self.check_for_updates() 
                else:
                    QMessageBox.warning(self, "Fehler", message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AddonManagerWindow()
    window.show()
    sys.exit(app.exec())