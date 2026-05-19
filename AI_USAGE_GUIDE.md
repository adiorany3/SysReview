# AI Usage Guide

## Status AI

AI pada versi ini sudah menjadi bagian dari sistem. Aplikasi membaca konfigurasi dari:

1. `.streamlit/secrets.toml` untuk penggunaan lokal.
2. Streamlit Cloud Secrets untuk deployment online.
3. Input API sementara di sidebar hanya sebagai fallback jika TOML belum diisi.

## Alur kerja AI

1. Lengkapi judul dan PICOS/PICO/PECO.
2. Generate protocol dan search strategy.
3. Import artikel dan lakukan screening.
4. Isi quality assessment dan data extraction.
5. Buka menu **AI Insight**.
6. Pilih jenis insight, misalnya Novelty & Gap Insight atau Discussion Draft.
7. Klik **Buat AI Insight Online**.

## Prinsip penggunaan

- AI tidak boleh membuat angka, sitasi, atau data baru yang tidak ada di project.
- AI hanya membantu diagnosis, gap, novelty, discussion, reviewer simulation, dan improvement plan.
- Semua kesimpulan akhir tetap perlu diverifikasi oleh peneliti.
