-- ============================================================
-- PDAM Tirta Jaya Mandiri — Database Setup
-- Jalankan sekali: mysql -u root -p < init_db.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS pdam_pengaduan
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE pdam_pengaduan;

-- ────────────────────────────────────────────────────────────
-- Tabel users (login)
-- role: 'pusat' bisa lihat & CRUD semua cabang
--       'cabang' hanya bisa CRUD data cabangnya sendiri
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  username      VARCHAR(60)  NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,       -- bcrypt hash
  nama_lengkap  VARCHAR(120) NOT NULL,
  role          ENUM('pusat','cabang') NOT NULL DEFAULT 'cabang',
  cabang        VARCHAR(80)  NULL,           -- NULL jika pusat
  aktif         TINYINT(1)   NOT NULL DEFAULT 1,
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ────────────────────────────────────────────────────────────
-- Tabel pengaduan (CRUD utama)
-- ────────────────────────────────────────────────────────────
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
  created_by            VARCHAR(60)  NULL,
  created_at            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at            DATETIME     NULL ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Index untuk query yang sering
CREATE INDEX idx_cabang   ON pengaduan (cabang);
CREATE INDEX idx_bulan    ON pengaduan (bulan_num);
CREATE INDEX idx_cluster  ON pengaduan (cluster);
CREATE INDEX idx_status   ON pengaduan (status);

-- ────────────────────────────────────────────────────────────
-- Seed users
-- Password default semua: Pdam@2025
-- Hash di-generate dengan: python3 -c "import bcrypt; print(bcrypt.hashpw(b'Pdam@2025', bcrypt.gensalt()).decode())"
-- GANTI hash di bawah dengan hasil generate di server Anda!
-- ────────────────────────────────────────────────────────────

-- Akun PUSAT (bisa akses semua data)
INSERT INTO users (username, password_hash, nama_lengkap, role, cabang) VALUES
('pusat',         '$2b$12$PLACEHOLDER_HASH_PUSAT___________.', 'Admin Pusat PDAM',          'pusat', NULL);

-- Akun 20 CABANG
INSERT INTO users (username, password_hash, nama_lengkap, role, cabang) VALUES
('cb_cibadak',    '$2b$12$PLACEHOLDER_HASH__________________.', 'Operator Cibadak/Caringin', 'cabang', 'CIBADAK/CARINGIN'),
('cb_citarik',    '$2b$12$PLACEHOLDER_HASH__________________.', 'Operator Citarik',          'cabang', 'CITARIK'),
('cb_kabandungan','$2b$12$PLACEHOLDER_HASH__________________.', 'Operator Kabandungan',      'cabang', 'KABANDUNGAN'),
('cb_cidahu',     '$2b$12$PLACEHOLDER_HASH__________________.', 'Operator Cidahu',           'cabang', 'CIDAHU'),
('cb_jampangkulon','$2b$12$PLACEHOLDER_HASH_________________.', 'Operator Jampangkulon',     'cabang', 'JAMPANGKULON'),
('cb_bojonggenteng','$2b$12$PLACEHOLDER_HASH________________.', 'Operator Bojonggenteng',    'cabang', 'BOJONGGENTENG'),
('cb_bojonglopang','$2b$12$PLACEHOLDER_HASH_________________.', 'Operator Bojonglopang',     'cabang', 'BOJONGLOPANG'),
('cb_parakansalak','$2b$12$PLACEHOLDER_HASH_________________.', 'Operator Parakansalak',     'cabang', 'PARAKANSALAK'),
('cb_cikembar',   '$2b$12$PLACEHOLDER_HASH__________________.', 'Operator Cikembar',         'cabang', 'CIKEMBAR'),
('cb_purabaya',   '$2b$12$PLACEHOLDER_HASH__________________.', 'Operator Purabaya',         'cabang', 'PURABAYA'),
('cb_pelabuhanratu','$2b$12$PLACEHOLDER_HASH________________.', 'Operator Pelabuhanratu',    'cabang', 'PELABUHANRATU'),
('cb_nagrak',     '$2b$12$PLACEHOLDER_HASH__________________.', 'Operator Nagrak',           'cabang', 'NAGRAK'),
('cb_ciambar',    '$2b$12$PLACEHOLDER_HASH__________________.', 'Operator Ciambar',          'cabang', 'CIAMBAR'),
('cb_parungkuda', '$2b$12$PLACEHOLDER_HASH__________________.', 'Operator Parungkuda',       'cabang', 'PARUNGKUDA'),
('cb_jampangtengah','$2b$12$PLACEHOLDER_HASH________________.', 'Operator Jampang Tengah',   'cabang', 'JAMPANG TENGAH'),
('cb_cisaat',     '$2b$12$PLACEHOLDER_HASH__________________.', 'Operator Cisaat',           'cabang', 'UNIT CISAAT'),
('cb_sukalarang', '$2b$12$PLACEHOLDER_HASH__________________.', 'Operator Sukalarang',       'cabang', 'SUKALARANG'),
('cb_cisolok',    '$2b$12$PLACEHOLDER_HASH__________________.', 'Operator Cisolok',          'cabang', 'CISOLOK'),
('cb_cicurug',    '$2b$12$PLACEHOLDER_HASH__________________.', 'Operator Cicurug',          'cabang', 'CICURUG'),
('cb_kalapanunggal','$2b$12$PLACEHOLDER_HASH________________.', 'Operator Kalapanunggal',    'cabang', 'KALAPANUNGGAL');
