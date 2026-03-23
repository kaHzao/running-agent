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

def get_weekly_stats(token, weeks_ago=0):
    headers = {"Authorization": f"Bearer {token}"}
    start = datetime.now() - timedelta(days=7 * (weeks_ago + 1))
    end = datetime.now() - timedelta(days=7 * weeks_ago)
    response = requests.get(
        f"https://www.strava.com/api/v3/athlete/activities?after={int(start.timestamp())}&before={int(end.timestamp())}&per_page=30",
        headers=headers
    )
    return response.json()

def format_pace(speed_ms):
    if not speed_ms or speed_ms == 0:
        return "N/A"
    pace_min = 1000 / speed_ms / 60
    return f"{int(pace_min)}:{int((pace_min % 1) * 60):02d} /km"

def summarize_week(activities):
    runs = [a for a in activities if a.get("type") == "Run"]
    total_km = sum(a.get("distance", 0) for a in runs) / 1000
    total_sesi = len(runs)
    total_menit = sum(a.get("moving_time", 0) for a in runs) // 60
    hr_list = [a.get("average_heartrate", 0) for a in runs if a.get("average_heartrate")]
    avg_hr = sum(hr_list) / len(hr_list) if hr_list else 0
    return total_km, total_sesi, total_menit, avg_hr

def format_activity_data(activity, detail, this_week, last_week):
    lap_summary = ""
    for i, lap in enumerate(detail.get("splits_metric", [])[:15], 1):
        lp = lap.get("average_speed", 0)
        lp_pace = format_pace(lp)
        hr = lap.get("average_heartrate", "N/A")
        lap_summary += f"  Km {i}: {lp_pace}, HR {hr} bpm\n"

    raw_cadence = detail.get("average_cadence", None)
    cadence_display = f"{int(raw_cadence * 2)} spm" if raw_cadence else "N/A"

    tw_km, tw_sesi, tw_menit, tw_hr = summarize_week(this_week)
    lw_km, lw_sesi, lw_menit, lw_hr = summarize_week(last_week)

    km_diff = tw_km - lw_km
    km_diff_str = f"+{km_diff:.1f}" if km_diff >= 0 else f"{km_diff:.1f}"
    sesi_diff = tw_sesi - lw_sesi
    sesi_diff_str = f"+{sesi_diff}" if sesi_diff >= 0 else f"{sesi_diff}"

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
Cadence     : {cadence_display}
Elevasi     : {activity.get('total_elevation_gain', 0):.0f} m
Kalori      : {activity.get('kilojoules', 0) * 0.239:.0f} kcal
Suffer Score: {activity.get('suffer_score', 'N/A')}

=== DATA PER KM ===
{lap_summary}
=== MINGGU INI ===
Total Jarak : {tw_km:.1f} km
Total Sesi  : {tw_sesi} lari
Total Waktu : {tw_menit} menit
HR Rata2    : {tw_hr:.1f} bpm

=== MINGGU LALU ===
Total Jarak : {lw_km:.1f} km
Total Sesi  : {lw_sesi} lari
Total Waktu : {lw_menit} menit
HR Rata2    : {lw_hr:.1f} bpm

=== PERBANDINGAN ===
Jarak       : {km_diff_str} km dibanding minggu lalu
Sesi        : {sesi_diff_str} sesi dibanding minggu lalu

=== PROFIL ATLET ===
Target      : Sub-21 menit untuk 5km (lomba 2 Mei 2026)
HR Istirahat: ~43 bpm
Cadence     : 174-176 spm
Volume      : 60-80 km/minggu
"""

def format_rest_day_data(this_week, last_week, last_activity):
    tw_km, tw_sesi, tw_menit, tw_hr = summarize_week(this_week)
    lw_km, lw_sesi, lw_menit, lw_hr = summarize_week(last_week)
    last_date = last_activity.get("start_date_local", "")[:10] if last_activity else "N/A"
    last_name = last_activity.get("name", "-") if last_activity else "-"
    last_dist = last_activity.get("distance", 0) / 1000 if last_activity else 0

    return f"""
HARI INI TIDAK ADA LARI - {datetime.now().strftime('%d %B %Y')}

