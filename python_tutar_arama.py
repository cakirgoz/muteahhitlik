import json
from datetime import datetime
from typing import Dict, Any, Optional


def tutar_bul(json_dosya_yolu: str, tarih: str, belge_sinifi: str, tarih_tipi: str = 'yayim') -> Dict[str, Any]:
    """
    Verilen tarih ve belge sınıfına göre geçerli tutarı bulur

    Args:
        json_dosya_yolu (str): JSON dosyasının yolu
        tarih (str): Aranacak tarih (YYYY-MM-DD formatında)
        belge_sinifi (str): Belge sınıfı (A, B, B1, C, C1, D, D1, E, E1, F, F1, G, G1)
        tarih_tipi (str): 'yayim' veya 'gecerlilik' (hangi tarih aralığına göre arama yapılacağı)

    Returns:
        dict: Bulunan sonuç objesi
    """

    try:
        # JSON dosyasını yükle
        with open(json_dosya_yolu, 'r', encoding='utf-8') as f:
            max_is_tutari_data = json.load(f)
    except FileNotFoundError:
        return {
            'success': False,
            'error': f'JSON dosyası bulunamadı: {json_dosya_yolu}'
        }
    except json.JSONDecodeError:
        return {
            'success': False,
            'error': 'JSON dosyası okunamadı. Geçersiz format.'
        }

    # Tarih string'ini datetime objesine çevir
    try:
        arama_tarihi = datetime.strptime(tarih, '%Y-%m-%d')
    except ValueError:
        return {
            'success': False,
            'error': 'Geçersiz tarih formatı. YYYY-MM-DD formatında tarih giriniz.'
        }

    # Belge sınıfının geçerli olup olmadığını kontrol et
    gecerli_belge_siniflari = ['A', 'B', 'B1', 'C', 'C1', 'D', 'D1', 'E', 'E1', 'F', 'F1', 'G', 'G1', 'H']
    if belge_sinifi not in gecerli_belge_siniflari:
        return {
            'success': False,
            'error': f'Geçersiz belge sınıfı. Geçerli sınıflar: {", ".join(gecerli_belge_siniflari)}'
        }

    # Tarih tipini kontrol et
    if tarih_tipi not in ['yayim', 'gecerlilik']:
        return {
            'success': False,
            'error': 'Geçersiz tarih tipi. "yayim" veya "gecerlilik" olmalıdır.'
        }

    # Uygun dönem verilerini bul
    uygun_donem = None

    for donem in max_is_tutari_data:
        if tarih_tipi == 'yayim':
            baslangic_tarihi = datetime.strptime(donem['yayim_tarihi'], '%Y-%m-%d')
            bitis_tarihi = datetime.strptime(donem['yayim_sonu'], '%Y-%m-%d')
        else:
            baslangic_tarihi = datetime.strptime(donem['gecerlilik_tarihi'], '%Y-%m-%d')
            bitis_tarihi = datetime.strptime(donem['gecerlilik_sonu'], '%Y-%m-%d')

        # Tarih aralığı kontrolü
        if baslangic_tarihi <= arama_tarihi <= bitis_tarihi:
            # Bu dönemde belirtilen belge sınıfı var mı?
            if belge_sinifi in donem['tutarlar']:
                uygun_donem = donem
                break  # İlk uygun dönemi bul ve dur

    if not uygun_donem:
        return {
            'success': False,
            'error': f'{tarih} tarihi için {belge_sinifi} sınıfında geçerli tutar bulunamadı.'
        }

    tutar = uygun_donem['tutarlar'][belge_sinifi]

    # Sınırsız tutar kontrolü
    if tutar == float('inf'):
        formatli_tutar = 'Sınırsız'
    else:
        formatli_tutar = f'{tutar:,.2f} ₺'

    return {
        'success': True,
        'data': {
            'donem': uygun_donem['donem'],
            'yayim_tarihi': uygun_donem['yayim_tarihi'],
            'yayim_sonu': uygun_donem['yayim_sonu'],
            'gecerlilik_tarihi': uygun_donem['gecerlilik_tarihi'],
            'gecerlilik_sonu': uygun_donem['gecerlilik_sonu'],
            'belge_sinifi': belge_sinifi,
            'tutar': tutar,
            'formatli_tutar': formatli_tutar
        }
    }


