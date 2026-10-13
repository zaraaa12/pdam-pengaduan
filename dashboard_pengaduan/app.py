import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import warnings
import base64
from pathlib import Path
from datetime import date

warnings.filterwarnings("ignore")

BASE_DIR  = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "REKAP_PENGADUAN_PELANGGAN_2025_update.xlsx"
LOGO_PATH = BASE_DIR / "data" / "logoPDAM.png"

# Import database layer 
try:
    import db as _db
    _db.init_db()
    DB_OK    = True
    DB_ERROR = ""
except Exception as _e:
    DB_OK    = False
    DB_ERROR = str(_e)

def _logo_b64():
    with open(LOGO_PATH, "rb") as f:
        return base64.b64encode(f.read()).decode()

def logo_img(size="36px", radius="9px"):
    if LOGO_PATH.exists():
        return (f'<img src="data:image/png;base64,{_logo_b64()}" '
                f'style="width:{size};height:{size};object-fit:contain;border-radius:{radius};">')
    return '<span style="font-size:1.3rem;">💧</span>'

_page_icon = LOGO_PATH if LOGO_PATH.exists() else "💧"

st.set_page_config(
    page_title="Dashboard Pengaduan PERUMDA AM TJM",
    page_icon=_page_icon,
    layout="wide",
    initial_sidebar_state="expanded",
)

# titik koordinat
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
BULAN_ORDER = ["JANUARI","FEBRUARI","MARET","APRIL","MEI","JUNI",
               "JULI","AGUSTUS","SEPTEMBER","OKTOBER","NOVEMBER","DESEMBER"]
COLORS      = {"TEKNIS":"#f97316","REKENING AIR":"#22d3ee","PELAYANAN":"#4ade80","LAINNYA":"#818cf8"}
CABANG_LIST = sorted(BRANCH_COORDS.keys())
STATUS_LIST = ["SELESAI","DALAM PROSES","BELUM DILAKSANAKAN"]

# CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&display=swap');
*, body { font-family: 'DM Sans', sans-serif !important; }
h1,h2,h3,h4 { font-family: 'Sora', sans-serif !important; }

