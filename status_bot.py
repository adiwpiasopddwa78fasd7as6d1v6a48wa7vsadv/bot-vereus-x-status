import time
import requests
from datetime import datetime, timezone
import os
from threading import Thread
from flask import Flask

# =======================================================
# CONFIGURATION (ตั้งค่าตรงนี้)
# =======================================================
WEBHOOK_URL = "https://discord.com/api/webhooks/1514211987234488401/dT70YrRMx2yVHSfw_Cb6Opf6VqdY8W5nOw5RQSU-qNLoGHO7ZPM5JQsH3Pfj9ei_LgYO"
API_URL = "https://api.weao.xyz/v1/status"  # ตรวจสอบ URL endpoint จาก https://docs.weao.xyz/ อีกครั้ง
CHECK_INTERVAL = 25  
FOOTER_TEXT = "Vereus X Status System"
# =======================================================

app = Flask('')

@app.route('/')
def home():
    return "<h1>Vereus X Status System v7 (Pure API) is Active!</h1>", 200

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def fetch_weao_api():
    """ดึงข้อมูลดิบจาก API ของ weao.xyz โดยตรง มั่นใจได้ว่าข้อมูลแม่นยำและไม่บัคจากโครงสร้างเว็บ"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json'
        }
        response = requests.get(API_URL, headers=headers, timeout=12)
        if response.status_code == 200:
            return "ONLINE", response.json()
        return "OFFLINE", None
    except Exception as e:
        print(f"[{time.strftime('%X')}] เชื่อมต่อ API ล้มเหลว: {e}")
        return "OFFLINE", None

def parse_status(status_raw):
    """แปลงค่าสถานะจาก API เป็นไอคอนและข้อความตามข้อกำหนด"""
    status_str = str(status_raw).lower().strip()
    if status_str in ["updated", "working", "active", "online", "true"]:
        return "🟢 Working"
    elif status_str in ["issues", "waiting fix", "maintenance", "bugged"]:
        return "🟠 Issues"
    else:
        return "🔴 Patched"

def build_embed(web_status, api_data):
    embed_color = 65280 if web_status == "ONLINE" else 16711680
    current_time_str = time.strftime('%X')
    
    embed = {
        "title": "🛡️ Executor Status by siw",
        "description": f"🌐 **WEBSITE WEAO STATUS:** {'🟢 ONLINE' if web_status == 'ONLINE' else '🔴 OFFLINE'}\n\n"
                       f"🟢 Working = UPDATE | 🟠 Issues = WAITING FIX | 🔴 Patched = DOWN",
        "color": embed_color,
        "fields": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": f"{FOOTER_TEXT} | อัปเดตล่าสุด: {current_time_str}"}
    }

    if web_status == "OFFLINE" or not api_data:
        embed["fields"].append({"name": "⚠️ System Warning", "value": "ไม่สามารถดึงข้อมูลจาก API ได้ในขณะนี้", "inline": False})
        return {"embeds": [embed]}

    # 1. ส่วนของ Roblox Version Update Tracker
    roblox = api_data.get("roblox", {})
    # ตรวจสอบโครงสร้างข้อมูลเวอร์ชัน (รองรับทั้งแบบ Object และแบบ String ตรงๆ)
    win_v = roblox.get("windows", {}).get("version", "N/A") if isinstance(roblox.get("windows"), dict) else roblox.get("windows", "N/A")
    mac_v = roblox.get("mac", {}).get("version", "N/A") if isinstance(roblox.get("mac"), dict) else roblox.get("mac", "N/A")
    and_v = roblox.get("android", {}).get("version", "N/A") if isinstance(roblox.get("android"), dict) else roblox.get("android", "N/A")
    ios_v = roblox.get("ios", {}).get("version", "N/A") if isinstance(roblox.get("ios"), dict) else roblox.get("ios", "N/A")

    roblox_tracker_text = (
        f"**Roblox Windows :** `{win_v}`\n"
        f"**Roblox Mac :** `{mac_v}`\n"
        f"**Roblox Android-iOS :** `{and_v}` / `{ios_v}`"
    )
    embed["fields"].append({"name": "🧩 Roblox Version Update Tracker", "value": roblox_tracker_text, "inline": False})

    # 2. ส่วนของรายชื่อ Executor (ดึงแบบ Dynamic วนลูปตามที่ API ส่งมาทั้งหมด ตัวใหม่จะขึ้นทันที)
    categories = {}
    exploits_list = api_data.get("exploits", api_data.get("executors", []))

    for item in exploits_list:
        name = item.get("name", "Unknown")
        version = item.get("version", "N/A")
        price = item.get("price", "Free")
        status_emoji = parse_status(item.get("status", "patched"))
        os_type = item.get("os", item.get("platform", "Windows")).capitalize()
        
        # ดึงค่าคุณสมบัติต่างๆ
        sunc = item.get("sunc", "N/A")
        unc = item.get("unc", "N/A")
        decomp = "✅" if item.get("decompiler", False) or item.get("decompiler") == "✅" else "❌"
        multi = "✅" if item.get("multi_instance", False) or item.get("multi_instance") == "✅" else "❌"
        raknet = "✅" if item.get("raknet", False) or item.get("raknet") == "❌" else "❌" # เช็คกรณีรับค่ามาตรงๆ
        
        note = item.get("note", item.get("message", ""))
        
        # จัดการ Markdown Links
        links = []
        if item.get("website"): links.append(f"[Website]({item['website']})")
        if item.get("discord"): links.append(f"[Discord]({item['discord']})")
        if item.get("purchase"): links.append(f"[Purchase]({item['purchase']})")
        links_formatted = " | ".join(links) if links else "No Links"

        # ประกอบโครงสร้างข้อความรูปแบบ Tree GUI ลงใน Webhook ลิสต์ยาวลงมา
        entry = f"{status_emoji.split()[0]} **{name}** `[{version}]` - {price}\n"
        if note:
            entry += f"┗ 💬 *{note}*\n"
        entry += f"┣ 📊 sUNC: `{sunc}%` | UNC: `{unc}%`\n"
        entry += f"┣ 🛠️ Decomp: {decomp} | Multi: {multi} | Raknet: {raknet}\n"
        entry += f"┗ 🔗 {links_formatted}\n"

        if os_type not in categories:
            categories[os_type] = []
        categories[os_type].append(entry)

    # นำหมวดหมู่ที่จัดกลุ่มเสร็จแล้วยัดลง Embed fields (พร้อมระบบ Chunk ป้องกันข้อความยาวเกินลิมิต Discord)
    for os_name, items in categories.items():
        chunk_text = ""
        part = 1
        for text in items:
            if len(chunk_text) + len(text) > 950:
                embed["fields"].append({
                    "name": f"💻 {os_name} Script Executor Exploits (Part {part})",
                    "value": chunk_text,
                    "inline": False
                })
                chunk_text = text + "\n"
                part += 1
            else:
                chunk_text += text + "\n"
        
        if chunk_text:
            field_title = f"💻 {os_name} Script Executor Exploits" if part == 1 else f"💻 {os_name} Script Executor Exploits (Part {part})"
            embed["fields"].append({"name": field_title, "value": chunk_text, "inline": False})

    return {"embeds": [embed]}

def monitor_loop():
    message_id = None
    webhook_url_with_wait = WEBHOOK_URL + ("" if "?wait=true" in WEBHOOK_URL else "?wait=true")
    time.sleep(3)
    print("=== ระบบดึงข้อมูลจาก Pure API (weao.xyz) เริ่มทำงาน ===")

    while True:
        web_status, api_data = fetch_weao_api()
        payload = build_embed(web_status, api_data)
        
        try:
            if message_id is None:
                response = requests.post(webhook_url_with_wait, json=payload)
                if response.status_code in [200, 201]:
                    message_id = response.json().get("id")
                    print(f"[{time.strftime('%X')}] สร้างข้อความหลักบนดิสคอร์ดสำเร็จ (ID: {message_id})")
            else:
                clean_url = WEBHOOK_URL.split('?')[0]
                edit_url = f"{clean_url}/messages/{message_id}"
                response = requests.patch(edit_url, json=payload)
                
                if response.status_code == 200:
                    print(f"[{time.strftime('%X')}] อัปเดตข้อมูลโครงสร้าง API เรียบร้อย")
                elif response.status_code == 404:
                    message_id = None  # หากข้อความถูกลบ ให้ทำการส่งใหม่
        except Exception as e:
            print(f"Discord Webhook Error: {e}")
            
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    server_thread = Thread(target=keep_alive)
    server_thread.start()
    monitor_loop()
