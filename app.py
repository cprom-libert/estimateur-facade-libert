import streamlit as st
import time
import requests

# --- 1. CONFIGURATION & SÉCURITÉ ---
st.set_page_config(page_title="Estimateur Libert & Cie (Stable)", layout="wide", page_icon="🛡️")

try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = ""

# --- 2. BASE DE PRIX STRICTE (LIBERT 2025) ---
# Structure aplatie pour éviter tout bug de clé introuvable
DB = {
    # LOGISTIQUE
    "BASE_VIE": 4500.00, "AUTORISATION": 605.00, 
    "ECHAFAUDAGE": 39.90, "ECHAFAUDAGE_PAV": 28.00, "FILET": 13.00,
    "TUNNEL": 60.00, "ALARME": 2070.00, "MAJORATION_HAUTEUR": 15.00,
    
    # SUPPORTS (Nettoyage + Piochage + Finition)
    "PLATRE": {"net": 16.50, "pioch": 150.00, "fin": 95.00, "ratio": 0.50, "nom": "Restauration Plâtre (Lourd)"},
    "PIERRE": {"net": 28.00, "pioch": 85.00, "fin": 48.00, "ratio": 0.10, "nom": "Ravalement Pierre de Taille"},
    "BRIQUE": {"net": 35.00, "pioch": 120.00, "fin": 25.00, "ratio": 0.15, "nom": "Restauration Brique"},
    "BETON":  {"net": 12.00, "pioch": 45.00, "fin": 58.00, "ratio": 0.05, "nom": "Ravalement D3 Armé"},
    "PAVILLON": {"net": 18.00, "pioch": 45.00, "fin": 42.00, "ratio": 0.10, "nom": "Ravalement I3 Souple"},

    # SINGULIERS
    "APPUI": 215.00, "DESCENTE": 165.00, "GARDE_CORPS": 160.00,
    "BANDEAU": 178.00, "CHIEN_ASSIS": 950.00,
    "PORTE_COCHERE": 3200.00, "PORTE_HALL": 850.00, "DEBORD_TOIT": 45.00
}

# --- 3. FONCTIONS ---
def get_adresses(q):
    if len(q) < 3: return []
    try:
        r = requests.get(f"https://api-adresse.data.gouv.fr/search/?q={q}&limit=5")
        return [f['properties']['label'] for f in r.json()['features']]
    except: return []

def get_image(adresse, heading, pitch):
    if GOOGLE_API_KEY:
        return f"https://maps.googleapis.com/maps/api/streetview?size=640x480&location={adresse}&fov=110&heading={heading}&pitch={pitch}&key={GOOGLE_API_KEY}"
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Immeuble_parisien.jpg/800px-Immeuble_parisien.jpg"

def ia_predict(adresse):
    # Logique simple et robuste pour pré-remplir
    ads = adresse.lower()
    if "allee" in ads or "chemin" in ads or "villa" in ads:
        return "PAVILLON", "PAVILLON", 2, 10
    
    if "sebastien" in ads or "faubourg" in ads: return "IMMEUBLE", "PLATRE", 4, 14
    if "pascal" in ads: return "IMMEUBLE", "BRIQUE", 6, 18
    if "general" in ads: return "IMMEUBLE", "BETON", 7, 20
    return "IMMEUBLE", "PIERRE", 6, 16 # Defaut

# --- 4. INTERFACE ---

# GESTION ÉTAT
if 'step' not in st.session_state: st.session_state.step = 1
if 'addr' not in st.session_state: st.session_state.addr = ""
if 'cam_h' not in st.session_state: st.session_state.cam_h = 0
if 'cam_p' not in st.session_state: st.session_state.cam_p = 10

# SIDEBAR (CONTROLES)
with st.sidebar:
    st.header("🎛️ Paramètres Techniques")
    
    st.subheader("1. Caméra")
    c1, c2, c3 = st.columns(3)
    if c1.button("⬅️"): st.session_state.cam_h -= 45
    if c2.button("🔄"): st.session_state.cam_h += 180
    if c3.button("➡️"): st.session_state.cam_h += 45
    st.session_state.cam_p = st.slider("Inclinaison", -10, 50, st.session_state.cam_p)

    st.divider()
    
    st.subheader("2. Configuration Bâtiment")
    # Ces variables sont MODIFIABLES par l'utilisateur
    # On initialise avec des valeurs par défaut, l'IA viendra les écraser une fois au chargement
    if 'ui_type' not in st.session_state: st.session_state.ui_type = "IMMEUBLE"
    if 'ui_mat' not in st.session_state: st.session_state.ui_mat = "PIERRE"
    if 'ui_niv' not in st.session_state: st.session_state.ui_niv = 5
    if 'ui_larg' not in st.session_state: st.session_state.ui_larg = 15
    
    type_bat = st.radio("Type", ["IMMEUBLE", "PAVILLON"], key="ui_type")
    mat_bat = st.selectbox("Matériau", ["PIERRE", "PLATRE", "BRIQUE", "BETON", "PAVILLON"], key="ui_mat")
    niv_bat = st.number_input("Niveaux (R+)", 1, 15, key="ui_niv")
    larg_bat = st.number_input("Largeur (m)", 5, 100, key="ui_larg")
    
    st.subheader("3. Options")
    opt_com = st.checkbox("Commerce RDC (Tunnel)", value=False)
    opt_alarme = st.checkbox("Alarme Échafaudage", value=True)
    opt_chiens = st.number_input("Nb Chiens-Assis", 0, 10, 0)
    opt_porte = st.selectbox("Porte Entrée", ["AUCUNE", "PORTE_COCHERE", "PORTE_HALL"])

