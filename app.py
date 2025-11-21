import streamlit as st
import time
import requests
import math

# --- CONFIGURATION ---
st.set_page_config(page_title="Estimateur Immeuble V44", layout="wide", page_icon="🏢")

# ==============================================================================
# 1. CLÉ GOOGLE API
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = ""

# ==============================================================================
# 2. BASE DE PRIX "IMMEUBLE" (LIBERT 2025)
# ==============================================================================
DB_PRIX = {
    "LOGISTIQUE": {
        "BASE_VIE": {"titre": "Installation Base Vie", "pourquoi": "Roulotte, WC, Cantonnement.", "pu": 4500.00, "unit": "Forfait"},
        "AUTORISATION": {"titre": "Taxes Voirie (ODP)", "pourquoi": "Redevance municipale.", "pu": 605.00, "unit": "Forfait"},
        "ECHAFAUDAGE": {"titre": "Échafaudage Tubulaire", "pourquoi": "Classe 4 + filets pare-gravats.", "pu": 39.90, "unit": "m²"},
        "TUNNEL": {"titre": "Tunnel Public", "pourquoi": "Sécurité piétons (Commerce).", "pu": 65.00, "unit": "ml"},
        "ALARME": {"titre": "Alarme Échafaudage", "pourquoi": "Système anti-intrusion.", "pu": 2070.00, "unit": "Forfait"},
        "MAJORATION_HAUTEUR": {"titre": "Majoration IGH", "pourquoi": "Manutention > R+5.", "pu": 15.00, "unit": "m²"}
    },
    "FACADES": { 
        "PLATRE_ANCIEN": {"titre": "Restauration Plâtre", "nettoyage": 16.50, "piochage": 160.00, "finition": 95.00, "ratio_degats": 0.50, "desc": "Décapage + Purge lourde + Micro-mortier"},
        "PIERRE_TAILLE": {"titre": "Ravalement Pierre", "nettoyage": 28.00, "piochage": 85.00, "finition": 48.00, "ratio_degats": 0.10, "desc": "Hydrogommage + Minéralisation"},
        "BRIQUE": {"titre": "Restauration Brique", "nettoyage": 35.00, "piochage": 120.00, "finition": 25.00, "ratio_degats": 0.15, "desc": "Nettoyage chimique + Hydrofuge"},
        "BETON": {"titre": "Ravalement D3", "nettoyage": 12.00, "piochage": 45.00, "finition": 58.00, "ratio_degats": 0.05, "desc": "Lavage HP + RPE Armé"}
    },
    "ZINGUERIE": {
        "APPUI": {"titre": "Appuis Zinc", "pourquoi": "Bavette neuve.", "pu": 215.00, "unit": "U"},
        "DESCENTE": {"titre": "Descentes EP", "pourquoi": "Remplacement Zinc/Fonte.", "pu": 165.00, "unit": "ml"},
        "GARDE_CORPS": {"titre": "Peinture Garde-corps", "pourquoi": "Traitement antirouille.", "pu": 160.00, "unit": "U"},
        "BANDEAU": {"titre": "Bandeau Zinc", "pourquoi": "Protection.", "pu": 178.00, "unit": "ml"},
        "CHIEN_ASSIS": {"titre": "Habillage Lucarne", "pourquoi": "Rénovation zinc.", "pu": 950.00, "unit": "U"}
    },
    "BOISERIE": {
        "PORTE_COCHERE": {"titre": "Restauration Porte Cochère", "pourquoi": "Décapage, greffes, lasure.", "pu": 3200.00, "unit": "U"},
        "PORTE_ENTREE": {"titre": "Peinture Porte Hall", "pourquoi": "Égrenage et laque.", "pu": 850.00, "unit": "U"}
    }
}

# ==============================================================================
# 3. MOTEUR DATA (OSM + GOOGLE)
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

