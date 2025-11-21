import streamlit as st
import time
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="Estimateur Libert V41 (Fix Photo)", layout="wide", page_icon="📸")

# ==============================================================================
# 1. SÉCURITÉ API (GESTION PROPRE)
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = "" # Pas de clé ? Pas de panique, on passera en mode illustration.

# ==============================================================================
# 2. FONCTION PHOTO (Celle qui posait problème, maintenant corrigée)
# ==============================================================================
def get_facade_image(adresse, style_backup):
    """
    Génère l'image de la façade.
    - Si Clé API présente : Retourne la vraie vue Street View orientée vers le haut.
    - Sinon : Retourne une image d'illustration selon le style.
    """
    # A. CAS AVEC CLÉ GOOGLE (La vraie photo)
    if GOOGLE_API_KEY and len(GOOGLE_API_KEY) > 10:
        base_url = "https://maps.googleapis.com/maps/api/streetview"
        
        # PARAMÈTRES CLÉS POUR VOIR LE BÂTIMENT ENTIER :
        # size=640x640 : Taille max standard
        # fov=110 : Grand angle (dézoom) pour voir la largeur
        # pitch=20 : Caméra relevée de 20° pour voir les corniches et le toit
        return f"{base_url}?size=640x640&location={adresse}&fov=110&pitch=20&key={GOOGLE_API_KEY}"
    
    # B. CAS SANS CLÉ (Images de secours fiables)
    if "Faubourien" in style_backup: 
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/14_rue_Saint-S%C3%A9bastien_Paris_11.jpg/800px-14_rue_Saint-S%C3%A9bastien_Paris_11.jpg"
    elif "Haussmannien" in style_backup: 
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Paris_-_Immeuble_bld_Raspail.jpg/800px-Paris_-_Immeuble_bld_Raspail.jpg"
    elif "Moderne" in style_backup: 
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Immeuble_d%27habitation_HBM.jpg/800px-Immeuble_d%27habitation_HBM.jpg"
    else: 
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Immeuble_parisien.jpg/800px-Immeuble_parisien.jpg"

# ==============================================================================
# 3. AUTRES FONCTIONS (Recherche & IA)
# ==============================================================================
def get_adresses_api(query):
    if not query or len(query) < 3: return []
    try:
        r = requests.get(f"https://api-adresse.data.gouv.fr/search/?q={query}&limit=5")
        return [f['properties']['label'] for f in r.json()['features']] if r.status_code == 200 else []
    except: return []

def ia_init(adresse):
    ads = adresse.lower()
    if "allee" in ads or "chemin" in ads or "villa" in ads:
        return "PAVILLON", "PAVILLON_ENDUIT", 2, 10
    
    if "sebastien" in ads or "faubourg" in ads: return "IMMEUBLE", "PLATRE_ANCIEN", 4, 14
    if "pascal" in ads: return "IMMEUBLE", "BRIQUE", 6, 18
    if "general" in ads: return "IMMEUBLE", "BETON", 7, 20
    return "IMMEUBLE", "PIERRE_TAILLE", 6, 16

