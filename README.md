# Projekt-Dokumentation: WoW Addon-Manager (Python)

## 1. Bisheriger Fortschritt
* **Projekt-Setup:** Einrichtung der Entwicklungsumgebung (Python & Visual Studio Code) sowie Erstellung einer Test-Umgebung (`dummy_wow`), die das Dateisystem von World of Warcraft simuliert.
* **Kernlogik (Lokale Erkennung):** Erfolgreiche Implementierung des Backend-Motors. Das Programm kann lokale WoW-Addons scannen und deren Metadaten auslesen.
* **Plattformunabhängigkeit:** Der Code wurde von Beginn an mit dem Modul `pathlib` geschrieben, um plattformübergreifend (Windows, macOS, Linux/SteamDeck) fehlerfrei mit Dateipfaden arbeiten zu können.
* **Fehlerbehandlung (Exception Handling):** Implementierung von `try-except`-Blöcken und UTF-8-Encoding, um Abstürze bei fehlerhaften oder internationalisierten Textdateien zu verhindern.

## 2. Aktuelle Projektstruktur
Das Projekt ist derzeit modular aufgebaut und trennt die Funktionalitäten in saubere Methoden:

**Dateibaum:**
```text
MeinAddonManager/
├── main.py                 # Das Hauptskript mit der Kernlogik
└── dummy_wow/              # Simulierte WoW-Ordnerstruktur für Tests
    └── Interface/
        └── AddOns/
            ├── MeinAddon/
            │   └── MeinAddon.toc
            └── DeadlyBossMods/
                └── DeadlyBossMods.toc
```

**Code-Architektur (`main.py`):**
1. `extract_version_from_toc(toc_path)`: Öffnet die `.toc`-Datei eines Addons, sucht gezielt nach dem String `## Version:` und extrahiert die Versionsnummer sicher.
2. `scan_for_addons(addons_dir_str)`: Iteriert durch das lokale Addon-Verzeichnis, identifiziert gültige Addon-Ordner und verknüpft diese mit der extrahierten Versionsnummer.
3. **Datenstruktur:** Das Ergebnis des Scans wird in einem dynamischen *Dictionary* (Schlüssel-Wert-Paare) gespeichert (z. B. `{"MeinAddon": "1.0.5"}`), welches das Fundament für zukünftige Versionsabgleiche bildet.

## 3. Nächste geplante Schritte (Roadmap)

* **Phase 2: Netzwerk-Requests & APIs (Datenbeschaffung)**
  * Anbindung an externe Datenbanken (z. B. GitHub API oder Wago API).
  * Automatischer Abgleich der lokal installierten Versionen (aus unserem Dictionary) mit den aktuellsten Versionen im Netz.
* **Phase 3: Download & Dateimanagement**
  * Herunterladen neuer `.zip`-Archive bei verfügbaren Updates.
  * Sicheres Löschen veralteter Addon-Ordner und Entpacken der neuen Dateien in das lokale Verzeichnis.
* **Phase 4: Grafische Benutzeroberfläche (GUI)**
  * Entwicklung eines modernen, plattformübergreifenden Frontends (z. B. mit *PyQt/PySide6*).
  * Verknüpfung der GUI-Buttons mit der Backend-Logik.
* **Phase 5: Performance & Deployment**
  * Integration von *Multi-Threading*, damit die Benutzeroberfläche während der Downloads flüssig bleibt.
  * "Packaging" (Kompilieren) der Python-Skripte in ausführbare, native Dateien (`.exe` für Windows, `.app` für macOS, Linux-kompatible Formate für das SteamDeck).