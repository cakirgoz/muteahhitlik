from datetime import date

from period_finder import (
    json_dosyasini_oku,
    donem_bul
)

print(json_dosyasini_oku())

print(donem_bul("2019-06-18", "gecerlilik"))

date_str = donem_bul("2019-06-18", "yayim")['tarih']