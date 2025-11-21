import streamlit as st
import time
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="Estimateur Libert V27", layout="wide", page_icon="🏡")

# ==============================================================================
# 🔑 API GOOGLE
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = "" 

# ==============================================================================
# 1. BASE DE PRIX "LIBERT 2025" (AVEC SECTION PAVILLON)
# ==============================================================================
DB_PRIX = {
    "LOGISTIQUE": {
        "BASE_VIE": {"titre": "Installation Chantier", "pourquoi": "Protection, accès et nettoyage.", "pu": 2500.00, "unit": "Forfait"},
        "ECHAFAUDAGE": {"titre": "Échafaudage", "pourquoi": "Montage/Démontage structure.", "pu": 39.90, "unit": "m²"},
        "ECHAFAUDAGE_PAV": {"titre": "Échafaudage Roulant/Fixe Léger", "pourquoi": "Structure adaptée pavillon.", "pu": 28.00, "unit": "m²"}
    },
    "PAVILLON": { # NOUVEAU PROFIL
        "NETTOYAGE": {"titre": "Lavage Basse Pression", "pourquoi": "Nettoyage façade (Kärcher doux + Antimousse).", "pu": 18.00, "unit": "m²"},
        "PIOCHAGE": {"titre": "Reprises d'enduit", "pourquoi": "Réparation des fissures et éclats.", "pu": 45.00, "unit": "m²"},
        "FINITION": {"titre": "Peinture RPE / I3", "pourquoi": "Imperméabilisation souple (Semi-épais).", "pu": 42.00, "unit": "m²"},
        "RATIO_DEGATS": 0.15
    },
    "PLATRE_ANCIEN": { 
        "NETTOYAGE": {"titre": "Décapage Chimique", "pourquoi": "Retrait peintures anciennes.", "pu": 16.50, "unit": "m²"},
        "PIOCHAGE": {"titre": "Purge Plâtre (Lourd)", "pourquoi": "Retrait des parties sonnant le creux.", "pu": 150.00, "unit": "m²"},
        "FINITION": {"titre": "Micro-Mortier Chaux", "pourquoi": "Respirant (Spécial ancien).", "pu": 90.00, "unit": "m²"},
        "RATIO_DEGATS": 0.50
    },
    "PIERRE": { 
        "NETTOYAGE": {"titre": "Hydrogommage", "pourquoi": "Gommage doux.", "pu": 25.00, "unit": "m²"},
        "PIOCHAGE": {"titre": "Ragréage Pierre", "pourquoi": "Reconstitution mortier pierre.", "pu": 37.50, "unit": "m²"},
        "FINITION": {"titre": "Minéralisation", "pourquoi": "Protection invisible.", "pu": 48.00, "unit": "m²"},
        "RATIO_DEGATS": 0.10
    },
    "ZINGUERIE": {
        "APPUI": {"titre": "Appuis Zinc", "pourquoi": "Bavette neuve.", "pu": 210.00, "unit": "U"},
        "DESCENTE": {"titre": "Descentes EP", "pourquoi": "Remplacement.", "pu": 165.00, "unit": "ml"},
        "GARDE_CORPS": {"titre": "Peinture Fer", "pourquoi": "Antirouille.", "pu": 160.00, "unit": "U"},
        "DEBORD_TOIT": {"titre": "Peinture Débords de Toit", "pourquoi": "Lasure des planches de rive/lambris.", "pu": 45.00, "unit": "ml"}
    }
}

# ==============================================================================
# 2. MOTEUR DE RECHERCHE INSTANTANÉ
# ==============================================================================
def search_address_live(user_input):
    """Retourne une liste d'adresses formatées pour le menu déroulant"""
    if not user_input or len(user_input) < 4:
        return []
    url = f"https://api-adresse.data.gouv.fr/search/?q={user_input}&limit=5"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            # On renvoie une liste propre
            return [f['properties']['label'] for f in r.json()['features']]
    except:
        return []
    return []

# ==============================================================================
# 3. MOTEUR ANALYSE (OSM + LOGIQUE PAVILLON)
# ==============================================================================
def get_geo_data(adresse):
    # Récup Lat/Lon pour interroger OSM
    url = f"https://api-adresse.data.gouv.fr/search/?q={adresse}&limit=1"
    try:
        r = requests.get(url).json()
        if r['features']:
            c = r['features'][0]['geometry']['coordinates']
            return c[1], c[0]
    except: return None, None
    return None, None

