import streamlit as st
import time
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="Estimateur Libert V46 (HD)", layout="wide", page_icon="🏢")

# ==============================================================================
# 1. SÉCURITÉ API
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = ""

# ==============================================================================
# 2. BASE DE PRIX
# ==============================================================================
DB_PRIX = {
    "LOGISTIQUE": {
        "BASE_VIE": {"titre": "Installation & Base Vie", "pourquoi": "Roulotte, WC, Cantonnement.", "pu": 4500.00, "unit": "Forfait"},
        "AUTORISATION": {"titre": "Taxes de Voirie (ODP)", "pourquoi": "Redevance municipale.", "pu": 605.00, "unit": "Forfait"},
        "ECHAFAUDAGE": {"titre": "Échafaudage Tubulaire", "pourquoi": "Classe 4 + filets pare-gravats.", "pu": 39.90, "unit": "m²"},
        "ECHAFAUDAGE_PAV": {"titre": "Échafaudage Léger", "pourquoi": "Structure adaptée pavillon.", "pu": 28.00, "unit": "m²"},
        "TUNNEL": {"titre": "Tunnel Public", "pourquoi": "Sécurité piétons (Commerce).", "pu": 65.00, "unit": "ml"},
        "ALARME": {"titre": "Alarme Échafaudage", "pourquoi": "Système anti-intrusion.", "pu": 2070.00, "unit": "Forfait"},
        "MAJORATION_HAUTEUR": {"titre": "Majoration Grande Hauteur", "pourquoi": "Manutention > R+5.", "pu": 15.00, "unit": "m²"}
    },
    "FACADES": { 
        "PLATRE_ANCIEN": {"titre": "Restauration Plâtre", "nettoyage": 16.50, "piochage": 160.00, "finition": 95.00, "ratio_degats": 0.50, "desc": "Décapage + Purge lourde + Micro-mortier"},
        "PIERRE_TAILLE": {"titre": "Ravalement Pierre", "nettoyage": 28.00, "piochage": 85.00, "finition": 48.00, "ratio_degats": 0.10, "desc": "Hydrogommage + Minéralisation"},
        "BRIQUE": {"titre": "Restauration Brique", "nettoyage": 35.00, "piochage": 120.00, "finition": 25.00, "ratio_degats": 0.15, "desc": "Nettoyage chimique + Hydrofuge"},
        "BETON": {"titre": "Ravalement D3", "nettoyage": 12.00, "piochage": 45.00, "finition": 58.00, "ratio_degats": 0.05, "desc": "Lavage HP + RPE Armé"},
        "PAVILLON_ENDUIT": {"titre": "Ravalement Pavillon", "nettoyage": 18.00, "piochage": 45.00, "finition": 42.00, "ratio_degats": 0.10, "desc": "Lavage + RPE"}
    },
    "ZINGUERIE": {
        "APPUI": {"titre": "Appuis Zinc", "pourquoi": "Bavette neuve.", "pu": 215.00, "unit": "U"},
        "DESCENTE": {"titre": "Descentes EP", "pourquoi": "Remplacement.", "pu": 165.00, "unit": "ml"},
        "GARDE_CORPS": {"titre": "Peinture Garde-corps", "pourquoi": "Traitement antirouille.", "pu": 160.00, "unit": "U"},
        "BANDEAU": {"titre": "Bandeau Zinc", "pourquoi": "Protection.", "pu": 178.00, "unit": "ml"},
        "CHIEN_ASSIS": {"titre": "Habillage Lucarne", "pourquoi": "Rénovation zinc.", "pu": 950.00, "unit": "U"}
    },
    "BOISERIE": {
        "PORTE_COCHERE": {"titre": "Restauration Porte Cochère", "pourquoi": "Décapage & Lasure.", "pu": 3200.00, "unit": "U"},
        "PORTE_ENTREE": {"titre": "Peinture Porte Hall", "pourquoi": "Laque tendue.", "pu": 850.00, "unit": "U"}
    }
}

