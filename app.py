import streamlit as st
import time
import requests
import base64

# --- CONFIGURATION ---
st.set_page_config(page_title="Estimateur Libert V37 (Pro)", layout="wide", page_icon="🏢")

# ==============================================================================
# 1. GESTION DES FICHIERS (LOGO & EXPORT)
# ==============================================================================

def get_base64_image(image_path):
    """Convertit l'image du logo en texte pour l'intégrer au rapport HTML"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None

def generer_html_a4(data, prix_db, total_ht, logo_b64):
    """Génère une page HTML format A4 prête à imprimer/PDF"""
    
    # Date du jour
    date_jour = time.strftime("%d/%m/%Y")
    
    # Construction des lignes du tableau
    rows_html = ""
    profil_data = prix_db["FACADES"][data['tech']['profil']]
    
    # Fonction interne pour ajouter une ligne au tableau HTML
    def html_row(titre, detail, qte, unit, pu, total):
        return f"""
        <tr style="border-bottom: 1px solid #eee;">
            <td style="padding: 8px; font-weight:bold; color:#333;">{titre}<br><span style="font-weight:normal; font-size:0.8em; color:#666;">{detail}</span></td>
            <td style="padding: 8px; text-align:center;">{int(qte) if unit!='m²' else int(qte)}</td>
            <td style="padding: 8px; text-align:center;">{unit}</td>
            <td style="padding: 8px; text-align:right;">{pu:,.2f} €</td>
            <td style="padding: 8px; text-align:right; font-weight:bold;">{total:,.2f} €</td>
        </tr>
        """

    # 1. Logistique
    rows_html += f"<tr><td colspan='5' style='background:#f4f4f4; padding:5px; font-weight:bold; font-size:0.9em;'>1. INSTALLATION & SÉCURITÉ</td></tr>"
    rows_html += html_row("Installation de Chantier", "Base vie, Roulotte, WC", 1, "Forfait", prix_db["LOGISTIQUE"]["BASE_VIE"]["pu"], prix_db["LOGISTIQUE"]["BASE_VIE"]["pu"])
    
    echaf = prix_db["LOGISTIQUE"]["ECHAFAUDAGE_PAV"] if data['type'] == "PAVILLON" else prix_db["LOGISTIQUE"]["ECHAFAUDAGE"]
    s_surf = data['metres']['surface']
    rows_html += html_row(echaf["titre"], echaf["pourquoi"], s_surf, "m²", echaf["pu"], s_surf * echaf["pu"])
    
    # 2. Façade
    rows_html += f"<tr><td colspan='5' style='background:#f4f4f4; padding:5px; font-weight:bold; font-size:0.9em; border-top:1px solid #ccc;'>2. TRAITEMENT DES SURFACES</td></tr>"
    rows_html += html_row(f"Nettoyage ({data['tech']['profil']})", profil_data["desc"], s_surf, "m²", profil_data["nettoyage"], s_surf * profil_data["nettoyage"])
    
    s_pioch = int(s_surf * profil_data["ratio_degats"])
    rows_html += html_row("Soin des Maçonneries", "Purge et reconstitution", s_pioch, "m²", profil_data["piochage"], s_pioch * profil_data["piochage"])
    rows_html += html_row("Finition Système", "Application revêtement", s_surf, "m²", profil_data["finition"], s_surf * profil_data["finition"])

    # 3. Finitions
    rows_html += f"<tr><td colspan='5' style='background:#f4f4f4; padding:5px; font-weight:bold; font-size:0.9em; border-top:1px solid #ccc;'>3. POINTS SINGULIERS</td></tr>"
    rows_html += html_row("Appuis de Fenêtre", "Zinc", data['metres']['fenetres'], "U", prix_db["ZINGUERIE"]["APPUI"]["pu"], data['metres']['fenetres'] * prix_db["ZINGUERIE"]["APPUI"]["pu"])
    
    # Gestion logo
    img_tag = f'<img src="data:image/png;base64,{logo_b64}" style="max-height:80px;">' if logo_b64 else "<h2>LIBERT & CIE</h2>"

    # CSS & HTML COMPLET
    return f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Helvetica', sans-serif; color: #333; font-size: 12px; }}
            .container {{ width: 100%; max-width: 800px; margin: 0 auto; }}
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; border-bottom: 2px solid #e67e22; padding-bottom: 10px; }}
            .client-info {{ background: #f9f9f9; padding: 15px; border-radius: 5px; margin-bottom: 20px; display: flex; justify-content: space-between; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th {{ background: #2c3e50; color: white; padding: 8px; text-align: left; font-size: 0.9em; }}
            .total-box {{ float: right; width: 250px; background: #2c3e50; color: white; padding: 15px; text-align: right; border-radius: 5px; }}
            .footer {{ clear: both; margin-top: 50px; border-top: 1px solid #ccc; padding-top: 10px; text-align: center; font-size: 0.8em; color: #777; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div>{img_tag}</div>
                <div style="text-align:right;">
                    <h1 style="margin:0; color:#2c3e50;">ESTIMATION DE TRAVAUX</h1>
                    <div style="font-size:1.1em; color:#e67e22;">Réf: DEV-{int(time.time())}</div>
                    <div>Date : {date_jour}</div>
                </div>
            </div>

            <div class="client-info">
                <div>
                    <b>ADRESSE DU CHANTIER :</b><br>
                    {data['adresse']}<br>
                    <span style="color:#666;">Paris / Île-de-France</span>
                </div>
                <div style="text-align:right;">
                    <b>CARACTÉRISTIQUES :</b><br>
                    Type : {data['type']}<br>
                    Hauteur : {data['geo']['etages']} Niveaux<br>
                    Surface : {s_surf} m²
                </div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th width="45%">Désignation</th>
                        <th width="10%" style="text-align:center;">Qté</th>
                        <th width="10%" style="text-align:center;">U</th>
                        <th width="15%" style="text-align:right;">P.U. HT</th>
                        <th width="20%" style="text-align:right;">Total HT</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>

            <div class="total-box">
                <div style="font-size:0.9em;">TOTAL NET HT</div>
                <div style="font-size:1.8em; font-weight:bold;">{total_ht:,.2f} €</div>
                <div style="font-size:0.8em; margin-top:5px; opacity:0.8;">TVA non incluse (10% ou 20%)</div>
            </div>

            <div class="footer">
                LIBERT & CIE - Expert Façade & Rénovation<br>
                Document estimatif non contractuel. Sous réserve de visite technique.
            </div>
        </div>
    </body>
    </html>
    """

