import streamlit as st
import time
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="Estimateur Libert V40 (Final)", layout="wide", page_icon="🏢")

# ==============================================================================
# 1. SÉCURITÉ & API
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = ""

# ==============================================================================
# 2. BASE DE PRIX (LIBERT 2025)
# ==============================================================================
DB_PRIX = {
    "LOGISTIQUE": {
        "BASE_VIE": {"titre": "Installation & Base Vie", "pourquoi": "Roulotte, WC, Cantonnement.", "pu": 4500.00, "unit": "Forfait"},
        "AUTORISATION": {"titre": "Taxes de Voirie (ODP)", "pourquoi": "Redevance municipale.", "pu": 605.00, "unit": "Forfait"},
        "ECHAFAUDAGE": {"titre": "Échafaudage Tubulaire", "pourquoi": "Classe 4 + filets pare-gravats.", "pu": 39.90, "unit": "m²"},
        "ECHAFAUDAGE_PAV": {"titre": "Échafaudage Léger", "pourquoi": "Structure adaptée pavillon.", "pu": 28.00, "unit": "m²"},
        "TUNNEL": {"titre": "Tunnel Public", "pourquoi": "Sécurité piétons (Commerce).", "pu": 60.00, "unit": "ml"},
        "ALARME": {"titre": "Alarme Échafaudage", "pourquoi": "Système anti-intrusion 24/7.", "pu": 2070.00, "unit": "Forfait"},
        "MAJORATION_HAUTEUR": {"titre": "Majoration Grande Hauteur", "pourquoi": "Manutention > R+5.", "pu": 15.00, "unit": "m²"}
    },
    "FACADES": { 
        "PLATRE": { 
            "titre": "Restauration Plâtre (Traditionnel)", 
            "nettoyage": 16.50, "piochage": 160.00, "finition": 95.00, "ratio_degats": 0.50, 
            "desc": "Décapage + Purge lourde maçonneries + Micro-mortier"
        },
        "PIERRE": { 
            "titre": "Ravalement Pierre de Taille", 
            "nettoyage": 28.00, "piochage": 85.00, "finition": 48.00, "ratio_degats": 0.10, 
            "desc": "Hydrogommage doux + Ragréage ponctuel + Minéralisation"
        },
        "BRIQUE": { 
            "titre": "Restauration Brique", 
            "nettoyage": 35.00, "piochage": 120.00, "finition": 25.00, "ratio_degats": 0.15, 
            "desc": "Nettoyage chimique + Changement briques + Hydrofuge"
        },
        "BETON": { 
            "titre": "Ravalement Technique D3", 
            "nettoyage": 12.00, "piochage": 45.00, "finition": 58.00, "ratio_degats": 0.05, 
            "desc": "Lavage HP + Passivation fers + RPE Armé"
        },
        "PAVILLON": { 
            "titre": "Ravalement Maison I3", 
            "nettoyage": 18.00, "piochage": 45.00, "finition": 42.00, "ratio_degats": 0.10, 
            "desc": "Lavage + Reprise fissures + RPE Souple"
        }
    },
    "ZINGUERIE": {
        "APPUI": {"titre": "Appuis de Fenêtre (Zinc)", "pourquoi": "Bavette neuve avec larmier.", "pu": 215.00, "unit": "U"},
        "DESCENTE": {"titre": "Descentes EP", "pourquoi": "Remplacement Zinc/Fonte.", "pu": 165.00, "unit": "ml"},
        "GARDE_CORPS": {"titre": "Peinture Garde-corps", "pourquoi": "Traitement antirouille.", "pu": 160.00, "unit": "U"},
        "BANDEAU": {"titre": "Couvre-Murette (Zinc)", "pourquoi": "Protection bandeaux.", "pu": 178.00, "unit": "ml"},
        "CHIEN_ASSIS": {"titre": "Habillage Chien-Assis", "pourquoi": "Rénovation zinc lucarne.", "pu": 950.00, "unit": "U"}
    },
    "BOISERIE": {
        "PORTE_COCHERE": {"titre": "Restauration Porte Cochère", "pourquoi": "Décapage, greffes, lasure.", "pu": 3200.00, "unit": "U"},
        "PORTE_ENTREE": {"titre": "Peinture Porte Hall", "pourquoi": "Égrenage et laque.", "pu": 850.00, "unit": "U"},
        "DEBORD_TOIT": {"titre": "Lasure Débords de Toit", "pourquoi": "Protection planches de rive.", "pu": 45.00, "unit": "ml"}
    }
}

