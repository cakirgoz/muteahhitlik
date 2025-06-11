def log_unit_price_ratio(params):
    return (
        f"📌 Birim Fiyat Oranı:\n"
        f"- Sözleşme dönemindeki yapı sınıfı birim fiyatı: {params['unit_price_contract']} ₺\n"
        f"- Başvuru dönemindeki yapı sınıfı birim fiyatı: {params['unit_price_application']} ₺\n"
        f"➡ Oran = {params['unit_price_ratio']:.4f}"
    )


def log_ufe_ratio(params):
    cp = params["contract_previous_month"]
    ap = params["application_previous_month"]

    return (
        f"📌 ÜFE Oranı:\n"
        f"- Sözleşme dönemi ({cp['year']}/{cp['month']}) ÜFE: {params['ufe_contract']}\n"
        f"- Başvuru dönemi ({ap['year']}/{ap['month']}) ÜFE: {params['ufe_application']}\n"
        f"➡ ÜFE Güncelleme Oranı = {params['ufe_update_ratio']:.4f}"
    )


def log_document_update_ratio(params):
    upr = params["unit_price_ratio"]
    ufe = params["ufe_update_ratio"]
    update = params["document_update_ratio"]

    min_limit = 0.9 * upr
    max_limit = 1.3 * upr

    if ufe < min_limit:
        return (
            f"📌 Belge Tutarı Güncelleme Oranı:\n"
            f"- ÜFE oranı = {ufe:.4f}, ancak bu değer birim fiyat oranının %90'ından küçük.\\\n"
            f"➡ Güncelleme oranı alt sınır olarak 0.9 × {upr:.4f} = {update:.6f} alınmıştır."
        )
    elif ufe > max_limit:
        return (
            f"📌 Belge Tutarı Güncelleme Oranı:\n"
            f"- ÜFE oranı = {ufe:.4f}, ancak bu değer birim fiyat oranının %130'undan büyük.\\\n"
            f"➡ Güncelleme oranı üst sınır olarak 1.3 × {upr:.4f} = {update:.6f} alınmıştır."
        )
    else:
        return (
            f"📌 Belge Tutarı Güncelleme Oranı:\\\n"
            f"- ÜFE oranı ({ufe:.6f}) sınırlar dahilinde olduğu için doğrudan kullanılmıştır."
        )

def log_base_amount(params):
    alan = params["building_area"]
    birim_maliyet = params["unit_price_contract"]
    oran = params["completion_percentage"]
    tutar = params["base_amount"]

    formula = r"""
$$
\text{yapi\_tutari} = \text{alan} \times \text{birim\_maliyet} \times \left(\frac{\text{tamamlanma\_yuzdesi}}{100}\right)
$$
"""

    explanation = (
        f"Yapı alanı = {alan:.2f} m², birim maliyet = {birim_maliyet:.2f} ₺, tamamlanma yüzdesi = %{oran:.2f}.\n"
        f"➡ Yapı tutarı = **{tutar:,.2f} ₺**"
    )

    return f"### 📌 Yapı Tutarı Hesabı\n{formula}\n\n{explanation}"

def log_contractor_base_amount(params):
    tutar = params["contractor_base_amount"]
    base_amount = params["base_amount"]
    is_industrial = params["is_industrial"]
    year_category = params.get("year_category")
    green = params.get("green_building_factor", 1.0)
    yuzde_20 = 0.20
    katsayi = 0.85 * green

    formula_normal = r"""
$$
\text{esas\_belge\_tutari} = 0.85 \times \text{yapi\_tutari} \times \text{yesil\_bina\_katsayisi}
$$
"""
    formula_2019_oncesi = r"""
$$
\text{esas\_belge\_tutari} = 0.20 \times \text{yapi\_tutari}
$$
"""
    formula_2019_sonrasi = r"""
$$
\text{esas\_belge\_tutari} = \min(\text{yapi\_tutari}, \text{sanayi\_ust\_limit})
$$
"""

    if is_industrial != "Evet":
        explanation = (
            f"Sanayi yapısı değil. 0.85 × yapı tutarı × yeşil bina katsayısı ({green}) uygulanmıştır.\n"
            f"➡ Müteahhitlik esas belge tutarı = **{tutar:,.2f} ₺**"
        )
        return f"### 📌 Müteahhitlik Belge Tutarı (Güncellenmemiş)\n{formula_normal}\n\n{explanation}"

    if year_category == "2019 Öncesi":
        explanation = (
            f"Sanayi yapısı (2019 öncesi). %20 oranı uygulanmıştır.\n"
            f"➡ Müteahhitlik esas belge tutarı = **{tutar:,.2f} ₺**"
        )
        return f"### 📌 Müteahhitlik Belge Tutarı (Güncellenmemiş)\n{formula_2019_oncesi}\n\n{explanation}"

    if year_category == "2019 Sonrası":
        max_limit = params["max_industrial_amount"]
        explanation = (
            f"Sanayi yapısı (2019 sonrası).\n"
            f"Yapı tutarı = {base_amount:,.2f} ₺, üst limit = {max_limit:,.2f} ₺.\n"
            f"➡ Seçilen tutar = **{tutar:,.2f} ₺** (küçük olan alındı)"
        )
        return f"### 📌 Müteahhitlik Belge Tutarı (Güncellenmemiş)\n{formula_2019_sonrasi}\n\n{explanation}"

    return "Sanayi yapı durumuna göre hesaplama yapılamadı."

def log_updated_contractor_amount(params):
    tutar = params["updated_contractor_amount"]
    base = params["contractor_base_amount"]
    guncelleme_orani = params["document_update_ratio"]

    formula = r"""
$$
\text{guncellenmis\_belge\_tutari} = \text{esas\_belge\_tutari} \times \text{belge\_guncelleme\_orani}
$$
"""

    explanation = (
        f"Güncellenmemiş belge tutarı = {base:,.2f} ₺, güncelleme oranı = {guncelleme_orani:.4f}\n"
        f"➡ Güncellenmiş belge tutarı = **{tutar:,.2f} ₺**"
    )

    return f"### 📌 Güncellenmiş Belge Tutarı\n{formula}\n\n{explanation}"

