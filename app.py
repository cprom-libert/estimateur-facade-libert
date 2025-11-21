import streamlit as st
import time
import requests
import math

# --- CONFIGURATION ---
st.set_page_config(page_title="Estimateur Libert V43 (Factuel)", layout="wide", page_icon="📐")

# ==============================================================================
# 1. CLÉ GOOGLE (POUR LA VUE)
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = ""

# ==============================================================================
# 2. BASE DE PRIX STRICTE (LIBERT 2025)
# ==============================================================================
DB_PRIX = {
    "LOGISTIQUE": {
        "BASE_VIE": {"titre": "Installation & Base Vie", "pourquoi": "Roulotte, WC, Cantonnement, Barrières.", "pu": 4500.00, "unit": "Forfait"},
        "AUTORISATION": {"titre": "Taxes Voirie (ODP)", "pourquoi": "Redevance municipale occupation domaine public.", "pu": 605.00, "unit": "Forfait"},
        "ECHAFAUDAGE": {"titre": "Échafaudage Tubulaire Classe 4", "pourquoi": "Structure lourde, platelage étanche.", "pu": 39.90, "unit": "m²"},
        "ECHAFAUDAGE_PAV": {"titre": "Échafaudage Léger", "pourquoi": "Structure adaptée pavillon.", "pu": 28.00, "unit": "m²"},
        "TUNNEL": {"titre": "Tunnel Protection Public", "pourquoi": "Obligatoire au-dessus des commerces.", "pu": 65.00, "unit": "ml"},
        "ALARME": {"titre": "Alarme Échafaudage", "pourquoi": "Système anti-intrusion 24/7.", "pu": 2070.00, "unit": "Forfait"},
        "MAJORATION_HAUTEUR": {"titre": "Majoration Grande Hauteur", "pourquoi": "Manutention supplémentaire > R+5.", "pu": 15.00, "unit": "m²"}
    },
    "FACADES": { 
        "PLATRE_ANCIEN": {"titre": "Restauration Plâtre (Traditionnel)", "nettoyage": 16.50, "piochage": 160.00, "finition": 95.00, "ratio_degats": 0.50, "desc": "Décapage + Purge lourde + Micro-mortier"},
        "PIERRE_TAILLE": {"titre": "Ravalement Pierre de Taille", "nettoyage": 28.00, "piochage": 85.00, "finition": 48.00, "ratio_degats": 0.10, "desc": "Hydrogommage + Ragréage + Minéralisation"},
        "BRIQUE": {"titre": "Restauration Brique", "nettoyage": 35.00, "piochage": 120.00, "finition": 25.00, "ratio_degats": 0.15, "desc": "Nettoyage chimique + Changement briques + Hydrofuge"},
        "BETON": {"titre": "Ravalement Technique D3", "nettoyage": 12.00, "piochage": 45.00, "finition": 58.00, "ratio_degats": 0.05, "desc": "Lavage HP + Passivation fers + RPE Armé"},
        "PAVILLON_ENDUIT": {"titre": "Ravalement Maison I3", "nettoyage": 18.00, "piochage": 45.00, "finition": 42.00, "ratio_degats": 0.10, "desc": "Lavage + Reprise fissures + RPE Souple"}
    },
    "ZINGUERIE": {
        "APPUI": {"titre": "Appuis Zinc", "pourquoi": "Bavette neuve.", "pu": 215.00, "unit": "U"},
        "DESCENTE": {"titre": "Descentes EP", "pourquoi": "Remplacement Zinc/Fonte.", "pu": 165.00, "unit": "ml"},
        "GARDE_CORPS": {"titre": "Peinture Garde-corps", "pourquoi": "Traitement antirouille.", "pu": 160.00, "unit": "U"},
        "BANDEAU": {"titre": "Bandeau Zinc", "pourquoi": "Protection.", "pu": 178.00, "unit": "ml"},
        "CHIEN_ASSIS": {"titre": "Habillage Chien-Assis", "pourquoi": "Rénovation zinc lucarne.", "pu": 950.00, "unit": "U"}
    },
    "BOISERIE": {
        "PORTE_COCHERE": {"titre": "Restauration Porte Cochère", "pourquoi": "Décapage, greffes, lasure.", "pu": 3200.00, "unit": "U"},
        "PORTE_ENTREE": {"titre": "Peinture Porte Hall", "pourquoi": "Égrenage et laque.", "pu": 850.00, "unit": "U"},
        "DEBORD_TOIT": {"titre": "Lasure Débords de Toit", "pourquoi": "Protection planches de rive.", "pu": 45.00, "unit": "ml"}
    }
}

