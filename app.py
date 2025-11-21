import streamlit as st
import time
import datetime
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="Estimateur Libert V23 (Stable)", layout="wide", page_icon="🏗️")

# ==============================================================================
# 🔑 CONFIGURATION API
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = "" 

# ==============================================================================
# 1. BASE DE PRIX "LIBERT 2025" (CORRIGÉE : UNITÉS AJOUTÉES)
# ==============================================================================
DB_PRIX = {
    "LOGISTIQUE": {
        "BASE_VIE": {"titre": "Installation & Base Vie", "pourquoi": "Roulotte, WC et protections obligatoires.", "pu": 4500.00, "unit": "Forfait"},
        "AUTORISATION": {"titre": "Taxes de Voirie (ODP)", "pourquoi": "Redevance municipale occupation trottoir.", "pu": 605.00, "unit": "Forfait"},
        "ECHAFAUDAGE": {"titre": "Échafaudage Tubulaire", "pourquoi": "Structure classe 4 + filets pare-gravats.", "pu": 39.90, "unit": "m²"},
        "MAJORATION_HAUTEUR": {"titre": "Majoration Grande Hauteur", "pourquoi": "Manutention supplémentaire au-delà de R+5.", "pu": 15.00, "unit": "m²"}
    },
    "PLATRE_ANCIEN": { 
        "NETTOYAGE": {"titre": "Décapage Chimique", "pourquoi": "Retrait peintures sans abîmer le plâtre.", "pu": 16.50, "unit": "m²"},
        "PIOCHAGE": {"titre": "Soin des Maçonneries (Purge)", "pourquoi": "Retrait des parties sonnant le creux.", "pu": 150.00, "unit": "m²"},
        "FINITION": {"titre": "Finition Micro-Mortier", "pourquoi": "Revêtement respirant (Chaux).", "pu": 90.00, "unit": "m²"},
        "RATIO_DEGATS": 0.50
    },
    "PIERRE_BRIQUE": { 
        "NETTOYAGE": {"titre": "Hydrogommage Doux", "pourquoi": "Gommage basse pression.", "pu": 25.00, "unit": "m²"},
        "PIOCHAGE": {"titre": "Ragréage Pierre", "pourquoi": "Reconstitution au mortier pierre.", "pu": 37.50, "unit": "m²"},
        "FINITION": {"titre": "Minéralisation", "pourquoi": "Protection invisible durcissante.", "pu": 48.00, "unit": "m²"},
        "RATIO_DEGATS": 0.10
    },
    "MODERNE_BETON": { 
        "NETTOYAGE": {"titre": "Lavage Haute Pression", "pourquoi": "Décrassage profond.", "pu": 12.00, "unit": "m²"},
        "PIOCHAGE": {"titre": "Traitement des fers", "pourquoi": "Passivation des aciers.", "pu": 37.50, "unit": "m²"},
        "FINITION": {"titre": "Revêtement D3 Armé", "pourquoi": "Imperméabilité et souplesse.", "pu": 55.00, "unit": "m²"},
        "RATIO_DEGATS": 0.05
    },
    "ZINGUERIE": {
        "APPUI": {"titre": "Appuis de Fenêtre (Zinc)", "pourquoi": "Bavette neuve avec larmier.", "pu": 210.00, "unit": "U"},
        "DESCENTE": {"titre": "Descentes EP", "pourquoi": "Remplacement Zinc/Fonte.", "pu": 165.00, "unit": "ml"},
        "GARDE_CORPS": {"titre": "Peinture Garde-corps", "pourquoi": "Traitement antirouille.", "pu": 160.00, "unit": "U"},
        "CHIEN_ASSIS": {"titre": "Habillage Chien-Assis", "pourquoi": "Rénovation zinc et jouées des lucarnes de toit.", "pu": 850.00, "unit": "U"}
    }
}

# ==============================================================================
# 2. FONCTIONS API & IMAGE
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
    if "Faubourien" in style_backup: return "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/14_rue_Saint-S%C3%A9bastien_Paris_11.jpg/800px-14_rue_Saint-S%C3%A9bastien_Paris_11.jpg"
    elif "Haussmannien" in style_backup: return "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Paris_-_Immeuble_bld_Raspail.jpg/800px-Paris_-_Immeuble_bld_Raspail.jpg"
    else: return "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Immeuble_parisien.jpg/800px-Immeuble_parisien.jpg"

