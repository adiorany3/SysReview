# Agro & Biosystems Systematic Review Builder

Versi ini sudah memasukkan **AI ke dalam sistem** dan membaca API dari **TOML/Streamlit Secrets**.

## Fitur utama

- Workflow terpadu systematic review: judul, PICOS/PICO/PECO, protocol, search strategy, import artikel, screening, PRISMA, quality assessment, data extraction, AI insight, dan export.
- Dukungan bidang agro, peternakan, akuakultur, pangan, lingkungan, serta teknik pertanian dan biosistem.
- Import artikel dari XLSX, XLS, CSV, dan RIS.
- Semua output tabel utama dapat diekspor ke XLSX.
- AI Insight sudah include di sistem: API key dibaca otomatis dari `.streamlit/secrets.toml` atau Streamlit Cloud Secrets.
- Export ZIP project berisi project state, protocol, prompt AI, dan tabel XLSX.
- Tombol reset memakai konfirmasi agar data tidak terhapus tidak sengaja.

## Cara menjalankan lokal

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Konfigurasi API lewat TOML

Edit file berikut:

```text
.streamlit/secrets.toml
```

Isi API key:

```toml
[ai]
enabled = true
api_base_url = "https://api.slashai.my.id"
api_key = "ISI_API_KEY_ANDA"
default_model = "slashai/gemini-3-flash"
high_quality_model = "slashai/gemini-3.1-pro"
```

Aplikasi akan otomatis membaca API dari TOML. User tidak perlu lagi memasukkan API key setiap kali membuka sistem.

## Deploy ke Streamlit Cloud

Jangan upload API key asli ke GitHub. Masukkan secrets melalui:

`App settings` → `Secrets`

Lalu tempel konfigurasi TOML yang sama.

## Catatan keamanan

- `.streamlit/secrets.toml` sudah dimasukkan ke `.gitignore`.
- File `.streamlit/secrets.example.toml` aman untuk GitHub karena hanya berisi placeholder.
- Project export tidak menyimpan API key.