# ==============================================================================
# 2. CONFIG API & DONNÉES
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = ""

DB_PRIX = {
    "LOGISTIQUE": {
        "BASE_VIE": {"titre": "Installation & Base Vie", "pourquoi": "Roulotte, WC, Cantonnement.", "pu": 4500.00, "unit": "Forfait"},
        "AUTORISATION": {"titre": "Taxes de Voirie (ODP)", "pourquoi": "Redevance municipale.", "pu": 605.00, "unit": "Forfait"},
        "ECHAFAUDAGE": {"titre": "Échafaudage Tubulaire", "pourquoi": "Classe 4 + filets.", "pu": 39.90, "unit": "m²"},
        "ECHAFAUDAGE_PAV": {"titre": "Échafaudage Léger", "pourquoi": "Adapté pavillon.", "pu": 28.00, "unit": "m²"},
        "TUNNEL": {"titre": "Tunnel Public", "pourquoi": "Sécurité piétons.", "pu": 60.00, "unit": "ml"}
    },
    "FACADES": { 
        "PLATRE_ANCIEN": {"titre": "Restauration Plâtre", "nettoyage": 16.50, "piochage": 150.00, "finition": 95.00, "ratio_degats": 0.50, "desc": "Décapage + Purge lourde + Micro-mortier"},
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
        "PORTE_ENTREE": {"titre": "Peinture Porte Hall", "pourquoi": "Laque tendue.", "pu": 850.00, "unit": "U"}
    }
}

# ==============================================================================
# 3. FONCTIONS MÉTIER
# ==============================================================================
def get_adresses_api(query):
    if not query or len(query) < 3: return []
    try:
        r = requests.get(f"https://api-adresse.data.gouv.fr/search/?q={query}&limit=5")
        return [f['properties']['label'] for f in r.json()['features']] if r.status_code == 200 else []
    except: return []

def get_street_view(adresse, heading, pitch):
    if GOOGLE_API_KEY:
        return f"https://maps.googleapis.com/maps/api/streetview?size=640x480&location={adresse}&fov=110&heading={heading}&pitch={pitch}&key={GOOGLE_API_KEY}"
    return "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Immeuble_parisien.jpg/800px-Immeuble_parisien.jpg"

