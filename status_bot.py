import time
import requests
from datetime import datetime, timezone
import os
from threading import Thread
from flask import Flask
from bs4 import BeautifulSoup
import re

# =======================================================
# CONFIGURATION (ตั้งค่าตรงนี้)
# =======================================================
WEBHOOK_URL = "https://discord.com/api/webhooks/1514211987234488401/dT70YrRMx2yVHSfw_Cb6Opf6VqdY8W5nOw5RQSU-qNLoGHO7ZPM5JQsH3Pfj9ei_LgYO"
TARGET_URL = "https://weao.xyz"  # ดึงจากหน้าเว็บหลักตรงๆ ไม่ง้อ API แล้ว
CHECK_INTERVAL = 30  
FOOTER_TEXT = "Vereus X Status System"
# =======================================================

app = Flask('')

@app.route('/')
def home():
    return "<h1>Vereus X Status System v6 (Smart Scraper) is Active!</h1>", 200

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# จำแนกหมวดหมู่คร่าวๆ สำหรับตัวที่รู้จัก ถ้าเจอตัวใหม่ที่ไม่รู้จัก จะถูกโยนเข้ากลุ่ม Windows 
KNOWN_PLATFORMS = {
    "MacSploit": "Mac", "Hydrogen": "Mac", "Opiumware": "Mac",
    "Delta": "Android", "Vega X": "Android", "Codex": "Android", "Arceus X": "Android",
    "Appleware": "iOS", "SwiftSploit": "iOS",
    "Serotonin": "External", "Severe": "External", "RbxCli": "External", "Lumen": "External", 
    "Matcha": "External", "Matrix Hub": "External", "Photon": "External", "DX9WARE V2": "External"
}