def get_street_view(adresse, heading, pitch):
    if GOOGLE_API_KEY and len(GOOGLE_API_KEY) > 10:
        # Optimisé pour voir la façade en entier (fov 110)
        return f"https://maps.googleapis.com/maps/api/streetview?size=640x480&location={adresse}&fov=110&heading={heading}&pitch={pitch}&key={GOOGLE_API_KEY}"
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Immeuble_parisien.jpg/800px-Immeuble_parisien.jpg"

# ==============================================================================
# 4. INTERFACE UTILISATEUR
# ==============================================================================

# ETATS
if 'step' not in st.session_state: st.session_state.step = 0
if 'real_data' not in st.session_state: st.session_state.real_data = {}
if 'cam_h' not in st.session_state: st.session_state.cam_h = 0
if 'cam_p' not in st.session_state: st.session_state.cam_p = 10

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎛️ Console Expert")
    
    st.subheader("📷 Cadrage Photo")
    c1, c2, c3 = st.columns(3)
    if c1.button("⬅️"): st.session_state.cam_h -= 45
    if c2.button("🔄"): st.session_state.cam_h += 180
    if c3.button("➡️"): st.session_state.cam_h += 45
    st.session_state.cam_p = st.slider("Haut/Bas", -10, 60, st.session_state.cam_p)
    
    st.divider()
    st.subheader("🏗️ Données Techniques")
    params_container = st.container()

# --- MAIN ---
st.title("🏢 Estimateur Immeuble V44 (Spécial Façade)")

c_search, c_btn = st.columns([3, 1])
with c_search:
    q = st.text_input("Adresse :", placeholder="Ex: 159 rue du faubourg saint antoine...")
    final_addr = None
    if q and len(q) > 4:
        opts = get_adresses_api(q)
        if opts: final_addr = st.selectbox("📍 Sélection :", opts, label_visibility="collapsed")
        else: final_addr = q

with c_btn:
    st.write(""); st.write("")
    if st.button("SCANNER", type="primary", use_container_width=True):
        if final_addr:
            with st.spinner("Analyse des données cadastrales..."):
                lat, lon = get_geo_data(final_addr)
                if lat:
                    osm_data = query_osm_real_data(lat, lon)
                    st.session_state.real_data = osm_data
                    st.session_state.addr_label = final_addr
                    st.session_state.cam_h = 0
                    st.session_state.step = 1
                else:
                    st.error("Adresse introuvable.")

