import os
import re
import subprocess
import sys

def time_to_seconds(time_str):
    """Wandelt Formate wie '18:30h' oder '06:15h' sicher in Sekunden um."""
    total_sec = 0
    match = re.search(r'(\d+):(\d+)h', time_str)
    if match:
        total_sec += int(match.group(1)) * 3600
        total_sec += int(match.group(2)) * 60
    return total_sec

def seconds_to_fmt(seconds):
    """Formatiert Sekunden zurück in 'XXh YYm'."""
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h {m}m"

def git_push(directory):
    """Führt git add, commit und push für das Repository aus."""
    os.chdir(directory)
    
    # Prüfen, ob es Änderungen gibt
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if not result.stdout.strip():
        print("ℹ️  Keine Änderungen zu pushen.")
        return
    
    # Dateien gezielt hinzufügen (nur das, was ins Repo soll)
    berichte = [f for f in os.listdir(directory) if f.startswith("Bericht_") and f.endswith(".html")]
    dateien_zum_adden = ["Archiv_Index.html", "Archiv_Index_html_erstellen.py", ".gitignore"] + berichte
    
    subprocess.run(["git", "add", "--"] + dateien_zum_adden)
    
    # Commit (nur wenn es wirklich Änderungen gibt)
    commit_result = subprocess.run(["git", "commit", "-m", "Archiv aktualisiert"], capture_output=True, text=True)
    if commit_result.returncode != 0 and "nothing to commit" in commit_result.stderr:
        print("ℹ️  Keine Änderungen zu committen.")
        return
    
    # Push
    push_result = subprocess.run(["git", "push"], capture_output=True, text=True)
    if push_result.returncode == 0:
        print("✅ Änderungen erfolgreich nach GitHub gepusht.")
    else:
        print(f"❌ Push fehlgeschlagen:\n{push_result.stderr}")

