import json
import re
from pathlib import Path

def load_addon_database():
    """
    Lädt die Mapping-Datenbank aus der lokalen JSON-Datei.
    Konvertiert alle Schlüssel in Kleinbuchstaben für case-insensitive Abfragen.
    """
    # Bestimmt den absoluten Pfad zur JSON-Datei relativ zum Speicherort dieses Skripts
    db_path = Path(__file__).parent / "database.json"
    
    if db_path.exists():
        try:
            with open(db_path, "r", encoding="utf-8") as file:
                content = file.read().strip() 
                if not content:
                    return {}
                    
                raw_db = json.loads(content)
                
                # Normalisiert die Schlüssel auf Kleinbuchstaben für eine tolerante Zuweisung
                safe_db = {}
                for key, value in raw_db.items():
                    safe_db[key.lower()] = value
                    
                return safe_db
                
        except Exception as e:
            print(f"Fehler beim Laden der JSON: {e}")
    else:
        print("Warnung: database.json wurde nicht gefunden!")
        
    return {}

def extract_metadata_from_toc(toc_path):
    """Liest relevante Metadaten (Version, Repository, IDs) aus einer .toc-Datei."""
    metadata = {
        "version": None, 
        "github_repo": None,
        "curse_id": None,
        "wago_id": None
    }
    
    try:
        with toc_path.open("r", encoding="utf-8") as datei:
            for zeile in datei:
                zeile = zeile.strip()
                
                if zeile.startswith("## Version:"):
                    metadata["version"] = zeile.split(":", 1)[1].strip()
                elif "github.com" in zeile:
                    match = re.search(r"github\.com/([^/]+/[^/\s]+)", zeile)
                    if match:
                        metadata["github_repo"] = match.group(1).replace(".git", "")
                elif zeile.startswith("## X-Curse-Project-ID:"):
                    metadata["curse_id"] = zeile.split(":", 1)[1].strip()
                elif zeile.startswith("## X-Wago-ID:"):
                    metadata["wago_id"] = zeile.split(":", 1)[1].strip()
                        
    except Exception as e:
        print(f"Fehler beim Lesen von {toc_path.name}: {e}")
        
    return metadata

def scan_for_addons(addons_dir_str):
    """
    Scant den angegebenen Ordner nach Addons.
    Fehlende Metadaten werden bei Übereinstimmung aus der lokalen Datenbank ergänzt.
    """
    addons_dir = Path(addons_dir_str)
    installed_addons = {}
    
    if not addons_dir.exists() or not addons_dir.is_dir():
        return installed_addons

    database = load_addon_database()

    for element in addons_dir.iterdir():
        if element.is_dir():
            toc_files = list(element.glob("*.toc"))
            
            if toc_files:
                toc_file = toc_files[0]
                metadata = extract_metadata_from_toc(toc_file)
                
                if metadata["version"]:
                    addon_name = element.name
                    addon_name_lower = addon_name.lower()
                    
                    # Überschreibt fehlende Metadaten mit Einträgen aus der JSON-Datenbank
                    if addon_name_lower in database:
                        db_entry = database[addon_name_lower] 
                        
                        if not metadata["github_repo"] and "github_repo" in db_entry:
                            metadata["github_repo"] = str(db_entry["github_repo"])
                            
                        if not metadata["curse_id"] and "curse_id" in db_entry:
                            metadata["curse_id"] = str(db_entry["curse_id"])
                            
                        if not metadata["wago_id"] and "wago_id" in db_entry:
                            metadata["wago_id"] = str(db_entry["wago_id"])
                        
                    installed_addons[addon_name] = metadata
                    
    return installed_addons