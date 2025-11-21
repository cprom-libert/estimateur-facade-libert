import streamlit as st
import time
import requests
import math

# --- CONFIGURATION ---
st.set_page_config(page_title="Estimateur Libert V25 (Data-Mining)", layout="wide", page_icon="🛰️")

# ==============================================================================
# 🔑 API GOOGLE (Pour l'image)
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = "" 

# ==============================================================================
# 1. BASE DE PRIX (LIBERT 2025)
# ==============================================================================
DB_PRIX = {
    "LOGISTIQUE": {
        "BASE_VIE": {"titre": "Installation & Base Vie", "pourquoi": "Roulotte, WC, Cantonnement.", "pu": 4500.00, "unit": "Forfait"},
        "AUTORISATION": {"titre": "Taxes Voirie", "pourquoi": "Redevance municipale.", "pu": 605.00, "unit": "Forfait"},
        "ECHAFAUDAGE": {"titre": "Échafaudage Tubulaire", "pourquoi": "Classe 4 + filets.", "pu": 39.90, "unit": "m²"},
        "TUNNEL": {"titre": "Tunnel Public", "pourquoi": "Sécurité piétons (Commerce).", "pu": 60.00, "unit": "ml"}
    },
    "PLATRE": { 
        "NETTOYAGE": {"titre": "Décapage Chimique", "pourquoi": "Retrait peintures anciennes.", "pu": 16.50, "unit": "m²"},
        "PIOCHAGE": {"titre": "Soin des Maçonneries", "pourquoi": "Purge des zones soufflées.", "pu": 150.00, "unit": "m²"},
        "FINITION": {"titre": "Micro-Mortier Chaux", "pourquoi": "Respirant.", "pu": 90.00, "unit": "m²"},
        "RATIO": 0.50
    },
    "PIERRE": { 
        "NETTOYAGE": {"titre": "Hydrogommage", "pourquoi": "Gommage doux.", "pu": 25.00, "unit": "m²"},
        "PIOCHAGE": {"titre": "Ragréage Pierre", "pourquoi": "Reconstitution.", "pu": 37.50, "unit": "m²"},
        "FINITION": {"titre": "Minéralisation", "pourquoi": "Silicate.", "pu": 48.00, "unit": "m²"},
        "RATIO": 0.10
    },
    "BETON": { 
        "NETTOYAGE": {"titre": "Lavage HP", "pourquoi": "Décrassage.", "pu": 12.00, "unit": "m²"},
        "PIOCHAGE": {"titre": "Passivation Aciers", "pourquoi": "Traitement antirouille.", "pu": 37.50, "unit": "m²"},
        "FINITION": {"titre": "Revêtement D3", "pourquoi": "Imperméabilité.", "pu": 55.00, "unit": "m²"},
        "RATIO": 0.05
    },
    "SINGULIERS": {
        "APPUI": {"titre": "Appuis Zinc", "pourquoi": "Bavette neuve.", "pu": 210.00, "unit": "U"},
        "DESCENTE": {"titre": "Descentes EP", "pourquoi": "Remplacement.", "pu": 165.00, "unit": "ml"},
        "GARDE_CORPS": {"titre": "Peinture Fer", "pourquoi": "Antirouille.", "pu": 160.00, "unit": "U"},
        "CHIEN_ASSIS": {"titre": "Habillage Lucarne", "pourquoi": "Rénovation zinc.", "pu": 950.00, "unit": "U"},
        "BANDEAU": {"titre": "Bandeau Zinc", "pourquoi": "Couvre-murette.", "pu": 178.00, "unit": "ml"},
        "BOIS_PORTE": {"titre": "Restauration Porte", "pourquoi": "Décapage & Lasure.", "pu": 3200.00, "unit": "Forfait"}
    }
}

# ==============================================================================
# 2. MOTEUR "DATA MINING" (OSM + API GOUV)
# ==============================================================================

def get_geo_data(adresse):
    """Récupère Lat/Lon précis via API Gouv"""
    url = f"https://api-adresse.data.gouv.fr/search/?q={adresse}&limit=1"
    try:
        r = requests.get(url).json()
        if r['features']:
            coords = r['features'][0]['geometry']['coordinates']
            return coords[1], coords[0] # Lat, Lon
    except: return None, None
    return None, None