def query_osm_structure(lat, lon):
    # On demande à OSM : est-ce une maison (detached) ou un immeuble ?
    query = f"""
    [out:json];
    (
      way["building"](around:15, {lat}, {lon});
    );
    out body;
    >;
    out skel qt;
    """
    try:
        r = requests.get("http://overpass-api.de/api/interpreter", params={'data': query})
        data = r.json()
        tags = {}
        if data['elements']:
            for el in data['elements']:
                if 'tags' in el:
                    tags = el['tags']
                    break
        return tags
    except: return {}

def analyser_projet(adresse):
    lat, lon = get_geo_data(adresse)
    if not lat: return None
    
    osm_tags = query_osm_structure(lat, lon)
    
    # 1. DÉTECTION PAVILLON VS IMMEUBLE
    type_bat = "IMMEUBLE"
    profil = "PIERRE" # Défaut
    
    # Indices OSM pour pavillon
    if osm_tags.get("building") == "detached" or osm_tags.get("building") == "house":
        type_bat = "PAVILLON"
        profil = "PAVILLON"
    
    # Indice Hauteur (Si < R+2 -> Probablement pavillon)
    etages = int(osm_tags.get("building:levels", 3))
    if etages <= 2:
        type_bat = "PAVILLON"
        profil = "PAVILLON"
    elif etages > 4:
        type_bat = "IMMEUBLE"
        profil = "PIERRE" # Par défaut Paris
    
    # Correction Profil Immeuble selon adresse (Fallback)
    if type_bat == "IMMEUBLE":
        if "sebastien" in adresse.lower() or "faubourg" in adresse.lower():
            profil = "PLATRE_ANCIEN"
        elif "general" in adresse.lower():
            profil = "BETON"

    # 2. CALCUL GÉOMÉTRIQUE
    # Estimation largeur façade (Faute de mieux via OSM)
    largeur = 10 if type_bat == "PAVILLON" else 16
    hauteur = etages * 3.0
    
    # CALCUL SURFACE (LA DIFFÉRENCE EST ICI)
    if type_bat == "PAVILLON":
        # Pavillon = On fait le tour (4 faces estimées)
        # Hypothèse : Maison carrée 10x10 -> Périmètre 40m
        perimetre = largeur * 3.5 # On estime 3.5 faces traitées moy.
        surface = int(perimetre * hauteur)
    else:
        # Immeuble = Juste la façade rue
        surface = int(largeur * hauteur)

    return {
        "adresse": adresse,
        "type": type_bat,
        "profil": profil,
        "geo": {"etages": etages, "largeur": largeur, "surface": surface},
        "osm": osm_tags
    }

def get_google_image(adresse):
    if GOOGLE_API_KEY and len(GOOGLE_API_KEY) > 10:
        return f"https://maps.googleapis.com/maps/api/streetview?size=640x480&location={adresse}&fov=120&pitch=5&key={GOOGLE_API_KEY}"
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c9/Pavillon_banlieue.jpg/800px-Pavillon_banlieue.jpg"

# ==============================================================================
# 4. INTERFACE UTILISATEUR
# ==============================================================================

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎛️ Ajustements")
    container_params = st.container()

# --- TITRE ---
st.title("🏡 Estimateur Façade (Immeuble & Pavillon)")

# --- BARRE DE RECHERCHE INTELLIGENTE ---
# On utilise un selectbox qui agit comme une barre de recherche
if 'adresse_sel' not in st.session_state: st.session_state.adresse_sel = None

# Astuce UX : On demande de taper d'abord
recherche = st.text_input("Tapez votre adresse :", placeholder="Ex: 12 allée des cerisiers...", help="Tapez et appuyez sur Entrée pour voir les suggestions")

# Si du texte est entré, on charge les suggestions
options_adresses = []
if recherche and len(recherche) > 4:
    options_adresses = search_address_live(recherche)

# Si on a des résultats, on affiche le selectbox pour valider
final_addr = None
if options_adresses:
    final_addr = st.selectbox("📍 Sélectionnez l'adresse exacte :", options_adresses)
elif recherche and len(recherche) > 4:
    st.caption("Aucune suggestion exacte trouvée, on utilise le texte brut.")
    final_addr = recherche

# --- LANCEMENT AUTOMATIQUE SI ADRESSE SÉLECTIONNÉE ---
if final_addr:
    if st.button("CALCULER LE DEVIS", type="primary", use_container_width=True):
        with st.spinner("Analyse de la parcelle..."):
            time.sleep(1)
            st.session_state.data = analyser_projet(final_addr)

