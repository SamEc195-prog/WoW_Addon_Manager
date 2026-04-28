import requests
import urllib.parse
import re

def get_latest_github_release(repo_name, client_type="retail"):
    """Holt das neueste Release und schließt falsche WoW-Clients rigoros aus."""
    url = f"https://api.github.com/repos/{repo_name}/releases/latest"
    headers = {"User-Agent": "WoWAddonManager-PortfolioProject"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            version = data.get("tag_name")
            
            for asset in data.get("assets", []):
                asset_name = asset.get("name", "").lower()
                
                if asset_name.endswith(".zip"):
                    # Die erweiterte Blacklist: Enthält nun auch "bcc" für Burning Crusade Classic
                    if client_type == "retail" and any(x in asset_name for x in ["classic", "cata", "tbc", "bcc", "wrath", "era", "mists", "mop"]):
                        continue
                        
                    return version, asset.get("browser_download_url")
                    
        return None, None
    except requests.exceptions.RequestException:
        return None, None

def get_latest_curseforge_release(project_id, client_type="retail"):
    """
    Fragt die CFWidget-API ab und nutzt einen strikten Blacklist-Ansatz, 
    um falsche Client-Dateien anhand ihres Datei- und Anzeigenamens auszuschließen.
    """
    url = f"https://api.cfwidget.com/{project_id}"
    headers = {"User-Agent": "WoWAddonManager-PortfolioProject"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            files = data.get("files", [])
            
            for file_info in files:
                file_type = str(file_info.get("type", "")).lower()
                version_name = str(file_info.get("display", "")).lower()
                file_name_real = str(file_info.get("name", "")).lower()
                
                full_name_check = f"{version_name} {file_name_real}"
                
                if "alpha" in file_type or "beta" in file_type or "alpha" in full_name_check or "beta" in full_name_check:
                    continue 
                
                # ==========================================
                # Das erweiterte Blacklist-Verfahren
                # ==========================================
                classic_keywords = ["classic", "era"]
                tbc_keywords = ["tbc", "bcc", "burningcrusade"] # Hier wurde "bcc" ergänzt
                wrath_keywords = ["wrath", "wotlk"]
                cata_keywords = ["cata"]
                mists_keywords = ["mists", "mop", "pandaria"]
                
                if client_type == "retail":
                    all_old_keywords = classic_keywords + tbc_keywords + wrath_keywords + cata_keywords + mists_keywords
                    if any(kw in full_name_check for kw in all_old_keywords):
                        continue 
                
                elif client_type == "classic":
                    all_other_keywords = tbc_keywords + wrath_keywords + cata_keywords + mists_keywords + ["retail"]
                    if any(kw in full_name_check for kw in all_other_keywords):
                        continue
                        
                    game_versions = file_info.get("versions", [])
                    has_classic_version = any(str(v).startswith("1.") for v in game_versions)
                    has_classic_name = any(kw in full_name_check for kw in classic_keywords)
                    
                    if not (has_classic_name or has_classic_version):
                        continue
                    
                version = file_info.get("display")
                file_id = str(file_info.get("id", ""))
                file_name = str(file_info.get("name", ""))
                
                if file_id and file_name:
                    part1 = file_id[:-3]
                    part2 = file_id[-3:]
                    safe_file_name = urllib.parse.quote(file_name)
                    download_url = f"https://edge.forgecdn.net/files/{part1}/{part2}/{safe_file_name}"
                else:
                    download_url = file_info.get("url")
                
                return version, download_url
                
        return None, None
    except requests.exceptions.RequestException:
        return None, None

def get_latest_wago_release(wago_id):
    """Prüft die Wago-API auf neue Versionen und filtert Vorabversionen."""
    url = f"https://addons.wago.io/api/projects/{wago_id}/version"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            version = data.get("version", "")
            
            if "alpha" in version.lower() or "beta" in version.lower():
                return None, None
                
            download_url = data.get("downloadUrl")
            return version, download_url
            
        return None, None
    except requests.exceptions.RequestException:
        return None, None

def scrape_curseforge_id(addon_name, client_type="retail"):
    """
    Sucht die CurseForge Project-ID via Web-Scraping.
    Passt die gesuchte URL dynamisch an den WoW-Client an.
    """
    slug = re.sub(r'[\s_]+', '-', addon_name).lower()
    
    # Viele Addon-Autoren hängen bei separaten Projekten "-classic" an die URL an
    if client_type == "classic" and "classic" not in slug:
        slug += "-classic"
        
    url = f"https://www.curseforge.com/wow/addons/{slug}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            match = re.search(r'class="project-id">(\d+)</span>', response.text)
            if match:
                return match.group(1)
        
        # Fallback: Wenn z.B. "leatrix-plus-classic" nicht gefunden wird, 
        # wird es noch einmal ohne Suffix (falls alles in einem Projekt liegt) versucht
        if client_type == "classic" and slug.endswith("-classic"):
            return scrape_curseforge_id(addon_name, "retail")
                
        return None
    except requests.exceptions.RequestException:
        return None