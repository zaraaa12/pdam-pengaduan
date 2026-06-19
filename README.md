# 💧 Dashboard Pengaduan PDAM Tirta Jaya Mandiri

Dashboard interaktif berbasis **Streamlit** untuk memvisualisasikan rekap pengaduan pelanggan PDAM Tirta Jaya Mandiri Kabupaten Sukabumi.

---

## 📁 Struktur Folder

```
dashboard_pengaduan/
├── app.py                                          # Aplikasi Streamlit utama
├── requirements.txt                                # Dependencies Python
├── README.md                                       # Panduan ini
└── data/
    └── REKAP_PENGADUAN_PELANGGAN_2025_update.xlsx  # File data (letakkan di sini)
```

---

## 🚀 Cara Menjalankan (Lokal)

### 1. Clone / download folder ini

### 2. Buat virtual environment (opsional tapi disarankan)
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Letakkan file Excel ke folder `data/`
```
dashboard_pengaduan/
└── data/
    └── REKAP_PENGADUAN_PELANGGAN_2025_update.xlsx
```

### 5. Jalankan aplikasi
```bash
streamlit run app.py
```

Buka browser ke: **http://localhost:8501**

---

## ☁️ Deploy ke Streamlit Cloud (Gratis)

### 1. Buat akun di https://streamlit.io

### 2. Push project ke GitHub
```bash
git init
git add .
git commit -m "Initial dashboard"
git branch -M main
git remote add origin https://github.com/username/dashboard-pdam.git
git push -u origin main
```

> **Catatan**: File `.xlsx` sebaiknya di-commit juga, atau gunakan `st.secrets` + Google Drive/S3 untuk data produksi.

### 3. Di Streamlit Cloud:
- Klik **"New app"**
- Pilih repo GitHub Anda
- Set **Main file path**: `app.py`
- Klik **Deploy**

---

## 📊 Fitur Dashboard

| Fitur | Keterangan |
|-------|------------|
| **KPI Cards** | Total pengaduan, breakdown per cluster, rata-rata durasi penyelesaian |
| **Donut Chart** | Proporsi 3 cluster pengaduan |
| **Bar Chart Bulanan** | Tren pengaduan per bulan per cluster |
| **Geo Map** | Peta sebaran pengaduan seluruh wilayah Kab. Sukabumi (bubble size = volume) |
| **Bar Cabang** | Ranking cabang berdasarkan jumlah pengaduan |
| **Detail Jenis** | Breakdown 5 jenis pengaduan spesifik |
| **Heatmap** | Bulan × Cluster untuk identifikasi pola musiman |
| **Histogram Durasi** | Distribusi lama penyelesaian per cluster |
| **Data Table** | Tabel detail pengaduan dengan filter |

---

## 🏷️ Kluster Pengaduan

| Cluster | Jenis Pengaduan |
|---------|----------------|
| 🔧 **TEKNIS** | Kebocoran Pipa Dinas, Kebocoran Instalatur, Supply Air |
| 💰 **REKENING AIR** | Pembayaran Melonjak |
| 🔩 **PELAYANAN** | Water Meter Rusak/Mati |

---

## ⚙️ Filter Tersedia (Sidebar)
- **Tahun** – Pilih tahun data
- **Bulan** – Filter satu atau beberapa bulan
- **Cabang** – Filter per cabang/kecamatan
- **Cluster** – Filter per kategori pengaduan

---

## 🔧 Troubleshooting

**File tidak ditemukan**: Pastikan file `.xlsx` ada di folder `data/` relatif terhadap `app.py`.

**Map tidak muncul**: Streamlit Cloud mendukung `plotly` mapbox dengan `carto-positron` tanpa token API.

**Data kosong**: Pastikan sheet `REKAP SMUA CABANG` ada di file Excel dan formatnya sesuai.
