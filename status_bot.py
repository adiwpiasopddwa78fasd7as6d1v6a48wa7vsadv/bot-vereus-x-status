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
API_EXPLOITS = "https://weao.xyz/api/status/exploits"
API_VERSIONS = "https://weao.xyz/api/versions/current"
CHECK_INTERVAL = 25  
FOOTER_TEXT = "Vereus X Status System"
# =======================================================

app = Flask('')

@app.route('/')
def home():
    return "<h1>Vereus X Status System v8 (Multi-API) is Active!</h1>", 200

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def fetch_weao_api():
    """ยิงรีเควสไปหา API 2 ตัวพร้อมกัน เพื่อดึงสถานะตัวรันและเวอร์ชันเกม"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json'
        }
        # ยิงดึงข้อมูล
        res_exploits = requests.get(API_EXPLOITS, headers=headers, timeout=12)
        res_versions = requests.get(API_VERSIONS, headers=headers, timeout=12)
        
        if res_exploits.status_code == 200 and res_versions.status_code == 200:
            return "ONLINE", res_exploits.json(), res_versions.json()
        return "OFFLINE", None, None
    except Exception as e:
        print(f"[{time.strftime('%X')}] เชื่อมต่อ API ล้มเหลว: {e}")
        return "OFFLINE", None, None

def parse_status(status_raw):
    """กรองข้อความจาก API เป็นไอคอนดิสคอร์ด"""
    status_str = str(status_raw).lower().strip()
    if status_str in ["updated", "working", "active", "online", "true"]:
        return "🟢 Working"
    elif status_str in ["issues", "waiting fix", "maintenance", "bugged", "testing"]:
        return "🟠 Issues"
    else:
        return "🔴 Patched"

def build_embed(web_status, exploits_data, versions_data):
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

    if web_status == "OFFLINE" or exploits_data is None:
        embed["fields"].append({"name": "⚠️ System Warning", "value": "ไม่สามารถดึงข้อมูลจาก API ได้ในขณะนี้", "inline": False})
        return {"embeds": [embed]}

    # 1. จัดการข้อมูลหน้า Roblox Version Update Tracker
    # (ระบบครอบคลุมกรณี API ส่งมาเป็น Object ซ้อนกัน หรือ String ตรงๆ)
    v_data = versions_data if isinstance(versions_data, dict) else (versions_data[0] if isinstance(versions_data, list) and versions_data else {})
    
    win_v = v_data.get("windows", "N/A") if isinstance(v_data.get("windows"), str) else v_data.get("windows", {}).get("version", "N/A")
    mac_v = v_data.get("mac", "N/A") if isinstance(v_data.get("mac"), str) else v_data.get("mac", {}).get("version", "N/A")
    and_v = v_data.get("android", "N/A") if isinstance(v_data.get("android"), str) else v_data.get("android", {}).get("version", "N/A")
    ios_v = v_data.get("ios", "N/A") if isinstance(v_data.get("ios"), str) else v_data.get("ios", {}).get("version", "N/A")

    roblox_tracker_text = (
        f"**Roblox Windows :** `{win_v}`\n"
        f"**Roblox Mac :** `{mac_v}`\n"
        f"**Roblox Android-iOS :** `{and_v}` / `{ios_v}`"
    )
    embed["fields"].append({"name": "🧩 Roblox Version Update Tracker", "value": roblox_tracker_text, "inline": False})

    # 2. จัดการข้อมูลหน้า Script Executor (จัดเป็นหมวดหมู่ตาม OS อัตโนมัติ)
    categories = {}
    
    # รองรับกรณีที่ API ส่งกลับมาเป็น List (Array) โดยตรง หรือส่งเป็น Dictionary
    exploits_list = exploits_data if isinstance(exploits_data, list) else exploits_data.get("exploits", exploits_data.get("data", []))

    for item in exploits_list:
        if not isinstance(item, dict): continue
        
        name = item.get("name", item.get("title", "Unknown"))
        version = item.get("version", "N/A")
        price = item.get("price", "Free")
        status_emoji = parse_status(item.get("status", "patched"))
        
        # ดึงหมวดหมู่ (ถ้า API ไม่มี OS ระบุให้ จะถือว่าเป็น Windows ไว้ก่อน)
        os_type = item.get("os", item.get("platform", "Windows")).capitalize()
        
        sunc = item.get("sunc", "N/A")
        unc = item.get("unc", "N/A")
        
        # เช็ค True/False จาก JSON
        decomp = "✅" if item.get("decompiler") in [True, "true", "✅", 1, "yes"] else "❌"
        multi = "✅" if item.get("multi_instance") in [True, "true", "✅", 1, "yes"] else "❌"
        raknet = "✅" if item.get("raknet") in [True, "true", "✅", 1, "yes"] else "❌"
        
        note = item.get("note", item.get("message", ""))
        
        # ดึงลิ้งก์จาก API 
        links = []
        if item.get("website"): links.append(f"[Website]({item['website']})")
        if item.get("discord"): links.append(f"[Discord]({item['discord']})")
        if item.get("purchase"): links.append(f"[Purchase]({item['purchase']})")
        links_formatted = " | ".join(links) if links else "No Links"

        # ต่อข้อความแบบ Tree Formatting 
        entry = f"{status_emoji.split()[0]} **{name}** `[{version}]` - {price}\n"
        if note:
            entry += f"┗ 💬 *{note}*\n"
        entry += f"┣ 📊 sUNC: `{sunc}%` | UNC: `{unc}%`\n"
        entry += f"┣ 🛠️ Decomp: {decomp} | Multi: {multi} | Raknet: {raknet}\n"
        entry += f"┗ 🔗 {links_formatted}\n"

        if os_type not in categories:
            categories[os_type] = []
        categories[os_type].append(entry)

    # ส่งหมวดหมู่ลง Embed ของ Webhook ป้องกัน Discord เตือนข้อความยาวเกิน
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
    print("=== ระบบดึงข้อมูลจาก Multi-API (weao.xyz) เริ่มทำงาน ===")

    while True:
        web_status, exploits_data, versions_data = fetch_weao_api()
        payload = build_embed(web_status, exploits_data, versions_data)
        
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
                    message_id = None  
        except Exception as e:
            print(f"Discord Webhook Error: {e}")
            
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    server_thread = Thread(target=keep_alive)
    server_thread.start()
    monitor_loop()
