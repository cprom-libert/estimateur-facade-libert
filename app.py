import streamlit as st
import time
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="Estimateur Libert V36", layout="wide", page_icon="🏗️")

# --- SÉCURITÉ ---
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = ""

# --- BASE DE DONNÉES PRIX (VOTRE BENCHMARK) ---
DB = {
    # LOGISTIQUE
    "BASE_VIE": 4500.00, "AUTORISATION": 605.00, 
    "ECHAFAUDAGE": 39.90, "ECHAFAUDAGE_PAV": 28.00, "FILET": 13.00,
    "TUNNEL": 60.00, "ALARME": 2070.00, "MAJORATION_HAUTEUR": 15.00,
    
    # SUPPORTS
    "PLATRE": {"net": 16.50, "pioch": 160.00, "fin": 95.00, "ratio": 0.50, "nom": "Restauration Plâtre (Traditionnel)"},
    "PIERRE": {"net": 28.00, "pioch": 85.00, "fin": 48.00, "ratio": 0.10, "nom": "Ravalement Pierre de Taille"},
    "BRIQUE": {"net": 35.00, "pioch": 120.00, "fin": 25.00, "ratio": 0.15, "nom": "Restauration Brique"},
    "BETON":  {"net": 12.00, "pioch": 45.00, "fin": 58.00, "ratio": 0.05, "nom": "Ravalement D3 Armé"},
    "PAVILLON": {"net": 18.00, "pioch": 45.00, "fin": 42.00, "ratio": 0.10, "nom": "Ravalement I3 Souple"},

    # SINGULIERS
    "APPUI": 215.00, "DESCENTE": 165.00, "GARDE_CORPS": 160.00,
    "BANDEAU": 178.00, "CHIEN_ASSIS": 950.00,
    "PORTE_COCHERE": 3200.00, "PORTE_HALL": 850.00, "DEBORD_TOIT": 45.00
}

# --- FONCTIONS ---
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

# Prédiction IA (Initialisation)
def ia_init(adresse):
    ads = adresse.lower()
    # 1. Pavillon ou Immeuble
    if "allee" in ads or "chemin" in ads or "villa" in ads:
        return "PAVILLON", "PAVILLON", 2, 10
    
    # 2. Type Immeuble
    if "sebastien" in ads or "faubourg" in ads: return "IMMEUBLE", "PLATRE", 4, 14
    if "pascal" in ads: return "IMMEUBLE", "BRIQUE", 6, 18
    if "general" in ads: return "IMMEUBLE", "BETON", 7, 20
    return "IMMEUBLE", "PIERRE", 6, 16 # Default

# --- INTERFACE ---

# GESTION DE SESSION (Mémoire)
if 'addr_current' not in st.session_state: st.session_state.addr_current = ""
if 'cam_h' not in st.session_state: st.session_state.cam_h = 0
if 'cam_p' not in st.session_state: st.session_state.cam_p = 10

# --- HEADER ---
st.title("🏢 Estimateur Libert & Cie")
st.markdown("Entrez l'adresse pour générer le diagnostic technique et financier.")

# --- BARRE DE RECHERCHE ---
c_search, c_blank = st.columns([3, 1])
with c_search:
    query = st.text_input("📍 Adresse du projet :", placeholder="Tapez une adresse...")
    # Autocomplete
    if query and len(query) > 4:
        suggestions = get_adresses(query)
        if suggestions:
            selection = st.selectbox("Suggestions :", suggestions, label_visibility="collapsed")
            
            # TRIGGER : Si nouvelle adresse, on lance l'IA
            if selection != st.session_state.addr_current:
                st.session_state.addr_current = selection
                # On charge les valeurs par défaut de l'IA dans la mémoire
                t, m, n, l = ia_init(selection)
                st.session_state.ia_type = t
                st.session_state.ia_mat = m
                st.session_state.ia_niv = n
                st.session_state.ia_larg = l
                # Reset cam
                st.session_state.cam_h = 0
                st.rerun()

