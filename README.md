# Agro Systematic Review Builder

Aplikasi Streamlit untuk membantu peneliti bidang agro, peternakan, pangan, agronomi, perikanan, akuakultur, dan lingkungan menyusun systematic review yang lebih rapi, terintegrasi, dan berbasis kaidah evidence synthesis.

## Fitur utama

1. **Judul & PICOS/PECO Analyzer**
   - Analisis kelayakan judul otomatis.
   - Skor kesiapan menuju target Q-level.
   - Deteksi kelemahan judul.
   - Rekomendasi judul dan research question.

2. **Protocol & Search Strategy**
   - Kriteria inklusi-eksklusi.
   - Boolean search string otomatis.
   - Rekomendasi database dan quality assessment sesuai bidang.

3. **Import & Screening**
   - Mendukung CSV, XLSX, dan RIS.
   - Normalisasi kolom otomatis.
   - Deteksi duplikasi DOI/judul.
   - Skor relevansi PICOS/PECO.
   - Saran screening otomatis: Include, Maybe, Exclude.

4. **PRISMA & Quality Assessment**
   - Ringkasan PRISMA otomatis berdasarkan screening.
   - Checklist quality assessment.
   - Kategori kualitas Low, Moderate, High.

5. **Data Extraction**
   - Ekstraksi outcome, effect direction, effect size, p-value, finding, limitation, dan implication.

6. **Evidence Insight Report**
   - Insight otomatis dari hasil judul, screening, PRISMA, quality assessment, dan data extraction.
   - Kekuatan bukti sementara.
   - Kesiapan meta-analysis.
   - Gap riset otomatis.
   - Rekomendasi tindak lanjut untuk naskah.

7. **Export Package**
   - Protocol markdown.
   - Methods template.
   - Insight report.
   - Screening CSV.
   - Quality CSV.
   - Extraction CSV.
   - Project state JSON.
   - Semua hasil bisa diekspor sebagai ZIP dari aplikasi.

## Cara menjalankan lokal

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Cara deploy online di Streamlit Community Cloud

1. Upload semua file ke repository GitHub.
2. Buka Streamlit Community Cloud.
3. Pilih repository.
4. Main file path: `app.py`.
5. Deploy.

## Workflow penggunaan

1. Buka **Panduan Workflow**.
2. Isi **Judul & PICOS/PECO**.
3. Rapikan **Protocol & Search**.
4. Import artikel dari database.
5. Lakukan screening.
6. Pantau PRISMA dan isi quality assessment.
7. Isi data extraction.
8. Buka Insight & Export untuk melihat laporan insight dan mengunduh seluruh hasil.

## Catatan penting

Sistem ini membantu standardisasi proses systematic review, tetapi keputusan akademik akhir tetap harus divalidasi peneliti. Sistem tidak menjamin artikel otomatis diterima di jurnal Q1/Q2, tetapi membantu memperkuat kelayakan metodologi, transparansi pelaporan, dan struktur naskah.
