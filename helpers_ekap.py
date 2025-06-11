from datetime import date
import json
import os
from period_finder import (
    json_dosyasini_oku,
    donem_bul
)
from ekap_max_tutar import tutar_bul
from helpers_mezuniyet import get_price_for_date


current_directory = os.path.dirname(os.path.abspath(__file__))
max_json_path = os.path.join(current_directory, 'max_is_tutari.json')
mezuniyet_tutar_json_path = os.path.join(current_directory, 'mezuniyet_tutar.json')


def format_currency(amount):
    """Format a number as Turkish Lira currency string with dots for thousands and comma for decimals"""
    formatted = f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} TL"

def format_date(date_value):
    """Format a date object as dd/mm/yyyy string"""
    if isinstance(date_value, date):
        return date_value.strftime("%d/%m/%Y")
    return date_value


def validate_dates(application_date, contract_date, acceptance_date=None):
    """Validate the chronological order of dates"""
    if not application_date > contract_date:
        return False, "Başvuru tarihi, Sözleşme/Diploma tarihinden büyük olmalıdır."

    if not acceptance_date < contract_date:
        return False, "Geçici Kabul/İskan tarihi, Sözleşme tarihinden büyük olmalıdır."

    if acceptance_date:
        if not application_date > acceptance_date:
            return False, "Başvuru tarihi, Geçici Kabul/İskan tarihinden büyük olmalıdır."
        if not acceptance_date > contract_date:
            return False, "Geçici Kabul/İskan tarihi, Sözleşme tarihinden büyük olmalıdır."

    return True, ""


def mezuniyet_guncelle(tarih1, tarih2, has_experience_cert=False):
    """
    Calculate updated graduation amount based on date differences

    Args:
        tarih1 (date): Later date (typically application date)
        tarih2 (date): Earlier date (typically graduation date)
        has_experience_cert (bool): Whether the person has experience certificate

    Returns:
        tuple: (float: Updated amount based on time difference,
               dict: Calculation details including years, months, days)
    """
    # yillik_tutar = 5668750
    yillik_tutar = get_price_for_date(tarih1, mezuniyet_tutar_json_path)
    if yillik_tutar:
        # Calculate initial differences
        yillar = tarih1.year - tarih2.year
        aylar = tarih1.month - tarih2.month
        gunler = tarih1.day - tarih2.day

        # Adjust for negative days
        if gunler < 0:
            if tarih1.year % 4 == 0 and tarih1.month - 1 == 2:
                gunler += 29
                aylar -= 1
            elif tarih1.year % 4 != 0 and tarih1.month - 1 == 2:
                gunler += 28
                aylar -= 1
            elif tarih1.month - 1 == 1 or tarih1.month - 1 == 3 or tarih1.month - 1 == 5 or tarih1.month - 1 == 7 or tarih1.month - 1 == 8 or tarih1.month == 10 - 1 or tarih1.month -1 == 0:
                gunler += 31
                aylar -= 1
            else:
                gunler += 30
                aylar -= 1

        # Adjust for negative months
        if aylar < 0:
            aylar += 12
            yillar -= 1

        # If no experience certificate and years >= 15, cap at 15 years
        if not has_experience_cert and yillar >= 15:
            yillar = 15
            aylar = 0
            gunler = 0

        # Calculate updated amount
        guncel_tutar = (yillik_tutar * yillar) + \
                       (yillik_tutar * aylar / 12) + \
                       (yillik_tutar * gunler / (12 * 30))

        # Return both the amount and calculation details
        calc_details = {
            'yillar': yillar,
            'aylar': aylar,
            'gunler': gunler,
            'yillik_tutar': yillik_tutar
        }
        return round(guncel_tutar, 2), calc_details
    else:
        return (0, None)


def calculate_building_permit_amount(building_class, building_area, completion_percentage):
    """Calculate building permit amount based on class, area and completion"""
    unit_prices = {
        'I-A': 1000, 'I-B': 1200,
        'II-A': 1500, 'II-B': 1700, 'II-C': 1900,
        'III-A': 2200, 'III-B': 2500,
        'IV-A': 3000, 'IV-B': 3300, 'IV-C': 3600,
        'V-A': 4000, 'V-B': 4300, 'V-C': 4600, 'V-D': 5000
    }

    unit_price = unit_prices.get(building_class, 0)
    total_amount = unit_price * building_area * (completion_percentage / 100)
    return total_amount


def clean_ufe_data(data):
    """ÜFE verilerindeki format hatalarını düzeltir"""
    # cleaned_data = {}
    # for year in data:
    #     cleaned_data[year] = {}
    #     for month, value in data[year].items():
    #         str_value = str(int(value))
    #         if len(str_value) < 5:
    #             multiplier = 10 ** (5 - len(str_value))
    #             value = value * multiplier
    #         cleaned_data[year][month] = value
    cleaned_data = data
    return cleaned_data


