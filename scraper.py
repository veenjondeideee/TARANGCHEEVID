import os
import json
import datetime
import requests
from bs4 import BeautifulSoup

def ask_gemini(prompt_text):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ไม่พบ API Key")
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print("AI Error:", e)
        return None

# 🌟 เพิ่มแหล่งข้อมูลอื่นจากข้างนอก (เช่น เว็บ Dek-D ที่ชอบสรุปโพสต์เฟสบุ๊กและประกาศ) มารันเช็คคู่กัน
source_links = {
    "เว็บหลักมหาลัย": "https://admission.ubu.ac.th/",
    "ข่าวสารภายนอก": "https://www.dek-d.com/tcas/68722/"  # หน้าสรุปค่าย UBU i-Camp 2027 ล่าสุด
}

print("🕵️‍♂️ บอตเริ่มทำงานสืบค้นข้อมูลจากหลายแหล่งเพื่อความแม่นยำ...")
collected_context = ""

for name, url in source_links.items():
    try:
        print(f"กำลังดึงข้อมูลจาก [{name}]: {url}")
        res = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        clean_text = " ".join(soup.get_text().split())
        collected_context += f"\n=== แหล่งข้อมูลจาก {name} ===\n{clean_text[:5000]}\n"
    except Exception as e:
        print(f"ดึงข้อมูลจาก {name} ไม่สำเร็จ: {e}")

# สั่งให้ AI ตรวจสอบข้อมูลจากทุกแหล่งคัดกรองวันเวลาที่ตรงกันและอัปเดตที่สุด
prompt = f"""
คุณคือผู้ช่วยตรวจสอบข้อมูล TCAS อัจฉริยะ 
นี่คือข้อมูลเกี่ยวกับกำหนดการและค่าย 'UBU i-Camp 2027' หรือประกาศรับสมัครของ ม.อุบลฯ จากหลายแหล่งข้อมูล (รวมถึงสรุปข่าวจากโซเชียล)
จงเปรียบเทียบข้อมูลและสกัดเอา 'กำหนดการรับสมัคร' หรือ 'วันจัดกิจกรรม' ที่ถูกต้องและอัปเดตที่สุด ออกมาเป็นรูปแบบ JSON เท่านั้น

รูปแบบ JSON ที่ต้องการ:
{{
    "news": [
        {{"title": "สรุปชื่อค่าย/รอบรับสมัครให้ชัดเจน เช่น ค่ายคณะวิทย์ Dream to Science", "date": "ระบุวันที่ เช่น 20 มิ.ย."}},
        {{"title": "ค่ายวิศวะ Gear กันเกรา", "date": "10 ก.ค."}}
    ]
}}

นี่คือข้อมูลจากหลายแหล่งที่คุณต้องนำมา cross-check ร่วมกัน:
{collected_context}
"""

print("🧠 ส่งข้อมูลให้ Gemini AI เปรียบเทียบและดับเบิ้ลเช็คความถูกต้อง...")
ai_response = ask_gemini(prompt)

if ai_response:
    try:
        clean_json = ai_response.replace("```json", "").replace("```", "").strip()
        final_data = json.loads(clean_json)
        final_data["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=4)
        print("🎉 อัปเดตข้อมูลแบบผ่านการเปรียบเทียบลง data.json สำเร็จแล้ว!")
    except Exception as e:
        print("แปลง JSON ผิดพลาด:", e)
