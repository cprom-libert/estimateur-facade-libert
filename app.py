import streamlit as st
import time
import datetime
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="Estimateur Libert V18 (Google Connected)", layout="wide")

# ==============================================================================
# 🔑 ZONE DE CONFIGURATION (COLLEZ VOTRE CLÉ CI-DESSOUS)
# ==============================================================================
GOOGLE_API_KEY = "AIzaSyAzlkVpcASo5K2vyIL1pU0brmgNbqnQzxQ" 
# Gardez les guillemets ! Ex: "AIzaSyD5J..."
# ==============================================================================

# ==========================================
# 1. BASE DE PRIX (BENCHMARK LIBERT)
# ==========================================
DB_PRIX = {
    "INSTALLATION": {
        "BASE_VIE": {"titre": "Installation & Base Vie", "pourquoi": "Roulotte, WC et protections obligatoires.", "pu": 4500.00, "unit": "Forfait"},
        "AUTORISATION": {"titre": "Taxes de Voirie (ODP)", "pourquoi": "Redevance municipale occupation trottoir.", "pu": 605.00, "unit": "Forfait"},
        "ECHAFAUDAGE": {"titre": "Échafaudage Tubulaire", "pourquoi": "Structure classe 4 + filets pare-gravats.", "pu": 39.90, "unit": "m²"},
        "FILET": {"titre": "Filets de protection", "pourquoi": "Protection chute d'objets.", "pu": 13.00, "unit": "m²"}
    },
    "PLATRE_ANCIEN": { 
        "NETTOYAGE": {"titre": "Décapage Chimique", "pourquoi": "Retrait peintures sans abîmer le plâtre.", "pu": 16.50},
        "PIOCHAGE": {"titre": "Soin des Maçonneries (Purge)", "pourquoi": "Retrait des parties sonnant le creux.", "pu": 150.00},
        "FINITION": {"titre": "Finition Micro-Mortier", "pourquoi": "Revêtement respirant (Chaux).", "pu": 90.00},
        "RATIO_DEGATS": 0.50
    },
    "PIERRE_BRIQUE": { 
        "NETTOYAGE": {"titre": "Hydrogommage Doux", "pourquoi": "Gommage basse pression.", "pu": 25.00},
        "PIOCHAGE": {"titre": "Ragréage Pierre", "pourquoi": "Reconstitution au mortier pierre.", "pu": 37.50},
        "FINITION": {"titre": "Minéralisation", "pourquoi": "Protection invisible durcissante.", "pu": 48.00},
        "RATIO_DEGATS": 0.10
    },
    "MODERNE_BETON": { 
        "NETTOYAGE": {"titre": "Lavage Haute Pression", "pourquoi": "Décrassage profond.", "pu": 12.00},
        "PIOCHAGE": {"titre": "Traitement des fers", "pourquoi": "Passivation des aciers.", "pu": 37.50},
        "FINITION": {"titre": "Revêtement D3 Armé", "pourquoi": "Imperméabilité et souplesse.", "pu": 55.00},
        "RATIO_DEGATS": 0.05
    },
    "BOISERIE": {
        "PORTE_COCHERE": {"titre": "Restauration Porte Cochère", "pourquoi": "Décapage, greffes et lasure.", "pu": 3200.00, "unit": "Forfait"},
        "PORTE_ENTREE": {"titre": "Peinture Porte Hall", "pourquoi": "Égrenage et laque tendue.", "pu": 850.00, "unit": "Forfait"}
    },
    "ZINGUERIE": {
        "APPUI": {"titre": "Appuis de Fenêtre (Zinc)", "pourquoi": "Bavette neuve avec larmier.", "pu": 210.00, "unit": "U"},
        "DESCENTE": {"titre": "Descentes EP", "pourquoi": "Remplacement Zinc/Fonte.", "pu": 165.00, "unit": "ml"},
        "GARDE_CORPS": {"titre": "Peinture Garde-corps", "pourquoi": "Traitement antirouille.", "pu": 160.00, "unit": "U"}
    }
}