def analyse_ia(adresse):
    ads = adresse.lower()
    # Logique Type
    if "allee" in ads or "chemin" in ads or "villa" in ads:
        return {"type": "PAVILLON", "profil": "PAVILLON_ENDUIT", "etages": 2, "largeur": 10}
    
    # Logique Immeuble
    type_b = "IMMEUBLE"
    if "sebastien" in ads or "faubourg" in ads: return {"type": type_b, "profil": "PLATRE_ANCIEN", "etages": 4, "largeur": 14}
    if "pascal" in ads: return {"type": type_b, "profil": "BRIQUE", "etages": 6, "largeur": 18}
    if "general" in ads: return {"type": type_b, "profil": "BETON", "etages": 7, "largeur": 22}
    return {"type": type_b, "profil": "PIERRE_TAILLE", "etages": 6, "largeur": 16}

# ==============================================================================
# 4. INTERFACE
# ==============================================================================

# Gestion Session
if 'addr' not in st.session_state: st.session_state.addr = ""
if 'data' not in st.session_state: st.session_state.data = None
if 'cam_h' not in st.session_state: st.session_state.cam_h = 0
if 'cam_p' not in st.session_state: st.session_state.cam_p = 10

# --- BARRE LATÉRALE ---
with st.sidebar:
    st.header("🎛️ Ajustements")
    
    # Caméra
    st.subheader("📷 Caméra")
    c1, c2, c3 = st.columns(3)
    if c1.button("⬅️"): st.session_state.cam_h -= 45
    if c2.button("🔄"): st.session_state.cam_h += 180
    if c3.button("➡️"): st.session_state.cam_h += 45
    st.session_state.cam_p = st.slider("Inclinaison", -10, 50, st.session_state.cam_p)
    
    st.divider()
    container_params = st.container()

# --- HEADER ---
# CHARGEMENT DU LOGO (Si présent dans le dossier)
logo_b64 = get_base64_image("LOGO LIBERT new2.png")
if logo_b64:
    st.markdown(f'<img src="data:image/png;base64,{logo_b64}" style="max-width:200px; margin-bottom:20px;">', unsafe_allow_html=True)
else:
    st.title("🏗️ Libert & Cie")

st.markdown("### Estimateur de Façade Intelligent")

# --- RECHERCHE ---
c_s, c_b = st.columns([3, 1])
query = c_s.text_input("Adresse :", value=st.session_state.addr, placeholder="Ex: 159 rue du faubourg saint antoine...")
if query and len(query)>4:
    res = get_adresses_api(query)
    if res:
        final = st.selectbox("📍 Confirmation :", res, label_visibility="collapsed")
        if c_b.button("ESTIMER", type="primary"):
            st.session_state.addr = final
            st.session_state.data = analyse_ia(final)
            st.rerun()