def get_latest_index(data):
    """En son mevcut endeks verisini bulur"""
    latest_year = max(data.keys())
    latest_month = max(int(k) for k in data[latest_year].keys() if float(data[latest_year][k]) > 0)
    return latest_year, str(latest_month)


def get_previous_month_info(date):
    """Verilen tarih için önceki ayın bilgilerini döndürür"""
    previous_month = date.month - 1
    year = date.year

    if previous_month == 0:
        previous_month = 12
        year -= 1

    return year, previous_month


def calculate_ufe_ratio(basvuru_tarihi, sozlesme_tarihi, ufe_data):
    """İki tarih arasındaki ÜFE güncelleme oranını hesaplar"""
    # Tarihleri datetime objesine çevir
    if isinstance(basvuru_tarihi, date):
        basvuru = basvuru_tarihi
    else:
        basvuru = date.strptime(basvuru_tarihi, "%Y.%m.%d")

    if isinstance(sozlesme_tarihi, date):
        sozlesme = sozlesme_tarihi
    else:
        sozlesme = date.strptime(sozlesme_tarihi, "%Y.%m.%d")

    # Tarih kontrolü
    if basvuru <= sozlesme:
        raise ValueError("Başvuru tarihi, sözleşme tarihinden büyük olmalıdır!")

    # Verileri temizle
    cleaned_data = clean_ufe_data(ufe_data)

    # En son mevcut veriyi bul
    latest_year, latest_month = get_latest_index(cleaned_data)
    uyari_mesaji = ""

    # Başvuru ve sözleşme tarihleri için önceki ay bilgilerini al
    basvuru_endeks_yili, basvuru_endeks_ayi = get_previous_month_info(basvuru)
    sozlesme_endeks_yili, sozlesme_endeks_ayi = get_previous_month_info(sozlesme)

    kullanilan_endeksler = {
        'basvuru': {'yil': basvuru_endeks_yili, 'ay': basvuru_endeks_ayi},
        'sozlesme': {'yil': sozlesme_endeks_yili, 'ay': sozlesme_endeks_ayi}
    }
    print(kullanilan_endeksler)
    try:
        basvuru_endeks = cleaned_data[str(basvuru_endeks_yili)][str(basvuru_endeks_ayi)]
        if basvuru_endeks == 0:
            raise KeyError
    except (KeyError, TypeError):
        basvuru_endeks = cleaned_data[latest_year][latest_month]
        kullanilan_endeksler['basvuru'] = {'yil': int(latest_year), 'ay': int(latest_month)}
        uyari_mesaji += f"Başvuru tarihi için {basvuru_endeks_yili}/{basvuru_endeks_ayi} endeksi mevcut değil. "
        uyari_mesaji += f"En son mevcut endeks ({latest_year}/{latest_month}) kullanıldı. "

    try:
        sozlesme_endeks = cleaned_data[str(sozlesme_endeks_yili)][str(sozlesme_endeks_ayi)]
        if sozlesme_endeks == 0:
            raise KeyError
    except (KeyError, TypeError):
        sozlesme_endeks = cleaned_data[latest_year][latest_month]
        kullanilan_endeksler['sozlesme'] = {'yil': int(latest_year), 'ay': int(latest_month)}
        uyari_mesaji += f"Sözleşme tarihi için {sozlesme_endeks_yili}/{sozlesme_endeks_ayi} endeksi mevcut değil. "
        uyari_mesaji += f"En son mevcut endeks ({latest_year}/{latest_month}) kullanıldı. "
    print(basvuru_endeks, sozlesme_endeks)
    guncelleme_orani = float(basvuru_endeks) / float(sozlesme_endeks)
    return guncelleme_orani, uyari_mesaji, kullanilan_endeksler


def calculate_ekap_updated_amount(document_amount, ufe_ratio):
    """
    EKAP belgesi için güncel tutarı hesaplar.

    Args:
        document_amount (float): Belge tutarı
        ufe_ratio (float): UFE artış oranı

    Returns:
        float: Güncel belge tutarı (Belge tutarı + UFE artışı)
    """
    ufe_increase = document_amount * ufe_ratio
    # total_amount = document_amount + ufe_increase
    total_amount = ufe_increase
    return total_amount

def guncelle_belge_tutari(belge_tutari):
    """Update document amount with a fixed percentage increase"""
    guncel_tutar = belge_tutari * 1.5  # 50% increase
    return guncel_tutar


def validate_industrial_building_experience(industrial_type):
    """
    Validates if the industrial building experience can be used based on building type.

    Args:
        industrial_type (str): Type of industrial building experience

    Returns:
        tuple: (bool, str) - (is_valid, message)
    """
    if industrial_type == 'İş deneyimine tabi olmayan sanayi yapısı':
        return (False, "Yapı Müteahhitlerinin Sınıflandırılması ve Kayıtlarının Tutulması " +
                "Hakkında Yönetmelik 16. maddesinin 9. fıkrası uyarınca 13. Maddenin 2. " +
                "fıkrasının a bendinde belirtilen yapılardan II-C(2), III-A(11), III-B(1) " +
                "ve IV-A(10) grubu ile tek katlı I-B(4) ve III-A(6) grubu yapım işlerinden " +
                "elde edilmiş iş deneyim belgeleri kullanılabilir. Bu yapılar haricinde 13. " +
                "Maddenin 2. fıkrasının a bendinde belirtilen diğer yapılardan elde edilen " +
                "iş deneyim belgeleri kullanılamaz.")
    return (True, "")


