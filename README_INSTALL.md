# SysReview - System AI via TOML

Versi ini sudah mengubah konfigurasi AI agar menjadi bagian dari sistem. API tidak lagi wajib diinput dari sidebar karena aplikasi membaca API dari `.streamlit/secrets.toml` atau Streamlit Cloud Secrets.

## Lokal

1. Buka `.streamlit/secrets.toml`.
2. Ganti `ISI_API_KEY_KAMU_DI_SINI` dengan API key asli.
3. Install dependency:

```bash
pip install -r requirements.txt
```

4. Jalankan aplikasi:

```bash
streamlit run app.py
```

## Streamlit Cloud

Jangan upload API key asli ke GitHub. Masukkan konfigurasi berikut di menu **App settings -> Secrets**:

```toml
[ai]
enabled = true
api_base_url = "https://api.slashai.my.id"
api_key = "ISI_API_KEY_KAMU"
default_model = "slashai/gemini-3-flash"
high_quality_model = "slashai/gemini-3.1-pro"
```

## Catatan keamanan

- `.streamlit/secrets.toml` sudah dimasukkan ke `.gitignore`.
- API key tidak ditampilkan di UI.
- API key tidak ikut tersimpan ke export project, ZIP hasil kerja, XLSX, DOCX, atau Markdown.
