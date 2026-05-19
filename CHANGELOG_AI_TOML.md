# Perubahan AI + TOML

Perubahan utama pada paket ini:

1. AI sudah include dalam sistem melalui sidebar **AI Sistem + API TOML**.
2. API key dibaca dari `.streamlit/secrets.toml` menggunakan `st.secrets`.
3. API base URL dan model default juga diatur dari TOML.
4. Input API manual di sidebar hanya menjadi fallback jika TOML belum diisi.
5. `.streamlit/secrets.toml` dimasukkan ke `.gitignore` agar API key asli tidak ikut ter-upload ke GitHub.
6. Disediakan `.streamlit/secrets.example.toml` sebagai contoh konfigurasi aman.
7. Export project tidak menyimpan API key.
8. Workflow dibuat menyatu: judul/PICOS → protocol/search → import/screening → PRISMA/quality → extraction → AI insight → export.
