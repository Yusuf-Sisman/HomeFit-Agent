# 🏠 HomeFit Pro Agent: Akıllı Konum Analiz Asistanı

**HomeFit Pro Agent**, bir evin çevresel imkanlarını (hastane, okul, ulaşım vb.) hem sayısal verilerle hem de yapay zeka yorumlarıyla analiz eden, coğrafi bilgi sistemleri (GIS) tabanlı bir web uygulamasıdır.

![Language](https://img.shields.io/badge/Language-Turkish%20%2F%20English-blue)
![Framework](https://img.shields.io/badge/Framework-FastAPI-green)
![AI](https://img.shields.io/badge/AI-Google%20Gemini%202.5%20Flash-orange)
![Deployment](https://img.shields.io/badge/Deployment-Render-lightgrey)

## 🚀 Özellikler

* **İnteraktif Harita Analizi:** Leaflet tabanlı harita üzerinde tıklayarak veya sürükleyerek konum seçimi.
* **Adres Öneri Sistemi:** Nominatim API destekli, yazarken tamamlanan (autocomplete) gelişmiş adres arama motoru.
* **Gelişmiş Tesis Analizi:**
    * Hastaneler, Eczaneler, Marketler, Parklar, Okullar ve İbadethaneler için gerçek zamanlı OSM verisi.
    * Alt kategori desteği (Metro, Otobüs, İlkokul, Lise, Cami, Sinagog vb.).
* **Dinamik Skorlama:** Kullanıcı tercihlerine göre (Normal, Çok Önemli) ağırlıklı puanlama sistemi.
* **Ağ Analizi (OSRM):** Kuşbakışı mesafe yerine gerçek yol ağı üzerinden yürüme ve sürüş süresi hesaplama.
* **🤖 Yapay Zeka Yorumu:** Analiz sonuçlarını profesyonel bir gayrimenkul danışmanı gibi yorumlayan Google Gemini entegrasyonu.
* **Görsel Raporlama:** Harita ve analiz sonuçlarını içeren çıktıya hazır görsel HTML rapor oluşturma.
* **Çift Dil Desteği:** Tek tıkla tamamen Türkçe veya İngilizce arayüz ve analiz.

## 🛠️ Teknoloji Yığını

* **Backend:** Python 3.x, FastAPI, Uvicorn
* **Frontend:** HTML5, CSS3 (Modern UI), Vanilla JavaScript
* **Harita:** Leaflet.js, OpenStreetMap
* **Veri Kaynakları:** Overpass API (OSM Data), OSRM (Routing Engine), Nominatim (Geocoding)
* **Yapay Zeka:** Google Generative AI (Gemini SDK)

## 📦 Kurulum ve Çalıştırma

### 1. Yerel Çalıştırma (Local)

Önce projeyi bilgisayarınıza indirin ve klasöre girin:

```bash
git clone https://github.com/kullaniciadi/homefit-pro.git
cd homefit-pro
```

Gerekli kütüphaneleri kurun:

```bash
pip install -r requirements.txt
```

Projeyi başlatın:

```bash
python main.py
```
Uygulamaya tarayıcınızdan `http://127.0.0.1:8000` adresinden erişebilirsiniz.

### 2. Gerekli Çevre Değişkenleri
Yapay zeka özelliğinin çalışması için bir API anahtarına ihtiyacınız vardır. Proje, bu anahtarı `GEMINI_API_KEY` değişkeninden okur.

## ☁️ Render Deployment (Canlıya Alma)

Bu proje Render üzerinde çalışacak şekilde optimize edilmiştir:
1.  **Runtime:** Python 3
2.  **Build Command:** `pip install -r requirements.txt`
3.  **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4.  **Environment Variables:** Render panelinden `GEMINI_API_KEY` değerini eklemeyi unutmayın.

## 📂 Proje Yapısı

```text
homefit-pro/
├── main.py              # FastAPI sunucusu ve AI/OSM mantığı
├── requirements.txt     # Gerekli Python kütüphaneleri
└── static/
    └── index.html       # Tek sayfa (SPA) Frontend arayüzü
```

## ⚖️ Lisans

Bu proje eğitim amaçlı geliştirilmiştir. Veri kaynağı olarak OpenStreetMap (ODbL) kullanılmaktadır.

---

### Nasıl Kullanılır?
1. Klasöründe `README.md` adında yeni bir dosya oluştur.
2. Yukarıdaki metni içine yapıştır.
3. GitHub'a yüklediğinde bu metin ana sayfada çok şık bir şekilde görünecektir.
