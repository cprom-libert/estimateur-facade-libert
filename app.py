import streamlit as st
import time
import datetime
import requests

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Estimateur Libert & Cie", layout="wide", page_icon="🏗️")

# ==============================================================================
# 1. GESTION DE LA CLÉ API GOOGLE (Sécurisée)
# ==============================================================================
# Le code cherche la clé dans les "Secrets" ou permet de la rentrer manuellement
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = ""

# ==============================================================================
# 2. BASE DE PRIX & PÉDAGOGIE (BENCHMARK LIBERT 2025)
# ==============================================================================
DB_PRIX = {
    "LOGISTIQUE": {
        "BASE_VIE": {"titre": "Installation & Base Vie", "pourquoi": "Roulotte, WC et protections obligatoires (Sécurité).", "pu": 4500.00, "unit": "Forfait"},
        "AUTORISATION": {"titre": "Taxes de Voirie (ODP)", "pourquoi": "Redevance municipale pour occupation du trottoir.", "pu": 605.00, "unit": "Forfait"},
        "ECHAFAUDAGE": {"titre": "Échafaudage Tubulaire", "pourquoi": "Structure Classe 4 avec filets pare-gravats.", "pu": 39.90, "unit": "m²"},
        "FILET": {"titre": "Filets de protection", "pourquoi": "Protection chute d'objets (Obligatoire).", "pu": 13.00, "unit": "m²"}
    },
    "PLATRE_ANCIEN": { 
        "NETTOYAGE": {"titre": "Décapage Chimique", "pourquoi": "Retrait des peintures sans abîmer le plâtre fragile.", "pu": 16.50},
        "PIOCHAGE": {"titre": "Soin des Maçonneries (Purge)", "pourquoi": "Retrait des parties qui sonnent creux (Vital pour la tenue).", "pu": 150.00},
        "FINITION": {"titre": "Finition Micro-Mortier", "pourquoi": "Revêtement respirant (Laisse sortir l'humidité).", "pu": 90.00},
        "RATIO_DEGATS": 0.50 # 50% de la surface est souvent à refaire
    },
    "PIERRE_BRIQUE": { 
        "NETTOYAGE": {"titre": "Hydrogommage Doux", "pourquoi": "Gommage basse pression pour respecter le calin de la pierre.", "pu": 25.00},
        "PIOCHAGE": {"titre": "Ragréage Pierre", "pourquoi": "Reconstitution des pierres abîmées au mortier spécial.", "pu": 37.50},
        "FINITION": {"titre": "Minéralisation", "pourquoi": "Protection invisible qui durcit la pierre.", "pu": 48.00},
        "RATIO_DEGATS": 0.10
    },
    "MODERNE_BETON": { 
        "NETTOYAGE": {"titre": "Lavage Haute Pression", "pourquoi": "Décrassage profond de la pollution.", "pu": 12.00},
        "PIOCHAGE": {"titre": "Traitement des fers", "pourquoi": "Passivation des aciers pour stopper la rouille.", "pu": 37.50},
        "FINITION": {"titre": "Revêtement D3 Armé", "pourquoi": "Imperméabilité totale et souplesse (Anti-fissure).", "pu": 55.00},
        "RATIO_DEGATS": 0.05
    },
    "BOISERIE": {
        "PORTE_COCHERE": {"titre": "Restauration Porte Cochère", "pourquoi": "Décapage, greffes de bois et lasure.", "pu": 3200.00, "unit": "Forfait"},
        "PORTE_ENTREE": {"titre": "Peinture Porte Hall", "pourquoi": "Égrenage et laque tendue haute résistance.", "pu": 850.00, "unit": "Forfait"}
    },
    "ZINGUERIE": {
        "APPUI": {"titre": "Appuis de Fenêtre (Zinc)", "pourquoi": "Bavette neuve pour rejeter l'eau loin de la façade.", "pu": 210.00, "unit": "U"},
        "DESCENTE": {"titre": "Descentes EP", "pourquoi": "Remplacement Zinc/Fonte (Étanchéité garantie).", "pu": 165.00, "unit": "ml"},
        "GARDE_CORPS": {"titre": "Peinture Garde-corps", "pourquoi": "Traitement antirouille indispensable.", "pu": 160.00, "unit": "U"},
        "BANDEAU": {"titre": "Couvre-Murette Zinc", "pourquoi": "Protection des bandeaux saillants contre la pluie.", "pu": 178.00, "unit": "ml"}
    }
}

# ==============================================================================
# 3. FONCTIONS INTELLIGENTES (API & IA)
# ==============================================================================

def get_adresses_api(query):
    """Autocomplétion adresse via API Gouv"""
    if not query: return []
    url = f"https://api-adresse.data.gouv.fr/search/?q={query}&limit=5"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return [f['properties']['label'] for f in r.json()['features']]
    except: return []
    return []

