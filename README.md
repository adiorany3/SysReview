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
- API key dimasukkan melalui input password di sidebar, sedangkan **API Base URL** dapat diisi sesuai provider. Sistem memakai format `POST {api-base}/v1/chat/completions` dengan header `Authorization: Bearer <your-key>`.
- Untuk kompatibilitas provider SlashAI/OpenAI-compatible, model dikirim pada dua tempat: field body JSON `model` dan header `model: slashai/<nama>`.
- API key dan API Base URL tidak disimpan ke `.srproj.json`, ZIP export, XLSX, DOCX, Markdown, atau kode aplikasi.
- Tersedia tombol **Hapus API key dari sesi ini** yang juga menghapus cache daftar model.
- Tersedia tiga pilihan model:
  - **Auto pilih model hemat biaya**: default memakai `slashai/gpt-5.5-instant`, lalu mencari model ringan/mini/nano/flash jika daftar model API tersedia.
  - **Auto pilih model kualitas tinggi**: default memakai `slashai/gpt-5.5`, lalu mencari model kualitas tinggi seperti `slashai/gpt-5.4-pro`, Claude Sonnet/Opus terbaru, Gemini Pro, atau model pro lain jika tersedia.
  - **Pilih manual**: pengguna memilih dari daftar model API jika endpoint `/v1/models` tersedia. Jika tidak, sistem menampilkan daftar bawaan SlashAI yang sudah dimasukkan ke aplikasi.
- Tombol **Cek model tersedia dari API key** membaca daftar model text-generation dari endpoint `GET {api-base}/v1/models` bila provider mendukung. Jika tidak mendukung, user tetap bisa memilih dari daftar bawaan SlashAI atau mengetik model manual.
- Jika daftar model belum dicek atau gagal dibaca, sistem memakai daftar bawaan SlashAI dan fallback default agar fitur tetap bisa dipakai.
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
POST {api-base}/v1/chat/completions
Authorization: Bearer <your-key>
Content-Type: application/json
model: slashai/<nama-model>
```

Body utama yang dikirim:

```json
{
  "model": "slashai/gpt-5.5-instant",
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
4. Masukkan API Key pribadi/Bearer token pada kolom password dan isi **API Base URL**. Untuk SlashAI/OpenAI-compatible provider, isi base URL tanpa endpoint akhir, misalnya `https://api-base`. Jika tidak sengaja menempelkan endpoint penuh `{api-base}/v1/chat/completions`, sistem akan menormalkannya otomatis.
5. Klik **Cek model tersedia dari API key** agar sistem mencoba membaca daftar model dari `GET {api-base}/v1/models`. Jika gagal, pilih dari daftar bawaan SlashAI atau tulis model manual.
6. Jika memakai mode manual, pilih model dari daftar atau tulis model secara manual, misalnya `slashai/gpt-5.5`, `slashai/gpt-5.5-instant`, atau `slashai/claude-sonnet-4.7`.
7. Buka tab **Online AI Insight** pada Q-Level Tools atau halaman Insight & Export.
8. Pilih jenis insight dan klik **Buat AI Insight Online**.
9. Setelah selesai, klik **Hapus API key dari sesi ini** bila menggunakan perangkat bersama.

Tanpa API key, aplikasi tetap berjalan penuh dengan Offline Mode berbasis rule, checklist, template, dan export dokumen.

API key dan API Base URL bersifat sementara pada sesi Streamlit dan sengaja tidak dimasukkan ke project state maupun export ZIP. Daftar model yang terbaca dari API base/API key juga hanya disimpan pada session state, bukan pada file project.

## Daftar Model Bawaan SlashAI

Aplikasi sudah memuat daftar model bawaan SlashAI sebagai fallback ketika endpoint `GET {api-base}/v1/models` tidak tersedia. Rekomendasi cepat:

- Hemat biaya/cepat: `slashai/gpt-5.5-instant`, `slashai/gpt-5.4-nano`, `slashai/gpt-5.4-mini`, `slashai/claude-haiku-4.5`, `slashai/gemini-3-flash`, `slashai/deepseek-v4-flash`.
- Kualitas tinggi: `slashai/gpt-5.5`, `slashai/gpt-5.4-pro`, `slashai/claude-sonnet-4.7`, `slashai/claude-opus-4.7`, `slashai/gemini-3.1-pro`, `slashai/deepseek-v4-pro`.
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