# ==============================================================================
# 4. BASE DE PRIX
# ==============================================================================
DB_PRIX = {
    "LOGISTIQUE": {
        "BASE_VIE": 4500.00, "AUTORISATION": 605.00, "ECHAFAUDAGE": 39.90, 
        "ECHAFAUDAGE_PAV": 28.00, "FILET": 13.00, "TUNNEL": 60.00, "ALARME": 2070.00, "MAJORATION_HAUTEUR": 15.00
    },
    "FACADES": { 
        "PLATRE_ANCIEN": {"titre": "Restauration Plâtre", "net": 16.50, "pioch": 150.00, "fin": 95.00, "ratio": 0.50, "desc": "Décapage + Purge lourde"},
        "PIERRE_TAILLE": {"titre": "Ravalement Pierre", "net": 28.00, "pioch": 85.00, "fin": 48.00, "ratio": 0.10, "desc": "Hydrogommage + Minéralisation"},
        "BRIQUE": {"titre": "Restauration Brique", "net": 35.00, "pioch": 120.00, "fin": 25.00, "ratio": 0.15, "desc": "Nettoyage chimique + Hydrofuge"},
        "BETON": {"titre": "Ravalement D3", "net": 12.00, "pioch": 45.00, "fin": 58.00, "ratio": 0.05, "desc": "Lavage HP + RPE Armé"},
        "PAVILLON_ENDUIT": {"titre": "Ravalement Pavillon", "net": 18.00, "pioch": 45.00, "fin": 42.00, "ratio": 0.10, "desc": "Lavage + RPE"}
    },
    "SINGULIERS": {
        "APPUI": 215.00, "DESCENTE": 165.00, "GARDE_CORPS": 160.00, "BANDEAU": 178.00, "CHIEN_ASSIS": 950.00,
        "PORTE_COCHERE": 3200.00, "PORTE_HALL": 850.00, "DEBORD_TOIT": 45.00
    }
}

# ==============================================================================
# 5. INTERFACE UTILISATEUR
# ==============================================================================

# Session
if 'addr_label' not in st.session_state: st.session_state.addr_label = ""

# SIDEBAR
with st.sidebar:
    st.header("🎛️ Paramètres")
    container_params = st.container()

# MAIN
st.title("🏢 Estimateur Libert V41")

c_search, c_go = st.columns([3, 1])
with c_search:
    query = st.text_input("Adresse :", placeholder="Tapez une adresse...")
    if query and len(query) > 4:
        features = get_adresses_api(query)
        if features:
            selected_label = st.selectbox("📍 Suggestions :", features, label_visibility="collapsed")
            if selected_label != st.session_state.addr_label:
                st.session_state.addr_label = selected_label
                t, m, n, l = ia_init(selected_label)
                st.session_state.ia_type = t
                st.session_state.ia_mat = m
                st.session_state.ia_niv = n
                st.session_state.ia_larg = l
                st.rerun()

