import json
from datetime import datetime, date
from typing import Dict, Any, Optional, Union


def tutar_bul(json_dosya_yolu: str, tarih: Union[str, date], belge_sinifi: str, tarih_tipi: str = 'gecerlilik') -> Dict[str, Any]:
    """
    Verilen tarih ve belge sınıfına göre geçerli tutarı bulur

    Args:
        json_dosya_yolu (str): JSON dosyasının yolu
        tarih (Union[str, date]): Aranacak tarih (YYYY-MM-DD formatında string veya date objesi)
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

    # Tarih parametresini datetime objesine çevir
    try:
        if isinstance(tarih, date):
            # Date objesi ise datetime'a çevir
            arama_tarihi = datetime.combine(tarih, datetime.min.time())
            tarih_str = tarih.strftime('%Y-%m-%d')
        elif isinstance(tarih, str):
            # String ise parse et
            arama_tarihi = datetime.strptime(tarih, '%Y-%m-%d')
            tarih_str = tarih
        else:
            return {
                'success': False,
                'error': f'Desteklenmeyen tarih tipi: {type(tarih)}. String veya date objesi bekleniyor.'
            }
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
            'error': f'{tarih_str} tarihi için {belge_sinifi} sınıfında geçerli tutar bulunamadı.\n\nGirilen belge sınıfının ruhsat onay tarihinde geçerli olduğunu kontrol edin!!!'
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

# print(tutar_bul('max_is_tutari.json', '2023-10-02', 'B1', 'yayim'))