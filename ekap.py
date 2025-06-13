rapor_log = []
import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
import os
from datetime import datetime, timedelta


from helpers_ekap import (
    format_currency,
    format_date,
    validate_dates,
    mezuniyet_guncelle,
    calculate_building_permit_amount,
    guncelle_belge_tutari,
    calculate_ufe_ratio,
    calculate_ekap_updated_amount,
    # Yeni eklenen fonksiyonlar
    validate_industrial_building_experience,
    calculate_pre_2019_industrial_amount,
    calculate_max_industrial_amount,
    determine_industrial_document_amount
)

from helpers_ykib import (
    validate_building_permit_inputs,
    generate_building_permit_params,
    get_unit_prices_for_building_classes,
    get_max_industrial_amount,
    get_previous_month_info,
    get_ufe_data_and_ratio,
    calculate_document_update_ratio,
    get_green_building_factor,
    calculate_base_amount,
    calculate_contractor_base_amount,
    calculate_updated_contractor_amount,
    get_unit_prices_for_building_classes_tutara_esas
)

from rapor_helpers import (
    log_unit_price_ratio,
    log_ufe_ratio,
    log_document_update_ratio,
    log_base_amount,
    log_contractor_base_amount,
    log_updated_contractor_amount
)

# json paths
current_dir = os.path.dirname(os.path.abspath(__file__))
json_path_max = os.path.join(current_dir, 'max_is_tutari.json')
json_path_birim_fiyat = os.path.join(current_dir, 'birim_fiyatlar.json')
json_path_ufe_data = os.path.join(current_dir, 'yi_ufe_data.json')



st.title('İş Deneyimi Girişi')

# Session state variables
if 'data' not in st.session_state:
    st.session_state['data'] = []
if 'calculated_amount' not in st.session_state:
    st.session_state['calculated_amount'] = None
if 'counter' not in st.session_state:
    st.session_state['counter'] = 0
if 'document_amount' not in st.session_state:
    st.session_state['document_amount'] = ''

# Experience type selection
experience_type = st.selectbox(
    "İş Deneyimi Türünü Seçin",
    ("EKAP İş Deneyim Belgesi Ekle", "Mezuniyet Belgesi Ekle", "Yapı Kullanma İzin Belgesi Ekle")
)

# Application date
today = date.today()
application_date = st.date_input(
    'Başvuru Tarihi',
    min_value=date(2000, 1, 1),
    value=today,
    format="DD.MM.YYYY"
)

if experience_type == "Mezuniyet Belgesi Ekle":
    # Create two columns for graduation date and department
    col1, col2 = st.columns(2)

    with col1:
        graduation_date = st.date_input(
            'Mezuniyet Tarihi',
            min_value=date(1950, 1, 1),
            value=None,
            format = "DD.MM.YYYY"
        )
    print(graduation_date)
    print(type(graduation_date))
    with col2:
        graduation_department = st.selectbox(
            'Mezun Olunan Bölüm',
            ["İnşaat Mühendisliği/Mimarlık", "Diğer Bölümler"]
        )

    # Add experience certificate checkbox on the next line
    has_experience_certificate = st.checkbox('İş Deneyim Belgesi mevcut.')

    calculate_button = st.button('Hesapla')
    if calculate_button:
        if graduation_department == "Diğer Bölümler":
            st.error(
                "Yönetmeliğin 13/2/a hükmü uyarınca: Mezuniyet belgeleri bakımından inşaat mühendisliği ve mimarlık bölümleri benzer iş grubuna denk sayılır. İnşaat mühendisliği ve mimarlık bölümleri haricinde mezuniyet belgesi iş deneyimi olarak dikkate alınmaz.")
            st.stop()

        if graduation_date is None:
            st.error('Lütfen mezuniyet tarihini giriniz.')
            st.stop()

        # Check if graduation date is valid (not in the future)
        if graduation_date > application_date:
            st.error('Mezuniyet tarihi başvuru tarihinden sonra olamaz.')
            st.stop()

        # For graduation certificates, we use a different validation approach
        # since we don't have contract and acceptance dates
        tutar, calc_details = mezuniyet_guncelle(
            application_date,
            graduation_date,
            has_experience_certificate
        )
        formatted_amount = format_currency(tutar)
        st.session_state['calculated_amount'] = formatted_amount

        print(calc_details)
        if not calc_details:
            st.error("Mezuniyet Belgesi ile İş Deneyim Tutarı Hesabı 03.10.2020 ve sonrası başvurular için yapılmaktadır.")
            # st.info("dfsdfsd")
        else:
            # Display results
            st.success(f'Güncel Belge Tutarı: {formatted_amount}')
            st.info(
                f"Başvuru tarihinde geçerli yıllık Mezuniyet Belgesi tutarı: {format_currency(calc_details['yillik_tutar'])}\n\n"
                f"Hesaplamaya esas Yıl: {calc_details['yillar']} Yıl, \n\n"
                f"Hesaplamaya esas Ay: {calc_details['aylar']} Ay, \n\n"
                f"Hesaplamaya esas Gün: {calc_details['gunler']} Gün\n\n"
                f"Belge Tutarı = ({format_currency(calc_details['yillik_tutar'])} X {calc_details['yillar']}) + ({format_currency(calc_details['yillik_tutar'])} X {calc_details['aylar']} / 12 )+ ({format_currency(calc_details['yillik_tutar'])} X {calc_details['gunler']} /12/30 )\n\n"
                f"Belge Tutarı: {formatted_amount}"
            )

