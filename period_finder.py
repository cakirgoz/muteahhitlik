import json
from datetime import datetime, date
import os

def json_dosyasini_oku(dosya_yolu="periods_json.json"):
    """
    JSON dosyasını okur ve dönem verilerini döndürür.
    
    Args:
        dosya_yolu (str): JSON dosyasının yolu
    
    Returns:
        list: Dönem verileri listesi
    """
    try:
        if os.path.exists(dosya_yolu):
            with open(dosya_yolu, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('periods', [])
        else:
            print(f"⚠️  JSON dosyası bulunamadı: {dosya_yolu}")
            print("Varsayılan veriler kullanılacak...")
            return get_default_periods()
    except Exception as e:
        print(f"❌ JSON dosyası okunurken hata oluştu: {e}")
        print("Varsayılan veriler kullanılacak...")
        return get_default_periods()

def get_default_periods():
    """
    JSON dosyası yoksa kullanılacak varsayılan veriler
    """
    return [
        {"yil": 2000, "donem": "2000_1", "yayim_baslangic": "2020-02-25", "yayim_bitis": "2001-02-09", "gecerlilik_baslangic": "2000-01-01", "gecerlilik_bitis": "2000-12-31"},
        {"yil": 2001, "donem": "2001_1", "yayim_baslangic": "2001-02-10", "yayim_bitis": "2002-03-06", "gecerlilik_baslangic": "2001-01-01", "gecerlilik_bitis": "2001-12-31"},
        {"yil": 2022, "donem": "2022_1", "yayim_baslangic": "2022-02-18", "yayim_bitis": "2022-06-20", "gecerlilik_baslangic": "2022-01-01", "gecerlilik_bitis": "2022-06-01"},
        {"yil": 2023, "donem": "2023_1", "yayim_baslangic": "2023-02-11", "yayim_bitis": "2023-08-11", "gecerlilik_baslangic": "2023-01-01", "gecerlilik_bitis": "2023-06-30"},
        {"yil": 2024, "donem": "2024_1", "yayim_baslangic": "2024-04-20", "yayim_bitis": "2025-01-30", "gecerlilik_baslangic": "2024-01-01", "gecerlilik_bitis": "2024-12-31"},
        {"yil": 2025, "donem": "2025_1", "yayim_baslangic": "2025-01-31", "yayim_bitis": "2025-12-31", "gecerlilik_baslangic": "2025-01-01", "gecerlilik_bitis": "2025-12-31"}
    ]

# JSON dosyasından verileri yükle
PERIODS_DATA = json_dosyasini_oku()


def donem_bul(tarih_param, opsiyon="yayim"):
    """
    Verilen tarihin hangi döneme ait olduğunu bulur.

    Args:
        tarih_param (str or datetime.date): Aranacak tarih (YYYY-MM-DD formatında string veya date objesi)
        opsiyon (str): "gecerlilik" veya "yayim" - hangi tarih aralığına göre arama yapılacağı

    Returns:
        dict: Bulunan dönem bilgisi veya None
    """
    print(f"Tarih şu: {tarih_param}")
    print(type(tarih_param))

    try:
        # Girilen tarihi datetime objesine çevir
        if isinstance(tarih_param, date):
            # Eğer date objesi ise direkt kullan
            aranan_tarih = datetime.combine(tarih_param, datetime.min.time())
            tarih_str = tarih_param.strftime("%Y-%m-%d")
        elif isinstance(tarih_param, str):
            # String ise parse et
            aranan_tarih = datetime.strptime(tarih_param, "%Y-%m-%d")
            tarih_str = tarih_param
        elif tarih_param is None:
            return {"hata": "Tarih değeri None"}
        else:
            return {"hata": f"Desteklenmeyen tarih tipi: {type(tarih_param)}"}

        # Her dönem için kontrol et
        for period in PERIODS_DATA:
            if opsiyon == "gecerlilik":
                baslangic = datetime.strptime(period["gecerlilik_baslangic"], "%Y-%m-%d")
                bitis = datetime.strptime(period["gecerlilik_bitis"], "%Y-%m-%d")
            elif opsiyon == "yayim":
                baslangic = datetime.strptime(period["yayim_baslangic"], "%Y-%m-%d")
                bitis = datetime.strptime(period["yayim_bitis"], "%Y-%m-%d")
            else:
                return {"hata": "Opsiyon 'gecerlilik' veya 'yayim' olmalıdır"}

            # Tarih aralığında mı kontrol et
            if baslangic <= aranan_tarih <= bitis:
                return {
                    "donem": period["donem"],
                    "yil": period["yil"],
                    "bulunan_opsiyon": opsiyon,
                    "aralık": f"{baslangic.strftime('%Y-%m-%d')} - {bitis.strftime('%Y-%m-%d')}",
                    "tarih": tarih_str
                }

        return None

    except ValueError as e:
        return {"hata": f"Tarih formatı hatalı: {e}"}
    except Exception as e:
        return {"hata": f"Beklenmeyen hata: {e}"}

def kullanici_arayuzu():
    """
    Kullanıcı ile etkileşim için basit bir arayüz
    """
    print("=== DÖNEM BULMA SİSTEMİ ===")
    print("Tarih formatı: YYYY-MM-DD (örn: 2023-05-15)")
    print("Çıkmak için 'q' yazın\n")
    
    while True:
        # Tarih girişi
        tarih = input("Aramak istediğiniz tarihi girin: ").strip()
        if tarih.lower() == 'q':
            print("Program sonlandırılıyor...")
            break
            
        # Opsiyon seçimi
        print("\nHangi tarih aralığına göre arama yapmak istiyorsunuz?")
        print("1. Geçerlilik tarihi")
        print("2. Yayım tarihi")
        
        secim = input("Seçiminizi yapın (1 veya 2): ").strip()
        
        if secim == "1":
            opsiyon = "gecerlilik"
        elif secim == "2":
            opsiyon = "yayim"
        else:
            print("Geçersiz seçim! Lütfen 1 veya 2 seçin.\n")
            continue
        
        # Dönem bulma
        sonuc = donem_bul(tarih, opsiyon)
        
        print("\n" + "="*50)
        if sonuc and "hata" not in sonuc:
            print(f"✅ DÖNEM BULUNDU!")
            print(f"Dönem Adı: {sonuc['donem']}")
            print(f"Yıl: {sonuc['yil']}")
            print(f"Arama Türü: {sonuc['bulunan_opsiyon'].title()}")
            print(f"Tarih Aralığı: {sonuc['aralık']}")
        elif sonuc and "hata" in sonuc:
            print(f"❌ HATA: {sonuc['hata']}")
        else:
            print(f"❌ Girilen tarih ({tarih}) için {opsiyon} aralığında dönem bulunamadı!")
        print("="*50 + "\n")

# Örnek kullanımlar
if __name__ == "__main__":
    print("Örnek Kullanımlar:")
    print("-" * 30)
    
    # Test örnekleri
    test_tarihleri = [
        ("2023-06-30", "gecerlilik"),
        ("2023-09-10", "yayim"),
        ("2022-06-15", "gecerlilik"),
        ("2024-05-01", "yayim")
    ]
    
    for tarih, opsiyon in test_tarihleri:
        sonuc = donem_bul(tarih, opsiyon)
        if sonuc and "hata" not in sonuc:
            print(f"Tarih: {tarih} ({opsiyon}) -> Dönem: {sonuc['donem']}")
        else:
            print(f"Tarih: {tarih} ({opsiyon}) -> Dönem bulunamadı")
    
    print("\n" + "="*50)
    print("İnteraktif kullanım için fonksiyonu çalıştırın:")
    print("kullanici_arayuzu()")
    print("="*50)
    
    # İnteraktif arayüzü başlat
    kullanici_arayuzu()
