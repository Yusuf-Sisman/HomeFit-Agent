# 🏠 HomeFit Agent: Akıllı Konum Analiz Asistanı 

**HomeFit Agent**, bir evin çevresel imkanlarını (hastane, okul, ulaşım vb.) hem sayısal verilerle hem de yapay zeka yorumlarıyla analiz eden, coğrafi bilgi sistemleri (GIS) tabanlı bir web uygulamasıdır.

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

## 📚 Referanslar & Kaynakça

Projenin geliştirilmesinde kullanılan açık kaynaklı veriler, kütüphaneler ve servis sağlayıcılar aşağıda listelenmiştir:

1. **OpenStreetMap (OSM) Data:** * Harita altlığı ve mekansal veri kaynağı olarak OpenStreetMap kullanılmıştır. Veriler [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/) kapsamında temin edilmektedir.
   * *Referans:* OpenStreetMap contributors. (2026). Planet dump retrieved from [https://planet.openstreetmap.org](https://planet.openstreetmap.org)

2. **Overpass API:** * Tesislerin (hastane, okul, park vb.) anlık koordinat sorgulamaları Overpass API üzerinden asenkron olarak gerçekleştirilmiştir.
   * *Referans:* Olbricht, R. (2026). Overpass API. [https://overpass-api.de/](https://overpass-api.de/)

3. **OSRM (Open Source Routing Machine):** * Kuşbakışı mesafe yerine, gerçek yol ağı algoritmalarıyla yürüme ve sürüş sürelerinin hesaplanmasında OSRM motoru kullanılmıştır.
   * *Referans:* Luxen, D., & Vetter, C. (2011). Real-time routing with OpenStreetMap data. *Proceedings of the 19th ACM SIGSPATIAL International Conference on Advances in Geographic Information Systems*. [http://project-osrm.org/](http://project-osrm.org/)

4. **Nominatim API:** * Adres arama ve otomatik tamamlama (Geocoding / Autocomplete) işlemleri için entegre edilmiştir.
   * *Referans:* Nominatim Geocoding Service. [https://nominatim.org/](https://nominatim.org/)

5. **Google Gemini API (GeoAI):** * Elde edilen ham mekansal verilerin doğal dil işleme (NLP) yetenekleriyle son kullanıcıya hitap edecek profesyonel bir gayrimenkul raporuna dönüştürülmesinde `gemini-1.5-flash` modeli kullanılmıştır.
   * *Referans:* Google Generative AI SDK. [https://ai.google.dev/](https://ai.google.dev/)

6. **Leaflet.js:** * Web tabanlı harita arayüzünün, özel işaretçilerin ve vektörel çizimlerin istemci tarafında görselleştirilmesi için tercih edilmiştir.
   * *Referans:* Agafonkin, V. (2026). Leaflet: An open-source JavaScript library for mobile-friendly interactive maps. [https://leafletjs.com/](https://leafletjs.com/)

7. **FastAPI Framework:** * Yüksek performanslı asenkron API uç noktalarının (endpoints) oluşturulmasında altyapı olarak kullanılmıştır.
   * *Referans:* Ramírez, S. (2026). FastAPI. [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/)