# ==============================================================================
# 3. MOTEUR "DATA MINING" (OSM + API GOUV)
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

def query_osm_real_data(lat, lon):
    """
    Interroge la base OpenStreetMap pour obtenir les VRAIES données.
    Ne devine rien. Si la donnée est absente, renvoie None.
    """
    query = f"""
    [out:json];
    (
      way["building"](around:15, {lat}, {lon});
    );
    out body;
    >;
    out skel qt;
    """
    try:
        r = requests.get("http://overpass-api.de/api/interpreter", params={'data': query})
        data = r.json()
        
        if data['elements']:
            # On cherche l'élément qui a des tags
            for el in data['elements']:
                if 'tags' in el:
                    t = el['tags']
                    # Extraction Factuelle
                    niveaux = t.get("building:levels", None) # Ex: "6"
                    toit_niv = t.get("roof:levels", None)    # Ex: "1" (Combles)
                    usage = t.get("building:use", None)      # Ex: "retail"
                    shop = t.get("shop", None)               # Ex: "bakery"
                    date = t.get("start_date", None)         # Ex: "1890"
                    
                    return {
                        "niveaux": int(niveaux) if niveaux else 0,
                        "toit": int(toit_niv) if toit_niv else 0,
                        "commerce": True if (shop or usage == "retail") else False,
                        "annee": date if date else "Inconnue"
                    }
    except:
        return None
    return None

def get_adresses_api(query):
    if not query or len(query) < 3: return []
    try:
        r = requests.get(f"https://api-adresse.data.gouv.fr/search/?q={query}&limit=5")
        return [f['properties']['label'] for f in r.json()['features']] if r.status_code == 200 else []
    except: return []

def get_street_view(adresse, heading, pitch):
    if GOOGLE_API_KEY and len(GOOGLE_API_KEY) > 10:
        # Paramètres ajustés pour voir TOUT le bâtiment (fov=110, pitch=20)
        return f"https://maps.googleapis.com/maps/api/streetview?size=640x480&location={adresse}&fov=110&heading={heading}&pitch={pitch}&key={GOOGLE_API_KEY}"
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/No_image_available.svg/600px-No_image_available.svg.png"

# ==============================================================================
# 4. INTERFACE UTILISATEUR
# ==============================================================================

# --- GESTION DE L'ÉTAT ---
if 'step' not in st.session_state: st.session_state.step = 0
if 'real_data' not in st.session_state: st.session_state.real_data = {}
if 'cam_h' not in st.session_state: st.session_state.cam_h = 0
if 'cam_p' not in st.session_state: st.session_state.cam_p = 20

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎛️ Console Expert")
    
    # 1. CAMERA
    st.subheader("📷 Cadrage")
    c1, c2, c3 = st.columns(3)
    if c1.button("⬅️"): st.session_state.cam_h -= 45
    if c2.button("🔄"): st.session_state.cam_h += 180
    if c3.button("➡️"): st.session_state.cam_h += 45
    st.session_state.cam_p = st.slider("Haut/Bas", -10, 60, st.session_state.cam_p)
    
    st.divider()
    st.subheader("🏗️ Données Techniques")
    params_container = st.container()

# --- TITRE ---
st.title("🏢 Estimateur Libert V43 (Factuel)")

