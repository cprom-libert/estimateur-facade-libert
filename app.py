import streamlit as st
import time
import requests

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Estimateur Libert & Cie (V33)", layout="wide", page_icon="🏢")

# ==============================================================================
# 1. SÉCURITÉ & API
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = "" # Laisser vide si pas de clé, l'image de secours s'affichera

# ==============================================================================
# 2. BASE DE PRIX EXPERTE (BENCHMARK LIBERT 2025)
# ==============================================================================
DB_PRIX = {
    "LOGISTIQUE": {
        "BASE_VIE": {"titre": "Installation & Base Vie", "pourquoi": "Roulotte, WC, Cantonnement et protections obligatoires.", "pu": 4500.00, "unit": "Forfait"},
        "AUTORISATION": {"titre": "Taxes de Voirie (ODP)", "pourquoi": "Redevance municipale occupation trottoir.", "pu": 605.00, "unit": "Forfait"},
        "ECHAFAUDAGE": {"titre": "Échafaudage Tubulaire", "pourquoi": "Structure classe 4 + filets pare-gravats.", "pu": 39.90, "unit": "m²"},
        "ECHAFAUDAGE_PAV": {"titre": "Échafaudage Léger", "pourquoi": "Structure adaptée pavillon.", "pu": 28.00, "unit": "m²"},
        "TUNNEL": {"titre": "Tunnel Public", "pourquoi": "Sécurité piétons (Commerce).", "pu": 60.00, "unit": "ml"},
        "ALARME": {"titre": "Alarme Échafaudage", "pourquoi": "Système anti-intrusion 24/7.", "pu": 2070.00, "unit": "Forfait"},
        "MAJORATION_HAUTEUR": {"titre": "Majoration Grande Hauteur", "pourquoi": "Manutention supplémentaire au-delà de R+5.", "pu": 15.00, "unit": "m²"}
    },
    "FACADES": { 
        "PLATRE_ANCIEN": { # Faubourg
            "titre": "Restauration Plâtre (Traditionnel)", 
            "nettoyage": 16.50, "piochage": 160.00, "finition": 95.00, "ratio_degats": 0.50, 
            "desc": "Décapage + Purge lourde maçonneries + Micro-mortier"
        },
        "PIERRE_TAILLE": { # Haussmann
            "titre": "Ravalement Pierre de Taille", 
            "nettoyage": 28.00, "piochage": 85.00, "finition": 48.00, "ratio_degats": 0.10, 
            "desc": "Hydrogommage doux + Ragréage ponctuel + Minéralisation"
        },
        "BRIQUE": { # Années 30
            "titre": "Restauration Brique", 
            "nettoyage": 35.00, "piochage": 120.00, "finition": 25.00, "ratio_degats": 0.15, 
            "desc": "Nettoyage chimique + Changement briques + Hydrofuge"
        },
        "BETON": { # Moderne
            "titre": "Ravalement Technique D3", 
            "nettoyage": 12.00, "piochage": 45.00, "finition": 58.00, "ratio_degats": 0.05, 
            "desc": "Lavage HP + Passivation fers + RPE Armé"
        },
        "PAVILLON_ENDUIT": { # Maison
            "titre": "Ravalement Maison I3", 
            "nettoyage": 18.00, "piochage": 45.00, "finition": 42.00, "ratio_degats": 0.10, 
            "desc": "Lavage + Reprise fissures + RPE Souple"
        }
    },
    "BOISERIE": {
        "PORTE_COCHERE": {"titre": "Restauration Porte Cochère", "pourquoi": "Décapage, greffes, lasure.", "pu": 3200.00, "unit": "U"},
        "PORTE_ENTREE": {"titre": "Peinture Porte Hall", "pourquoi": "Égrenage et laque.", "pu": 850.00, "unit": "U"},
        "DEBORD_TOIT": {"titre": "Lasure Débords de Toit", "pourquoi": "Protection planches de rive.", "pu": 45.00, "unit": "ml"}
    },
    "ZINGUERIE": {
        "APPUI": {"titre": "Appuis de Fenêtre (Zinc)", "pourquoi": "Bavette neuve avec larmier.", "pu": 215.00, "unit": "U"},
        "DESCENTE": {"titre": "Descentes EP", "pourquoi": "Remplacement Zinc/Fonte.", "pu": 165.00, "unit": "ml"},
        "GARDE_CORPS": {"titre": "Peinture Garde-corps", "pourquoi": "Traitement antirouille.", "pu": 160.00, "unit": "U"},
        "BANDEAU": {"titre": "Couvre-Murette (Zinc)", "pourquoi": "Protection bandeaux.", "pu": 178.00, "unit": "ml"},
        "CHIEN_ASSIS": {"titre": "Habillage Chien-Assis", "pourquoi": "Rénovation zinc lucarne.", "pu": 950.00, "unit": "U"}
    }
}

