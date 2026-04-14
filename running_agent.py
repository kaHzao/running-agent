import requests
from datetime import datetime, timedelta
import time
import os
import random

STRAVA_CLIENT_ID      = os.environ.get("STRAVA_CLIENT_ID", "214802")
STRAVA_CLIENT_SECRET  = os.environ.get("STRAVA_CLIENT_SECRET", "")
STRAVA_REFRESH_TOKEN  = os.environ.get("STRAVA_REFRESH_TOKEN", "")
ANTHROPIC_API_KEY     = os.environ.get("ANTHROPIC_API_KEY", "")
TELEGRAM_BOT_TOKEN    = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID      = os.environ.get("TELEGRAM_CHAT_ID", "")

QUOTES = [
    "Lari bukan tentang menjadi lebih baik dari orang lain. Ini tentang menjadi lebih baik dari dirimu kemarin.",
    "Setiap langkah yang kamu ambil hari ini adalah investasi untuk finish line esok hari.",
    "Rasa sakit itu sementara. Bangga itu selamanya.",
    "Tubuhmu bisa melakukan hampir segalanya. Pikiranmu yang perlu diyakinkan.",
    "Pelari terbaik bukan yang tercepat, tapi yang tidak pernah berhenti.",
    "Jarak sub-3 jam tidak dibangun dalam satu hari, tapi setiap hari membangunnya.",
    "Ketika kakimu berat, biarkan hatimu yang meringankan langkahmu.",
    "Lari adalah percakapan antara pikiran dan tubuh. Pastikan pikiranmu selalu menang.",
    "Setiap kilometer yang kamu tempuh hari ini adalah kilometer yang tidak perlu kamu takuti di hari lomba.",
    "Tidak ada latihan yang sia-sia. Semuanya menghitung.",
    "Sub-3 jam bukan mimpi. Itu rencana yang sedang kamu jalankan setiap hari.",
    "Istirahat bukan kelemahan. Istirahat adalah bagian dari strategi juara.",
    "Pelari sejati tahu kapan harus mendorong dan kapan harus mundur.",
    "Marathon bukan tentang 42km terakhir. Tapi tentang semua km yang kamu latih sebelumnya.",
    "Bangun pagi, lari, tidur, ulangi. Itulah resep sub-3 jam.",
    "Kecepatan datang dari konsistensi, bukan dari terburu-buru.",
    "Satu kilometer hari ini lebih baik dari nol kilometer kemarin.",
    "Tubuh yang kuat dibangun dari kebiasaan kecil yang dilakukan setiap hari.",
    "Jangan hitung jarak yang tersisa. Hitung langkah yang sudah kamu ambil.",
    "Hujan, panas, lelah — pelari sejati tetap keluar.",
    "Pace-mu hari ini mungkin lambat, tapi kamu masih lebih cepat dari orang yang tidur di rumah.",
    "Setiap pelari sub-3 jam pernah berlari lambat. Kuncinya mereka tidak berhenti.",
    "Kaki akan berhenti, tapi tekad tidak boleh.",
    "Saat kamu ingin berhenti, ingat kenapa kamu mulai.",
    "Latihan yang berat membuat lomba terasa mudah.",
    "Jangan takut lambat, takutlah berhenti.",
    "Konsistensi mengalahkan intensitas dalam jangka panjang.",
    "Setiap pagi adalah kesempatan baru untuk menjadi lebih kuat.",
    "Marathon dimulai dari langkah pertama, bukan dari garis start.",
    "Tubuhmu adalah mesin terbaik yang pernah ada. Rawat dan latih dengan baik.",
    "Progress bukan selalu terlihat hari ini, tapi pasti terasa di finish line.",
    "Lari bukan hanya olahraga. Ini adalah meditasi bergerak.",
    "Semakin keras latihan, semakin mudah lomba.",
    "Percayai prosesnya. Sub-3 jam adalah hasil dari ribuan kilometer latihan.",
    "Tubuhmu selalu bisa lebih dari yang kamu pikir.",
    "Jadikan lari sebagai kebiasaan, bukan beban.",
    "Setiap tetes keringat adalah bukti kerja kerasmu.",
    "Finish line terasa manis karena start line terasa berat.",
    "Pelari tidak lahir. Pelari dibentuk oleh konsistensi.",
    "Hari ini mungkin berat, tapi kamu lebih kuat dari rasa beratmu.",
]

