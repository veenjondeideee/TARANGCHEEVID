import os
import json
import datetime
import requests
from bs4 import BeautifulSoup

def ask_gemini(prompt_text):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ ไม่พบ API Key ในระบบ (GEMINI_API_KEY)")
        return None
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt_text
            }]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print("เกิดข้อผิดพลาดในการเชื่อมต่อกับ Gemini AI:", e)
        return None

# ตั้งค่าลิงก์สแกนหลักเพื่อเอาไว้หาข้อมูลให้น้อคู่กัน
target_urls = [
    "https://admission.ubu.ac.th/",
    "https://admissions.kku.ac.th/",
    "https://www.dek-d.com/tcas/68722/"
]

# 🌟 1. อ่านสิ่งที่น้อพิมพ์ถามในแชทมาจากไฟล์ data.json
user_question = "อยากรู้กำหนดการและค่ายล่าสุดของ ม.อุบลฯ และ ม.ขอนแก่น ครับ" # คำถามเริ่มต้นหากไฟล์ว่าง
current_news = []

if os.path.exists('data.json'):
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            old_data = json.load(f)
            user_question = old_data.get("user_chat", user_question)
            current_news = old_data.get("news", [])
    except Exception as e:
        print("ไม่สามารถอ่านฐานข้อมูลเก่าได้:", e)

print(f"💬 ได้รับคำถามจากช่องแชทหน้าเว็บ: '{user_question}'")
print("🤖 บอตกำลังเริ่มสืบค้นหน้าเว็บต่างๆ เพื่อมาหาคำตอบให้น้อ...")

# 2. ไปกวาดข้อมูลจากเว็บเป้าหมายมาเตรียมไว้ให้ AI อ่าน
collected_context = ""
for url in target_urls:
    try:
        res = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        clean_text = " ".join(soup.get_text().split())
        collected_context += f"\n[ข้อมูลจากเว็บ {url}]:\n{clean_text[:4000]}\n"
    except:
        pass

# 3. ประกอบคำสั่ง (Prompt) สั่งให้ AI ทำ 2 หน้าที่: ตอบคำถามแชท + สรุป JSON ปฏิทิน
prompt = f"""
คุณคือผู้ช่วยส่วนตัววิเคราะห์ข้อมูล TCAS และแชทบอตอัจฉริยะ 
จงอ่านข้อมูลจากหน้าเว็บที่รวบรวมมาให้ และทำตามคำสั่งต่อไปนี้:

1. ตอบคำถามของผู้ใช้ที่พิมพ์มาในช่องแชท: "{user_question}" (ให้ตอบแบบเป็นกันเอง น่ารัก เรียกว่า 'น้อลลล' หรือ 'น้อ' และให้คำแนะนำที่ชัดเจนตามข้อมูลจริง)
2. ค้นหาและสกัดกำหนดการ วันรับสมัคร หรือวันจัดค่ายกิจกรรมล่าสุด เพื่อเอาไปปักหมุดบนปฏิทิน

จงตอบกลับในรูปแบบ JSON เท่านั้น ห้ามมีคำนำ คำส่งท้าย หรือสัญลักษณ์ Markdown อื่นๆ นอกเหนือจากรูปแบบ JSON นี้เป๊ะๆ:
{{
    "user_chat": "{user_question}",
    "bot_response": "ใส่คำตอบของบอตที่คุยกับผู้ใช้ตรงนี้ ยาวและละเอียดได้ตามต้องการ",
    "news": [
        {{"title": "ข้อความปักหมุดปฏิทิน เช่น ค่าย UBU i-Camp 2027", "date": "ระบุวันของเดือน เช่น 20 มิ.ย."}}
    ]
}}

นี่คือเนื้อหาหน้าเว็บทั้งหมดสำหรับใช้อ้างอิงหาคำตอบ:
{collected_context}
"""

print("🧠 กำลังส่งคำถามไปให้ Gemini AI ประมวลผลและพิมพ์แชทตอบ...")
ai_response = ask_gemini(prompt)

if ai_response:
    try:
        clean_json = ai_response.replace("```json", "").replace("```", "").strip()
        final_data = json.loads(clean_json)
        
        # ใส่เวลาอัปเดตระบบ
        final_data["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=4)
        print("🎉 บอตอัปเดตคำตอบในแชทและข้อมูลปฏิทินลงไฟล์ data.json สำเร็จแล้ว!")
    except Exception as e:
        print("❌ แปลงข้อมูลจาก AI เป็น JSON ไม่สำเร็จ:", e)
        print("คำตอบดิบจาก AI คือ:", ai_response)