# ==============================================================================
# 3. FONCTIONS TECHNIQUES (IMAGE & ADRESSE)
# ==============================================================================
def get_adresses_api(query):
    if not query or len(query) < 3: return []
    try:
        r = requests.get(f"https://api-adresse.data.gouv.fr/search/?q={query}&limit=5")
        return [f['properties']['label'] for f in r.json()['features']] if r.status_code == 200 else []
    except: return []

def get_facade_image(adresse, style_backup, heading=0, pitch=20):
    """
    Récupère l'image Google optimisée pour voir TOUT le bâtiment.
    Pitch=20 par défaut pour regarder vers le toit.
    """
    if GOOGLE_API_KEY and len(GOOGLE_API_KEY) > 10:
        base = "https://maps.googleapis.com/maps/api/streetview"
        return f"{base}?size=640x640&location={adresse}&fov=110&heading={heading}&pitch={pitch}&key={GOOGLE_API_KEY}"
    
    # Images de secours
    if "Faubourien" in style_backup: return "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/14_rue_Saint-S%C3%A9bastien_Paris_11.jpg/800px-14_rue_Saint-S%C3%A9bastien_Paris_11.jpg"
    elif "Haussmannien" in style_backup: return "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Paris_-_Immeuble_bld_Raspail.jpg/800px-Paris_-_Immeuble_bld_Raspail.jpg"
    elif "Moderne" in style_backup: return "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Immeuble_d%27habitation_HBM.jpg/800px-Immeuble_d%27habitation_HBM.jpg"
    else: return "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Immeuble_parisien.jpg/800px-Immeuble_parisien.jpg"

def pre_analyse_ia(adresse):
    ads = adresse.lower()
    
    # 1. Détection Type (Pavillon vs Immeuble)
    if "allee" in ads or "chemin" in ads or "impasse" in ads or "villa" in ads:
        return {"type": "PAVILLON", "profil": "PAVILLON_ENDUIT", "etages": 2, "largeur": 10, "annee": "Inconnue"}
    
    # 2. Détection Profil Immeuble
    type_bien = "IMMEUBLE"
    etages = 5 # Moyenne
    largeur = 15
    
    if "sebastien" in ads or "faubourg" in ads or "temple" in ads: 
        profil = "PLATRE_ANCIEN"
        etages = 4 # Souvent plus bas sauf grand axe
    elif "pascal" in ads or "thibaud" in ads: 
        profil = "PIERRE_BRIQUE" # Brique années 30
    elif "general" in ads or "leclerc" in ads: 
        profil = "BETON"
        etages = 7
    else: 
        profil = "PIERRE_TAILLE" # Haussmann par défaut
        etages = 6

    return {"type": type_bien, "profil": profil, "etages": etages, "largeur": largeur, "annee": "Inconnue"}

# ==============================================================================
# 4. INTERFACE UTILISATEUR
# ==============================================================================

# --- SIDEBAR : CENTRE DE CONTRÔLE ---
with st.sidebar:
    st.header("🎯 Cadrage Photo")
    
    # Gestion État Caméra
    if 'cam_heading' not in st.session_state: st.session_state.cam_heading = 0
    if 'cam_pitch' not in st.session_state: st.session_state.cam_pitch = 20 # Regarde vers le haut par défaut

    def rotate_cam(angle):
        st.session_state.cam_heading = (st.session_state.cam_heading + angle) % 360

    c_r1, c_r2, c_r3 = st.columns(3)
    with c_r1: st.button("⬅️", on_click=rotate_cam, args=(-45,), help="Gauche 45°")
    with c_r2: st.button("🔄", on_click=rotate_cam, args=(180,), help="Demi-tour")
    with c_r3: st.button("➡️", on_click=rotate_cam, args=(45,), help="Droite 45°")

    st.session_state.cam_pitch = st.slider("Inclinaison (Haut/Bas)", -10, 60, st.session_state.cam_pitch, help="Montez pour voir le toit")
    
    st.divider()
    st.header("🎛️ Paramètres Expert")
    container_config = st.container()

