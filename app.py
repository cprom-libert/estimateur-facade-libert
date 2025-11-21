import streamlit as st
import time
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="Estimateur Libert V19", layout="wide")

# ==========================================
# 1. BASE DE DONNÉES PRIX
# ==========================================
DB_PRIX = {
    "LOGISTIQUE": {
        "BASE_VIE": {"titre": "Base Vie Chantier", "pourquoi": "Roulotte & WC obligatoires.", "pu": 4500.00, "unit": "Forfait"},
        "AUTORISATION": {"titre": "Taxes Voirie", "pourquoi": "Redevance occupation.", "pu": 605.00, "unit": "Forfait"},
        "ECHAFAUDAGE": {"titre": "Échafaudage", "pourquoi": "Accès & Sécurité.", "pu": 39.90, "unit": "m²"},
        "FILET": {"titre": "Filets", "pourquoi": "Protection chutes.", "pu": 13.00, "unit": "m²"}
    },
    "PLATRE_ANCIEN": { 
        "NETTOYAGE": {"titre": "Décapage Chimique", "pourquoi": "Retrait peintures.", "pu": 16.50},
        "PIOCHAGE": {"titre": "Purge Maçonnerie", "pourquoi": "Retrait parties mortes.", "pu": 150.00},
        "FINITION": {"titre": "Finition Micro-Mortier", "pourquoi": "Respirant (Chaux).", "pu": 90.00},
        "RATIO_DEGATS": 0.50
    },
    "PIERRE_BRIQUE": { 
        "NETTOYAGE": {"titre": "Hydrogommage", "pourquoi": "Gommage doux.", "pu": 25.00},
        "PIOCHAGE": {"titre": "Ragréage Pierre", "pourquoi": "Reconstitution.", "pu": 37.50},
        "FINITION": {"titre": "Minéralisation", "pourquoi": "Protection invisible.", "pu": 48.00},
        "RATIO_DEGATS": 0.10
    },
    "MODERNE_BETON": { 
        "NETTOYAGE": {"titre": "Lavage HP", "pourquoi": "Décrassage.", "pu": 12.00},
        "PIOCHAGE": {"titre": "Traitement Fers", "pourquoi": "Passivation.", "pu": 37.50},
        "FINITION": {"titre": "Revêtement D3", "pourquoi": "Imperméabilité.", "pu": 55.00},
        "RATIO_DEGATS": 0.05
    },
    "BOISERIE": {
        "PORTE_COCHERE": {"titre": "Restauration Porte", "pourquoi": "Décapage & Lasure.", "pu": 3200.00, "unit": "Forfait"},
        "PORTE_ENTREE": {"titre": "Peinture Porte", "pourquoi": "Laque tendue.", "pu": 850.00, "unit": "Forfait"}
    },
    "ZINGUERIE": {
        "APPUI": {"titre": "Appuis Zinc", "pourquoi": "Bavette neuve.", "pu": 210.00, "unit": "U"},
        "DESCENTE": {"titre": "Descentes EP", "pourquoi": "Remplacement.", "pu": 165.00, "unit": "ml"},
        "GARDE_CORPS": {"titre": "Peinture Fer", "pourquoi": "Antirouille.", "pu": 160.00, "unit": "U"},
        "BANDEAU": {"titre": "Bandeaux Zinc", "pourquoi": "Couvre-murette.", "pu": 178.00, "unit": "ml"}
    }
}

# ==========================================
# 2. FONCTIONS API
# ==========================================
def get_adresses_api(query):
    if not query: return []
    url = f"https://api-adresse.data.gouv.fr/search/?q={query}&limit=5"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return [f['properties']['label'] for f in r.json()['features']]
    except: return []
    return []

def get_image_style(style):
    # Images d'illustration fiables (Wikimedia)
    if "Faubourien" in style: 
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/14_rue_Saint-S%C3%A9bastien_Paris_11.jpg/800px-14_rue_Saint-S%C3%A9bastien_Paris_11.jpg"
    elif "Haussmannien" in style: 
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Paris_-_Immeuble_bld_Raspail.jpg/800px-Paris_-_Immeuble_bld_Raspail.jpg"
    elif "Moderne" in style: 
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Immeuble_d%27habitation_HBM.jpg/800px-Immeuble_d%27habitation_HBM.jpg"
    else: 
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Immeuble_parisien.jpg/800px-Immeuble_parisien.jpg"

# ==========================================
# 3. INTELLIGENCE ARTIFICIELLE
# ==========================================
def proposition_ia(adresse):
    ads = adresse.lower()
    if "sebastien" in ads or "faubourg" in ads:
        return {"style": "Faubourien (Plâtre)", "annee": "1850", "profil": "PLATRE_ANCIEN", "porte": "PORTE_COCHERE", "etages": 4, "largeur": 14}
    elif "pascal" in ads or "thibaud" in ads:
        return {"style": "Années 30 (Brique)", "annee": "1930", "profil": "PIERRE_BRIQUE", "porte": "PORTE_ENTREE", "etages": 6, "largeur": 18}
    elif "general" in ads or "leclerc" in ads:
        return {"style": "Moderne (Béton)", "annee": "1970", "profil": "MODERNE_BETON", "porte": "PORTE_ENTREE", "etages": 7, "largeur": 22}
    else:
        # Par défaut Haussmann
        return {"style": "Haussmannien (Pierre)", "annee": "1890", "profil": "PIERRE_BRIQUE", "porte": "PORTE_COCHERE", "etages": 6, "largeur": 16}