# ==============================================================================
# 3. MOTEUR DATA & IMAGE
# ==============================================================================

def get_geo_data(adresse):
    """Récupère GPS"""
    try:
        r = requests.get(f"https://api-adresse.data.gouv.fr/search/?q={adresse}&limit=1").json()
        if r['features']:
            c = r['features'][0]['geometry']['coordinates']
            return c[1], c[0]
    except: return None, None
    return None, None

def query_osm_real_data(lat, lon):
    """Récupère Hauteur et Commerce via OSM"""
    query = f"""
    [out:json];
    (way["building"](around:20, {lat}, {lon}););
    out body;
    >;
    out skel qt;
    """
    try:
        r = requests.get("http://overpass-api.de/api/interpreter", params={'data': query})
        data = r.json()
        if data['elements']:
            for el in data['elements']:
                if 'tags' in el:
                    t = el['tags']
                    return {
                        "niveaux": int(t.get("building:levels", 0)),
                        "toit": int(t.get("roof:levels", 0)),
                        "commerce": True if (t.get("shop") or t.get("building:use") == "retail") else False,
                        "annee": t.get("start_date", "Inconnue")
                    }
    except: pass
    return {"niveaux": 0, "toit": 0, "commerce": False, "annee": "Inconnue"}

def get_adresses_api(query):
    if len(query) < 3: return []
    try:
        r = requests.get(f"https://api-adresse.data.gouv.fr/search/?q={query}&limit=5")
        return [f['properties']['label'] for f in r.json()['features']]
    except: return []

def get_street_view(lat, lon, heading, pitch, fov=80):
    """
    URL optimisée pour la qualité.
    On utilise lat/lon au lieu de l'adresse pour être sûr du point de vue.
    FOV réduit à 80 pour moins de distorsion.
    """
    if GOOGLE_API_KEY and len(GOOGLE_API_KEY) > 10:
        base = "https://maps.googleapis.com/maps/api/streetview"
        return f"{base}?size=640x640&location={lat},{lon}&fov={fov}&heading={heading}&pitch={pitch}&key={GOOGLE_API_KEY}"
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Immeuble_parisien.jpg/800px-Immeuble_parisien.jpg"

def get_google_maps_link(lat, lon):
    """Lien vers le vrai Street View HD"""
    return f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}"

# ==============================================================================
# 4. INTERFACE
# ==============================================================================

# Etats
if 'step' not in st.session_state: st.session_state.step = 0
if 'real_data' not in st.session_state: st.session_state.real_data = {}
if 'addr_label' not in st.session_state: st.session_state.addr_label = ""
if 'gps' not in st.session_state: st.session_state.gps = (0,0)
if 'cam_h' not in st.session_state: st.session_state.cam_h = 0
if 'cam_p' not in st.session_state: st.session_state.cam_p = 10
if 'cam_fov' not in st.session_state: st.session_state.cam_fov = 80 # Zoom

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎛️ Paramètres Photo")
    
    st.subheader("Rotation")
    c1, c2, c3 = st.columns(3)
    def rot(angle): st.session_state.cam_h = (st.session_state.cam_h + angle) % 360
    if c1.button("⬅️"): rot(-45)
    if c2.button("🔄"): rot(180)
    if c3.button("➡️"): rot(45)
    
    st.session_state.cam_p = st.slider("Inclinaison (Haut/Bas)", -10, 60, st.session_state.cam_p)
    st.session_state.cam_fov = st.slider("Zoom (FOV)", 20, 120, st.session_state.cam_fov, help="Plus petit = Plus zoomé")
    
    st.divider()
    st.subheader("🏗️ Données Techniques")
    params_container = st.container()

# --- MAIN ---
st.title("🏢 Estimateur Libert V46 (Qualité Image)")

c_search, c_btn = st.columns([3, 1])
with c_search:
    q = st.text_input("Adresse :", placeholder="Tapez une adresse...")
    final