import streamlit as st
import time
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="Estimateur Libert V29 (Cadrage)", layout="wide", page_icon="🎯")

# ==============================================================================
# 🔑 API GOOGLE (VOTRE CLÉ)
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = ""

# ==============================================================================
# 1. BASE DE PRIX (INCHANGÉE)
# ==============================================================================
DB_PRIX = {
    "LOGISTIQUE": {
        "BASE_VIE": {"titre": "Installation & Base Vie", "pourquoi": "Roulotte, WC, Cantonnement.", "pu": 4500.00, "unit": "Forfait"},
        "AUTORISATION": {"titre": "Taxes Voirie", "pourquoi": "Redevance municipale.", "pu": 605.00, "unit": "Forfait"},
        "ECHAFAUDAGE": {"titre": "Échafaudage Tubulaire", "pourquoi": "Classe 4 + filets.", "pu": 39.90, "unit": "m²"},
        "ECHAFAUDAGE_PAV": {"titre": "Échafaudage Léger", "pourquoi": "Structure adaptée pavillon.", "pu": 28.00, "unit": "m²"},
        "TUNNEL": {"titre": "Tunnel Public", "pourquoi": "Sécurité piétons (Commerce).", "pu": 60.00, "unit": "ml"},
        "MAJORATION_HAUTEUR": {"titre": "Majoration Grande Hauteur", "pourquoi": "Manutention > R+5.", "pu": 15.00, "unit": "m²"}
    },
    "FACADES": { 
        "PLATRE_ANCIEN": {"titre": "Restauration Plâtre (Lourd)", "nettoyage": 16.50, "piochage": 150.00, "finition": 95.00, "ratio_degats": 0.50, "desc": "Décapage + Purge maçonnerie + Micro-mortier"},
        "PIERRE_TAILLE": {"titre": "Ravalement Pierre de Taille", "nettoyage": 28.00, "piochage": 85.00, "finition": 48.00, "ratio_degats": 0.10, "desc": "Hydrogommage + Ragréage + Minéralisation"},
        "BRIQUE": {"titre": "Restauration Brique", "nettoyage": 35.00, "piochage": 120.00, "finition": 25.00, "ratio_degats": 0.15, "desc": "Nettoyage chimique + Changement briques + Hydrofuge"},
        "BETON": {"titre": "Ravalement Technique D3", "nettoyage": 12.00, "piochage": 45.00, "finition": 58.00, "ratio_degats": 0.05, "desc": "Lavage HP + Passivation fers + RPE Armé"},
        "PAVILLON_ENDUIT": {"titre": "Ravalement Maison I3", "nettoyage": 18.00, "piochage": 45.00, "finition": 42.00, "ratio_degats": 0.10, "desc": "Lavage + Reprise fissures + RPE Souple"}
    },
    "BOISERIE": {
        "PORTE_COCHERE": {"titre": "Restauration Porte Cochère", "pourquoi": "Décapage, greffes, lasure.", "pu": 3200.00, "unit": "U"},
        "PORTE_ENTREE": {"titre": "Peinture Porte Hall", "pourquoi": "Égrenage et laque.", "pu": 850.00, "unit": "U"},
        "DEBORD_TOIT": {"titre": "Lasure Débords de Toit", "pourquoi": "Protection planches de rive.", "pu": 45.00, "unit": "ml"}
    },
    "ZINGUERIE": {
        "APPUI": {"titre": "Appuis de Fenêtre (Zinc)", "pourquoi": "Bavette neuve.", "pu": 215.00, "unit": "U"},
        "DESCENTE": {"titre": "Descentes EP", "pourquoi": "Remplacement Zinc/Fonte.", "pu": 165.00, "unit": "ml"},
        "GARDE_CORPS": {"titre": "Peinture Garde-corps", "pourquoi": "Traitement antirouille.", "pu": 160.00, "unit": "U"},
        "BANDEAU": {"titre": "Couvre-Murette (Zinc)", "pourquoi": "Protection bandeaux.", "pu": 178.00, "unit": "ml"},
        "CHIEN_ASSIS": {"titre": "Habillage Chien-Assis", "pourquoi": "Rénovation zinc lucarne.", "pu": 950.00, "unit": "U"}
    }
}