def get_facade_image(adresse, style_backup, user_key=None):
    """
    Récupère la photo Google Street View avec réglages GRAND ANGLE.
    """
    # Priorité à la clé utilisateur si fournie dans la sidebar, sinon clé secrète
    api_key = user_key if user_key else GOOGLE_API_KEY
    
    if api_key and len(api_key) > 10:
        base_url = "https://maps.googleapis.com/maps/api/streetview"
        # PARAMÈTRES AJUSTÉS VUE D'ENSEMBLE :
        # fov=120 (Grand angle max)
        # pitch=10 (Regarde vers le haut pour voir le toit)
        params = f"?size=640x640&location={adresse}&fov=120&pitch=10&key={api_key}"
        return f"{base_url}{params}"
    
    # SINON : Image illustrative (Backup)
    if "Faubourien" in style_backup: return "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/14_rue_Saint-S%C3%A9bastien_Paris_11.jpg/800px-14_rue_Saint-S%C3%A9bastien_Paris_11.jpg"
    elif "Haussmannien" in style_backup: return "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Paris_-_Immeuble_bld_Raspail.jpg/800px-Paris_-_Immeuble_bld_Raspail.jpg"
    elif "Moderne" in style_backup: return "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Immeuble_d%27habitation_HBM.jpg/800px-Immeuble_d%27habitation_HBM.jpg"
    else: return "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Immeuble_parisien.jpg/800px-Immeuble_parisien.jpg"

def proposition_ia(adresse_choisie):
    """Déduction du style et des dimensions selon l'adresse"""
    ads = adresse_choisie.lower()
    if "sebastien" in ads or "faubourg" in ads:
        return {"style": "Faubourien (Plâtre)", "annee": "1850", "profil": "PLATRE_ANCIEN", "porte": "PORTE_COCHERE", "etages": 4, "largeur": 14}
    elif "pascal" in ads or "thibaud" in ads:
        return {"style": "Années 30 (Brique)", "annee": "1930", "profil": "PIERRE_BRIQUE", "porte": "PORTE_ENTREE", "etages": 6, "largeur": 18}
    elif "general" in ads or "leclerc" in ads:
        return {"style": "Moderne (Béton)", "annee": "1970", "profil": "MODERNE_BETON", "porte": "PORTE_ENTREE", "etages": 7, "largeur": 22}
    else:
        # Par défaut
        return {"style": "Haussmannien (Pierre)", "annee": "1890", "profil": "PIERRE_BRIQUE", "porte": "PORTE_COCHERE", "etages": 6, "largeur": 16}

# ==============================================================================
# 4. INTERFACE UTILISATEUR (STREAMLIT)
# ==============================================================================

# --- SIDEBAR (Réglages) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/10967/10967633.png", width=50)
    st.header("Paramètres")
    
    # Zone pour mettre la clé manuellement si besoin
    user_api_key = st.text_input("Clé API Google (Optionnel)", type="password", help="Collez votre clé ici si vous n'utilisez pas les secrets.")
    
    st.divider()
    st.info("L'IA pré-remplit les dimensions ci-dessous une fois l'adresse choisie. Vous pouvez les corriger.")
    
    # Conteneur vide qui sera rempli après l'analyse
    container_params = st.container()

# --- MAIN PAGE ---
st.title("🏡 Estimateur Façade Libert & Cie")
st.markdown("### Diagnostic Instantané & Devis Détaillé")

# Gestion de l'état (Session State)
if 'adresse_input' not in st.session_state: st.session_state.adresse_input = ""
if 'data_ia' not in st.session_state: st.session_state.data_ia = None

# Zone Recherche
col1, col2 = st.columns([3, 1])
with col1:
    search = st.text_input("Entrez l'adresse du bâtiment :", placeholder="Ex: 159 rue du faubourg saint antoine...", value=st.session_state.adresse_input)
    # Menu déroulant API Gouv
    if search and len(search) > 4:
        opts = get_adresses_api(search)
        if opts: final_addr = st.selectbox("📍 Sélectionnez l'adresse exacte :", opts)
        else: final_addr = search
    else:
        final_addr = None

with col2:
    st.write("") 
    st.write("") 
    launch = st.button("LANCER L'AUDIT", type="primary", use_container_width=True)

if launch and final_addr:
    st.session_state.data_ia = proposition_ia(final_addr)
    st.session_state.adresse_input = final_addr

