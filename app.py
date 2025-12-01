import streamlit as st
from ui import render_main_interface
from pricing import calculate_estimate
from email_utils import send_estimation_email
from pdf_generator import generate_pdf

st.set_page_config(layout="wide")

def main():
    st.session_state.setdefault("step", 0)

    st.markdown("<style>.block-container { padding-top: 1rem; }</style>", unsafe_allow_html=True)

    # Étape principale
    if st.session_state.step == 0:
        form_data = render_main_interface()
        if form_data:
            st.session_state.form_data = form_data
            st.session_state.step = 1

    # Étape estimation + coordonnées client
    elif st.session_state.step == 1:
        st.header("Coordonnées et validation")
        contact_name = st.text_input("Votre prénom et nom")
        contact_email = st.text_input("Votre adresse e-mail")
        submit = st.button("Recevoir l'estimation par e-mail")

        if submit and contact_name and contact_email:
            estimation = calculate_estimate(st.session_state.form_data)
            pdf = generate_pdf(estimation, contact_name)
            send_estimation_email(contact_name, contact_email, estimation, pdf)
            st.success("Estimation envoyée à " + contact_email)
            st.session_state.step = 2

    elif st.session_state.step == 2:
        st.success("Merci pour votre demande. Nous reviendrons vers vous prochainement.")

if __name__ == "__main__":
    main()
