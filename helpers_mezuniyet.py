import json
from datetime import datetime
import os


def get_price_for_date(date, json_file_path):
    """
    Verilen tarih ve json dosyasına göre, belirtilen tarihin hangi dönemde olduğunu
    ve o döneme ait fiyat bilgisini döndüren fonksiyon.

    Args:
    - date (datetime.date): Kullanıcının girdiği tarih
    - json_file_path (str): JSON dosyasının yolu

    Returns:
    - float: O döneme ait yıllık tutar
    """
    # JSON dosyasını aç ve içeriğini oku
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Verilen tarih ile dönemi kontrol et
    for period in data:
        # "baslangic_yayim" ve "bitis_yayim" tarihlerini string'den datetime'a çevir
        start_date = datetime.strptime(period['baslangic_yayim'], '%d.%m.%Y').date()
        end_date = datetime.strptime(period['bitis_yayim'], '%d.%m.%Y').date()

        # Eğer verilen tarih, dönemin yayım tarihleri arasında ise, fiyatı döndür
        if start_date <= date <= end_date:
            return period['yillik_tutar']

    # Eğer tarih hiçbir döneme denk gelmiyorsa, None döndür
    return None


# # Örnek kullanım
# date = datetime(2025, 5, 15).date()  # Örnek tarih
# json_file_path = "mezuniyet_tutar.json"  # JSON dosyanızın yolu
#
# price = get_price_for_date(date, json_file_path)
# if price:
#     print(f"{date} tarihi için yıllık tutar: {price} TL")
# else:
#     print(f"{date} tarihi için geçerli bir dönem bulunamadı.")