def calculate_pre_2019_industrial_amount(document_amount):
    """
    Calculates the document amount for pre-2019 industrial buildings.

    Args:
        document_amount (float): Original document amount

    Returns:
        float: Calculated document amount (20% of original)
    """
    return document_amount * 0.20


def calculate_max_industrial_amount(approval_date, authority_group, teblig_tarih_secimi):
    """
    Calculates maximum allowed document amount based on approval date and authority group.
    This is a placeholder function - to be updated with actual logic later.

    Args:
        approval_date (datetime.date): Approval date of the building permit
        authority_group (str): Authority group at the time of approval

    Returns:
        float: Maximum allowed document amount
    """
    after_2019_parameters = json_dosyasini_oku()
    print(approval_date)
    period = donem_bul(approval_date, teblig_tarih_secimi)


    base_amount = tutar_bul(max_json_path, approval_date, authority_group, teblig_tarih_secimi)
    print(base_amount)
    return base_amount


def determine_industrial_document_amount(industrial_type, year_category, document_amount,
                                         approval_date=None, authority_group=None, is_building_owner=False,
                                         teblig_tarih_secimi="yayim"):
    """
    Determines the final document amount for industrial buildings based on various conditions.

    Args:
        industrial_type (str): Type of industrial building experience
        year_category (str): Pre or post 2019 category
        document_amount (float): Original document amount
        approval_date (datetime.date, optional): Approval date for post-2019 cases
        authority_group (str, optional): Authority group for post-2019 cases
        is_building_owner (bool): Whether the document owner is also the building owner
        teblig_tarih_secimi (str): Tebliğ tarih seçimi

    Returns:
        tuple: (float, str) - (final_amount, message)
    """
    # Check building owner status first
    if is_building_owner:
        return (0,
                "Yerleşik Kamu İhale Kurumu ve Yargı kararları uyarınca; Yapı müteahhidi, sözleşme tarihi ile yapı kullanma izin belgesi düzenleme tarihi arasında herhangi bir zaman diliminde taşınmazın hissedarı veya sahibi statüsünde olmuşsa, bu yapılar için EKAP İş Deneyim Belgesi düzenlenemez.")

    # Validate industrial building experience
    is_valid, message = validate_industrial_building_experience(industrial_type)
    if not is_valid:
        return (0, message)

    # Handle industrial building experience cases
    if industrial_type == 'İş deneyimine tabi sanayi yapısı':

        if year_category == '02/12/2019 Öncesi':
            # Pre-2019 case: Use 20% of document amount
            calculated_amount = calculate_pre_2019_industrial_amount(document_amount)
            return (calculated_amount,
                    f"Yönetmeliğin 16/9 maddesi uyarınca belge tutarı olarak belge tutarının %20'si alınmıştır.\n\nBelge Tutarı: {format_currency(calculated_amount)}\n")

        elif year_category == '02/12/2019 Sonrası':
            # Post-2019 case: Compare with maximum allowed amount
            max_amount_result = calculate_max_industrial_amount(approval_date, authority_group, teblig_tarih_secimi)

            # Check if maximum amount calculation was successful
            if not max_amount_result.get('success'):
                return (0, f"Maksimum tutar hesaplanamadı: {max_amount_result.get('error', 'Bilinmeyen hata')}")

            # Extract maximum amount from result
            max_amount = max_amount_result['data']['tutar']

            # Compare document amount with maximum allowed amount
            if document_amount <= max_amount:
                # User's amount is within limits
                final_amount = document_amount
                message = (
                    f"Ruhsat onay tarihi ({approval_date.strftime('%d.%m.%Y')}) tarihinde üstlenebilecek maksimum iş miktarı: {format_currency(max_amount)}\n"
                    f"Belge tutarı: {format_currency(document_amount)}\n"
                    f"Yönetmelik uyarınca belge tutarı olarak {format_currency(final_amount)} alınmıştır.")
            else:
                # User's amount exceeds maximum, use maximum
                final_amount = max_amount
                message = (
                    f"Ruhsat onay tarihi ({approval_date.strftime('%d.%m.%Y')}) tarihinde üstlenebilecek maksimum iş miktarı: {format_currency(max_amount)}\n"
                    f"Belge tutarı: {format_currency(document_amount)}\n"
                    f"Yönetmelik uyarınca belge tutarı olarak {format_currency(final_amount)} alınmıştır.")

            return (final_amount, message)

    # Default case: return original amount
    return (document_amount, "")