# RAPPORT
if st.session_state.addr_label:
    
    # 1. Controles Sidebar
    with container_params:
        u_type = st.radio("Type", ["IMMEUBLE", "PAVILLON"], index=0 if st.session_state.ia_type=="IMMEUBLE" else 1)
        u_mat = st.selectbox("Support", list(DB_PRIX["FACADES"].keys()), index=list(DB_PRIX["FACADES"].keys()).index(st.session_state.ia_mat))
        
        cn, cl = st.columns(2)
        u_niv = cn.number_input("Niveaux (R+)", 1, 15, st.session_state.ia_niv)
        u_larg = cl.number_input("Largeur (m)", 5, 100, st.session_state.ia_larg)
        
        st.subheader("Options")
        u_com = st.checkbox("Commerce RDC", value=False)
        u_alarme = st.checkbox("Alarme", value=(True if u_type=="IMMEUBLE" else False))
        u_chiens = st.number_input("Chiens-Assis", 0, 10, 0)
        u_porte = st.selectbox("Porte", ["PORTE_COCHERE", "PORTE_ENTREE", "AUCUNE"])

    # Calculs
    h_calc = u_niv * 3.0
    s_calc = int(h_calc * u_larg) if u_type == "IMMEUBLE" else int((u_larg * 4) * h_calc)
    nb_fen = int(s_calc / 12)

    # 2. Affichage Photo & Synthèse
    st.divider()
    c_img, c_txt = st.columns([1.5, 2])
    with c_img:
        # APPEL DE LA FONCTION CORRIGÉE
        # On passe l'adresse et le style pour le backup
        style_friendly = "Haussmannien" if "PIERRE" in u_mat else "Faubourien"
        st.image(get_facade_image(st.session_state.addr_label, style_friendly), use_column_width=True)
        
    with c_txt:
        st.subheader(st.session_state.addr_label)
        k1, k2, k3 = st.columns(3)
        k1.metric("Surface", f"{s_calc} m²")
        k2.metric("Hauteur", f"{h_calc} m")
        k3.metric("Type", DB_PRIX["FACADES"][u_mat]["titre"])

    # 3. Devis
    st.markdown("### 📑 Détail Estimatif")
    total = 0
    
    def add_line(titre, qte, pu, unit):
        tot = qte * pu
        with st.container():
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"**{titre}**")
            c2.write(f"{int(qte)} {unit}")
            c3.write(f"**{tot:,.2f} €**")
            st.markdown("<hr style='margin:2px 0; opacity:0.1'>", unsafe_allow_html=True)
        return tot

    # LOGISTIQUE
    st.markdown("#### 1. Logistique")
    if u_type == "PAVILLON": total += add_line("Échafaudage Léger", s_calc, DB_PRIX["LOGISTIQUE"]["ECHAFAUDAGE_PAV"], "m²")
    else:
        total += add_line("Base Vie", 1, DB_PRIX["LOGISTIQUE"]["BASE_VIE"], "U")
        total += add_line("Taxes Voirie", 1, DB_PRIX["LOGISTIQUE"]["AUTORISATION"], "U")
        total += add_line("Échafaudage Classe 4", s_calc, DB_PRIX["LOGISTIQUE"]["ECHAFAUDAGE"], "m²")
        if u_com: total += add_line("Tunnel Protection", u_larg, DB_PRIX["LOGISTIQUE"]["TUNNEL"], "ml")
        if u_alarme: total += add_line("Alarme", 1, DB_PRIX["LOGISTIQUE"]["ALARME"], "U")
        if u_niv > 6: total += add_line("Majoration Hauteur", s_calc, DB_PRIX["LOGISTIQUE"]["MAJORATION_HAUTEUR"], "m²")

    # FAÇADE
    st.markdown("#### 2. Façade")
    prof = DB_PRIX["FACADES"][u_mat]
    total += add_line(f"Nettoyage ({u_mat})", s_calc, prof['net'], "m²")
    
    s_pioch = int(s_calc * prof['ratio'])
    if u_chiens > 0 and u_mat == "PLATRE_ANCIEN": s_pioch = int(s_calc * 0.60)
    total += add_line("Maçonnerie (Purge)", s_pioch, prof['pioch'], "m²")
    total += add_line("Finition Système", s_calc, prof['fin'], "m²")

    # FINITIONS
    st.markdown("#### 3. Finitions")
    if u_porte != "AUCUNE": total += add_line(f"Restauration {u_porte}", 1, DB_PRIX["BOISERIE"][u_porte], "U")
    if u_type == "PAVILLON": total += add_line("Débords Toit", int(u_larg*4), DB_PRIX["BOISERIE"]["DEBORD_TOIT"], "ml")
    
    total += add_line("Appuis Zinc", nb_fen, DB_PRIX["ZINGUERIE"]["APPUI"], "U")
    total += add_line("Descentes EP", int(h_calc), DB_PRIX["ZINGUERIE"]["DESCENTE"], "ml")
    if u_type == "IMMEUBLE": total += add_line("Bandeaux Zinc", int(u_larg*2), DB_PRIX["ZINGUERIE"]["BANDEAU"], "ml")
    total += add_line("Garde-Corps", int(nb_fen*0.7), DB_PRIX["ZINGUERIE"]["GARDE_CORPS"], "U")
    if u_chiens > 0: total += add_line("Habillage Chiens-Assis", u_chiens, DB_PRIX["ZINGUERIE"]["CHIEN_ASSIS"], "U")

    # TOTAL
    st.markdown("---")
    col_tot, col_vide = st.columns([2, 1])
    with col_tot:
        st.markdown(f"<h2 style='text-align:right'>TOTAL HT : {total:,.2f} €</h2>", unsafe_allow_html=True)

elif st.session_state.addr_label == "":
    st.info("👈 Entrez une adresse.")