def tum_tutarlari_listele(json_dosya_yolu: str, tarih: str, tarih_tipi: str = 'gecerlilik') -> Dict[str, Any]:
    """
    Belirli bir tarih aralığındaki tüm belge sınıfları için tutarları listeler

    Args:
        json_dosya_yolu (str): JSON dosyasının yolu
        tarih (str): Aranacak tarih (YYYY-MM-DD formatında)
        tarih_tipi (str): 'yayim' veya 'gecerlilik'

    Returns:
        dict: Tüm belge sınıfları için sonuçlar
    """

    try:
        # JSON dosyasını yükle
        with open(json_dosya_yolu, 'r', encoding='utf-8') as f:
            max_is_tutari_data = json.load(f)
    except FileNotFoundError:
        return {
            'success': False,
            'error': f'JSON dosyası bulunamadı: {json_dosya_yolu}'
        }
    except json.JSONDecodeError:
        return {
            'success': False,
            'error': 'JSON dosyası okunamadı. Geçersiz format.'
        }

    try:
        arama_tarihi = datetime.strptime(tarih, '%Y-%m-%d')
    except ValueError:
        return {
            'success': False,
            'error': 'Geçersiz tarih formatı. YYYY-MM-DD formatında tarih giriniz.'
        }

    # Uygun dönem verilerini bul
    uygun_donem = None

    for donem in max_is_tutari_data:
        if tarih_tipi == 'yayim':
            baslangic_tarihi = datetime.strptime(donem['yayim_tarihi'], '%Y-%m-%d')
            bitis_tarihi = datetime.strptime(donem['yayim_sonu'], '%Y-%m-%d')
        else:
            baslangic_tarihi = datetime.strptime(donem['gecerlilik_tarihi'], '%Y-%m-%d')
            bitis_tarihi = datetime.strptime(donem['gecerlilik_sonu'], '%Y-%m-%d')

        if baslangic_tarihi <= arama_tarihi <= bitis_tarihi:
            uygun_donem = donem
            break

    if not uygun_donem:
        return {
            'success': False,
            'error': f'{tarih} tarihi için geçerli dönem bulunamadı.'
        }

    # Tutarları formatla
    formatli_tutarlar = {}
    for sinif, tutar in uygun_donem['tutarlar'].items():
        if tutar == float('inf'):
            formatli_tutar = 'Sınırsız'
        else:
            formatli_tutar = f'{tutar:,.2f} ₺'

        formatli_tutarlar[sinif] = {
            'tutar': tutar,
            'formatli_tutar': formatli_tutar
        }

    return {
        'success': True,
        'data': {
            'donem': uygun_donem['donem'],
            'yayim_tarihi': uygun_donem['yayim_tarihi'],
            'yayim_sonu': uygun_donem['yayim_sonu'],
            'gecerlilik_tarihi': uygun_donem['gecerlilik_tarihi'],
            'gecerlilik_sonu': uygun_donem['gecerlilik_sonu'],
            'tutarlar': formatli_tutarlar
        }
    }


