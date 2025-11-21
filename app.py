import streamlit as st
import time
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="Estimateur Libert V23 (Expert)", layout="wide", page_icon="🏗️")

# ==============================================================================
# 🔑 API GOOGLE
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = "" 

# ==============================================================================
# 1. BASE DE PRIX EXPERTE (PRIX LIBERT AFFINÉS)
# ==============================================================================
DB_PRIX = {
    "LOGISTIQUE": {
        "BASE_VIE": {"titre": "Installation & Base Vie", "pourquoi": "Roulotte, WC, Cantonnement et protections obligatoires.", "pu": 4500.00, "unit": "Forfait"},
        "AUTORISATION": {"titre": "Taxes de Voirie (ODP)", "pourquoi": "Redevance municipale occupation trottoir.", "pu": 605.00, "unit": "Forfait"},
        "ECHAFAUDAGE": {"titre": "Échafaudage Tubulaire", "pourquoi": "Structure classe 4 + filets pare-gravats.", "pu": 39.90, "unit": "m²"},
        "MAJORATION_HAUTEUR": {"titre": "Majoration Grande Hauteur", "pourquoi": "Manutention supplémentaire au-delà de R+5.", "pu": 15.00, "unit": "m²"}
    },
    # --- SUPPORTS ---
    "PLATRE": { 
        "NETTOYAGE": {"titre": "Décapage Chimique / Grattage", "pourquoi": "Retrait des RPE ou peintures bloquantes.", "pu": 22.00, "unit": "m²"},
        "PIOCHAGE": {"titre": "Purge & Reconstitution (Plâtre/Chaux)", "pourquoi": "Sondage méthodique, purge des zones soufflées.", "pu": 150.00, "unit": "m²"},
        "FINITION": {"titre": "Micro-Mortier Chaux", "pourquoi": "Finition minérale respirante (Type Tilia).", "pu": 95.00, "unit": "m²"},
        "RATIO_DEGATS": 0.50 # Le plâtre est souvent très abîmé
    },
    "PIERRE_TAILLE": { 
        "NETTOYAGE": {"titre": "Hydrogommage Doux", "pourquoi": "Gommage basse pression respectant le calin.", "pu": 28.00, "unit": "m²"},
        "PIOCHAGE": {"titre": "Ragréage & Joints", "pourquoi": "Réparation ponctuelle au mortier pierre.", "pu": 85.00, "unit": "m²"},
        "FINITION": {"titre": "Minéralisation / Hydrofuge", "pourquoi": "Protection invisible (Keim/Silicate).", "pu": 48.00, "unit": "m²"},
        "RATIO_DEGATS": 0.10
    },
    "BRIQUE": { 
        "NETTOYAGE": {"titre": "Nettoyage Chimique", "pourquoi": "Nettoyage des salissures urbaines sur brique.", "pu": 35.00, "unit": "m²"},
        "PIOCHAGE": {"titre": "Remplacement de Briques", "pourquoi": "Changement des briques éclatées et rejointoiement.", "pu": 120.00, "unit": "m²"},
        "FINITION": {"titre": "Hydrofuge Incolore", "pourquoi": "Protection contre les infiltrations sans changer l'aspect.", "pu": 25.00, "unit": "m²"},
        "RATIO_DEGATS": 0.15
    },
    "BETON": { 
        "NETTOYAGE": {"titre": "Lavage Haute Pression", "pourquoi": "Décrassage profond (pollution/mousses).", "pu": 12.00, "unit": "m²"},
        "PIOCHAGE": {"titre": "Traitement des fers", "pourquoi": "Passivation des aciers et reprises d'épaufrures.", "pu": 45.00, "unit": "m²"},
        "FINITION": {"titre": "Revêtement D3 Armé", "pourquoi": "Imperméabilité et souplesse (anti-fissure).", "pu": 58.00, "unit": "m²"},
        "RATIO_DEGATS": 0.05
    },
    # --- FINITIONS ---
    "ZINGUERIE": {
        "APPUI": {"titre": "Appuis de Fenêtre (Zinc)", "pourquoi": "Bavette neuve avec larmier.", "pu": 210.00, "unit": "U"},
        "DESCENTE": {"titre": "Descentes EP", "pourquoi": "Remplacement Zinc/Fonte.", "pu": 165.00, "unit": "ml"},
        "GARDE_CORPS": {"titre": "Peinture Garde-corps", "pourquoi": "Traitement antirouille.", "pu": 160.00, "unit": "U"},
        "BANDEAU": {"titre": "Couvre-Murette Zinc", "pourquoi": "Protection des bandeaux saillants.", "pu": 178.00, "unit": "ml"},
        "CHIEN_ASSIS": {"titre": "Habillage Chien-Assis", "pourquoi": "Rénovation zinc et jouées.", "pu": 850.00, "unit": "U"}
    },
    "BOISERIE": {
        "PORTE_COCHERE": {"titre": "Restauration Porte Cochère", "pourquoi": "Décapage, greffes et lasure.", "pu": 3200.00, "unit": "Forfait"},
        "PORTE_ENTREE": {"titre": "Peinture Porte Hall", "pourquoi": "Égrenage et laque tendue.", "pu": 850.00, "unit": "Forfait"}
    }
}