# --- RECHERCHE ---
c_search, c_btn = st.columns([3, 1])
with c_search:
    # Barre de recherche avec autocomplétion
    q = st.text_input("Adresse :", placeholder="Tapez une adresse...")
    final_addr = None
    if q and len(q) > 4:
        opts = get_adresses_api(q)
        if opts: final_addr = st.selectbox("📍 Sélection :", opts, label_visibility="collapsed")
        else: final_addr = q

with c_btn:
    st.write(""); st.write("")
    if st.button("CHARGER LES DONNÉES", type="primary", use_container_width=True):
        if final_addr:
            with st.spinner("Interrogation des bases cadastrales (OSM)..."):
                # 1. Récupération GPS
                lat, lon = get_geo_data(final_addr)
                if lat:
                    # 2. Récupération DATA RÉELLE
                    osm_data = query_osm_real_data(lat, lon)
                    
                    # 3. Stockage
                    st.session_state.real_data = osm_data if osm_data else {"niveaux": 0, "toit": 0, "commerce": False, "annee": "Inconnue"}
                    st.session_state.addr_label = final_addr
                    st.session_state.cam_h = 0 # Reset caméra
                    st.session_state.step = 1 # Afficher résultats
                else:
                    st.error("Adresse introuvable.")

# --- AFFICHAGE RÉSULTATS ---
if st.session_state.step == 1:
    
    rd = st.session_state.real_data
    
    # --- 1. REMPLISSAGE INTELLIGENT DE LA SIDEBAR ---
    with params_container:
        # A. TYPE DE BIEN
        u_type = st.radio("Type", ["IMMEUBLE", "PAVILLON"], horizontal=True)
        
        # B. MATÉRIAU (Pas de devinette ici, l'expert choisit)
        st.caption("Sélectionnez le support (Visuel) :")
        u_mat = st.selectbox("Support", list(DB_PRIX["FACADES"].keys()))
        
        # C. DIMENSIONS (Pré-remplies si DATA existe, sinon 0)
        st.caption("Dimensions (Données OSM) :")
        
        # Si OSM a trouvé les niveaux, on les met, sinon on met 0 pour forcer la saisie
        val_niv = rd['niveaux'] if rd['niveaux'] > 0 else 0
        label_niv = "✅ Niveaux (R+)" if rd['niveaux'] > 0 else "✏️ Niveaux (R+) À SAISIR"
        
        u_niv = st.number_input(label_niv, value=val_niv, min_value=0, step=1)
        u_larg = st.number_input("✏️ Largeur Façade (m)", value=15, min_value=5)
        
        # D. OPTIONS
        st.markdown("---")
        st.caption("Options Détectées :")
        
        # Commerce détecté ?
        is_com = rd['commerce']
        label_com = "✅ Commerce RDC (Détecté)" if is_com else "Commerce RDC"
        u_com = st.checkbox(label_com, value=is_com)
        
        u_alarme = st.checkbox("Alarme", value=True)
        
        # Toit détecté ?
        has_toit = True if rd['toit'] > 0 else False
        u_chiens = st.number_input("Chiens-assis", value=(2 if has_toit else 0))
        
        u_porte = st.selectbox("Porte Entrée", ["AUCUNE", "PORTE_COCHERE", "PORTE_ENTREE"])

    # --- 2. VISUEL ---
    st.divider()
    c_img, c_kpi = st.columns([1.5, 2])
    
    with c_img:
        # Image Google
        st.image(get_street_view(st.session_state.addr_label, st.session_state.cam_h, st.session_state.cam_p), use_column_width=True)
        st.caption("Vue Street View temps réel")
        
    with c_kpi:
        st.subheader(st.session_state.addr_label)
        
        # Alertes sur la qualité de la donnée
        if rd['niveaux'] > 0:
            st.success(f"✅ **Donnée Fiable :** Ce bâtiment est enregistré comme **R+{rd['niveaux']}** dans le cadastre OpenStreetMap.")
        else:
            st.warning("⚠️ **Donnée Manquante :** La hauteur n'est pas dans la base. Veuillez saisir le nombre d'étages à gauche.")
            
        if rd['annee'] != "Inconnue":
            st.info(f"📅 **Année de construction :** {rd['annee']}")
            
        # Calculs Live
        h_calc = u_niv * 3.0
        s_calc = int(h_calc * u_larg)
        nb_fen = int(s_calc / 12)
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Surface", f"{s_calc} m²")
        k2.metric("Hauteur", f"{h_calc} m")
        k3.metric("Type", u_type)

    # --- 3. DEVIS ---
    st.markdown("### 📑 Devis Estimatif")
    
    if u_niv == 0:
        st.error("🛑 **Action Requise :** Veuillez saisir le nombre d'étages dans le menu de gauche pour calculer le prix.")
    else:
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

        # A. LOGISTIQUE
        st.markdown("#### 1. Logistique")
        if u_type == "PAVILLON": 
            total += add("Échafaudage Léger", s_calc, DB_PRIX["LOGISTIQUE"]["ECHAFAUDAGE_PAV"]["pu"], "m²")
        else:
            total += add("Base Vie", 1, DB_PRIX["LOGISTIQUE"]["BASE_VIE"]["pu"], "Fft")
            total += add("Taxes Voirie", 1, DB_PRIX["LOGISTIQUE"]["AUTORISATION"]["pu"], "Fft")
            total += add("Échafaudage Classe 4", s_calc, DB_PRIX["LOGISTIQUE"]["ECHAFAUDAGE"]["pu"], "m²")
            
            if u_com: total += add("Tunnel Protection", u_larg, DB_PRIX["LOGISTIQUE"]["TUNNEL"]["pu"], "ml")
            if u_alarme: total += add("Alarme", 1, DB_PRIX["LOGISTIQUE"]["ALARME"]["pu"], "Fft")
            if u_niv > 6: total += add("Majoration Hauteur", s_calc, DB_PRIX["LOGISTIQUE"]["MAJORATION_HAUTEUR"]["pu"], "m²")

        # B. FAÇADE
        st.markdown("#### 2. Traitement")
        total += add(f"Nettoyage ({u_mat})", s_calc, prof['nettoyage'], "m²")
        
        # Piochage
        s_pioch = int(s_calc * prof['ratio_degats'])
        if u_chiens > 0 and u_mat == "PLATRE_ANCIEN": s_pioch = int(s_calc * 0.60)
        total += add("Maçonnerie (Purge)", s_pioch, prof['piochage'], "m²")
        total += add("Finition Système", s_calc, prof['finition'], "m²")

        # C. FINITIONS
        st.markdown("#### 3. Finitions")
        if u_porte != "AUCUNE": total += add(f"Restauration {u_porte}", 1, DB_PRIX["BOISERIE"][u_porte]["pu"], "U")
        
        total += add("Appuis Zinc", nb_fen, DB_PRIX["ZINGUERIE"]["APPUI"]["pu"], "U")
        total += add("Descentes EP", int(h_calc), DB_PRIX["ZINGUERIE"]["DESCENTE"]["pu"], "ml")
        
        if u_type == "IMMEUBLE": 
            total += add("Bandeaux Zinc", int(u_larg*2), DB_PRIX["ZINGUERIE"]["BANDEAU"]["pu"], "ml")
            total += add("Garde-Corps", int(nb_fen*0.7), DB_PRIX["ZINGUERIE"]["GARDE_CORPS"]["pu"], "U")
        
        if u_chiens > 0: 
            total += add("Habillage Chiens-Assis", u_chiens, DB_PRIX["ZINGUERIE"]["CHIEN_ASSIS"]["pu"], "U")

        st.markdown("---")
        st.markdown(f"<h2 style='text-align:right'>TOTAL HT : {total:,.2f} €</h2>", unsafe_allow_html=True)