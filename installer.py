import requests
import zipfile
import shutil
from pathlib import Path

def download_and_install_addon(download_url, wow_addons_dir, addon_name):
    """Lädt ein Addon als ZIP herunter, löscht die alte Version und entpackt die neue."""
    addons_path = Path(wow_addons_dir)
    zip_path = addons_path / f"{addon_name}_update.zip"
    
    print(f"  -> Lade {addon_name} herunter...")
    try:
        # Header-Anpassungen (Spoofing) zur Umgehung von Cloudflare und Hotlink-Protection
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/zip, application/octet-stream, */*",
            "Referer": "https://www.curseforge.com/",
            "Origin": "https://www.curseforge.com"
        }
        
        response = requests.get(download_url, headers=headers, stream=True, timeout=15)
        response.raise_for_status() 
        
        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
    except Exception as e:
        print(f"  -> Fehler beim Download: {e}")
        return False

    # Löscht das alte Verzeichnis vor dem Entpacken
    old_addon_path = addons_path / addon_name
    if old_addon_path.exists():
        print("  -> Lösche alte Version...")
        shutil.rmtree(old_addon_path, ignore_errors=True)

    # Entpackt das heruntergeladene Archiv
    print("  -> Entpacke neue Version...")
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(addons_path)
    except Exception as e:
        print(f"  -> Fehler beim Entpacken: {e}")
        return False

    # Bereinigt das temporäre ZIP-Archiv
    zip_path.unlink(missing_ok=True)
    print(f"  -> Update erfolgreich abgeschlossen!\n")
    return True

def install_local_addon(zip_file_path, wow_addons_dir, addon_name):
    """Entpackt ein lokal bereitgestelltes ZIP-Archiv in den WoW-Ordner."""
    addons_path = Path(wow_addons_dir)
    zip_path = Path(zip_file_path)

    if not zip_path.exists() or zip_path.suffix.lower() != '.zip':
        return False, "Ungültige Datei. Bitte eine .zip Datei verwenden."

    old_addon_path = addons_path / addon_name
    if old_addon_path.exists():
        try:
            shutil.rmtree(old_addon_path, ignore_errors=True)
        except Exception as e:
            return False, f"Fehler beim Löschen der alten Version: {e}"

    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(addons_path)
    except Exception as e:
        return False, f"Fehler beim Entpacken: {e}"

    return True, "Erfolgreich installiert!"