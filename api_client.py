import requests
import urllib.parse
import re

def get_latest_github_release(repo_name):
    """Holt die neueste Release-Version und den Download-Link aus einem GitHub-Repository."""
    url = f"https://api.github.com/repos/{repo_name}/releases/latest"
    headers = {"User-Agent": "WoWAddonManager-PortfolioProject"}
    
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
    """Fragt die CFWidget-API ab und konstruiert den direkten CDN-Download-Link."""
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
                
                # Ignoriert experimentelle Alpha- oder Beta-Versionen
                if "alpha" in file_type or "beta" in file_type or "alpha" in version_name or "beta" in version_name:
                    continue 
                    
                version = file_info.get("display")
                file_id = str(file_info.get("id", ""))
                file_name = str(file_info.get("name", ""))
                
                if file_id and file_name:
                    part1 = file_id[:-3]
                    part2 = file_id[-3:]
                    
                    # URL-Encoding für den sicheren Umgang mit Sonderzeichen im Dateinamen
                    safe_file_name = urllib.parse.quote(file_name)
                    
                    # Nutzt den Edge-Server für direkten Datei-Zugriff
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

def scrape_curseforge_id(addon_name):
    """
    Versucht die CurseForge Project-ID durch Web-Scraping der HTML-Seite zu finden.
    Formatiert den Addon-Namen vorab zu einer mutmaßlichen CurseForge-URL.
    """
    # URL-Slug generieren (z.B. "Decor Vendor" -> "decor-vendor")
    slug = re.sub(r'[\s_]+', '-', addon_name).lower()
    url = f"https://www.curseforge.com/wow/addons/{slug}"
    
    # Spoofing-Header verhindern die Blockierung durch Cloudflare
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        # HTML-Parsing wird nur bei erfolgreichem Seitenabruf durchgeführt
        if response.status_code == 200:
            match = re.search(r'class="project-id">(\d+)</span>', response.text)
            if match:
                return match.group(1)
                
        return None
    except requests.exceptions.RequestException:
        return None