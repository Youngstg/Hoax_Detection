# Sistem Deteksi Berita Hoax

Website otomatis untuk memeriksa keaslian berita berdasarkan analisis machine learning dan verifikasi sumber terpercaya.

## Fitur

- **Analisis Machine Learning**: Menggunakan 3 model (Random Forest, Naive Bayes, Logistic Regression)
- **Verifikasi Sumber**: Memeriksa referensi ke sumber berita terpercaya
- **Analisis Sentimen**: Mendeteksi pola emosional dalam teks
- **Deteksi Pola Mencurigakan**: Identifikasi kata-kata dan pola yang sering digunakan dalam hoax
- **Riwayat Analisis**: Menyimpan hasil analisis sebelumnya
- **Interface Responsif**: Antarmuka web yang mobile-friendly

## Instalasi

### Backend (Flask)

1. Install dependencies:
```bash
cd backend
pip install -r ../requirements.txt
```

2. Download NLTK data (jalankan Python dan eksekusi):
```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
```

3. Jalankan server:
```bash
python app.py
```

Server akan berjalan di `http://localhost:5000`

### Frontend

1. Buka folder frontend:
```bash
cd frontend
```

2. Buka file `index.html` di browser atau gunakan live server

## Penggunaan

1. Buka website di browser
2. Masukkan teks berita yang ingin dianalisis
3. Klik "Analisis Berita"
4. Lihat hasil analisis dengan tingkat kepercayaan
5. Periksa riwayat analisis di bagian bawah

## Struktur Project

```
Hoax_Detection/
├── backend/
│   ├── app.py              # Flask API server
│   ├── news_analyzer.py    # ML models dan preprocessing
│   └── models/             # Saved ML models
├── frontend/
│   ├── index.html          # Main webpage
│   ├── style.css           # Styles
│   └── script.js           # JavaScript logic
├── data/                   # Training data (jika ada)
├── requirements.txt        # Python dependencies
└── README.md
```

## API Endpoints

- `POST /api/analyze` - Analisis teks berita
- `GET /api/history` - Riwayat analisis
- `GET /api/health` - Health check

## Model Machine Learning

Sistem menggunakan tiga model yang digabungkan:

1. **Random Forest**: Baik untuk feature importance
2. **Naive Bayes**: Efektif untuk text classification
3. **Logistic Regression**: Interpretable dan cepat

### Features yang Dianalisis:

- Jumlah kata dan karakter
- Panjang rata-rata kata
- Sentimen (polaritas dan subjektivitas)
- Kata-kata mencurigakan
- Pola kapitalisasi
- Jumlah tanda seru dan tanya

## Sumber Terpercaya

Sistem memeriksa referensi ke sumber berita terpercaya seperti:
- Reuters, AP, BBC, CNN, NPR (International)
- Kompas, Detik, Tempo, Antara, Liputan6 (Indonesia)

## Pengembangan Lanjutan

- Tambah dataset training yang lebih besar
- Implementasi web scraping untuk verifikasi real-time
- Integrasi dengan fact-checking APIs
- Tambah model deep learning (BERT, etc.)
- Implementasi caching untuk performa yang lebih baik