elif experience_type == "Yapı Kullanma İzin Belgesi Ekle":
    col1, col2 = st.columns(2)

    with col1:
        contract_date = st.date_input('Sözleşme Tarihi', min_value=date(2000, 1, 1), value=None, format="DD.MM.YYYY")
        building_class = st.selectbox('Sözleşme Tarihindeki Yapı Sınıfı', [
            'I-A', 'I-B', 'II-A', 'II-B', 'II-C',
            'III-A', 'III-B', 'III-C', 'IV-A', 'IV-B', 'IV-C',
            'V-A', 'V-B', 'V-C', 'V-D'
        ])
        building_area = st.number_input('Yapı Alanı (m²)', min_value=0.0, value=0.0)
        green_building = st.checkbox("Yeşil Bina Sertifikası Düzenlenmiş Yapı mı?")

        is_industrial = st.radio("Sanayi Yapısı mı?", ["Hayır", "Evet"], horizontal=True)

    with col2:
        acceptance_date = st.date_input('Geçici Kabul/İskan Tarihi',
                                        min_value=date(2000, 1, 1), value=None, format="DD.MM.YYYY")
        building_class_application_dat = st.selectbox('Başvuru Tarihindeki Yapı Sınıfı', [
            'I-A', 'I-B', 'II-A', 'II-B', 'II-C',
            'III-A', 'III-B', 'IV-A', 'IV-B', 'IV-C',
            'V-A', 'V-B', 'V-C', 'V-D'
        ],help="Başvuru tarihindeki yapı sınıfının sözleşme tarihindeki yapı sınıfından farklı olması durumunda farklı işaretlenebilir.\\\nAksi halde sözleşme tarihindeki yapı sınıfı ile aynı olması gerekmektedir.")
        completion_percentage = st.number_input('Tamamlanma Yüzdesi (%)',
                                                min_value=0.0, max_value=100.0,
                                                value=100.0, step=0.1)
        teblig_sinir_tarih_opsiyonu = st.radio(
            'Yapı Yaklaşık Birim Maliyetleri Tarih Geçerlilik Seçeneği:',
            ['Tebliğ yayımlanma tarihi esas alınsın.', 'Tebliğde belirtilen geçerlilik süresi esas alınsın.'],
            horizontal=False,
            help="Yapı ruhsatı onay tarihini seçin"
        )
        if teblig_sinir_tarih_opsiyonu == 'Tebliğ yayımlanma tarihi esas alınsın.':
            tarih_opsiyonu = "yayim"
        else:
            tarih_opsiyonu = "gecerlilik"

    if is_industrial == "Evet":
        if is_industrial:
            industrial_type = st.radio(
                'Sanayi Yapısı Tipi',
                ['İş deneyimine tabi sanayi yapısı', 'İş deneyimine tabi olmayan sanayi yapısı'],
                horizontal=True,
                help="Sanayi yapısının iş deneyimine tabi olup olmadığını seçin"
            )

        year_category = st.radio("", ["2019 Öncesi", "2019 Sonrası"], horizontal=True)

        if year_category == "2019 Öncesi":
            st.session_state.percentage_selected = st.checkbox("Belge Tutarı %20'si", value=True)

        if year_category == "2019 Sonrası":
            approval_date = st.date_input('Ruhsat Onay Tarihi',
                                          min_value=date(2000, 1, 1), value=None, format="DD.MM.YYYY")
            print(approval_date )
            authority_group = st.selectbox('Ruhsat Onay Tarihindeki Yetki Belge Grubu',
                                           ['A', 'B', 'B1', 'C', 'C1', 'D', 'D1', 'E', 'E1',
                                            'F', 'F1', 'G', 'G1', 'H'])

    col3, col4 = st.columns(2)
    with col3:
        calculate_base_button = st.button('Belge Tutarı Hesapla')
    with col4:
        # update_button = st.button('Güncelle')
        pass

    if calculate_base_button:
        # Kullanıcı verilerini dictionary olarak hazırla (sadece girdilerle)
        raw_inputs = {
            "application_date": application_date,
            "contract_date": contract_date,
            "acceptance_date": acceptance_date,
            "building_class": building_class,
            "building_class_application_date": building_class_application_dat,
            "building_area": building_area,
            "completion_percentage": completion_percentage,
            "teblig_sinir_tarih_opsiyonu": teblig_sinir_tarih_opsiyonu,
            "is_industrial": is_industrial,
            "year_category": year_category if is_industrial == "Evet" else None,
            "percentage_selected": (
                st.session_state.get(
                    "percentage_selected") if is_industrial == "Evet" and year_category == "2019 Öncesi" else None
            ),
            "approval_date": approval_date if is_industrial == "Evet" and year_category == "2019 Sonrası" else None,
            "authority_group": authority_group if is_industrial == "Evet" and year_category == "2019 Sonrası" else None,
            "green_building": green_building,
            "industrial_type": industrial_type if is_industrial == "Evet" else None,
            "tarih_opsiyonu": tarih_opsiyonu,
            "tarih_opsiyonu_gercerlilik": "gecerlilik",
        }

        # Doğrulama
        errors = validate_building_permit_inputs(raw_inputs)
        if errors:
            for error in errors:
                st.error(error)
            st.stop()


        # Tüm parametreleri içeren sabit yapıyı oluştur
        params = generate_building_permit_params(raw_inputs)

        try:
            unit_prices = get_unit_prices_for_building_classes(
                contract_date=params["contract_date"],
                application_date=params["application_date"],
                building_class_contract=params["building_class"],
                building_class_application=params["building_class_application_date"],
                tarih_opsiyonu=params["tarih_opsiyonu"],
                # json_path='birim_fiyatlar.json',
                json_path=json_path_birim_fiyat
            )
            params.update(unit_prices)
        except ValueError as e:
            st.error(str(e))
            st.stop()

        rapor_log.append(log_unit_price_ratio(params))

        try:
            unit_prices = get_unit_prices_for_building_classes_tutara_esas(
                contract_date=params["contract_date"],
                building_class_contract=params["building_class"],
                tarih_opsiyonu='gecerlilik',
                json_path=json_path_birim_fiyat
            )
            params.update(unit_prices)
        except ValueError as e:
            st.error(str(e))
            st.stop()


        if params["is_industrial"] == "Evet" and params["year_category"] == "2019 Sonrası":
            try:
                max_amount = get_max_industrial_amount(
                    approval_date=params["approval_date"],
                    authority_group=params["authority_group"],
                    tarih_opsiyonu=params["tarih_opsiyonu"],
                    # json_path="max_is_tutari.json",
                    json_path=json_path_max
                )
                params["max_industrial_amount"] = max_amount
            except ValueError as e:
                st.error(str(e))
                st.stop()

        params["contract_previous_month"] = get_previous_month_info(params["contract_date"])
        params["application_previous_month"] = get_previous_month_info(params["application_date"])

        try:
            ufe_data = get_ufe_data_and_ratio(
                contract_month_info=params["contract_previous_month"],
                application_month_info=params["application_previous_month"],
                # json_path="yi_ufe_data.json",
                json_path=json_path_ufe_data
            )
            params.update(ufe_data)
        except ValueError as e:
            st.error(str(e))
            st.stop()

        rapor_log.append(log_ufe_ratio(params))

        try:
            update_ratio = calculate_document_update_ratio(params)
            params["document_update_ratio"] = update_ratio
        except ValueError as e:
            st.error(str(e))
            st.stop()

        rapor_log.append(log_document_update_ratio(params))

        green_factor = get_green_building_factor(params.get("green_building"))
        params["green_building_factor"] = green_factor

        try:
            base_amount = calculate_base_amount(params)
            params["base_amount"] = base_amount
        except ValueError as e:
            st.error(str(e))
            st.stop()

        rapor_log.append(log_base_amount(params))

        try:
            contractor_amount = calculate_contractor_base_amount(params)
            params["contractor_base_amount"] = contractor_amount
        except ValueError as e:
            st.error(str(e))
            st.stop()

        rapor_log.append(log_contractor_base_amount(params))

        try:
            updated_amount = calculate_updated_contractor_amount(params)
            params["updated_contractor_amount"] = updated_amount
            updated_amount_formatted = format_currency(updated_amount)
        except ValueError as e:
            st.error(str(e))
            st.stop()

        rapor_log.append(log_updated_contractor_amount(params))

        st.success("Tüm kontroller sağlandı, hesaplamalar yapıldı.")
        st.success(f'Güncel Belge Tutarı: {updated_amount_formatted}')

        with st.expander("📄 Hesaplama Detaylarını Göster", expanded=False):
            st.markdown("### 📄 Açıklamalı Hesaplama Adımları")
            for entry in rapor_log:
                st.markdown(entry)
                st.markdown("---")

        with st.expander("🧮 Hesaplama Parametrelerini Göster", expanded=False):
            st.markdown("### 📄 Hesap Parametreleri")
            params_pretty = json.dumps(params, indent=4, ensure_ascii=False, default=str)
            st.code(params_pretty, language="json")

        # st.write("### Params")
        # st.json(params)
        #
        # st.markdown("### 📄 Açıklamalı Hesaplama Adımları")
        # for entry in rapor_log:
        #     st.markdown(entry)


