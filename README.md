# SocialGlass Downloader

Downloader bertema glassmorphism hitam-putih untuk video publik dari YouTube, TikTok, Instagram, Facebook, dan X/Twitter menggunakan Flask + yt-dlp.

## Jalankan
Perlu Python 3.10+. Untuk output audio MP3, pasang FFmpeg juga.

```bash
python -m venv .venv
```
Windows PowerShell:
```powershell
.venv\Scripts\activate
pip install -r requirements.txt
python server.py
```
macOS/Linux:
```bash
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```
Buka `http://127.0.0.1:5000`.

## Catatan
- Gunakan hanya video milik sendiri atau yang Anda punya izin untuk mengunduh; patuhi ketentuan platform dan hak cipta.
- Tidak melewati DRM, login, atau pembatasan konten privat. Keberhasilan tergantung dukungan extractor yang dapat berubah sewaktu-waktu.
- SPCK Editor hanya menjalankan frontend statis; fitur unduh memerlukan backend Python.
- Ini dibuat untuk uji coba lokal. Jangan membuka ke internet tanpa autentikasi, rate limiting, kuota penyimpanan, pembersihan file, dan konfigurasi keamanan.
- File hasil disimpan pada folder `downloads/`.
