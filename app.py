import streamlit as st
import time
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="Estimateur Libert V45", layout="wide", page_icon="🎯")

# ==============================================================================
# 1. CLÉ GOOGLE (NÉCESSAIRE POUR LE GÉOCODAGE ET L'IMAGE)
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
        "TUNNEL": {"titre": "Tunnel Public", "pourquoi": "Sécurité piétons (Commerce).", "pu": 65.00, "unit": "ml"},
        "ALARME": {"titre": "Alarme Échafaudage", "pourquoi": "Système anti-intrusion.", "pu": 2070.00, "unit": "Forfait"},
        "MAJORATION_HAUTEUR": {"titre": "Majoration Grande Hauteur", "pourquoi": "Manutention > R+5.", "pu": 15.00, "unit": "m²"}
    },
    "FACADES": { 
        "PLATRE_ANCIEN": {"titre": "Restauration Plâtre", "nettoyage": 16.50, "piochage": 160.00, "finition": 95.00, "ratio_degats": 0.50, "desc": "Décapage + Purge lourde + Micro-mortier"},
        "PIERRE_TAILLE": {"titre": "Ravalement Pierre", "nettoyage": 28.00, "piochage": 85.00, "finition": 48.00, "ratio_degats": 0.10, "desc": "Hydrogommage + Minéralisation"},
        "BRIQUE": {"titre": "Restauration Brique", "nettoyage": 35.00, "piochage": 120.00, "finition": 25.00, "ratio_degats": 0.15, "desc": "Nettoyage chimique + Hydrofuge"},
        "BETON": {"titre": "Ravalement D3", "nettoyage": 12.00, "piochage": 45.00, "finition": 58.00, "ratio_degats": 0.05, "desc": "Lavage HP + RPE Armé"},
        "PAVILLON_ENDUIT": {"titre": "Ravalement Pavillon", "nettoyage": 18.00, "piochage": 45.00, "finition": 42.00, "ratio_degats": 0.10, "desc": "Lavage + RPE"}
    },
    "ZINGUERIE": {
        "APPUI": {"titre": "Appuis Zinc", "pourquoi": "Bavette neuve.", "pu": 215.00, "unit": "U"},
        "DESCENTE": {"titre": "Descentes EP", "pourquoi": "Remplacement.", "pu": 165.00, "unit": "ml"},
        "GARDE_CORPS": {"titre": "Peinture Garde-corps", "pourquoi": "Traitement antirouille.", "pu": 160.00, "unit": "U"},
        "BANDEAU": {"titre": "Bandeau Zinc", "pourquoi": "Protection.", "pu": 178.00, "unit": "ml"},
        "CHIEN_ASSIS": {"titre": "Habillage Lucarne", "pourquoi": "Rénovation zinc.", "pu": 950.00, "unit": "U"}
    },
    "BOISERIE": {
        "PORTE_COCHERE": {"titre": "Restauration Porte Cochère", "pourquoi": "Décapage & Lasure.", "pu": 3200.00, "unit": "U"},
        "PORTE_ENTREE": {"titre": "Peinture Porte Hall", "pourquoi": "Égrenage et laque.", "pu": 850.00, "unit": "U"}
    }
}

# ==============================================================================
# 3. FONCTIONS INTELLIGENTES (GPS & PHOTO)
# ==============================================================================

def get_gps_coordinates(adresse):
    """
    Convertit l'adresse en Lat/Lon précis via API Gouv.
    C'est crucial pour que Street View se place au bon endroit.
    """
    url = f"https://api-adresse.data.gouv.fr/search/?q={adresse}&limit=1"
    try:
        r = requests.get(url).json()
        if r['features']:
            # Renvoie (Latitude, Longitude)
            c = r['features'][0]['geometry']['coordinates']
            return c[1], c[0] 
    except: return None, None
    return None, None

