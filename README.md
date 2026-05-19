# Agro Systematic Review Builder

Aplikasi Streamlit untuk membantu penyusunan **systematic review** bidang agro, peternakan, pangan, agronomi, perikanan, dan lingkungan.

## Fitur

- Protocol & PICOS/PECO
- Boolean search string builder
- Import artikel dari CSV, Excel, atau RIS
- Screening judul/abstrak dan full-text
- Deteksi duplikasi berdasarkan DOI dan judul
- PRISMA flow summary
- Quality assessment checklist
- Data extraction table
- Descriptive synthesis chart
- Export CSV, protocol, methods template, dan project config

## Struktur Folder

```text
agro_sysreview_streamlit/
├── app.py
├── requirements.txt
├── README.md
├── .streamlit/
│   └── config.toml
└── data/
    └── sample_articles.csv
```

## Cara Menjalankan di Laptop

1. Buka terminal pada folder project.
2. Install dependency:

```bash
pip install -r requirements.txt
```

3. Jalankan aplikasi:

```bash
streamlit run app.py
```

4. Buka browser sesuai alamat yang muncul, biasanya:

```text
http://localhost:8501
```

## Cara Deploy Online ke Streamlit Community Cloud

1. Buat repository GitHub baru.
2. Upload semua file dalam folder ini ke repository tersebut.
3. Buka Streamlit Community Cloud.
4. Pilih **New app**.
5. Hubungkan repository GitHub.
6. Isi main file path:

```text
app.py
```

7. Klik **Deploy**.

## Format File Artikel yang Disarankan

Gunakan CSV/XLSX dengan kolom berikut:

```text
id,title,authors,year,journal,doi,country,study_design,species_or_crop,intervention,comparator,outcome,abstract,source_database
```

Kolom tidak harus lengkap. Aplikasi akan membuat kolom yang belum ada secara otomatis.

## Catatan Akademik

Aplikasi ini membantu alur kerja systematic review, tetapi keputusan ilmiah tetap harus dilakukan oleh peneliti. Untuk naskah jurnal bereputasi, pastikan bagian metode menjelaskan database, tanggal pencarian, search string, kriteria inklusi-eksklusi, proses screening, quality assessment, dan metode sintesis secara transparan.