=== AKTIVITAS TERAKHIR ===
Tanggal     : {last_date}
Nama        : {last_name}
Jarak       : {last_dist:.2f} km

=== MINGGU INI ===
Total Jarak : {tw_km:.1f} km
Total Sesi  : {tw_sesi} lari
Total Waktu : {tw_menit} menit

=== MINGGU LALU ===
Total Jarak : {lw_km:.1f} km
Total Sesi  : {lw_sesi} lari
Total Waktu : {lw_menit} menit

=== PROFIL ATLET ===
Target      : Sub-21 menit untuk 5km (lomba 2 Mei 2026)
Sisa waktu  : {(datetime(2026, 5, 2) - datetime.now()).days} hari menuju lomba
Volume      : 60-80 km/minggu
"""

# ============================================================
# OPENROUTER AI
# ============================================================
def analyze_with_openrouter(data_text, is_rest_day=False):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/kaHzao/running-agent",
        "X-Title": "Running Agent Kahzao"
    }

    if is_rest_day:
        prompt = f"""Kamu adalah pelatih lari pribadi yang suportif dan memotivasi.
Hari ini atlet tidak lari. Berikan pesan harian dalam Bahasa Indonesia berdasarkan data berikut.

{data_text}

Format pesan (gunakan emoji, singkat dan memotivasi):

HARI ISTIRAHAT
[Apresiasi bahwa istirahat adalah bagian penting dari latihan]

STATUS MINGGUAN
[Ringkasan progress minggu ini vs minggu lalu dengan angka spesifik]

COUNTDOWN LOMBA
[Hitung mundur dan motivasi menuju lomba 2 Mei 2026 sub-21 menit]

SARAN HARI INI
[Rekomendasi konkret untuk hari istirahat: nutrisi, tidur, stretching, dll]

RENCANA LATIHAN BERIKUTNYA
[Saran sesi lari berikutnya yang spesifik: jarak, pace target, tipe latihan]"""
    else:
        prompt = f"""Kamu adalah pelatih lari pribadi yang ahli dan suportif.
Analisa data lari berikut dan berikan laporan dalam Bahasa Indonesia yang spesifik.

{data_text}

Format laporan (gunakan emoji):

RINGKASAN SESI
[Ringkasan singkat performa hari ini berdasarkan data]

ANALISA PERFORMA
[Analisa pace, HR, cadence per km dengan angka spesifik]

TREN MINGGUAN
[Bandingkan minggu ini vs minggu lalu secara spesifik dengan angka]

KESIAPAN LOMBA Sub-21 Menit 2 Mei 2026
[Estimasi gap dan kesiapan hitung berdasarkan pace saat ini]

PERHATIAN
[Tanda overtraining atau hal yang perlu diwaspadai]

REKOMENDASI SESI BERIKUTNYA
[Saran latihan konkret dan spesifik]"""

    payload = {
        "model": "google/gemma-3-4b-it:free",
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
        this_week = get_weekly_stats(token, weeks_ago=0)
        last_week = get_weekly_stats(token, weeks_ago=1)

        activity_date = activity.get("start_date_local", "")[:10] if activity else ""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        if activity and activity_date in [today, yesterday]:
            # Ada lari baru — kirim analisa lengkap
            detail = get_activity_detail(token, activity["id"])
            data_text = format_activity_data(activity, detail, this_week, last_week)
            print("Menganalisa lari dengan OpenRouter AI...")
            analysis = analyze_with_openrouter(data_text, is_rest_day=False)
            message = f"Laporan Lari - {datetime.now().strftime('%d %b %Y')}\n\n{analysis}"
        else:
            # Tidak ada lari — kirim motivasi + rencana
            data_text = format_rest_day_data(this_week, last_week, activity)
            print("Hari istirahat — kirim motivasi...")
            analysis = analyze_with_openrouter(data_text, is_rest_day=True)
            message = f"Pesan Harian - {datetime.now().strftime('%d %b %Y')}\n\n{analysis}"

        send_telegram(message)
        print("Pesan berhasil dikirim ke Telegram!")

    except Exception as e:
        error_msg = f"Error pada Running Agent:\n{str(e)}"
        send_telegram(error_msg)
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()
