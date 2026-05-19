# Agro Systematic Review Builder

Aplikasi Streamlit untuk membantu peneliti bidang agro, peternakan, pangan, agronomi, perikanan, akuakultur, dan lingkungan menyusun systematic review yang lebih rapi, terintegrasi, dan berbasis kaidah evidence synthesis.

## Versi ini

**Auto-Sync Integrated Workflow + Safe Reset Edition**

Versi ini memperkuat integrasi antarmenu. Isi dari menu sebelumnya menjadi dasar otomatis untuk menu berikutnya. Ketika peneliti mengubah judul, bidang, kerangka PICO/PICOS/PECO, population, intervention/exposure, comparator, outcome, atau study design, sistem dapat langsung memperbarui Protocol, Search Strategy, Screening Score, PRISMA, Quality Assessment, Data Extraction, Evidence Insight Report, dan Export Package.

## Integrasi otomatis antarmenu

Alur integrasi sistem:

1. **Judul & PICOS/PECO** menjadi sumber utama proyek.
2. Sistem otomatis membuat atau memperbarui **Research Question**.
3. Sistem otomatis membentuk **Inclusion Criteria** dan **Exclusion Criteria**.
4. Sistem otomatis menyusun **Search Terms** dan **Boolean Search String**.
5. Search terms otomatis dipakai untuk menghitung **PICOS/PECO Relevance Score** pada artikel.
6. Hasil screening otomatis mengubah angka **PRISMA**.
7. Artikel yang masuk tahap include otomatis muncul di **Quality Assessment** dan **Data Extraction**.
8. Quality Assessment dan Data Extraction otomatis dibaca oleh **Evidence Insight Report**.
9. Semua hasil otomatis masuk ke **Export ZIP**.

Di sidebar tersedia:

- **Auto-sync antarmenu**: mengaktifkan sinkronisasi otomatis.
- **Timpa isi otomatis**: memperbarui ulang research question, criteria, dan search terms dari menu sebelumnya. Matikan opsi ini apabila ingin mempertahankan edit manual.
- **Sinkronkan semua modul**: tombol untuk menyamakan seluruh menu dengan data terbaru.
- **Hapus / reset data project**: tombol aman untuk mengembalikan aplikasi ke kondisi awal. Tombol ini hanya aktif setelah pengguna mencentang konfirmasi dan mengetik kata `RESET`.

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

3. **Protocol & Search Strategy Terintegrasi**
   - Research question mengikuti menu Judul & PICOS/PECO.
   - Kriteria inklusi-eksklusi otomatis menyesuaikan framework, tahun, bahasa, scope, dan study design.
   - Boolean search string otomatis mengikuti population, intervention/exposure, comparator, outcome, dan study design.
   - Tersedia tombol untuk mengambil ulang isi otomatis dari menu sebelumnya.

4. **Import & Screening**
   - Mendukung XLSX, XLS, dan RIS.
   - Normalisasi kolom otomatis.
   - Deteksi duplikasi DOI/judul.
   - Skor relevansi PICOS/PECO otomatis mengikuti Search Strategy aktif.
   - Saran screening otomatis: Include, Maybe, Exclude.

5. **PRISMA & Quality Assessment**
   - Ringkasan PRISMA otomatis berdasarkan screening.
   - Artikel include otomatis masuk ke tabel quality assessment.
   - Checklist quality assessment.
   - Kategori kualitas Low, Moderate, High.

6. **Data Extraction**
   - Artikel include otomatis masuk ke tabel data extraction.
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

9. **Safe Reset Data**
   - Menghapus seluruh data project sementara.
   - Mengembalikan judul, protocol, search terms, artikel, PRISMA, quality assessment, extraction, notes, dan konfigurasi ke tampilan awal.
   - Dilengkapi konfirmasi dua langkah agar tidak terhapus secara tidak sengaja.
   - Disarankan melakukan export ZIP terlebih dahulu sebelum reset jika data masih diperlukan.

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
2. Aktifkan **Auto-sync antarmenu** di sidebar.
3. Isi **Judul & PICOS/PECO**.
4. Simpan dan analisis. Menu Protocol & Search akan otomatis menyesuaikan.
5. Buka **Protocol & Search** untuk mengecek research question, inclusion-exclusion, dan Boolean search.
6. Import artikel dari database memakai XLSX/XLS/RIS.
7. Lakukan screening. PRISMA otomatis berubah.
8. Isi quality assessment dan data extraction untuk artikel include.
9. Buka Insight & Export untuk melihat laporan insight dan mengunduh seluruh hasil.
10. Jika ingin memulai project baru, buka sidebar **Hapus / reset data project**, centang konfirmasi, ketik `RESET`, lalu tekan tombol hapus.

## Catatan penting

Sistem ini membantu standardisasi proses systematic review, tetapi keputusan akademik akhir tetap harus divalidasi peneliti. Sistem tidak menjamin artikel otomatis diterima di jurnal Q1/Q2, tetapi membantu memperkuat kelayakan metodologi, transparansi pelaporan, dan struktur naskah.