def fetch_weao_data():
    """กวาดข้อมูลจากหน้าเว็บแบบอัจฉริยะ ดักจับตัวรันใหม่ๆ และเจาะลึกสเตตัสอัตโนมัติ"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return "OFFLINE", []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        executors = []
        cards_found = []
        
        # 1. ค้นหาจุดที่มีคำว่า "Last updated:" (เพราะการ์ดทุกใบจะมีคำนี้)
        update_nodes = soup.find_all(string=re.compile(r'Last updated:', re.IGNORECASE))
        
        for node in update_nodes:
            card = node.parent
            # 2. ไต่ขึ้นไปหาตัวกล่อง Container หลักของการ์ดใบนั้น
            for _ in range(5):
                if card.parent and card.parent.find(string=re.compile(r'sUNC:')):
                    card = card.parent
                else:
                    break
                    
            if card not in cards_found:
                cards_found.append(card)
                
        # 3. เจาะสกัดข้อมูลจากการ์ดที่เจอทีละใบ
        for card in cards_found:
            # แยกแต่ละบรรทัดด้วยเครื่องหมาย | เพื่อให้ Regex จับข้อความได้ง่าย
            raw_text = card.get_text(separator=' | ')
            parts = [p.strip() for p in raw_text.split('|') if p.strip()]
            
            # ชื่อส่วนใหญ่จะอยู่ตำแหน่งแรกสุดของการ์ด
            name = parts[0] if parts else "Unknown"
            
            # ตรวจจับสถานะ (Working, Issues, Patched)
            if re.search(r'\| (Updated|Working|Active) \|', raw_text, re.IGNORECASE):
                status = "Working"
                icon = "🟢"
            elif re.search(r'\| (Issues|Maintenance) \|', raw_text, re.IGNORECASE):
                status = "Issues"
                icon = "🟠"
            else:
                status = "Patched"
                icon = "🔴"
                
            # ดึงข้อมูลตัวเลขและสถานะฟังก์ชันต่างๆ
            sunc = re.search(r'sUNC:\s*(\d+%?)', raw_text)
            sunc = sunc.group(1) if sunc else "N/A"
            
            unc = re.search(r'UNC:\s*(\d+%?)', raw_text)
            unc = unc.group(1) if unc else "N/A"
            
            decomp = re.search(r'Decompiler:\s*([✅❌])', raw_text)
            decomp = decomp.group(1) if decomp else "❌"
            
            multi = re.search(r'Multi-Instance:\s*([✅❌])', raw_text)
            multi = multi.group(1) if multi else "❌"
            
            raknet = re.search(r'Raknet Library:\s*([✅❌])', raw_text)
            raknet = raknet.group(1) if raknet else "❌"
            
            # ดึงข้อมูลราคาหรือระบบคีย์
            price = re.search(r'\| (Free|Key System|\$[\d\.]+.*?|Paid) \|', raw_text, re.IGNORECASE)
            price = price.group(1).strip() if price else "Free"
            
            # ดึงลิ้งก์ที่กดได้ (Website, Discord, Purchase)
            links_str = []
            for a in card.find_all('a', href=True):
                link_text = a.get_text(strip=True).lower()
                if 'website' in link_text:
                    links_str.append(f"[Website]({a['href']})")
                elif 'discord' in link_text:
                    links_str.append(f"[Discord]({a['href']})")
                elif 'purchase' in link_text:
                    links_str.append(f"[Purchase]({a['href']})")
                    
            platform = KNOWN_PLATFORMS.get(name, "Windows")
            
            executors.append({
                "name": name,
                "platform": platform,
                "status_text": status,
                "status_icon": icon,
                "sunc": sunc,
                "unc": unc,
                "decomp": decomp,
                "multi": multi,
                "raknet": raknet,
                "price": price,
                "links": " | ".join(links_str) if links_str else "No Links"
            })
            
        return "ONLINE", executors
        
    except Exception as e:
        print(f"Error scraping: {e}")
        return "OFFLINE", []

def build_embed(web_status, executors_data):
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

    if web_status == "OFFLINE" or not executors_data:
        embed["fields"].append({"name": "⚠️ System Warning", "value": "ไม่สามารถดึงข้อมูลจากเว็บไซต์ได้ในขณะนี้", "inline": False})
        return {"embeds": [embed]}

    categories = {}
    for data in executors_data:
        os_type = data["platform"]
        # จัดฟอร์แมตข้อความให้สวยงามและละเอียด
        entry = f"{data['status_icon']} **{data['name']}** - `{data['price']}`\n"
        entry += f"┣ 📊 sUNC: `{data['sunc']}` | UNC: `{data['unc']}`\n"
        entry += f"┣ 🛠️ Decomp: {data['decomp']} | Multi: {data['multi']} | Raknet: {data['raknet']}\n"
        entry += f"┗ 🔗 {data['links']}\n"

        if os_type not in categories:
            categories[os_type] = []
        categories[os_type].append(entry)

    # ป้องกันบัคข้อความเกิน 1024 ตัวอักษรของ Discord 
    for os_name, items in categories.items():
        chunk_text = ""
        part = 1
        for i, text in enumerate(items):
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
            title = f"💻 {os_name} Script Executor Exploits" if part == 1 else f"💻 {os_name} Script Executor Exploits (Part {part})"
            embed["fields"].append({"name": title, "value": chunk_text, "inline": False})

    return {"embeds": [embed]}

def monitor_loop():
    message_id = None
    webhook_url_with_wait = WEBHOOK_URL + ("" if "?wait=true" in WEBHOOK_URL else "?wait=true")
    time.sleep(3)
    print("=== ระบบกวาดหน้าเว็บอัจฉริยะเริ่มทำงาน ===")

    while True:
        web_status, executors_data = fetch_weao_data()
        payload = build_embed(web_status, executors_data)
        
        try:
            if message_id is None:
                response = requests.post(webhook_url_with_wait, json=payload)
                if response.status_code in [200, 201]:
                    message_id = response.json().get("id")
                    print(f"[{time.strftime('%X')}] สร้างข้อความหลักสำเร็จ (ID: {message_id})")
            else:
                clean_url = WEBHOOK_URL.split('?')[0]
                edit_url = f"{clean_url}/messages/{message_id}"
                response = requests.patch(edit_url, json=payload)
                
                if response.status_code == 200:
                    print(f"[{time.strftime('%X')}] อัปเดตสถานะและข้อมูลเชิงลึกเรียบร้อย")
                elif response.status_code == 404:
                    message_id = None
        except Exception as e:
            print(f"Discord Webhook Error: {e}")
            
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    server_thread = Thread(target=keep_alive)
    server_thread.start()
    monitor_loop()
