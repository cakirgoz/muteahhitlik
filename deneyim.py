import streamlit as st
import pandas as pd


def main():
    # Set page config
    st.set_page_config(page_title="Başvuru Bilgileri", layout="wide")

    # Custom CSS to match the design
    st.markdown("""
        <style>
        .stSelectbox {
            margin-bottom: 10px;
        }
        .main {
            padding: 20px;
        }
        .status-badge {
            background-color: #f0f2f6;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 14px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("Başvuru Bilgileri")
        st.markdown("Yapı Müteahhitleri İl Yetki Belgesi Komisyon Başvuru Dosyası İnceleme Formu")

    # Company information
    st.markdown("### ABAK İNŞAAT MÜHENDİSLİK EMLAK TURİZM HAYVANCILIK SANAYİ VE TİCARET LİMİTED ŞİRKETİ")
    st.markdown("Başvuru No: 795666617")

    # Navigation tabs
    tabs = st.tabs(
        ["Başvuru", "Başvuru Dosyaları", "Başvuru Detay Bilgileri", "İnceleme", "Karar", "Şikayet", "İtiraz"])

    with tabs[0]:
        # Form fields
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            # Document checks
            st.markdown("#### Belge Kontrolleri")
            st.selectbox("Ticaret Odası Kayıt Belgesi", ["Uygun"], key="ticaret")
            st.selectbox("Türkiye Ticaret Sicil Gazetesi", ["Uygun"], key="sicil")
            st.selectbox("Bildirim Yükümlülüğü Taahhütnamesi", ["Uygun"], key="taahhut")

            # Numeric inputs
            st.markdown("#### Finansal Bilgiler")
            st.number_input("Cari Oran", value=0.5430, format="%.4f", key="cari_oran")
            st.number_input("Öz Kaynak Oranı", value=0.3651, format="%.4f", key="oz_kaynak")
            st.number_input("Kısa Vadeli Banka Borçlarının Öz Kaynak Oranı", value=0.46, format="%.2f",
                            key="banka_borc")
            st.number_input("Banka Referans Mektubu", value=4174841.12, format="%.2f", key="banka_ref")

            # Group determination
            st.number_input("Grup Belirlemesine Esas İş Deneyim Miktarı (TL)", value=60920467.26, format="%.2f",
                            key="is_deneyim")

        with col2:
            # Experience fields
            st.markdown("#### Deneyim Bilgileri")
            st.selectbox("İş Hacmi Bilgileri", ["Yok", "Var"], key="is_hacmi")
            st.selectbox("Usta İş Gücü Bilgisi", ["Var", "Yok"], key="usta_bilgisi")
            st.selectbox("Teknik Personel İş Gücü Bilgisi", ["Yok", "Var"], key="teknik_personel")

        # Notes section
        st.markdown("#### Açıklama")
        st.text_area("", value="Grup Belirlemesine Esas İş Deneyim Miktarı (TL) F Grubu için uygun değildir.",
                     height=100)


if __name__ == "__main__":
    main()