# ==============================================================================
# 3. FONCTIONS TECHNIQUES
# ==============================================================================
def get_adresses_api(query):
    if not query or len(query) < 3: return []
    try:
        r = requests.get(f"https://api-adresse.data.gouv.fr/search/?q={query}&limit=5")
        return [f['properties']['label'] for f in r.json()['features']] if r.status_code == 200 else []
    except: return []

def get_facade_image(adresse, heading=0, pitch=20):
    """
    Fonction image corrigée : Ne dépend plus d'aucune variable externe.
    """
    if GOOGLE_API_KEY and len(GOOGLE_API_KEY) > 10:
        base = "https://maps.googleapis.com/maps/api/streetview"
        return f"{base}?size=640x640&location={adresse}&fov=110&heading={heading}&pitch={pitch}&key={GOOGLE_API_KEY}"
    
    # Image de secours générique (si pas de clé)
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Immeuble_parisien.jpg/800px-Immeuble_parisien.jpg"

def ia_init(adresse):
    ads = adresse.lower()
    # 1. Type Pavillon
    if "allee" in ads or "chemin" in ads or "villa" in ads:
        return "PAVILLON", "PAVILLON", 2, 10
    
    # 2. Type Immeuble
    if "sebastien" in ads or "faubourg" in ads: return "IMMEUBLE", "PLATRE", 4, 14
    if "pascal" in ads: return "IMMEUBLE", "BRIQUE", 6, 18
    if "general" in ads: return "IMMEUBLE", "BETON", 7, 20
    
    # Défaut
    return "IMMEUBLE", "PIERRE", 6, 16

# ==============================================================================
# 4. INTERFACE UTILISATEUR
# ==============================================================================

# SESSIONS
if 'addr_label' not in st.session_state: st.session_state.addr_label = ""
if 'cam_h' not in st.session_state: st.session_state.cam_h = 0
if 'cam_p' not in st.session_state: st.session_state.cam_p = 20

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎛️ Paramètres")
    
    st.subheader("📷 Vue")
    c1, c2, c3 = st.columns(3)
    if c1.button("⬅️"): st.session_state.cam_h -= 45
    if c2.button("🔄"): st.session_state.cam_h += 180
    if c3.button("➡️"): st.session_state.cam_h += 45
    st.session_state.cam_p = st.slider("Inclinaison", -10, 60, st.session_state.cam_p)
    
    st.divider()
    st.subheader("🏗️ Bâtiment")
    container_params = st.container()

# --- MAIN ---
st.title("🏢 Estimateur Libert V40 (Final)")

c_search, c_go = st.columns([3, 1])
with c_search:
    query = st.text_input("Adresse :", placeholder="Tapez une adresse...")
    if query and len(query) > 4:
        features = get_adresses_api(query)
        if features:
            selected_label = st.selectbox("📍 Suggestions :", features, label_visibility="collapsed")
            
            if selected_label and selected_label != st.session_state.addr_label:
                st.session_state.addr_label = selected_label
                t, m, n, l = ia_init(selected_label)
                st.session_state.ia_type = t
                st.session_state.ia_mat = m
                st.session_state.ia_niv = n
                st.session_state.ia_larg = l
                st.session_state.cam_h = 0
                st.rerun()