# ==============================================================================
# 2. FONCTIONS API
# ==============================================================================
def get_adresses_api(query):
    if not query: return []
    url = f"https://api-adresse.data.gouv.fr/search/?q={query}&limit=5"
    try:
        r = requests.get(url)
        return [f['properties']['label'] for f in r.json()['features']] if r.status_code == 200 else []
    except: return []

def get_facade_image(adresse, style_backup, heading=0, pitch=10):
    if GOOGLE_API_KEY and len(GOOGLE_API_KEY) > 10:
        base = "https://maps.googleapis.com/maps/api/streetview"
        return f"{base}?size=640x640&location={adresse}&fov=100&heading={heading}&pitch={pitch}&key={GOOGLE_API_KEY}"
    
    # Images de secours
    if "Plâtre" in style_backup: return "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/14_rue_Saint-S%C3%A9bastien_Paris_11.jpg/800px-14_rue_Saint-S%C3%A9bastien_Paris_11.jpg"
    elif "Pierre" in style_backup: return "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Paris_-_Immeuble_bld_Raspail.jpg/800px-Paris_-_Immeuble_bld_Raspail.jpg"
    else: return "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Immeuble_d%27habitation_HBM.jpg/800px-Immeuble_d%27habitation_HBM.jpg"

# ==============================================================================
# 3. INTELLIGENCE ARTIFICIELLE (PREDICTION)
# ==============================================================================
def proposition_ia_avancee(adresse):
    ads = adresse.lower()
    
    # Logique prédictive (Aider l'utilisateur sans le bloquer)
    if "sebastien" in ads or "faubourg" in ads:
        return {"support": "PLATRE", "annee": "1850", "porte": "PORTE_COCHERE", "etages": 4, "largeur": 14, "toiture": False}
    elif "pascal" in ads:
        return {"support": "BRIQUE", "annee": "1930", "porte": "PORTE_ENTREE", "etages": 6, "largeur": 18, "toiture": False}
    elif "general" in ads or "leclerc" in ads:
        return {"support": "BETON", "annee": "1970", "porte": "PORTE_ENTREE", "etages": 7, "largeur": 22, "toiture": False}
    else:
        return {"support": "PIERRE_TAILLE", "annee": "1890", "porte": "PORTE_COCHERE", "etages": 6, "largeur": 16, "toiture": True}

# ==============================================================================
# 4. INTERFACE UTILISATEUR
# ==============================================================================

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔧 Calibrage Expert")
    
    st.subheader("📷 Caméra Street View")
    cam_heading = st.slider("Orientation", 0, 360, 0, 10)
    cam_pitch = st.slider("Inclinaison", -10, 45, 10)
    
    st.divider()
    st.subheader("🏗️ Données Techniques")
    # Le container sera rempli après le chargement de l'adresse
    container_params = st.container()

# --- MAIN PAGE ---
st.title("🔎 Estimateur Façade Libert & Cie")
st.markdown("### Adresse du projet")

if 'adresse_input' not in st.session_state: st.session_state.adresse_input = ""
if 'data_ia' not in st.session_state: st.session_state.data_ia = None

c_search, c_btn = st.columns([3, 1])
with c_search:
    query = st.text_input("Rechercher :", placeholder="159 rue du faubourg saint antoine...", value=st.session_state.adresse_input)
    final_addr = None
    if query and len(query)>4:
        opts = get_adresses_api(query)
        if opts: final_addr = st.selectbox("📍 Confirmation :", opts)

with c_btn:
    st.write("")
    st.write("")
    launch = st.button("ANALYSER", type="primary", use_container_width=True)

if launch and final_addr:
    st.session_state.data_ia = proposition_ia_avancee(final_addr)
    st.session_state.adresse_input = final_addr