def generate_index():
    directory = os.path.dirname(os.path.abspath(__file__))
    files = [f for f in os.listdir(directory) if f.startswith("Bericht_") and f.endswith(".html")]
    
    if not files:
        print("Keine Berichte gefunden!")
        return

    def dso_sort_key(filename):
        pure_name = re.sub(r'^Bericht_\d{4}_', '', filename).lower()
        return [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', pure_name)]

    files.sort(key=dso_sort_key)

    processed_files = []
    total_seconds_all = 0
    total_frames_all = 0

    for file in files:
        path = os.path.join(directory, file)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Daten aus der summen-zeile
            match = re.search(r"<tr class='summen-zeile'>.*?<td.*?>(\d+)</td>\s*<td.*?>(.*?)</td>", content, re.DOTALL)
            frame_val = match.group(1) if match else "0"
            time_val = match.group(2) if match else "00:00h"
            
            # Bild-Extraktion
            img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content)
            thumb_src = img_match.group(1) if img_match else ""
            
            sec = time_to_seconds(time_val)
            total_seconds_all += sec
            total_frames_all += int(frame_val)
            
            jahr = re.search(r'Bericht_(\d{4})_', file).group(1) if re.search(r'Bericht_(\d{4})_', file) else "????"
            display_name = re.sub(r'^Bericht_\d{4}_', '', file).replace(".html", "").replace("_", " ")
            
            processed_files.append({
                'file': file,
                'name': display_name,
                'jahr': jahr,
                'zeit': time_val,
                'frames': frame_val,
                'seconds': sec,
                'thumb': thumb_src
            })

    html_content = f"""
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <title>Astro-Fotoberichtarchiv</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0b0e14; color: #e0e0e0; margin: 30px; }}
            .container {{ max-width: 1600px; margin: auto; }}
            h1 {{ color: #4e9af1; text-align: center; font-weight: 300; letter-spacing: 1px; margin-bottom: 30px; }}
            
            .dashboard {{ 
                display: flex; justify-content: center; gap: 60px; background: #16213e; 
                padding: 20px; border-radius: 12px; border: 1px solid #1f4068; margin-bottom: 30px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            }}
            .stat-item {{ text-align: center; }}
            .stat-val {{ display: block; font-size: 1.6em; font-weight: bold; color: #4e9af1; }}
            .stat-label {{ font-size: 0.8em; color: #95a5a6; text-transform: uppercase; letter-spacing: 1px; }}

            .filter-box {{ text-align: center; margin-bottom: 30px; }}
            #yearFilter {{ 
                padding: 12px 25px; width: 400px; border-radius: 25px; border: 1px solid #1f4068;
                background: #1a1a2e; color: white; text-align: center; outline: none; transition: 0.3s; font-size: 1em;
            }}
            #yearFilter:focus {{ border-color: #4e9af1; box-shadow: 0 0 12px rgba(78, 154, 241, 0.4); }}

            /* Optimiertes Grid für 1600px Breite */
            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 25px; }}
            
            .card {{ 
                background: #16213e; border-radius: 10px; border: 1px solid #1f4068; 
                display: flex; flex-direction: column; position: relative; transition: 0.3s; overflow: hidden;
            }}
            .card:hover {{ transform: translateY(-5px); border-color: #4e9af1; box-shadow: 0 8px 20px rgba(0,0,0,0.4); }}
            
            .card-header {{ padding: 15px; position: relative; }}
            /* Padding-Right verhindert Überlappung mit dem Jahr-Badge */
            .card h3 {{ margin: 0; color: #fff; font-size: 1.2em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding-right: 65px; }}
            
            .thumb-box {{ width: 100%; height: 180px; background: #000; overflow: hidden; border-top: 1px solid #1f4068; border-bottom: 1px solid #1f4068; }}
            .thumb-box img {{ width: 100%; height: 100%; object-fit: cover; opacity: 0.85; transition: 0.5s; }}
            .card:hover .thumb-box img {{ opacity: 1; transform: scale(1.08); }}

            .card-body {{ padding: 12px 15px; font-size: 0.9em; background: rgba(15, 52, 96, 0.3); }}
            .info-row {{ display: flex; justify-content: space-between; margin-bottom: 5px; color: #95a5a6; }}
            .val-highlight {{ color: #4e9af1; font-weight: 600; }}

            .year-badge {{ 
                position: absolute; top: 14px; right: 15px; background: #0f3460; color: #4e9af1; 
                padding: 2px 8px; border-radius: 5px; font-size: 0.8em; border: 1px solid #4e9af1; font-weight: bold;
                z-index: 5;
            }}
            
            .open-link {{ text-decoration: none; color: inherit; height: 100%; display: flex; flex-direction: column; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⭐ Astro-Fotoberichtarchiv</h1>
            
            <div class="dashboard">
                <div class="stat-item"><span class="stat-val" id="statObj">{len(files)}</span><span class="stat-label">Objekte</span></div>
                <div class="stat-item"><span class="stat-val" id="statTime">{seconds_to_fmt(total_seconds_all)}</span><span class="stat-label">Gesamtzeit</span></div>
                <div class="stat-item"><span class="stat-val" id="statFrames">{total_frames_all}</span><span class="stat-label">Frames</span></div>
            </div>

            <div class="filter-box">
                <input type="text" id="yearFilter" onkeyup="filter()" placeholder="Objektname oder Jahr eingeben...">
            </div>

            <div class="grid" id="reportGrid">
    """

    for item in processed_files:
        img_tag = f'<img src="{item["thumb"]}" loading="lazy">' if item["thumb"] else '<div style="height:100%; display:flex; align-items:center; justify-content:center; color:#333; font-size:0.8em;">Kein Vorschaubild</div>'
        
        html_content += f"""
                <div class="card" data-year="{item['jahr']}" data-name="{item['name']}" data-sec="{item['seconds']}" data-frames="{item['frames']}">
                    <a href="{item['file']}" target="_blank" class="open-link">
                        <span class="year-badge">{item['jahr']}</span>
                        <div class="card-header">
                            <h3 title="{item['name']}">{item['name']}</h3>
                        </div>
                        <div class="thumb-box">
                            {img_tag}
                        </div>
                        <div class="card-body">
                            <div class="info-row"><span>Belichtung:</span><span class="val-highlight">{item['zeit']}</span></div>
                            <div class="info-row"><span>Frames:</span><span class="val-highlight">{item['frames']}</span></div>
                        </div>
                    </a>
                </div>
        """

    html_content += """
            </div>
        </div>
        <script>
            function filter() {
                var val = document.getElementById('yearFilter').value.toLowerCase();
                var cards = document.getElementsByClassName('card');
                var count = 0, totalSec = 0, totalFrames = 0;

                for (var i = 0; i < cards.length; i++) {
                    var txt = cards[i].getAttribute('data-year') + " " + cards[i].getAttribute('data-name').toLowerCase();
                    if (txt.indexOf(val) > -1) {
                        cards[i].style.display = "";
                        count++;
                        totalSec += parseInt(cards[i].getAttribute('data-sec'));
                        totalFrames += parseInt(cards[i].getAttribute('data-frames'));
                    } else {
                        cards[i].style.display = "none";
                    }
                }
                document.getElementById('statObj').innerText = count;
                document.getElementById('statFrames').innerText = totalFrames;
                var h = Math.floor(totalSec / 3600), m = Math.floor((totalSec % 3600) / 60);
                document.getElementById('statTime').innerText = h + "h " + m + "m";
            }
        </script>
    </body>
    </html>
    """

    index_path = os.path.join(directory, "Archiv_Index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    os.startfile(index_path)

if __name__ == "__main__":
    push_mode = "--push" in sys.argv or "-p" in sys.argv
    generate_index()
    if push_mode:
        directory = os.path.dirname(os.path.abspath(__file__))
        git_push(directory)