# ==============================================================================
# 2. FONCTIONS TECHNIQUES
# ==============================================================================
def get_adresses_api(query):
    if not query or len(query) < 3: return []
    try:
        r = requests.get(f"https://api-adresse.data.gouv.fr/search/?q={query}&limit=5")
        return [f['properties']['label'] for f in r.json()['features']] if r.status_code == 200 else []
    except: return []

def get_street_view(adresse, heading, pitch):
    if GOOGLE_API_KEY and len(GOOGLE_API_KEY) > 10:
        # fov=100 pour voir large, pitch=10 pour voir un peu en hauteur
        return f"https://maps.googleapis.com/maps/api/streetview?size=640x480&location={adresse}&fov=100&heading={heading}&pitch={pitch}&key={GOOGLE_API_KEY}"
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Immeuble_parisien.jpg/800px-Immeuble_parisien.jpg"

def pre_analyse_ia(adresse):
    ads = adresse.lower()
    if "allee" in ads or "chemin" in ads or "impasse" in ads:
        return {"type": "PAVILLON", "profil": "PAVILLON_ENDUIT", "etages": 2, "largeur": 10, "annee": "Inconnue"}
    else:
        type_bien = "IMMEUBLE"
        etages = 5
        largeur = 15
        if "sebastien" in ads or "faubourg" in ads: profil = "PLATRE_ANCIEN"
        elif "pascal" in ads: profil = "BRIQUE"
        elif "general" in ads: profil = "BETON"
        else: profil = "PIERRE_TAILLE"
        return {"type": type_bien, "profil": profil, "etages": etages, "largeur": largeur, "annee": "Inconnue"}

# ==============================================================================
# 3. INTERFACE UTILISATEUR
# ==============================================================================

# GESTION DE L'ÉTAT DE LA CAMÉRA (Pour les boutons)
if 'cam_heading' not in st.session_state: st.session_state.cam_heading = 0
if 'cam_pitch' not in st.session_state: st.session_state.cam_pitch = 10

# Fonctions de rotation
def rotate_cam(angle):
    st.session_state.cam_heading = (st.session_state.cam_heading + angle) % 360

# --- SIDEBAR : CENTRE DE CONTRÔLE ---
with st.sidebar:
    st.header("🎯 Cadrage Façade")
    st.info("Si l'image ne montre pas le bon bâtiment, utilisez ces boutons pour tourner la caméra.")
    
    # BOUTONS DE ROTATION RAPIDE
    col_r1, col_r2, col_r3 = st.columns(3)
    with col_r1: 
        st.button("⬅️", on_click=rotate_cam, args=(-45,), help="Pivoter Gauche 45°")
    with col_r2: 
        st.button("🔄", on_click=rotate_cam, args=(180,), help="Demi-tour (Trottoir d'en face)")
    with col_r3: 
        st.button("➡️", on_click=rotate_cam, args=(45,), help="Pivoter Droite 45°")

    # SLIDERS DE PRÉCISION
    st.session_state.cam_heading = st.slider("Rotation Fine (360°)", 0, 360, st.session_state.cam_heading)
    st.session_state.cam_pitch = st.slider("Inclinaison (Voir Toit)", -10, 45, st.session_state.cam_pitch)
    
    st.divider()
    st.header("🎛️ Paramètres Expert")
    container_config = st.container()

# --- PAGE PRINCIPALE ---
st.title("🏢 Estimateur Libert V29 (Précision)")

# Gestion état
if 'addr' not in st.session_state: st.session_state.addr = ""
if 'ia_data' not in st.session_state: st.session_state.ia_data = None

# Barre Recherche
c1, c2 = st.columns([3, 1])
with c1:
    q = st.text_input("Adresse :", value=st.session_state.addr, placeholder="Ex: 159 rue du faubourg saint antoine...")
    final_addr = None
    if q and len(q)>4:
        opts = get_adresses_api(q)
        if opts: final_addr = st.selectbox("📍 Validation :", opts)
        else: final_addr = q
with c2:
    st.write(""); st.write("")
    if st.button("CHARGER", type="primary", use_container_width=True):
        if final_addr:
            st.session_state.ia_data = pre_analyse_ia(final_addr)
            st.session_state.addr = final_addr
            # Reset caméra par défaut au chargement
            st.session_state.cam_heading = 0 

