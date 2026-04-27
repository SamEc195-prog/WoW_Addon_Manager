import requests
import urllib.parse # NEU: Für sichere URL-Generierung

def get_latest_github_release(repo_name):
    url = f"https://api.github.com/repos/{repo_name}/releases/latest"
    headers = {"User-Agent": "MeinWoWAddonManager-PortfolioProject"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            version = data.get("tag_name")
            download_url = None
            
            assets = data.get("assets", [])
            for asset in assets:
                if asset.get("name", "").endswith(".zip"):
                    download_url = asset.get("browser_download_url")
                    break 
                    
            return version, download_url
        return None, None
    except requests.exceptions.RequestException:
        return None, None

def get_latest_curseforge_release(project_id):
    url = f"https://api.cfwidget.com/{project_id}"
    headers = {"User-Agent": "MeinWoWAddonManager-PortfolioProject"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            files = data.get("files", [])
            
            for file_info in files:
                file_type = str(file_info.get("type", "")).lower()
                version_name = str(file_info.get("display", "")).lower()
                
                if "alpha" in file_type or "beta" in file_type or "alpha" in version_name or "beta" in version_name:
                    continue 
                    
                version = file_info.get("display")
                
                file_id = str(file_info.get("id", ""))
                file_name = str(file_info.get("name", ""))
                
                if file_id and file_name:
                    part1 = file_id[:-3]
                    part2 = file_id[-3:]
                    
                    # NEU: urllib.parse kümmert sich um ALLE Sonderzeichen (Leerzeichen, +, & etc.)
                    safe_file_name = urllib.parse.quote(file_name)
                    
                    # NEU: Wir nutzen den "edge" Server statt den "media" Server
                    download_url = f"https://edge.forgecdn.net/files/{part1}/{part2}/{safe_file_name}"
                else:
                    download_url = file_info.get("url")
                
                return version, download_url
                
        return None, None
    except requests.exceptions.RequestException:
        return None, None

def get_latest_wago_release(wago_id):
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

# In api_client.py
import re # Wenn nicht schon oben importiert

def scrape_curseforge_id(addon_name):
    """
    Versucht die CurseForge Project-ID durch Web-Scraping der HTML-Seite zu finden.
    Formatiert den Addon-Namen zu einer mutmaßlichen CurseForge-URL.
    """
    # 1. URL-Slug generieren (z.B. "Decor Vendor" -> "decor-vendor")
    # Wir ersetzen Leerzeichen und Unterstriche durch Bindestriche und machen alles klein.
    slug = re.sub(r'[\s_]+', '-', addon_name).lower()
    url = f"https://www.curseforge.com/wow/addons/{slug}"
    
    # 2. Spoofing-Headers nutzen, um Cloudflare nicht zu triggern
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        # Nur wenn die Seite existiert (200 OK) durchsuchen wir das HTML
        if response.status_code == 200:
            # 3. Mit RegEx die von dir gefundene project-id Klasse suchen
            match = re.search(r'class="project-id">(\d+)</span>', response.text)
            if match:
                return match.group(1)
                
        return None
    except requests.exceptions.RequestException:
        return None