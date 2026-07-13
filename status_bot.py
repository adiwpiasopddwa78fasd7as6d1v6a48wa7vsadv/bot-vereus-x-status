import time
import requests
from datetime import datetime, timezone
import os
from threading import Thread
from flask import Flask

# =======================================================
# CONFIGURATION (ตั้งค่าตรงนี้)
# =======================================================
WEBHOOK_URL = ""
API_EXPLOITS = "https://weao.xyz/api/status/exploits"
API_VERSIONS = "https://weao.xyz/api/versions/current"
CHECK_INTERVAL = 25  
FOOTER_TEXT = "Vereus X Status System"
# =======================================================

app = Flask('')

@app.route('/')
def home():
    return "<h1>Vereus X Status System v9 (Exact Match) is Active!</h1>", 200

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def fetch_weao_api():
    """ยิงรีเควสไปหา API 2 ตัวพร้อมกัน"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json'
        }
        res_exploits = requests.get(API_EXPLOITS, headers=headers, timeout=12)
        res_versions = requests.get(API_VERSIONS, headers=headers, timeout=12)
        
        if res_exploits.status_code == 200 and res_versions.status_code == 200:
            return "ONLINE", res_exploits.json(), res_versions.json()
        return "OFFLINE", None, None
    except Exception as e:
        print(f"[{time.strftime('%X')}] เชื่อมต่อ API ล้มเหลว: {e}")
        return "OFFLINE", None, None

def parse_status(status_raw):
    """แปลงสถานะให้ตรงกับรูปภาพ"""
    status_str = str(status_raw).lower().strip()
    if status_str in ["updated", "working", "active", "online", "true"]:
        return "🟢 Working"
    elif status_str in ["issues", "waiting fix", "maintenance", "bugged", "testing"]:
        return "🟠 Issues"
    else:
        return "🔴 Patched"

def format_date(date_str):
    """พยายามจัดรูปแบบวันที่และเวลาให้เหมือนในรูป (ตัดเลข 0 ข้างหน้าออก)"""
    if not date_str or date_str == "Unknown":
        return "Unknown"
    try:
        if 'T' in str(date_str) and 'Z' in str(date_str):
            dt = datetime.strptime(str(date_str).split('.')[0], "%Y-%m-%dT%H:%M:%S")
            # แปลงเป็น 7/9/2026, 4:00:14 PM UTC (ลบ 0 นำหน้าเดือน/วัน/ชั่วโมง)
            formatted = dt.strftime("%m/%d/%Y, %I:%M:%S %p UTC")
            formatted = formatted.replace("/0", "/").lstrip("0").replace(", 0", ", ")
            return formatted
    except:
        pass
    return str(date_str)

def build_embed(web_status, exploits_data, versions_data):
    embed_color = 65280 if web_status == "ONLINE" else 16711680
    current_time_str = time.strftime('%H:%M:%S')
    
    embed = {
        "description": f"🌐 **WEBSITE WEAO STATUS:** {'🟢 ONLINE' if web_status == 'ONLINE' else '🔴 OFFLINE'}\n\n"
                       f"🟢 Working = UPDATE | 🟠 Issues = WAITING FIX | 🔴 Patched = DOWN",
        "color": embed_color,
        "fields": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": f"{FOOTER_TEXT} | Last Updated: {current_time_str}"}
    }

    if web_status == "OFFLINE" or exploits_data is None:
        embed["fields"].append({"name": "⚠️ System Warning", "value": "ไม่สามารถดึงข้อมูลจาก API ได้ในขณะนี้", "inline": False})
        return {"embeds": [embed]}

    # 1. จัดการข้อมูลหน้า Roblox Version Update Tracker ให้ตรงกับภาพ
    v_data = versions_data if isinstance(versions_data, dict) else (versions_data[0] if isinstance(versions_data, list) and versions_data else {})
    
    def get_ver_info(os_name):
        data = v_data.get(os_name, {})
        if isinstance(data, str):
            return data, "Unknown"
        return data.get("version", "N/A"), format_date(data.get("last_updated", data.get("updatedAt", "Unknown")))

    win_v, win_date = get_ver_info("windows")
    mac_v, mac_date = get_ver_info("mac")
    and_v, and_date = get_ver_info("android")
    ios_v, ios_date = get_ver_info("ios")

    roblox_tracker_text = (
        f"**Roblox Windows :** `{win_v}`\n"
        f"└ Last Updated:จัดให้ครับพี่ซัน! รอบนี้ผม **ล้างข้อมูลส่วนเกินออกทั้งหมด** (พวก sUNC, UNC, ราคา, ลิ้งก์, ดีคอมไพล์) ให้เหลือแค่ชื่อและสเตตัสเพียวๆ และจัด Layout ให้ **เหมือนในรูปภาพ `image_1bfdc0.png` แบบ 100%** ทั้งหัวข้อ หมวดหมู่ และไอคอนครับ!

ก๊อปปี้โค้ดด้านล่างนี้ไปวางทับในไฟล์ `status_bot.py` ได้เลยครับ:

```python
import time
import requests
from datetime import datetime, timezone
import os
จัดให้ตามคำขอครับ! ผมเคลียร์พวกรายละเอียดปลีกย่อยอย่าง sUNC, Decompiler, ราคา และลิ้งก์ต่างๆ ออกไปให้หมดเกลี้ยงเลยครับ แล้วปรับโครงสร้างการเรียงข้อความให้ **ถอดแบบมาจากในรูปภาพ 100% เป๊ะๆ** ทั้งสัญลักษณ์เส้นโยง (`└`) และการจัดหมวดหมู่ OS

ก๊อปปี้โค้ดนี้ไปวางทับในไฟล์ `status_bot.py` ได้เลยครับ:

```python
import time
import requests
from datetime import datetime, timezone
import os
from threading import Thread
from flask import Flask

# =======================================================
# CONFIGURATION (ตั้งค่าตรงนี้)
# =======================================================
WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL_HERE"
API_EXPLOITS = "https://weao.xyz/api/status/exploits"
API_VERSIONS = "https://weao.xyz/api/versions/current"
CHECK_INTERVAL = 25  
FOOTER_TEXT = "Vereus X Status System"
# =======================================================

app = Flask('')

@app.route('/')
def home():
    return "<h1>Vereus X Status System v9 (Exact Image Match) is Active!</h1>", 200

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def fetch_weao_api():
    """ยิงรีเควสไปหา API 2 ตัวพร้อมกัน"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json'
        }
        res_exploits = requests.get(API_EXPLOITS, headers=headers, timeout=12)
        res_versions = requests.get(API_VERSIONS, headers=headers, timeout=12)
        
        if res_exploits.status_code == 200 and res_versions.status_code == 200:
            return "ONLINE", res_exploits.json(), res_versions.json()
        return "OFFLINE", None, None
    except Exception as e:
        print(f"[{time.strftime('%X')}] เชื่อมต่อ API ล้มเหลว: {e}")
        return "OFFLINE", None, None