# --- RÉSULTATS ---
if st.session_state.data:
    d = st.session_state.data
    
    # 1. PARAMETRES (Sidebar)
    with container_params:
        v_type = st.radio("Type", ["IMMEUBLE", "PAVILLON"], index=0 if d['type']=="IMMEUBLE" else 1)
        v_profil = st.selectbox("Support", list(DB_PRIX["FACADES"].keys()), index=list(DB_PRIX["FACADES"].keys()).index(d['profil']))
        
        v_niv = st.number_input("Niveaux (R+)", 1, 15, d['etages'])
        v_larg = st.number_input("Largeur (m)", 5, 100, d['largeur'])
        
        # Calculs
        h_calc = v_niv * 3.0
        s_calc = int(h_calc * v_larg)
        if v_type == "PAVILLON": s_calc = int((v_larg * 4) * h_calc)
        nb_fen = int(s_calc / 12)
        
        st.caption("Quantités Ajustables :")
        v_fen = st.number_input("Fenêtres", value=nb_fen)
        v_chiens = st.number_input("Chiens-assis", value=0)
        v_com = st.checkbox("Commerce RDC", value=False)
        v_porte = st.selectbox("Porte", ["AUCUNE", "PORTE_COCHERE", "PORTE_ENTREE"])

    # 2. VISUEL
    st.divider()
    ci, ct = st.columns([1.5, 2])
    with ci:
        st.image(get_street_view(st.session_state.addr, st.session_state.cam_h, st.session_state.cam_p), use_column_width=True)
    with ct:
        st.subheader("Synthèse")
        k1, k2, k3 = st.columns(3)
        k1.metric("Surface", f"{s_calc} m²")
        k2.metric("Hauteur", f"{h_calc} m")
        k3.metric("Ouvertures", f"{v_fen} U")
        
        if v_type == "IMMEUBLE": st.info("🏢 Configuration : Immeuble Collectif")
        else: st.success("🏡 Configuration : Maison Individuelle")

    # 3. DEVIS
    st.markdown("### 📑 Devis Estimatif")
    total = 0
    prof_data = DB_PRIX["FACADES"][v_profil]
    
    # Logique d'ajout
    def add(nom, qte, pu, unit=""):
        tot = qte * pu
        if tot > 0:
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"**{nom}**")
            c2.write(f"{int(qte)} {unit}")
            c3.write(f"**{tot:,.2f} €**")
            st.markdown("<hr style='margin:2px 0; opacity:0.1'>", unsafe_allow_html=True)
        return tot

    # CALCULS PRIX
    st.markdown("##### 1. Logistique")
    if v_type == "PAVILLON":
        total += add("Échafaudage Léger", s_calc, DB_PRIX["LOGISTIQUE"]["ECHAFAUDAGE_PAV"]["pu"], "m²")
    else:
        total += add("Base Vie & Chantier", 1, DB_PRIX["LOGISTIQUE"]["BASE_VIE"]["pu"], "Fft")
        total += add("Échafaudage Classe 4", s_calc, DB_PRIX["LOGISTIQUE"]["ECHAFAUDAGE"]["pu"], "m²")
        total += add("Taxes Voirie (ODP)", 1, DB_PRIX["LOGISTIQUE"]["AUTORISATION"]["pu"], "Fft")
        if v_com: total += add("Tunnel Protection", v_larg, DB_PRIX["LOGISTIQUE"]["TUNNEL"]["pu"], "ml")
    
    st.markdown("##### 2. Traitement")
    total += add(f"Nettoyage ({v_profil})", s_calc, prof_data["nettoyage"], "m²")
    s_pioch = int(s_calc * prof_data["ratio_degats"])
    if v_chiens > 0 and v_profil == "PLATRE_ANCIEN": s_pioch = int(s_calc * 0.60)
    total += add("Maçonnerie / Purge", s_pioch, prof_data["piochage"], "m²")
    total += add("Finition Système", s_calc, prof_data["finition"], "m²")
    
    st.markdown("##### 3. Finitions")
    total += add("Appuis Zinc", v_fen, DB_PRIX["ZINGUERIE"]["APPUI"]["pu"], "U")
    total += add("Descentes EP", int(h_calc), DB_PRIX["ZINGUERIE"]["DESCENTE"]["pu"], "ml")
    if v_chiens > 0: total += add("Habillage Chiens-Assis", v_chiens, DB_PRIX["ZINGUERIE"]["CHIEN_ASSIS"]["pu"], "U")
    if v_porte != "AUCUNE": total += add("Restauration Porte", 1, DB_PRIX["BOISERIE"][v_porte]["pu"], "U")
    if v_type == "IMMEUBLE": 
        total += add("Garde-Corps", int(v_fen*0.7), DB_PRIX["ZINGUERIE"]["GARDE_CORPS"]["pu"], "U")
        total += add("Bandeaux Zinc", int(v_larg*2), DB_PRIX["ZINGUERIE"]["BANDEAU"]["pu"], "ml")

    st.markdown("---")
    
    # --- EXPORT ---
    # Préparation des données pour le PDF
    export_data = {
        "adresse": st.session_state.addr,
        "type": v_type,
        "geo": {"etages": v_niv},
        "metres": {"surface": s_calc, "fenetres": v_fen},
        "tech": {"profil": v_profil}
    }
    
    # Génération HTML pour download
    html_content = generer_html_a4(export_data, DB_PRIX, total, logo_b64)
    
    c_tot, c_dl = st.columns([2, 1])
    with c_tot:
        st.markdown(f"<h2 style='margin:0'>TOTAL HT : {total:,.2f} €</h2>", unsafe_allow_html=True)
    with c_dl:
        st.download_button("📥 TÉLÉCHARGER LE DEVIS (PDF)", data=html_content, file_name="Devis_Libert.html", mime="text/html")