# Panduan Penggunaan AI Insight

Panduan ini membantu peneliti memilih model AI, jenis insight, dan instruksi tambahan agar output AI lebih sesuai untuk systematic review bidang agro, peternakan, perikanan/akuakultur, pangan, lingkungan, serta teknik pertanian dan biosistem.

## 1. Saran memilih model

### Auto pilih model hemat biaya
Gunakan untuk cek cepat, ringkasan awal, novelty sederhana, validasi judul/protocol, dan daftar revisi singkat. Mode ini cocok ketika project masih awal atau data artikel belum banyak.

### Auto pilih model kualitas tinggi
Gunakan untuk draft Discussion, reviewer simulation, novelty-gap yang lebih tajam, manuscript improvement plan, dan analisis mendalam. Mode ini lebih cocok ketika screening, quality assessment, dan data extraction sudah terisi.

### Pilih manual
Gunakan jika model otomatis ditolak provider, muncul pesan deposit/premium, atau ingin mencoba model tertentu. Contoh model ringan/flash: `slashai/gemini-3-flash`, `slashai/deepseek-v4-flash`, `slashai/mimo-v2-flash`, dan `slashai/Step-3.5-Flash`.

## 2. Jenis insight yang tersedia

### Novelty & Gap Insight
Digunakan untuk mencari gap riset, novelty statement, dan arah kontribusi ilmiah. Cocok untuk memperkuat Introduction dan Discussion.

Contoh instruksi tambahan:
- Fokuskan novelty pada bidang agro tropis dan implikasi praktis.
- Bedakan gap metodologis, gap populasi/komoditas, gap outcome, dan gap wilayah penelitian.
- Buatkan 3 alternatif novelty statement untuk akhir Introduction.

### Discussion Draft
Digunakan untuk membuat narasi Discussion awal berdasarkan data project. Cocok jika quality assessment dan data extraction sudah mulai lengkap.

Contoh instruksi tambahan:
- Susun discussion dalam 4 paragraf: pola temuan, penyebab heterogenitas, kualitas bukti, dan implikasi praktis.
- Jangan membuat angka baru; gunakan data project saja.
- Tulis dengan gaya artikel jurnal internasional dalam Bahasa Indonesia formal.

### Reviewer Simulation
Digunakan untuk simulasi komentar reviewer jurnal Q-level sebelum submit.

Contoh instruksi tambahan:
- Berikan major concern, minor concern, dan revisi prioritas.
- Nilai apakah search strategy sudah replikatif dan PRISMA sudah transparan.
- Urutkan risiko dari yang paling mungkin menyebabkan desk rejection.

### Manuscript Improvement Plan
Digunakan untuk membuat rencana perbaikan naskah dari title sampai conclusion.

Contoh instruksi tambahan:
- Pisahkan perbaikan wajib, penting, dan opsional.
- Buat rencana revisi 7 hari kerja.
- Fokuskan pada kesiapan jurnal Scopus Q1/Q2.

### Meta-analysis Advice
Digunakan untuk menilai kesiapan meta-analysis.

Contoh instruksi tambahan:
- Cek outcome mana yang paling siap untuk meta-analysis.
- Sebutkan data mean, SD, n, atau comparator yang belum lengkap.
- Sarankan subgroup analysis berdasarkan dosis, komoditas, durasi, lokasi, atau jenis perlakuan.

## 3. Agar hasil AI sesuai

Lengkapi minimal judul, framework, population, intervention/exposure, comparator, outcome, study design, kriteria inklusi-eksklusi, dan beberapa artikel. Untuk insight yang lebih tajam, lengkapi juga screening, PRISMA, quality assessment, dan data extraction.

Hindari meminta AI membuat sitasi, angka, jumlah artikel, atau kesimpulan yang belum ada di data project. Hasil AI harus tetap divalidasi oleh peneliti dengan artikel asli dan kaidah PRISMA/ROSES.

## 4. Copy-paste manual ke ChatGPT Web tanpa API key

Pada versi terbaru, bagian **Ringkasan dan Prompt Manual** tetap muncul walaupun pengguna tidak mengaktifkan Online AI Mode dan tidak mengisi API key. Peneliti dapat:

1. memilih jenis insight, kedalaman output, dan fokus output;
2. menambahkan instruksi khusus;
3. membuka **Lihat ringkasan data project untuk API / ChatGPT Web**;
4. menyalin **Prompt siap copy ke ChatGPT Web / API**;
5. menempelkan prompt tersebut ke ChatGPT Web atau layanan AI lain secara manual.

Cara ini berguna untuk pengguna yang memiliki akses ChatGPT Web, tetapi tidak memiliki API key atau tidak ingin mengirim data lewat API dari aplikasi Streamlit.
