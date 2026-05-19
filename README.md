# Agro Systematic Review Builder

Aplikasi Streamlit untuk membantu peneliti bidang agro, peternakan, pangan, agronomi, perikanan, akuakultur, dan lingkungan menyusun systematic review yang lebih rapi, terintegrasi, dan berbasis kaidah evidence synthesis.

## Versi ini

**Enhanced Examples & Guidance Edition**

Versi ini menambahkan contoh dan informasi otomatis sesuai pilihan pengguna. Ketika peneliti memilih bidang dan kerangka PICO/PICOS/PECO, sistem menampilkan contoh judul, komponen review, research question, keyword, Boolean search, database, quality assessment, dan insight naskah yang sesuai.

## Fitur utama

1. **Judul & PICOS/PECO Analyzer**
   - Analisis kelayakan judul otomatis.
   - Skor kesiapan menuju target Q-level.
   - Deteksi kelemahan judul.
   - Rekomendasi judul dan research question.
   - Contoh dinamis berdasarkan bidang dan framework.

2. **Contoh dan Informasi Sesuai Pilihan**
   - Penjelasan PICO, PICOS, dan PECO.
   - Contoh topik untuk peternakan, agro/agronomi, perikanan/akuakultur, pangan, dan lingkungan.
   - Contoh komponen Population, Intervention/Exposure, Comparator, Outcome, dan Study Design.
   - Contoh Boolean search dan keyword.
   - Insight kelemahan, kekuatan, serta catatan untuk target Q1/Q2, Q2/Q3, Scopus awal, dan Sinta/Kampus.

3. **Protocol & Search Strategy**
   - Kriteria inklusi-eksklusi.
   - Boolean search string otomatis.
   - Rekomendasi database dan quality assessment sesuai bidang.

4. **Import & Screening**
   - Mendukung XLSX, XLS, dan RIS.
   - Normalisasi kolom otomatis.
   - Deteksi duplikasi DOI/judul.
   - Skor relevansi PICOS/PECO.
   - Saran screening otomatis: Include, Maybe, Exclude.

5. **PRISMA & Quality Assessment**
   - Ringkasan PRISMA otomatis berdasarkan screening.
   - Checklist quality assessment.
   - Kategori kualitas Low, Moderate, High.

6. **Data Extraction**
   - Ekstraksi outcome, effect direction, effect size, p-value, finding, limitation, dan implication.

7. **Evidence Insight Report**
   - Insight otomatis dari hasil judul, screening, PRISMA, quality assessment, dan data extraction.
   - Kekuatan bukti sementara.
   - Kesiapan meta-analysis.
   - Gap riset otomatis.
   - Rekomendasi tindak lanjut untuk naskah.

8. **Export Package**
   - Protocol markdown.
   - Methods template.
   - Insight report.
   - Examples and guidance markdown.
   - Screening XLSX.
   - PRISMA counts XLSX.
   - Quality assessment XLSX.
   - Data extraction XLSX.
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
3. Baca contoh dan informasi sesuai pilihan bidang/framework.
4. Terapkan contoh apabila ingin memakai template awal.
5. Rapikan **Protocol & Search**.
6. Import artikel dari database memakai XLSX/XLS/RIS.
7. Lakukan screening.
8. Pantau PRISMA dan isi quality assessment.
9. Isi data extraction.
10. Buka Insight & Export untuk melihat laporan insight dan mengunduh seluruh hasil.

## Catatan penting

Sistem ini membantu standardisasi proses systematic review, tetapi keputusan akademik akhir tetap harus divalidasi peneliti. Sistem tidak menjamin artikel otomatis diterima di jurnal Q1/Q2, tetapi membantu memperkuat kelayakan metodologi, transparansi pelaporan, dan struktur naskah.
