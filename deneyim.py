import streamlit as st
import pandas as pd
from datetime import date

# Add custom CSS to hide the GitHub icon
hide_streamlit_style = """
            <style>
            [data-testid="stToolbar"] {visibility: hidden !important;}
            footer {visibility: hidden !important;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
# Your app code goes here


if 'data' not in st.session_state:
    st.session_state['data'] = []
if 'calculated_amount' not in st.session_state:
    st.session_state['calculated_amount'] = None
if 'counter' not in st.session_state:
    st.session_state['counter'] = 0

def sabit_tutar_hesapla():
    return 10000

def format_currency(amount):
    return f"{amount:,.2f} TL"

st.title('İş Deneyimi Girişi')

experience_type = st.selectbox(
    "İş Deneyimi Türünü Seçin",
    ("EKAP İş Deneyim Belgesi Ekle", "Mezuniyet Belgesi Ekle", "Yapı Kullanma İzin Belgesi Ekle")
)

today = date.today()
application_date = st.date_input(
    'Başvuru Tarihi',
    min_value=date(2000, 1, 1),
    value=today
)

if experience_type == "Mezuniyet Belgesi Ekle":
    graduation_date = st.date_input(
        'Mezuniyet Tarihi',
        min_value=date(2000, 1, 1),
        value=None
    )

    calculate_button = st.button('Hesapla')
    if calculate_button:
        if graduation_date:
            tutar = sabit_tutar_hesapla()
            formatted_amount = format_currency(tutar)
            st.session_state['calculated_amount'] = formatted_amount
            st.success(f'Güncel Belge Tutarı: {formatted_amount}')

    if st.session_state['calculated_amount']:
        add_button = st.button('Tabloya Ekle')
        if add_button:
            st.session_state['counter'] += 1
            new_entry = {
                'No': st.session_state['counter'],
                'Başvuru Tarihi': application_date,
                'Sözleşme Tarihi/Diploma Tarihi': graduation_date,
                'Geçici Kabul/İskan Tarihi': '-',
                'İlk Sözleşme Bedeli': '-',
                'Belge Tutarı': '-',
                'Güncel Belge Tutarı': st.session_state['calculated_amount']
            }
            st.session_state['data'].append(new_entry)
            st.session_state['calculated_amount'] = None
            st.success('Kayıt başarıyla eklendi!')

elif experience_type == "Yapı Kullanma İzin Belgesi Ekle":
    col1, col2 = st.columns(2)

    with col1:
        contract_date = st.date_input('Sözleşme Tarihi', min_value=date(2000, 1, 1), value=None)
        building_class = st.selectbox('Yapı Sınıfı', [
            'I-A', 'I-B',
            'II-A', 'II-B', 'II-C',
            'III-A', 'III-B',
            'IV-A', 'IV-B', 'IV-C',
            'V-A', 'V-B', 'V-C', 'V-D'
        ])
        completion_percentage = st.number_input('Tamamlanma Yüzdesi (%)', min_value=0.0, max_value=100.0, value=0.0, step=0.1)

    with col2:
        acceptance_date = st.date_input('Geçici Kabul/İskan Tarihi', min_value=date(2000, 1, 1), value=None)
        building_area = st.number_input('Yapı Alanı (m²)', min_value=0.0, value=0.0)

    calculate_button = st.button('Hesapla')
    if calculate_button:
        if None not in (contract_date, acceptance_date) and building_area != 0.0:
            tutar = sabit_tutar_hesapla()
            formatted_amount = format_currency(tutar)
            st.session_state['calculated_amount'] = formatted_amount
            st.success(f'Güncel Belge Tutarı: {formatted_amount}')
        else:
            st.error('Lütfen tüm alanları doldurun.')

    if st.session_state['calculated_amount']:
        add_button = st.button('Tabloya Ekle')
        if add_button:
            st.session_state['counter'] += 1
            new_entry = {
                'No': st.session_state['counter'],
                'Başvuru Tarihi': application_date,
                'Sözleşme Tarihi/Diploma Tarihi': contract_date,
                'Geçici Kabul/İskan Tarihi': acceptance_date,
                'İlk Sözleşme Bedeli': building_class,
                'Belge Tutarı': f"{building_area:,.2f} m²",
                'Güncel Belge Tutarı': st.session_state['calculated_amount']
            }
            st.session_state['data'].append(new_entry)
            st.session_state['calculated_amount'] = None
            st.success('Kayıt başarıyla eklendi!')

else:  # EKAP İş Deneyim Belgesi Ekle
    col1, col2 = st.columns(2)

    with col1:
        contract_date = st.date_input('Sözleşme Tarihi', min_value=date(2000, 1, 1), value=None)
        initial_amount = st.number_input('İlk Sözleşme Bedeli', min_value=0.0, value=0.0)

    with col2:
        acceptance_date = st.date_input('Geçici Kabul/İskan Tarihi', min_value=date(2000, 1, 1), value=None)
        document_amount = st.number_input('Belge Tutarı', min_value=0.0, value=0.0)

    calculate_button = st.button('Hesapla')
    if calculate_button:
        if None not in (contract_date, acceptance_date) and 0.0 not in (initial_amount, document_amount):
            tutar = sabit_tutar_hesapla()
            formatted_amount = format_currency(tutar)
            st.session_state['calculated_amount'] = formatted_amount
            st.success(f'Güncel Belge Tutarı: {formatted_amount}')
        else:
            st.error('Lütfen tüm alanları doldurun.')

    if st.session_state['calculated_amount']:
        add_button = st.button('Tabloya Ekle')
        if add_button:
            st.session_state['counter'] += 1
            new_entry = {
                'No': st.session_state['counter'],
                'Başvuru Tarihi': application_date,
                'Sözleşme Tarihi/Diploma Tarihi': contract_date,
                'Geçici Kabul/İskan Tarihi': acceptance_date,
                'İlk Sözleşme Bedeli': format_currency(initial_amount),
                'Belge Tutarı': format_currency(document_amount),
                'Güncel Belge Tutarı': st.session_state['calculated_amount']
            }
            st.session_state['data'].append(new_entry)
            st.session_state['calculated_amount'] = None
            st.success('Kayıt başarıyla eklendi!')

if st.session_state['data']:
    st.write('### Kayıtlar')
    df = pd.DataFrame(st.session_state['data']).astype({
        'No': int,
        'Başvuru Tarihi': 'datetime64[ns]',
        'Sözleşme Tarihi/Diploma Tarihi': str,
        'Geçici Kabul/İskan Tarihi': str,
        'İlk Sözleşme Bedeli': str,
        'Belge Tutarı': str,
        'Güncel Belge Tutarı': str
    })
    st.dataframe(df, hide_index=True)