# PAGE PRINCIPALE
st.title("🏢 Estimateur Libert V35 (Fiabilité)")

# BARRE RECHERCHE
c_search, c_go = st.columns([3, 1])
query = c_search.text_input("Adresse :", value=st.session_state.addr)
# Autocomplete
if query and len(query) > 4:
    res = get_adresses(query)
    if res:
        sel = st.selectbox("Suggestions :", res, label_visibility="collapsed")
        if sel != st.session_state.addr:
            st.session_state.addr = sel
            # LANCEMENT IA UNE SEULE FOIS
            t, m, n, l = ia_predict(sel)
            st.session_state.ui_type = t
            st.session_state.ui_mat = m
            st.session_state.ui_niv = n
            st.session_state.ui_larg = l
            st.rerun()

# AFFICHAGE DU RAPPORT
if st.session_state.addr:
    st.divider()
    
    # 1. VISUEL
    col_img, col_kpi = st.columns([1.5, 2])
    with col_img:
        st.image(get_image(st.session_state.addr, st.session_state.cam_h, st.session_state.cam_p), use_column_width=True)
        st.caption(f"Angle {st.session_state.cam_h}° | Pitch {st.session_state.cam_p}°")
    
    with col_kpi:
        st.subheader("Synthèse des Métrés")
        
        # CALCULS (Cœur du réacteur)
        h_calc = niv_bat * 3.0
        s_calc = int(h_calc * larg_bat)
        if type_bat == "PAVILLON": 
            s_calc = int((larg_bat * 4) * h_calc) # 4 façades
            
        nb_fen = int(s_calc / 12)
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Surface", f"{s_calc} m²")
        k2.metric("Hauteur", f"{h_calc} m")
        k3.metric("Ouvertures", f"{nb_fen} U")
        
        st.info(f"Système retenu : **{DB[mat_bat]['nom']}**")

    # 2. DEVIS
    st.markdown("### 📑 Devis Détaillé")
    total = 0
    
    def add(nom, qte, pu, unit=""):
        tot = qte * pu
        if tot > 0:
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"**{nom}**")
            c2.write(f"{int(qte)} {unit}")
            c3.write(f"**{tot:,.2f} €**")
            st.markdown("<hr style='margin:0; opacity:0.1'>", unsafe_allow_html=True)
        return tot

    st.markdown("##### 1. INSTALLATION")
    if type_bat == "PAVILLON":
        total += add("Échafaudage Léger", s_calc, DB["ECHAFAUDAGE_PAV"], "m²")
    else:
        total += add("Base Vie & Installations", 1, DB["BASE_VIE"], "Fft")
        total += add("Taxes Voirie", 1, DB["AUTORISATION"], "Fft")
        total += add("Échafaudage Classe 4", s_calc, DB["ECHAFAUDAGE"], "m²")
        if opt_com: total += add("Tunnel Protection", larg_bat, DB["TUNNEL"], "ml")
        if opt_alarme: total += add("Alarme", 1, DB["ALARME"], "Fft")
        if niv_bat > 6: total += add("Majoration Grande Hauteur", s_calc, DB["MAJORATION_HAUTEUR"], "m²")

    st.markdown("##### 2. TRAITEMENT")
    data_mat = DB[mat_bat]
    total += add("Nettoyage des fonds", s_calc, data_mat['net'], "m²")
    
    # Calcul Piochage
    s_pioch = int(s_calc * data_mat['ratio'])
    if opt_chiens > 0 and mat_bat == "PLATRE": s_pioch = int(s_calc * 0.60) # Majoration
    total += add(f"Maçonnerie / Purge ({int(data_mat['ratio']*100)}%)", s_pioch, data_mat['pioch'], "m²")
    
    total += add("Finition Système", s_calc, data_mat['fin'], "m²")

    st.markdown("##### 3. FINITIONS")
    total += add("Appuis Zinc", nb_fen, DB["APPUI"], "U")
    total += add("Descentes EP", int(h_calc), DB["DESCENTE"], "ml")
    
    if type_bat == "IMMEUBLE":
        total += add("Garde-Corps", int(nb_fen*0.7), DB["GARDE_CORPS"], "U")
        total += add("Bandeaux Zinc", int(larg_bat*2), DB["BANDEAU"], "ml")
    else:
        total += add("Débords de Toit", int(larg_bat*4), DB["DEBORD_TOIT"], "ml")
        
    if opt_chiens > 0: total += add("Habillage Chiens-Assis", opt_chiens, DB["CHIEN_ASSIS"], "U")
    if opt_porte != "AUCUNE": total += add(f"Restauration {opt_porte}", 1, DB[opt_porte], "U")

    # TOTAL
    st.markdown("---")
    st.markdown(f"<h2 style='text-align:right'>TOTAL HT : {total:,.2f} €</h2>", unsafe_allow_html=True)