def get_random_quote():
    return random.choice(QUOTES)

def get_week_bounds(weeks_ago=0):
    today = datetime.now()
    monday_this_week = today - timedelta(days=today.weekday())
    monday_this_week = monday_this_week.replace(hour=0, minute=0, second=0, microsecond=0)
    monday_start = monday_this_week - timedelta(weeks=weeks_ago)
    sunday_end = monday_start + timedelta(days=7)
    return int(monday_start.timestamp()), int(sunday_end.timestamp())

def get_week_label(weeks_ago=0):
    today = datetime.now()
    monday = today - timedelta(days=today.weekday()) - timedelta(weeks=weeks_ago)
    sunday = monday + timedelta(days=6)
    return f"{monday.strftime('%d %b')} - {sunday.strftime('%d %b')}"

def get_day_of_week():
    days = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    return days[datetime.now().weekday()]

def get_days_into_week():
    return datetime.now().weekday() + 1

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
    after, before = get_week_bounds(weeks_ago)
    response = requests.get(
        f"https://www.strava.com/api/v3/athlete/activities?after={after}&before={before}&per_page=30",
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

    hari_ini = get_day_of_week()
    hari_ke = get_days_into_week()

    return f"""
DATA LARI - {datetime.now().strftime('%d %B %Y')} ({hari_ini})

KONTEKS PENTING:
Hari ini {hari_ini}, hari ke-{hari_ke} dari 7 dalam minggu ini.
Mileage minggu ini WAJAR lebih kecil dari minggu lalu karena minggu belum selesai.
Jangan interpretasikan perbedaan volume sebagai penurunan performa.

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
=== MINGGU INI ({get_week_label(0)}) — Hari ke-{hari_ke} dari 7 ===
Total Jarak : {tw_km:.1f} km
Total Sesi  : {tw_sesi} lari
Total Waktu : {tw_menit} menit
HR Rata2    : {tw_hr:.1f} bpm

=== MINGGU LALU ({get_week_label(1)}) — Lengkap 7 hari ===
Total Jarak : {lw_km:.1f} km
Total Sesi  : {lw_sesi} lari
Total Waktu : {lw_menit} menit
HR Rata2    : {lw_hr:.1f} bpm

=== PERBANDINGAN ===
Jarak       : {km_diff_str} km dibanding minggu lalu
Sesi        : {sesi_diff_str} sesi dibanding minggu lalu

=== PROFIL ATLET ===
Target      : Sub-3:00 Marathon 2028
HR Istirahat: 41-45 bpm
Volume      : 60-80 km/minggu
"""

def format_rest_day_data(this_week, last_week, last_activity):
    tw_km, tw_sesi, tw_menit, tw_hr = summarize_week(this_week)
    lw_km, lw_sesi, lw_menit, lw_hr = summarize_week(last_week)
    last_date = last_activity.get("start_date_local", "")[:10] if last_activity else "N/A"
    last_name = last_activity.get("name", "-") if last_activity else "-"
    last_dist = last_activity.get("distance", 0) / 1000 if last_activity else 0

    hari_ini = get_day_of_week()
    hari_ke = get_days_into_week()

    return f"""
HARI ISTIRAHAT - {datetime.now().strftime('%d %B %Y')} ({hari_ini})

KONTEKS PENTING:
Hari ini {hari_ini}, hari ke-{hari_ke} dari 7 dalam minggu ini.
Mileage minggu ini WAJAR lebih kecil karena minggu belum selesai.

=== AKTIVITAS TERAKHIR ===
Tanggal     : {last_date}
Nama        : {last_name}
Jarak       : {last_dist:.2f} km

=== MINGGU INI ({get_week_label(0)}) — Hari ke-{hari_ke} dari 7 ===
Total Jarak : {tw_km:.1f} km
Total Sesi  : {tw_sesi} lari
Total Waktu : {tw_menit} menit

=== MINGGU LALU ({get_week_label(1)}) — Lengkap 7 hari ===
Total Jarak : {lw_km:.1f} km
Total Sesi  : {lw_sesi} lari
Total Waktu : {lw_menit} menit

=== PROFIL ATLET ===
Target      : Sub-3:00 Marathon 2028
HR Istirahat: 41-45 bpm
Volume      : 60-80 km/minggu
"""

def analyze_with_claude(data_text, is_rest_day=False):
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    format_rules = """
ATURAN FORMAT WAJIB:
- Bahasa Indonesia
- Setiap bagian dipisah SATU baris kosong
- Judul: emoji + HURUF KAPITAL, contoh: 🏃 RINGKASAN SESI
- Isi langsung di bawah judul tanpa baris kosong
- DILARANG bullet point (*) dan markdown (**bold** atau *italic*)
- Setiap poin baru = baris baru
"""

    if is_rest_day:
        prompt = f"""{format_rules}

Kamu adalah pelatih lari pribadi yang suportif. Hari ini atlet istirahat.
Data: {data_text}

PENTING: Jangan bandingkan mileage minggu ini vs minggu lalu seolah keduanya lengkap.
Minggu ini baru hari ke berapa — sebutkan itu, dan bilang mileage segini wajar.

Format:

🛌 HARI ISTIRAHAT
[Apresiasi istirahat sebagai bagian strategi menuju Sub-3:00 Marathon 2028]

📊 STATUS MINGGUAN
[Progress minggu ini — sebutkan ini baru hari ke berapa, mileage wajar segini]

💆 SARAN HARI INI
[Rekomendasi nutrisi, tidur, stretching]

🏃 RENCANA LATIHAN BERIKUTNYA
[Saran sesi lari berikutnya: jarak, pace, tipe latihan]"""

    else:
        prompt = f"""{format_rules}

Kamu adalah pelatih lari pribadi yang ahli. Analisa data lari ini:
{data_text}

PENTING TREN MINGGUAN:
Minggu ini baru hari ke berapa — jangan bilang volume turun jika memang belum selesai seminggu.
Bandingkan secara proporsional dan adil.

PENTING PROGRESS SUB-3:00:
Fokus pada PERKEMBANGAN POSITIF — apakah pace membaik, HR lebih efisien, konsistensi membaik.
Beri gambaran realistis tapi memotivasi tentang perjalanan menuju Sub-3:00.

Format:

🏃 RINGKASAN SESI
[Ringkasan performa hari ini]

📊 ANALISA PERFORMA
[Pace, HR, cadence per km dengan angka spesifik]

📈 TREN MINGGUAN
[Konteks adil — sebutkan ini baru hari ke berapa dalam minggu]

🎯 PROGRESS MENUJU SUB-3:00 MARATHON 2028
[Fokus perkembangan positif dan area yang membaik]

⚠️ PERHATIAN
[Hanya jika ada hal yang benar-benar perlu diwaspadai]

💡 REKOMENDASI SESI BERIKUTNYA
[Saran konkret sesuai target Sub-3:00 Marathon]"""

    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}]
    }

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=payload
    )
    data = response.json()

    if "content" not in data:
        error_info = data.get("error", {})
        raise Exception(f"Claude error: {error_info.get('message', str(data))}")

    return data["content"][0]["text"]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    chunks = [message[i:i+4096] for i in range(0, len(message), 4096)]
    for chunk in chunks:
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": chunk
        })
        time.sleep(0.5)

