import streamlit as st
import time
import requests
import base64
from io import BytesIO
from xhtml2pdf import pisa # La librairie magique pour le PDF

# --- CONFIGURATION ---
st.set_page_config(page_title="Estimateur Libert V38 (PDF)", layout="wide", page_icon="📄")

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
        "ECHAFAUDAGE": {"titre": "Échafaudage Tubulaire", "pourquoi": "Classe 4 + filets.", "pu": 39.90, "unit": "m²"},
        "ECHAFAUDAGE_PAV": {"titre": "Échafaudage Léger", "pourquoi": "Structure adaptée.", "pu": 28.00, "unit": "m²"},
        "TUNNEL": {"titre": "Tunnel Public", "pourquoi": "Sécurité piétons.", "pu": 60.00, "unit": "ml"},
        "ALARME": {"titre": "Alarme Échafaudage", "pourquoi": "Système anti-intrusion.", "pu": 2070.00, "unit": "Forfait"},
        "MAJORATION_HAUTEUR": {"titre": "Majoration Grande Hauteur", "pourquoi": "Manutention > R+5.", "pu": 15.00, "unit": "m²"}
    },
    "FACADES": { 
        "PLATRE_ANCIEN": {"titre": "Restauration Plâtre", "nettoyage": 16.50, "piochage": 160.00, "finition": 95.00, "ratio_degats": 0.50, "desc": "Décapage + Purge lourde + Micro-mortier"},
        "PIERRE_TAILLE": {"titre": "Ravalement Pierre", "nettoyage": 28.00, "piochage": 85.00, "finition": 48.00, "ratio_degats": 0.10, "desc": "Hydrogommage + Ragréage + Minéralisation"},
        "BRIQUE": {"titre": "Restauration Brique", "nettoyage": 35.00, "piochage": 120.00, "finition": 25.00, "ratio_degats": 0.15, "desc": "Nettoyage chimique + Hydrofuge"},
        "BETON": {"titre": "Ravalement D3", "nettoyage": 12.00, "piochage": 45.00, "finition": 58.00, "ratio_degats": 0.05, "desc": "Lavage HP + Passivation + RPE Armé"},
        "PAVILLON_ENDUIT": {"titre": "Ravalement Pavillon", "nettoyage": 18.00, "piochage": 45.00, "finition": 42.00, "ratio_degats": 0.10, "desc": "Lavage + Reprise fissures + RPE"}
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
        "PORTE_ENTREE": {"titre": "Peinture Porte Hall", "pourquoi": "Laque tendue.", "pu": 850.00, "unit": "U"},
        "DEBORD_TOIT": {"titre": "Lasure Débords de Toit", "pourquoi": "Protection bois.", "pu": 45.00, "unit": "ml"}
    }
}

# ==============================================================================
# 3. MOTEUR DE GÉNÉRATION PDF (NOUVEAU)
# ==============================================================================

def get_image_base64(path):
    """Convertit le logo en base64 pour le PDF"""
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    except:
        return None

