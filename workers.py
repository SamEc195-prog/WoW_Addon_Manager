import re
from PyQt6.QtCore import QThread, pyqtSignal
from installer import download_and_install_addon
from scanner import scan_for_addons
from api_client import get_latest_github_release, get_latest_curseforge_release, get_latest_wago_release, scrape_curseforge_id

def clean_version(version_str):
    """Extrahiert die reine Versionsnummer aus einem String und entfernt störende Buchstaben."""
    if not version_str:
        return ""
    match = re.search(r'(\d+[\.\d]*)', version_str)
    return match.group(1) if match else version_str.strip()

class ScanWorker(QThread):
    """Führt den Scan-Vorgang im Hintergrund aus."""
    progress_update = pyqtSignal(int, int) 
    status_update = pyqtSignal(str)
    addon_scanned = pyqtSignal(str, str, str, str) 
    finished = pyqtSignal()

    def __init__(self, wow_path):
        super().__init__()
        self.wow_path = wow_path
        
        # NEU: Client-Typ anhand des Dateipfades ableiten
        self.client_type = "retail" # Standardwert
        path_lower = self.wow_path.lower()
        if "_classic_" in path_lower or "_classic_era_" in path_lower:
            self.client_type = "classic"
        # Man könnte hier noch _ptr_ oder _beta_ hinzufügen

    def run(self):
        self.status_update.emit(f"Lese lokale {self.client_type.capitalize()}-Addons...")
        addons = scan_for_addons(self.wow_path)
        total = len(addons)
        
        if total == 0:
            self.finished.emit()
            return

        for i, (name, data) in enumerate(addons.items()):
            self.status_update.emit(f"Prüfe {name}...")
            self.progress_update.emit(i, total)
            
            local_v = data["version"]
            online_v, url = None, None
            current_curse_id = data["curse_id"]
            
            if not current_curse_id and not data["github_repo"] and not data["wago_id"]:
                self.status_update.emit(f"Scrape ID für {name}...")
                current_curse_id = scrape_curseforge_id(name, self.client_type)
            
            # API-Abfragen mit Übergabe des Client-Typs
            if data["github_repo"]:
                online_v, url = get_latest_github_release(data["github_repo"], self.client_type)
            
            if not online_v and current_curse_id:
                online_v, url = get_latest_curseforge_release(current_curse_id, self.client_type)
                
            if not online_v and data["wago_id"]:
                # Wago trennt IDs pro Spielversion meistens direkt auf der Plattform, 
                # daher ist hier ein Filter seltener nötig.
                online_v, url = get_latest_wago_release(data["wago_id"])
                
            clean_local = clean_version(local_v)
            clean_online = clean_version(online_v) if online_v else None
            
            actual_update_url = url if (clean_online and clean_online != clean_local) else ""
            
            self.addon_scanned.emit(name, clean_local, clean_online or "-", actual_update_url)
        
        self.progress_update.emit(total, total) 
        self.status_update.emit("Scan abgeschlossen!")
        self.finished.emit()

class UpdateWorker(QThread):
    """Verarbeitet den Download und die Installation von Addon-Updates im Hintergrund."""
    progress_update = pyqtSignal(int, int)
    status_update = pyqtSignal(str) 
    finished = pyqtSignal()         

    def __init__(self, updates_dict, wow_path):
        super().__init__()
        self.updates_dict = updates_dict
        self.wow_path = wow_path

    def run(self):
        total = len(self.updates_dict)
        for i, (name, url) in enumerate(self.updates_dict.items()):
            self.progress_update.emit(i, total)
            self.status_update.emit(f"Aktualisiere {name} ({i+1}/{total})...")
            download_and_install_addon(url, self.wow_path, name)
            
        self.progress_update.emit(total, total)
        self.status_update.emit("Alle Updates abgeschlossen!")
        self.finished.emit()