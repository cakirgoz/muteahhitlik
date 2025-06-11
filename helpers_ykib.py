import json
from datetime import datetime


def validate_building_permit_inputs(params):
    errors = []

    if not params.get("contract_date"):
        errors.append("Contract date is missing.")
    if not params.get("acceptance_date"):
        errors.append("Acceptance date is missing.")
    if not params.get("building_area") or params["building_area"] == 0.0:
        errors.append("Building area cannot be zero.")

    if params.get("is_industrial") == "Evet":
        if params.get("industrial_type") == "İş deneyimine tabi olmayan sanayi yapısı":
            errors.append("İş deneyimine tabi olmayan sanayi yapıları müteahhitlik başvurularında kullanılamaz.")

        if params.get("year_category") == "2019 Sonrası":
            if not params.get("approval_date"):
                errors.append("Approval date is missing for industrial structure (post-2019).")
            if not params.get("authority_group"):
                errors.append("Authority group is missing for industrial structure (post-2019).")

    return errors
# def generate_building_permit_params(inputs):
#     return {
#         "application_date": inputs.get("application_date"),
#         "contract_date": inputs.get("contract_date"),
#         "acceptance_date": inputs.get("acceptance_date"),
#         "building_class": inputs.get("building_class"),
#         "building_class_application_date": inputs.get("building_class_application_date"),
#         "building_area": inputs.get("building_area"),
#         "completion_percentage": inputs.get("completion_percentage"),
#         "teblig_sinir_tarih_opsiyonu": inputs.get("teblig_sinir_tarih_opsiyonu"),
#         "is_industrial": inputs.get("is_industrial"),
#         "year_category": inputs.get("year_category"),
#         "percentage_selected": inputs.get("percentage_selected"),
#         "approval_date": inputs.get("approval_date"),
#         "authority_group": inputs.get("authority_group"),
#         "green_building": inputs.get("green_building"),
#
#     }

def generate_building_permit_params(inputs):
    return {
        "application_date": inputs.get("application_date"),
        "contract_date": inputs.get("contract_date"),
        "acceptance_date": inputs.get("acceptance_date"),
        "building_class": inputs.get("building_class"),
        "building_class_application_date": inputs.get("building_class_application_date"),
        "building_area": inputs.get("building_area"),
        "completion_percentage": inputs.get("completion_percentage"),
        "teblig_sinir_tarih_opsiyonu": inputs.get("teblig_sinir_tarih_opsiyonu"),
        "tarih_opsiyonu": inputs.get("tarih_opsiyonu"),  # 👈 burası yeni
        "is_industrial": inputs.get("is_industrial"),
        "industrial_type": inputs.get("industrial_type"),
        "year_category": inputs.get("year_category"),
        "percentage_selected": inputs.get("percentage_selected"),
        "approval_date": inputs.get("approval_date"),
        "authority_group": inputs.get("authority_group"),
        "green_building": inputs.get("green_building"),
    }


def get_unit_prices_for_building_classes(contract_date, application_date, building_class_contract,
                                         building_class_application, tarih_opsiyonu,
                                         json_path='birim_fiyatlar.json'):
    from datetime import datetime
    import json

    def date_in_range(date_obj, start_str, end_str):
        start = datetime.strptime(start_str, "%Y-%m-%d").date()
        end = datetime.strptime(end_str, "%Y-%m-%d").date()
        return start <= date_obj <= end

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if tarih_opsiyonu == "yayim":
        field_start = "yayim_tarihi"
        field_end = "yayim_sonu"
    else:
        field_start = "gecerlilik_tarihi"
        field_end = "gecerlilik_sonu"

    contract_unit_price = None
    application_unit_price = None

    for record in data:
        # Sözleşme tarihi dönemi
        if contract_unit_price is None and date_in_range(contract_date, record[field_start], record[field_end]):
            price = record["data"].get(building_class_contract)
            if price is None:
                raise ValueError(f"Seçilen tarih için seçmiş olduğunuz {building_class_contract} yapı sınıfı bulunamamıştır, girdiğiniz tarihi veya yapı sınıfını kontrol ediniz.")
            contract_unit_price = price

        # Başvuru tarihi dönemi
        if application_unit_price is None and date_in_range(application_date, record[field_start], record[field_end]):
            price = record["data"].get(building_class_application)
            if price is None:
                raise ValueError(f"Seçilen tarih için seçmiş olduğunuz {building_class_application} yapı sınıfı bulunamamıştır, girdiğiniz tarihi veya yapı sınıfını kontrol ediniz.")
            application_unit_price = price

        # Erken çıkmak için
        if contract_unit_price is not None and application_unit_price is not None:
            break

    if contract_unit_price is None:
        raise ValueError(f"Seçilen tarih için seçmiş olduğunuz {building_class_contract} yapı sınıfı bulunamamıştır, girdiğiniz tarihi veya yapı sınıfını kontrol ediniz.")
    if application_unit_price is None:
        raise ValueError(f"Seçilen tarih için seçmiş olduğunuz {building_class_application} yapı sınıfı bulunamamıştır, girdiğiniz tarihi veya yapı sınıfını kontrol ediniz.")

    unit_price_ratio = application_unit_price / contract_unit_price

    return {
        "unit_price_contract": contract_unit_price,
        "unit_price_application": application_unit_price,
        "unit_price_ratio": unit_price_ratio
    }


