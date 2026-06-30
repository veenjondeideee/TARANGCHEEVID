import os
import json
import datetime
import requests
from bs4 import BeautifulSoup

# 1. ดึงข้อความจากหน้าเว็บประกาศ (สมมติว่าเป็นเว็บ Admission UBU หรือเว็บที่คุณบันทึกไว้)
# ในระบบจริงเราสามารถเขียนให้ดึงลิงก์จากที่คุณพิมพ์ทิ้งไว้ได้ แต่เริ่มต้นเราจะฟิกซ์ลิงก์หลักไว้ก่อนครับ
URL = "https://admission.ubu.ac.th/" 

def ask_gemini(prompt_text):
    # ดึง API Key จากระบบความปลอดภัยของ GitHub
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ไม่พบ API Key")
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
    
    response = requests.post(url, headers=headers, json=payload)
    try:
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print("เกิดข้อผิดพลาดในการอ่านคำตอบจาก AI:", e)
        return None

try:
    print("กำลังเข้าไปอ่านหน้าเว็บ...")
    res = requests.get(URL)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # ดึงเอาข้อความทั้งหมดในหน้าเว็บส่งให้ AI วิเคราะห์
    web_text = soup.get_text()
    
    # สั่งคำสั่ง (Prompt) ให้ AI แปลงข้อมูลเป็นฟอร์แมต JSON เพื่อให้ปฏิทินเราอ่านง่าย
    prompt = f"""
    คุณคือผู้ช่วยจัดตารางเรียน TCAS 70 จงนำข้อความจากเว็บประกาศต่อไปนี้ 
    ไปค้นหาว่ามี 'กำหนดการ' 'วันสมัคร' หรือ 'วันสอบ' อะไรที่สำคัญบ้าง 
    แล้วสรุปออกมาเป็นรูปแบบ JSON เท่านั้น ห้ามมีคำอธิบายอื่น โดยให้ใช้โครงสร้างแบบนี้เป๊ะๆ:
    {{
        "news": [
            {{"title": "ข้อความสรุปสั้นๆ ว่าต้องทำอะไร", "date": "ระบุแค่วันที่ เช่น 15 ต.ค."}},
            {{"title": "ส่งพอร์ตโฟลิโอ", "date": "1 พ.ย."}}
        ]
    }}
    
    นี่คือข้อความจากเว็บ:
    {web_text[:4000]} 
    """
    
    print("กำลังส่งข้อมูลให้ Gemini AI ช่วยจัดตาราง...")
    ai_response = ask_gemini(prompt)
    
    if ai_response:
        # ล้างแท็ก ```json ที่ AI ชอบแถมมาออก
        clean_json = ai_response.replace("```json", "").replace("```", "").strip()
        final_data = json.loads(clean_json)
        
        # ใส่เวลาอัปเดตปัจจุบันลงไป
        final_data["last_updated"] = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # เซฟลงไฟล์ data.json เพื่อให้หน้าเว็บ index.html ดึงไปใช้
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=4)
        print("บอต AI จัดตารางให้เรียบร้อยแล้ว! 💾")
        
except Exception as e:
    print(f"เกิดข้อผิดพลาดในระบบบอต: {e}")
