import requests
from datetime import datetime, timedelta
import time
import os

# ============================================================
# KONFIGURASI — ambil dari GitHub Secrets
# ============================================================
STRAVA_CLIENT_ID      = os.environ.get("STRAVA_CLIENT_ID", "214802")
STRAVA_CLIENT_SECRET  = os.environ.get("STRAVA_CLIENT_SECRET", "")
STRAVA_REFRESH_TOKEN  = os.environ.get("STRAVA_REFRESH_TOKEN", "")
OPENROUTER_API_KEY    = os.environ.get("OPENROUTER_API_KEY", "")
TELEGRAM_BOT_TOKEN    = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID      = os.environ.get("TELEGRAM_CHAT_ID", "")

# ============================================================
# STRAVA
# ============================================================
def get_strava_token():
    response = requests.post("https://www.strava.com/oauth/token", data={
        "client_id": STRAVA_CLIENT_ID,
        "client_secret": STRAVA_CLIENT_SECRET,
        "refresh_token": STRAVA_REFRESH_TOKEN,
        "grant_type": "refresh_token"
    })
    return response.json()["access_token"]

def get_latest_activity(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        "https://www.strava.com/api/v3/athlete/activities?per_page=1",
        headers=headers
    )
    activities = response.json()
    return activities[0] if activities else None

def get_activity_detail(token, activity_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"https://www.strava.com/api/v3/activities/{activity_id}",
        headers=headers
    )
    return response.json()

def get_weekly_stats(token):
    headers = {"Authorization": f"Bearer {token}"}
    week_ago = int((datetime.now() - timedelta(days=7)).timestamp())
    response = requests.get(
        f"https://www.strava.com/api/v3/athlete/activities?after={week_ago}&per_page=30",
        headers=headers
    )
    return response.json()

def format_pace(speed_ms):
    if not speed_ms or speed_ms == 0:
        return "N/A"
    pace_min = 1000 / speed_ms / 60
    return f"{int(pace_min)}:{int((pace_min % 1) * 60):02d} /km"

def format_activity_data(activity, detail, weekly):
    lap_summary = ""
    for i, lap in enumerate(detail.get("splits_metric", [])[:15], 1):
        lp = lap.get("average_speed", 0)
        lp_pace = format_pace(lp)
        hr = lap.get("average_heartrate", "N/A")
        lap_summary += f"  Km {i}: {lp_pace}, HR {hr} bpm\n"

    total_weekly_km = sum(a.get("distance", 0) for a in weekly) / 1000
    total_weekly_runs = len([a for a in weekly if a.get("type") == "Run"])
    total_weekly_time = sum(a.get("moving_time", 0) for a in weekly) // 60

    return f"""
DATA LARI - {datetime.now().strftime('%d %B %Y')}

=== AKTIVITAS TERBARU ===
Nama        : {activity.get('name', '-')}
Jenis       : {activity.get('type', 'Run')}
Jarak       : {activity.get('distance', 0)/1000:.2f} km
Durasi      : {activity.get('moving_time', 0)//60} menit {activity.get('moving_time', 0)%60} detik
Pace Rata2  : {format_pace(activity.get('average_speed', 0))}
HR Rata2    : {activity.get('average_heartrate', 'N/A')} bpm
HR Max      : {activity.get('max_heartrate', 'N/A')} bpm
Kadenz      : {detail.get('average_cadence', 'N/A')} spm
Elevasi     : {activity.get('total_elevation_gain', 0):.0f} m
Kalori      : {activity.get('kilojoules', 0) * 0.239:.0f} kcal
Suffer Score: {activity.get('suffer_score', 'N/A')}

=== DATA PER KM ===
{lap_summary}
=== STATISTIK 7 HARI TERAKHIR ===
Total Jarak : {total_weekly_km:.1f} km
Total Sesi  : {total_weekly_runs} lari
Total Waktu : {total_weekly_time} menit

=== PROFIL ATLET ===
Target      : Sub-21 menit untuk 5km (lomba 2 Mei 2026)
HR Istirahat: ~43 bpm
Kadenz Biasa: 174-176 spm
Volume Biasa: 60-80 km/minggu
"""

# ============================================================
# OPENROUTER AI
# ============================================================
def analyze_with_openrouter(data_text):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/kaHzao/running-agent",
        "X-Title": "Running Agent Kahzao"
    }

    prompt = f"""Kamu adalah pelatih lari pribadi yang ahli dan suportif.
Analisa data lari berikut dan berikan laporan dalam Bahasa Indonesia yang spesifik.

{data_text}

Format laporan (gunakan emoji, jangan generik):

RINGKASAN SESI
[Ringkasan singkat performa hari ini berdasarkan data]

ANALISA PERFORMA
[Analisa pace, HR, kadenz per km sebutkan angka spesifik]

TREN MINGGUAN
[Bagaimana sesi ini dibanding minggu terakhir]

KESIAPAN LOMBA Sub-21 Menit 2 Mei 2026
[Estimasi gap dan kesiapan hitung berdasarkan pace saat ini]

PERHATIAN
[Tanda overtraining atau hal yang perlu diwaspadai]

REKOMENDASI SESI BERIKUTNYA
[Saran latihan konkret dan spesifik]"""

    payload = {
        "model": "meta-llama/llama-3.1-8b-instruct:free",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1024
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload
    )
    data = response.json()

    if "choices" not in data:
        error_info = data.get("error", {})
        raise Exception(f"OpenRouter error: {error_info.get('message', str(data))}")

    return data["choices"][0]["message"]["content"]

# ============================================================
# TELEGRAM
# ============================================================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    chunks = [message[i:i+4096] for i in range(0, len(message), 4096)]
    for chunk in chunks:
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk
        })
        time.sleep(0.5)

# ============================================================
# MAIN
# ============================================================
def main():
    print("Running Agent dimulai...")

    try:
        token = get_strava_token()
        activity = get_latest_activity(token)

        if not activity:
            send_telegram("Tidak ada aktivitas ditemukan di Strava.")
            return

        activity_date = activity.get("start_date_local", "")[:10]
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        if activity_date not in [today, yesterday]:
            send_telegram(f"Aktivitas terakhir di Strava: {activity_date}. Belum ada lari baru.")
            return

        detail = get_activity_detail(token, activity["id"])
        weekly = get_weekly_stats(token)
        data_text = format_activity_data(activity, detail, weekly)

        print("Menganalisa dengan OpenRouter AI...")
        analysis = analyze_with_openrouter(data_text)

        message = f"Laporan Lari - {datetime.now().strftime('%d %b %Y')}\n\n{analysis}"
        send_telegram(message)
        print("Laporan berhasil dikirim ke Telegram!")

    except Exception as e:
        error_msg = f"Error pada Running Agent:\n{str(e)}"
        send_telegram(error_msg)
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()
