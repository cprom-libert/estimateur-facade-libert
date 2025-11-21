import streamlit as st
import time
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="Estimateur Libert V44 (Design)", layout="wide", page_icon="🎨")

# ==============================================================================
# 🎨 CSS PERSONNALISÉ (LE SECRET DU DESIGN)
# ==============================================================================
st.markdown("""
<style>
    /* Fond général plus doux */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* En-tête stylisé */
    .main-header {
        background: linear-gradient(90deg, #2c3e50 0%, #34495e 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Cartes de statistiques */
    .stat-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #e67e22;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
    }
    .stat-value { font-size: 24px; font-weight: bold; color: #2c3e50; }
    .stat-label { font-size: 14px; color: #7f8c8d; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Tableau de devis propre */
    .quote-table {
        width: 100%;
        border-collapse: collapse;
        background: white;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }
    .quote-table th {
        background-color: #2c3e50;
        color: white;
        padding: 15px;
        text-align: left;
        font-weight: 600;
    }
    .quote-table td {
        padding: 15px;
        border-bottom: 1px solid #eee;
        color: #444;
    }
    .quote-row:hover { background-color: #fcfcfc; }
    .price-cell { font-weight: bold; color: #2c3e50; text-align: right; }
    .qty-cell { text-align: center; background: #f8f9fa; border-radius: 4px; font-size: 0.9em; }
    
    /* Total */
    .total-block {
        background-color: #2c3e50;
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: right;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. CONFIG ET DATA
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = ""

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
        "PLATRE_ANCIEN": {"titre": "Restauration Plâtre (Traditionnel)", "nettoyage": 16.50, "piochage": 160.00, "finition": 95.00, "ratio_degats": 0.50, "desc": "Décapage + Purge lourde + Micro-mortier"},
        "PIERRE_TAILLE": {"titre": "Ravalement Pierre de Taille", "nettoyage": 28.00, "piochage": 85.00, "finition": 48.00, "ratio_degats": 0.10, "desc": "Hydrogommage + Ragréage + Minéralisation"},
        "BRIQUE": {"titre": "Restauration Brique", "nettoyage": 35.00, "piochage": 120.00, "finition": 25.00, "ratio_degats": 0.15, "desc": "Nettoyage chimique + Changement briques + Hydrofuge"},
        "BETON": {"titre": "Ravalement Technique D3", "nettoyage": 12.00, "piochage": 45.00, "finition": 58.00, "ratio_degats": 0.05, "desc": "Lavage HP + Passivation fers + RPE Armé"},
        "PAVILLON_ENDUIT": {"titre": "Ravalement Maison I3", "nettoyage": 18.00, "piochage": 45.00, "finition": 42.00, "ratio_degats": 0.10, "desc": "Lavage + Reprise fissures + RPE Souple"}
    },
    "ZINGUERIE": {
        "APPUI": {"titre": "Appuis Zinc", "pourquoi": "Bavette neuve.", "pu": 215.00, "unit": "U"},
        "DESCENTE": {"titre": "Descentes EP", "pourquoi": "Remplacement Zinc/Fonte.", "pu": 165.00, "unit": "ml"},
        "GARDE_CORPS": {"titre": "Peinture Garde-corps", "pourquoi": "Traitement antirouille.", "pu": 160.00, "unit": "U"},
        "BANDEAU": {"titre": "Bandeau Zinc", "pourquoi": "Protection.", "pu": 178.00, "unit": "ml"},
        "CHIEN_ASSIS": {"titre": "Habillage Chien-Assis", "pourquoi": "Rénovation zinc lucarne.", "pu": 950.00, "unit": "U"}
    },
    "BOISERIE": {
        "PORTE_COCHERE": {"titre": "Restauration Porte Cochère", "pourquoi": "Décapage, greffes, lasure.", "pu": 3200.00, "unit": "U"},
        "PORTE_ENTREE": {"titre": "Peinture Porte Hall", "pourquoi": "Égrenage et laque.", "pu": 850.00, "unit": "U"}
    }
}

# ==============================================================================
# 2. FONCTIONS TECHNIQUES
# ==============================================================================
def get_geo_data(adresse):
    try:
        r = requests.get(f"https://api-adresse.data.gouv.fr/search/?q={adresse}&limit=1").json()
        if r['features']:
            c = r['features'][0]['geometry']['coordinates']
            return c[1], c[0]
    except: return None, None
    return None, None

def query_osm_real_data(lat, lon):
    query = f"""
    [out:json];
    (way["building"](around:20, {lat}, {lon}););
    out body;
    >;
    out skel qt;
    """
    try:
        r = requests.get("http://overpass-api.de/api/interpreter", params={'data': query})
        data = r.json()
        if data['elements']:
            for el in data['elements']:
                if 'tags' in el:
                    t = el['tags']
                    return {
                        "niveaux": int(t.get("building:levels", 0)),
                        "toit": int(t.get("roof:levels", 0)),
                        "commerce": True if (t.get("shop") or t.get("building:use") == "retail") else False,
                        "annee": t.get("start_date", "Inconnue")
                    }
    except: pass
    return {"niveaux": 0, "toit": 0, "commerce": False, "annee": "Inconnue"}

def get_adresses_api(query):
    if len(query) < 3: return []
    try:
        r = requests.get(f"https://api-adresse.data.gouv.fr/search/?q={query}&limit=5")
        return [f['properties']['label'] for f in r.json()['features']]
    except: return []

def get_street_view(adresse, heading, pitch):
    if GOOGLE_API_KEY and len(GOOGLE_API_KEY) > 10:
        return f"https://maps.googleapis.com/maps/api/streetview?size=640x480&location={adresse}&fov=110&heading={heading}&pitch={pitch}&key={GOOGLE_API_KEY}"
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Immeuble_parisien.jpg/800px-Immeuble_parisien.jpg"

# ==============================================================================
# 3. INTERFACE
# ==============================================================================

# Gestion Session
if 'step' not in st.session_state: st.session_state.step = 0
if 'real_data' not in st.session_state: st.session_state.real_data = {}
if 'addr_label' not in st.session_state: st.session_state.addr_label = ""
if 'cam_h' not in st.session_state: st.session_state.cam_h = 0
if 'cam_p' not in st.session_state: st.session_state.cam_p = 10

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎛️ Console Expert")
    
    st.subheader("📷 Cadrage Photo")
    c1, c2, c3 = st.columns(3)
    def rot(angle): st.session_state.cam_h = (st.session_state.cam_h + angle) % 360
    if c1.button("⬅️"): rot(-45)
    if c2.button("🔄"): rot(180)
    if c3.button("➡️"): rot(45)
    st.session_state.cam_p = st.slider("Haut/Bas", -10, 60, st.session_state.cam_p)
    
    st.divider()
    st.subheader("🏗️ Données Techniques")
    params_container = st.container()

# --- RECHERCHE (HEADER) ---
# Affichage d'un beau titre uniquement si pas de résultat encore
if st.session_state.step == 0:
    st.markdown("""
    <div class="main-header">
        <h1>🏡 Estimateur Libert & Cie</h1>
        <p>Analysez n'importe quel bâtiment instantanément : Surface, État, Prix.</p>
    </div>
    """, unsafe_allow_html=True)

c_search, c_btn = st.columns([3, 1])
with c_search:
    q = st.text_input("Rechercher une adresse :", placeholder="Ex: 159 rue du faubourg saint antoine...", label_visibility="collapsed")
    final_addr = None
    if q and len(q) > 4:
        opts = get_adresses_api(q)
        if opts: final_addr = st.selectbox("📍 Sélectionnez :", opts)
        else: final_addr = q

with c_btn:
    if st.button("LANCER L'ESTIMATION", type="primary", use_container_width=True):
        if final_addr:
            with st.spinner("Analyse en cours..."):
                lat, lon = get_geo_data(final_addr)
                if lat:
                    st.session_state.real_data = query_osm_real_data(lat, lon)
                    st.session_state.addr_label = final_addr
                    st.session_state.cam_h = 0
                    st.session_state.step = 1
                else:
                    st.error("Adresse introuvable.")

# --- RESULTATS ---
if st.session_state.step == 1:
    rd = st.session_state.real_data
    
    # 1. CONFIGURATION (Sidebar)
    with params_container:
        ads = st.session_state.addr_label.lower()
        def_mat_idx = 1 
        if "sebastien" in ads or "faubourg" in ads: def_mat_idx = 0
        elif "general" in ads: def_mat_idx = 3
        
        u_mat = st.selectbox("Support Façade", list(DB_PRIX["FACADES"].keys()), index=def_mat_idx)
        st.markdown("---")
        
        # Hauteur & Largeur
        val_niv = rd['niveaux'] if rd['niveaux'] > 0 else 5
        u_niv = st.number_input("Niveaux (R+)", value=val_niv, min_value=1)
        u_larg = st.number_input("Largeur (m)", value=15, min_value=5)
        
        st.markdown("---")
        u_com = st.checkbox("Commerce RDC", value=rd['commerce'])
        u_alarme = st.checkbox("Alarme", value=True)
        has_toit = True if rd['toit'] > 0 else False
        u_chiens = st.number_input("Chiens-assis", value=(2 if has_toit else 0))
        u_porte = st.selectbox("Porte Entrée", ["PORTE_COCHERE", "PORTE_ENTREE", "AUCUNE"])

    # Calculs
    h_calc = u_niv * 3.0
    s_calc = int(h_calc * u_larg)
    nb_fen = int(s_calc / 12)

    # 2. VISUEL & SYNTHÈSE (DESIGN CARD)
    st.markdown(f"### 📍 Rapport pour : {st.session_state.addr_label}")
    
    col_viz, col_stats = st.columns([1.5, 1])
    
    with col_viz:
        st.image(get_street_view(st.session_state.addr_label, st.session_state.cam_h, st.session_state.cam_p), use_column_width=True)
    
    with col_stats:
        # Cartes de stats avec HTML
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{s_calc} m²</div>
            <div class="stat-label">Surface Façade</div>
        </div>
        <div class="stat-card" style="margin-top:10px;">
            <div class="stat-value">R+{u_niv-1}</div>
            <div class="stat-label">Hauteur ({h_calc}m)</div>
        </div>
        <div class="stat-card" style="margin-top:10px; border-left: 5px solid #3498db;">
            <div class="stat-value">{DB_PRIX["FACADES"][u_mat]["titre"]}</div>
            <div class="stat-label">Type de Travaux</div>
        </div>
        """, unsafe_allow_html=True)

    # 3. DEVIS (DESIGN TABLEAU)
    st.markdown("### 📑 Détail Estimatif")
    
    # Génération du HTML du tableau
    table_html = """
    <table class="quote-table">
        <thead>
            <tr>
                <th width="50%">Désignation des ouvrages</th>
                <th width="15%">Quantité</th>
                <th width="15%" style="text-align:right;">Prix U.</th>
                <th width="20%" style="text-align:right;">Total HT</th>
            </tr>
        </thead>
        <tbody>
    """
    
    total = 0
    prof = DB_PRIX["FACADES"][u_mat]

    def add_html_row(titre, desc, qte, pu, unit):
        tot = qte * pu
        return tot, f"""
        <tr class="quote-row">
            <td>
                <div style="font-weight:600; color:#2c3e50;">{titre}</div>
                <div style="font-size:0.85em; color:#7f8c8d;">{desc}</div>
            </td>
            <td class="qty-cell">{int(qte)} {unit}</td>
            <td style="text-align:right;">{pu:,.2f} €</td>
            <td class="price-cell">{tot:,.2f} €</td>
        </tr>
        """

    # A. LOGISTIQUE
    table_html += "<tr><td colspan='4' style='background:#f1f2f6; font-weight:bold; color:#7f8c8d; font-size:0.8em;'>1. LOGISTIQUE & SÉCURITÉ</td></tr>"
    t, r = add_html_row(DB_PRIX["LOGISTIQUE"]["BASE_VIE"]["titre"], DB_PRIX["LOGISTIQUE"]["BASE_VIE"]["pourquoi"], 1, DB_PRIX["LOGISTIQUE"]["BASE_VIE"]["pu"], "U")
    total += t; table_html += r
    
    t, r = add_html_row(DB_PRIX["LOGISTIQUE"]["ECHAFAUDAGE"]["titre"], DB_PRIX["LOGISTIQUE"]["ECHAFAUDAGE"]["pourquoi"], s_calc, DB_PRIX["LOGISTIQUE"]["ECHAFAUDAGE"]["pu"], "m²")
    total += t; table_html += r
    
    t, r = add_html_row(DB_PRIX["LOGISTIQUE"]["AUTORISATION"]["titre"], DB_PRIX["LOGISTIQUE"]["AUTORISATION"]["pourquoi"], 1, DB_PRIX["LOGISTIQUE"]["AUTORISATION"]["pu"], "U")
    total += t; table_html += r

    if u_com:
        t, r = add_html_row(DB_PRIX["LOGISTIQUE"]["TUNNEL"]["titre"], DB_PRIX["LOGISTIQUE"]["TUNNEL"]["pourquoi"], u_larg, DB_PRIX["LOGISTIQUE"]["TUNNEL"]["pu"], "ml")
        total += t; table_html += r
    if u_alarme:
        t, r = add_html_row(DB_PRIX["LOGISTIQUE"]["ALARME"]["titre"], DB_PRIX["LOGISTIQUE"]["ALARME"]["pourquoi"], 1, DB_PRIX["LOGISTIQUE"]["ALARME"]["pu"], "U")
        total += t; table_html += r

    # B. FACADE
    table_html += "<tr><td colspan='4' style='background:#f1f2f6; font-weight:bold; color:#7f8c8d; font-size:0.8em;'>2. TRAITEMENT TECHNIQUE</td></tr>"
    t, r = add_html_row(f"Nettoyage ({u_mat})", prof['desc'], s_calc, prof['nettoyage'], "m²")
    total += t; table_html += r
    
    s_pioch = int(s_calc * prof['ratio_degats'])
    if u_chiens > 0 and u_mat == "PLATRE_ANCIEN": s_pioch = int(s_calc * 0.60)
    t, r = add_html_row("Maçonnerie & Purge", f"Ratio estimé: {int(prof['ratio_degats']*100)}%", s_pioch, prof['piochage'], "m²")
    total += t; table_html += r
    
    t, r = add_html_row("Finition Système", "Application complète", s_calc, prof['finition'], "m²")
    total += t; table_html += r

    # C. FINITIONS
    table_html += "<tr><td colspan='4' style='background:#f1f2f6; font-weight:bold; color:#7f8c8d; font-size:0.8em;'>3. FINITIONS & POINTS SINGULIERS</td></tr>"
    if u_porte != "AUCUNE":
        t, r = add_html_row(DB_PRIX["BOISERIE"][u_porte]["titre"], DB_PRIX["BOISERIE"][u_porte]["pourquoi"], 1, DB_PRIX["BOISERIE"][u_porte]["pu"], "U")
        total += t; table_html += r
        
    t, r = add_html_row("Appuis Zinc", "Remplacement à neuf", nb_fen, DB_PRIX["ZINGUERIE"]["APPUI"]["pu"], "U")
    total += t; table_html += r
    
    t, r = add_html_row("Descentes EP", "Zinc/Fonte", int(h_calc), DB_PRIX["ZINGUERIE"]["DESCENTE"]["pu"], "ml")
    total += t; table_html += r
    
    t, r = add_html_row("Bandeaux Zinc", "Protection saillies", int(u_larg*2), DB_PRIX["ZINGUERIE"]["BANDEAU"]["pu"], "ml")
    total += t; table_html += r
    
    t, r = add_html_row("Garde-Corps", "Peinture antirouille", int(nb_fen*0.7), DB_PRIX["ZINGUERIE"]["GARDE_CORPS"]["pu"], "U")
    total += t; table_html += r
    
    if u_chiens > 0:
        t, r = add_html_row("Habillage Chiens-Assis", "Rénovation complète", u_chiens, DB_PRIX["ZINGUERIE"]["CHIEN_ASSIS"]["pu"], "U")
        total += t; table_html += r

    table_html += "</tbody></table>"
    
    # AFFICHER LE TABLEAU HTML
    st.markdown(table_html, unsafe_allow_html=True)
    
    # TOTAL
    st.markdown(f"""
    <div class="total-block">
        <div style="font-size:0.9em; opacity:0.8;">TOTAL ESTIMATIF HT</div>
        <div style="font-size:2.5em; font-weight:bold;">{total:,.2f} €</div>
        <div style="font-size:0.8em; margin-top:5px;">TVA non incluse (10% Rénovation / 20% Neuf)</div>
    </div>
    <div style="text-align:center; margin-top:20px; font-size:0.8em; color:#7f8c8d;">
        Estimation indicative générée par l'IA Libert & Cie. Sous réserve de visite technique.
    </div>
    """, unsafe_allow_html=True)

elif st.session_state.addr_label == "":
    st.info("👈 Entrez une adresse pour démarrer l'estimation.")