# --- MAIN ---
st.title("🏢 Estimateur Libert V33 (Complet)")

if 'addr' not in st.session_state: st.session_state.addr = ""
if 'ia_data' not in st.session_state: st.session_state.ia_data = None

c1, c2 = st.columns([3, 1])
with c1:
    # Autocomplétion
    input_val = st.session_state.addr if st.session_state.addr else ""
    q = st.text_input("Adresse :", value=input_val, placeholder="Ex: 159 rue du faubourg saint antoine...")
    
    final_addr = None
    if q and len(q)>4:
        opts = get_adresses_api(q)
        if opts: final_addr = st.selectbox("📍 Confirmation :", opts)
        else: final_addr = q
with c2:
    st.write(""); st.write("")
    if st.button("CHARGER", type="primary", use_container_width=True):
        if final_addr:
            st.session_state.ia_data = pre_analyse_ia(final_addr)
            st.session_state.addr = final_addr
            st.session_state.cam_heading = 0 # Reset angle

# --- CALCULS & AFFICHAGE ---
if st.session_state.ia_data:
    d = st.session_state.ia_data
    
    # --- 1. SIDEBAR (PARAMÈTRES MODIFIABLES) ---
    with container_config:
        st.subheader("1. Structure")
        v_type = st.radio("Type de Bien", ["IMMEUBLE", "PAVILLON"], index=0 if d['type']=="IMMEUBLE" else 1, horizontal=True)
        
        ce, cl = st.columns(2)
        with ce: v_etages = st.number_input("Niveaux (R+)", value=d['etages'], min_value=1)
        with cl: v_largeur = st.number_input("Largeur (m)", value=d['largeur'], min_value=5)
        
        st.subheader("2. Matériau")
        opts_mat = list(DB_PRIX["FACADES"].keys())
        idx_mat = opts_mat.index(d['profil']) if d['profil'] in opts_mat else 0
        v_profil = st.selectbox("Support dominant", opts_mat, index=idx_mat)
        
        st.subheader("3. Points Singuliers")
        if v_type == "IMMEUBLE":
            v_com = st.checkbox("Commerces RDC", value=False, help="Ajoute tunnel et alarme")
            v_porte_type = st.selectbox("Porte Entrée", ["PORTE_COCHERE", "PORTE_ENTREE", "AUCUNE"])
            v_chiens = st.number_input("Chiens-Assis", value=0, min_value=0)
        else:
            v_com = False
            v_porte_type = "AUCUNE"
            v_chiens = st.number_input("Lucarnes", value=0)
            
        # Calculs dynamiques
        calc_h = v_etages * 3.0
        if v_type == "PAVILLON":
            calc_s = (v_largeur * 4) * calc_h
        else:
            calc_s = v_largeur * calc_h
            
        v_fenetres = st.number_input("Nb Fenêtres", value=int(calc_s / 12))
        v_garde_corps = st.number_input("Nb Garde-corps", value=int(v_fenetres*0.6))
        
    # --- 2. VISUEL ---
    st.divider()
    ci, ct = st.columns([1.5, 2])
    with ci:
        # Image avec pitch ajustable pour voir le toit
        st.image(get_facade_image(st.session_state.addr, d['profil'], st.session_state.cam_heading, st.session_state.cam_pitch), caption="Vue Street View (Ajustable)", use_column_width=True)
    with ct:
        st.subheader("Synthèse Projet")
        st.success(f"**{v_type}** | Support : **{DB_PRIX['FACADES'][v_profil]['titre']}**")
        m1, m2, m3 = st.columns(3)
        m1.metric("Hauteur", f"{calc_h} m")
        m2.metric("Surface", f"{calc_s} m²")
        m3.metric("Points Spéciaux", f"{v_fenetres + v_chiens} U")
        
        tags = []
        if v_com: tags.append("🏪 Commerce")
        if v_chiens > 0: tags.append(f"🏠 {v_chiens} Chiens-assis")
        if v_porte_type != "AUCUNE": tags.append("🚪 Porte")
        if tags: st.markdown(" ".join([f"`{t}`" for t in tags]))

    # --- 3. DEVIS ---
    st.markdown("### 📑 Devis Détaillé")
    total = 0
    prof_data = DB_PRIX["FACADES"][v_profil]
    
    def add_line(icon, key, cat, qty, u=None):
        if key not in DB_PRIX[cat]:
            st.error(f"Erreur clé : {key} dans {cat}")
            return 0
        i = DB_PRIX[cat][key]
        unit = u if u else i['unit']
        p = qty * i['pu']
        
        with st.container():
            ca, cb, cc = st.columns([3, 1, 1])
            ca.markdown(f"**{icon} {i['titre']}**\n<br><span style='color:grey;font-size:0.8em'>{i['pourquoi']}</span>", unsafe_allow_html=True)
            cb.markdown(f"<div style='text-align:center'>{int(qty)} {unit}</div>", unsafe_allow_html=True)
            cc.markdown(f"<div style='text-align:right'><b>{p:,.2f} €</b></div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:5px 0; opacity:0.1'>", unsafe_allow_html=True)
        return p

    # A. LOGISTIQUE
    st.markdown("##### 1. Logistique")
    if v_type == "PAVILLON":
        total += add_line("🛡️", "ECHAFAUDAGE_PAV", "LOGISTIQUE", calc_s)
    else:
        total += add_line("🚧", "BASE_VIE", "LOGISTIQUE", 1)
        total += add_line("🛡️", "ECHAFAUDAGE", "LOGISTIQUE", calc_s)
        total += add_line("📜", "AUTORISATION", "LOGISTIQUE", 1)
    
    if v_com: 
        total += add_line("🚇", "TUNNEL", "LOGISTIQUE", v_largeur)
        total += add_line("🚨", "ALARME", "LOGISTIQUE", 1) # Alarme auto si commerce
    
    if v_etages > 6: total += add_line("🏗️", "MAJORATION_HAUTEUR", "LOGISTIQUE", calc_s)

    # B. FAÇADE
    st.markdown("##### 2. Traitement")
    total += add_line("💦", "NETTOYAGE", v_profil, calc_s) # Utilise v_profil (la clé du dict)
    
    s_pioch = int(calc_s * prof_data["ratio_degats"])
    if v_chiens > 0 and v_profil == "PLATRE_ANCIEN": s_pioch = int(calc_s * 0.60)
    total += add_line("🧱", "PIOCHAGE", v_profil, s_pioch)
    total += add_line("🎨", "FINITION", v_profil, calc_s)

    # C. FINITIONS
    st.markdown("##### 3. Finitions & Détails")
    if v_porte_type != "AUCUNE": total += add_line("🚪", v_porte_type, "BOISERIE", 1)
    if v_type == "PAVILLON": total += add_line("🏠", "DEBORD_TOIT", "BOISERIE", int(v_largeur*4))
    
    total += add_line("🌧️", "APPUI", "ZINGUERIE", v_fenetres)
    total += add_line("⬇️", "DESCENTE", "ZINGUERIE", int(calc_h))
    if v_type == "IMMEUBLE": total += add_line("🏛️", "BANDEAU", "ZINGUERIE", int(v_largeur*2))
    if v_garde_corps > 0: total += add_line("🖌️", "GARDE_CORPS", "ZINGUERIE", v_garde_corps)
    if v_chiens > 0: total += add_line("🏠", "CHIEN_ASSIS", "ZINGUERIE", v_chiens)

    st.markdown("---")
    c1, c2 = st.columns([2, 1])
    with c2:
        st.markdown(f"<div style='background:#2c3e50;color:white;padding:20px;border-radius:10px;text-align:right'><small>TOTAL HT</small><h1 style='margin:0'>{total:,.2f} €</h1></div>", unsafe_allow_html=True)

elif st.session_state.addr == "":
    st.info("👈 Entrez une adresse pour démarrer.")