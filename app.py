from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import math
import logging
import requests
from bs4 import BeautifulSoup
import uvicorn
import nest_asyncio
import re

# ✅ استدعاء الموديل الذكي المدرب
from model import generate_response

# إعداد السجلات
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# إضافة CORS لدعم الطلبات من الواجهة الأمامية
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# قاعدة بيانات المقاعد الثابتة
stadium_seats = {
    "A12": "الصف الأول، الجهة اليمنى، بوابة 5",
    "B5": "الصف الثاني، الجهة الوسطى، بوابة 3",
    "C9": "الصف الثالث، الجهة اليسرى، بوابة 7",
}

# ردود مبرمجة مسبقًا للأسئلة العامة
predefined_responses = {
    "مرحبا": "مرحبا! كيف يمكنني مساعدتك اليوم؟",
    "شكرا": "على الرحب والسعة!",
    "كيف حالك": "أنا بخير، شكرًا لسؤالك! وأنت؟",
    "من أنت": "أنا شات بوت لمساعدتك في الاستاد، يمكنني مساعدتك في العثور على مقعدك، أقرب مخرج، أو معلومات عن المباريات.",
    "وداعا": "وداعًا! أتمنى لك يومًا رائعًا.",
}

class ChatRequest(BaseModel):
    message: str
    location: dict = None

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371e3
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_seat_location(ticket_number):
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT seat, section FROM tickets WHERE ticket_number = ?", (ticket_number,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return f"مقعدك هو {result[0]} في القطاع {result[1]}. اتبع المسار: ادخل من البوابة 3، ثم اتجه يسارًا نحو الممر 5."
        return "لم يتم العثور على التذكرة في قاعدة البيانات. جرب البحث في قاعدة المقاعد الثابتة: " + stadium_seats.get(ticket_number.upper(), "المقعد غير موجود.")
    except Exception as e:
        logger.error(f"خطأ في get_seat_location: {str(e)}")
        return f"حدث خطأ أثناء البحث عن المقعد: {str(e)}"

def find_nearest_exit(user_lat, user_lon):
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name, latitude, longitude FROM exits")
        exits = cursor.fetchall()
        conn.close()
        if not exits:
            return "لا توجد بيانات عن المخارج."
        nearest_exit = None
        min_distance = float('inf')
        for exit in exits:
            exit_name, exit_lat, exit_lon = exit
            distance = haversine_distance(user_lat, user_lon, exit_lat, exit_lon)
            if distance < min_distance:
                min_distance = distance
                nearest_exit = exit_name
        return f"أقرب مخرج لك هو {nearest_exit} على بعد {min_distance:.2f} متر. اتجه نحو الممر الرئيسي للوصول إليه."
    except Exception as e:
        logger.error(f"خطأ في find_nearest_exit: {str(e)}")
        return f"حدث خطأ أثناء البحث عن المخرج: {str(e)}"

def get_match_info(team_name):
    try:
        url = "https://www.spl.com.sa/ar/fixtures?compSeason=858"
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        matches = []
        for row in soup.find_all("tr", class_="matches__row"):
            columns = row.find_all("td")
            if len(columns) > 3:
                match_teams = columns[1].text.strip()
                match_time = columns[2].text.strip()
                match_stadium = columns[3].text.strip()
                if team_name.lower() in match_teams.lower():
                    matches.append(f"{match_teams} - {match_time} في {match_stadium}")
        return matches if matches else ["لم يتم العثور على مباريات لهذا الفريق."]
    except Exception as e:
        logger.error(f"خطأ في get_match_info: {str(e)}")
        return [f"حدث خطأ أثناء جلب بيانات المباريات: {str(e)}"]

def init_db():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS tickets
                        (ticket_number TEXT PRIMARY KEY, seat TEXT, section TEXT)''')
        cursor.execute("INSERT OR IGNORE INTO tickets (ticket_number, seat, section) VALUES (?, ?, ?)", ("12345", "15", "B"))
        cursor.execute('''CREATE TABLE IF NOT EXISTS exits
                        (name TEXT PRIMARY KEY, latitude REAL, longitude REAL)''')
        cursor.execute("INSERT OR IGNORE INTO exits (name, latitude, longitude) VALUES (?, ?, ?)", ("المخرج 1", 24.8607, 46.7176))
        cursor.execute("INSERT OR IGNORE INTO exits (name, latitude, longitude) VALUES (?, ?, ?)", ("المخرج 2", 24.8610, 46.7180))
        cursor.execute("INSERT OR IGNORE INTO exits (name, latitude, longitude) VALUES (?, ?, ?)", ("المخرج 3", 24.8605, 46.7170))
        conn.commit()
        logger.info("تم تهيئة قاعدة البيانات بنجاح")
    except Exception as e:
        logger.error(f"خطأ أثناء تهيئة قاعدة البيانات: {str(e)}")
    finally:
        conn.close()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    logger.debug("تم الوصول إلى الصفحة الرئيسية")
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
async def chat(request: ChatRequest):
    logger.debug(f"تم استلام طلب إلى /chat: {request.message}")
    
    user_input = request.message.strip().lower()
    user_location = request.location
    response = ""

    # ✅ البحث عن تذكرة
    ticket_match = re.search(r'\b\d+\b', user_input)
    if "تذكرة" in user_input and ticket_match:
        ticket_number = ticket_match.group()
        response = get_seat_location(ticket_number)

    # ✅ البحث عن أقرب مخرج
    elif any(keyword in user_input for keyword in ["مخرج", "أقرب", "خروج"]):
        if user_location and 'latitude' in user_location and 'longitude' in user_location:
            user_lat = user_location['latitude']
            user_lon = user_location['longitude']
            response = find_nearest_exit(user_lat, user_lon)
        else:
            response = "يرجى السماح بالوصول إلى موقعك للعثور على أقرب مخرج."

    # ✅ البحث عن مباراة
    elif "مباراة" in user_input or "مباريات" in user_input:
        team_name = re.sub(r'(مباراة|مباريات)', '', user_input).strip()
        if team_name:
            matches = get_match_info(team_name)
            response = "\n".join(matches)
        else:
            response = "يرجى تحديد اسم الفريق للبحث عن المباريات."

    # ✅ رد من قاعدة جاهزة أو من الموديل الذكي
    else:
        response = predefined_responses.get(user_input)
        if not response:
            response = generate_response(user_input)

    logger.debug(f"الرد المرسل: {response}")
    return {"response": response}

if __name__ == "__main__":
    init_db()
    nest_asyncio.apply()
    uvicorn.run(app, host="0.0.0.0", port=5000)
