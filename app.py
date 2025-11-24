import streamlit as st
import requests
import math

# --- CONFIGURATION ---
st.set_page_config(page_title="Estimateur V53 (Google Native)", layout="wide", page_icon="📍")

# ==============================================================================
# 1. CLÉ API GOOGLE (CRUCIAL : Doit avoir "Geocoding API" + "Street View Static" activés)
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = ""

# ==============================================================================
# 2. MOTEUR INTELLIGENT 100% GOOGLE
# ==============================================================================

def get_google_geocode(address):
    """
    Demande à Google (et non plus à la France) où se trouve l'adresse.
    Google renvoie souvent le point d'accès sur rue ('ROOFTOP').
    """
    if not GOOGLE_API_KEY: return None, None
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_API_KEY}"
    r = requests.get(url).json()
    if r['status'] == 'OK':
        loc = r['results'][0]['geometry']['location']
        return loc['lat'], loc['lng']
    return None, None

def get_smart_heading(lat_bat, lon_bat):
    """
    Astuce de Mathématicien :
    On demande à Google les métadonnées de la voiture Street View la plus proche.
    On récupère la position de la voiture (lat_car, lon_car).
    On calcule l'angle (trigonométrie) pour que la voiture regarde le bâtiment.
    """
    if not GOOGLE_API_KEY: return 0
    
    # 1. Où est la voiture ?
    meta_url = f"https://maps.googleapis.com/maps/api/streetview/metadata?location={lat_bat},{lon_bat}&key={GOOGLE_API_KEY}"
    meta = requests.get(meta_url).json()
    
    if meta['status'] == 'OK':
        lat_car = meta['location']['lat']
        lon_car = meta['location']['lng']
        
        # 2. Calcul de l'angle (Voiture -> Bâtiment)
        # Formule de relèvement (Bearing)
        dLon = math.radians(lon_bat - lon_car)
        lat1 = math.radians(lat_car)
        lat2 = math.radians(lat_bat)
        
        y = math.sin(dLon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dLon)
        
        bearing = math.degrees(math.atan2(y, x))
        return (bearing + 360) % 360
        
    return 0 # Par défaut Nord

def get_google_image(lat, lon, heading, pitch):
    if GOOGLE_API_KEY:
        # On utilise la lat/lon précises de Google Geocoding
        return f"https://maps.googleapis.com/maps/api/streetview?size=640x480&location={lat},{lon}&fov=80&heading={heading}&pitch={pitch}&key={GOOGLE_API_KEY}"
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Immeuble_parisien.jpg/800px-Immeuble_parisien.jpg"

# ==============================================================================
# 3. INTERFACE
# ==============================================================================

if 'heading' not in st.session_state: st.session_state.heading = 0
if 'gps' not in st.session_state: st.session_state.gps = (None, None)

st.title("📍 Estimateur V53 : Intelligence Google")
st.markdown("Cette version utilise l'algorithme natif de Google pour se positionner face au bâtiment.")

# --- BARRE DE RECHERCHE ---
c1, c2 = st.columns([3, 1])
query = c1.text_input("Adresse complète", placeholder="Ex: 159 rue du faubourg saint antoine 75011 Paris")

if c2.button("🔍 SCANNER", type="primary"):
    if query and len(query) > 5:
        with st.spinner("Interrogation du satellite Google..."):
            # 1. On cherche le GPS via Google
            lat, lon = get_google_geocode(query)
            
            if lat:
                st.session_state.gps = (lat, lon)
                # 2. On calcule l'angle idéal automatiquement
                auto_heading = get_smart_heading(lat, lon)
                st.session_state.heading = auto_heading
            else:
                st.error("Google ne trouve pas cette adresse exacte.")

# --- AFFICHAGE ---
if st.session_state.gps[0]:
    lat, lon = st.session_state.gps
    
    col_img, col_ctrl = st.columns([2, 1])
    
    with col_img:
        url = get_google_image(lat, lon, st.session_state.heading, 10)
        st.image(url, caption="Vue calculée automatiquement", use_container_width=True)
        st.caption(f"GPS Google : {lat}, {lon} | Angle calculé : {int(st.session_state.heading)}°")

    with col_ctrl:
        st.info("L'angle a été calculé automatiquement pour faire face au bâtiment.")
        st.write("**Ajustement manuel si besoin :**")
        
        c_g, c_d = st.columns(2)
        if c_g.button("⬅️ -45°"): st.session_state.heading -= 45
        if c_d.button("➡️ +45°"): st.session_state.heading += 45
        
        st.slider("Rotation Fine", 0, 360, int(st.session_state.heading), key="slider_h", on_change=lambda: st.session_state.update(heading=st.session_state.slider_h))

    # --- LE RESTE DU DEVIS (SIMPLIFIÉ POUR L'EXEMPLE) ---
    st.divider()
    st.subheader("Devis Rapide")
    s = st.number_input("Surface estimée (m²)", value=200)
    st.metric("Budget Estimatif", f"{s * 150:,.2f} €")
    
elif not GOOGLE_API_KEY:
    st.error("⚠️ ERREUR : Aucune Clé API Google détectée dans `.streamlit/secrets.toml`.")
    st.warning("Pour que cette V53 fonctionne, vous devez activer 'Geocoding API' et 'Street View Static API' sur votre compte Google Cloud.")