def create_pdf(data_devis, total_ht, logo_path="LOGO LIBERT new2.png"):
    """Génère le PDF binaire à partir des données"""
    
    # 1. Préparation du Logo
    logo_b64 = get_image_base64(logo_path)
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" width="150">' if logo_b64 else "<h2>LIBERT & CIE</h2>"
    
    # 2. Construction des lignes du tableau HTML
    # On utilise des tableaux HTML classiques car xhtml2pdf ne gère pas bien le Flexbox
    rows = ""
    
    # --- LOGISTIQUE ---
    rows += """<tr style="background-color:#f0f0f0;"><td colspan="5"><b>1. INSTALLATION & SÉCURITÉ</b></td></tr>"""
    for item in data_devis['logistique']:
        rows += f"""
        <tr>
            <td><b>{item['titre']}</b><br/><span style="font-size:10px; color:#666;">{item['desc']}</span></td>
            <td align="center">{int(item['qte'])}</td>
            <td align="center">{item['unit']}</td>
            <td align="right">{item['pu']:,.2f} €</td>
            <td align="right"><b>{item['total']:,.2f} €</b></td>
        </tr>"""
        
    # --- FAÇADE ---
    rows += """<tr style="background-color:#f0f0f0;"><td colspan="5"><b>2. TRAITEMENT DES FAÇADES</b></td></tr>"""
    for item in data_devis['facade']:
        rows += f"""
        <tr>
            <td><b>{item['titre']}</b><br/><span style="font-size:10px; color:#666;">{item['desc']}</span></td>
            <td align="center">{int(item['qte'])}</td>
            <td align="center">{item['unit']}</td>
            <td align="right">{item['pu']:,.2f} €</td>
            <td align="right"><b>{item['total']:,.2f} €</b></td>
        </tr>"""

    # --- FINITIONS ---
    rows += """<tr style="background-color:#f0f0f0;"><td colspan="5"><b>3. FINITIONS & POINTS SINGULIERS</b></td></tr>"""
    for item in data_devis['finitions']:
        rows += f"""
        <tr>
            <td><b>{item['titre']}</b><br/><span style="font-size:10px; color:#666;">{item['desc']}</span></td>
            <td align="center">{int(item['qte'])}</td>
            <td align="center">{item['unit']}</td>
            <td align="right">{item['pu']:,.2f} €</td>
            <td align="right"><b>{item['total']:,.2f} €</b></td>
        </tr>"""

    # 3. Template HTML complet (Style Facture)
    html_template = f"""
    <html>
    <head>
        <style>
            @page {{ size: A4; margin: 2cm; }}
            body {{ font-family: Helvetica, sans-serif; font-size: 12px; color: #333; }}
            .header-table {{ width: 100%; margin-bottom: 30px; }}
            .info-box {{ background-color: #f9f9f9; padding: 10px; border: 1px solid #ddd; }}
            .main-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .main-table th {{ background-color: #2c3e50; color: white; padding: 8px; text-align: left; }}
            .main-table td {{ padding: 8px; border-bottom: 1px solid #eee; }}
            .total-section {{ margin-top: 20px; text-align: right; }}
            .footer {{ position: fixed; bottom: 0; width: 100%; text-align: center; font-size: 10px; color: #777; }}
        </style>
    </head>
    <body>
        <table class="header-table">
            <tr>
                <td width="50%">{logo_html}</td>
                <td width="50%" align="right">
                    <h1>ESTIMATION</h1>
                    <p>Date : {time.strftime("%d/%m/%Y")}</p>
                </td>
            </tr>
        </table>

        <table class="header-table">
            <tr>
                <td width="50%">
                    <div class="info-box">
                        <b>CHANTIER :</b><br/>
                        {data_devis['adresse']}<br/>
                        {data_devis['cp']}
                    </div>
                </td>
                <td width="50%">
                    <div class="info-box">
                        <b>CARACTÉRISTIQUES :</b><br/>
                        Type : {data_devis['type']}<br/>
                        Hauteur : R+{data_devis['etages']-1}<br/>
                        Surface : {data_devis['surface']} m²
                    </div>
                </td>
            </tr>
        </table>

        <table class="main-table">
            <thead>
                <tr>
                    <th width="40%">Désignation</th>
                    <th width="10%" align="center">Qté</th>
                    <th width="10%" align="center">U</th>
                    <th width="15%" align="right">P.U. HT</th>
                    <th width="25%" align="right">Total HT</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>

        <div class="total-section">
            <h2>TOTAL HT : {total_ht:,.2f} €</h2>
            <p>TVA non incluse (10% Rénovation / 20% Neuf)</p>
        </div>

        <div class="footer">
            Ce document est une estimation indicative générée par IA. Il ne constitue pas une offre contractuelle.<br/>
            Une visite technique est obligatoire pour valider les métrés et l'état des supports.
        </div>
    </body>
    </html>
    """
    
    # 4. Conversion HTML -> PDF
    pdf_file = BytesIO()
    pisa_status = pisa.CreatePDF(html_template, dest=pdf_file)
    
    if pisa_status.err:
        return None
    return pdf_file.getvalue()