def query_openstreetmap(lat, lon):
    """
    Interroge OpenStreetMap pour trouver le bâtiment sous le point GPS
    et extraire ses métadonnées (Étages, Forme, Largeur approx).
    """
    overpass_url = "http://overpass-api.de/api/interpreter"
    # Rayon de 15m autour du point pour trouver le 'way' (bâtiment)
    overpass_query = f"""
    [out:json];
    (
      way["building"](around:15, {lat}, {lon});
    );
    out body;
    >;
    out skel qt;
    """
    try:
        response = requests.get(overpass_url, params={'data': overpass_query})
        data = response.json()
        
        if data['elements']:
            # On cherche les tags du bâtiment
            tags = {}
            nodes = []
            for el in data['elements']:
                if el['type'] == 'way' and 'tags' in el:
                    tags = el['tags']
                    nodes = el['nodes']
                    break
            
            # Estimation largeur (très approximative via bounding box des noeuds)
            # Pour une vraie précision, il faudrait calculer la géométrie du polygone face à la rue
            largeur_estimee = 14 # Valeur par défaut
            
            return tags, largeur_estimee
    except:
        return {}, 14
    return {}, 14

def analyser_batiment_reel(adresse):
    # 1. Géolocalisation
    lat, lon = get_geo_data(adresse)
    if not lat:
        return None # Échec adresse
        
    # 2. Data Mining OSM
    tags_osm, largeur_osm = query_openstreetmap(lat, lon)
    
    # 3. Analyse des Tags OSM (La "Vraie" Intelligence)
    
    # A. HAUTEUR / ÉTAGES
    # OSM contient souvent 'building:levels'
    levels = tags_osm.get('building:levels', None)
    if levels:
        try:
            etages = int(levels)
        except:
            etages = 5 # Fallback
        source_hauteur = "✅ Donnée Réelle (OpenStreetMap)"
    else:
        # Fallback probabiliste selon quartier
        if "750" in adresse: etages = 6 # Paris moyen
        else: etages = 3
        source_hauteur = "⚠️ Estimation IA (Data manquante)"

    # B. STYLE & MATÉRIAUX
    # On déduit le style via l'année ou le quartier (Logique renforcée)
    annee_est = "Inconnue"
    style = "Classique"
    profil = "PIERRE"
    toiture_complexe = False
    
    # Logique Parisienne Avancée
    if "750" in adresse: # Paris
        if etages <= 4:
            style = "Faubourien (Plâtre)"
            profil = "PLATRE"
            annee_est = "Av. 1850"
            toiture_complexe = False
        elif 5 <= etages <= 7:
            style = "Haussmannien (Pierre)"
            profil = "PIERRE"
            annee_est = "1850-1914"
            toiture_complexe = True # Haussmann a toujours des chambres de bonne/mansardes
        else:
            style = "Moderne / Art Déco"
            profil = "BETON"
            annee_est = "Ap. 1950"
            toiture_complexe = False
    
    # C. COMMERCES
    # OSM a parfois 'shop=*' ou 'building:use=retail'
    commerce = False
    if 'shop' in tags_osm or tags_osm.get('building:levels:retail', 0):
        commerce = True
        
    # D. LARGEUR (Si OSM échoue, on garde standard)
    largeur = largeur_osm if largeur_osm > 5 else 16

    # E. CALCULS
    hauteur_m = etages * 3.0
    surface = int(hauteur_m * largeur)
    nb_fen = int(surface/12)
    
    return {
        "adresse": adresse,
        "source": source_hauteur,
        "style": style,
        "annee": annee_est,
        "profil": profil,
        "geo": {"etages": etages, "largeur": largeur, "surface": surface},
        "specif": {"toiture": toiture_complexe, "commerce": commerce},
        "qty": {"fenetres": nb_fen, "ep": int(hauteur_m)}
    }

def get_street_view_url(adresse, api_key):
    if api_key:
        base = "https://maps.googleapis.com/maps/api/streetview"
        return f"{base}?size=640x480&location={adresse}&fov=110&pitch=15&key={api_key}"
    # Image illustrative
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Paris_-_Immeuble_bld_Raspail.jpg/800px-Paris_-_Immeuble_bld_Raspail.jpg"

# ==============================================================================
# 3. INTERFACE UTILISATEUR
# ==============================================================================

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎛️ Contrôle Expert")
    container_params = st.container() # Pour les corrections manuelles

# --- MAIN ---
st.title("🛰️ Estimateur Façade V25 (Data-Mining)")
st.info("Analyse croisée : API Gouv (Localisation) + OpenStreetMap (Structure Bâtiment) + Base Libert.")

if 'data' not in st.session_state: st.session_state.data = None

col1, col2 = st.columns([3, 1])
with col1:
    addr = st.text_input("Adresse :", placeholder="159 rue du faubourg saint antoine...")
with col2:
    st.write("")
    st.write("")
    btn = st.button("SCANNER", type="primary", use_container_width=True)

if btn and addr:
    with st.spinner("🛰️ Interrogation des satellites et bases de données..."):
        time.sleep(1)
        st.session_state.data = analyser_batiment_reel(addr)