else:  # EKAP İş Deneyim Belgesi Ekle
    # Sözleşme Tarihi ve Geçici Kabul/İskan Tarihi
    col1, col2 = st.columns(2)
    with col1:
        contract_date = st.date_input('Sözleşme Tarihi', min_value=date(2000, 1, 1), value=None, format="DD.MM.YYYY")
    with col2:
        acceptance_date = st.date_input('Geçici Kabul/İskan Tarihi', min_value=date(2000, 1, 1), value=None, format="DD.MM.YYYY")

    # İlk Sözleşme Bedeli ve Belge Tutarı
    col1, col2 = st.columns(2)
    with col1:
        initial_amount = st.number_input('İlk Sözleşme Bedeli', min_value=0.0, value=0.0, step=1.0)
    with col2:
        document_amount = st.number_input('Belge Tutarı', min_value=0.0, value=0.0, step=1.0)

    # Bir satırda 4 alan: Belge tutarının %85'i, Yeşil Bina Sertifikası, Ortak Girişim, Oran
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        take_85_percent = st.checkbox('Belge tutarının %85\'ini al.',
                                      help="Belge tutarının %85'i alınması gereken, ancak %85'i alınmadan düzenlenen Ekap iş deneyim belgelerinde işaretlenmesi gerekmektedir.")
    with col2:
        green_building = st.checkbox("Yeşil Bina Sertifikası Düzenlenmiş Yapı mı?")
    with col3:
        joint_venture = st.checkbox("Belge Ortak Girişim Olarak mı Alınmış?")
    with col4:
        if joint_venture:
            venture_ratio = st.number_input("Ortak Girişim Oranı (%)", min_value=0.0, value=0.0, step=1.0)
            print(venture_ratio)
            print(type(venture_ratio))
        else:
            st.write("-")

    # Esas Unsur Yüzdesi ve Adına EKAP seçeneği aynı satırda
    col1, col2 = st.columns(2)
    with col1:
        essential_element_percentage = st.number_input("Esas Unsur Yüzdesi (%)", min_value=0.0, value=100.0, step=1.0)
    with col2:
        is_building_owner = st.checkbox(
            'Adına EKAP iş deneyim belgesi düzenlenen aynı zamanda kısmen veya tamamen yapı sahibi.',
            help="Yapı müteahhidi, sözleşme tarihi ile yapı kullanma izin belgesi tarihi arasında herhangi bir zaman diliminde taşınmazın hissedarı veya sahibi statütüsünde olmuşsa, bu yapılar için EKAP İş Deneyim Belgesi düzenlenemez.")

    # Sanayi Yapısı mı?
    is_industrial = st.checkbox('Sanayi Yapısı mı?',
                                help="Sanayi yapısının iş deneyimine tabi olup olmadığını seçin")

    if is_industrial:
        industrial_type = st.radio(
            'Sanayi Yapısı Tipi',
            ['İş deneyimine tabi sanayi yapısı', 'İş deneyimine tabi olmayan sanayi yapısı'],
            horizontal=True,
            help="Sanayi yapısının iş deneyimine tabi olup olmadığını seçin"
        )

        if industrial_type == 'İş deneyimine tabi sanayi yapısı':
            st.caption("Bu, iş deneyimi şartı aranan sanayi yapıları için geçerlidir. 1")
        if industrial_type == 'İş deneyimine tabi olmayan sanayi yapısı':
            st.caption("Bu, iş deneyimi şartı aranan sanayi yapıları için geçerlidir. 2")

        year_category = st.radio(
            'Yapı Ruhsatı Onay Tarihi',
            ['02/12/2019 Öncesi', '02/12/2019 Sonrası'],
            horizontal=True,
            help="Yapı ruhsatı onay tarihini seçin"
        )

        if year_category == '02/12/2019 Sonrası':
            col5, col6 = st.columns(2)
            with col5:
                approval_date = st.date_input(
                    'Yapı Ruhsatı Onay Tarihi',
                    value=date(2019, 12, 2),
                    min_value=date(2019, 12, 2),
                    format="DD.MM.YYYY",
                    help="Yapı ruhsatının onay tarihini seçin"
                )
            with col6:
                authority_group = st.selectbox(
                    'Ruhsat Onay Tarihindeki Belge Grubu',
                    ['A', 'B', 'B1', 'C', 'C1', 'D', 'D1', 'E', 'E1', 'F', 'F1', 'G', 'G1', 'H'],
                    help="Ruhsat onay tarihindeki belge grubunu seçin"
                )
            teblig_sinir_tarih_opsiyonu = st.radio(
                'Yapı Yaklaşık Birim Maliyetleri Tarih Geçerlilik Seçeneği:',
                ['Teblig yayimlanma tarihi esas alinsin', 'Tebligde belirtilen gecerlilik suresi esas alınsın.'],
                horizontal=False,
                help="Yapı ruhsatı onay tarihini seçin"
            )
            if teblig_sinir_tarih_opsiyonu == 'Teblig yayimlanma tarihi esas alinsin':
                teblig_tarih_secimi = "yayim"
                print("yes")
            else:
                teblig_tarih_secimi = "gecerlilik"

    if st.button('Hesapla'):
        if is_building_owner:
            st.error(
                "Yerleşik Kamu İhale Kurumu ve Yargı kararları uyarınca; Yapı müteahhidi, yapı ruhsatı ile yapı kullanma izin belgesi düzenleme tarihleri arasında herhangi bir zaman diliminde taşınmazın hissedarı veya sahibi statüsünde olmuşsa, bu yapılar için EKAP İş Deneyim Belgesi düzenlenemez.")
            st.stop()

        if None not in (contract_date, acceptance_date) and 0.0 not in (initial_amount, document_amount):
            try:
                # current_dir = os.path.dirname(os.path.abspath(__file__))
                json_path = json_path_ufe_data

                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        ufe_data = json.load(f)
                except FileNotFoundError:
                    st.error(f"UFE veri dosyası bulunamadı: {json_path}")
                    st.error("Lütfen 'yi_ufe_data.json' dosyasının uygulama klasöründe olduğundan emin olun.")
                    st.stop()

                # Handle industrial building cases
                if is_industrial:
                    # İş deneyimine tabi olmayan sanayi yapısı kontrolü
                    if industrial_type == 'İş deneyimine tabi olmayan sanayi yapısı':
                        st.error(
                            "Yapı Müteahhitlerinin Sınıflandırılması ve Kayıtlarının Tutulması Hakkında Yönetmelik 16. maddesinin 9. fıkrası uyarınca 13. Maddenin 2. fıkrasının a bendinde belirtilen yapılardan II-C(2), III-A(11), III-B(1) ve IV-A(10) grubu ile tek katlı I-B(4) ve III-A(6) grubu yapım işlerinden elde edilmiş iş deneyim belgeleri kullanılabilir. Bu yapılar haricinde 13. Maddenin 2. fıkrasının a bendinde belirtilen diğer yapılardan elde edilen iş deneyim belgeleri kullanılamaz."
                        )
                        st.stop()

                    # Sanayi yapısı ve 02/12/2019 sonrası kontrolü (sadece iş deneyimine tabi olanlar için)
                    if industrial_type == 'İş deneyimine tabi sanayi yapısı' and year_category == '02/12/2019 Sonrası' and approval_date:
                        # Belirli belge grupları için tarih kontrolü
                        restricted_groups = ['B1', 'C1', 'D1', 'E1', 'F1', 'G1']
                        cutoff_date = datetime(2020, 10, 3).date()

                        if authority_group in restricted_groups and approval_date < cutoff_date:
                            formatted_date = approval_date.strftime('%d.%m.%Y')
                            st.error(
                                f"Ruhsat onay tarihi olan {formatted_date} tarihinde {authority_group} belge grubu yürürlükte bulunmamaktadır.\n"
                                f"Girmiş olduğunuz \"Ruhsat onay tarihi\" veya \"Ruhsat onay tarihindeki belge grubu\" bilgilerini kontrol edin!!!"
                            )
                            st.stop()

                    # Orijinal belge tutarını sakla ve hesaplama detaylarını takip et
                    original_document_amount = document_amount
                    calculation_details = []

                    # %85 hesaplaması
                    if take_85_percent:
                        document_amount = document_amount * 0.85
                        calculation_details.append("85% oranı uygulandı")

                    # Yeşil bina hesaplaması
                    if green_building:
                        document_amount = document_amount * 1.05
                        calculation_details.append("Yeşil bina artırımı (%5) uygulandı")

                    # Esas unsur yüzdesi hesaplaması (her durumda uygula)
                    if essential_element_percentage != 100:
                        document_amount = document_amount * (essential_element_percentage / 100)
                        calculation_details.append(f"Esas unsur yüzdesi ({essential_element_percentage}%) uygulandı")

                    # Ortaklık oranı hesaplaması
                    if joint_venture and venture_ratio != 100:
                        document_amount = document_amount * (venture_ratio / 100)
                        calculation_details.append(f"Ortaklık oranı ({venture_ratio}%) uygulandı")

                    # Hesaplanan belge tutarını sakla
                    calculated_document_amount = document_amount

                    # Fonksiyonu çağır (sadece iş deneyimine tabi sanayi yapıları için)
                    if industrial_type == 'İş deneyimine tabi sanayi yapısı':
                        final_document_amount, base_message = determine_industrial_document_amount(
                            industrial_type,
                            year_category,
                            document_amount,
                            approval_date if year_category == '02/12/2019 Sonrası' else None,
                            authority_group if year_category == '02/12/2019 Sonrası' else None,
                            is_building_owner,
                            teblig_tarih_secimi if year_category == '02/12/2019 Sonrası' else None,
                        )

                        # Detaylı mesaj oluştur - Resimdeki format tamamen
                        if base_message and year_category == '02/12/2019 Sonrası':
                            detailed_message = "**📊 HESAPLAMA DETAYLARI**\n\n"

                            # 1. GRUP: Kullanıcı tarafından girişi yapılan bilgiler
                            detailed_message += "**Kullanıcı tarafından girişi yapılan bilgiler:**\n\n"
                            detailed_message += f"• Başvuru Tarihi: {application_date.strftime('%d.%m.%Y') if 'application_date' in locals() else 'Belirtilmemiş'}\n\n"
                            detailed_message += f"• Sözleşme Tarihi: {contract_date.strftime('%d.%m.%Y') if 'contract_date' in locals() else 'Belirtilmemiş'}\n\n"
                            detailed_message += f"• Geçici Kabul/İskan Tarihi: {acceptance_date.strftime('%d.%m.%Y') if 'acceptance_date' in locals() else 'Belirtilmemiş'}\n\n"
                            detailed_message += f"• Belge Tutarı (A): {format_currency(original_document_amount)}\n\n"
                            detailed_message += f"• Belge tutarının %85'ini al: {'Evet' if take_85_percent else 'Hayır'}\n\n"
                            detailed_message += f"• Yeşil Bina Sertifikası: {'Evet' if green_building else 'Hayır'}\n\n"
                            detailed_message += f"• Ortak Girişim Oranı (%) (B): %{venture_ratio if joint_venture else '100.0'}\n\n"
                            detailed_message += f"• Esas Unsur Yüzdesi (%) (C): %{essential_element_percentage}\n\n"
                            detailed_message += f"• Yapı Sahibi veya Hissedar mı?: {'Evet' if is_building_owner else 'Hayır'}\n\n"
                            detailed_message += f"• Yapı Ruhsatı Onay Tarihi: {approval_date.strftime('%d.%m.%Y') if approval_date else 'Belirtilmemiş'}\n\n"
                            detailed_message += f"• Ruhsat Onay Tarihindeki Belge Grubu: {authority_group if authority_group else 'Belirtilmemiş'}\n\n"
                            detailed_message += f"• Yapı Yaklaşık Birim Maliyetleri Tarih Geçerlilik Seçeneği: {teblig_tarih_secimi if teblig_tarih_secimi else 'Belirtilmemiş'}\n\n"

                            # 2. GRUP: Müteahhitlik Belge Grubuna Esas Belge Tutarı hesabı
                            detailed_message += "**Müteahhitlik Belge Grubuna Esas Belge Tutarı hesabı:**\n\n"
                            detailed_message += f"• A: Belge Tutarı = {format_currency(original_document_amount)}\n\n"
                            detailed_message += f"• B: Ortak Girişim Oranı (%) = %{venture_ratio if joint_venture else '100.0'} = {venture_ratio / 100 if joint_venture else 1.0}\n\n"
                            detailed_message += f"• C: Esas Unsur Yüzdesi (%) = %{essential_element_percentage} = {essential_element_percentage / 100}\n\n"
                            detailed_message += f"• D: Belge tutarının %85'ini al katsayısı = {'0.85' if take_85_percent else '1.0'}\n\n"
                            detailed_message += f"• E: Yeşil Bina Sertifikası katsayısı = {'1.05' if green_building else '1.0'}\n\n"

                            # 3. GRUP: Güncellenmemiş Belge Tutarı hesaplaması
                            # Formül değerleri
                            b_value = venture_ratio / 100 if joint_venture else 1.0
                            c_value = essential_element_percentage / 100
                            d_value = 0.85 if take_85_percent else 1.0
                            e_value = 1.05 if green_building else 1.0

                            detailed_message += f"**Güncellenmemiş Belge Tutarı = A × B × C × D × E = {format_currency(original_document_amount)} × {b_value} × {c_value} × {d_value} × {e_value} = {format_currency(calculated_document_amount)}**\n\n"

                            # 4. GRUP: İş Deneyim Tutarı Tespiti (Sadece gerekli durumlarda)
                            work_experience_amount = calculated_document_amount  # Varsayılan değer
                            if approval_date and authority_group:
                                detailed_message += "**İş Deneyim Tutarı Tutarı Tespiti (Yönetmelik Madde 16/9):**\n\n"
                                detailed_message += f"• Ruhsat Onay Tarihi = {approval_date.strftime('%d.%m.%Y')}\n\n"
                                detailed_message += f"• Ruhsat Onay Tarihindeki belge Grubu = {authority_group}\n\n"

                                # Base message'dan maksimum tutar bilgisini çıkar
                                max_amount_info = ""
                                max_amount_value = None
                                for line in base_message.split('\n'):
                                    if "üstlenebilecek maksimum iş miktarı" in line or "maksimum" in line.lower():
                                        max_amount_parts = line.split(':')
                                        if len(max_amount_parts) > 1:
                                            max_amount_info = max_amount_parts[1].strip()
                                            # Rakamsal değeri de çıkarmaya çalış
                                            try:
                                                # Para formatından rakamsal değeri çıkar
                                                import re

                                                numbers = re.findall(r'[\d.,]+', max_amount_info)
                                                if numbers:
                                                    max_amount_str = numbers[0].replace('.', '').replace(',', '.')
                                                    max_amount_value = float(max_amount_str)
                                            except:
                                                pass
                                        break

                                detailed_message += f"• Ruhsat Onay Tarihinde üstlenebileceği azami iş tutarı = {max_amount_info if max_amount_info else 'Hesaplanıyor...'}\n\n"
                                detailed_message += f"• Güncellenmemiş Belge Tutarı = {format_currency(calculated_document_amount)}\n\n"

                                # Hangi tutarın kullanıldığını belirle
                                if max_amount_value and max_amount_value < calculated_document_amount:
                                    work_experience_amount = max_amount_value
                                    detailed_message += f"• Azami tutar limiti nedeniyle sınırlanmıştır.\n\n"
                                else:
                                    work_experience_amount = calculated_document_amount

                                detailed_message += f"**İş Deneyimine esas Tutar = {format_currency(work_experience_amount)}**\n\n"

                            # 5. GRUP: ÜFE güncelleme hesabı - Direkt hesaplama
                            detailed_message += "**ÜFE güncelleme hesabı:**\n\n"

                            # Sözleşme ayından önceki ay
                            contract_prev_month = contract_date.replace(day=1) - timedelta(days=1)
                            contract_month_str = f"{contract_prev_month.year}/{contract_prev_month.strftime('%B')}"

                            # Başvuru ayından önceki ay
                            application_prev_month = application_date.replace(day=1) - timedelta(days=1)
                            application_month_str = f"{application_prev_month.year}/{application_prev_month.strftime('%B')}"

                            # ÜFE endeks değerlerini al
                            contract_index = ufe_data.get(str(contract_prev_month.year), {}).get(
                                str(contract_prev_month.month), "Bulunamadı")
                            application_index = ufe_data.get(str(application_prev_month.year), {}).get(
                                str(application_prev_month.month), "Bulunamadı")

                            # ÜFE oranını hesapla
                            if contract_index != "Bulunamadı" and application_index != "Bulunamadı":
                                ufe_ratio = application_index / contract_index
                            else:
                                # Eğer endeks bulunamazsa, final_document_amount ile work_experience_amount arasındaki oranı kullan
                                ufe_ratio = final_document_amount / work_experience_amount if work_experience_amount > 0 else 1.0

                            detailed_message += f"• Sözleşmeden önceki ay: {contract_month_str}\n\n"
                            detailed_message += f"• Sözleşme ayından önceki aya ait endeks: {contract_index}\n\n"
                            detailed_message += f"• Başvuru tarihinden önceki ay: {application_month_str}\n\n"
                            detailed_message += f"• Başvuru ayından önceki aya ait endeks: {application_index}\n\n"
                            detailed_message += f"• ÜFE Güncelleme oranı: {application_index} / {contract_index} = {ufe_ratio:.6f}\n\n"

                            # 6. GRUP: Final sonuç
                            # Güncel tutarı hesapla
                            calculated_final_amount = work_experience_amount * ufe_ratio
                            detailed_message += f"**Güncel Tutar = İş Deneyimine esas Tutar × ÜFE Güncelleme oranı = {format_currency(work_experience_amount)} × {ufe_ratio:.6f} = {format_currency(calculated_final_amount)}**"

                            final_message = detailed_message
                        else:
                            final_message = base_message

                        # Mesajı göster
                        if final_message:
                            if "kullanılamaz" in final_message:
                                st.error(final_message)
                                st.stop()
                            else:
                                st.info(final_message)

                        if final_document_amount == 0:
                            st.stop()
                    else:
                        # İş deneyimine tabi olmayan sanayi yapısı durumunda normal hesaplama yap
                        final_document_amount = calculated_document_amount
                else:
                    final_document_amount = document_amount * 0.85 * (
                            essential_element_percentage / 100) if take_85_percent else document_amount
                    final_document_amount = final_document_amount * 1.05 * (
                            essential_element_percentage / 100) if green_building else final_document_amount
                    final_document_amount = final_document_amount * (venture_ratio / 100) * (
                            essential_element_percentage / 100) if joint_venture else final_document_amount

                ufe_ratio, warning_message, used_indices = calculate_ufe_ratio(
                    application_date,
                    contract_date,
                    ufe_data
                )
                updated_amount = calculate_ekap_updated_amount(final_document_amount, ufe_ratio)
                formatted_amount = format_currency(updated_amount)
                st.session_state['calculated_amount'] = formatted_amount
                st.success(f'Güncel Belge Tutarı: {formatted_amount}')

                # Sanayi yapısı değilse hesaplama detaylarını göster
                if not is_industrial:
                    st.markdown("---")
                    st.markdown("### 📊 Hesaplama Detayları")

                    # Kullanıcı girdileri
                    st.markdown("**Kullanıcı tarafından girişi yapılan bilgiler:**")
                    col1, col2 = st.columns(2)

                    # Ortak girişim oranını kontrol et
                    display_venture_ratio = venture_ratio if joint_venture else 100

                    with col1:
                        st.write(f"• Başvuru Tarihi: {application_date.strftime('%d.%m.%Y')}")
                        st.write(f"• Sözleşme Tarihi: {contract_date.strftime('%d.%m.%Y')}")
                        st.write(f"• Geçici Kabul/İskan Tarihi: {acceptance_date.strftime('%d.%m.%Y')}")
                        st.write(f"• İlk Sözleşme Bedeli: {format_currency(initial_amount)}")
                        st.write(f"• Belge Tutarı (A): {format_currency(document_amount)}")

                    with col2:
                        st.write(f"• Belge tutarının %85'ini al: {'Evet' if take_85_percent else 'Hayır'}")
                        st.write(f"• Yeşil Bina Sertifikası: {'Evet' if green_building else 'Hayır'}")
                        st.write(f"• Ortak Girişim Oranı (%) (B): %{display_venture_ratio}")
                        st.write(f"• Esas Unsur Yüzdesi (%) (C): %{essential_element_percentage}")
                        st.write(f"• Yapı Sahibi veya Hissedar mı?: {'Evet' if is_building_owner else 'Hayır'}")

                    # Hesaplama parametreleri
                    st.markdown("**Müteahhitlik Belge Grubuna Esas Belge Tutarı hesabı:**")
                    d_factor = 0.85 if take_85_percent else 1.0
                    e_factor = 1.05 if green_building else 1.0
                    f_factor = display_venture_ratio / 100

                    st.write(f"• D: Belge tutarının %85'ini al katsayısı = {d_factor}")
                    st.write(f"• E: Yeşil Bina Sertifikası katsayısı = {e_factor}")
                    st.write(f"• F: Ortak girişim oranı = %{display_venture_ratio} = {f_factor}")

                    unupdated_amount = document_amount * f_factor * (
                            essential_element_percentage / 100) * d_factor * e_factor
                    st.write(
                        f"**Güncellenmemiş Belge Tutarı = A × B × C × D × E = {format_currency(unupdated_amount)}**")

                    # ÜFE güncelleme bilgileri
                    st.markdown("**ÜFE güncelleme hesabı:**")

                    # Sözleşme ayından önceki ay
                    contract_prev_month = contract_date.replace(day=1) - timedelta(days=1)
                    contract_month_str = f"{contract_prev_month.year}/{contract_prev_month.strftime('%B')}"

                    # Başvuru ayından önceki ay
                    application_prev_month = application_date.replace(day=1) - timedelta(days=1)
                    application_month_str = f"{application_prev_month.year}/{application_prev_month.strftime('%B')}"

                    # ÜFE endeks değerlerini al
                    contract_index = ufe_data.get(str(contract_prev_month.year), {}).get(str(contract_prev_month.month),
                                                                                         "Bulunamadı")
                    application_index = ufe_data.get(str(application_prev_month.year), {}).get(
                        str(application_prev_month.month), "Bulunamadı")

                    st.write(f"• Sözleşmeden önceki ay: {contract_month_str}")
                    st.write(f"• Sözleşme ayından önceki aya ait endeks: {contract_index}")
                    st.write(f"• Başvuru tarihinden önceki ay: {application_month_str}")
                    st.write(f"• Başvuru ayından önceki aya ait endeks: {application_index}")
                    st.write(f"• ÜFE Güncelleme oranı: {application_index} / {contract_index} = {ufe_ratio:.6f}")

                    st.markdown(
                        f"**Güncel Tutar = Güncellenmemiş Belge Tutarı × ÜFE Güncelleme oranı = {formatted_amount}**")

                if warning_message:
                    st.warning(warning_message)

            except ValueError as e:
                st.error(str(e))
        else:
            st.error('Lütfen tüm alanları doldurun.')