# --- RÉSULTATS ---
if st.session_state.data_ia:
    d = st.session_state.data_ia
    
    # --- BARRE LATÉRALE DYNAMIQUE (C'est ici que vous corrigez l'IA) ---
    with container_params:
        # 1. LE SUPPORT (CRUCIAL POUR LE PRIX)
        options_support = ["PLATRE", "PIERRE_TAILLE", "BRIQUE", "BETON"]
        # On pré-selectionne ce que l'IA a trouvé, mais vous pouvez changer
        index_defaut = options_support.index(d['support'])
        val_support = st.selectbox("Nature de la Façade", options_support, index=index_defaut)
        
        st.divider()
        
        # 2. LES DIMENSIONS
        val_etages = st.number_input("Niveaux (R+X +1)", value=d['etages'], min_value=1)
        val_largeur = st.number_input("Largeur (m)", value=d['largeur'], min_value=5)
        has_toiture = st.checkbox("Combles / Chiens-assis ?", value=d['toiture'])
        
        # Calculs
        hauteur_calc = val_etages * 3.0
        s_calc = int(hauteur_calc * val_largeur)
        st.metric("Surface Façade", f"{s_calc} m²")

    # VISUEL
    st.divider()
    c1, c2 = st.columns([1.2, 2])
    
    with c1:
        img = get_facade_image(st.session_state.adresse_input, val_support, heading=cam_heading, pitch=cam_pitch)
        st.image(img, caption="Vue Street View (Ajustable)", use_column_width=True)
        
    with c2:
        st.subheader("📊 Analyse Technique")
        
        # Affichage pédagogique du support choisi
        lbl_support = "Inconnu"
        if val_support == "PLATRE": lbl_support = "Façade Plâtre / Pans de Bois"
        if val_support == "PIERRE_TAILLE": lbl_support = "Pierre de Taille (Haussmann)"
        if val_support == "BRIQUE": lbl_support = "Brique Apparente / Enduit"
        if val_support == "BETON": lbl_support = "Béton Armé / Préfabriqué"
        
        st.info(f"**Support retenu :** {lbl_support}")
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Hauteur", f"R+{val_etages-1}")
        k2.metric("Surface", f"{s_calc} m²")
        k3.metric("Année (Est.)", d['annee'])
        
        if has_toiture:
            st.warning("🏠 **Toiture complexe détectée** : Les travaux incluent le traitement des lucarnes/chiens-assis.")

    # DEVIS
    st.markdown("### 📑 Devis Estimatif Détaillé")
    
    # On récupère les prix du support CHOISI PAR L'UTILISATEUR (pas juste l'IA)
    profil_prix = DB_PRIX[val_support]
    total = 0
    
    def add_line(icon, key, cat, qty, u=None):
        # Sécurité
        if cat not in DB_PRIX: return 0
        if key not in DB_PRIX[cat]: return 0
        
        item = DB_PRIX[cat][key]
        unit = u if u else item.get('unit', 'm²')
        price = qty * item['pu']
        
        with st.container():
            ca, cb, cc = st.columns([3, 1, 1])
            ca.markdown(f"**{icon} {item['titre']}** \n<small style='color:grey'>{item['pourquoi']}</small>", unsafe_allow_html=True)
            cb.markdown(f"<div style='text-align:center'>{qty} {unit}</div>", unsafe_allow_html=True)
            cc.markdown(f"<div style='text-align:right'><b>{price:,.2f} €</b></div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:5px 0; opacity:0.1'>", unsafe_allow_html=True)
        return price

    # 1. INSTALLATION
    st.markdown("##### 1. Installation de Chantier")
    total += add_line("🚧", "BASE_VIE", "LOGISTIQUE", 1)
    total += add_line("🛡️", "ECHAFAUDAGE", "LOGISTIQUE", s_calc)
    total += add_line("📜", "AUTORISATION", "LOGISTIQUE", 1)
    if val_etages > 6:
        total += add_line("🏗️", "MAJORATION_HAUTEUR", "LOGISTIQUE", s_calc)

    # 2. FAÇADE (Dynamique selon support)
    st.markdown("##### 2. Traitement Façade")
    total += add_line("💦", "NETTOYAGE", val_support, s_calc)
    
    # Calcul piochage
    surf_pioch = int(s_calc * profil_prix["RATIO_DEGATS"])
    # Titre dynamique
    titre_pioch = f"🧱 {profil_prix['PIOCHAGE']['titre']}"
    if profil_prix["RATIO_DEGATS"] >= 0.5: titre_pioch += " (Lourd)"
    
    total += add_line("🧱", "PIOCHAGE", val_support, surf_pioch)
    total += add_line("🎨", "FINITION", val_support, s_calc)

    # 3. FINITIONS
    st.markdown("##### 3. Finitions & Toiture")
    nb_fen = int(s_calc/12)
    ml_ep = int(hauteur_calc)
    
    total += add_line("🚪", d['porte'], "BOISERIE", 1, "U")
    total += add_line("🌧️", "APPUI", "ZINGUERIE", nb_fen)
    total += add_line("⬇️", "DESCENTE", "ZINGUERIE", ml_ep, "ml")
    total += add_line("🏛️", "BANDEAU", "ZINGUERIE", int(val_largeur*2), "ml")
    total += add_line("🖌️", "GARDE_CORPS", "ZINGUERIE", int(nb_fen*0.7))
    
    if has_toiture:
        nb_chiens = max(1, int(val_largeur / 6))
        total += add_line("🏠", "CHIEN_ASSIS", "ZINGUERIE", nb_chiens)

    # TOTAL
    st.markdown("---")
    col_t1, col_t2 = st.columns([2, 1])
    with col_t2:
        st.markdown(f"""
        <div style="background:#2c3e50;color:white;padding:20px;border-radius:10px;text-align:right">
            <small>TOTAL HT ESTIMÉ</small>
            <h1 style="margin:0">{total:,.2f} €</h1>
        </div>
        """, unsafe_allow_html=True)

elif launch:
    st.error("Sélectionnez une adresse.")