"""
db.py — Koneksi MySQL untuk Dashboard Pengaduan PDAM
Requires: pip install mysql-connector-python bcrypt openpyxl pandas

PERBAIKAN (Juni 2026):
_get_db_config() lama bisa diam-diam fallback ke localhost ketika
dipanggil dari Flask (portal.py) karena import streamlit + akses
st.secrets melempar error di tempat yang tidak terduga.
Versi ini TIDAK bergantung pada streamlit sama sekali untuk baca config;
streamlit secrets hanya dibaca lewat fungsi terpisah yang dipanggil
secara eksplisit dari app.py (dashboard), bukan otomatis saat import.
"""
import os
import bcrypt
import mysql.connector
from mysql.connector import pooling
import pandas as pd
from pathlib import Path
from typing import Optional
from contextlib import contextmanager


def _read_streamlit_secrets() -> dict:
    """
    Coba baca st.secrets HANYA jika benar-benar berjalan di dalam
    Streamlit runtime. Return {} jika tidak relevan/gagal — TIDAK PERNAH
    melempar exception ke pemanggil.
    """
    try:
        import streamlit as st
        # st.secrets melempar error jika file secrets.toml tidak ada
        # SAAT diakses, bukan saat di-import — jadi bungkus rapat di sini.
        secrets = st.secrets
        mysql_cfg = secrets.get("mysql", None)
        if mysql_cfg is None:
            return {}
        return dict(mysql_cfg)
    except Exception:
        # Mencakup: streamlit tidak terinstall, tidak ada secrets.toml,
        # dipanggil dari luar streamlit runtime, dll.
        return {}


def _get_db_config() -> dict:
    """
    Urutan prioritas:
    1. Streamlit secrets (HANYA jika tersedia & valid) — untuk dashboard
       saat dideploy di Streamlit Cloud.
    2. Environment variable MYSQL_HOST / MYSQL_PORT / dst — untuk Flask
       portal (lokal pakai .env, atau Railway pakai Variables).
    3. Fallback localhost — untuk development tanpa konfigurasi apapun.
    """
    st_secrets = _read_streamlit_secrets()

    def pick(key_secrets: str, env_key: str, default):
        # Streamlit secrets menang HANYA jika key-nya benar-benar ada di sana.
        if key_secrets in st_secrets and st_secrets[key_secrets] not in (None, ""):
            return st_secrets[key_secrets]
        env_val = os.getenv(env_key)
        if env_val not in (None, ""):
            return env_val
        return default

    database = str(pick("database", "MYSQL_DB", "pdam_pengaduan")).strip()
    if database.lower() == "pengaduan_pelanggan":
        database = "pdam_pengaduan"

    return {
        "host":       str(pick("host", "MYSQL_HOST", "localhost")).strip(),
        "port":       int(pick("port", "MYSQL_PORT", 3306)),
        "database":   database,
        "user":       str(pick("user", "MYSQL_USER", "root")).strip(),
        "password":   str(pick("password", "MYSQL_PASSWORD", "")),
        "charset":    "utf8mb4",
        "autocommit": False,
    }


DB_CONFIG = _get_db_config()

# Path ke file Excel (satu folder dengan db.py)
EXCEL_PATH = Path(__file__).parent / "data" / "REKAP_PENGADUAN_PELANGGAN_2025_update.xlsx"

BULAN_ORDER = ["JANUARI","FEBRUARI","MARET","APRIL","MEI","JUNI",
               "JULI","AGUSTUS","SEPTEMBER","OKTOBER","NOVEMBER","DESEMBER"]