def get_street_view_url(lat, lon, heading, pitch):
    """
    Construit l'URL Street View avec les coordonnées GPS.
    """
    if GOOGLE_API_KEY:
        base = "https://maps.googleapis.com/maps/api/streetview"
        # location=lat,lon est plus précis que location=adresse
        loc = f"{lat},{lon}"
        return f"{base}?size=640x480&location={loc}&fov=110&heading={heading}&pitch={pitch}&key={GOOGLE_API_KEY}"
    
    # Image de secours si pas de clé
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Immeuble_parisien.jpg/800px-Immeuble_parisien.jpg"

def ia_proposition(adresse):
    """Pré-remplissage intelligent"""
    ads = adresse.lower()
    # Logique Pavillon
    if "allee" in ads or "chemin" in ads or "villa" in ads:
        return {"type": "PAVILLON", "profil": "PAVILLON_ENDUIT", "etages": 2, "largeur": 10}
    
    # Logique Immeuble
    if "sebastien" in ads or "faubourg" in ads: return {"type": "IMMEUBLE", "profil": "PLATRE_ANCIEN", "etages": 4, "largeur": 14}
    if "pascal" in ads: return {"type": "IMMEUBLE", "profil": "BRIQUE", "etages": 6, "largeur": 18}
    if "general" in ads: return {"type": "IMMEUBLE", "profil": "BETON", "etages": 7, "largeur": 22}
    
    # Défaut Parisien
    return {"type": "IMMEUBLE", "profil": "PIERRE_TAILLE", "etages": 5, "largeur": 15}

# ==============================================================================
# 4. INTERFACE UTILISATEUR
# ==============================================================================

# --- ETAT DE L'APPLICATION ---
if 'step' not in st.session_state: st.session_state.step = 1 # 1=Recherche, 2=Cadrage, 3=Rapport
if 'addr_txt' not in st.session_state: st.session_state.addr_txt = ""
if 'gps' not in st.session_state: st.session_state.gps = (None, None)
if 'cam_h' not in st.session_state: st.session_state.cam_h = 0 # Angle caméra
if 'ia_data' not in st.session_state: st.session_state.ia_data = {}

# --- HEADER ---
st.title("🎯 Estimateur Libert & Cie")

# ---------------------------------------------------------
# ÉTAPE 1 : RECHERCHE (Simple et propre)
# ---------------------------------------------------------
if st.session_state.step == 1:
    st.markdown("#### 1. Quelle est l'adresse du bâtiment ?")
    
    c1, c2 = st.columns([3, 1])
    with c1:
        query = st.text_input("Adresse :", placeholder="Ex: 159 rue du faubourg saint antoine...")
    with c2:
        st.write("")
        st.write("")
        if st.button("TROUVER LE BÂTIMENT", type="primary", use_container_width=True):
            if len(query) > 5:
                with st.spinner("Géolocalisation précise..."):
                    lat, lon = get_gps_coordinates(query)
                    if lat:
                        st.session_state.gps = (lat, lon)
                        st.session_state.addr_txt = query
                        st.session_state.ia_data = ia_proposition(query)
                        st.session_state.step = 2
                        st.rerun()
                    else:
                        st.error("Adresse introuvable. Essayez d'être plus précis (Code postal).")

