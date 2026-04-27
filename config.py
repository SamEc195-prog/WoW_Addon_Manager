from PyQt6.QtCore import QSettings
from pathlib import Path

class ConfigManager:
    """Verwaltet alle lokalen Einstellungen der Anwendung."""
    
    def __init__(self):
        # QSettings kümmert sich automatisch um Registry (Win) oder .plist (Mac)
        self.settings = QSettings("PortfolioProject", "WoWAddonManager")

    def get_wow_path(self):
        """Gibt den gespeicherten Pfad zurück (oder einen leeren String)."""
        return self.settings.value("wow_path", "")

    def set_wow_path(self, path):
        """Speichert den Pfad dauerhaft im System."""
        self.settings.setValue("wow_path", path)

    def is_path_valid(self):
        """Prüft, ob der gespeicherte Pfad existiert und gültig ist."""
        path = self.get_wow_path()
        return bool(path and Path(path).exists())