# ==========================================
# 2. FONCTIONS API (ADRESSE & IMAGE)
# ==========================================
def get_adresses_api(query):
    """Récupère les suggestions d'adresses"""
    if not query: return []
    url = f"https://api-adresse.data.gouv.fr/search/?q={query}&limit=5"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return [feature['properties']['label'] for feature in data['features']]
    except: return []
    return []

def get_facade_image(adresse, style_backup):
    """
    Tente de récupérer la vraie photo Google.
    Si pas de clé ou erreur -> Renvoie une image d'illustration.
    """
    # Si une clé est renseignée (différente du texte par défaut)
    if GOOGLE_API_KEY and "VOTRE_CLE" not in GOOGLE_API_KEY:
        base_url = "https://maps.googleapis.com/maps/api/streetview"
        params = {
            "size": "600x400",
            "location": adresse,
            "key": GOOGLE_API_KEY
        }
        # On construit l'URL finale pour l'afficher
        return f"{base_url}?size=600x400&location={adresse}&key={GOOGLE_API_KEY}"
    
    # SINON : Image de secours (Backup)
    if "Faubourien" in style_backup: return "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/14_rue_Saint-S%C3%A9bastien_Paris_11.jpg/800px-14_rue_Saint-S%C3%A9bastien_Paris_11.jpg"
    elif "Haussmannien" in style_backup: return "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Paris_-_Immeuble_bld_Raspail.jpg/800px-Paris_-_Immeuble_bld_Raspail.jpg"
    elif "Moderne" in style_backup: return "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Immeuble_d%27habitation_HBM.jpg/800px-Immeuble_d%27habitation_HBM.jpg"
    else: return "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Immeuble_parisien.jpg/800px-Immeuble_parisien.jpg"

# ==========================================
# 3. LOGIQUE IA
# ==========================================
def proposition_ia(adresse_choisie):
    # Logique prédictive simple (à remplacer par API BDNB plus tard)
    if "sebastien" in adresse_choisie.lower() or "faubourg" in adresse_choisie.lower():
        return {"style": "Faubourien (Plâtre)", "annee": 1850, "profil": "PLATRE_ANCIEN", "porte": "PORTE_COCHERE", "etages": 4, "largeur": 14}
    elif "pascal" in adresse_choisie.lower():
        return {"style": "Années 30 (Brique)", "annee": 1930, "profil": "PIERRE_BRIQUE", "porte": "PORTE_ENTREE", "etages": 6, "largeur": 18}
    else:
        return {"style": "Haussmannien (Pierre)", "annee": 1890, "profil": "PIERRE_BRIQUE", "porte": "PORTE_COCHERE", "etages": 6, "largeur": 16}

# ==========================================
# 4. INTERFACE UTILISATEUR
# ==========================================
with st.sidebar:
    st.header("🔧 Paramètres Techniques")
    st.info("L'IA pré-remplit ces valeurs. Ajustez-les si nécessaire.")
    container_params = st.container()

st.title("🏡 Estimateur Façade Interactif")
st.markdown("### 1. Localisation du Bien")

if 'adresse_input' not in st.session_state: st.session_state.adresse_input = ""
if 'data_ia' not in st.session_state: st.session_state.data_ia = None

col_search, col_btn = st.columns([3, 1])
with col_search:
    search_query = st.text_input("Adresse :", placeholder="159 rue du faubourg saint antoine...", value=st.session_state.adresse_input)
    if search_query and len(search_query) > 3:
        options = get_adresses_api(search_query)
        selected_address = st.selectbox("📍 Confirmation :", options) if options else search_query
    else:
        selected_address = None

with col_btn:
    st.write("")
    st.write("")
    launch = st.button("ANALYSER", type="primary", use_container_width=True)

if launch and selected_address:
    st.session_state.data_ia = proposition_ia(selected_address)
    st.session_state.adresse_input = selected_address