# ==========================================
# 4. INTERFACE
# ==========================================
# Initialisation session
if 'adresse_input' not in st.session_state: st.session_state.adresse_input = ""
if 'data_ia' not in st.session_state: st.session_state.data_ia = None

# Sidebar
with st.sidebar:
    st.header("🔧 Paramètres")
    # Conteneur pour les réglages dynamiques
    container_params = st.container()

st.title("🏡 Estimateur Façade Libert")

# Recherche
col_s, col_b = st.columns([3, 1])
with col_s:
    query = st.text_input("Adresse :", placeholder="Tapez une adresse...", value=st.session_state.adresse_input)
    # Liste déroulante si recherche
    sel_addr = None
    if query and len(query) > 3:
        opts = get_adresses_api(query)
        if opts: sel_addr = st.selectbox("📍 Confirmer l'adresse :", opts)
    
with col_b:
    st.write("")
    st.write("")
    if st.button("ANALYSER", type="primary", use_container_width=True):
        if sel_addr:
            st.session_state.data_ia = proposition_ia(sel_addr)
            st.session_state.adresse_input = sel_addr
        elif query:
            # Force l'analyse même sans selection menu déroulant
            st.session_state.data_ia = proposition_ia(query)
            st.session_state.adresse_input = query

# RÉSULTATS
if st.session_state.data_ia:
    d = st.session_state.data_ia
    
    # -- SIDEBAR DYNAMIQUE --
    with container_params:
        st.subheader("Dimensions")
        v_etages = st.number_input("Niveaux (R+)", value=d['etages'], min_value=1)
        v_largeur = st.number_input("Largeur (m)", value=d['largeur'], min_value=5)
        
        # Calculs
        h_calc = v_etages * 3.0
        s_calc = int(h_calc * v_largeur)
        nb_fen = int(s_calc / 12)
        ml_ep = int(h_calc)
        
        st.metric("Surface", f"{s_calc} m²")
        st.caption(f"Hauteur: {h_calc}m")

    # -- VISUEL --
    st.divider()
    c_img, c_txt = st.columns([1, 2])
    with c_img:
        try:
            # Tentative affichage clé Google si dispo
            key = st.secrets["GOOGLE_API_KEY"]
            url = f"https://maps.googleapis.com/maps/api/streetview?size=600x400&location={st.session_state.adresse_input}&key={key}"
            st.image(url, use_column_width=True)
        except:
            # Fallback image illustration
            st.image(get_image_style(d['style']), caption="Style détecté", use_column_width=True)
            
    with c_txt:
        st.subheader(st.session_state.adresse_input)
        st.success(f"**Typologie :** {d['style']}")
        
        k1, k2 = st.columns(2)
        k1.metric("Année", d['annee'])
        k2.metric("Ouvertures", f"{nb_fen} fenêtres")

    # -- DEVIS --
    st.subheader("📑 Devis Estimatif")
    
    profil = DB_PRIX[d['profil']]
    total_ht = 0
    
    def ligne(icon, key, cat, qte, unit=None):
        if key not in DB_PRIX[cat]: return 0
        item = DB_PRIX[cat][key]
        u = unit if unit else item.get('unit', 'm²')
        tot = qte * item['pu']
        
        with st.container():
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.markdown(f"**{icon} {item['titre']}** \n<span style='color:gray;font-size:0.8em'>{item['pourquoi']}</span>", unsafe_allow_html=True)
            c2.markdown(f"<div style='text-align:center;padding-top:10px'>{qte} {u}</div>", unsafe_allow_html=True)
            c3.markdown(f"<div style='text-align:right;font-weight:bold;padding-top:10px'>{tot:,.2f} €</div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:5px 0;opacity:0.1'>", unsafe_allow_html=True)
        return tot

    st.markdown("##### 1. Logistique")
    total_ht += ligne("🚧", "BASE_VIE", "LOGISTIQUE", 1, "Forfait")
    total_ht += ligne("🛡️", "ECHAFAUDAGE", "LOGISTIQUE", s_calc)
    total_ht += ligne("📜", "AUTORISATION", "LOGISTIQUE", 1, "Forfait")

    st.markdown("##### 2. Façade")
    total_ht += ligne("💦", "NETTOYAGE", d['profil'], s_calc)
    s_pioch = int(s_calc * profil["RATIO_DEGATS"])
    total_ht += ligne("🧱", "PIOCHAGE", d['profil'], s_pioch)
    total_ht += ligne("🎨", "FINITION", d['profil'], s_calc)

    st.markdown("##### 3. Finitions")
    total_ht += ligne("🚪", d['porte'], "BOISERIE", 1, "U")
    total_ht += ligne("🌧️", "APPUI", "ZINGUERIE", nb_fen, "U")
    total_ht += ligne("⬇️", "DESCENTE", "ZINGUERIE", ml_ep, "ml")
    total_ht += ligne("🖌️", "GARDE_CORPS", "ZINGUERIE", int(nb_fen*0.7), "U")
    # Ajout Bandeau manquant
    total_ht += ligne("🏛️", "BANDEAU", "ZINGUERIE", int(v_largeur*2), "ml")

    # TOTAL
    st.markdown("---")
    col_fin_l, col_fin_r = st.columns([2,1])
    with col_fin_r:
        st.markdown(f"""
        <div style="background:#2c3e50;color:white;padding:15px;border-radius:5px;text-align:right">
            <div style="font-size:0.8em">TOTAL HT</div>
            <div style="font-size:1.5em;font-weight:bold">{total_ht:,.2f} €</div>
        </div>
        """, unsafe_allow_html=True)