# Agro & Biosystems Systematic Review Builder

**Q-Level Manuscript Builder + Save & Resume + SlashAI/OpenAI-Compatible Chat Completions + Biosystems Edition**

Aplikasi Streamlit ini dirancang untuk membantu peneliti menyusun systematic review bidang agro, peternakan, teknik pertanian dan biosistem, perikanan/akuakultur, pangan, dan lingkungan secara lebih terarah menuju standar naskah jurnal bereputasi.

## Fitur Utama

### 1. Workflow Terpadu
- Judul & PICOS/PECO menjadi sumber utama.
- Protocol & Search Strategy otomatis mengikuti pilihan sebelumnya.
- Screening otomatis memengaruhi PRISMA, Quality Assessment, Data Extraction, Insight, dan Export.
- Tersedia auto-sync dan tombol sinkronisasi manual.

### 2. Title & Protocol Analyzer
- Analisis kelayakan judul.
- Skor kesiapan judul/protocol.
- Deteksi kelemahan judul.
- Rekomendasi judul yang lebih kuat.
- Generator research question.
- Generator PICOS, PICO, atau PECO.
- Contoh dinamis sesuai bidang dan framework, termasuk Teknik Pertanian dan Biosistem.

### 3. Protocol & Search Strategy
- Inclusion criteria otomatis.
- Exclusion criteria otomatis.
- Search terms otomatis.
- Boolean search strategy otomatis.
- Rekomendasi database berdasarkan bidang, termasuk ASABE Technical Library dan IEEE Xplore untuk topik rekayasa/sensor/IoT bila relevan.

#### Bidang Teknik Pertanian dan Biosistem
Sistem sekarang mendukung topik systematic review seperti smart irrigation, precision agriculture, sensor/IoT pertanian, remote sensing, mekanisasi pertanian, soil compaction akibat lalu lintas mesin, controlled traffic farming, greenhouse technology, postharvest engineering, solar/hybrid dryer, efisiensi energi, dan renewable energy untuk sistem pertanian.

Contoh otomatis tersedia untuk:
- **PICOS**: smart irrigation technologies terhadap water use efficiency dan crop yield;
- **PICO**: solar drying technologies terhadap drying performance dan mutu produk;
- **PECO**: paparan agricultural machinery traffic terhadap soil compaction dan crop performance.

### 4. Import dan Screening Artikel
- Mendukung XLSX, XLS, dan RIS.
- Semua hasil tabel diekspor dalam format XLSX.
- Deteksi duplikasi berdasarkan DOI dan judul.
- Skor relevansi PICOS/PECO otomatis.
- Dual reviewer screening: Reviewer 1, Reviewer 2, conflict, dan consensus.

### 5. PRISMA dan Quality Assessment
- PRISMA flow count otomatis.
- Quality assessment dasar.
- Risk of Bias sederhana: selection, performance, detection, attrition, reporting, dan other bias.
- Overall risk of bias otomatis.
- Certainty of evidence/GRADE sederhana otomatis.

### 6. Data Extraction
- Ekstraksi karakteristik studi.
- Outcome, effect direction, effect size, p-value.
- Kolom meta-analysis: mean, SD, n intervensi/kontrol, outcome unit.
- Key finding, limitation, implication, novelty note.

### 7. Q-Level Manuscript Tools
- PRISMA 2020 Compliance Checker.
- PRISMA-S Search Strategy Audit.
- Risk of Bias & GRADE summary.
- Meta-Analysis Readiness Checker.
- Novelty & Gap Analyzer.
- Journal Targeting Assistant.
- Q-Level Manuscript Builder.
- Cover Letter Template.
- Pre-Submission Reviewer Check.

### 8. Simpan dan Lanjutkan Project
- Setiap langkah menyediakan tombol **Simpan progress** dalam format `.srproj.json`.
- Sidebar menyediakan menu **Simpan & lanjutkan project**.
- Peneliti dapat mengunduh `systematic_review_project_state.srproj.json`, menutup aplikasi, lalu mengunggah file tersebut di lain waktu untuk melanjutkan dari posisi terakhir.
- File project menyimpan judul, PICOS/PECO, protocol, search terms, artikel screening, PRISMA, quality assessment, data extraction, catatan, dan konfigurasi auto-sync.
- Saat memuat project lama, sistem meminta konfirmasi agar project aktif tidak terganti secara tidak sengaja.


