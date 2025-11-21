import streamlit as st
import time
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="Rapport Technique Libert V48", layout="wide", page_icon="📐")

# ==============================================================================
# 1. SÉCURITÉ API
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = ""

# ==============================================================================
# 2. BASE DE DONNÉES TECHNIQUE & PRIX (LIBERT 2025)
# ==============================================================================
DB_BET = {
    "LOGISTIQUE": {
        "BASE_VIE": {"titre": "Installation de Chantier", "desc": "Mise en place base vie, roulotte, raccordements provisoires et protections.", "norme": "Règl. Voirie", "pu": 4500.00, "unit": "Forfait"},
        "AUTORISATION": {"titre": "Droits de Voirie (ODP)", "desc": "Redevance d'occupation du domaine public (Provision).", "norme": "Admin", "pu": 605.00, "unit": "Forfait"},
        "ECHAFAUDAGE": {"titre": "Échafaudage Classe 4", "desc": "Structure tubulaire fixe, calcul de charge, filets pare-gravats 160g.", "norme": "NF HD 1000", "pu": 39.90, "unit": "m²"},
        "ECHAFAUDAGE_PAV": {"titre": "Échafaudage Léger", "desc": "Structure adaptée pour pavillon R+1/R+2.", "norme": "NF", "pu": 28.00, "unit": "m²"},
        "TUNNEL": {"titre": "Tunnel Piétons", "desc": "Protection étanche au-dessus des commerces/entrées.", "norme": "Sécurité", "pu": 65.00, "unit": "ml"},
        "ALARME": {"titre": "Sécurisation Électronique", "desc": "Système anti-intrusion 24/7 sur échafaudage.", "norme": "APSAD", "pu": 2070.00, "unit": "Forfait"},
        "MAJORATION_HAUTEUR": {"titre": "Sujétions IGH", "desc": "Manutention et levage au-delà de R+5.", "norme": "-", "pu": 15.00, "unit": "m²"}
    },
    "FACADES": { 
        "PLATRE_ANCIEN": {
            "titre": "Restauration Plâtre (Traditionnel)", 
            "net": {"titre": "Décapage Chimique", "desc": "Élimination des badigeons par voie chimique biodégradable.", "pu": 16.50},
            "pioch": {"titre": "Purge & Reconstitution", "desc": "Piochage des plâtres morts (Est. 50%) et réfection au plâtre gros.", "pu": 160.00},
            "fin": {"titre": "Micro-Mortier Chaux", "desc": "Finition minérale respirante type Tilia/Légacalce.", "pu": 95.00},
            "ratio": 0.50
        },
        "PIERRE_TAILLE": { 
            "titre": "Ravalement Pierre de Taille", 
            "net": {"titre": "Hydrogommage Doux", "desc": "Projection basse pression d'abrasif neutre (Archifine).", "pu": 28.00},
            "pioch": {"titre": "Ragréage Pierre", "desc": "Reconstitution des modénatures au mortier pierre.", "pu": 85.00},
            "fin": {"titre": "Minéralisation", "desc": "Application d'un hydrofuge ou lasure minérale (Keim).", "pu": 48.00},
            "ratio": 0.10
        },
        "BRIQUE": { 
            "titre": "Restauration Brique", 
            "net": {"titre": "Nettoyage Chimique", "desc": "Nettoyage adapté briques rouges/jaunes.", "pu": 35.00},
            "pioch": {"titre": "Remplacement Briques", "desc": "Changement éléments éclatés et rejointoiement.", "pu": 120.00},
            "fin": {"titre": "Hydrofuge de surface", "desc": "Protection incolore contre les infiltrations.", "pu": 25.00},
            "ratio": 0.15
        },
        "BETON": { 
            "titre": "Ravalement Technique D3", 
            "net": {"titre": "Lavage Haute Pression", "desc": "Décrassage pollution et micro-organismes.", "pu": 12.00},
            "pioch": {"titre": "Traitement des fers", "desc": "Passivation antirouille et reprise épaufrures.", "pu": 45.00},
            "fin": {"titre": "Revêtement D3 Armé", "desc": "Système souple imperméable classe I3.", "pu": 58.00},
            "ratio": 0.05
        },
        "PAVILLON_ENDUIT": { 
            "titre": "Ravalement Pavillon", 
            "net": {"titre": "Lavage Façade", "desc": "Traitement anticryptogamique et lavage.", "pu": 18.00},
            "pioch": {"titre": "Reprises Fissures", "desc": "Ouverture et pontage des fissures.", "pu": 45.00},
            "fin": {"titre": "Peinture RPE", "desc": "Revêtement Plastique Épais taloché.", "pu": 42.00},
            "ratio": 0.10
        }
    },
    "FINITIONS": {
        "APPUI": {"titre": "Appuis de Fenêtre Zinc", "desc": "Façonnage et pose bavette avec larmier.", "norme": "DTU 40.5", "pu": 215.00, "unit": "U"},
        "DESCENTE": {"titre": "Descentes EP", "desc": "Remplacement Zinc/Fonte avec dauphin.", "norme": "DTU 60.11", "pu": 165.00, "unit": "ml"},
        "GARDE_CORPS": {"titre": "Peinture Ferronneries", "desc": "Grattage, antirouille et laque de finition.", "norme": "DTU 59.1", "pu": 160.00, "unit": "U"},
        "BANDEAU": {"titre": "Bandeaux Zinc", "desc": "Protection des corniches saillantes.", "norme": "DTU 40.5", "pu": 178.00, "unit": "ml"},
        "CHIEN_ASSIS": {"titre": "Habillage Lucarne", "desc": "Rénovation complète zinc et jouées.", "norme": "-", "pu": 950.00, "unit": "U"},
        "PORTE_COCHERE": {"titre": "Restauration Porte Cochère", "desc": "Décapage, greffes bois et lasure/peinture.", "norme": "-", "pu": 3200.00, "unit": "U"},
        "PORTE_ENTREE": {"titre": "Peinture Porte Hall", "desc": "Préparation et peinture glycérophtalique.", "norme": "-", "pu": 850.00, "unit": "U"},
        "DEBORD_TOIT": {"titre": "Lasure Débords de Toit", "desc": "Protection des planches de rive.", "norme": "-", "pu": 45.00, "unit": "ml"}
    }
}