# ==============================================================================
# 4. FONCTIONS TECHNIQUES
# ==============================================================================
def get_adresses_api(query):
    if not query or len(query) < 3: return []
    try:
        r = requests.get(f"https://api-adresse.data.gouv.fr/search/?q={query}&limit=5")
        if r.status_code == 200:
            # On stocke l'objet complet pour avoir le CP et la Ville
            return r.json()['features']
    except: return []
    return []

def get_facade_image(adresse, heading=0, pitch=20):
    if GOOGLE_API_KEY and len(GOOGLE_API_KEY) > 10:
        base = "https://maps.googleapis.com/maps/api/streetview"
        return f"{base}?size=640x640&location={adresse}&fov=110&heading={heading}&pitch={pitch}&key={GOOGLE_API_KEY}"
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Immeuble_parisien.jpg/800px-Immeuble_parisien.jpg"

def ia_init(adresse):
    ads = adresse.lower()
    if "allee" in ads or "chemin" in ads or "villa" in ads:
        return "PAVILLON", "PAVILLON_ENDUIT", 2, 10
    
    if "sebastien" in ads or "faubourg" in ads: return "IMMEUBLE", "PLATRE_ANCIEN", 4, 14
    if "pascal" in ads: return "IMMEUBLE", "BRIQUE", 6, 18
    if "general" in ads: return "IMMEUBLE", "BETON", 7, 20
    return "IMMEUBLE", "PIERRE_TAILLE", 6, 16

# ==============================================================================
# 5. INTERFACE UTILISATEUR
# ==============================================================================

# SESSION STATE
if 'addr_label' not in st.session_state: st.session_state.addr_label = ""
if 'addr_cp' not in st.session_state: st.session_state.addr_cp = "" # Pour le PDF
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
st.title("🏢 Estimateur Libert V38 (PDF)")