# --- RÉSULTATS ---
if 'data' in st.session_state and st.session_state.data:
    d = st.session_state.data
    
    # 1. PARAMÈTRES EDITABLES
    with container_params:
        # Type de bien détecté
        st.info(f"Type détecté : **{d['type']}**")
        
        v_etages = st.number_input("Niveaux (R+)", value=d['geo']['etages'], min_value=1)
        
        # Logique différente selon type
        if d['type'] == "PAVILLON":
            v_perimetre = st.number_input("Périmètre maison (m)", value=int(d['geo']['largeur']*3.5), help="Tour de la maison")
            surface_calc = v_perimetre * (v_etages * 3.0)
            st.caption("Calcul : Périmètre x Hauteur")
        else:
            v_largeur = st.number_input("Largeur Façade (m)", value=d['geo']['largeur'])
            surface_calc = v_largeur * (v_etages * 3.0)
            st.caption("Calcul : Façade x Hauteur")
            
        st.metric("Surface à traiter", f"{int(surface_calc)} m²")
        
    # 2. VISUEL
    st.divider()
    c_img, c_txt = st.columns([1, 2])
    with c_img:
        st.image(get_google_image(d['adresse']), caption="Vue Satellite", use_column_width=True)
    with c_txt:
        st.subheader(f"Rapport : {d['type']}")
        st.success(f"Profil Prix : {d['profil']}")
        
        if d['type'] == "PAVILLON":
            st.markdown("""
            * **Configuration :** Maison Individuelle (4 façades estimées)
            * **Échafaudage :** Allégé (Roulant/Fixe)
            * **Points clés :** Débords de toits, soubassements.
            """)
        else:
            st.markdown("""
            * **Configuration :** Immeuble Collectif (Façade rue)
            * **Échafaudage :** Lourd (Classe 4 + ODP)
            * **Points clés :** Bandeaux, Garde-corps, Sécurité rue.
            """)

    # 3. DEVIS
    st.markdown("### 📑 Estimation Détaillée")
    
    profil_prix = DB_PRIX[d['profil']]
    total = 0
    
    def add(icon, key, cat, qty, u=None):
        if key not in DB_PRIX[cat]: return 0
        item = DB_PRIX[cat][key]
        unit = u if u else item['unit']
        p = qty * item['pu']
        
        with st.container():
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.markdown(f"**{icon} {item['titre']}**\n<small style='color:grey'>{item['pourquoi']}</small>", unsafe_allow_html=True)
            c2.markdown(f"<div style='text-align:center'>{int(qty)} {unit}</div>", unsafe_allow_html=True)
            c3.markdown(f"<div style='text-align:right'><b>{p:,.2f} €</b></div>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:5px 0; opacity:0.1'>", unsafe_allow_html=True)
        return p

    # LOGISTIQUE (Différente si Pavillon)
    st.markdown("##### 1. Installation")
    if d['type'] == "PAVILLON":
        total += add("🛡️", "ECHAFAUDAGE_PAV", "LOGISTIQUE", surface_calc)
        # Pas de base vie lourde ni taxe voirie souvent pour pavillon
        st.caption("ℹ️ Pas de taxe voirie comptée pour pavillon (domaine privé).")
    else:
        total += add("🚧", "BASE_VIE", "LOGISTIQUE", 1)
        total += add("🛡️", "ECHAFAUDAGE", "LOGISTIQUE", surface_calc)
        total += add("📜", "AUTORISATION", "LOGISTIQUE", 1)

    # TRAITEMENT
    st.markdown("##### 2. Façade")
    total += add("💦", "NETTOYAGE", d['profil'], surface_calc)
    s_pioch = int(surface_calc * profil_prix["RATIO_DEGATS"])
    total += add("🧱", "PIOCHAGE", d['profil'], s_pioch)
    total += add("🎨", "FINITION", d['profil'], surface_calc)

    # FINITIONS
    st.markdown("##### 3. Détails")
    nb_fen = int(surface_calc/15)
    total += add("🌧️", "APPUI", "ZINGUERIE", nb_fen)
    
    if d['type'] == "PAVILLON":
        # Débords de toit (Périmètre maison)
        perim = surface_calc / (v_etages * 3.0)
        total += add("🏠", "DEBORD_TOIT", "ZINGUERIE", perim, "ml")
    else:
        total += add("🖌️", "GARDE_CORPS", "ZINGUERIE", int(nb_fen*0.7))

    # TOTAL
    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    with col2:
        st.markdown(f"""
        <div style="background:#2c3e50;color:white;padding:20px;border-radius:10px;text-align:right">
            <small>TOTAL HT</small>
            <h1 style="margin:0">{total:,.2f} €</h1>
        </div>
        """, unsafe_allow_html=True)