# ---------------------------------------------------------
# ÉTAPE 2 : CALIBRAGE VISUEL (Le "Viseur")
# ---------------------------------------------------------
if st.session_state.step == 2:
    st.markdown(f"#### 2. Confirmez la vue pour : **{st.session_state.addr_txt}**")
    
    col_img, col_ctrl = st.columns([2, 1])
    
    with col_ctrl:
        st.info("👆 **Utilisez les boutons pour centrer le bâtiment.**")
        st.write("Google regarde parfois le trottoir d'en face.")
        
        c_rot1, c_rot2 = st.columns(2)
        if c_rot1.button("⬅️ Pivoter Gauche"): st.session_state.cam_h -= 45
        if c_rot2.button("➡️ Pivoter Droite"): st.session_state.cam_h += 45
        
        if st.button("🔄 DEMI-TOUR (Trottoir d'en face)", type="secondary", use_container_width=True):
            st.session_state.cam_h += 180
            
        st.write("---")
        if st.button("✅ C'EST LA BONNE FAÇADE", type="primary", use_container_width=True):
            st.session_state.step = 3
            st.rerun()
            
        if st.button("Annuler / Changer d'adresse"):
            st.session_state.step = 1
            st.rerun()

    with col_img:
        # Affiche l'image avec l'angle actuel (cam_h)
        lat, lon = st.session_state.gps
        img_url = get_street_view_url(lat, lon, st.session_state.cam_h, 10)
        st.image(img_url, caption=f"Angle de vue : {st.session_state.cam_h}°", use_column_width=True)