c_search, c_go = st.columns([3, 1])
with c_search:
    query = st.text_input("Adresse :", placeholder="Tapez une adresse...")
    features = get_adresses_api(query)
    
    if features:
        # On crée un dict pour mapper Label -> Feature
        options = {f['properties']['label']: f for f in features}
        selected_label = st.selectbox("📍 Suggestions :", options.keys(), label_visibility="collapsed")
        
        if selected_label and selected_label != st.session_state.addr_label:
            st.session_state.addr_label = selected_label
            # On extrait le CP et la Ville
            props = options[selected_label]['properties']
            st.session_state.addr_cp = f"{props.get('postcode', '')} {props.get('city', '')}"
            
            # Init IA
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
        st.caption(st.session_state.addr_cp)
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Surface", f"{s_calc} m²")
        k2.metric("Hauteur", f"{h_calc} m")
        k3.metric("Type", DB_PRIX["FACADES"][u_mat]["titre"])

    # 3. CALCUL DEVIS & PRÉPARATION PDF
    total = 0
    data_pdf = {
        "adresse": st.session_state.addr_label,
        "cp": st.session_state.addr_cp,
        "type": u_type, "etages": u_niv, "surface": s_calc,
        "tech": {"profil": u_mat},
        "metres": {"surface": s_calc, "fenetres": nb_fen},
        "logistique": [], "facade": [], "finitions": []
    }
    
    def add_line(cat, key, qte, unit=None):
        if key not in DB_PRIX[cat]: return 0
        item = DB_PRIX[cat][key]
        u = unit if unit else item['unit']
        tot = qte * item['pu']
        
        # Ajout pour affichage écran
        # (Code affichage écran simplifié ici pour la clarté, on focus sur la data PDF)
        
        # Ajout pour PDF
        line_data = {"titre": item['titre'], "desc": item['pourquoi'], "qte": qte, "unit": u, "pu": item['pu'], "total": tot}
        if cat == "LOGISTIQUE": data_pdf['logistique'].append(line_data)
        elif cat == "FACADES": data_pdf['facade'].append(line_data)
        else: data_pdf['finitions'].append(line_data)
        
        return tot

    # LOGISTIQUE
    if u_type == "PAVILLON": total += add_line("LOGISTIQUE", "ECHAFAUDAGE_PAV", s_calc)
    else:
        total += add_line("LOGISTIQUE", "BASE_VIE", 1)
        total += add_line("LOGISTIQUE", "AUTORISATION", 1)
        total += add_line("LOGISTIQUE", "ECHAFAUDAGE", s_calc)
        if u_com: total += add_line("LOGISTIQUE", "TUNNEL", u_larg)
        if u_alarme: total += add_line("LOGISTIQUE", "ALARME", 1)
        if u_niv > 6: total += add_line("LOGISTIQUE", "MAJORATION_HAUTEUR", s_calc)

    # FAÇADE
    prof = DB_PRIX["FACADES"][u_mat]
    total += add_line("FACADES", "NETTOYAGE", s_calc) # Nettoyage est DANS Facades
    
    # Correction : Il faut appeler les sous-clés spécifiques du profil dans le PDF
    # Pour simplifier le PDF generator, on ajoute manuellement les lignes FACADE qui sont dynamiques
    p_net = s_calc * prof['nettoyage']
    data_pdf['facade'].append({"titre": f"Nettoyage ({u_mat})", "desc": prof['desc'], "qte": s_calc, "unit": "m²", "pu": prof['nettoyage'], "total": p_net})
    total += p_net
    
    s_pioch = int(s_calc * prof['ratio_degats'])
    if u_chiens > 0 and u_mat == "PLATRE_ANCIEN": s_pioch = int(s_calc * 0.60)
    p_pioch = s_pioch * prof['piochage']
    data_pdf['facade'].append({"titre": "Maçonnerie (Purge)", "desc": f"Ratio dégâts: {int(prof['ratio_degats']*100)}%", "qte": s_pioch, "unit": "m²", "pu": prof['piochage'], "total": p_pioch})
    total += p_pioch
    
    p_fin = s_calc * prof['finition']
    data_pdf['facade'].append({"titre": "Finition Système", "desc": prof['desc'], "qte": s_calc, "unit": "m²", "pu": prof['finition'], "total": p_fin})
    total += p_fin

    # FINITIONS
    if u_porte != "AUCUNE": total += add_line("BOISERIE", u_porte, 1)
    if u_type == "PAVILLON": total += add_line("BOISERIE", "DEBORD_TOIT", int(u_larg*4))
    
    total += add_line("ZINGUERIE", "APPUI", nb_fen)
    total += add_line("ZINGUERIE", "DESCENTE", int(h_calc))
    if u_type == "IMMEUBLE": total += add_line("ZINGUERIE", "BANDEAU", int(u_larg*2))
    total += add_line("ZINGUERIE", "GARDE_CORPS", int(nb_fen*0.7))
    if u_chiens > 0: total += add_line("ZINGUERIE", "CHIEN_ASSIS", u_chiens)

    # --- AFFICHAGE TOTAL & BOUTON PDF ---
    st.markdown("---")
    c_t, c_pdf = st.columns([2, 1])
    
    with c_t:
        st.markdown(f"### Total Estimatif HT : {total:,.2f} €")
        st.caption("Consultez le PDF pour le détail ligne par ligne.")
        
    with c_pdf:
        # GÉNÉRATION PDF
        pdf_bytes = create_pdf(data_pdf, total)
        if pdf_bytes:
            st.download_button(
                label="📥 TÉLÉCHARGER LE DEVIS (PDF)",
                data=pdf_bytes,
                file_name="Devis_Libert_Estimation.pdf",
                mime="application/pdf",
                type="primary"
            )
        else:
            st.warning("Erreur génération PDF (Vérifiez le logo).")

elif st.session_state.addr_label == "":
    st.info("👈 Entrez une adresse pour commencer.")