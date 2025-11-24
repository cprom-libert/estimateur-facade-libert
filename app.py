import streamlit as st
import requests

st.set_page_config(page_title="V54 - Diagnostic API", layout="wide", page_icon="👨‍⚕️")

# 1. RECUPERATION CLE
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    API_KEY = ""

st.title("👨‍⚕️ Diagnostic de votre Clé Google")

if not API_KEY:
    st.error("❌ Aucune clé API trouvée dans .streamlit/secrets.toml")
    st.stop()

st.success(f"✅ Clé détectée (début : {API_KEY[:5]}...)")

# 2. TEST
st.subheader("Test de connexion")
adresse_test = "159 rue du faubourg saint antoine Paris"
st.write(f"Tentative de géolocalisation pour : **{adresse_test}**")

if st.button("LANCER LE DIAGNOSTIC", type="primary"):
    # Appel direct à l'API Geocoding
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={adresse_test}&key={API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # ANALYSE DU RÉSULTAT
        status = data.get("status")
        
        st.markdown("---")
        st.write(f"**Statut renvoyé par Google :** `{status}`")
        
        if status == "OK":
            st.balloons()
            st.success("✅ TOUT FONCTIONNE ! L'API Geocoding est active.")
            st.json(data['results'][0]['geometry']['location'])
            st.info("Vous pouvez remettre le code V53, le problème venait peut-être de l'adresse saisie.")
            
        elif status == "REQUEST_DENIED":
            st.error("❌ ACCÈS REFUSÉ (REQUEST_DENIED)")
            st.warning("👉 Cause probable : L'API 'Geocoding API' n'est pas activée sur votre compte Google Cloud.")
            st.markdown(f"**Message d'erreur détaillé :** {data.get('error_message')}")
            
        elif status == "OVER_QUERY_LIMIT":
            st.error("❌ QUOTA DÉPASSÉ ou FACTURATION INACTIVE")
            st.warning("👉 Vérifiez que vous avez lié une carte bancaire au projet Google Cloud (même pour l'offre gratuite).")
            
        else:
            st.error(f"❌ Erreur inconnue : {status}")
            st.json(data)
            
    except Exception as e:
        st.error(f"Erreur de connexion internet : {e}")