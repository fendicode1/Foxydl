import os, re, uuid, threading
from pathlib import Path
from urllib.parse import urlparse
from flask import Flask, jsonify, request, send_from_directory, render_template
import yt_dlp

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "downloads"
OUT.mkdir(exist_ok=True)
app = Flask(__name__, static_folder="static", template_folder="templates")
jobs, lock = {}, threading.Lock()
DOMAINS = {
 "youtube.com","www.youtube.com","m.youtube.com","youtu.be","music.youtube.com",
 "tiktok.com","www.tiktok.com","vm.tiktok.com","vt.tiktok.com",
 "instagram.com","www.instagram.com","facebook.com","www.facebook.com","m.facebook.com","fb.watch",
 "x.com","www.x.com","twitter.com","www.twitter.com","mobile.twitter.com"
}
def valid_url(raw):
 raw=(raw or "").strip()
 if not raw or len(raw)>2048: raise ValueError("Masukkan URL yang valid.")
 p=urlparse(raw)
 if p.scheme not in ("http","https") or not p.hostname: raise ValueError("URL harus diawali http:// atau https://.")
 if p.hostname.lower().rstrip(".") not in DOMAINS: raise ValueError("Gunakan link YouTube, TikTok, Instagram, Facebook, atau X.")
 if p.username or p.password: raise ValueError("URL dengan kredensial tidak diizinkan.")
 return raw
def opts():
 return {"quiet":True,"no_warnings":True,"noplaylist":True,"socket_timeout":15,"retries":1,"extractor_retries":1,"cachedir":False}
@app.get("/")
def home(): return render_template("index.html")
@app.get("/api/health")
def health(): return jsonify(ok=True, service="SocialGlass Downloader", version="1.0")
@app.post("/api/info")
def info():
 try:
  url=valid_url((request.get_json(silent=True) or {}).get("url"))
  cfg=opts(); cfg.update(skip_download=True)
  with yt_dlp.YoutubeDL(cfg) as ydl: d=ydl.extract_info(url, download=False)
  if not d: raise ValueError("Metadata video tidak tersedia.")
  return jsonify(title=str(d.get("title") or "Video")[:180], uploader=str(d.get("uploader") or d.get("channel") or "Unknown creator")[:100], duration=d.get("duration"), thumbnail=d.get("thumbnail"), platform=str(d.get("extractor_key") or "Media")[:60])
 except Exception as e: return jsonify(error=str(e)[:300] or "Tidak dapat membaca video."),400
def work(jid,url,fmt):
 template=str(OUT/(jid+".%(ext)s")); cfg=opts()
 cfg.update(format=("bestaudio/best" if fmt=="audio" else "best[ext=mp4]/best"),outtmpl=template,max_filesize=500*1024*1024)
 if fmt=="audio": cfg["postprocessors"]=[{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}]
 try:
  with yt_dlp.YoutubeDL(cfg) as ydl:
   d=ydl.extract_info(url,download=True); filename=ydl.prepare_filename(d)
  if fmt=="audio": filename=str(Path(filename).with_suffix(".mp3"))
  elif Path(filename).with_suffix(".mp4").exists(): filename=str(Path(filename).with_suffix(".mp4"))
  p=Path(filename)
  if not p.exists():
   matches=list(OUT.glob(jid+".*"))
   if matches: p=matches[0]
  if not p.exists(): raise RuntimeError("File hasil tidak ditemukan. Untuk audio, pastikan FFmpeg terpasang.")
  with lock: jobs[jid]={"status":"done","filename":p.name}
 except Exception as e:
  with lock: jobs[jid]={"status":"error","error":str(e)[:300]}
@app.post("/api/download")
def download():
 try:
  b=request.get_json(silent=True) or {}; url=valid_url(b.get("url")); fmt=b.get("format","video")
  if fmt not in ("video","audio"): raise ValueError("Format tidak dikenal.")
  jid=uuid.uuid4().hex
  with lock: jobs[jid]={"status":"processing"}
  threading.Thread(target=work,args=(jid,url,fmt),daemon=True).start()
  return jsonify(job_id=jid),202
 except Exception as e: return jsonify(error=str(e)),400
@app.get("/api/status/<jid>")
def status(jid):
 if not re.fullmatch(r"[a-f0-9]{32}",jid): return jsonify(error="ID tidak valid."),400
 with lock: d=jobs.get(jid)
 if not d: return jsonify(error="Job tidak ditemukan atau server baru dimulai."),404
 result=dict(d)
 if result.get("status")=="done": result["download_url"]="/files/"+jid
 return jsonify(result)
@app.get("/files/<jid>")
def file(jid):
 if not re.fullmatch(r"[a-f0-9]{32}",jid): return "Not found",404
 with lock: d=jobs.get(jid)
 if not d or d.get("status")!="done" or Path(d.get("filename","")).name!=d.get("filename"): return "File belum siap atau tidak ditemukan.",404
 return send_from_directory(OUT,d["filename"],as_attachment=True,download_name=d["filename"])
if __name__=="__main__":
 print("SocialGlass: http://127.0.0.1:5000 — gunakan hanya untuk konten yang Anda miliki/berizin.")
 app.run(host="127.0.0.1",port=int(os.environ.get("PORT","5000")),debug=False,threaded=True)
