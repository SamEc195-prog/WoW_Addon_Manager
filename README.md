# WoW Addon Manager

<img width="479" height="448" alt="wowam-v1-screenshot" src="https://github.com/user-attachments/assets/712dddb8-3edd-4376-9446-97d645923bc9" />

</br>

Ein plattformübergreifender, performanter Addon-Manager für World of Warcraft, entwickelt in **Python 3** und **PyQt6**.

Dieses Projekt orientiert sich optisch und funktional an professionellen Vorbildern wie CurseForge, bietet jedoch eine leichtgewichtige, offene und werbefreie Alternative. Besonderer Wert wurde auf eine saubere Softwarearchitektur (Separation of Concerns), Ausfallsicherheit und eine exzellente User Experience (UX) gelegt.

---

## Features

- **Asynchrone Performance:** Die Benutzeroberfläche bleibt dank Multithreading (PyQt6 `QThread`) beim Scannen und Herunterladen stets flüssig.
- **Multi-API Kaskade:** Intelligente Update-Suche über verschiedene Quellen (GitHub Releases -> CurseForge via CFWidget -> Wago). Alpha- und Beta-Versionen werden automatisch herausgefiltert.
- **Cloudflare Bypass & Direct CDN:** Umgeht aggressive Hotlink-Sperren durch strategisches Browser-Spoofing (User-Agent & Referer) und generiert direkte Download-URLs (edge.forgecdn.net).
- **Smart 3-Tier Sorting:** Eine Live-Insertion-Sortierung ordnet Addons automatisch nach Priorität:
  1. Updates verfügbar (Handlungsbedarf)
  2. Manuelle Suche erforderlich (Nicht verfolgt)
  3. Aktuell (Up to date)
- **Manueller Drag & Drop Fallback:** Fehlen API-Daten, bietet der Manager einen One-Click-Zugang zur CurseForge-Websuche und akzeptiert manuell heruntergeladene `.zip`-Dateien per Drag & Drop für eine saubere Auto-Installation.
- **Lokale Override-Datenbank:** Eine `database.json` füllt fehlende Metadaten in `.toc`-Dateien automatisch auf (Case-Insensitive).

---

## Architektur (Separation of Concerns)

Das Projekt folgt strikten MVC-Prinzipien, um Logik, Netzwerk, Daten und UI strikt voneinander zu trennen:

- **`gui.py` (View / Controller):** Die PyQt6-Oberfläche. Verwaltet dynamische Listen, Drag&Drop-Dialoge und reagiert asynchron auf Worker-Signale.
- **`workers.py` (Service):** Kapselt langlaufende Prozesse (`ScanWorker`, `UpdateWorker`) in Hintergrund-Threads, um UI-Freezes zu verhindern.
- **`scanner.py` (Logik):** Parst lokale `.toc`-Dateien via RegEx und füllt fehlende Daten durch die Override-Datenbank auf.
- **`api_client.py` (Netzwerk):** Behandelt alle externen API-Aufrufe (GitHub, CurseForge, Wago). Isoliert Netzwerkausfälle vom Rest des Programms.
- **`installer.py` (File Management):** Verwaltet das Dateisystem. Löscht alte Versionen sicher und entpackt neue ZIP-Archive (sowohl aus dem Netz als auch lokal gedroppt).
- **`config.py` (Model):** Nutzt `QSettings` für die persistente, plattformübergreifende Speicherung des WoW-Ordnerpfads.

---

## Tech Stack

- **Sprache:** Python 3.10+
- **GUI-Framework:** PyQt6
- **Netzwerk:** `requests`, `urllib`
- **Datenverarbeitung:** `json`, `re` (RegEx), `pathlib`

---

## Installation & Start

1. Repository klonen:
   ```bash
   git clone [https://github.com/DEIN_NAME/wow-addon-manager.git](https://github.com/DEIN_NAME/wow-addon-manager.git)
   cd wow-addon-manager
   ```
2. Abhängigkeiten installieren:

   ```bash
   pip install -r requirements.txt
   ```

   (Hinweis: requirements.txt sollte PyQt6 und requests enthalten)

3. Programm starten:

```bash
   python gui.py
```

## Roadmap / Next Steps

[x] Grundlegendes Parsing der .toc Dateien

[x] API-Anbindungen (GitHub, CurseForge, Wago)

[x] Drag & Drop Installation für Randfälle

[ ] Funktionen erweitern: Deinstallation der Addons

[ ] Zu jedem Addon das entsprechende Icon anzeigen