# --- AFFICHAGE DES RÉSULTATS ---
if st.session_state.data_ia:
    d = st.session_state.data_ia
    
    # 1. BARRE LATÉRALE DYNAMIQUE (Correction Manuelle)
    with container_params:
        val_etages = st.number_input("Niveaux (R+)", value=d['etages'], min_value=1, step=1)
        val_largeur = st.number_input("Largeur Façade (m)", value=d['largeur'], min_value=5, step=1)
        
        # Calculs en temps réel
        hauteur_calc = val_etages * 3.0
        s_calc = int(hauteur_calc * val_largeur)
        nb_fen = int(s_calc / 12)
        
        st.divider()
        st.metric("📏 Surface Calculée", f"{s_calc} m²")
        st.caption(f"Hauteur estimée : {hauteur_calc}m")

    # 2. CONTENU PRINCIPAL
    st.divider()
    
    # BLOC VISUEL
    c_img, c_info = st.columns([1, 1.5])
    with c_img:
        # Appel de l'image (avec clé utilisateur ou secrète)
        img_src = get_facade_image(st.session_state.adresse_input, d['style'], user_api_key)
        st.image(img_src, caption="Vue Grand Angle (IA)", use_column_width=True)
        
    with c_info:
        st.subheader(f"Rapport pour : {st.session_state.adresse_input}")
        st.success(f"**Architecture identifiée :** {d['style']}")
        
        # Indicateurs
        k1, k2, k3 = st.columns(3)
        k1.metric("Année", d['annee'])
        k2.metric("Niveaux", f"R+{val_etages-1}")
        k3.metric("Ouvertures", f"{nb_fen} fenêtres")
        
        st.info("💡 **Note :** L'estimation ci-dessous inclut le traitement spécifique des points singuliers (zinguerie, menuiseries) détectés pour ce type de bâtiment.")

    # 3. DEVIS DÉTAILLÉ (PÉDAGOGIQUE)
    st.markdown("### 📑 Détail de l'Investissement")
    
    profil = DB_PRIX[d['profil']]
    total_ht = 0
    
    def ligne_devis(icon, key, cat, qte, unit=None):
        # Sécurité clé
        if key not in DB_PRIX[cat]: return 0
        
        item = DB_PRIX[cat][key]
        u = unit if unit else item.get('unit', 'm²')
        tot = qte * item['pu']
        
        with st.container():
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.markdown(f"**{icon} {item['titre']}**")
                st.caption(f"ℹ️ {item['pourquoi']}")
            with c2:
                st.markdown(f"<div style='text-align:center; padding-top:5px;'>{qte} {u}</div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div style='text-align:right; font-weight:bold; color:#2c3e50;'>{tot:,.2f} €</div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:5px 0; opacity:0.1;'>", unsafe_allow_html=True)
        return tot

    # SECTION 1
    st.markdown("#### 1️⃣ Installation & Sécurité")
    total_ht += ligne_devis("🚧", "BASE_VIE", "LOGISTIQUE", 1, "Forfait")
    total_ht += ligne_devis("🛡️", "ECHAFAUDAGE", "LOGISTIQUE", s_calc)
    total_ht += ligne_devis("📜", "AUTORISATION", "LOGISTIQUE", 1, "Forfait")

    # SECTION 2
    st.markdown("#### 2️⃣ Traitement de Façade")
    total_ht += ligne_devis("💦", "NETTOYAGE", d['profil'], s_calc)
    
    # Piochage (Calcul critique)
    s_pioch = int(s_calc * profil["RATIO_DEGATS"])
    # Personnalisation du titre si gros dégâts
    titre_pioch = "Soin des Maçonneries"
    if profil["RATIO_DEGATS"] >= 0.5: titre_pioch = "⚠️ Réfection Lourde des Fonds"
    
    # On hacke un peu pour afficher le bon titre
    DB_PRIX[d['profil']]["PIOCHAGE"]["titre"] = titre_pioch
    
    total_ht += ligne_devis("🧱", "PIOCHAGE", d['profil'], s_pioch)
    total_ht += ligne_devis("🎨", "FINITION", d['profil'], s_calc)

    # SECTION 3
    st.markdown("#### 3️⃣ Finitions & Détails")
    total_ht += ligne_devis("🚪", d['porte'], "BOISERIE", 1, "U")
    total_ht += ligne_devis("🌧️", "APPUI", "ZINGUERIE", nb_fen, "U")
    total_ht += ligne_devis("⬇️", "DESCENTE", "ZINGUERIE", int(hauteur_calc), "ml")
    # Bandeau (estimé largeur x 2)
    total_ht += ligne_devis("🏛️", "BANDEAU", "ZINGUERIE", int(val_largeur*2), "ml")
    # Garde-corps (70% des fenêtres)
    total_ht += ligne_devis("🖌️", "GARDE_CORPS", "ZINGUERIE", int(nb_fen*0.7), "U")

    # TOTAL FINAL
    st.markdown("---")
    col_fin_txt, col_fin_prix = st.columns([2, 1])
    with col_fin_prix:
        st.markdown(f"""
        <div style="background:#2c3e50; color:white; padding:20px; border-radius:8px; text-align:right;">
            <div style="font-size:0.9em; opacity:0.8;">TOTAL ESTIMATIF HT</div>
            <div style="font-size:1.8em; font-weight:bold;">{total_ht:,.2f} €</div>
        </div>
        """, unsafe_allow_html=True)
    with col_fin_txt:
        st.caption("⚠️ Estimation indicative basée sur une analyse visuelle et algorithmique. Ce document ne vaut pas contrat. Une visite technique est obligatoire pour valider les supports (notamment l'état réel des plâtres et l'adhérence). TVA non incluse.")

elif launch:
    st.warning("Veuillez sélectionner une adresse dans la liste.")