# SI UNE ADRESSE EST ANALYSÉE
if st.session_state.data_ia:
    data = st.session_state.data_ia
    
    # --- BARRE LATÉRALE (Editable) ---
    with container_params:
        val_etages = st.number_input("Nombre de niveaux (R+X +1)", value=data['etages'], min_value=1, step=1)
        val_largeur = st.number_input("Largeur Façade (m)", value=data['largeur'], min_value=5, step=1)
        
        st.markdown("---")
        hauteur_calc = val_etages * 3.0
        surface_calc = int(hauteur_calc * val_largeur)
        st.metric("Surface Totale", f"{surface_calc} m²")
        
        # Recalcul des points singuliers
        nb_fenetres = int(surface_calc / 12)
        ml_ep = int(hauteur_calc)
        
    # --- RAPPORT ---
    st.divider()
    
    # 1. VISUEL (GOOGLE OU BACKUP)
    col_img, col_txt = st.columns([1, 2])
    
    with col_img:
        # Récupération intelligente de l'image
        final_image_url = get_facade_image(selected_address, data['style'])
        st.image(final_image_url, caption=f"Vue : {selected_address}", use_column_width=True)
        
    with col_txt:
        st.subheader(f"Rapport pour : {selected_address}")
        st.success(f"**Typologie :** {data['style']} (Année env. {data['annee']})")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Niveaux", f"{val_etages} (R+{val_etages-1})")
        c2.metric("Surface", f"{surface_calc} m²")
        c3.metric("Ouvertures est.", f"{nb_fenetres} fenêtres")

    # 2. DEVIS DÉTAILLÉ
    st.markdown("### 📑 Estimation Détaillée")
    
    profil = DB_PRIX[data['profil']]
    porte_type = data['porte']
    total_ht = 0

    def ligne_devis(icon, item_key, db_cat, qte, unit_ov=None):
        item = DB_PRIX[db_cat][item_key]
        u = unit_ov if unit_ov else item.get('unit', 'm²')
        tot = qte * item['pu']
        
        with st.container():
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.markdown(f"**{icon} {item['titre']}**")
                st.caption(f"💡 {item['pourquoi']}")
            with c2:
                st.markdown(f"<div style='text-align:center;'>{qte} {u}</div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div style='text-align:right; font-weight:bold;'>{tot:,.2f} €</div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:5px 0; opacity:0.2;'>", unsafe_allow_html=True)
        return tot

    # CALCULS
    st.markdown("#### 1️⃣ Installation & Accès")
    total_ht += ligne_devis("🚧", "BASE_VIE", "LOGISTIQUE", 1, "Forfait")
    total_ht += ligne_devis("🛡️", "ECHAFAUDAGE", "LOGISTIQUE", surface_calc)
    total_ht += ligne_devis("📜", "AUTORISATION", "LOGISTIQUE", 1, "Forfait")

    st.markdown("#### 2️⃣ Maçonnerie & Façade")
    total_ht += ligne_devis("💦", "NETTOYAGE", data['profil'], surface_calc)
    
    # Piochage
    surf_pioch = int(surface_calc * profil["RATIO_DEGATS"])
    total_ht += ligne_devis("🧱", "PIOCHAGE", data['profil'], surf_pioch)
    total_ht += ligne_devis("🎨", "FINITION", data['profil'], surface_calc)

    st.markdown("#### 3️⃣ Finitions & Boiseries")
    total_ht += ligne_devis("🚪", porte_type, "BOISERIE", 1, "Unité")
    total_ht += ligne_devis("🌧️", "APPUI", "ZINGUERIE", nb_fenetres, "U")
    total_ht += ligne_devis("🚽", "DESCENTE", "ZINGUERIE", ml_ep, "ml")
    total_ht += ligne_devis("🖌️", "GARDE_CORPS", "ZINGUERIE", int(nb_fenetres*0.7), "U")

    # TOTAL
    st.markdown("---")
    col_tot_L, col_tot_R = st.columns([2, 1])
    with col_tot_R:
        st.markdown(f"<div style='background:#2c3e50; color:white; padding:15px; border-radius:5px; text-align:center;'><h3>TOTAL HT : {total_ht:,.2f} €</h3></div>", unsafe_allow_html=True)
        st.caption("TVA applicable en sus (10% ou 20%)")

elif launch:
    st.warning("Veuillez sélectionner une adresse.")