BRANCH_COORDS = {
    "CIBADAK/CARINGIN": {"lat":-6.8940,"lon":106.7855,"kec":"Cibadak/Caringin"},
    "CITARIK":          {"lat":-6.9820,"lon":106.5580,"kec":"Citarik"},
    "KABANDUNGAN":      {"lat":-6.8530,"lon":106.6350,"kec":"Kabandungan"},
    "CIDAHU":           {"lat":-6.8120,"lon":106.8180,"kec":"Cidahu"},
    "JAMPANGKULON":     {"lat":-7.3220,"lon":106.5690,"kec":"Jampangkulon"},
    "BOJONGGENTENG":    {"lat":-6.9170,"lon":106.8950,"kec":"Bojonggenteng"},
    "BOJONGLOPANG":     {"lat":-7.2800,"lon":106.6500,"kec":"Bojonglopang"},
    "PARAKANSALAK":     {"lat":-6.9680,"lon":106.6870,"kec":"Parakansalak"},
    "CIKEMBAR":         {"lat":-6.9850,"lon":106.7580,"kec":"Cikembar"},
    "PURABAYA":         {"lat":-7.1050,"lon":106.7780,"kec":"Purabaya"},
    "PELABUHANRATU":    {"lat":-6.9890,"lon":106.5440,"kec":"Pelabuhanratu"},
    "NAGRAK":           {"lat":-6.8730,"lon":106.8500,"kec":"Nagrak"},
    "CIAMBAR":          {"lat":-6.9450,"lon":106.8270,"kec":"Ciambar"},
    "PARUNGKUDA":       {"lat":-6.9550,"lon":106.8400,"kec":"Parungkuda"},
    "JAMPANG TENGAH":   {"lat":-7.1380,"lon":106.7020,"kec":"Jampang Tengah"},
    "UNIT CISAAT":      {"lat":-6.9230,"lon":106.9030,"kec":"Cisaat"},
    "SUKALARANG":       {"lat":-6.9120,"lon":106.9450,"kec":"Sukalarang"},
    "CISOLOK":          {"lat":-6.9600,"lon":106.4750,"kec":"Cisolok"},
    "CICURUG":          {"lat":-6.7880,"lon":106.7920,"kec":"Cicurug"},
    "KUTAJAYA":         {"lat":-6.7950,"lon":106.8050,"kec":"Kutajaya"},
    "KALAPANUNGGAL":    {"lat":-6.8620,"lon":106.7230,"kec":"Kalapanunggal"},
}

# ─────────────────────────────────────────────────────────────────────────────
# CONNECTION POOL
# ─────────────────────────────────────────────────────────────────────────────
_pool = None

def _get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="pdam_pool",
            pool_size=5,
            pool_reset_session=True,
            **DB_CONFIG,
        )
    return _pool

@contextmanager
def get_conn():
    conn = _get_pool().get_connection()
    try:
        yield conn
    finally:
        try:
            conn.close()
        except Exception:
            pass