# --- AFFICHAGE (Seulement si adresse validée) ---
if st.session_state.addr_current:
    
    # ======================================================
    # ZONE 1 : LE CONTRÔLE EXPERT (Apparaît MAINTENANT)
    # ======================================================
    with st.sidebar:
        st.header("🎛️ Ajustements Techniques")
        st.info("L'IA a pré-configuré ces valeurs. Modifiez-les pour affiner le devis.")
        
        # 1. CAMÉRA
        st.subheader("📷 Vue")
        cc1, cc2, cc3 = st.columns(3)
        if cc1.button("⬅️"): st.session_state.cam_h -= 45
        if cc2.button("🔄"): st.session_state.cam_h += 180
        if cc3.button("➡️"): st.session_state.cam_h += 45
        st.session_state.cam_p = st.slider("Inclinaison", -10, 60, st.session_state.cam_p)

        st.divider()

        # 2. PARAMÈTRES BÂTIMENT (Modifiables)
        st.subheader("🏗️ Structure")
        # On utilise les valeurs IA comme "value" par défaut
        u_type = st.radio("Type", ["IMMEUBLE", "PAVILLON"], index=0 if st.session_state.ia_type=="IMMEUBLE" else 1)
        u_mat = st.selectbox("Matériau", ["PIERRE", "PLATRE", "BRIQUE", "BETON", "PAVILLON"], index=["PIERRE", "PLATRE", "BRIQUE", "BETON", "PAVILLON"].index(st.session_state.ia_mat))
        
        c_n, c_l = st.columns(2)
        u_niv = c_n.number_input("Niveaux (R+)", 1, 15, st.session_state.ia_niv)
        u_larg = c_l.number_input("Largeur (m)", 5, 100, st.session_state.ia_larg)
        
        st.subheader("🛠️ Options")
        u_com = st.checkbox("Commerce RDC (Tunnel)", value=False)
        u_alarme = st.checkbox("Alarme Échafaudage", value=(True if u_type=="IMMEUBLE" else False))
        u_chiens = st.number_input("Chiens-Assis", 0, 10, 0)
        u_porte = st.selectbox("Porte", ["AUCUNE", "PORTE_COCHERE", "PORTE_HALL"])

    # ======================================================
    # ZONE 2 : LE RAPPORT
    # ======================================================
    st.divider()
    
    # VISUEL
    col_img, col_data = st.columns([1.5, 2])
    with col_img:
        st.image(get_image(st.session_state.addr_current, st.session_state.cam_h, st.session_state.cam_p), use_column_width=True)
        st.caption("Utilisez le menu de gauche pour tourner la caméra.")
        
    with col_data:
        st.subheader(f"Analyse : {st.session_state.addr_current}")
        
        # Calculs LIVE (basés sur les inputs de la sidebar)
        h_calc = u_niv * 3.0
        if u_type == "PAVILLON":
            s_calc = int((u_larg * 4) * h_calc)
        else:
            s_calc = int(h_calc * u_larg)
        
        nb_fen = int(s_calc / 12)
        
        # Indicateurs
        k1, k2, k3 = st.columns(3)
        k1.metric("Surface", f"{s_calc} m²")
        k2.metric("Hauteur", f"{h_calc} m")
        k3.metric("Ouvertures", f"{nb_fen} U")
        
        st.success(f"**Système retenu :** {DB[u_mat]['nom']}")
        
        # Badges
        tags = []
        if u_com: tags.append("🏪 Commerce")
        if u_chiens > 0: tags.append("🏠 Toiture")
        st.markdown(" ".join([f"`{t}`" for t in tags]))

    # ======================================================
    # ZONE 3 : LE DEVIS
    # ======================================================
    st.markdown("### 📑 Estimation Détaillée")
    
    total = 0
    
    def add(nom, qte, pu, unit=""):
        tot = qte * pu
        if tot > 0:
            with st.container():
                ca, cb, cc = st.columns([3, 1, 1])
                ca.write(f"**{nom}**")
                cb.write(f"{int(qte)} {unit}")
                cc.write(f"**{tot:,.2f} €**")
                st.markdown("<hr style='margin:0; opacity:0.1'>", unsafe_allow_html=True)
        return tot

    # 1. INSTALLATION
    st.markdown("##### 1. Logistique")
    if u_type == "PAVILLON":
        total += add("Échafaudage Léger", s_calc, DB["ECHAFAUDAGE_PAV"], "m²")
    else:
        total += add("Base Vie & Installations", 1, DB["BASE_VIE"], "Fft")
        total += add("Taxes Voirie", 1, DB["AUTORISATION"], "Fft")
        total += add("Échafaudage Classe 4", s_calc, DB["ECHAFAUDAGE"], "m²")
        if u_com: total += add("Tunnel Protection Public", u_larg, DB["TUNNEL"], "ml")
        if u_alarme: total += add("Alarme Anti-Intrusion", 1, DB["ALARME"], "Fft")
        if u_niv > 6: total += add("Majoration Grande Hauteur", s_calc, DB["MAJORATION_HAUTEUR"], "m²")

    # 2. TRAITEMENT
    st.markdown("##### 2. Façade")
    mat_data = DB[u_mat]
    total += add(f"Nettoyage ({u_mat})", s_calc, mat_data['net'], "m²")
    
    # Piochage intelligent
    s_pioch = int(s_calc * mat_data['ratio'])
    if u_chiens > 0 and u_mat == "PLATRE": s_pioch = int(s_calc * 0.60) # Majoration si toiture complexe
    
    total += add("Maçonnerie & Purge", s_pioch, mat_data['pioch'], "m²")
    total += add("Finition Système", s_calc, mat_data['fin'], "m²")

    # 3. FINITIONS
    st.markdown("##### 3. Finitions")
    total += add("Appuis Zinc", nb_fen, DB["APPUI"], "U")
    total += add("Descentes EP", int(h_calc), DB["DESCENTE"], "ml")
    
    if u_type == "IMMEUBLE":
        total += add("Garde-Corps", int(nb_fen*0.7), DB["GARDE_CORPS"], "U")
        total += add("Bandeaux Zinc", int(u_larg*2), DB["BANDEAU"], "ml")
    else:
        total += add("Débords de Toit", int(u_larg*4), DB["DEBORD_TOIT"], "ml")
        
    if u_chiens > 0: total += add("Habillage Chiens-Assis", u_chiens, DB["CHIEN_ASSIS"], "U")
    if u_porte != "AUCUNE": total += add(f"Restauration {u_porte}", 1, DB[u_porte], "U")

    # TOTAL
    st.markdown("---")
    c_fin1, c_fin2 = st.columns([2, 1])
    with c_fin2:
        st.markdown(f"""
        <div style="background:#2c3e50;color:white;padding:20px;border-radius:10px;text-align:right">
            <small>TOTAL HT ESTIMÉ</small>
            <h1 style="margin:0">{total:,.2f} €</h1>
        </div>
        """, unsafe_allow_html=True)

else:
    # Message d'accueil si aucune adresse
    st.info("👈 Commencez par saisir une adresse ci-dessus.")