# ---------------------------------------------------------
# ÉTAPE 3 : RAPPORT & DEVIS (Affichage Natif Stable)
# ---------------------------------------------------------
if st.session_state.step == 3:
    d = st.session_state.ia_data
    
    # --- SIDEBAR : PARAMETRES TECHNIQUES ---
    with st.sidebar:
        st.header("🎛️ Réglages Experts")
        
        st.subheader("Dimensions")
        u_type = st.radio("Type", ["IMMEUBLE", "PAVILLON"], index=0 if d['type']=="IMMEUBLE" else 1)
        u_mat = st.selectbox("Support", list(DB_PRIX["FACADES"].keys()), index=list(DB_PRIX["FACADES"].keys()).index(d['profil']))
        
        c_etg, c_larg = st.columns(2)
        u_niv = c_etg.number_input("Niveaux (R+)", 1, 15, d['etages'])
        u_larg = c_larg.number_input("Largeur (m)", 5, 100, d['largeur'])
        
        st.subheader("Options")
        u_com = st.checkbox("Commerce RDC", value=False)
        u_alarme = st.checkbox("Alarme", value=(True if u_type=="IMMEUBLE" else False))
        u_chiens = st.number_input("Chiens-assis", 0, 10, 0)
        u_porte = st.selectbox("Porte", ["PORTE_COCHERE", "PORTE_ENTREE", "AUCUNE"])
        
        if st.button("🔙 Changer la photo"):
            st.session_state.step = 2
            st.rerun()

    # --- CALCULS ---
    h_calc = u_niv * 3.0
    s_calc = int(h_calc * u_larg)
    if u_type == "PAVILLON": s_calc = int((u_larg * 4) * h_calc)
    nb_fen = int(s_calc / 12)

    # --- AFFICHAGE RAPPORT ---
    c_visuel, c_synth = st.columns([1, 2])
    
    with c_visuel:
        # On réaffiche la photo validée à l'étape 2
        lat, lon = st.session_state.gps
        st.image(get_street_view_url(lat, lon, st.session_state.cam_h, 10), use_column_width=True)
        st.caption(f"📍 {st.session_state.addr_txt}")

    with c_synth:
        st.subheader("Synthèse Technique")
        k1, k2, k3 = st.columns(3)
        k1.metric("Surface", f"{s_calc} m²")
        k2.metric("Hauteur", f"{h_calc} m")
        k3.metric("Type", DB_PRIX["FACADES"][u_mat]["titre"])
        
        st.info("Le devis ci-dessous est calculé sur la base des paramètres à gauche (Sidebar). Modifiez-les pour ajuster le prix.")

    # --- DEVIS (TABLEAU NATIF) ---
    st.markdown("### 📑 Détail Estimatif")
    
    total = 0
    devis_data = [] # On stocke les lignes pour un affichage propre

    def add(cat, code_prix, qte, unit_force=None):
        if code_prix not in DB_PRIX[cat]: return 0
        item = DB_PRIX[cat][code_prix]
        u = unit_force if unit_force else item['unit']
        tot = qte * item['pu']
        devis_data.append({
            "Poste": item['titre'],
            "Détail": item['pourquoi'],
            "Qté": f"{int(qte)} {u}",
            "Prix U.": f"{item['pu']:.2f} €",
            "Total HT": f"{tot:,.2f} €",
            "valeur_brute": tot # Pour le total final
        })
        return tot

    # 1. LOGISTIQUE
    if u_type == "PAVILLON": 
        total += add("LOGISTIQUE", "ECHAFAUDAGE_PAV", s_calc, "m²")
    else:
        total += add("LOGISTIQUE", "BASE_VIE", 1)
        total += add("LOGISTIQUE", "AUTORISATION", 1)
        total += add("LOGISTIQUE", "ECHAFAUDAGE", s_calc)
        if u_com: total += add("LOGISTIQUE", "TUNNEL", u_larg, "ml")
        if u_alarme: total += add("LOGISTIQUE", "ALARME", 1)
        if u_niv > 6: total += add("LOGISTIQUE", "MAJORATION_HAUTEUR", s_calc)

    # 2. FACADE
    prof = DB_PRIX["FACADES"][u_mat]
    # Ajout manuel car structure différente
    p_net = s_calc * prof['nettoyage']
    devis_data.append({"Poste": f"Nettoyage ({u_mat})", "Détail": prof['desc'], "Qté": f"{s_calc} m²", "Prix U.": f"{prof['nettoyage']:.2f} €", "Total HT": f"{p_net:,.2f} €", "valeur_brute": p_net})
    total += p_net
    
    s_pioch = int(s_calc * prof['ratio_degats'])
    if u_chiens > 0 and u_mat == "PLATRE_ANCIEN": s_pioch = int(s_calc * 0.60)
    p_pioch = s_pioch * prof['piochage']
    devis_data.append({"Poste": "Maçonnerie (Purge)", "Détail": f"Ratio estimé {int(prof['ratio_degats']*100)}%", "Qté": f"{s_pioch} m²", "Prix U.": f"{prof['piochage']:.2f} €", "Total HT": f"{p_pioch:,.2f} €", "valeur_brute": p_pioch})
    total += p_pioch
    
    p_fin = s_calc * prof['finition']
    devis_data.append({"Poste": "Finition Système", "Détail": prof['desc'], "Qté": f"{s_calc} m²", "Prix U.": f"{prof['finition']:.2f} €", "Total HT": f"{p_fin:,.2f} €", "valeur_brute": p_fin})
    total += p_fin

    # 3. FINITIONS
    if u_porte != "AUCUNE": total += add("BOISERIE", u_porte, 1)
    total += add("ZINGUERIE", "APPUI", nb_fen)
    total += add("ZINGUERIE", "DESCENTE", int(h_calc), "ml")
    
    if u_type == "IMMEUBLE":
        total += add("ZINGUERIE", "BANDEAU", int(u_larg*2), "ml")
        total += add("ZINGUERIE", "GARDE_CORPS", int(nb_fen*0.7))
    
    if u_chiens > 0: total += add("ZINGUERIE", "CHIEN_ASSIS", u_chiens)

    # --- AFFICHAGE TABLEAU NATIF (STABLE) ---
    st.dataframe(
        devis_data, 
        column_config={
            "Poste": st.column_config.TextColumn("Désignation", width="medium"),
            "Détail": st.column_config.TextColumn("Description Technique", width="large"),
            "valeur_brute": None # Cache la colonne de calcul
        },
        use_container_width=True,
        hide_index=True
    )

    # --- TOTAL ---
    st.markdown("---")
    c_fin1, c_fin2 = st.columns([3, 1])
    with c_fin2:
        st.markdown(f"""
        <div style="background:#2c3e50; color:white; padding:20px; border-radius:10px; text-align:right;">
            <div style="font-size:0.8em">TOTAL HT</div>
            <div style="font-size:2em; font-weight:bold">{total:,.2f} €</div>
        </div>
        """, unsafe_allow_html=True)