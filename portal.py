"""
portal.py — Web Portal Pengaduan Pelanggan PDAM Tirta Jaya Mandiri
Jalankan: python portal.py  (default port 5000)

Pastikan file ini diletakkan di folder yang sama dengan db.py,
atau sesuaikan sys.path di bawah.
"""

import sys
import os
from pathlib import Path
from datetime import date, datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for

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

    # ── Ambil & validasi field wajib ────────────────────────────────────────
    nama = f.get("nama_pelanggan", "").strip()[:150]
    if not nama:
        return jsonify({"error": "Nama pelanggan wajib diisi"}), 400

    cabang = f.get("cabang", "").strip().upper()
    if cabang not in db.BRANCH_COORDS:
        return jsonify({"error": "Cabang tidak valid"}), 400

    # ── Field opsional ──────────────────────────────────────────────────────
    no_sambung = f.get("no_sambung", "").strip()[:50] or None
    alamat     = f.get("alamat_rincian", "").strip() or None

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
        "no_sambung":            no_sambung,
        "blok":                  None,
        "kebocoran_pipa_dinas":  kpd,
        "kebocoran_instalatur":  ki,
        "supply_air":            sa,
        "pembayaran_melonjak":   pm,
        "water_meter_rusak":     wmr,
        "lainnya":               lai,
        "alamat":                alamat,
        "rincian":               None,
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
        return jsonify({"error": "Gagal menyimpan pengaduan. Coba lagi."}), 500

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