# ==============================================================================
# 3. MOTEUR TECHNIQUE
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

def get_street_view(lat, lon, heading, pitch):
    if GOOGLE_API_KEY and len(GOOGLE_API_KEY) > 10:
        return f"https://maps.googleapis.com/maps/api/streetview?size=640x400&location={lat},{lon}&fov=80&heading={heading}&pitch={pitch}&key={GOOGLE_API_KEY}"
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Immeuble_parisien.jpg/800px-Immeuble_parisien.jpg"

# ==============================================================================
# 4. INTERFACE
# ==============================================================================

# --- ETAT ---
if 'step' not in st.session_state: st.session_state.step = 0
if 'real_data' not in st.session_state: st.session_state.real_data = {}
if 'addr_label' not in st.session_state: st.session_state.addr_label = ""
if 'gps' not in st.session_state: st.session_state.gps = (0,0)
if 'cam_h' not in st.session_state: st.session_state.cam_h = 0
if 'cam_p' not in st.session_state: st.session_state.cam_p = 10

# --- CSS POUR RAPPORT PAPIER ---
st.markdown("""
<style>
    .report-container { background: white; padding: 40px; border: 1px solid #ddd; box-shadow: 0 0 15px rgba(0,0,0,0.1); max-width: 1000px; margin: auto; }
    .report-header { display: flex; justify-content: space-between; border-bottom: 2px solid #2c3e50; padding-bottom: 20px; margin-bottom: 20px; }
    .report-title { color: #2c3e50; font-size: 24px; font-weight: bold; }
    .report-meta { text-align: right; font-size: 12px; color: #666; }
    .section-header { background: #f4f6f7; padding: 8px 15px; font-weight: bold; color: #2c3e50; border-left: 5px solid #e67e22; margin-top: 20px; font-size: 14px; }
    .line-item { display: flex; justify-content: space-between; padding: 8px 15px; border-bottom: 1px solid #eee; font-size: 13px; }
    .line-desc { flex: 3; }
    .line-qty { flex: 1; text-align: center; }
    .line-price { flex: 1; text-align: right; font-weight: bold; }
    .total-block { background: #2c3e50; color: white; padding: 15px; text-align: right; font-size: 18px; font-weight: bold; margin-top: 30px; }
    .tech-detail { font-size: 11px; color: #666; font-style: italic; display: block; }
    @media print { .stSidebar, .stButton { display: none; } }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR (CONTROLES) ---
with st.sidebar:
    st.header("🎛️ Paramétrage")
    
    st.subheader("📷 Vue Façade")
    c1, c2, c3 = st.columns(3)
    def rot(a): st.session_state.cam_h = (st.session_state.cam_h + a) % 360
    if c1.button("⬅️"): rot(-45)
    if c2.button("🔄"): rot(180)
    if c3.button("➡️"): rot(45)
    st.session_state.cam_p = st.slider("Inclinaison", -10, 60, st.session_state.cam_p)
    
    st.divider()
    st.subheader("🏗️ Données Bâtiment")
    params_container = st.container()

# --- MAIN ---
if st.session_state.step == 0:
    st.title("📐 Estimateur Technique V48")
    c1, c2 = st.columns([3, 1])
    q = c1.text_input("Adresse du projet :", placeholder="Ex: 159 rue du faubourg saint antoine...")
    
    if q and len(q)>4:
        opts = get_adresses_api(q)
        final_addr = c1.selectbox("📍 Validation :", opts, label_visibility="collapsed")
    else: final_addr = None

    if c2.button("GÉNÉRER RAPPORT", type="primary"):
        if final_addr:
            with st.spinner("Analyse Bâtimentaire..."):
                lat, lon = get_geo_data(final_addr)
                if lat:
                    st.session_state.gps = (lat, lon)
                    st.session_state.real_data = query_osm_real_data(lat, lon)
                    st.session_state.addr_label = final_addr
                    st.session_state.cam_h = 0
                    st.session_state.step = 1
                    st.rerun()
                else:
                    st.error("Adresse introuvable.")

# --- RAPPORT ---
if st.session_state.step == 1:
    rd = st.session_state.real_data
    
    # 1. REGLAGES (Sidebar)
    with params_container:
        ads = st.session_state.addr_label.lower()
        def_idx = 1 
        if "sebastien" in ads or "faubourg" in ads: def_idx = 0
        elif "general" in ads: def_idx = 3
        
        u_mat = st.selectbox("Nature Support", list(DB_PRIX["FACADES"].keys()), index=def_idx)
        
        # Immeuble ou Pavillon ?
        u_type = st.radio("Type", ["IMMEUBLE", "PAVILLON"], horizontal=True, index=0)
        
        val_niv = rd['niveaux'] if rd['niveaux'] > 0 else 5
        u_niv = st.number_input("Niveaux (R+)", value=val_niv, min_value=1)
        u_larg = st.number_input("Largeur (m)", value=15, min_value=5)
        
        st.markdown("---")
        st.caption("Options :")
        u_com = st.checkbox("Commerce RDC", value=rd['commerce'])
        u_alarme = st.checkbox("Alarme", value=True)
        has_toit = True if rd['toit'] > 0 else False
        u_chiens = st.number_input("Chiens-assis", value=(2 if has_toit else 0))
        u_porte = st.selectbox("Porte", ["PORTE_COCHERE", "PORTE_ENTREE", "AUCUNE"])

    # 2. CALCULS
    h_calc = u_niv * 3.0
    s_calc = int(h_calc * u_larg)
    if u_type == "PAVILLON": s_calc = int((u_larg * 4) * h_calc)
    nb_fen = int(s_calc / 12)

    # 3. DOCUMENT TYPE "BET" (HTML PUR)
    st.markdown(f"""
    <div class="report-container">
        <div class="report-header">
            <div>
                <div class="report-title">RAPPORT D'ESTIMATION</div>
                <div>LIBERT & CIE - Département Façades</div>
            </div>
            <div class="report-meta">
                Date : {time.strftime("%d/%m/%Y")}<br>
                Ref : {int(time.time())}<br>
                {st.session_state.addr_label}
            </div>
        </div>
    """, unsafe_allow_html=True)

    # PHOTO
    lat, lon = st.session_state.gps
    img = get_street_view(lat, lon, st.session_state.cam_h, st.session_state.cam_p)
    st.image(img, use_column_width=True)
    
    # INFOS BÂTIMENT
    st.info(f"📍 **Caractéristiques :** {u_type} | Hauteur {h_calc}m (R+{u_niv-1}) | Surface {s_calc} m² | Support : {DB_PRIX['FACADES'][u_mat]['titre']}")

    # DEVIS
    total = 0
    
    def html_line(titre, desc, norme, qte, unit, pu):
        tot = qte * pu
        return tot, f"""
        <div class="line-item">
            <div class="line-desc">
                <b>{titre}</b> <span style="color:#e67e22;">[{norme}]</span>
                <span class="tech-detail">{desc}</span>
            </div>
            <div class="line-qty">{int(qte)} {unit}</div>
            <div class="line-price">{tot:,.2f} €</div>
        </div>
        """

    # SECTION 1
    st.markdown('<div class="section-header">1. INSTALLATION DE CHANTIER & SÉCURITÉ</div>', unsafe_allow_html=True)
    if u_type == "PAVILLON":
        t, h = html_line(DB_PRIX["LOGISTIQUE"]["ECHAFAUDAGE_PAV"]["titre"], DB_PRIX["LOGISTIQUE"]["ECHAFAUDAGE_PAV"]["desc"], DB_PRIX["LOGISTIQUE"]["ECHAFAUDAGE_PAV"]["norme"], s_calc, "m²", DB_PRIX["LOGISTIQUE"]["ECHAFAUDAGE_PAV"]["pu"])
        total += t; st.markdown(h, unsafe_allow_html=True)
    else:
        for k in ["BASE_VIE", "AUTORISATION", "ECHAFAUDAGE"]:
            item = DB_PRIX["LOGISTIQUE"][k]
            q = s_calc if k == "ECHAFAUDAGE" else 1
            unit = "m²" if k == "ECHAFAUDAGE" else "Fft"
            t, h = html_line(item["titre"], item["desc"], item["norme"], q, unit, item["pu"])
            total += t; st.markdown(h, unsafe_allow_html=True)
        
        if u_com:
            i = DB_PRIX["LOGISTIQUE"]["TUNNEL"]
            t, h = html_line(i["titre"], i["desc"], i["norme"], u_larg, "ml", i["pu"])
            total += t; st.markdown(h, unsafe_allow_html=True)
        if u_alarme:
            i = DB_PRIX["LOGISTIQUE"]["ALARME"]
            t, h = html_line(i["titre"], i["desc"], i["norme"], 1, "Fft", i["pu"])
            total += t; st.markdown(h, unsafe_allow_html=True)
        if u_niv > 6:
            i = DB_PRIX["LOGISTIQUE"]["MAJORATION_HAUTEUR"]
            t, h = html_line(i["titre"], i["desc"], i["norme"], s_calc, "m²", i["pu"])
            total += t; st.markdown(h, unsafe_allow_html=True)

    # SECTION 2
    st.markdown('<div class="section-header">2. TRAITEMENT DES FAÇADES</div>', unsafe_allow_html=True)
    prof = DB_PRIX["FACADES"][u_mat]
    
    t, h = html_line(prof["net"]["titre"], prof["net"]["desc"], "DTU 59.1", s_calc, "m²", prof["net"]["pu"])
    total += t; st.markdown(h, unsafe_allow_html=True)
    
    s_pioch = int(s_calc * prof["ratio_degats"])
    if u_chiens > 0 and u_mat == "PLATRE_ANCIEN": s_pioch = int(s_calc * 0.60)
    t, h = html_line(prof["pioch"]["titre"], prof["pioch"]["desc"], "DTU 26.1", s_pioch, "m²", prof["pioch"]["pu"])
    total += t; st.markdown(h, unsafe_allow_html=True)
    
    t, h = html_line(prof["fin"]["titre"], prof["fin"]["desc"], "NF T 36-005", s_calc, "m²", prof["fin"]["pu"])
    total += t; st.markdown(h, unsafe_allow_html=True)

    # SECTION 3
    st.markdown('<div class="section-header">3. FINITIONS & POINTS SINGULIERS</div>', unsafe_allow_html=True)
    if u_porte != "AUCUNE":
        i = DB_PRIX["BOISERIE"][u_porte]
        t, h = html_line(i["titre"], i["desc"], "-", 1, "U", i["pu"])
        total += t; st.markdown(h, unsafe_allow_html=True)
        
    i = DB_PRIX["ZINGUERIE"]["APPUI"]
    t, h = html_line(i["titre"], i["desc"], "DTU 40.5", nb_fen, "U", i["pu"])
    total += t; st.markdown(h, unsafe_allow_html=True)
    
    i = DB_PRIX["ZINGUERIE"]["DESCENTE"]
    t, h = html_line(i["titre"], i["desc"], "DTU 60.11", int(h_calc), "ml", i["pu"])
    total += t; st.markdown(h, unsafe_allow_html=True)
    
    if u_type == "IMMEUBLE":
        i = DB_PRIX["ZINGUERIE"]["BANDEAU"]
        t, h = html_line(i["titre"], i["desc"], "DTU 40.5", int(u_larg*2), "ml", i["pu"])
        total += t; st.markdown(h, unsafe_allow_html=True)
        i = DB_PRIX["ZINGUERIE"]["GARDE_CORPS"]
        t, h = html_line(i["titre"], i["desc"], "DTU 59.1", int(nb_fen*0.7), "U", i["pu"])
        total += t; st.markdown(h, unsafe_allow_html=True)
        
    if u_chiens > 0:
        i = DB_PRIX["ZINGUERIE"]["CHIEN_ASSIS"]
        t, h = html_line(i["titre"], i["desc"], "-", u_chiens, "U", i["pu"])
        total += t; st.markdown(h, unsafe_allow_html=True)

    # TOTAL
    st.markdown(f"""
    <div class="total-block">
        TOTAL ESTIMATIF HT : {total:,.2f} €
    </div>
    <div style="text-align:center; margin-top:20px; font-size:11px; color:#999;">
        Ce document est une estimation budgétaire générée automatiquement. Il ne remplace pas un devis contradictoire établi après visite technique sur site.
    </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    if st.button("🔄 Nouvelle Estimation"):
        st.session_state.step = 0
        st.rerun()