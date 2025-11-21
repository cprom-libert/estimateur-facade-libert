import streamlit as st
import time
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="Estimateur Libert V28 (Intégrale)", layout="wide", page_icon="🏢")

# ==============================================================================
# 🔑 API GOOGLE (GARDER VOTRE CLÉ)
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = "" 

# ==============================================================================
# 1. BASE DE PRIX COMPLÈTE (Celle qui ne doit rien oublier)
# ==============================================================================
DB_PRIX = {
    "LOGISTIQUE": {
        "BASE_VIE": {"titre": "Installation de Chantier & Base Vie", "pourquoi": "Roulotte, WC, Cantonnement, Barrières.", "pu": 4500.00, "unit": "Forfait"},
        "AUTORISATION": {"titre": "Taxes de Voirie (ODP)", "pourquoi": "Redevance municipale occupation trottoir.", "pu": 605.00, "unit": "Forfait"},
        "ECHAFAUDAGE": {"titre": "Échafaudage Tubulaire Classe 4", "pourquoi": "Structure lourde pour IGH/Immeuble.", "pu": 39.90, "unit": "m²"},
        "ECHAFAUDAGE_PAV": {"titre": "Échafaudage Léger / Roulant", "pourquoi": "Structure adaptée maison individuelle.", "pu": 28.00, "unit": "m²"},
        "TUNNEL": {"titre": "Tunnel de Protection Public", "pourquoi": "Obligatoire au-dessus des vitrines/commerces.", "pu": 65.00, "unit": "ml"},
        "ALARME": {"titre": "Alarme Anti-Intrusion", "pourquoi": "Sécurisation des échafaudages (Zone dense).", "pu": 2070.00, "unit": "Forfait"}
    },
    "FACADES": { 
        "PLATRE_ANCIEN": {"titre": "Restauration Plâtre (Lourd)", "nettoyage": 16.50, "piochage": 150.00, "finition": 95.00, "ratio_degats": 0.50, "desc": "Décapage + Purge maçonnerie + Micro-mortier"},
        "PIERRE_TAILLE": {"titre": "Ravalement Pierre de Taille", "nettoyage": 28.00, "piochage": 85.00, "finition": 48.00, "ratio_degats": 0.10, "desc": "Hydrogommage + Ragréage + Minéralisation"},
        "BRIQUE": {"titre": "Restauration Brique", "nettoyage": 35.00, "piochage": 120.00, "finition": 25.00, "ratio_degats": 0.15, "desc": "Nettoyage chimique + Changement briques + Hydrofuge"},
        "BETON": {"titre": "Ravalement Technique D3", "nettoyage": 12.00, "piochage": 45.00, "finition": 58.00, "ratio_degats": 0.05, "desc": "Lavage HP + Passivation fers + RPE Armé"},
        "PAVILLON_ENDUIT": {"titre": "Ravalement Maison I3", "nettoyage": 18.00, "piochage": 45.00, "finition": 42.00, "ratio_degats": 0.10, "desc": "Lavage + Reprise fissures + RPE Souple"}
    },
    "BOISERIE": {
        "PORTE_COCHERE": {"titre": "Restauration Porte Cochère", "pourquoi": "Décapage thermique, greffes, lasure.", "pu": 3200.00, "unit": "U"},
        "PORTE_ENTREE": {"titre": "Peinture Porte Hall", "pourquoi": "Égrenage et peinture laque.", "pu": 850.00, "unit": "U"},
        "DEBORD_TOIT": {"titre": "Lasure Débords de Toit", "pourquoi": "Protection des planches de rive (Pavillon).", "pu": 45.00, "unit": "ml"}
    },
    "ZINGUERIE": {
        "APPUI": {"titre": "Appuis de Fenêtre (Zinc)", "pourquoi": "Bavette neuve avec larmier.", "pu": 215.00, "unit": "U"},
        "DESCENTE": {"titre": "Descentes EP (Zinc/Fonte)", "pourquoi": "Remplacement complet.", "pu": 165.00, "unit": "ml"},
        "GARDE_CORPS": {"titre": "Peinture Garde-corps", "pourquoi": "Traitement antirouille ferronnerie.", "pu": 160.00, "unit": "U"},
        "BANDEAU": {"titre": "Couvre-Murette (Zinc)", "pourquoi": "Protection des bandeaux saillants.", "pu": 178.00, "unit": "ml"},
        "CHIEN_ASSIS": {"titre": "Habillage Chien-Assis", "pourquoi": "Rénovation zinc et jouées lucarne.", "pu": 950.00, "unit": "U"}
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
        return f"https://maps.googleapis.com/maps/api/streetview?size=640x480&location={adresse}&fov=110&heading={heading}&pitch={pitch}&key={GOOGLE_API_KEY}"
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Immeuble_parisien.jpg/800px-Immeuble_parisien.jpg"

def pre_analyse_ia(adresse):
    """Détection initiale pour pré-remplir les champs"""
    ads = adresse.lower()
    
    # TYPE DE BIEN
    if "allee" in ads or "chemin" in ads or "impasse" in ads:
        type_bien = "PAVILLON"
        profil = "PAVILLON_ENDUIT"
        etages = 2
        largeur = 10
    else:
        type_bien = "IMMEUBLE"
        etages = 5
        largeur = 15
        # Profil Immeuble
        if "sebastien" in ads or "faubourg" in ads: profil = "PLATRE_ANCIEN"
        elif "pascal" in ads: profil = "BRIQUE"
        elif "general" in ads: profil = "BETON"
        else: profil = "PIERRE_TAILLE"

    return {"type": type_bien, "profil": profil, "etages": etages, "largeur": largeur, "annee": "Inconnue"}

# ==============================================================================
# 3. INTERFACE UTILISATEUR
# ==============================================================================

# --- SIDEBAR : CENTRE DE CONTRÔLE TOTAL ---
with st.sidebar:
    st.header("🎛️ Paramètres Expert")
    
    # 1. IMAGE
    st.subheader("📷 Vue Façade")
    cam_h = st.slider("Rotation", 0, 360, 0, label_visibility="collapsed")
    cam_p = st.slider("Inclinaison", -10, 45, 10, label_visibility="collapsed")
    
    st.divider()
    
    # 2. CONFIGURATION BÂTIMENT (Le Container sera rempli après l'adresse)
    container_config = st.container()

# --- PAGE PRINCIPALE ---
st.title("🏢 Estimateur Libert V28 (Intégrale)")

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

# --- MOTEUR DE CALCUL ---
if st.session_state.ia_data:
    d = st.session_state.ia_data
    
    # --- REMPLISSAGE SIDEBAR (CONTROLES MANUELS) ---
    with container_config:
        # A. TYPE & DIMENSIONS
        st.subheader("1. Structure")
        v_type = st.radio("Type de Bien", ["IMMEUBLE", "PAVILLON"], index=0 if d['type']=="IMMEUBLE" else 1, horizontal=True)
        
        c_etg, c_larg = st.columns(2)
        with c_etg: v_etages = st.number_input("Niveaux (R+)", value=d['etages'], min_value=1)
        with c_larg: v_largeur = st.number_input("Largeur (m)", value=d['largeur'], min_value=5)
        
        # B. MATÉRIAU
        st.subheader("2. Matériau Façade")
        opts_mat = list(DB_PRIX["FACADES"].keys())
        idx_mat = opts_mat.index(d['profil']) if d['profil'] in opts_mat else 0
        v_profil = st.selectbox("Support dominant", opts_mat, index=idx_mat)
        
        # C. DÉTAILS & OPTIONS (C'est là qu'on remet tout ce qui manquait !)
        st.subheader("3. Points Singuliers")
        
        # Options Immeuble
        if v_type == "IMMEUBLE":
            v_com = st.checkbox("Commerces au RDC (Tunnel)", value=False)
            v_alarme = st.checkbox("Zone sensible (Alarme)", value=True)
            v_porte_type = st.selectbox("Menuiserie Entrée", ["PORTE_COCHERE", "PORTE_ENTREE", "AUCUNE"])
            v_chiens = st.number_input("Chiens-Assis (Toit)", value=0, min_value=0)
        else:
            v_com = False
            v_alarme = False
            v_porte_type = "AUCUNE" # Souvent inclus dans lot menuiserie pavillon
            v_chiens = st.number_input("Lucarnes", value=0)
            
        # Quantités ajustables
        st.caption("Quantités estimées (Ajustables)")
        
        # Calculs auto pour pré-remplir
        calc_h = v_etages * 3.0
        if v_type == "PAVILLON":
            calc_s = (v_largeur * 4) * calc_h # Périmètre x Hauteur (Approx 4 faces)
        else:
            calc_s = v_largeur * calc_h
            
        calc_fen = int(calc_s / 12)
        
        v_fenetres = st.number_input("Nb Fenêtres", value=calc_fen)
        v_garde_corps = st.number_input("Nb Garde-corps", value=int(v_fenetres*0.6))
        
    # --- AFFICHAGE CENTRAL ---
    st.divider()
    
    # 1. VISUEL
    ci, ct = st.columns([1.5, 2])
    with ci:
        st.image(get_street_view(st.session_state.addr, cam_h, cam_p), caption="Street View Live", use_column_width=True)
    with ct:
        st.subheader("Synthèse Projet")
        st.success(f"**{v_type}** | Support : **{DB_PRIX['FACADES'][v_profil]['titre']}**")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Hauteur", f"{calc_h} m")
        m2.metric("Surface Traitée", f"{calc_s} m²")
        m3.metric("Points Singuliers", f"{v_fenetres + v_chiens} U")
        
        # Tags actifs
        tags = []
        if v_com: tags.append("🏪 Commerce (Tunnel)")
        if v_chiens > 0: tags.append(f"🏠 {v_chiens} Chiens-assis")
        if v_porte_type != "AUCUNE": tags.append("🚪 Porte incluse")
        st.write(" ".join([f"`{t}`" for t in tags]))

    # 2. DEVIS (LE COEUR DU SYSTÈME)
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

    # --- SECTION A : LOGISTIQUE ---
    st.markdown("##### 1. Logistique & Accès")
    # Base vie
    total += add_row("🚧", DB_PRIX["LOGISTIQUE"]["BASE_VIE"]["titre"], DB_PRIX["LOGISTIQUE"]["BASE_VIE"]["pourquoi"], 1, DB_PRIX["LOGISTIQUE"]["BASE_VIE"]["pu"], "Forfait")
    
    # Echafaudage (Différent si Pavillon)
    if v_type == "PAVILLON":
        echaf = DB_PRIX["LOGISTIQUE"]["ECHAFAUDAGE_PAV"]
    else:
        echaf = DB_PRIX["LOGISTIQUE"]["ECHAFAUDAGE"]
        # Taxe voirie (rarement sur pavillon)
        taxe = DB_PRIX["LOGISTIQUE"]["AUTORISATION"]
        total += add_row("📜", taxe["titre"], taxe["pourquoi"], 1, taxe["pu"], "Forfait")
        
    total += add_row("🛡️", echaf["titre"], echaf["pourquoi"], calc_s, echaf["pu"], "m²")
    
    # Options Immeuble
    if v_com:
        tun = DB_PRIX["LOGISTIQUE"]["TUNNEL"]
        total += add_row("🚇", tun["titre"], tun["pourquoi"], v_largeur, tun["pu"], "ml")
    if v_alarme and v_type == "IMMEUBLE":
        ala = DB_PRIX["LOGISTIQUE"]["ALARME"]
        total += add_row("🚨", ala["titre"], ala["pourquoi"], 1, ala["pu"], "Forfait")

    # --- SECTION B : FAÇADE ---
    st.markdown("##### 2. Traitement des Façades")
    # Nettoyage
    total += add_row("💦", f"Nettoyage ({v_profil})", prof_data["desc"], calc_s, prof_data["nettoyage"], "m²")
    
    # Piochage (Surface calculée par ratio)
    s_pioch = int(calc_s * prof_data["ratio_degats"])
    # Si on a coché "Chiens assis", on augmente le risque piochage (toiture complexe)
    if v_chiens > 0 and v_profil == "PLATRE_ANCIEN": s_pioch = int(calc_s * 0.60)
        
    total += add_row("🧱", "Piochage & Maçonnerie", "Purge et reconstitution des fonds.", s_pioch, prof_data["piochage"], "m²")
    
    # Finition
    total += add_row("🎨", "Finition Système", prof_data["desc"], calc_s, prof_data["finition"], "m²")

    # --- SECTION C : SINGULIERS & BOISERIE ---
    st.markdown("##### 3. Finitions & Points Singuliers")
    
    # Boiseries
    if v_porte_type != "AUCUNE":
        item_porte = DB_PRIX["BOISERIE"][v_porte_type]
        total += add_row("🚪", item_porte["titre"], item_porte["pourquoi"], 1, item_porte["pu"], "U")
    
    if v_type == "PAVILLON":
        deb = DB_PRIX["BOISERIE"]["DEBORD_TOIT"]
        perim = v_largeur * 4 # Approx
        total += add_row("🏠", deb["titre"], deb["pourquoi"], perim, deb["pu"], "ml")

    # Zinc
    zp = DB_PRIX["ZINGUERIE"]
    total += add_row("🌧️", zp["APPUI"]["titre"], zp["APPUI"]["pourquoi"], v_fenetres, zp["APPUI"]["pu"], "U")
    total += add_row("⬇️", zp["DESCENTE"]["titre"], zp["DESCENTE"]["pourquoi"], int(calc_h), zp["DESCENTE"]["pu"], "ml")
    
    if v_type == "IMMEUBLE":
        total += add_row("🏛️", zp["BANDEAU"]["titre"], zp["BANDEAU"]["pourquoi"], int(v_largeur*2), zp["BANDEAU"]["pu"], "ml")
    
    if v_garde_corps > 0:
        total += add_row("🖌️", zp["GARDE_CORPS"]["titre"], zp["GARDE_CORPS"]["pourquoi"], v_garde_corps, zp["GARDE_CORPS"]["pu"], "U")
        
    if v_chiens > 0:
        total += add_row("🏠", zp["CHIEN_ASSIS"]["titre"], zp["CHIEN_ASSIS"]["pourquoi"], v_chiens, zp["CHIEN_ASSIS"]["pu"], "U")

    # TOTAL
    st.markdown("---")
    c_tot_1, c_tot_2 = st.columns([2, 1])
    with c_tot_2:
        st.markdown(f"""
        <div style="background:#2c3e50;color:white;padding:20px;border-radius:10px;text-align:right">
            <small>TOTAL HT ESTIMÉ</small>
            <h1 style="margin:0">{total:,.2f} €</h1>
        </div>
        """, unsafe_allow_html=True)

elif st.session_state.addr == "":
    st.info("👈 Entrez une adresse pour commencer.")