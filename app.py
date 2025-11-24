import streamlit as st
import time
import requests
import math

# --- CONFIGURATION (FORCE LE MODE CLAIR) ---
st.set_page_config(
    page_title="Rapport V57", 
    layout="wide", 
    page_icon="📐",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# 1. SÉCURITÉ & PRIX
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = ""

DB_PRIX = {
    "LOGISTIQUE": {
        "BASE_VIE": {"titre": "Installation de Chantier", "desc": "Mise en place base vie, roulotte, raccordements.", "norme": "Règl. Voirie", "pu": 4500.00, "unit": "Forfait"},
        "AUTORISATION": {"titre": "Droits de Voirie", "desc": "Redevance domaine public.", "norme": "Admin", "pu": 605.00, "unit": "Forfait"},
        "ECHAFAUDAGE": {"titre": "Échafaudage Classe 4", "desc": "Tubulaire fixe, filets.", "norme": "NF HD 1000", "pu": 39.90, "unit": "m²"},
        "ECHAFAUDAGE_PAV": {"titre": "Échafaudage Léger", "desc": "Structure pavillon.", "norme": "NF", "pu": 28.00, "unit": "m²"},
        "TUNNEL": {"titre": "Tunnel Piétons", "desc": "Protection étanche.", "norme": "Sécurité", "pu": 65.00, "unit": "ml"},
        "ALARME": {"titre": "Sécurisation", "desc": "Système anti-intrusion.", "norme": "APSAD", "pu": 2070.00, "unit": "Forfait"},
        "MAJORATION_HAUTEUR": {"titre": "Sujétions IGH", "desc": "Levage > R+5.", "norme": "-", "pu": 15.00, "unit": "m²"}
    },
    "FACADES": { 
        "PLATRE_ANCIEN": {"titre": "Restauration Plâtre", "net": 16.50, "pioch": 160.00, "fin": 95.00, "ratio": 0.50},
        "PIERRE_TAILLE": {"titre": "Ravalement Pierre", "net": 28.00, "pioch": 85.00, "fin": 48.00, "ratio": 0.10},
        "BRIQUE": {"titre": "Restauration Brique", "net": 35.00, "pioch": 120.00, "fin": 25.00, "ratio": 0.15},
        "BETON": {"titre": "Ravalement D3", "net": 12.00, "pioch": 45.00, "fin": 58.00, "ratio": 0.05},
        "PAVILLON_ENDUIT": {"titre": "Ravalement Pavillon", "net": 18.00, "pioch": 45.00, "fin": 42.00, "ratio": 0.10}
    },
    "ZINGUERIE": {
        "APPUI": {"titre": "Appuis Zinc", "desc": "Façonnage bavette.", "norme": "DTU 40.5", "pu": 215.00, "unit": "U"},
        "DESCENTE": {"titre": "Descentes EP", "desc": "Remplacement.", "norme": "DTU 60.11", "pu": 165.00, "unit": "ml"},
        "GARDE_CORPS": {"titre": "Peinture Fer", "desc": "Antirouille + Laque.", "norme": "DTU 59.1", "pu": 160.00, "unit": "U"},
        "BANDEAU": {"titre": "Bandeaux Zinc", "desc": "Protection corniches.", "norme": "DTU 40.5", "pu": 178.00, "unit": "ml"},
        "CHIEN_ASSIS": {"titre": "Lucarne", "desc": "Rénovation zinc.", "norme": "-", "pu": 950.00, "unit": "U"}
    },
    "BOISERIE": {
        "PORTE_COCHERE": {"titre": "Porte Cochère", "desc": "Restauration complète.", "norme": "-", "pu": 3200.00, "unit": "U"},
        "PORTE_ENTREE": {"titre": "Porte Hall", "desc": "Peinture.", "norme": "-", "pu": 850.00, "unit": "U"},
        "DEBORD_TOIT": {"titre": "Débords Toit", "desc": "Lasure planches.", "norme": "-", "pu": 45.00, "unit": "ml"}
    }
}

# ==============================================================================
# 2. FONCTIONS GOOGLE (Sécurisées)
# ==============================================================================

def get_google_geocode(address):
    if not GOOGLE_API_KEY: return None, None
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={GOOGLE_API_KEY}"
        r = requests.get(url).json()
        if r['status'] == 'OK':
            loc = r['results'][0]['geometry']['location']
            return loc['lat'], loc['lng']
    except: pass
    return None, None

def get_smart_heading(lat_bat, lon_bat):
    if not GOOGLE_API_KEY: return 0
    try:
        url = f"https://maps.googleapis.com/maps/api/streetview/metadata?location={lat_bat},{lon_bat}&source=outdoor&key={GOOGLE_API_KEY}"
        meta = requests.get(url).json()
        if meta['status'] == 'OK':
            lat_car = meta['location']['lat']
            lon_car = meta['location']['lng']
            dLon = math.radians(lon_bat - lon_car)
            y = math.sin(dLon) * math.cos(math.radians(lat_bat))
            x = math.cos(math.radians(lat_car)) * math.sin(math.radians(lat_bat)) - math.sin(math.radians(lat_car)) * math.cos(math.radians(lat_bat)) * math.cos(dLon)
            return (math.degrees(math.atan2(y, x)) + 360) % 360
    except: pass
    return 0

def get_street_view_hd(lat, lon, heading, pitch):
    if GOOGLE_API_KEY:
        # URL Google HD
        return f"https://maps.googleapis.com/maps/api/streetview?size=2048x1024&location={lat},{lon}&fov=90&heading={heading}&pitch={pitch}&source=outdoor&key={GOOGLE_API_KEY}"
    # Image de secours si pas de clé
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Immeuble_parisien.jpg/800px-Immeuble_parisien.jpg"

def get_adresses_api(query):
    if len(query) < 3: return []
    try:
        r = requests.get(f"https://api-adresse.data.gouv.fr/search/?q={query}&limit=5")
        return [f['properties']['label'] for f in r.json()['features']]
    except: return []

def query_osm(lat, lon):
    try:
        q = f"""[out:json];(way["building"](around:20, {lat}, {lon}););out body;>;out skel qt;"""
        r = requests.get("http://overpass-api.de/api/interpreter", params={'data': q}).json()
        if r['elements']:
            t = r['elements'][0]['tags']
            return {
                "niveaux": int(t.get("building:levels", 0)),
                "toit": int(t.get("roof:levels", 0)),
                "commerce": True if (t.get("shop") or t.get("building:use")=="retail") else False
            }
    except: pass
    return {"niveaux": 0, "toit": 0, "commerce": False}

# ==============================================================================
# 3. INTERFACE
# ==============================================================================

if 'step' not in st.session_state: st.session_state.step = 0
if 'gps' not in st.session_state: st.session_state.gps = (0,0)
if 'cam_h' not in st.session_state: st.session_state.cam_h = 0
if 'cam_p' not in st.session_state: st.session_state.cam_p = 10
if 'addr_label' not in st.session_state: st.session_state.addr_label = ""
if 'real_data' not in st.session_state: st.session_state.real_data = {}

# CSS FORCE (Fond blanc et texte noir pour être sûr que ça s'affiche)
st.markdown("""
<style>
    .report-container { 
        background-color: white !important; 
        color: black !important;
        padding: 0px; 
        border: 1px solid #ccc; 
        box-shadow: 0 5px 15px rgba(0,0,0,0.2); 
        max-width: 1000px; 
        margin: auto; 
        border-radius: 8px; 
        overflow: hidden;
    }
    .report-banner { width: 100%; height: 350px; object-fit: cover; display: block; border-bottom: 5px solid #2c3e50; }
    .report-content { padding: 40px; }
    .line-item { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }
    .total-block { background: #2c3e50; color: white !important; padding: 20px; text-align: right; font-size: 20px; font-weight: bold; margin-top: 30px; }
    h1, h2, h3 { color: #2c3e50 !important; }
</style>
""", unsafe_allow_html=True)

# SIDEBAR
with st.sidebar:
    st.header("🎛️ Paramètres")
    c1, c2, c3 = st.columns(3)
    if c1.button("⬅️"): st.session_state.cam_h -= 45
    if c2.button("🔄"): st.session_state.cam_h += 180
    if c3.button("➡️"): st.session_state.cam_h += 45
    st.session_state.cam_p = st.slider("Inclinaison", -10, 60, st.session_state.cam_p)
    
    st.divider()
    params_container = st.container()

# MAIN : RECHERCHE
if st.session_state.step == 0:
    st.title("Estimateur V57 (Blindé)")
    c1, c2 = st.columns([3, 1])
    q = c1.text_input("Adresse :", placeholder="159 rue du faubourg saint antoine...")
    
    if q and len(q)>4:
        opts = get_adresses_api(q)
        final_addr = c1.selectbox("📍 Choix :", opts)
    else: final_addr = None

    if c2.button("GÉNÉRER", type="primary"):
        if final_addr:
            lat, lon = get_google_geocode(final_addr)
            if lat:
                st.session_state.gps = (lat, lon)
                st.session_state.cam_h = get_smart_heading(lat, lon)
                st.session_state.real_data = query_osm(lat, lon)
                st.session_state.addr_label = final_addr
                st.session_state.step = 1
                st.rerun()
            else:
                st.error("Google ne trouve pas l'adresse. Vérifiez votre clé API.")

# MAIN : RAPPORT
if st.session_state.step == 1:
    rd = st.session_state.real_data
    
    with params_container:
        u_mat = st.selectbox("Support", list(DB_PRIX["FACADES"].keys()))
        u_type = st.radio("Type", ["IMMEUBLE", "PAVILLON"])
        u_niv = st.number_input("Niveaux", value=(rd['niveaux'] if rd['niveaux']>0 else 5))
        u_larg = st.number_input("Largeur (m)", value=15)
        u_porte = st.selectbox("Porte", ["AUCUNE", "PORTE_COCHERE", "PORTE_ENTREE"])

    # Calculs
    h_calc = u_niv * 3.0
    s_calc = int(h_calc * u_larg)
    if u_type == "PAVILLON": s_calc = int((u_larg * 4) * h_calc)
    
    # Image
    img_url = get_street_view_hd(st.session_state.gps[0], st.session_state.gps[1], st.session_state.cam_h, st.session_state.cam_p)
    
    # HTML
    st.markdown(f"""
    <div class="report-container">
        <img src="{img_url}" class="report-banner" onerror="this.onerror=null; this.src='https://via.placeholder.com/800x400?text=Image+Non+Disponible';">
        <div class="report-content">
            <h2>RAPPORT D'ESTIMATION</h2>
            <p><b>Adresse :</b> {st.session_state.addr_label}</p>
            <p><b>Surface :</b> {s_calc} m² | <b>Hauteur :</b> {h_calc}m</p>
            <hr>
    """, unsafe_allow_html=True)
    
    total = 0
    def add_line(titre, px, qte, unit):
        t = px * qte
        st.markdown(f"""
        <div class="line-item">
            <div style="flex:3"><b>{titre}</b></div>
            <div style="flex:1; text-align:center">{int(qte)} {unit}</div>
            <div style="flex:1; text-align:right"><b>{t:,.2f} €</b></div>
        </div>
        """, unsafe_allow_html=True)
        return t

    # Lignes simplifiées pour débug
    st.markdown("<h4>1. LOGISTIQUE</h4>", unsafe_allow_html=True)
    for k in ["BASE_VIE", "AUTORISATION", "ECHAFAUDAGE"]:
        item = DB_PRIX["LOGISTIQUE"][k]
        total += add_line(item["titre"], item["pu"], s_calc if k=="ECHAFAUDAGE" else 1, "m²" if k=="ECHAFAUDAGE" else "Fft")

    st.markdown("<h4>2. FAÇADE</h4>", unsafe_allow_html=True)
    prof = DB_PRIX["FACADES"][u_mat]
    total += add_line(f"Nettoyage {u_mat}", prof["net"], s_calc, "m²")
    total += add_line("Réparation", 160.00, s_calc * prof["ratio"], "m²") # Simplifié pour test
    total += add_line("Finition", prof["fin"], s_calc, "m²")

    if u_porte != "AUCUNE":
        total += add_line(DB_PRIX["BOISERIE"][u_porte]["titre"], DB_PRIX["BOISERIE"][u_porte]["pu"], 1, "U")

    st.markdown(f"""
            <div class="total-block">TOTAL : {total:,.2f} € HT</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Nouvelle recherche"):
        st.session_state.step = 0
        st.rerun()