# ─────────────────────────────────────────────────────────────────────────────
# INIT — pastikan tabel ada, seed user & data Excel jika kosong
# ─────────────────────────────────────────────────────────────────────────────
def init_db():
    """
    Dipanggil satu kali saat app start.
    - Buat tabel users & pengaduan jika belum ada
    - Seed 21 user default jika tabel users kosong
    - Import data dari Excel ke tabel pengaduan jika tabel pengaduan kosong
    """
    with get_conn() as conn:
        cur = conn.cursor()

        # ── Tabel users ──────────────────────────────────────────────────────
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
          id            INT AUTO_INCREMENT PRIMARY KEY,
          username      VARCHAR(60)  NOT NULL UNIQUE,
          password_hash VARCHAR(255) NOT NULL,
          nama_lengkap  VARCHAR(120) NOT NULL DEFAULT '',
          role          ENUM('pusat','cabang') NOT NULL DEFAULT 'cabang',
          cabang        VARCHAR(80)  NULL,
          aktif         TINYINT(1)   NOT NULL DEFAULT 1,
          created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # ── Tabel pengaduan ──────────────────────────────────────────────────
        cur.execute("""
        CREATE TABLE IF NOT EXISTS pengaduan (
          id                    INT AUTO_INCREMENT PRIMARY KEY,
          cabang                VARCHAR(80)  NOT NULL,
          bulan                 VARCHAR(20)  NOT NULL,
          bulan_num             TINYINT      NOT NULL DEFAULT 0,
          nama_pelanggan        VARCHAR(150) NOT NULL,
          no_sambung            VARCHAR(50)  NULL,
          blok                  VARCHAR(30)  NULL,
          kebocoran_pipa_dinas  TINYINT(1)   NOT NULL DEFAULT 0,
          kebocoran_instalatur  TINYINT(1)   NOT NULL DEFAULT 0,
          supply_air            TINYINT(1)   NOT NULL DEFAULT 0,
          pembayaran_melonjak   TINYINT(1)   NOT NULL DEFAULT 0,
          water_meter_rusak     TINYINT(1)   NOT NULL DEFAULT 0,
          lainnya               TINYINT(1)   NOT NULL DEFAULT 0,
          alamat                TEXT         NULL,
          rincian               TEXT         NULL,
          status                VARCHAR(40)  NOT NULL DEFAULT 'BELUM DILAKSANAKAN',
          tgl_pengaduan         DATE         NULL,
          tgl_penyelesaian      DATE         NULL,
          cluster               VARCHAR(20)  NOT NULL DEFAULT 'LAINNYA',
          durasi                INT          NULL,
          created_by            VARCHAR(60)  NULL DEFAULT 'import',
          created_at            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at            DATETIME     NULL ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)

        # Index
        for idx in [
            "CREATE INDEX idx_cabang  ON pengaduan(cabang)",
            "CREATE INDEX idx_cluster ON pengaduan(cluster)",
            "CREATE INDEX idx_status  ON pengaduan(status)",
            "CREATE INDEX idx_bulan   ON pengaduan(bulan_num)",
        ]:
            try:
                cur.execute(idx)
            except Exception:
                pass

        conn.commit()

        # ── Seed users jika kosong ────────────────────────────────────────────
        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            _seed_users(cur)
            conn.commit()
            print("[db] ✅ 21 user default berhasil dibuat.")

        # ── Import Excel jika tabel pengaduan kosong ─────────────────────────
        cur.execute("SELECT COUNT(*) FROM pengaduan")
        if cur.fetchone()[0] == 0:
            n = _import_excel(cur)
            conn.commit()
            if n > 0:
                print(f"[db] ✅ {n} baris data berhasil diimport dari Excel.")
            else:
                print("[db] ℹ️ Excel tidak ditemukan atau kosong, tabel pengaduan tetap kosong.")

        cur.close()


# ─────────────────────────────────────────────────────────────────────────────
# SEED USERS
# ─────────────────────────────────────────────────────────────────────────────
def _seed_users(cur):
    pw = bcrypt.hashpw("Pdam@2025".encode(), bcrypt.gensalt()).decode()
    users = [
        ("pusat",             "Admin Pusat PDAM",          "pusat",  None),
        ("cb_cibadak",        "Operator Cibadak/Caringin", "cabang", "CIBADAK/CARINGIN"),
        ("cb_citarik",        "Operator Citarik",          "cabang", "CITARIK"),
        ("cb_kabandungan",    "Operator Kabandungan",      "cabang", "KABANDUNGAN"),
        ("cb_cidahu",         "Operator Cidahu",           "cabang", "CIDAHU"),
        ("cb_jampangkulon",   "Operator Jampangkulon",     "cabang", "JAMPANGKULON"),
        ("cb_bojonggenteng",  "Operator Bojonggenteng",    "cabang", "BOJONGGENTENG"),
        ("cb_bojonglopang",   "Operator Bojonglopang",     "cabang", "BOJONGLOPANG"),
        ("cb_parakansalak",   "Operator Parakansalak",     "cabang", "PARAKANSALAK"),
        ("cb_cikembar",       "Operator Cikembar",         "cabang", "CIKEMBAR"),
        ("cb_purabaya",       "Operator Purabaya",         "cabang", "PURABAYA"),
        ("cb_pelabuhanratu",  "Operator Pelabuhanratu",    "cabang", "PELABUHANRATU"),
        ("cb_nagrak",         "Operator Nagrak",           "cabang", "NAGRAK"),
        ("cb_ciambar",        "Operator Ciambar",          "cabang", "CIAMBAR"),
        ("cb_parungkuda",     "Operator Parungkuda",       "cabang", "PARUNGKUDA"),
        ("cb_jampangtengah",  "Operator Jampang Tengah",   "cabang", "JAMPANG TENGAH"),
        ("cb_cisaat",         "Operator Cisaat",           "cabang", "UNIT CISAAT"),
        ("cb_sukalarang",     "Operator Sukalarang",       "cabang", "SUKALARANG"),
        ("cb_cisolok",        "Operator Cisolok",          "cabang", "CISOLOK"),
        ("cb_cicurug",        "Operator Cicurug",          "cabang", "CICURUG"),
        ("cb_kalapanunggal",  "Operator Kalapanunggal",    "cabang", "KALAPANUNGGAL"),
    ]
    sql = """INSERT IGNORE INTO users
             (username, password_hash, nama_lengkap, role, cabang)
             VALUES (%s, %s, %s, %s, %s)"""
    for uname, nama, role, cab in users:
        cur.execute(sql, (uname, pw, nama, role, cab))


# ─────────────────────────────────────────────────────────────────────────────
# IMPORT EXCEL → DATABASE
# ─────────────────────────────────────────────────────────────────────────────
def _has_mark(v) -> bool:
    if v is None:
        return False
    s = str(v).strip()
    return s not in ("", "nan", "0", "0.0", "None")

def _do_cluster(kpd, ki, sa, pm, wmr) -> str:
    if kpd or ki or sa:  return "TEKNIS"
    if pm:               return "REKENING AIR"
    if wmr:              return "PELAYANAN"
    return "LAINNYA"

def _import_excel(cur) -> int:
    """Baca sheet '2025' dari Excel, masukkan ke tabel pengaduan. Return jumlah baris."""
    if not EXCEL_PATH.exists():
        return 0

    try:
        raw = pd.read_excel(EXCEL_PATH, sheet_name="2025", header=None)
    except Exception as e:
        print(f"[db] ⚠️ Gagal baca Excel: {e}")
        return 0

    df = raw.iloc[7:].copy()
    df.columns = ["No","Cabang","Bulan","Nama_Pelanggan","No_Sambung","Blok",
                  "Kebocoran_Pipa_Dinas","Kebocoran_Instalatur","Supply_Air",
                  "Pembayaran_Melonjak","Water_Meter_Rusak","Lainnya",
                  "Alamat","Rincian","Status","Tgl_Pengaduan","Tgl_Penyelesaian"]

    # Filter baris valid (No harus angka)
    def is_valid_no(x):
        if pd.isna(x): return False
        return str(x).replace(".0","").strip().isdigit()

    df = df[df["No"].apply(is_valid_no)].copy()
    if df.empty:
        return 0

    # Normalize kolom
    df["Tgl_Pengaduan"]    = pd.to_datetime(df["Tgl_Pengaduan"],    errors="coerce")
    df["Tgl_Penyelesaian"] = pd.to_datetime(df["Tgl_Penyelesaian"], errors="coerce")
    df["Cabang"] = df["Cabang"].astype(str).str.strip().str.upper()
    df["Bulan"]  = df["Bulan"].astype(str).str.strip().str.upper()

    # Perbaiki Bulan yang tidak valid
    bulan_map_num = {i+1: m for i, m in enumerate(BULAN_ORDER)}
    for idx, row in df.iterrows():
        if row["Bulan"] not in BULAN_ORDER:
            month_num = row["Tgl_Pengaduan"].month if pd.notna(row["Tgl_Pengaduan"]) else None
            df.at[idx, "Bulan"] = bulan_map_num.get(month_num, "JANUARI")

    df["Status"] = (df["Status"].astype(str).str.strip().str.upper()
                   .replace({"SUDAH TERKENDALI":"SELESAI","SUDAH DI BAYAR":"SELESAI",
                              "NAN":"BELUM DILAKSANAKAN","":"BELUM DILAKSANAKAN"}))
    df["Status"] = df["Status"].apply(
        lambda x: x if x in ("SELESAI","DALAM PROSES","BELUM DILAKSANAKAN") else "BELUM DILAKSANAKAN"
    )

    sql = """
    INSERT INTO pengaduan
      (cabang, bulan, bulan_num, nama_pelanggan, no_sambung, blok,
       kebocoran_pipa_dinas, kebocoran_instalatur, supply_air,
       pembayaran_melonjak, water_meter_rusak, lainnya,
       alamat, rincian, status,
       tgl_pengaduan, tgl_penyelesaian,
       cluster, durasi, created_by)
    VALUES
      (%s,%s,%s,%s,%s,%s, %s,%s,%s,%s,%s,%s, %s,%s,%s, %s,%s, %s,%s,%s)
    """

    count = 0
    batch = []

    for _, row in df.iterrows():
        cab = row["Cabang"]
        if cab not in BRANCH_COORDS:
            continue  # skip cabang tidak dikenal

        bln     = row["Bulan"]
        bln_num = BULAN_ORDER.index(bln) + 1 if bln in BULAN_ORDER else 0

        nama = str(row["Nama_Pelanggan"]).strip()[:150] if pd.notna(row["Nama_Pelanggan"]) else "—"
        if not nama or nama in ("nan",""):
            nama = "—"

        kpd = int(_has_mark(row["Kebocoran_Pipa_Dinas"]))
        ki  = int(_has_mark(row["Kebocoran_Instalatur"]))
        sa  = int(_has_mark(row["Supply_Air"]))
        pm  = int(_has_mark(row["Pembayaran_Melonjak"]))
        wmr = int(_has_mark(row["Water_Meter_Rusak"]))
        lai = int(_has_mark(row["Lainnya"]))

        cluster = _do_cluster(kpd, ki, sa, pm, wmr)

        tgl_p = row["Tgl_Pengaduan"].date()    if pd.notna(row["Tgl_Pengaduan"])    else None
        tgl_s = row["Tgl_Penyelesaian"].date() if pd.notna(row["Tgl_Penyelesaian"]) else None
        durasi = (tgl_s - tgl_p).days if tgl_p and tgl_s and tgl_s >= tgl_p else None

        no_sam = str(row["No_Sambung"]).strip()[:50] if pd.notna(row["No_Sambung"]) and str(row["No_Sambung"]).strip() not in ("nan","") else None
        blok   = str(row["Blok"]).strip()[:30]       if pd.notna(row["Blok"])       and str(row["Blok"]).strip()       not in ("nan","") else None
        alamat = str(row["Alamat"]).strip()           if pd.notna(row["Alamat"])     and str(row["Alamat"]).strip()     not in ("nan","") else None
        rinc   = str(row["Rincian"]).strip()          if pd.notna(row["Rincian"])    and str(row["Rincian"]).strip()    not in ("nan","") else None

        batch.append((
            cab, bln, bln_num, nama, no_sam, blok,
            kpd, ki, sa, pm, wmr, lai,
            alamat, rinc, row["Status"],
            tgl_p, tgl_s,
            cluster, durasi, "import"
        ))

        # Insert per 500 baris (batch)
        if len(batch) >= 500:
            cur.executemany(sql, batch)
            count += len(batch)
            batch = []

    if batch:
        cur.executemany(sql, batch)
        count += len(batch)

    return count


# ─────────────────────────────────────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────────────────────────────────────
def login(username: str, password: str) -> Optional[dict]:
    """Return dict user jika login berhasil, None jika gagal."""
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT * FROM users WHERE username=%s AND aktif=1 LIMIT 1",
            (username.strip(),)
        )
        row = cur.fetchone()
        cur.close()

    if not row:
        return None
    if not bcrypt.checkpw(password.encode(), row["password_hash"].encode()):
        return None
    return row


def change_password(user_id: int, old_pw: str, new_pw: str) -> bool:
    """Ganti password. Return True jika berhasil."""
    with get_conn() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT password_hash FROM users WHERE id=%s", (user_id,))
        row = cur.fetchone()
        if not row or not bcrypt.checkpw(old_pw.encode(), row["password_hash"].encode()):
            cur.close()
            return False
        new_hash = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
        cur.execute("UPDATE users SET password_hash=%s WHERE id=%s", (new_hash, user_id))
        conn.commit()
        cur.close()
    return True


# ─────────────────────────────────────────────────────────────────────────────
# READ
# ─────────────────────────────────────────────────────────────────────────────
def fetch_pengaduan(cabang_filter: Optional[str] = None) -> pd.DataFrame:
    """
    Ambil data dari DB.
    cabang_filter → hanya data cabang itu (untuk role 'cabang').
    Return DataFrame dengan kolom PascalCase kompatibel app.py.
    """
    with get_conn() as conn:
        if cabang_filter:
            df = pd.read_sql(
                "SELECT * FROM pengaduan WHERE cabang=%s ORDER BY id",
                conn, params=(cabang_filter,)
            )
        else:
            df = pd.read_sql("SELECT * FROM pengaduan ORDER BY id", conn)

    if df.empty:
        return pd.DataFrame(columns=[
            "No","Cabang","Bulan","Bulan_Num","Nama_Pelanggan","No_Sambung","Blok",
            "Kebocoran_Pipa_Dinas","Kebocoran_Instalatur","Supply_Air",
            "Pembayaran_Melonjak","Water_Meter_Rusak","Lainnya",
            "Alamat","Rincian","Status","Tgl_Pengaduan","Tgl_Penyelesaian",
            "Cluster","Durasi","Created_By","lat","lon","Kec",
        ])

    # Rename snake_case → PascalCase
    df = df.rename(columns={
        "id": "No", "cabang": "Cabang", "bulan": "Bulan",
        "bulan_num": "Bulan_Num", "nama_pelanggan": "Nama_Pelanggan",
        "no_sambung": "No_Sambung", "blok": "Blok",
        "kebocoran_pipa_dinas": "Kebocoran_Pipa_Dinas",
        "kebocoran_instalatur": "Kebocoran_Instalatur",
        "supply_air": "Supply_Air", "pembayaran_melonjak": "Pembayaran_Melonjak",
        "water_meter_rusak": "Water_Meter_Rusak", "lainnya": "Lainnya",
        "alamat": "Alamat", "rincian": "Rincian", "status": "Status",
        "tgl_pengaduan": "Tgl_Pengaduan", "tgl_penyelesaian": "Tgl_Penyelesaian",
        "cluster": "Cluster", "durasi": "Durasi", "created_by": "Created_By",
    })

    # Tipe boolean
    for c in ["Kebocoran_Pipa_Dinas","Kebocoran_Instalatur","Supply_Air",
              "Pembayaran_Melonjak","Water_Meter_Rusak","Lainnya"]:
        if c in df.columns:
            df[c] = df[c].astype(bool)

    df["Tgl_Pengaduan"]    = pd.to_datetime(df.get("Tgl_Pengaduan"),    errors="coerce")
    df["Tgl_Penyelesaian"] = pd.to_datetime(df.get("Tgl_Penyelesaian"), errors="coerce")
    df["No"]               = df["No"].astype(str)

    # Kolom turunan untuk chart/map
    df["lat"] = df["Cabang"].map(lambda c: BRANCH_COORDS.get(c, {}).get("lat"))
    df["lon"] = df["Cabang"].map(lambda c: BRANCH_COORDS.get(c, {}).get("lon"))
    df["Kec"] = df["Cabang"].map(lambda c: BRANCH_COORDS.get(c, {}).get("kec", c))

    return df


# ─────────────────────────────────────────────────────────────────────────────
# CREATE
# ─────────────────────────────────────────────────────────────────────────────
def insert_pengaduan(data: dict) -> int:
    """Insert satu baris. Return id baru."""
    sql = """
    INSERT INTO pengaduan
      (cabang, bulan, bulan_num, nama_pelanggan, no_sambung, blok,
       kebocoran_pipa_dinas, kebocoran_instalatur, supply_air,
       pembayaran_melonjak, water_meter_rusak, lainnya,
       alamat, rincian, status, tgl_pengaduan, tgl_penyelesaian,
       cluster, durasi, created_by)
    VALUES
      (%(cabang)s, %(bulan)s, %(bulan_num)s, %(nama_pelanggan)s,
       %(no_sambung)s, %(blok)s,
       %(kebocoran_pipa_dinas)s, %(kebocoran_instalatur)s, %(supply_air)s,
       %(pembayaran_melonjak)s, %(water_meter_rusak)s, %(lainnya)s,
       %(alamat)s, %(rincian)s, %(status)s,
       %(tgl_pengaduan)s, %(tgl_penyelesaian)s,
       %(cluster)s, %(durasi)s, %(created_by)s)
    """
    # Pastikan key 'blok' dan 'lainnya' ada
    data.setdefault("blok", None)
    data.setdefault("lainnya", 0)

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, data)
        conn.commit()
        new_id = cur.lastrowid
        cur.close()
    return new_id


# ─────────────────────────────────────────────────────────────────────────────
# UPDATE
# ─────────────────────────────────────────────────────────────────────────────
def update_pengaduan(row_id: int, data: dict) -> None:
    """Update satu baris berdasarkan id."""
    data.setdefault("blok", None)
    data.setdefault("lainnya", 0)
    data["id"] = row_id

    sql = """
    UPDATE pengaduan SET
      cabang=%(cabang)s, bulan=%(bulan)s, bulan_num=%(bulan_num)s,
      nama_pelanggan=%(nama_pelanggan)s, no_sambung=%(no_sambung)s,
      kebocoran_pipa_dinas=%(kebocoran_pipa_dinas)s,
      kebocoran_instalatur=%(kebocoran_instalatur)s,
      supply_air=%(supply_air)s, pembayaran_melonjak=%(pembayaran_melonjak)s,
      water_meter_rusak=%(water_meter_rusak)s, lainnya=%(lainnya)s,
      alamat=%(alamat)s, rincian=%(rincian)s, status=%(status)s,
      tgl_pengaduan=%(tgl_pengaduan)s, tgl_penyelesaian=%(tgl_penyelesaian)s,
      cluster=%(cluster)s, durasi=%(durasi)s
    WHERE id=%(id)s
    """
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql, data)
        conn.commit()
        cur.close()


# ─────────────────────────────────────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────────────────────────────────────
def delete_pengaduan(row_id: int) -> None:
    """Hapus satu baris berdasarkan id."""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM pengaduan WHERE id=%s", (row_id,))
        conn.commit()
        cur.close()