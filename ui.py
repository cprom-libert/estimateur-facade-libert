import streamlit as st

def render_main_interface():
    st.header("Estimation de ravalement de façade")
    col1, col2 = st.columns([1, 2])

    with col1:
        st.image("https://maps.googleapis.com/maps/api/streetview?size=400x300&location=15+Rue+Brézin,+75014+Paris&key=YOUR_API_KEY", caption="Façade estimée")

    with col2:
        adresse = st.text_input("Adresse du bâtiment")
        hauteur = st.number_input("Hauteur de la façade (m)", min_value=1.0, max_value=60.0)
        largeur = st.number_input("Largeur de la façade (m)", min_value=1.0, max_value=100.0)
        etat = st.selectbox("État de la façade", ["Bon", "Moyen", "Dégradé"])
        chien_assis = st.checkbox("Présence de chiens assis ?")
        options = st.multiselect("Prestations souhaitées", ["Nettoyage", "Peinture", "Zinguerie", "Echafaudage"])
        urg = st.selectbox("Délais souhaité", ["3 mois", "6 mois", "+6 mois"])

        if st.button("Continuer"):
            return {
                "adresse": adresse,
                "hauteur": hauteur,
                "largeur": largeur,
                "etat": etat,
                "options": options,
                "urgence": urg,
                "chiens_assis": chien_assis
            }
