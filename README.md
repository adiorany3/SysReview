# Agro Systematic Review Builder

**Q-Level Manuscript Builder + Compliance Checker Edition**

Aplikasi Streamlit ini dirancang untuk membantu peneliti menyusun systematic review bidang agro, peternakan, perikanan/akuakultur, pangan, dan lingkungan secara lebih terarah menuju standar naskah jurnal bereputasi.

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
- Contoh dinamis sesuai bidang dan framework.

### 3. Protocol & Search Strategy
- Inclusion criteria otomatis.
- Exclusion criteria otomatis.
- Search terms otomatis.
- Boolean search strategy otomatis.
- Rekomendasi database berdasarkan bidang.

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

### 8. Insight dan Export
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
  - `project_state.json`

### 9. Safe Reset
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