### 9. Optional Personal AI Insight + SlashAI Model Selector
- Default sistem tetap **Offline Mode** tanpa API.
- Pengguna dapat mengaktifkan **Online AI Mode** dan memasukkan API Key/Bearer token pribadi secara sementara.
- API key dimasukkan melalui input password di sidebar, sedangkan **API Base URL** dapat diisi sesuai provider. Sistem memakai format `POST https://api.slashai.my.id/v1/chat/completions` dengan header `Authorization: Bearer <your-key>`.
- Untuk kompatibilitas provider SlashAI/OpenAI-compatible, model dikirim pada dua tempat: field body JSON `model` dan header `model: slashai/<nama>`.
- API key dan API Base URL tidak disimpan ke `.srproj.json`, ZIP export, XLSX, DOCX, Markdown, atau kode aplikasi.
- Tersedia tombol **Hapus API key dari sesi ini** yang juga menghapus cache daftar model.
- Tersedia tiga pilihan model:
  - **Auto pilih model hemat biaya**: default memakai `slashai/gemini-3-flash`, lalu mencari model ringan/flash/nano/mini jika daftar model API tersedia.
  - **Auto pilih model kualitas tinggi**: default memakai `slashai/gemini-3.1-pro`, lalu mencoba model kualitas tinggi non-GPT terlebih dahulu. Jika model premium ditolak karena deposit, sistem otomatis mencoba fallback ringan/flash.
  - **Pilih manual**: pengguna memilih dari daftar model API jika endpoint `/v1/models` tersedia. Jika tidak, sistem menampilkan daftar bawaan SlashAI yang sudah dimasukkan ke aplikasi.
- Tombol **Cek model tersedia dari API key** membaca daftar model text-generation dari endpoint `GET https://api.slashai.my.id/v1/models` bila provider mendukung. Jika tidak mendukung, user tetap bisa memilih dari daftar bawaan SlashAI atau mengetik model manual.
- Jika daftar model belum dicek atau gagal dibaca, sistem memakai daftar bawaan SlashAI dan fallback default agar fitur tetap bisa dipakai.

### Catatan koneksi SlashAI `/v1/models`

Beberapa gateway OpenAI-compatible dapat mengembalikan respons `/v1/models` dalam format teks, daftar Markdown, SSE, atau JSON dengan tambahan data sehingga parser JSON standar memunculkan error seperti `Extra data: line 2 column 1`. Versi ini sudah dibuat toleran terhadap kondisi tersebut. Jika `/v1/models` tidak mengembalikan JSON tunggal yang bersih, aplikasi tidak berhenti; sistem otomatis memakai daftar model bawaan SlashAI dan pengguna tetap bisa menjalankan Online AI melalui endpoint `POST /v1/chat/completions`.
- Insight online yang dapat dibuat:
  - Novelty & Gap Insight
  - Discussion Draft
  - Reviewer Simulation
  - Manuscript Improvement Plan
  - Meta-analysis Advice
- Data project hanya dikirim ke API saat pengguna menekan tombol **Buat AI Insight Online**.

### 10. Insight dan Export
- Evidence Insight Report otomatis.
- Descriptive chart untuk tahun, negara, arah efek, dan kualitas.
- Export ZIP berisi:
  - `protocol_systematic_review.md`
  - `methods_template.md`
  - `evidence_insight_report.md`
  - `q_level_manuscript_draft.md`
  - `q_level_manuscript_draft.docx`
  - `cover_letter_template.md`
  - `cover_letter_template.docx`
  - `screening_results.xlsx`
  - `quality_assessment.xlsx`
  - `data_extraction.xlsx`
  - `prisma_counts.xlsx`
  - `prisma_2020_compliance.xlsx`
  - `prisma_s_search_audit.xlsx`
  - `meta_analysis_readiness.xlsx`
  - `novelty_gap_analysis.xlsx`
  - `journal_targeting.xlsx`
  - `reviewer_check.xlsx`
  - `online_ai_*.md` jika pengguna membuat AI insight online
  - `project_state.srproj.json`
  - `project_state_README.txt`

