# Integrated Agro Systematic Review Builder

Aplikasi Streamlit untuk membantu peneliti menyusun systematic review bidang agro, peternakan, agronomi, pangan, perikanan, dan lingkungan secara terpadu.

## Perubahan versi terintegrasi

Versi ini sudah dirapikan agar setiap bagian tidak berjalan sendiri-sendiri. Alur data dibuat terpadu dari awal sampai akhir:

1. **Title & Protocol Analyzer**
   - Menganalisis kelayakan judul.
   - Membuat skor kesiapan Q-level.
   - Membuat PICOS/PECO, research question, Boolean search, rekomendasi database, quality tool, dan draft protocol.
   - Hasilnya otomatis mengisi modul protocol, search strategy, dan screening relevance.

2. **Protocol & PICOS**
   - Menjadi pusat data review.
   - Jika PICOS/PECO diubah, search terms dan scoring artikel dapat diperbarui otomatis.

3. **Search Strategy**
   - Boolean search dibangun dari data protocol.
   - Search terms yang disimpan akan menghitung ulang relevansi artikel yang sudah diimpor.
   - Database final akan masuk ke protocol dan draft methods.

4. **Import & Screening**
   - File CSV/XLSX/RIS otomatis dinormalisasi.
   - Sistem mendeteksi duplikasi.
   - Artikel diberi PICOS relevance score.
   - Keputusan screening dapat dibantu dengan saran otomatis.

5. **PRISMA Flow**
   - Jumlah PRISMA otomatis ditarik dari hasil screening.
   - Mode manual tetap tersedia bila peneliti memiliki data dari sumber tambahan.

6. **Quality Assessment**
   - Hanya menampilkan artikel yang sudah masuk kategori Include.
   - Terhubung dengan hasil screening/full-text.

7. **Data Extraction**
   - Hanya menampilkan artikel Include.
   - Data awal seperti judul, komoditas/spesies, intervensi, pembanding, dan outcome ditarik dari tabel screening.

8. **Synthesis & Export**
   - Menarik semua data dari protocol, PRISMA, screening, quality assessment, dan data extraction.
   - Dapat mengekspor protocol, methods template, synthesis summary, CSV, JSON, dan paket ZIP output.

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