def main():
    print("Running Agent dimulai...")

    try:
        token = get_strava_token()
        activity = get_latest_activity(token)
        this_week = get_weekly_stats(token, weeks_ago=0)
        last_week = get_weekly_stats(token, weeks_ago=1)

        activity_date = activity.get("start_date_local", "")[:10] if activity else ""
        today = datetime.now().strftime("%Y-%m-%d")
        quote = get_random_quote()

        if activity and activity_date == today:
            detail = get_activity_detail(token, activity["id"])
            data_text = format_activity_data(activity, detail, this_week, last_week)
            print("Menganalisa lari dengan Claude AI...")
            analysis = analyze_with_claude(data_text, is_rest_day=False)
            message = f"Laporan Lari - {datetime.now().strftime('%d %b %Y')}\n\n{analysis}\n\n💬 {quote}"
        else:
            data_text = format_rest_day_data(this_week, last_week, activity)
            print("Hari istirahat — kirim motivasi...")
            analysis = analyze_with_claude(data_text, is_rest_day=True)
            message = f"Pesan Harian - {datetime.now().strftime('%d %b %Y')}\n\n{analysis}\n\n💬 {quote}"

        send_telegram(message)
        print("Pesan berhasil dikirim ke Telegram!")

    except Exception as e:
        error_msg = f"Error pada Running Agent:\n{str(e)}"
        send_telegram(error_msg)
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()