# --- RAPPORT ---
if st.session_state.addr_label:
    
    # 1. CONTROLES
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

    # 2. VISUEL
    st.divider()
    c_img, c_txt = st.columns([1.5, 2])
    with c_img:
        st.image(get_facade_image(st.session_state.addr_label, heading=st.session_state.cam_h, pitch=st.session_state.cam_p), use_column_width=True)
    with c_txt:
        st.subheader(st.session_state.addr_label)
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Surface", f"{s_calc} m²")
        k2.metric("Hauteur", f"{h_calc} m")
        k3.metric("Type", DB_PRIX["FACADES"][u_mat]["titre"])

    # 3. DEVIS
    st.markdown("### 📑 Détail Estimatif")
    total = 0
    
    def add_line(cat, key, qte, unit=None):
        if key not in DB_PRIX[cat]: return 0
        item = DB_PRIX[cat][key]
        u = unit if unit else item['unit']
        tot = qte * item['pu']
        
        with st.container():
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.markdown(f"**{item['titre']}**\n<br><span style='color:grey;font-size:0.8em'>{item['pourquoi']}</span>", unsafe_allow_html=True)
            c2.markdown(f"<div style='text-align:center'>{int(qte)} {u}</div>", unsafe_allow_html=True)
            c3.markdown(f"<div style='text-align:right'><b>{tot:,.2f} €</b></div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:5px 0; opacity:0.1'>", unsafe_allow_html=True)
        return tot

    # LOGISTIQUE
    st.markdown("#### 1. Logistique")
    if u_type == "PAVILLON": total += add_line("LOGISTIQUE", "ECHAFAUDAGE_PAV", s_calc)
    else:
        total += add_line("LOGISTIQUE", "BASE_VIE", 1)
        total += add_line("LOGISTIQUE", "AUTORISATION", 1)
        total += add_line("LOGISTIQUE", "ECHAFAUDAGE", s_calc)
        if u_com: total += add_line("LOGISTIQUE", "TUNNEL", u_larg)
        if u_alarme: total += add_line("LOGISTIQUE", "ALARME", 1)
        if u_niv > 6: total += add_line("LOGISTIQUE", "MAJORATION_HAUTEUR", s_calc)

    # FAÇADE
    st.markdown("#### 2. Façade")
    prof = DB_PRIX["FACADES"][u_mat]
    
    # Nettoyage
    p_net = s_calc * prof['nettoyage']
    with st.container():
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.markdown(f"**Nettoyage ({u_mat})**\n<br><span style='color:grey;font-size:0.8em'>{prof['desc']}</span>", unsafe_allow_html=True)
        c2.markdown(f"<div style='text-align:center'>{s_calc} m²</div>", unsafe_allow_html=True)
        c3.markdown(f"<div style='text-align:right'><b>{p_net:,.2f} €</b></div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin:5px 0; opacity:0.1'>", unsafe_allow_html=True)
    total += p_net
    
    # Piochage
    s_pioch = int(s_calc * prof['ratio_degats'])
    if u_chiens > 0 and u_mat == "PLATRE": s_pioch = int(s_calc * 0.60)
    p_pioch = s_pioch * prof['piochage']
    with st.container():
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.markdown(f"**Maçonnerie (Purge)**\n<br><span style='color:grey;font-size:0.8em'>Ratio dégâts: {int(prof['ratio_degats']*100)}%</span>", unsafe_allow_html=True)
        c2.markdown(f"<div style='text-align:center'>{s_pioch} m²</div>", unsafe_allow_html=True)
        c3.markdown(f"<div style='text-align:right'><b>{p_pioch:,.2f} €</b></div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin:5px 0; opacity:0.1'>", unsafe_allow_html=True)
    total += p_pioch
    
    # Finition
    p_fin = s_calc * prof['finition']
    with st.container():
        c1, c2, c3 = st.columns([3, 1, 1])
        c1.markdown(f"**Finition Système**\n<br><span style='color:grey;font-size:0.8em'>{prof['desc']}</span>", unsafe_allow_html=True)
        c2.markdown(f"<div style='text-align:center'>{s_calc} m²</div>", unsafe_allow_html=True)
        c3.markdown(f"<div style='text-align:right'><b>{p_fin:,.2f} €</b></div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin:5px 0; opacity:0.1'>", unsafe_allow_html=True)
    total += p_fin

    # FINITIONS
    st.markdown("#### 3. Finitions")
    if u_porte != "AUCUNE": total += add_line("BOISERIE", u_porte, 1)
    if u_type == "PAVILLON": total += add_line("BOISERIE", "DEBORD_TOIT", int(u_larg*4))
    
    total += add_line("ZINGUERIE", "APPUI", nb_fen)
    total += add_line("ZINGUERIE", "DESCENTE", int(h_calc))
    if u_type == "IMMEUBLE": total += add_line("ZINGUERIE", "BANDEAU", int(u_larg*2))
    total += add_line("ZINGUERIE", "GARDE_CORPS", int(nb_fen*0.7))
    if u_chiens > 0: total += add_line("ZINGUERIE", "CHIEN_ASSIS", u_chiens)

    # TOTAL
    st.markdown("---")
    col_tot, col_vide = st.columns([2, 1])
    with col_tot:
        st.markdown(f"<h2 style='text-align:right'>TOTAL ESTIMATIF HT : {total:,.2f} €</h2>", unsafe_allow_html=True)
        st.caption("TVA non incluse. Estimation indicative.")

elif st.session_state.addr_label == "":
    st.info("👈 Entrez une adresse.")