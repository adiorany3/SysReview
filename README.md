# Guided Agro Systematic Review Builder

Aplikasi Streamlit untuk membantu peneliti menyusun systematic review bidang agro, peternakan, agronomi, pangan, perikanan, akuakultur, dan lingkungan dengan workflow yang lebih mudah diikuti.

## Perubahan versi 2.1 guided workflow

Versi ini menyusun ulang sistem menjadi **alur langkah berurutan**. Setiap halaman sekarang memiliki keterangan:

- tujuan langkah;
- input yang harus disiapkan;
- output yang dihasilkan;
- tindakan lanjut sebelum pindah ke langkah berikutnya;
- status apakah langkah tersebut sudah aktif/lengkap.

Menu utama tidak lagi berupa modul terpisah, tetapi menjadi urutan kerja:

1. **Analisis Judul & Topik**
   - Menilai kelayakan judul.
   - Membuat skor kesiapan menuju target Q-level.
   - Mendeteksi kelemahan judul.
   - Menyusun rekomendasi judul, research question, PICOS/PECO, Boolean search awal, database, quality tool, dan draft protocol.

2. **Susun Protocol & PICOS**
   - Mengunci judul final, research question, PICOS/PECO, rentang tahun, kriteria inklusi, dan kriteria eksklusi.
   - Menjadi pusat data untuk seluruh proses review.

3. **Bangun Search Strategy**
   - Menyusun Boolean search dari protocol.
   - Menentukan database final.
   - Membuat search log template agar pencarian artikel terdokumentasi.

4. **Import Artikel & Screening**
   - Mengimpor file CSV/XLSX/RIS.
   - Menormalkan kolom bibliografi.
   - Mendeteksi duplikasi.
   - Memberi skor relevansi PICOS/PECO.
   - Membantu keputusan Include/Maybe/Exclude.

5. **Cek PRISMA Flow**
   - Mengambil angka PRISMA secara otomatis dari data screening.
   - Menampilkan identification, screening, eligibility, dan included.
   - Menyediakan mode manual bila peneliti memiliki data tambahan dari sumber lain.

6. **Nilai Kualitas Studi**
   - Hanya menampilkan artikel yang sudah included.
   - Menghasilkan quality score, quality category, dan catatan kualitas metodologi.

7. **Ekstraksi Data**
   - Mengambil data utama dari artikel included.
   - Mencatat desain studi, sampel, durasi, intervensi, outcome, effect direction, effect size, p-value, dan key finding.

8. **Sintesis & Export Naskah**
   - Menggabungkan protocol, PRISMA, screening, quality assessment, dan data extraction.
   - Mengekspor protocol, methods template, synthesis summary, CSV, project JSON, dan paket ZIP output.

## Cara menjalankan lokal

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy online dengan Streamlit Community Cloud

1. Upload folder ini ke GitHub.
2. Buka Streamlit Community Cloud.
3. Pilih repository.
4. Main file: `app.py`.
5. Deploy.

## Format file bibliografi yang didukung

- CSV
- XLSX/XLS
- RIS

Kolom ideal untuk data artikel:

```text
title, authors, year, journal, doi, abstract, country, study_design, species_or_crop, intervention, comparator, outcome, source_database
```

Kolom lain tetap dapat diimpor, tetapi sistem akan mencoba menyesuaikan nama kolom utama secara otomatis.

## Catatan penggunaan

Sistem ini membantu penyusunan systematic review agar lebih rapi dan sesuai alur PRISMA/PICOS/PECO, tetapi validasi ilmiah akhir tetap perlu dilakukan oleh peneliti. Sistem tidak menjamin artikel pasti diterima di jurnal Q-level, namun membantu menyiapkan struktur, transparansi metode, dan evidence synthesis yang lebih kuat.