# --- MOTEUR DE CALCUL ---
if st.session_state.ia_data:
    d = st.session_state.ia_data
    
    # --- REMPLISSAGE SIDEBAR ---
    with container_config:
        st.subheader("1. Structure")
        v_type = st.radio("Type de Bien", ["IMMEUBLE", "PAVILLON"], index=0 if d['type']=="IMMEUBLE" else 1, horizontal=True)
        
        c_etg, c_larg = st.columns(2)
        with c_etg: v_etages = st.number_input("Niveaux (R+)", value=d['etages'], min_value=1)
        with c_larg: v_largeur = st.number_input("Largeur (m)", value=d['largeur'], min_value=5)
        
        st.subheader("2. Matériau")
        opts_mat = list(DB_PRIX["FACADES"].keys())
        idx_mat = opts_mat.index(d['profil']) if d['profil'] in opts_mat else 0
        v_profil = st.selectbox("Support dominant", opts_mat, index=idx_mat)
        
        st.subheader("3. Points Singuliers")
        if v_type == "IMMEUBLE":
            v_com = st.checkbox("Commerces RDC", value=False)
            v_alarme = st.checkbox("Alarme", value=True)
            v_porte_type = st.selectbox("Porte Entrée", ["PORTE_COCHERE", "PORTE_ENTREE", "AUCUNE"])
            v_chiens = st.number_input("Chiens-Assis", value=0, min_value=0)
        else:
            v_com = False; v_alarme = False
            v_porte_type = "AUCUNE"
            v_chiens = st.number_input("Lucarnes", value=0)
            
        st.caption("--- Ajustement Quantités ---")
        calc_h = v_etages * 3.0
        if v_type == "PAVILLON":
            calc_s = (v_largeur * 4) * calc_h
        else:
            calc_s = v_largeur * calc_h
            
        v_fenetres = st.number_input("Nb Fenêtres", value=int(calc_s / 12))
        v_garde_corps = st.number_input("Nb Garde-corps", value=int(v_fenetres*0.6))
        
    # --- VISUEL ---
    st.divider()
    ci, ct = st.columns([1.5, 2])
    with ci:
        # Image utilisant le HEADING du session_state
        st.image(get_street_view(st.session_state.addr, st.session_state.cam_heading, st.session_state.cam_pitch), caption=f"Orientation Caméra : {st.session_state.cam_heading}°", use_column_width=True)
        st.caption("Utilisez les boutons ⬅️ 🔄 ➡️ dans le menu de gauche si la façade n'est pas visible.")
        
    with ct:
        st.subheader("Synthèse Projet")
        st.success(f"**{v_type}** | Support : **{DB_PRIX['FACADES'][v_profil]['titre']}**")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Hauteur", f"{calc_h} m")
        m2.metric("Surface Traitée", f"{calc_s} m²")
        m3.metric("Points Singuliers", f"{v_fenetres + v_chiens} U")
        
        tags = []
        if v_com: tags.append("🏪 Commerce")
        if v_chiens > 0: tags.append(f"🏠 {v_chiens} Chiens-assis")
        if v_porte_type != "AUCUNE": tags.append("🚪 Porte")
        st.markdown(" ".join([f"`{t}`" for t in tags]))

    # --- DEVIS ---
    st.markdown("### 📑 Devis Détaillé")
    total = 0
    prof_data = DB_PRIX["FACADES"][v_profil]
    
    def add_row(icon, titre, pourquoi, qte, pu, unit):
        p = qte * pu
        with st.container():
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.markdown(f"**{icon} {titre}**\n<br><span style='color:grey;font-size:0.8em'>{pourquoi}</span>", unsafe_allow_html=True)
            c2.markdown(f"<div style='text-align:center'>{int(qte) if unit!='m²' else int(qte)} {unit}</div>", unsafe_allow_html=True)
            c3.markdown(f"<div style='text-align:right'><b>{p:,.2f} €</b></div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:5px 0; opacity:0.1'>", unsafe_allow_html=True)
        return p

    st.markdown("##### 1. Logistique & Accès")
    if v_type == "PAVILLON":
        echaf = DB_PRIX["LOGISTIQUE"]["ECHAFAUDAGE_PAV"]
        total += add_row("🛡️", echaf["titre"], echaf["pourquoi"], calc_s, echaf["pu"], "m²")
    else:
        total += add_row("🚧", DB_PRIX["LOGISTIQUE"]["BASE_VIE"]["titre"], DB_PRIX["LOGISTIQUE"]["BASE_VIE"]["pourquoi"], 1, DB_PRIX["LOGISTIQUE"]["BASE_VIE"]["pu"], "Forfait")
        total += add_row("🛡️", DB_PRIX["LOGISTIQUE"]["ECHAFAUDAGE"]["titre"], DB_PRIX["LOGISTIQUE"]["ECHAFAUDAGE"]["pourquoi"], calc_s, DB_PRIX["LOGISTIQUE"]["ECHAFAUDAGE"]["pu"], "m²")
        total += add_row("📜", DB_PRIX["LOGISTIQUE"]["AUTORISATION"]["titre"], DB_PRIX["LOGISTIQUE"]["AUTORISATION"]["pourquoi"], 1, DB_PRIX["LOGISTIQUE"]["AUTORISATION"]["pu"], "Forfait")
    
    if v_com:
        tun = DB_PRIX["LOGISTIQUE"]["TUNNEL"]
        total += add_row("🚇", tun["titre"], tun["pourquoi"], v_largeur, tun["pu"], "ml")
    if v_alarme and v_type == "IMMEUBLE":
        ala = DB_PRIX["LOGISTIQUE"]["ALARME"]
        total += add_row("🚨", ala["titre"], ala["pourquoi"], 1, ala["pu"], "Forfait")

    st.markdown("##### 2. Traitement des Façades")
    total += add_row("💦", f"Nettoyage ({v_profil})", prof_data["desc"], calc_s, prof_data["nettoyage"], "m²")
    
    s_pioch = int(calc_s * prof_data["ratio_degats"])
    if v_chiens > 0 and v_profil == "PLATRE_ANCIEN": s_pioch = int(calc_s * 0.60)
    total += add_row("🧱", "Piochage & Maçonnerie", "Purge et reconstitution des fonds.", s_pioch, prof_data["piochage"], "m²")
    total += add_row("🎨", "Finition Système", prof_data["desc"], calc_s, prof_data["finition"], "m²")

    st.markdown("##### 3. Finitions & Points Singuliers")
    if v_porte_type != "AUCUNE":
        item_porte = DB_PRIX["BOISERIE"][v_porte_type]
        total += add_row("🚪", item_porte["titre"], item_porte["pourquoi"], 1, item_porte["pu"], "U")
    
    if v_type == "PAVILLON":
        deb = DB_PRIX["BOISERIE"]["DEBORD_TOIT"]
        perim = v_largeur * 4 
        total += add_row("🏠", deb["titre"], deb["pourquoi"], perim, deb["pu"], "ml")

    zp = DB_PRIX["ZINGUERIE"]
    total += add_row("🌧️", zp["APPUI"]["titre"], zp["APPUI"]["pourquoi"], v_fenetres, zp["APPUI"]["pu"], "U")
    total += add_row("⬇️", zp["DESCENTE"]["titre"], zp["DESCENTE"]["pourquoi"], int(calc_h), zp["DESCENTE"]["pu"], "ml")
    
    if v_type == "IMMEUBLE":
        total += add_row("🏛️", zp["BANDEAU"]["titre"], zp["BANDEAU"]["pourquoi"], int(v_largeur*2), zp["BANDEAU"]["pu"], "ml")
    
    if v_garde_corps > 0:
        total += add_row("🖌️", zp["GARDE_CORPS"]["titre"], zp["GARDE_CORPS"]["pourquoi"], v_garde_corps, zp["GARDE_CORPS"]["pu"], "U")
        
    if v_chiens > 0:
        total += add_row("🏠", zp["CHIEN_ASSIS"]["titre"], zp["CHIEN_ASSIS"]["pourquoi"], v_chiens, zp["CHIEN_ASSIS"]["pu"], "U")

    st.markdown("---")
    col_fin1, col_fin2 = st.columns([2, 1])
    with col_fin2:
        st.markdown(f"""
        <div style="background:#2c3e50;color:white;padding:20px;border-radius:10px;text-align:right">
            <small>TOTAL HT ESTIMÉ</small>
            <h1 style="margin:0">{total:,.2f} €</h1>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.addr == "":
    st.info("👈 Commencez par entrer une adresse.")