# ==============================================================================
# 3. INTELLIGENCE ARTIFICIELLE
# ==============================================================================
def proposition_ia_avancee(adresse):
    ads = adresse.lower()
    
    if "159" in ads and "antoine" in ads:
        return {
            "style": "Faubourien (Grand Gabarit)", "annee": "1860", "profil": "PLATRE_ANCIEN", 
            "porte": "PORTE_COCHERE", "etages": 6, "largeur": 16, "toiture": True
        }
    elif "sebastien" in ads:
        return {"style": "Faubourien (Classique)", "annee": "1850", "profil": "PLATRE_ANCIEN", "porte": "PORTE_COCHERE", "etages": 4, "largeur": 14, "toiture": False}
    elif "pascal" in ads:
        return {"style": "Années 30", "annee": "1930", "profil": "PIERRE_BRIQUE", "porte": "PORTE_ENTREE", "etages": 6, "largeur": 18, "toiture": False}
    else:
        return {"style": "Haussmannien", "annee": "1890", "profil": "PIERRE_BRIQUE", "porte": "PORTE_COCHERE", "etages": 6, "largeur": 16, "toiture": True}

# ==============================================================================
# 4. INTERFACE UTILISATEUR
# ==============================================================================

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔧 Calibrage Expert")
    st.subheader("📷 Caméra Street View")
    cam_heading = st.slider("Orientation (Rotation)", 0, 360, 0, 10)
    cam_pitch = st.slider("Inclinaison (Haut/Bas)", -10, 45, 10)
    st.divider()
    st.subheader("📏 Dimensions")
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
    
    # MISE A JOUR SIDEBAR
    with container_params:
        val_etages = st.number_input("Niveaux (R+X +1)", value=d['etages'], min_value=1)
        val_largeur = st.number_input("Largeur (m)", value=d['largeur'], min_value=5)
        has_toiture = st.checkbox("Combles / Chiens-assis ?", value=d['toiture'])
        
        hauteur_calc = val_etages * 3.0
        s_calc = int(hauteur_calc * val_largeur)
        st.metric("Surface Façade", f"{s_calc} m²")

    # VISUEL & DATA
    st.divider()
    c1, c2 = st.columns([1.2, 2])
    
    with c1:
        img = get_facade_image(st.session_state.adresse_input, d['style'], heading=cam_heading, pitch=cam_pitch)
        st.image(img, caption="Vue Street View (Ajustable via menu gauche)", use_column_width=True)
        
    with c2:
        st.subheader("📊 Analyse Croisée")
        st.info(f"**Bâtiment identifié :** {d['style']}")
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Hauteur", f"R+{val_etages-1}")
        k2.metric("Surface Développée", f"{s_calc} m²")
        k3.metric("Année (Est.)", d['annee'])
        
        if has_toiture:
            st.warning("🏠 **Points singuliers toiture détectés** (Chiens-assis/Lucarnes). Inclus dans l'estimation.")

    # DEVIS DÉTAILLÉ
    st.markdown("### 📑 Estimation Détaillée")
    profil = DB_PRIX[d['profil']]
    total = 0
    
    def add_line(icon, key, cat, qty, u=None):
        # Sécurité anti-crash
        if key not in DB_PRIX[cat]: return 0
        
        item = DB_PRIX[cat][key]
        # Sécurité unité manquante : par défaut m² si non trouvé
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

    # 2. FAÇADE
    st.markdown("##### 2. Traitement Façade")
    total += add_line("💦", "NETTOYAGE", d['profil'], s_calc)
    surf_pioch = int(s_calc * profil["RATIO_DEGATS"])
    total += add_line("🧱", "PIOCHAGE", d['profil'], surf_pioch)
    total += add_line("🎨", "FINITION", d['profil'], s_calc)

    # 3. FINITIONS
    st.markdown("##### 3. Finitions & Toiture")
    nb_fen = int(s_calc/12)
    total += add_line("🌧️", "APPUI", "ZINGUERIE", nb_fen)
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