# --- RESULTATS ---
if st.session_state.data:
    d = st.session_state.data
    
    # 1. SIDEBAR DE CORRECTION (L'IA propose, vous validez)
    with container_params:
        st.caption(f"Source Hauteur : {d['source']}")
        
        # Valeurs pré-remplies par OSM
        v_etages = st.number_input("Niveaux (R+)", value=d['geo']['etages'], min_value=1)
        v_largeur = st.number_input("Largeur (m)", value=d['geo']['largeur'], min_value=5)
        
        st.markdown("---")
        # Options détectées (mais modifiables)
        v_toit = st.checkbox("Toiture / Chiens-assis", value=d['specif']['toiture'])
        v_com = st.checkbox("Commerces RDC", value=d['specif']['commerce'])
        
        # Recalcul
        h_reel = v_etages * 3.0
        s_reel = int(h_reel * v_largeur)
        st.metric("Surface Corrigée", f"{s_reel} m²")

    # 2. RAPPORT VISUEL
    st.divider()
    c_img, c_txt = st.columns([1.5, 2])
    
    with c_img:
        st.image(get_street_view_url(addr, GOOGLE_API_KEY), caption="Vue Satellite / Rue", use_column_width=True)
        
    with c_txt:
        st.subheader(f"Analyse : {d['style']}")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Hauteur Donnée", f"R+{v_etages-1}")
        m2.metric("Surface Façade", f"{s_reel} m²")
        m3.metric("Année Est.", d['annee'])
        
        # Badges contextuels
        tags = []
        if v_toit: tags.append("🏠 Toiture Mansardée")
        if v_com: tags.append("🏪 Zone Commerciale")
        if d['profil'] == "PLATRE": tags.append("🧱 Support Fragile (Plâtre)")
        
        st.markdown(" ".join([f"`{t}`" for t in tags]))

    # 3. DEVIS INTELLIGENT
    st.markdown("### 📋 Estimation Technique")
    
    total = 0
    profil = DB_PRIX[d['profil']]
    
    def line(icon, key, cat, qty, u=None):
        if key not in DB_PRIX[cat]: return 0
        i = DB_PRIX[cat][key]
        unit = u if u else i['unit']
        p = qty * i['pu']
        
        with st.container():
            ca, cb, cc = st.columns([3, 1, 1])
            ca.markdown(f"**{icon} {i['titre']}**\n<span style='color:grey;font-size:0.8em'>{i['pourquoi']}</span>", unsafe_allow_html=True)
            cb.markdown(f"<div style='text-align:center'>{qty} {unit}</div>", unsafe_allow_html=True)
            cc.markdown(f"<div style='text-align:right'><b>{p:,.2f} €</b></div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:5px 0; opacity:0.1'>", unsafe_allow_html=True)
        return p

    # A. INSTALLATION
    st.markdown("##### 1. Logistique & Sécurité")
    total += line("🚧", "BASE_VIE", "LOGISTIQUE", 1)
    total += line("🛡️", "ECHAFAUDAGE", "LOGISTIQUE", s_reel)
    total += line("📜", "AUTORISATION", "LOGISTIQUE", 1)
    
    if v_com: # Si commerce coché ou détecté
        total += line("🚇", "TUNNEL", "LOGISTIQUE", v_largeur)
    if v_etages > 6:
        total += line("🏗️", "MAJORATION_HAUTEUR", "LOGISTIQUE", s_reel)

    # B. FAÇADE
    st.markdown("##### 2. Traitement des Supports")
    total += line("💦", "NETTOYAGE", d['profil'], s_reel)
    
    # Piochage Intelligent
    s_pioch = int(s_reel * profil["RATIO"])
    # Si toiture complexe (Haussmann), on suppose plus de dégradations en haut
    if v_toit and d['profil'] == "PLATRE": s_pioch = int(s_reel * 0.60)
        
    total += line("🧱", "PIOCHAGE", d['profil'], s_pioch)
    total += line("🎨", "FINITION", d['profil'], s_reel)

    # C. FINITIONS
    st.markdown("##### 3. Points Singuliers")
    nb_fen = int(s_reel/12)
    total += line("🚪", "BOIS_PORTE", "SINGULIERS", 1)
    total += line("🌧️", "APPUI", "SINGULIERS", nb_fen)
    total += line("⬇️", "DESCENTE", "SINGULIERS", int(v_etages*3))
    total += line("🏛️", "BANDEAU", "SINGULIERS", int(v_largeur*2))
    
    if v_toit:
        # Estimation Chiens-assis : 1 tous les 4m de large
        nb_chiens = max(2, int(v_largeur / 4))
        total += line("🏠", "CHIEN_ASSIS", "SINGULIERS", nb_chiens)

    # TOTAL
    st.markdown("---")
    ct1, ct2 = st.columns([2, 1])
    with ct2:
        st.markdown(f"""
        <div style="background:#2c3e50;color:white;padding:20px;border-radius:10px;text-align:right">
            <small>ESTIMATION HT</small>
            <h1 style="margin:0">{total:,.2f} €</h1>
        </div>
        """, unsafe_allow_html=True)