def get_max_industrial_amount(approval_date, authority_group, tarih_opsiyonu, json_path="max_is_tutari.json"):
    def date_in_range(date_obj, start_str, end_str):
        start = datetime.strptime(start_str, "%Y-%m-%d").date()
        end = datetime.strptime(end_str, "%Y-%m-%d").date()
        return start <= date_obj <= end

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if tarih_opsiyonu == "yayim":
        field_start = "yayim_tarihi"
        field_end = "yayim_sonu"
    else:
        field_start = "gecerlilik_tarihi"
        field_end = "gecerlilik_sonu"

    for record in data:
        if date_in_range(approval_date, record[field_start], record[field_end]):
            amount = record["tutarlar"].get(authority_group)
            if amount is None:
                raise ValueError(f"Belirtilen tarihte belirtilen {authority_group} belge grubu bulunamamıştır. Girdiğiniz tarihi veya belge grubunu kontrol ediniz.")
            return amount

    raise ValueError(f"Belirtilen tarihte belirtilen {authority_group} belge grubu bulunamamıştır. Girdiğiniz tarihi veya belge grubunu kontrol ediniz.")

def get_previous_month_info(date_obj):
    year = date_obj.year
    month = date_obj.month

    if month == 1:
        return {"year": year - 1, "month": 12}
    else:
        return {"year": year, "month": month - 1}


def get_ufe_data_and_ratio(contract_month_info, application_month_info, json_path='yi_ufe_data.json'):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    year_contract = str(contract_month_info["year"])
    month_contract = str(contract_month_info["month"])
    year_application = str(application_month_info["year"])
    month_application = str(application_month_info["month"])

    try:
        ufe_contract = data[year_contract][month_contract]
    except KeyError:
        raise ValueError(f"ÜFE verisi bulunamadı: {year_contract}/{month_contract}")

    try:
        ufe_application = data[year_application][month_application]
    except KeyError:
        raise ValueError(f"ÜFE verisi bulunamadı: {year_application}/{month_application}")

    try:
        ufe_update_ratio = ufe_application / ufe_contract
    except ZeroDivisionError:
        raise ValueError("Sözleşme dönemine ait ÜFE verisi sıfır, oran hesaplanamıyor.")

    return {
        "ufe_contract": ufe_contract,
        "ufe_application": ufe_application,
        "ufe_update_ratio": ufe_update_ratio
    }

def calculate_document_update_ratio(params):
    upr = params.get("unit_price_ratio")
    ufe = params.get("ufe_update_ratio")

    if upr is None or ufe is None:
        raise ValueError("Güncelleme oranı hesaplanamıyor. unit_price_ratio ve ufe_update_ratio gereklidir.")

    min_allowed = 0.9 * upr
    max_allowed = 1.3 * upr

    if ufe < min_allowed:
        return min_allowed
    elif ufe > max_allowed:
        return max_allowed
    else:
        return ufe



def get_green_building_factor(green_building_selected):
    return 1.05 if green_building_selected else 1.0


def calculate_base_amount(params):
    area = params.get("building_area")
    unit_price = params.get("unit_price_contract")
    completion = params.get("completion_percentage")

    if area is None or unit_price is None or completion is None:
        raise ValueError("Base amount hesaplamak için building_area, unit_price_contract ve completion_percentage gereklidir.")

    return area * unit_price * (completion / 100)

def calculate_contractor_base_amount(params):
    base_amount = params.get("base_amount")
    green_factor = params.get("green_building_factor", 1.0)
    is_industrial = params.get("is_industrial")
    year_category = params.get("year_category")

    if base_amount is None:
        raise ValueError("Base amount gereklidir.")

    # Sanayi yapısı değilse
    if is_industrial != "Evet":
        return 0.85 * base_amount * green_factor

    # Sanayi yapısı ve 2019 öncesi
    if year_category == "2019 Öncesi":
        return 0.20 * base_amount

    # Sanayi yapısı ve 2019 sonrası
    if year_category == "2019 Sonrası":
        max_amount = params.get("max_industrial_amount")
        if max_amount is None:
            raise ValueError("max_industrial_amount değeri gerekli.")
        return min(base_amount, max_amount)

    # Diğer tüm durumlar
    raise ValueError("Müteahhitlik belge tutarı hesaplaması için gerekli bilgiler eksik.")

def calculate_updated_contractor_amount(params):
    base = params.get("contractor_base_amount")
    update_ratio = params.get("document_update_ratio")

    if base is None or update_ratio is None:
        raise ValueError("Güncellenmiş belge tutarı hesaplamak için contractor_base_amount ve document_update_ratio gereklidir.")

    return base * update_ratio


