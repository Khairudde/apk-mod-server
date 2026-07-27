# Panduan Setup Integrasi APK Modding Server

Dokumen ini memandu Anda melalui langkah-langkah untuk menyiapkan repositori GitHub, mendeploy aplikasi FastAPI ke Railway, dan mengkonfigurasi token Hugging Face untuk server modifikasi APK Anda.

## 1. Setup Repositori GitHub

Untuk memulai, Anda perlu membuat repositori GitHub baru dan mengunggah kode proyek Anda ke sana. Ini akan menjadi sumber kode yang akan digunakan Railway untuk deployment.

### Langkah-langkah:

1.  **Buat Repositori Baru di GitHub:**
    *   Buka [GitHub](https://github.com/).
    *   Login ke akun Anda.
    *   Klik tombol `+` di pojok kanan atas, lalu pilih `New repository`.
    *   Berikan nama repositori (misalnya, `apk-mod-server`).
    *   Pilih `Public` atau `Private` sesuai preferensi Anda.
    *   **Jangan** centang `Add a README file`, `Add .gitignore`, atau `Choose a license` karena kita akan mengunggah file yang sudah ada.
    *   Klik `Create repository`.

2.  **Inisialisasi Git Lokal dan Unggah Kode:**
    *   Buka terminal Anda.
    *   Navigasikan ke direktori proyek Anda (`/home/ubuntu/apk_mod_fastapi_api`):
        ```bash
        cd /home/ubuntu/apk_mod_fastapi_api
        ```
    *   Inisialisasi repositori Git lokal:
        ```bash
        git init
        ```
    *   Tambahkan semua file proyek ke staging area:
        ```bash
        git add .
        ```
    *   Buat commit pertama:
        ```bash
        git commit -m "Initial commit: FastAPI APK Modding Server"
        ```
    *   Tambahkan remote origin ke repositori GitHub Anda (ganti `YOUR_USERNAME` dan `YOUR_REPOSITORY_NAME`):
        ```bash
        git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
        ```
    *   Push kode Anda ke GitHub:
        ```bash
        git branch -M main
        git push -u origin main
        ```

    Setelah langkah-langkah ini, kode proyek Anda akan tersedia di GitHub.

## 2. Deployment ke Railway

Railway adalah platform deployment yang memudahkan Anda untuk menghosting aplikasi Anda. Kita akan menghubungkan repositori GitHub Anda ke Railway untuk deployment otomatis.

### Langkah-langkah:

1.  **Login ke Railway:**
    *   Buka [Railway](https://railway.app/).
    *   Login menggunakan akun GitHub Anda.

2.  **Buat Proyek Baru:**
    *   Di dashboard Railway, klik `New Project`.
    *   Pilih `Deploy from GitHub Repo`.
    *   Anda mungkin perlu memberikan otorisasi kepada Railway untuk mengakses repositori GitHub Anda. Ikuti instruksi di layar.
    *   Pilih repositori `apk-mod-server` yang baru saja Anda buat.

3.  **Konfigurasi Deployment:**
    *   Railway akan secara otomatis mendeteksi `Dockerfile` Anda dan mencoba membangun serta mendeploy aplikasi.
    *   Pastikan `Root Directory` diatur ke `/` (atau direktori tempat `Dockerfile` Anda berada jika tidak di root).
    *   Railway akan memulai proses build. Anda bisa memantau log build di dashboard Railway.

4.  **Konfigurasi Variabel Lingkungan (Environment Variables):**
    *   Setelah proyek dibuat di Railway, navigasikan ke `Settings` proyek Anda.
    *   Di bagian `Variables`, tambahkan variabel lingkungan yang diperlukan:
        *   `PORT`: `8000` (sesuai dengan port yang diekspos di `Dockerfile` dan `uvicorn`)
        *   `HUGGINGFACE_API_TOKEN`: Token API Hugging Face Anda (akan dijelaskan di bagian selanjutnya).
    *   Klik `Add Variable` untuk setiap variabel.

5.  **Domain dan Akses:**
    *   Setelah deployment berhasil, Railway akan memberikan Anda URL publik untuk aplikasi Anda. Anda bisa menemukannya di bagian `Domains` atau `Overview` proyek Anda.
    *   Gunakan URL ini sebagai endpoint webhook Anda.

## 3. Konfigurasi Token Hugging Face

Untuk menggunakan Hugging Face Inference API, Anda memerlukan token API. Token ini harus disimpan sebagai variabel lingkungan di Railway untuk keamanan.

### Langkah-langkah:

1.  **Dapatkan Token Hugging Face API:**
    *   Buka [Hugging Face](https://huggingface.co/).
    *   Login ke akun Anda.
    *   Klik ikon profil Anda di pojok kanan atas, lalu pilih `Settings`.
    *   Di sidebar kiri, pilih `Access Tokens`.
    *   Klik `New token`.
    *   Berikan nama untuk token Anda (misalnya, `apk-mod-server-token`).
    *   Pilih `Role` sebagai `read` atau `write` tergantung pada kebutuhan Anda (untuk Inference API, `read` biasanya cukup).
    *   Klik `Generate a token`.
    *   **Salin token yang dihasilkan.** Token ini hanya akan ditampilkan sekali.

2.  **Tambahkan Token ke Railway:**
    *   Kembali ke dashboard proyek Railway Anda.
    *   Navigasikan ke `Settings` > `Variables`.
    *   Tambahkan variabel baru dengan nama `HUGGINGFACE_API_TOKEN` dan tempel token yang Anda salin sebagai nilainya.
    *   Railway akan secara otomatis me-restart aplikasi Anda dengan variabel lingkungan baru.

Dengan mengikuti panduan ini, Anda akan memiliki server modifikasi APK berbasis FastAPI yang berjalan di Railway, terhubung ke GitHub, dan siap untuk berinteraksi dengan Hugging Face Inference API.

---

**Catatan Penting:**
*   Pastikan Anda telah menginstal `apktool` dan `uber-apk-signer` di dalam `Dockerfile` dengan versi yang sesuai. `Dockerfile` yang saya berikan sudah mencakup instalasi dasar.
*   Logika modifikasi APK di `main.py` masih berupa placeholder. Anda perlu mengimplementasikan logika parsing `instruksi` dan modifikasi file (smali, XML, dll.) sesuai kebutuhan Anda.
*   Untuk produksi, pertimbangkan untuk menggunakan layanan penyimpanan objek (seperti AWS S3 atau Google Cloud Storage) untuk menyimpan APK yang dimodifikasi dan mengembalikan URL publiknya, daripada hanya mengembalikan path lokal.