def parse_status(status_raw):
    """กรองข้อความจาก API เป็นไอคอนดิสคอร์ดแบบในภาพ"""
    status_str = str(status_raw).lower().strip()
    if status_str in ["updated", "working", "active", "online", "true"]:
        return "🟢 Working"
    elif status_str in ["issues", "waiting fix", "maintenance", "bugged", "testing"]:
        return "🟠 Issues"
    else:
        return "🔴 Patched"

def format_date(date_string):
    """แปลงวันที่จาก API ให้อยู่ในรูปแบบ 7/9/2026, 4:00:14 PM UTC (แบบไม่เติมเลข 0 นำหน้า)"""
    if not date_string or date_string == "N/A":
        return "N/A"
    try:
        # รองรับ format แบบ ISO 8601
        dt = datetime.fromisoformat(date_string.replace("Z", "+00:00"))
        hour_12 = dt.hour % 12 or 12
        ampm = "AM" if dt.hour < 12 else "PM"
        return f"{dt.month}/{dt.day}/{dt.year}, {hour_12}:{dt.minute:02d}:{dt.second:02d} {ampm} UTC"
    except:
        return str(date_string)

def build_embed(web_status, exploits_data, versions_data):
    embed_color = 65280 if web_status == "ONLINE" else 16711680
    current_time_str = time.strftime('%X')
    
    embed = {
        "title": "🛡️ WEAO Status by siw",
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

    # ==========================================
    # 1. จัดการข้อมูล Roblox Version Update Tracker
    # ==========================================
    v_data = versions_data if isinstance(versions_data, dict) else (versions_data[0] if isinstance(versions_data, list) and versions_data else {})
    
    v_win = v_data.get("windows", {}) if isinstance(v_data.get("windows"), dict) else {"version": str(v_data.get("windows", "N/A"))}
    v_mac = v_data.get("mac", {}) if isinstance(v_data.get("mac"), dict) else {"version": str(v_data.get("mac", "N/A"))}
    v_and = v_data.get("android", {}) if isinstance(v_data.get("android"), dict) else {"version": str(v_data.get("android", "N/A"))}
    v_ios = v_data.get("ios", {}) if isinstance(v_data.get("ios"), dict) else {"version": str(v_data.get("ios", "N/A"))}

    # แปลงและจัดฟอร์แมตวันที่
    win_date = format_date(v_win.get("date") or v_win.get("last_updated") or "N/A")
    mac_date = format_date(v_mac.get("date") or v_mac.get("last_updated") or "N/A")
    and_date = format_date(v_and.get("date") or v_and.get("last_updated") or "N/A")
    ios_date = format_date(v_ios.get("date") or v_ios.get("last_updated") or "N/A")

    roblox_tracker_text = (
        f"**Roblox Windows :** `{v_win.get('version', 'N/A')}`\n"
        f"└ Last Updated: {win_date}\n\n"
        f"**Roblox Mac :** `{v_mac.get('version', 'N/A')}`\n"
        f"└ Last Updated: {mac_date}\n\n"
        f"**Roblox Android-iOS :** `{v_and.get('version', 'N/A')}` / `{v_ios.get('version', 'N/A')}`\n"
        f"└ Android: {and_date}\n"
        f"└ iOS: {ios_date}"
    )
    embed["fields"].append({"name": "🧩 Roblox Version Update Tracker", "value": roblox_tracker_text, "inline": False})

    # ==========================================
    # 2. จัดการข้อมูล Script Executor Exploits
    # ==========================================
    categories = {
        "Windows Script Executor Exploits": [],
        "Mac Script Executor Exploits": [],
        "Android Script Executor Exploits": [],
        "iOS Script Executor Exploits": [],
        "Windows External Exploits": []
    }
    
    exploits_list = exploits_data if isinstance(exploits_data, list) else exploits_data.get("exploits", exploits_data.get("data", []))

    for item in exploits_list:
        if not isinstance(item, dict): continue
        
        name = item.get("name", item.get("title", "Unknown"))
        status_emoji = parse_status(item.get("status", "patched"))
        
        # จัดหมวดหมู่ตามในรูปภาพ 100%
        os_raw = str(item.get("os", item.get("platform", "Windows"))).lower()
        if os_raw == "windows":
            cat_name = "Windows Script Executor Exploits"
        elif os_raw == "mac":
            cat_name = "Mac Script Executor Exploits"
        elif os_raw == "android":
            cat_name = "Android Script Executor Exploits"
        elif os_raw == "ios":
            cat_name = "iOS Script Executor Exploits"
        elif os_raw == "external":
            cat_name = "Windows External Exploits"
        else:
            cat_name = f"{os_raw.capitalize()} Script Executor Exploits"

        # โครงสร้างข้อความ: **Name** : 🟢 Status (ไม่มี sUNC หรือฟีเจอร์อื่นๆ แล้ว)
        entry = f"**{name}** : {status_emoji}"

        if cat_name not in categories:
            categories[cat_name] = []
        categories[cat_name].append(entry)

    # ส่งเข้า Embed เรียงตามหมวดหมู่
    order = [
        "Windows Script Executor Exploits",
        "Mac Script Executor Exploits",
        "Android Script Executor Exploits",
        "iOS Script Executor Exploits",
        "Windows External Exploits"
    ]
    
    # เพิ่มหมวดหมู่อื่นๆ ที่อาจหลงเข้ามาจาก API
    for k in categories.keys():
        if k not in order: order.append(k)

    for cat_name in order:
        items = categories.get(cat_name, [])
        if not items: continue # ข้ามหมวดที่ไม่มีตัวรัน

        chunk_text = ""
        part = 1
        for text in items:
            if len(chunk_text) + len(text) > 950:
                embed["fields"].append({
                    "name": f"💻 {cat_name} (Part {part})",
                    "value": chunk_text,
                    "inline": False
                })
                chunk_text = text + "\n"
                part += 1
            else:
                chunk_text += text + "\n"
        
        if chunk_text:
            field_title = f"💻 {cat_name}" if part == 1 else f"💻 {cat_name} (Part {part})"
            embed["fields"].append({"name": field_title, "value": chunk_text, "inline": False})

    return {"embeds": [embed]}

def monitor_loop():
    message_id = None
    webhook_url_with_wait = WEBHOOK_URL + ("" if "?wait=true" in WEBHOOK_URL else "?wait=true")
    time.sleep(3)
    print("=== ระบบดึงข้อมูลจาก Multi-API (weao.xyz) เริ่มทำงาน (Exact Match) ===")

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
                    print(f"[{time.strftime('%X')}] อัปเดตข้อมูลตรงตามภาพเรียบร้อย")
                elif response.status_code == 404:
                    message_id = None  
        except Exception as e:
            print(f"Discord Webhook Error: {e}")
            
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    server_thread = Thread(target=keep_alive)
    server_thread.start()
    monitor_loop()
