# 🏃 Garmin AI Running Agent

Agent AI yang menganalisa data lari harian dari Garmin 165 via Strava, menggunakan Gemini AI, dan mengirim laporan ke Telegram.

## Cara Pakai Setelah Setup

1. Selesai lari, tunggu data sync ke Strava (~2 menit)
2. Buka GitHub repo ini di HP
3. Klik tab **Actions**
4. Klik **🏃 Running Agent**
5. Klik **Run workflow** → **Run workflow**
6. Tunggu ~30 detik → laporan muncul di Telegram!

## Setup Secrets

Pergi ke **Settings → Secrets and variables → Actions → New repository secret**

| Secret | Keterangan |
|--------|-----------|
| `STRAVA_CLIENT_ID` | Client ID dari strava.com/settings/api |
| `STRAVA_CLIENT_SECRET` | Client Secret dari Strava |
| `STRAVA_REFRESH_TOKEN` | Refresh Token dari Strava |
| `GEMINI_API_KEY` | API Key dari aistudio.google.com |
| `TELEGRAM_BOT_TOKEN` | Token dari @BotFather |
| `TELEGRAM_CHAT_ID` | ID dari @userinfobot |

## Struktur File

```
├── running_agent.py          # Kode utama agent
├── .github/
│   └── workflows/
│       └── running_agent.yml # GitHub Actions workflow
└── README.md
```

## Laporan yang Dihasilkan

- 🏃 Ringkasan sesi
- 📊 Analisa performa (pace, HR, kadenz per km)
- 📈 Tren mingguan
- 🎯 Kesiapan lomba sub-21 menit
- ⚠️ Peringatan overtraining
- 💡 Rekomendasi sesi berikutnya