def csv_den_json_olustur(csv_dosya_yolu: str, json_dosya_yolu: str) -> bool:
    """
    CSV dosyasından JSON dosyası oluşturur

    Args:
        csv_dosya_yolu (str): CSV dosyasının yolu
        json_dosya_yolu (str): Oluşturulacak JSON dosyasının yolu

    Returns:
        bool: İşlem başarılı ise True
    """
    import csv

    try:
        json_data = []

        with open(csv_dosya_yolu, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')

            for row in reader:
                # Tarihleri düzenle
                yayim_tarihi_parts = row['YAYIM_TARIHI'].split('.')
                yayim_tarihi = f"{yayim_tarihi_parts[2]}-{yayim_tarihi_parts[1].zfill(2)}-{yayim_tarihi_parts[0].zfill(2)}"

                yayim_sonu_parts = row['YAYIM_SONU'].split('.')
                yayim_sonu = f"{yayim_sonu_parts[2]}-{yayim_sonu_parts[1].zfill(2)}-{yayim_sonu_parts[0].zfill(2)}"

                gecerlilik_tarihi_parts = row['GECERLILIK_TARIHI'].split('.')
                gecerlilik_tarihi = f"{gecerlilik_tarihi_parts[2]}-{gecerlilik_tarihi_parts[1].zfill(2)}-{gecerlilik_tarihi_parts[0].zfill(2)}"

                gecerlilik_sonu_parts = row['GECERLILIK_SON'].split('.')
                gecerlilik_sonu = f"{gecerlilik_sonu_parts[2]}-{gecerlilik_sonu_parts[1].zfill(2)}-{gecerlilik_sonu_parts[0].zfill(2)}"

                # Tutarları işle - A sütunu sınırsız değeri içeriyor
                tutarlar = {}
                siniflar = ['A', 'B', 'B1', 'C', 'C1', 'D', 'D1', 'E', 'E1', 'F', 'F1', 'G', 'G1', 'H']

                # A sütunu özel durum - sınırsız tutar
                if 'A' in row and row['A']:
                    a_deger = row['A'].replace('₺', '').replace('?', '').strip()
                    if '10.000.000.000.000.000.000.000.000,00' in a_deger:
                        tutarlar['A'] = float('inf')  # Sınırsız için infinity
                    else:
                        try:
                            # Normal tutar
                            tutar_str = a_deger.replace('.', '').replace(',', '.')
                            tutarlar['A'] = float(tutar_str)
                        except ValueError:
                            pass

                # Diğer sınıflar için normal işlem
                for sinif in siniflar[1:]:  # A'yı atlayarak devam et
                    if sinif in row and row[sinif] and row[sinif] != 'yok':
                        # Para birimini ve formatı temizle
                        tutar_str = row[sinif].replace('₺', '').replace('?', '').strip()
                        tutar_str = tutar_str.replace('.', '').replace(',', '.')
                        try:
                            tutarlar[sinif] = float(tutar_str)
                        except ValueError:
                            continue

                # Sınır durumunu belirle
                sinir_durumu = 'sınırsız' if tutarlar.get('A') == float('inf') else 'normal'

                donem_data = {
                    'donem': row['DONEM'],
                    'yayim_tarihi': yayim_tarihi,
                    'yayim_sonu': yayim_sonu,
                    'gecerlilik_tarihi': gecerlilik_tarihi,
                    'gecerlilik_sonu': gecerlilik_sonu,
                    'sinir_durumu': sinir_durumu,
                    'tutarlar': tutarlar
                }

                json_data.append(donem_data)

        # JSON dosyasına yaz
        with open(json_dosya_yolu, 'w', encoding='utf-8') as jsonfile:
            json.dump(json_data, jsonfile, ensure_ascii=False, indent=2, default=str)  # default=str infinity için

        return True

    except Exception as e:
        print(f"Hata: {e}")
        return False


# Kullanım örnekleri
if __name__ == "__main__":
    # Önce CSV'den JSON oluştur
    csv_dosyasi = "max_is_tutari.csv"
    json_dosyasi = "max_is_tutari.json"

    print("CSV dosyasından JSON oluşturuluyor...")
    if csv_den_json_olustur(csv_dosyasi, json_dosyasi):
        print(f"JSON dosyası başarıyla oluşturuldu: {json_dosyasi}")
    else:
        print("JSON dosyası oluşturulurken hata oluştu!")
        exit()

    print("\n" + "=" * 50 + "\n")

    # Örnek kullanım
    # Tek bir tutar arama
    sonuc = tutar_bul(json_dosyasi, "2019-06-15", "B1", "gecerlilik")
    if sonuc['success']:
        print("Bulunan tutar:")
        print(f"Dönem: {sonuc['data']['donem']}")
        print(f"Belge Sınıfı: {sonuc['data']['belge_sinifi']}")
        print(f"Tutar: {sonuc['data']['formatli_tutar']}")
        print(f"Geçerlilik: {sonuc['data']['gecerlilik_tarihi']} - {sonuc['data']['gecerlilik_sonu']}")
    else:
        print(f"Hata: {sonuc['error']}")

    print("\n" + "=" * 30 + "\n")

    # B1 sınıfı için arama
    sonuc2 = tutar_bul(json_dosyasi, "2025-05-29", "B1", "gecerlilik")
    if sonuc2['success']:
        print("B1 sınıfı için bulunan tutar:")
        print(f"Dönem: {sonuc2['data']['donem']}")
        print(f"Belge Sınıfı: {sonuc2['data']['belge_sinifi']}")
        print(f"Tutar: {sonuc2['data']['formatli_tutar']}")
    else:
        print(f"Hata: {sonuc2['error']}")

    print("\n" + "=" * 50 + "\n")

    # Tüm tutarları listeleme
    tum_sonuclar = tum_tutarlari_listele(json_dosyasi, "2025-06-15", "gecerlilik")
    if tum_sonuclar['success']:
        print("Tüm tutarlar:")
        print(f"Dönem: {tum_sonuclar['data']['donem']}")
        print(f"Geçerlilik: {tum_sonuclar['data']['gecerlilik_tarihi']} - {tum_sonuclar['data']['gecerlilik_sonu']}")
        print("\nBelge Sınıfları ve Tutarları:")
        for sinif, tutar_bilgi in tum_sonuclar['data']['tutarlar'].items():
            print(f"{sinif}: {tutar_bilgi['formatli_tutar']}")
    else:
        print(f"Hata: {tum_sonuclar['error']}")