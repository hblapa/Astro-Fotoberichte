import os
import re
from datetime import datetime

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
    total_seconds_all = 0  # Einheitlich benannt
    total_frames_all = 0    # Einheitlich benannt

    for file in files:
        path = os.path.join(directory, file)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Sucht die summen-zeile und greift die Werte für Frames und Zeit ab
            match = re.search(r"<tr class='summen-zeile'>.*?<td.*?>(\d+)</td>\s*<td.*?>(.*?)</td>", content, re.DOTALL)
            
            frame_val = match.group(1) if match else "0"
            time_val = match.group(2) if match else "00:00h"
            
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
                'seconds': sec
            })

    html_content = f"""
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <title>Astro-Fotoarchiv</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #1a1a2e; color: #e0e0e0; margin: 40px; }}
            .container {{ max-width: 1600px; margin: auto; }}
            h1 {{ color: #4e9af1; text-align: center; margin-bottom: 10px; }}
            
            .dashboard {{ 
                display: flex; justify-content: space-around; background: #16213e; 
                padding: 20px; border-radius: 12px; border: 1px solid #4e9af1; margin-bottom: 30px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            }}
            .stat-item {{ text-align: center; }}
            .stat-val {{ display: block; font-size: 1.5em; font-weight: bold; color: #4e9af1; }}
            .stat-label {{ font-size: 0.8em; color: #95a5a6; text-transform: uppercase; }}

            .filter-box {{ text-align: center; margin-bottom: 20px; }}
            #yearFilter {{ 
                padding: 12px; width: 300px; border-radius: 8px; border: 2px solid #0f3460;
                background: #16213e; color: white; font-size: 1.1em; outline: none;
            }}

            .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 25px; }}
            .card {{ 
                background: #16213e; border-radius: 12px; padding: 20px; border: 1px solid #0f3460; 
                display: flex; flex-direction: column; position: relative; transition: 0.2s;
            }}
            .card:hover {{ border-color: #4e9af1; transform: translateY(-3px); }}
            
            .year-badge {{ position: absolute; top: 15px; right: 15px; background: #004a99; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85em; }}
            .card h3 {{ margin: 0 0 10px 0; color: #fff; font-size: 1.25em; width: 75%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
            .card p {{ font-size: 0.9em; color: #95a5a6; }}
            .val-highlight {{ color: #4e9af1; font-weight: bold; }}
            .open-btn {{ display: inline-block; margin-top: 15px; padding: 10px; background: #004a99; color: white; text-decoration: none; border-radius: 6px; text-align: center; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⭐ Astro-Fotobericht Archiv</h1>
            
            <div class="dashboard">
                <div class="stat-item">
                    <span class="stat-val" id="statObj">{len(files)}</span>
                    <span class="stat-label">Objekte</span>
                </div>
                <div class="stat-item">
                    <span class="stat-val" id="statTime">{seconds_to_fmt(total_seconds_all)}</span>
                    <span class="stat-label">Gesamtzeit</span>
                </div>
                <div class="stat-item">
                    <span class="stat-val" id="statFrames">{total_frames_all}</span>
                    <span class="stat-label">Einzelframes</span>
                </div>
            </div>

            <div class="filter-box">
                <input type="text" id="yearFilter" onkeyup="filter()" placeholder="Jahr oder Name suchen...">
            </div>

            <div class="grid" id="reportGrid">
    """

    for item in processed_files:
        html_content += f"""
                <div class="card" data-year="{item['jahr']}" data-name="{item['name']}" data-sec="{item['seconds']}" data-frames="{item['frames']}">
                    <span class="year-badge">{item['jahr']}</span>
                    <h3 title="{item['name']}">{item['name']}</h3>
                    <p>Belichtung: <span class="val-highlight">{item['zeit']}</span><br>Frames: <span class="val-highlight">{item['frames']}</span></p>
                    <a href="{item['file']}" target="_blank" class="open-btn">Bericht öffnen</a>
                </div>
        """

    html_content += """
            </div>
        </div>
        <script>
            function filter() {
                var val = document.getElementById('yearFilter').value.toLowerCase();
                var cards = document.getElementsByClassName('card');
                
                var count = 0;
                var totalSec = 0;
                var totalFrames = 0;

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
                
                var h = Math.floor(totalSec / 3600);
                var m = Math.floor((totalSec % 3600) / 60);
                document.getElementById('statTime').innerText = h + "h " + m + "m";
            }
            filter();
        </script>
    </body>
    </html>
    """

    index_path = os.path.join(directory, "Archiv_Index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    os.startfile(index_path)

if __name__ == "__main__":
    generate_index()