[data-testid="stAppViewContainer"],
[data-testid="stHeader"] { background: #0a0e1a !important; }
.main, .block-container { background: #0a0e1a !important; padding-top: 1.2rem !important; }
#MainMenu, footer { visibility: hidden; }

/* Hide default Streamlit collapse button */
button[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"],
button[title="Collapse sidebar"], button[title="Expand sidebar"],
button[aria-label="Collapse sidebar"], button[aria-label="Expand sidebar"],
div[data-testid="stSidebarNav"] { display: none !important; }

/* ── LOGIN PAGE ── */
.login-outer {
    min-height: 85vh;
    display: flex;
    align-items: center;
    justify-content: center;
}
.login-card {
    background: #12172e;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 40px 40px 32px;
    width: 100%;
    box-shadow: 0 24px 60px rgba(0,0,0,0.5);
}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {
    background: #0f1224 !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
    min-width: 230px !important; max-width: 230px !important;
    transition: min-width .32s cubic-bezier(.4,0,.2,1),
                max-width .32s cubic-bezier(.4,0,.2,1),
                transform  .32s cubic-bezier(.4,0,.2,1),
                opacity    .22s ease !important;
}
section[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }
section[data-testid="stSidebar"] * { color: #9aa3c8 !important; }
[data-testid="stAppViewContainer"] {
    transition: margin-left .32s cubic-bezier(.4,0,.2,1) !important;
}

/* Radio nav */
div[data-testid="stRadio"] > label { display: none !important; }
div[data-testid="stRadio"] > div   { gap: 0 !important; flex-direction: column !important; }
div[data-testid="stRadio"] > div > label {
    padding: 10px 20px 10px 24px !important; border-radius: 0 !important;
    cursor: pointer !important; border-left: 3px solid transparent !important;
    margin: 0 !important; color: #7b86b0 !important; font-size: 0.875rem !important;
    font-weight: 400 !important; transition: all .18s !important; background: transparent !important;
}
div[data-testid="stRadio"] > div > label:hover {
    background: rgba(139,92,246,.08) !important; color: #c8cfe8 !important;
    border-left: 3px solid rgba(139,92,246,.4) !important;
}
div[data-testid="stRadio"] > div > label:has(input:checked) {
    background: rgba(139,92,246,.16) !important; border-left: 3px solid #8b5cf6 !important;
    color: #e0e6ff !important; font-weight: 600 !important;
}
div[data-testid="stRadio"] > div > label > div:first-child { display: none !important; }

.sb-section { padding: 16px 20px 6px; font-size: 0.68rem; font-weight: 700;
              letter-spacing: 1.4px; text-transform: uppercase; color: #3d4468 !important; }
.sb-divider { height: 1px; background: rgba(255,255,255,0.06); margin: 6px 0; }

.user-chip { margin: 10px 14px 0; padding: 10px 14px;
             background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.22);
             border-radius: 10px; }
.user-chip .uname { color: white !important; font-weight: 600; font-size: .82rem; }
.user-chip .urole { color: #6366f1 !important; font-size: .7rem; margin-top: 2px; }

/* Metric Cards */
.mc { border-radius: 14px; padding: 16px 18px; color: white; margin-bottom: 6px;
      border: 1px solid rgba(255,255,255,0.07); position: relative; overflow: hidden; }
.mc::after { content:''; position:absolute; top:-24px; right:-24px; width:80px; height:80px;
             border-radius:50%; background:rgba(255,255,255,0.04); }
.mc-blue   { background: linear-gradient(135deg,#1e3a5f,#1a56db); }
.mc-orange { background: linear-gradient(135deg,#431407,#c2410c); }
.mc-cyan   { background: linear-gradient(135deg,#0c3349,#0891b2); }
.mc-green  { background: linear-gradient(135deg,#052e16,#16a34a); }
.mc-purple { background: linear-gradient(135deg,#2e1065,#7c3aed); }
.mc-lbl { font-size:.68rem; opacity:.7; font-weight:600; letter-spacing:.6px; text-transform:uppercase; }
.mc-val { font-size:2rem; font-weight:800; line-height:1.1; font-family:'Sora',sans-serif; }
.mc-sub { font-size:.72rem; opacity:.55; margin-top:2px; }
.mc-ico { font-size:1.3rem; opacity:.55; float:right; margin-top:-2px; }

.sec-hdr { font-size:.78rem; font-weight:700; color:#6366f1; padding:0 0 8px;
           border-bottom:1px solid rgba(99,102,241,.25); margin-bottom:14px;
           text-transform:uppercase; letter-spacing:.8px; }

/* Table */
.dtw { background:#12172e; border-radius:14px; overflow:hidden; border:1px solid rgba(255,255,255,0.06); }
.dth { background:#181e3a; padding:12px 16px; display:flex; justify-content:space-between;
       align-items:center; border-bottom:1px solid rgba(255,255,255,0.06); }
.dth-title { color:white; font-weight:700; font-size:.875rem; font-family:'Sora',sans-serif; }
.dtable { width:100%; border-collapse:collapse; }
.dtable th { background:#1e2444; color:#5a6490; font-size:.68rem; font-weight:700;
             text-transform:uppercase; letter-spacing:.6px; padding:10px 14px; text-align:left; }
.dtable td { color:#c8cfe8; font-size:.82rem; padding:9px 14px;
             border-bottom:1px solid rgba(255,255,255,0.04); vertical-align:middle; }
.dtable tr:hover td { background:rgba(139,92,246,.07); }
.dtable tr:last-child td { border-bottom:none; }

/* Badges */
.bselesai { background:#052e16; color:#4ade80; border:1px solid #166534; border-radius:20px; padding:2px 10px; font-size:.7rem; font-weight:600; white-space:nowrap; }
.bproses  { background:#1c1917; color:#fb923c; border:1px solid #9a3412; border-radius:20px; padding:2px 10px; font-size:.7rem; font-weight:600; white-space:nowrap; }
.bbelum   { background:#1e1b4b; color:#a5b4fc; border:1px solid #3730a3; border-radius:20px; padding:2px 10px; font-size:.7rem; font-weight:600; white-space:nowrap; }
.bteknis  { background:#431407; color:#fb923c; border-radius:20px; padding:2px 10px; font-size:.7rem; font-weight:600; white-space:nowrap; }
.brekening{ background:#0c3349; color:#38bdf8; border-radius:20px; padding:2px 10px; font-size:.7rem; font-weight:600; white-space:nowrap; }
.bpelayan { background:#052e16; color:#4ade80; border-radius:20px; padding:2px 10px; font-size:.7rem; font-weight:600; white-space:nowrap; }
.blainnya { background:#1e1b4b; color:#a5b4fc; border-radius:20px; padding:2px 10px; font-size:.7rem; font-weight:600; white-space:nowrap; }

.stTextInput input { background:#181e3a !important; border:1px solid rgba(255,255,255,0.12) !important;
                     color:white !important; border-radius:8px !important; }
.stTextInput input::placeholder { color:#4a5578 !important; }

/* Interactive Table Styling */
.th-cell {
    background: #181e3a; color: #7b8ab8; font-size: 0.68rem; font-weight: 700;
    letter-spacing: 0.6px; padding: 9px 8px; border-radius: 6px;
    white-space: nowrap; text-transform: uppercase;
}
.td-no { color: #5a6490; font-size: 0.75rem; font-weight: 600; }
.td-nama { color: white; font-size: 0.82rem; font-weight: 600; line-height: 1.25; }
.td-telp { color: #5a6490; font-size: 0.68rem; margin-top: 2px; }
.td-kec { color: #818cf8; font-size: 0.8rem; }
.td-bln { color: #7b8ab8; font-size: 0.78rem; }
.td-rin { color: #9aa3c8; font-size: 0.78rem; line-height: 1.25; }
.td-tgl { color: #7b8ab8; font-size: 0.75rem; }
.td-dur { color: #f59e0b; font-weight: 700; font-size: 0.8rem; }

/* Table Action Buttons */
div[data-testid="column"] button:has(p:contains("✏️")),
div[data-testid="column"] button:has(span:contains("✏️")) {
    background: rgba(99, 102, 241, 0.15) !important;
    border: 1px solid rgba(99, 102, 241, 0.4) !important;
    color: #a5b4fc !important;
    padding: 0 !important;
    min-height: 32px !important;
    height: 32px !important;
    width: 100% !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}
div[data-testid="column"] button:has(p:contains("✏️")):hover,
div[data-testid="column"] button:has(span:contains("✏️")):hover {
    background: rgba(99, 102, 241, 0.35) !important;
    border-color: #818cf8 !important;
    transform: translateY(-1px);
}

div[data-testid="column"] button:has(p:contains("🗑️")),
div[data-testid="column"] button:has(span:contains("🗑️")) {
    background: rgba(239, 68, 68, 0.15) !important;
    border: 1px solid rgba(239, 68, 68, 0.4) !important;
    color: #fca5a5 !important;
    padding: 0 !important;
    min-height: 32px !important;
    height: 32px !important;
    width: 100% !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}
div[data-testid="column"] button:has(p:contains("🗑️")):hover,
div[data-testid="column"] button:has(span:contains("🗑️")):hover {
    background: rgba(239, 68, 68, 0.35) !important;
    border-color: #f87171 !important;
    transform: translateY(-1px);
}
</style>
""", unsafe_allow_html=True)

for _k, _v in {
    "logged_in":      False,
    "user":           None,
    "pg":             0,
    "active_section": "laporan",
    "prev_page":      "📈  Grafik & Peta",
    "prev_crud":      "➕  Tambah Data",
    "login_error":    "",
}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

def recluster(r: dict) -> str:
    if r.get("kebocoran_pipa_dinas") or r.get("kebocoran_instalatur") or r.get("supply_air"):
        return "TEKNIS"
    if r.get("pembayaran_melonjak"): return "REKENING AIR"
    if r.get("water_meter_rusak"):   return "PELAYANAN"
    return "LAINNYA"

@st.cache_data(ttl=60)
def _load_data_cached(cabang: str) -> pd.DataFrame:
    return _db.fetch_pengaduan(cabang)

def get_df() -> pd.DataFrame:
    if not DB_OK:
        return pd.DataFrame()
    cabang = st.session_state.user["cabang"] if st.session_state.user["role"] == "cabang" else None
    return _load_data_cached(cabang)

def sbadge(s):
    s = str(s).upper()
    if "SELESAI" in s: return '<span class="bselesai">✓ Selesai</span>'
    if "PROSES"  in s: return '<span class="bproses">⟳ Proses</span>'
    return '<span class="bbelum">○ Belum</span>'

def cbadge(c):
    c = str(c).upper()
    if c=="TEKNIS":       return '<span class="bteknis">🔧 Teknis</span>'
    if c=="REKENING AIR": return '<span class="brekening">💰 Rekening</span>'
    if c=="PELAYANAN":    return '<span class="bpelayan">🔩 Pelayanan</span>'
    return '<span class="blainnya">📌 Lainnya</span>'

# Auto-restore session dari st.query_params jika halaman di-refresh (F5)
if not st.session_state.logged_in and DB_OK:
    saved_user = st.query_params.get("session_user")
    if saved_user:
        user_info = _db.get_user_by_username(saved_user)
        if user_info:
            st.session_state.logged_in = True
            st.session_state.user = user_info
            _load_data_cached.clear()  # Pastikan data terbaru di-fetch dari MySQL saat refresh

# LOGIN PAGE
if not st.session_state.logged_in:

    st.markdown("""
    <style>
    section[data-testid="stSidebar"]     { display: none !important; }
    [data-testid="stAppViewContainer"]   { margin-left: 0 !important; }
    </style>
    """, unsafe_allow_html=True)

    if not DB_OK:
        st.markdown(f"""
        <div style="background:#1c0a0a;border:1px solid rgba(239,68,68,.4);border-radius:10px;
             padding:12px 16px;margin-bottom:16px;font-size:.82rem;">
          <b style="color:#f87171;">⚠️ Database belum terhubung</b>
          <div style="color:#9aa3c8;margin-top:4px;">{DB_ERROR}</div>
          <div style="color:#6b7280;margin-top:6px;font-size:.75rem;">
            Edit <code style="color:#818cf8;">db.py</code> →
            sesuaikan <code style="color:#818cf8;">DB_CONFIG</code>
            (host, user, password, database) lalu restart app.
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Centered login card
    _, mid, _ = st.columns([1, 1.1, 1])
    with mid:
        st.markdown(f"""
        <div style="text-align:center;padding:32px 0 24px;">
          <div style="display:inline-flex;align-items:center;justify-content:center;
               background:linear-gradient(135deg,#1e3a8a,#3b82f6);
               width:68px;height:68px;border-radius:18px;margin-bottom:16px;
               box-shadow:0 8px 24px rgba(30,58,138,0.5);">
            {logo_img("52px","12px")}
          </div>
          <div style="color:white;font-family:'Sora',sans-serif;font-size:1.3rem;
               font-weight:700;margin-bottom:4px;">Dashboard Pengaduan</div>
          <div style="color:#4a5578;font-size:.8rem;">
            PERUMDA Air Minum Tirta Jaya Mandiri — Kabupaten Sukabumi</div>
        </div>
        """, unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="login-card">', unsafe_allow_html=True)

            username_input = st.text_input("Username", placeholder="contoh: pusat atau cb_cibadak", key="login_username")
            password_input = st.text_input("Password", type="password", placeholder="Password Anda", key="login_password")

            # error login 
            if st.session_state.login_error:
                st.markdown(f"""
                <div style="background:rgba(239,68,68,0.12);border:1px solid rgba(239,68,68,0.3);
                     border-radius:8px;padding:10px 14px;margin:8px 0;color:#f87171;font-size:.82rem;">
                  {st.session_state.login_error}
                </div>
                """, unsafe_allow_html=True)

            btn_masuk = st.button("🔐  Masuk", use_container_width=True, type="primary")

            if btn_masuk:
                st.session_state.login_error = ""
                if not username_input.strip() or not password_input:
                    st.session_state.login_error = "Username dan password wajib diisi."
                    st.rerun()
                elif not DB_OK:
                    st.session_state.login_error = f"Database tidak terhubung. Periksa konfigurasi db.py."
                    st.rerun()
                else:
                    result = _db.login(username_input.strip(), password_input)
                    if result:
                        st.session_state.logged_in    = True
                        st.session_state.user         = result
                        st.session_state.login_error  = ""
                        st.query_params["session_user"] = result["username"]
                        _load_data_cached.clear()
                        st.rerun()
                    else:
                        st.session_state.login_error = "Username atau password salah."
                        st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

        # Hint password dihapus sesuai permintaan

    st.stop()   

user        = st.session_state.user
is_pusat    = user["role"] == "pusat"
user_cabang = user.get("cabang")
scope_label = "Semua Cabang" if is_pusat else f"Cabang {user_cabang}"

# Sidebar toggle button (JS injected into parent doc) 
components.html("""
<script>
(function() {
  var doc = window.parent.document;
  var old = doc.getElementById('__pdam_toggle__');
  if (old) old.remove();
                

  if (!doc.getElementById('__pdam_toggle_css__')) {
    var s = doc.createElement('style'); s.id = '__pdam_toggle_css__';
    s.textContent = `
      #__pdam_toggle__ {
        position:fixed; top:14px; left:14px; z-index:2147483647;
        width:34px; height:34px; display:flex; align-items:center; justify-content:center;
        background:#1a2040; border:1px solid rgba(255,255,255,0.12); border-radius:8px;
        cursor:pointer; box-shadow:0 2px 12px rgba(0,0,0,0.5);
        transition:background .2s,border-color .2s; outline:none; padding:0;
      }
      #__pdam_toggle__:hover { background:rgba(99,102,241,0.28); border-color:#6366f1; }
      #__pdam_toggle__ svg { display:block; transition:transform .32s cubic-bezier(.4,0,.2,1); }
      #__pdam_toggle__.is-collapsed svg { transform:scaleX(-1); }
    `;
    doc.head.appendChild(s);
  }

  var btn = doc.createElement('button');
  btn.id = '__pdam_toggle__'; btn.title = 'Toggle sidebar';
  btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 18 18" fill="none">
    <rect x="1.5" y="1.5" width="5" height="15" rx="1.2"
          fill="rgba(99,102,241,0.18)" stroke="#818cf8" stroke-width="1.3"/>
    <line x1="10" y1="5"  x2="16.5" y2="5"  stroke="#a5b4fc" stroke-width="1.4" stroke-linecap="round"/>
    <line x1="10" y1="9"  x2="16.5" y2="9"  stroke="#a5b4fc" stroke-width="1.4" stroke-linecap="round"/>
    <line x1="10" y1="13" x2="16.5" y2="13" stroke="#a5b4fc" stroke-width="1.4" stroke-linecap="round"/>
  </svg>`;

  var collapsed = false, SIDEBAR_W = 230, ANIM_MS = 320;
  btn.onclick = function() {
    collapsed = !collapsed;
    var sb = doc.querySelector('section[data-testid="stSidebar"]');
    var aw = doc.querySelector('[data-testid="stAppViewContainer"]');
    var main = doc.querySelector('section.main') || doc.querySelector('main');
    if (!sb || !aw) return;
    if (collapsed) {
      sb.style.setProperty('transition', 'transform '+ANIM_MS+'ms cubic-bezier(.4,0,.2,1), min-width '+ANIM_MS+'ms, max-width '+ANIM_MS+'ms, width '+ANIM_MS+'ms', 'important');
      sb.style.setProperty('transform', 'translateX(-'+(SIDEBAR_W+10)+'px)', 'important');
      sb.style.setProperty('min-width', '0px', 'important');
      sb.style.setProperty('max-width', '0px', 'important');
      sb.style.setProperty('width', '0px', 'important');
      sb.style.setProperty('flex-basis', '0px', 'important');
      sb.style.setProperty('overflow', 'hidden', 'important');
      sb.style.setProperty('border-right', 'none', 'important');
      sb.style.setProperty('opacity', '0', 'important');
      sb.style.setProperty('pointer-events', 'none', 'important');
      aw.style.setProperty('margin-left', '0px', 'important');
      aw.style.setProperty('width', '100vw', 'important');
      aw.style.setProperty('max-width', '100vw', 'important');
      if (main) {
        main.style.setProperty('width', '100%', 'important');
        main.style.setProperty('max-width', '100%', 'important');
      }
      btn.classList.add('is-collapsed');
    } else {
      sb.style.setProperty('transform', 'translateX(0)', 'important');
      sb.style.setProperty('min-width', SIDEBAR_W+'px', 'important');
      sb.style.setProperty('max-width', SIDEBAR_W+'px', 'important');
      sb.style.setProperty('width', SIDEBAR_W+'px', 'important');
      sb.style.removeProperty('flex-basis');
      sb.style.removeProperty('overflow');
      sb.style.setProperty('border-right', '1px solid rgba(255,255,255,0.07)', 'important');
      sb.style.setProperty('opacity', '1', 'important');
      sb.style.removeProperty('pointer-events');
      aw.style.removeProperty('margin-left');
      aw.style.removeProperty('width');
      aw.style.removeProperty('max-width');
      if (main) {
        main.style.removeProperty('width');
        main.style.removeProperty('max-width');
      }
      setTimeout(function(){ aw.style.removeProperty('transition'); }, ANIM_MS+20);
      btn.classList.remove('is-collapsed');
    }
  };
  doc.body.appendChild(btn);
})();
</script>
""", height=0, scrolling=False)

# ── Dialogs: Edit & Delete Pengaduan (Dipanggil dari Tabel Data Interaktif) ──
@st.dialog("✏️ Edit Data Pengaduan", width="large")
def dialog_edit_pengaduan(row_id: int):
    df_curr = get_df()
    match = df_curr[df_curr["No"].astype(str) == str(row_id)]
    if match.empty:
        _load_data_cached.clear()
        df_curr = get_df()
        match = df_curr[df_curr["No"].astype(str) == str(row_id)]
    if match.empty:
        st.error(f"Data dengan ID #{row_id} tidak ditemukan.")
        return
    row = match.iloc[0]

    foto_val = str(row.get("Foto")).strip() if pd.notna(row.get("Foto")) and str(row.get("Foto")).strip() not in ("", "None", "nan") else None

    st.markdown(f"""
    <div style="background:#161b36;border:1px solid rgba(99,102,241,0.25);border-radius:10px;padding:10px 14px;margin-bottom:14px;display:flex;justify-content:space-between;align-items:center;">
      <div>
        <span style="color:#818cf8;font-weight:700;">ID #{row_id}</span> &nbsp;|&nbsp;
        <b style="color:white;">{row['Nama_Pelanggan']}</b> &nbsp;|&nbsp;
        <span style="color:#9aa3c8;">{row['Cabang']}</span>
      </div>
      <div>
        {cbadge(row['Cluster'])} &nbsp; {sbadge(row['Status'])}
      </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form(f"form_dialog_edit_{row_id}"):
        c1, c2 = st.columns(2)
        with c1:
            nm = st.text_input("Nama Pelanggan *", value=str(row["Nama_Pelanggan"]))
            tl = st.text_input("No. Telepon / HP", value=str(row["No_Telp"]) if pd.notna(row.get("No_Telp")) and str(row.get("No_Telp")) not in ("None","nan") else "")
            ns = st.text_input("No. Sambung", value=str(row["No_Sambung"]) if pd.notna(row.get("No_Sambung")) and str(row.get("No_Sambung")) not in ("None","nan") else "")
            al = st.text_area("Alamat Lengkap", value=str(row["Alamat"]) if pd.notna(row.get("Alamat")) and str(row.get("Alamat")) not in ("None","nan") else "", height=80)
            cb = st.selectbox("Cabang", CABANG_LIST, index=CABANG_LIST.index(row["Cabang"]) if row["Cabang"] in CABANG_LIST else 0) if is_pusat else user_cabang
            if not is_pusat:
                st.text_input("Cabang", value=user_cabang, disabled=True)
            bl = st.selectbox("Bulan", BULAN_ORDER, index=BULAN_ORDER.index(row["Bulan"]) if row["Bulan"] in BULAN_ORDER else 0)
        with c2:
            tp  = st.date_input("Tgl Pengaduan",  value=row["Tgl_Pengaduan"].date()    if pd.notna(row["Tgl_Pengaduan"])    else date.today())
            ts  = st.date_input("Tgl Selesai",    value=row["Tgl_Penyelesaian"].date() if pd.notna(row["Tgl_Penyelesaian"]) else date.today())
            st_ = st.selectbox("Status", STATUS_LIST, index=STATUS_LIST.index(row["Status"]) if row["Status"] in STATUS_LIST else 0)
            rn  = st.text_area("Rincian Keluhan", value=str(row["Rincian"]) if pd.notna(row.get("Rincian")) and str(row.get("Rincian")) not in ("None","nan") else "", height=80)

            if foto_val:
                img_path = BASE_DIR.parent / "static" / foto_val
                if img_path.exists():
                    st.markdown("📷 **Foto Pengaduan**")
                    st.image(str(img_path), caption=f"File: {foto_val}", use_container_width=True)
                else:
                    st.caption(f"📷 Foto Bukti: `{foto_val}` (file tidak ada di server)")
            else:
                st.caption("ℹ️ Tidak ada foto bukti yang diunggah dari portal.")

        st.markdown("**Jenis Pengaduan:**")
        j1,j2,j3,j4,j5 = st.columns(5)
        kpd = j1.checkbox("Keb. Pipa Dinas", value=bool(row["Kebocoran_Pipa_Dinas"]))
        ki  = j2.checkbox("Keb. Instalatur",  value=bool(row["Kebocoran_Instalatur"]))
        sa  = j3.checkbox("Supply Air",        value=bool(row["Supply_Air"]))
        pm  = j4.checkbox("Pmbyr Melonjak",    value=bool(row["Pembayaran_Melonjak"]))
        wmr = j5.checkbox("WM Rusak",          value=bool(row["Water_Meter_Rusak"]))

        b_sub, b_can = st.columns([2, 1])
        with b_sub:
            submitted = st.form_submit_button("💾 Simpan Perubahan", use_container_width=True, type="primary")
        with b_can:
            cancelled = st.form_submit_button("✖ Batal", use_container_width=True)

        if cancelled:
            st.rerun()

        if submitted:
            if not nm.strip():
                st.error("Nama pelanggan wajib diisi!")
            else:
                data = {
                    "cabang": cb, "bulan": bl, "bulan_num": BULAN_ORDER.index(bl)+1,
                    "nama_pelanggan": nm.strip(), "no_telp": tl or None, "no_sambung": ns or None,
                    "kebocoran_pipa_dinas": int(kpd), "kebocoran_instalatur": int(ki),
                    "supply_air": int(sa), "pembayaran_melonjak": int(pm),
                    "water_meter_rusak": int(wmr), "lainnya": 0,
                    "alamat": al or None, "foto": foto_val, "rincian": rn or None, "status": st_,
                    "tgl_pengaduan": tp, "tgl_penyelesaian": ts,
                    "cluster": recluster({"kebocoran_pipa_dinas":kpd,"kebocoran_instalatur":ki,
                                          "supply_air":sa,"pembayaran_melonjak":pm,"water_meter_rusak":wmr}),
                    "durasi": max((ts - tp).days, 0),
                }
                _db.update_pengaduan(row_id, data)
                _load_data_cached.clear()
                st.success(f"✅ Data #{row_id} (**{nm}**) berhasil diperbarui!")
                st.rerun()

@st.dialog("🗑️ Konfirmasi Hapus Data")
def dialog_delete_pengaduan(row_id: int):
    df_curr = get_df()
    match = df_curr[df_curr["No"].astype(str) == str(row_id)]
    if match.empty:
        _load_data_cached.clear()
        df_curr = get_df()
        match = df_curr[df_curr["No"].astype(str) == str(row_id)]
    if match.empty:
        st.error(f"Data dengan ID #{row_id} tidak ditemukan.")
        return
    row = match.iloc[0]

    no_tlp_str = f" &nbsp;|&nbsp; 📞 <b>Telp:</b> {row['No_Telp']}" if pd.notna(row.get("No_Telp")) and str(row.get("No_Telp")) not in ("None","nan","") else ""
    alamat_str = f"<br>📍 <b>Alamat:</b> {row['Alamat']}" if pd.notna(row.get("Alamat")) and str(row.get("Alamat")) not in ("None","nan") else ""

    st.markdown(f"""
    <div style="background:#1c0f14;border:1px solid rgba(239,68,68,.35);
         border-radius:12px;padding:16px 20px;margin:10px 0;">
      <div style="color:#f87171;font-weight:700;margin-bottom:8px;font-size:0.92rem;">
        ⚠️ Yakin ingin menghapus data ini secara permanen?
      </div>
      <div style="color:#c8cfe8;font-size:.84rem;line-height:2.0;">
        🆔 <b>ID:</b> #{row_id} &nbsp;|&nbsp;
        👤 <b>Nama:</b> {row['Nama_Pelanggan']}{no_tlp_str}<br>
        🏢 <b>Cabang:</b> {row['Cabang']} &nbsp;|&nbsp;
        📅 <b>Bulan:</b> {row['Bulan']}<br>
        🏷️ <b>Cluster:</b> {row['Cluster']}<br>
        📋 <b>Status:</b> {row['Status']}{alamat_str}
      </div>
    </div>""", unsafe_allow_html=True)

    c_del, c_can = st.columns([1.5, 1])
    with c_del:
        if st.button("🗑️ Hapus Permanen", type="primary", use_container_width=True, key=f"btn_confirm_del_{row_id}"):
            _db.delete_pengaduan(row_id)
            _load_data_cached.clear()
            st.success(f"✅ Data #{row_id} berhasil dihapus!")
            st.rerun()
    with c_can:
        if st.button("✖ Batal", use_container_width=True, key=f"btn_cancel_del_{row_id}"):
            st.rerun()

# SIDEBAR 
with st.sidebar:
    st.markdown(f"""
    <div style="padding:20px 20px 14px;border-bottom:1px solid rgba(255,255,255,0.07);">
      <div style="display:flex;align-items:center;gap:10px;">
        <div style="background:linear-gradient(135deg,#1e3a8a,#3b82f6);width:40px;height:40px;
             border-radius:9px;flex-shrink:0;overflow:hidden;padding:3px;
             display:flex;align-items:center;justify-content:center;">
          {logo_img("34px","6px")}
        </div>
        <div>
          <div style="color:white!important;font-weight:700;font-size:.93rem;font-family:'Sora',sans-serif;">PERUMDA AM TJM</div>
          <div style="color:#4a5578!important;font-size:.7rem;margin-top:1px;">Dashboard Pengaduan</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # User chip
    role_label = "👑 Pusat — Akses Penuh" if is_pusat else f"🏢 {user_cabang}"
    st.markdown(f"""
    <div class="user-chip">
      <div class="uname">{user['nama_lengkap']}</div>
      <div class="urole">{role_label}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-section">📌 Menu Navigasi</div>', unsafe_allow_html=True)
    nav_menu = st.radio("nav_menu",
                        ["📈  Grafik & Peta", "📋  Tabel Data Interaktif", "➕  Tambah Data"],
                        label_visibility="collapsed", key="nav_menu")
    st.caption("💡 Edit dan Hapus data kini langsung di Tabel Data Interaktif.")

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)

    is_laporan = nav_menu in ["📈  Grafik & Peta", "📋  Tabel Data Interaktif"]
    if is_laporan:
        st.markdown('<div class="sb-section">🔽 Filter Data</div>', unsafe_allow_html=True)
        bulan_sel   = st.multiselect("Bulan",   BULAN_ORDER, default=[])
        cluster_sel = st.multiselect("Cluster", list(COLORS.keys()), default=[])
        cabang_sel  = st.multiselect("Cabang",  CABANG_LIST, default=[]) if is_pusat else []
        st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)

        st.markdown('<div class="sb-section">🎫 Tickets Status</div>', unsafe_allow_html=True)
        _df_tmp = get_df()
        _n      = len(_df_tmp)
        _nsel   = int(_df_tmp["Status"].str.contains("SELESAI",na=False).sum()) if _n else 0
        _npro   = int(_df_tmp["Status"].str.contains("PROSES",na=False).sum())  if _n else 0
        _nbel   = int(_df_tmp["Status"].str.contains("BELUM",na=False).sum())   if _n else 0
        st.markdown("".join([
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:8px 20px;border-bottom:1px solid rgba(255,255,255,0.05);">'
            f'<span style="color:#7b86b0!important;font-size:.82rem;">{lbl}</span>'
            f'<span style="background:{bg};color:{fg}!important;border-radius:12px;'
            f'padding:2px 10px;font-size:.72rem;font-weight:700;">{val}</span></div>'
            for lbl,bg,fg,val in [
                ("Total",  "#1e2444","#a5b4fc",f"{_n:,}"),
                ("Selesai","#052e16","#4ade80",f"{_nsel:,}"),
                ("Proses", "#431407","#fb923c",str(_npro)),
                ("Belum",  "#1e1b4b","#a5b4fc",str(_nbel)),
            ]
        ]) + '<div style="margin-bottom:8px;"></div>', unsafe_allow_html=True)
    else:
        bulan_sel, cluster_sel, cabang_sel = [], [], []

    if st.button("🔄  Refresh Data Terbaru", use_container_width=True, key="btn_refresh_data"):
        _load_data_cached.clear()
        st.rerun()

    if st.button("🚪  Logout", use_container_width=True, key="btn_logout"):
        for _k in ["logged_in","user","pg","active_section","prev_page","prev_crud","login_error"]:
            st.session_state.pop(_k, None)
        st.query_params.clear()
        st.rerun()

# Routing
if nav_menu == "➕  Tambah Data":
    active = "crud"
    crud   = "Tambah"
    page   = ""
elif nav_menu == "📋  Tabel Data Interaktif":
    active = "laporan"
    page   = "Tabel Data Interaktif"
    crud   = ""
else:
    active = "laporan"
    page   = "Grafik & Peta"
    crud   = ""

st.session_state.active_section = active

# Apply filters 
df = get_df()
if bulan_sel:   df = df[df["Bulan"].isin(bulan_sel)]
if cluster_sel: df = df[df["Cluster"].isin(cluster_sel)]
# Clamp years to 2026 for date columns
for col in ["Tgl_Pengaduan", "Tgl_Penyelesaian"]:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')
        df.loc[df[col].dt.year > 2026, col] = df[col].apply(lambda d: d.replace(year=2026) if pd.notnull(d) else d)
if is_pusat and cabang_sel:
    df = df[df["Cabang"].isin(cabang_sel)]

st.markdown(f"""
<div style="background:linear-gradient(135deg,#12172e,#1a2040);border-radius:14px;
     padding:16px 22px;margin-bottom:18px;display:flex;align-items:center;gap:14px;
     border:1px solid rgba(255,255,255,0.06);">
  <div style="background:linear-gradient(135deg,#1e3a8a,#3b82f6);width:48px;height:48px;
       border-radius:11px;display:flex;align-items:center;justify-content:center;
       overflow:hidden;padding:4px;">
    {logo_img("40px","7px")}
  </div>
  <div style="flex:1">
    <div style="color:white;font-weight:700;font-size:1.1rem;font-family:'Sora',sans-serif;">
      Dashboard Pengaduan Pelanggan </div>
    <div style="color:#4a5578;font-size:.78rem;margin-top:2px;">
      PERUSAHAAN UMUM DAERAH AIR MINUM TIRTA JAYA MANDIRI — {scope_label.upper()}</div>
  </div>
  <div style="background:#1e2444;border-radius:10px;padding:8px 18px;text-align:center;">
    <div style="color:#4a5578;font-size:.65rem;text-transform:uppercase;letter-spacing:.5px;">Data</div>
    <div style="color:white;font-size:1.3rem;font-weight:800;font-family:'Sora',sans-serif;">{len(df):,}</div>
  </div>
</div>
""", unsafe_allow_html=True)

if not DB_OK:
    st.error(f"⚠️ Database tidak terhubung: {DB_ERROR}")
    st.info("Edit `db.py` → sesuaikan `DB_CONFIG` → restart app.")
    st.stop()

# KELOLA DATA
if active == "crud":
    st.markdown('<div class="sec-hdr">➕ Tambah Data Pengaduan</div>', unsafe_allow_html=True)
    with st.form("f_tambah", clear_on_submit=True):
        c1,c2 = st.columns(2)
        with c1:
            nama      = st.text_input("Nama Pelanggan *")
            notelp    = st.text_input("No. Telepon / HP")
            nosambung = st.text_input("No. Sambung")
            alamat    = st.text_area("Alamat", height=70)
            cab       = st.selectbox("Cabang *", CABANG_LIST) if is_pusat else user_cabang
            if not is_pusat:
                st.text_input("Cabang", value=user_cabang, disabled=True)
            bln = st.selectbox("Bulan *", BULAN_ORDER)
        with c2:
            tgl_p = st.date_input("Tgl Pengaduan *")
            tgl_s = st.date_input("Tgl Penyelesaian")
            sts   = st.selectbox("Status", STATUS_LIST)
            rin   = st.text_area("Rincian", height=70)
        st.markdown("**Jenis Pengaduan:**")
        j1,j2,j3,j4,j5 = st.columns(5)
        kpd=j1.checkbox("Keb. Pipa Dinas"); ki=j2.checkbox("Keb. Instalatur")
        sa=j3.checkbox("Supply Air"); pm=j4.checkbox("Pmbyr Melonjak"); wmr=j5.checkbox("WM Rusak")
        if st.form_submit_button("💾 Simpan ke Database", use_container_width=True):
            if not nama.strip():
                st.error("Nama wajib diisi!")
            else:
                payload = {
                    "cabang": cab, "bulan": bln, "bulan_num": BULAN_ORDER.index(bln)+1,
                    "nama_pelanggan": nama.strip(), "no_telp": notelp or None, "no_sambung": nosambung or None, "blok": None,
                    "kebocoran_pipa_dinas": int(kpd), "kebocoran_instalatur": int(ki),
                    "supply_air": int(sa), "pembayaran_melonjak": int(pm),
                    "water_meter_rusak": int(wmr), "lainnya": 0,
                    "alamat": alamat or None, "rincian": rin or None, "status": sts,
                    "tgl_pengaduan": tgl_p, "tgl_penyelesaian": tgl_s,
                    "cluster": recluster({"kebocoran_pipa_dinas":kpd,"kebocoran_instalatur":ki,
                                          "supply_air":sa,"pembayaran_melonjak":pm,"water_meter_rusak":wmr}),
                    "durasi": max((tgl_s - tgl_p).days, 0),
                    "created_by": user["username"],
                }
                new_id = _db.insert_pengaduan(payload)
                _load_data_cached.clear()
                st.success(f"✅ Data **{nama}** tersimpan! (ID: {new_id})")

# GRAFIK & PETA
elif active == "laporan" and "Grafik" in page:
    total = len(df)
    if total == 0:
        st.info("Belum ada data. Tambahkan melalui menu Kelola Data → Tambah Data.")
        st.stop()

    t_tek=(df["Cluster"]=="TEKNIS").sum(); t_rek=(df["Cluster"]=="REKENING AIR").sum()
    t_pel=(df["Cluster"]=="PELAYANAN").sum()
    pct_ok = df["Status"].str.contains("SELESAI",na=False).sum()/total*100
    avg_dur= df["Durasi"].dropna().mean() if "Durasi" in df.columns else 0

    c1,c2,c3,c4,c5 = st.columns(5)
    with c1: st.markdown(f'<div class="mc mc-blue"><span class="mc-ico">📊</span><div class="mc-lbl">Total Pengaduan</div><div class="mc-val">{total:,}</div><div class="mc-sub">{scope_label}</div></div>',unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="mc mc-orange"><span class="mc-ico">🔧</span><div class="mc-lbl">Teknis</div><div class="mc-val">{t_tek:,}</div><div class="mc-sub">{t_tek/total*100:.1f}%</div></div>',unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="mc mc-cyan"><span class="mc-ico">💰</span><div class="mc-lbl">Rekening Air</div><div class="mc-val">{t_rek:,}</div><div class="mc-sub">{t_rek/total*100:.1f}%</div></div>',unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="mc mc-green"><span class="mc-ico">🔩</span><div class="mc-lbl">Pelayanan</div><div class="mc-val">{t_pel:,}</div><div class="mc-sub">{t_pel/total*100:.1f}%</div></div>',unsafe_allow_html=True)
    with c5: st.markdown(f'<div class="mc mc-purple"><span class="mc-ico">⏱️</span><div class="mc-lbl">Avg Selesai</div><div class="mc-val">{avg_dur:.1f}h</div><div class="mc-sub">Selesai {pct_ok:.0f}%</div></div>',unsafe_allow_html=True)
    st.markdown("<br>",unsafe_allow_html=True)

    ca,cb_ = st.columns([1,2])
    with ca:
        st.markdown('<div class="sec-hdr">Distribusi Cluster</div>',unsafe_allow_html=True)
        cc = df["Cluster"].value_counts().reset_index(); cc.columns=["Cluster","n"]
        fig=px.pie(cc,names="Cluster",values="n",color="Cluster",color_discrete_map=COLORS,hole=0.58)
        fig.update_traces(textposition="outside",textinfo="percent+label",marker_line_width=2,marker_line_color="#0a0e1a")
        fig.update_layout(showlegend=False,height=290,margin=dict(t=10,b=10,l=10,r=10),paper_bgcolor="rgba(0,0,0,0)",font=dict(color="#c8cfe8"))
        st.plotly_chart(fig,use_container_width=True)
    with cb_:
        st.markdown('<div class="sec-hdr">Tren Pengaduan per Bulan</div>',unsafe_allow_html=True)
        db_=df.groupby(["Bulan","Bulan_Num","Cluster"]).size().reset_index(name="n").sort_values("Bulan_Num")
        fig=px.bar(db_,x="Bulan",y="n",color="Cluster",color_discrete_map=COLORS,barmode="group",category_orders={"Bulan":BULAN_ORDER})
        fig.update_layout(height=290,margin=dict(t=10,b=40,l=0,r=0),xaxis_title="",yaxis_title="",
                          legend=dict(orientation="h",y=-0.4,font=dict(color="#c8cfe8")),
                          paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                          xaxis=dict(tickfont=dict(size=10,color="#7b8ab8"),gridcolor="rgba(255,255,255,0.05)"),
                          yaxis=dict(gridcolor="rgba(255,255,255,0.05)",tickfont=dict(color="#7b8ab8")),font=dict(color="#c8cfe8"))
        st.plotly_chart(fig,use_container_width=True)

    if "lat" in df.columns and not df.empty:
        st.markdown('<div class="sec-hdr">Geo Map — Sebaran per Wilayah</div>', unsafe_allow_html=True)
        mt = df.dropna(subset=["lat", "lon"]).groupby(["Cabang", "Kec", "lat", "lon"]).size().reset_index(name="Total")
        if not mt.empty:
            dom = (df.groupby(["Cabang", "Cluster"]).size().reset_index(name="n")
                   .sort_values("n", ascending=False).drop_duplicates("Cabang")[["Cabang", "Cluster"]])
            md = mt.merge(dom, on="Cabang")
            md["hover"] = md.apply(lambda r: f"<b>{r['Kec']}</b><br>Total: {r['Total']}<br>Dominan: {r['Cluster']}", axis=1)
            fig = px.scatter_mapbox(
                md, lat="lat", lon="lon", size="Total", color="Cluster",
                color_discrete_map=COLORS, hover_name="Kec", custom_data=["hover"],
                size_max=50, zoom=8.5, center={"lat": -7.05, "lon": 106.75},
                mapbox_style="open-street-map", height=420
            )
            fig.update_traces(hovertemplate="%{customdata[0]}<extra></extra>", marker=dict(opacity=0.85, sizemin=8))
            fig.update_layout(
                margin=dict(t=0, b=0, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", y=-0.04, bgcolor="rgba(20,26,50,.85)", borderwidth=1, font=dict(color="white"))
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("ℹ️ Data lokasi (koordinat) tidak tersedia untuk filter saat ini.")

    ce_,cf_ = st.columns(2)
    with ce_:
        st.markdown('<div class="sec-hdr">Heatmap Bulan × Cluster</div>',unsafe_allow_html=True)
        hdf=(df[df["Cluster"]!="LAINNYA"].groupby(["Bulan","Bulan_Num","Cluster"]).size().reset_index(name="n").sort_values("Bulan_Num"))
        if not hdf.empty:
            hpv=hdf.pivot_table(index="Cluster",columns="Bulan",values="n",fill_value=0)
            hpv=hpv.reindex(columns=[b for b in BULAN_ORDER if b in hpv.columns])
            fig=px.imshow(hpv,text_auto=True,color_continuous_scale="Plasma",aspect="auto")
            fig.update_layout(height=240,margin=dict(t=10,b=10,l=0,r=0),coloraxis_showscale=False,
                              paper_bgcolor="rgba(0,0,0,0)",
                              xaxis=dict(tickfont=dict(size=9,color="#7b8ab8")),yaxis=dict(tickfont=dict(size=10,color="#7b8ab8")))
            st.plotly_chart(fig,use_container_width=True)
    with cf_:
        st.markdown('<div class="sec-hdr">Distribusi Durasi (Hari)</div>',unsafe_allow_html=True)
        if "Durasi" in df.columns:
            # Duplicate histogram block removed
            ddf = df.dropna(subset=["Durasi"]).copy()
            if not ddf.empty:
                min_dur = ddf["Durasi"].min()
                max_dur = ddf["Durasi"].max()
                fig = px.histogram(
                    ddf,
                    x="Durasi",
                    color="Cluster",
                    color_discrete_map=COLORS,
                    nbins=30,
                    barmode="overlay",
                    opacity=0.75,
                )
                fig.update_layout(
                    height=240,
                    margin=dict(t=10, b=20, l=0, r=0),
                    xaxis_title="Hari",
                    yaxis_title="",
                    legend=dict(orientation="h", y=-0.5, font=dict(size=10, color="#c8cfe8")),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(range=[min_dur, max_dur], gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color="#7b8ab8")),
                    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", tickfont=dict(color="#7b8ab8")),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Tidak ada data Durasi untuk ditampilkan.")
        else:
            st.info("Kolom 'Durasi' tidak tersedia.")

# TABEL DATA 
elif active == "laporan" and "Tabel" in page:
    st.markdown('<div class="sec-hdr">📋 Tabel Data Pengaduan — Interaktif</div>',unsafe_allow_html=True)

    sc1,sc2,sc3,sc4 = st.columns([3,1.5,1.5,1.5])
    with sc1: q       = st.text_input("🔍 Cari nama / no sambung / rincian / cabang...", key="tbl_q")
    with sc2: fcl     = st.selectbox("Cluster", ["Semua"]+list(COLORS.keys()), key="tbl_cl")
    with sc3: fst     = st.selectbox("Status",  ["Semua"]+STATUS_LIST, key="tbl_st")
    with sc4: sort_by = st.selectbox("Urutkan", ["Tgl_Pengaduan","Nama_Pelanggan","Kec","Durasi","Cluster"], key="tbl_sort")
    sort_asc = st.toggle("Urutan Naik ↑", value=False, key="tbl_asc")

    dt = df.copy()
    if q:
        mask = (dt["Nama_Pelanggan"].astype(str).str.contains(q,case=False,na=False)|
                dt["No_Sambung"].astype(str).str.contains(q,case=False,na=False)|
                dt["Rincian"].astype(str).str.contains(q,case=False,na=False)|
                dt["Cabang"].astype(str).str.contains(q,case=False,na=False)|
                dt["Kec"].astype(str).str.contains(q,case=False,na=False))
        dt = dt[mask]
    if fcl!="Semua": dt=dt[dt["Cluster"]==fcl]
    if fst!="Semua": dt=dt[dt["Status"]==fst]
    if sort_by in dt.columns: dt=dt.sort_values(sort_by,ascending=sort_asc)
    n_total = len(dt)

    sm1,sm2,sm3,sm4 = st.columns(4)
    with sm1: st.metric("📊 Ditampilkan", f"{n_total:,}")
    with sm2:
        pok = dt["Status"].str.contains("SELESAI",na=False).sum()/n_total*100 if n_total else 0
        st.metric("✅ Selesai", f"{pok:.1f}%")
    with sm3:
        ad = dt["Durasi"].dropna().mean() if "Durasi" in dt.columns and n_total else 0
        st.metric("⏱️ Avg Durasi", f"{ad:.1f} hari" if n_total else "—")
    with sm4:
        tc = dt["Cluster"].value_counts().index[0] if n_total else "—"
        st.metric("🏷️ Dominan", tc)

    # Filter per Cabang — hanya untuk akses Pusat
    if is_pusat:
        cb_opts = ["Semua Cabang"] + sorted(dt["Cabang"].dropna().unique().tolist())
        # Restore filter dari session state
        if "tbl_cabang_filter" not in st.session_state:
            st.session_state["tbl_cabang_filter"] = "Semua Cabang"
        # Pastikan nilai yang tersimpan masih valid
        if st.session_state["tbl_cabang_filter"] not in cb_opts:
            st.session_state["tbl_cabang_filter"] = "Semua Cabang"

        fc_cols = st.columns([1, 5])
        with fc_cols[0]:
            st.markdown('<div style="padding-top:8px;color:#7b8ab8;font-size:.78rem;font-weight:600;">🏢 Cabang:</div>', unsafe_allow_html=True)
        with fc_cols[1]:
            cb_sel = st.selectbox(
                "Pilih Cabang",
                cb_opts,
                index=cb_opts.index(st.session_state["tbl_cabang_filter"]),
                label_visibility="collapsed",
                key="tbl_cabang_sel",
            )
            st.session_state["tbl_cabang_filter"] = cb_sel

        # Terapkan filter cabang ke dt
        if cb_sel != "Semua Cabang":
            dt = dt[dt["Cabang"] == cb_sel]

            # Mini summary card untuk cabang terpilih
            n_cb   = len(dt)
            sel_cb = dt["Status"].str.contains("SELESAI", na=False).sum()
            pro_cb = dt["Status"].str.contains("PROSES", na=False).sum()
            bel_cb = dt["Status"].str.contains("BELUM", na=False).sum()
            pct_cb = sel_cb / n_cb * 100 if n_cb else 0
            avg_cb = dt["Durasi"].dropna().mean() if "Durasi" in dt.columns else 0
            dom_cb = dt["Cluster"].value_counts().index[0] if n_cb else "—"
            pct_color_cb = "#4ade80" if pct_cb >= 70 else "#fb923c" if pct_cb >= 40 else "#f87171"

            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#12172e,#161e3a);border:1px solid rgba(99,102,241,0.3);
                 border-radius:12px;padding:12px 18px;margin:8px 0 4px;
                 display:flex;align-items:center;gap:24px;flex-wrap:wrap;">
              <div style="flex:1;min-width:140px;">
                <div style="color:#7b8ab8;font-size:.65rem;text-transform:uppercase;letter-spacing:.8px;margin-bottom:2px;">Cabang Dipilih</div>
                <div style="color:white;font-weight:700;font-size:.95rem;font-family:'Sora',sans-serif;">🏢 {cb_sel}</div>
              </div>
              <div style="text-align:center;min-width:70px;">
                <div style="color:#7b8ab8;font-size:.62rem;text-transform:uppercase;">Total</div>
                <div style="color:white;font-weight:800;font-size:1.3rem;">{n_cb:,}</div>
              </div>
              <div style="text-align:center;min-width:70px;">
                <div style="color:#7b8ab8;font-size:.62rem;text-transform:uppercase;">Selesai</div>
                <div style="color:#4ade80;font-weight:700;font-size:1.1rem;">{sel_cb}</div>
              </div>
              <div style="text-align:center;min-width:70px;">
                <div style="color:#7b8ab8;font-size:.62rem;text-transform:uppercase;">Proses</div>
                <div style="color:#fb923c;font-weight:700;font-size:1.1rem;">{pro_cb}</div>
              </div>
              <div style="text-align:center;min-width:70px;">
                <div style="color:#7b8ab8;font-size:.62rem;text-transform:uppercase;">Belum</div>
                <div style="color:#a5b4fc;font-weight:700;font-size:1.1rem;">{bel_cb}</div>
              </div>
              <div style="text-align:center;min-width:80px;">
                <div style="color:#7b8ab8;font-size:.62rem;text-transform:uppercase;">% Selesai</div>
                <div style="color:{pct_color_cb};font-weight:800;font-size:1.1rem;">{pct_cb:.1f}%</div>
              </div>
              <div style="text-align:center;min-width:80px;">
                <div style="color:#7b8ab8;font-size:.62rem;text-transform:uppercase;">Avg Durasi</div>
                <div style="color:#f59e0b;font-weight:700;font-size:1rem;">{avg_cb:.1f} hr</div>
              </div>
              <div style="text-align:center;min-width:100px;">
                <div style="color:#7b8ab8;font-size:.62rem;text-transform:uppercase;">Dominan</div>
                <div>{cbadge(dom_cb)}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        # Recalculate n_total setelah filter cabang
        n_total = len(dt)

    # Pagination controls & Page size
    p_ctrl1, p_ctrl2, p_ctrl3, p_ctrl4 = st.columns([1, 2, 1, 1], vertical_alignment="center")
    PAGE = p_ctrl4.selectbox("Tampilkan", [15, 25, 50, 100], index=0, key="tbl_page_size")
    n_pages = max(1, (n_total + PAGE - 1) // PAGE)
    if st.session_state.pg >= n_pages:
        st.session_state.pg = 0

    with p_ctrl1:
        if st.button("⬅ Prev", key="btn_prev", use_container_width=True) and st.session_state.pg > 0:
            st.session_state.pg -= 1
            st.rerun()
    with p_ctrl2:
        st.markdown(
            f"<div style='text-align:center;color:#7b8ab8;font-size:.85rem;'>"
            f"Hal <b style='color:white'>{st.session_state.pg+1}</b> / <b style='color:white'>{n_pages}</b>"
            f" &nbsp;|&nbsp; {n_total:,} data total</div>",
            unsafe_allow_html=True
        )
    with p_ctrl3:
        if st.button("Next ➡", key="btn_next", use_container_width=True) and st.session_state.pg < n_pages - 1:
            st.session_state.pg += 1
            st.rerun()

    start = st.session_state.pg * PAGE
    page_df = dt.iloc[start:start + PAGE]

    dth_title = f"Data Pengaduan 2025 &mdash; {scope_label}"
    dth_subtitle = f"{start+1}&ndash;{min(start+PAGE, n_total)} dari {format(n_total, ',')}"

    st.markdown(f"""
    <div class="dtw" style="margin-bottom:8px;">
      <div class="dth">
        <span class="dth-title">📋 {dth_title}</span>
        <span style="color:#7b8ab8;font-size:.75rem;">{dth_subtitle}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if page_df.empty:
        st.info("ℹ️ Tidak ada data yang sesuai dengan filter pencarian.")
    else:
        col_w = [0.6, 2.0, 1.2, 0.9, 1.1, 2.2, 1.1, 1.0, 0.7, 1.3]

        # Table Header
        th_cols = st.columns(col_w, vertical_alignment="center")
        th_cols[0].markdown('<div class="th-cell">#</div>', unsafe_allow_html=True)
        th_cols[1].markdown('<div class="th-cell">NAMA PELANGGAN</div>', unsafe_allow_html=True)
        th_cols[2].markdown('<div class="th-cell">CABANG / KEC</div>', unsafe_allow_html=True)
        th_cols[3].markdown('<div class="th-cell">BULAN</div>', unsafe_allow_html=True)
        th_cols[4].markdown('<div class="th-cell">CLUSTER</div>', unsafe_allow_html=True)
        th_cols[5].markdown('<div class="th-cell">RINCIAN</div>', unsafe_allow_html=True)
        th_cols[6].markdown('<div class="th-cell">STATUS</div>', unsafe_allow_html=True)
        th_cols[7].markdown('<div class="th-cell">TGL</div>', unsafe_allow_html=True)
        th_cols[8].markdown('<div class="th-cell">DURASI</div>', unsafe_allow_html=True)
        th_cols[9].markdown('<div class="th-cell" style="text-align:center;">AKSI</div>', unsafe_allow_html=True)

        st.markdown('<div style="height:1px;background:rgba(99,102,241,0.25);margin:4px 0 8px;"></div>', unsafe_allow_html=True)

        # Table Rows
        for _, r in page_df.iterrows():
            rid = int(r["No"])
            tp  = r["Tgl_Pengaduan"].strftime("%d/%m/%Y") if pd.notna(r["Tgl_Pengaduan"]) else "—"
            dur = f"{int(r['Durasi'])}h" if "Durasi" in r.index and pd.notna(r["Durasi"]) else "—"
            nm  = str(r["Nama_Pelanggan"])
            nm_disp = nm[:25] + "…" if len(nm) > 25 else nm
            tl_disp = f"<div class='td-telp'>📞 {r['No_Telp']}</div>" if pd.notna(r.get("No_Telp")) and str(r.get("No_Telp")) not in ("None","nan","") else ""
            rin = str(r["Rincian"]) if pd.notna(r.get("Rincian","")) and str(r.get("Rincian")) not in ("None","nan") else "—"
            rin_disp = rin[:36] + "…" if len(rin) > 36 else rin
            kec = str(r.get("Kec", r.get("Cabang", "—")))

            r_cols = st.columns(col_w, vertical_alignment="center")
            r_cols[0].markdown(f'<div class="td-no">#{rid}</div>', unsafe_allow_html=True)
            r_cols[1].markdown(f'<div class="td-nama" title="{nm}">{nm_disp}{tl_disp}</div>', unsafe_allow_html=True)
            r_cols[2].markdown(f'<div class="td-kec">{kec}</div>', unsafe_allow_html=True)
            r_cols[3].markdown(f'<div class="td-bln">{r["Bulan"]}</div>', unsafe_allow_html=True)
            r_cols[4].markdown(cbadge(r["Cluster"]), unsafe_allow_html=True)
            r_cols[5].markdown(f'<div class="td-rin" title="{rin}">{rin_disp}</div>', unsafe_allow_html=True)
            r_cols[6].markdown(sbadge(r["Status"]), unsafe_allow_html=True)
            r_cols[7].markdown(f'<div class="td-tgl">{tp}</div>', unsafe_allow_html=True)
            r_cols[8].markdown(f'<div class="td-dur">{dur}</div>', unsafe_allow_html=True)

            b_edit, b_del = r_cols[9].columns(2)
            if b_edit.button("✏️", key=f"tbl_btn_edit_{rid}", help=f"Edit pengaduan #{rid} ({nm})"):
                dialog_edit_pengaduan(rid)
            if b_del.button("🗑️", key=f"tbl_btn_del_{rid}", help=f"Hapus pengaduan #{rid} ({nm})"):
                dialog_delete_pengaduan(rid)

            st.markdown('<div style="height:1px;background:rgba(255,255,255,0.04);margin:2px 0;"></div>', unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)
    exp_cols=["No","Cabang","Kec","Bulan","Nama_Pelanggan","No_Sambung","Rincian","Cluster","Status","Tgl_Pengaduan","Tgl_Penyelesaian","Durasi"]
    exp=dt[[c for c in exp_cols if c in dt.columns]]
    st.download_button("⬇️ Export CSV",data=exp.to_csv(index=False).encode("utf-8"),
                       file_name="pengaduan_2025.csv",mime="text/csv")

# Footer 
st.markdown(
    f'<div style="text-align:center;color:#2a3050;font-size:.75rem;padding:20px 0 8px;">'
    f'{logo_img("15px","3px")} PERUMDA Air Minum Tirta Jaya Mandiri &nbsp;|&nbsp; '
    f'Login: <b style="color:#6366f1">{user["username"]}</b> &nbsp;|&nbsp; {scope_label}'
    f'</div>',unsafe_allow_html=True)