### 11. Safe Reset
- Tombol hapus/reset data project.
- Konfirmasi dua langkah: centang pernyataan dan ketik `RESET`.
- Data tidak akan terhapus tanpa konfirmasi lengkap.

## Cara Menjalankan Lokal

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy ke Streamlit Cloud

1. Upload semua file ke GitHub.
2. Buka Streamlit Community Cloud.
3. Pilih repository.
4. Main file: `app.py`.
5. Deploy.


## Cara Menyimpan dan Melanjutkan Pekerjaan

1. Setelah menyelesaikan langkah tertentu, klik tombol **Simpan progress Langkah ...** di halaman tersebut, atau gunakan sidebar **Simpan & lanjutkan project**.
2. Unduh file `.srproj.json`. File ini adalah snapshot penuh project.
3. Saat ingin melanjutkan, jalankan aplikasi lagi.
4. Buka sidebar **Simpan & lanjutkan project**.
5. Upload file `.srproj.json`.
6. Centang konfirmasi bahwa project aktif akan diganti.
7. Klik **Muat dan lanjutkan project**.

Dengan cara ini, peneliti tidak perlu menyelesaikan systematic review dalam satu sesi. Proses dapat dihentikan pada tahap judul, protocol, screening, quality assessment, extraction, atau manuscript building, lalu dilanjutkan lagi dari file project yang sama.

## Penggunaan API Key Personal dan Pemilihan Model

Untuk aplikasi Streamlit online yang digunakan banyak orang, jangan menanam API key developer di dalam kode. Gunakan alur berikut:

Format request Online AI yang digunakan sistem:

```text
POST https://api.slashai.my.id/v1/chat/completions
Authorization: Bearer <your-key>
Content-Type: application/json
model: slashai/<nama-model>
```

Body utama yang dikirim:

```json
{
  "model": "slashai/gemini-3-flash",
  "messages": [
    {"role": "system", "content": "instruksi sistematis review"},
    {"role": "user", "content": "data project dan tugas insight"}
  ],
  "temperature": 0.2,
  "max_tokens": 2200
}
```

1. Buka sidebar **Online AI Insight (opsional)**.
2. Pilih **Online AI Mode**.
3. Pilih strategi model:
   - **Auto pilih model hemat biaya** untuk penggunaan lebih ekonomis.
   - **Auto pilih model kualitas tinggi** untuk insight yang lebih kuat.
   - **Pilih manual** untuk menentukan model sendiri.
4. Masukkan API Key pribadi/Bearer token pada kolom password dan isi **API Base URL**. Default sudah memakai endpoint SlashAI `https://api.slashai.my.id/v1/chat/completions`. Pengguna boleh mengisi base URL `https://api.slashai.my.id`, `https://api.slashai.my.id/v1`, atau endpoint penuh `https://api.slashai.my.id/v1/chat/completions`; sistem akan menormalkannya otomatis.
5. Klik **Cek model tersedia dari API key** agar sistem mencoba membaca daftar model dari `GET https://api.slashai.my.id/v1/models`. Jika gagal, pilih dari daftar bawaan SlashAI atau tulis model manual.
6. Jika memakai mode manual, pilih model dari daftar atau tulis model secara manual, misalnya `slashai/gemini-3-flash`, `slashai/deepseek-v4-flash`, atau model lain yang tersedia.
7. Buka tab **Online AI Insight** pada Q-Level Tools atau halaman Insight & Export.
8. Pilih jenis insight dan klik **Buat AI Insight Online**.
9. Setelah selesai, klik **Hapus API key dari sesi ini** bila menggunakan perangkat bersama.