# Add to table button (if calculation is done)
if st.session_state.get('calculated_amount') is not None:
    if st.button('Tabloya Ekle'):
        st.session_state['counter'] += 1
        new_entry = {
            'No': st.session_state['counter'],
            'Başvuru Tarihi': application_date,
            'İş Deneyim Tipi': experience_type,
            'Sözleşme Tarihi/Diploma Tarihi': contract_date if experience_type != "Mezuniyet Belgesi Ekle" else graduation_date,
            'Geçici Kabul/İskan Tarihi': acceptance_date if experience_type != "Mezuniyet Belgesi Ekle" else "-",
            'İlk Sözleşme Bedeli': format_currency(
                initial_amount) if experience_type == "EKAP İş Deneyim Belgesi Ekle" else "-",
            'Belge Tutarı': format_currency(
                document_amount) if experience_type == "EKAP İş Deneyim Belgesi Ekle" else "-",
            'Güncel Belge Tutarı': st.session_state['calculated_amount']
        }
        st.session_state['data'].append(new_entry)
        st.session_state['calculated_amount'] = None
        st.success('Kayıt başarıyla eklendi!')

# Display table if there are entries
if st.session_state['data']:
    st.write('### Kayıtlar')
    df = pd.DataFrame(st.session_state['data'])
    df['Başvuru Tarihi'] = df['Başvuru Tarihi'].apply(format_date)
    df['Sözleşme Tarihi/Diploma Tarihi'] = df['Sözleşme Tarihi/Diploma Tarihi'].apply(format_date)
    df['Geçici Kabul/İskan Tarihi'] = df['Geçici Kabul/İskan Tarihi'].apply(format_date)
    st.dataframe(df, hide_index=True)