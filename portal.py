"""
portal.py — Web Portal Pengaduan Pelanggan PDAM Tirta Jaya Mandiri
Jalankan: .\venv\Scripts\python.exe portal.py  (default port 5000)
atau aktifkan venv terlebih dahulu: .\venv\Scripts\Activate.ps1
"""

import sys
import os
import uuid
from pathlib import Path
from datetime import date, datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename

# ── Load .env untuk development lokal (di Railway, .env tidak ada — tidak masalah) ──
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv belum terinstall, lanjut pakai env variable sistem

# ── Pastikan db.py bisa di-import ──────────────────────────────────────────
# Jika portal.py diletakkan SATU FOLDER DI ATAS dashboard_pengaduan/ (struktur user saat ini):
sys.path.insert(0, str(Path(__file__).parent / "dashboard_pengaduan"))

# Jika portal.py diletakkan di folder YANG SAMA dengan db.py, pakai ini sebagai gantinya:
# sys.path.insert(0, str(Path(__file__).parent))

import db  # noqa: E402  (db.py dari project Streamlit yang sudah ada)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "pdam_portal_secret_key_2025")

# Konfigurasi Upload Folder Gambar
UPLOAD_FOLDER = Path(__file__).parent / "static" / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Maksimal 16MB file upload

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'}

def allowed_file(filename):
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

BULAN_ORDER = [
    "JANUARI","FEBRUARI","MARET","APRIL","MEI","JUNI",
    "JULI","AGUSTUS","SEPTEMBER","OKTOBER","NOVEMBER","DESEMBER"
]

CABANG_LIST = sorted(db.BRANCH_COORDS.keys())


def _cluster(kpd, ki, sa, pm, wmr) -> str:
    if kpd or ki or sa:  return "TEKNIS"
    if pm:               return "REKENING AIR"
    if wmr:              return "PELAYANAN"
    return "LAINNYA"


# ── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Halaman utama: form pengaduan."""
    today = date.today()
    tanggal_str = today.strftime("%d %B %Y").lstrip("0")   # misal: 14 Juni 2025 (aman di Windows & Linux)
    return render_template(
        "form.html",
        cabang_list=CABANG_LIST,
        tanggal=tanggal_str,
        tanggal_iso=today.isoformat(),
    )


@app.route("/submit", methods=["POST"])
def submit():
    """Terima POST dari form, simpan ke MySQL, redirect ke halaman sukses."""
    f = request.form

    # Helper function untuk respon error (flash / json)
    def err_response(msg, code=400):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
            return jsonify({"error": msg}), code
        flash(msg, "error")
        return redirect(url_for("index"))

    # ── Ambil & validasi field wajib ────────────────────────────────────────
    nama = f.get("nama_pelanggan", "").strip()[:150]
    if not nama:
        return err_response("Nama pelanggan wajib diisi.", 400)

    no_telp = f.get("no_telp", "").strip()[:30]
    if not no_telp:
        return err_response("Nomor telepon wajib diisi.", 400)

    cabang = f.get("cabang", "").strip().upper()
    if cabang not in db.BRANCH_COORDS:
        return err_response("Cabang / Wilayah Layanan tidak valid.", 400)

    # ── Field opsional & alamat ──────────────────────────────────────────────
    no_sambung = f.get("no_sambung", "").strip()[:50] or None
    alamat     = f.get("alamat", "").strip() or f.get("alamat_rincian", "").strip() or None
    rincian    = f.get("rincian", "").strip() or None

    # ── Upload Gambar (Foto Bukti) ──────────────────────────────────────────
    foto_path = None
    if "foto" in request.files:
        foto_file = request.files["foto"]
        if foto_file and foto_file.filename != "":
            if allowed_file(foto_file.filename):
                filename = secure_filename(foto_file.filename)
                ext = Path(filename).suffix.lower()
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}{ext}"
                save_path = UPLOAD_FOLDER / unique_filename
                foto_file.save(save_path)
                foto_path = f"uploads/{unique_filename}"
            else:
                return err_response("Format gambar tidak didukung (gunakan JPG, PNG, WEBP, GIF).", 400)

    # ── Jenis pengaduan (checkbox) ──────────────────────────────────────────
    kpd = 1 if f.get("kebocoran_pipa") else 0
    ki  = 1 if f.get("kebocoran_instalatur") else 0
    sa  = 1 if f.get("air_mati") else 0
    pm  = 1 if f.get("tagihan") else 0
    wmr = 1 if f.get("water_meter") else 0
    lai = 1 if f.get("lainnya") else 0

    # ── Tanggal ─────────────────────────────────────────────────────────────
    tgl_today  = date.today()
    bulan_nama = BULAN_ORDER[tgl_today.month - 1]
    bulan_num  = tgl_today.month

    cluster = _cluster(kpd, ki, sa, pm, wmr)

    data = {
        "cabang":                cabang,
        "bulan":                 bulan_nama,
        "bulan_num":             bulan_num,
        "nama_pelanggan":        nama,
        "no_telp":               no_telp,
        "no_sambung":            no_sambung,
        "blok":                  None,
        "kebocoran_pipa_dinas":  kpd,
        "kebocoran_instalatur":  ki,
        "supply_air":            sa,
        "pembayaran_melonjak":   pm,
        "water_meter_rusak":     wmr,
        "lainnya":               lai,
        "alamat":                alamat,
        "foto":                  foto_path,
        "rincian":               rincian,
        "status":                "BELUM DILAKSANAKAN",
        "tgl_pengaduan":         tgl_today,
        "tgl_penyelesaian":      None,
        "cluster":               cluster,
        "durasi":                None,
        "created_by":            "pelanggan_web",
    }

    try:
        new_id = db.insert_pengaduan(data)
    except Exception as e:
        app.logger.error(f"DB error: {e}")
        return err_response("Gagal menyimpan pengaduan. Coba lagi.", 500)

    # Redirect ke halaman sukses dengan nomor tiket
    return redirect(url_for("sukses", tiket=new_id))


@app.route("/sukses")
def sukses():
    tiket = request.args.get("tiket", "—")
    tanggal_str = date.today().strftime("%d %B %Y").lstrip("0")
    return render_template("sukses.html", tiket=tiket, tanggal=tanggal_str)


# ── Health check (opsional, untuk monitoring) ────────────────────────────────
@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})


if __name__ == "__main__":
    # Inisialisasi DB (buat tabel & seed user jika belum ada)
    try:
        db.init_db()
        print("[portal] ✅ DB siap.")
    except Exception as e:
        print(f"[portal] ⚠️ DB init gagal: {e}")

    # Railway inject PORT secara otomatis. Lokal tetap default ke 5000.
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "1") == "1"  # set FLASK_DEBUG=0 di Railway
    app.run(debug=debug_mode, host="0.0.0.0", port=port)