Tanpa API key, aplikasi tetap berjalan penuh dengan Offline Mode berbasis rule, checklist, template, dan export dokumen.

API key dan API Base URL bersifat sementara pada sesi Streamlit dan sengaja tidak dimasukkan ke project state maupun export ZIP. Daftar model yang terbaca dari API base/API key juga hanya disimpan pada session state, bukan pada file project.

## Daftar Model Bawaan SlashAI

Aplikasi sudah memuat daftar model bawaan SlashAI sebagai fallback ketika endpoint `GET https://api.slashai.my.id/v1/models` tidak tersedia. Rekomendasi cepat:

- Hemat biaya/cepat: `slashai/gemini-3-flash`, `slashai/deepseek-v4-flash`, `slashai/mimo-v2-flash`, `slashai/Step-3.5-Flash`, `slashai/gpt-5.4-nano`, `slashai/gpt-5-nano`.
- Kualitas tinggi: `slashai/gemini-3.1-pro`, `slashai/deepseek-v4-pro`, `slashai/Qwen3.6-Max-Preview`, `slashai/claude-sonnet-4.7`, lalu GPT premium sebagai opsi jika akun sudah deposit/terbuka aksesnya.
- Manual/coding-review: model Codex dan review tetap tersedia di daftar manual, tetapi untuk insight jurnal systematic review sistem lebih menyarankan model general reasoning/writing.

Lihat file `SLASHAI_AVAILABLE_MODELS.md` untuk daftar lengkap.

## Format Import Artikel

Gunakan file XLSX/XLS dengan kolom yang disarankan:

- id
- title
- authors
- year
- journal
- doi
- country
- study_design
- species_or_crop
- intervention
- comparator
- outcome
- abstract
- source_database

Sistem akan menambahkan kolom screening, reviewer, PRISMA, quality, risk of bias, GRADE, dan extraction secara otomatis.

## Catatan Akademik

Sistem ini membantu menyusun dan mengecek kelengkapan naskah systematic review, tetapi tidak menjamin artikel diterima di jurnal Q1/Q2. Peneliti tetap perlu melakukan validasi manual terhadap:

- kesesuaian scope jurnal target;
- kualitas artikel primer;
- akurasi data extraction;
- pemilihan alat risk of bias;
- keputusan meta-analysis;
- interpretasi hasil;
- author guidelines jurnal target.


## Tambahan Panduan Contoh Riset per Bidang

Paket ini menyertakan file `CONTOH_RISET_PER_BIDANG.md` yang berisi contoh topik systematic review untuk bidang:

- Peternakan
- Agro/Agronomi
- Perikanan/Akuakultur
- Pangan
- Lingkungan
- Teknik Pertanian dan Biosistem

Panduan ini membantu pengguna menentukan framework PICO, PICOS, atau PECO sebelum masuk ke menu Title & Protocol Analyzer.

## Update: Auto-isi contoh saat bidang/kerangka berubah

Versi ini menambahkan logika agar pilihan **Bidang** dan **Kerangka** menjadi pemicu utama pengisian otomatis. Jika pengguna mengubah bidang, misalnya dari Peternakan ke Teknik Pertanian dan Biosistem, sistem dapat langsung menyesuaikan:

- judul contoh;
- Population/Problem;
- Intervention/Exposure;
- Comparator;
- Outcome;
- Study Design;
- Research Question;
- Search Terms;
- Boolean Search Strategy;
- Protocol, Screening Score, Quality Assessment, Data Extraction, Insight, dan Export.

Fitur ini dapat dikendalikan melalui toggle **Otomatis isi contoh sesuai bidang/kerangka** pada Langkah 1 atau **Auto-isi contoh saat bidang berubah** di sidebar. Jika peneliti sudah mengedit manual dan tidak ingin datanya tertimpa contoh, matikan toggle tersebut. Peneliti juga tetap dapat memakai tombol **Terapkan contoh bidang ini sekarang** untuk mengisi ulang contoh kapan saja.

## Perbaikan troubleshooting API key ditolak

Pada versi ini, field API key sudah dibuat lebih toleran. Pengguna boleh menempelkan salah satu format berikut:

```text
sk-xxxx
Bearer sk-xxxx
Authorization: Bearer sk-xxxx
```

Aplikasi akan membersihkan awalan `Bearer` atau `Authorization: Bearer` secara otomatis agar tidak terjadi error `Bearer Bearer ...` pada header request.

Jika muncul error otorisasi 401/403, aplikasi sekarang menampilkan detail yang lebih jelas. Penyebabnya tidak selalu API key dicabut; bisa juga karena model tidak tersedia untuk key tersebut, endpoint/API Base tidak cocok, quota/saldo bermasalah, atau provider menolak model tertentu. Gunakan tombol **Tes Chat Completions** di sidebar untuk menguji kombinasi API Base, model, dan API key secara langsung melalui `POST /v1/chat/completions`.

Rekomendasi pengaturan SlashAI:

```text
API Base URL: https://api.slashai.my.id
Model hemat: slashai/gemini-3-flash
Model kualitas tinggi: slashai/gemini-3.1-pro
```

## Perbaikan: Deteksi error deposit/akses premium SlashAI

Jika provider mengembalikan pesan seperti:

```text
access_denied: Deposit required to unlock pre
```

maka aplikasi tidak lagi menyimpulkan bahwa API key dicabut. Pesan tersebut berarti server menolak request karena akun/API key belum memiliki akses saldo/deposit untuk model yang dipilih, atau model tersebut berada pada kelas premium/pre yang perlu dibuka terlebih dahulu.

Tindakan yang disarankan:

1. cek saldo/deposit/top up pada provider SlashAI;
2. tunggu beberapa detik jika server menyebut waktu reset;
3. gunakan mode **Pilih manual** dan coba model ringan/flash seperti:
   - `slashai/gemini-3-flash`
   - `slashai/deepseek-v4-flash`
   - `slashai/mimo-v2-flash`
4. jika tetap ditolak, gunakan Offline Mode. Semua fitur systematic review tetap berjalan tanpa API.

Pengaturan default hemat biaya pada versi ini diarahkan ke model ringan/flash terlebih dahulu agar mengurangi risiko terkena pembatasan premium.


## Catatan akses/deposit SlashAI

Jika server mengembalikan pesan seperti `Deposit required to unlock premium models`, itu bukan berarti API key salah. Artinya model yang dipilih membutuhkan saldo/deposit atau akses premium di provider. Sistem versi ini akan mencoba fallback otomatis ke model ringan/flash pada mode otomatis. Untuk menghindari error berulang, gunakan mode manual dan pilih salah satu model ringan berikut:

- `slashai/gemini-3-flash`
- `slashai/deepseek-v4-flash`
- `slashai/mimo-v2-flash`
- `slashai/Step-3.5-Flash`

API key tetap tidak disimpan ke project state, export ZIP, XLSX, DOCX, atau Markdown.


## Panduan AI Insight agar hasil lebih sesuai

Versi ini menambahkan panduan di menu **Online AI Insight** agar peneliti tahu kapan memakai model hemat biaya, model kualitas tinggi, atau model manual. Pada setiap jenis insight, sistem juga menampilkan:

- tujuan insight;
- data yang sebaiknya sudah dilengkapi;
- contoh instruksi tambahan;
- ciri output yang baik;
- pilihan kedalaman output: Ringkas, Standar, Mendalam;
- fokus output, misalnya kesiapan jurnal Q-level, novelty-gap, PRISMA/ROSES, discussion, meta-analysis, atau reviewer simulation.

File pendukung: `AI_USAGE_GUIDE.md`. Saat export ZIP dari aplikasi, panduan ini juga tersedia sebagai `ai_usage_guide.md`.

Contoh instruksi tambahan yang bisa dimasukkan user:

```text
Fokuskan pada bidang Teknik Pertanian dan Biosistem. Buat output untuk target jurnal Q2. Jangan membuat sitasi baru. Beri rekomendasi perbaikan metode PRISMA, quality assessment, dan discussion secara praktis.
```