# --- RESULTATS ---
if st.session_state.step == 1:
    
    rd = st.session_state.real_data
    
    # 1. SIDEBAR INTELLIGENTE
    with params_container:
        # On détermine le profil par défaut selon l'adresse (Pas de pavillon !)
        ads = st.session_state.addr_label.lower()
        def_mat_idx = 1 # Pierre par défaut
        if "sebastien" in ads or "faubourg" in ads: def_mat_idx = 0 # Plâtre
        elif "general" in ads: def_mat_idx = 3 # Béton
        
        u_mat = st.selectbox("Support Façade", list(DB_PRIX["FACADES"].keys()), index=def_mat_idx)
        
        st.markdown("---")
        # Si OSM donne une hauteur, on l'utilise, sinon 5 par défaut
        val_niv = rd['niveaux'] if rd['niveaux'] > 0 else 5
        label_niv = "✅ Niveaux (R+)" if rd['niveaux'] > 0 else "✏️ Niveaux (R+) À SAISIR"
        
        u_niv = st.number_input(label_niv, value=val_niv, min_value=1)
        u_larg = st.number_input("✏️ Largeur Façade (m)", value=15, min_value=5)
        
        st.markdown("---")
        st.caption("Options :")
        u_com = st.checkbox("Commerce RDC", value=rd['commerce'])
        u_alarme = st.checkbox("Alarme", value=True)
        
        has_toit = True if rd['toit'] > 0 else False
        u_chiens = st.number_input("Chiens-assis", value=(2 if has_toit else 0))
        u_porte = st.selectbox("Porte Entrée", ["PORTE_COCHERE", "PORTE_ENTREE", "AUCUNE"])

    # 2. VISUEL
    st.divider()
    c_img, c_kpi = st.columns([1.5, 2])
    
    with c_img:
        st.image(get_street_view(st.session_state.addr_label, st.session_state.cam_h, st.session_state.cam_p), caption="Façade sur rue", use_column_width=True)
        
    with c_kpi:
        st.subheader(st.session_state.addr_label)
        
        if rd['niveaux'] == 0:
            st.warning("⚠️ Hauteur non trouvée dans le cadastre. Vérifiez le nombre d'étages à gauche.")
            
        # Calculs Facade
        h_calc = u_niv * 3.0
        s_calc = int(h_calc * u_larg)
        nb_fen = int(s_calc / 12)
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Surface Façade", f"{s_calc} m²")
        k2.metric("Hauteur", f"{h_calc} m")
        k3.metric("Support", DB_PRIX["FACADES"][u_mat]["titre"])

    # 3. DEVIS
    st.markdown("### 📑 Devis Détaillé")
    total = 0
    prof = DB_PRIX["FACADES"][u_mat]
    
    def add(titre, qte, pu, unit):
        t = qte * pu
        with st.container():
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"**{titre}**")
            c2.write(f"{int(qte)} {unit}")
            c3.write(f"**{t:,.2f} €**")
            st.markdown("<hr style='margin:2px 0; opacity:0.1'>", unsafe_allow_html=True)
        return t

    # LOGISTIQUE
    st.markdown("#### 1. Logistique")
    total += add("Base Vie & Installations", 1, DB_PRIX["LOGISTIQUE"]["BASE_VIE"]["pu"], "Fft")
    total += add("Taxes Voirie (ODP)", 1, DB_PRIX["LOGISTIQUE"]["AUTORISATION"]["pu"], "Fft")
    total += add("Échafaudage Classe 4", s_calc, DB_PRIX["LOGISTIQUE"]["ECHAFAUDAGE"]["pu"], "m²")
    
    if u_com: total += add("Tunnel Protection", u_larg, DB_PRIX["LOGISTIQUE"]["TUNNEL"]["pu"], "ml")
    if u_alarme: total += add("Alarme", 1, DB_PRIX["LOGISTIQUE"]["ALARME"]["pu"], "Fft")
    if u_niv > 6: total += add("Majoration Hauteur", s_calc, DB_PRIX["LOGISTIQUE"]["MAJORATION_HAUTEUR"]["pu"], "m²")

    # FAÇADE
    st.markdown("#### 2. Traitement")
    total += add(f"Nettoyage ({u_mat})", s_calc, prof['nettoyage'], "m²")
    s_pioch = int(s_calc * prof['ratio_degats'])
    if u_chiens > 0 and u_mat == "PLATRE_ANCIEN": s_pioch = int(s_calc * 0.60)
    total += add("Maçonnerie (Purge)", s_pioch, prof['piochage'], "m²")
    total += add("Finition Système", s_calc, prof['finition'], "m²")

    # FINITIONS
    st.markdown("#### 3. Finitions")
    if u_porte != "AUCUNE": total += add(f"Restauration {u_porte}", 1, DB_PRIX["BOISERIE"][u_porte]["pu"], "U")
    
    total += add("Appuis Zinc", nb_fen, DB_PRIX["ZINGUERIE"]["APPUI"]["pu"], "U")
    total += add("Descentes EP", int(h_calc), DB_PRIX["ZINGUERIE"]["DESCENTE"]["pu"], "ml")
    total += add("Bandeaux Zinc", int(u_larg*2), DB_PRIX["ZINGUERIE"]["BANDEAU"]["pu"], "ml")
    total += add("Garde-Corps", int(nb_fen*0.7), DB_PRIX["ZINGUERIE"]["GARDE_CORPS"]["pu"], "U")
    
    if u_chiens > 0: total += add("Habillage Chiens-Assis", u_chiens, DB_PRIX["ZINGUERIE"]["CHIEN_ASSIS"]["pu"], "U")

    st.markdown("---")
    st.markdown(f"<h2 style='text-align:right'>TOTAL HT : {total:,.2f} €</h2>", unsafe_allow_html=True)

elif st.session_state.addr_label == "":
    st.info("👈 Entrez une adresse.")