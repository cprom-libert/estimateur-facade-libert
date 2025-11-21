import streamlit as st
import time
import datetime
import requests # Nécessaire pour interroger l'API Adresse Gouv

# --- CONFIGURATION ---
st.set_page_config(page_title="Estimateur Libert V15", layout="wide")

# ==========================================
# 1. BASE DE PRIX "LIBERT & CIE" (BENCHMARK)
# ==========================================
DB_PRIX = {
    "INSTALLATION": {
        "BASE_VIE": 4500.00, "AUTORISATION": 605.00, 
        "ECHAFAUDAGE": 39.90, "FILET": 13.00
    },
    "PLATRE_ANCIEN": { # Faubourg
        "NETTOYAGE": 16.50, "PIOCHAGE": 150.00, "FINITION": 90.00, "RATIO_DEGATS": 0.50
    },
    "PIERRE_BRIQUE": { # Années 30
        "NETTOYAGE": 25.00, "PIOCHAGE": 37.50, "FINITION": 48.00, "RATIO_DEGATS": 0.10
    },
    "MODERNE_BETON": { # Années 70
        "NETTOYAGE": 12.00, "PIOCHAGE": 37.50, "FINITION": 55.00, "RATIO_DEGATS": 0.05
    },
    "ZINGUERIE": {
        "APPUI": 210.00, "BANDEAU": 178.00, "DESCENTE": 165.00, "GARDE_CORPS": 160.00
    }
}

# ==========================================
# 2. FONCTIONS API (ADRESSE & IMAGE)
# ==========================================

def get_adresses_api(query):
    """Interroge l'API du gouvernement pour l'autocomplétion"""
    if not query: return []
    url = f"https://api-adresse.data.gouv.fr/search/?q={query}&limit=5"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # On retourne une liste de (Label complet, Code Postal)
            return [feature['properties']['label'] for feature in data['features']]
    except:
        return []
    return []

def get_image_style(style_detecte):
    """Retourne une photo d'illustration réaliste selon le style"""
    if "Faubourien" in style_detecte:
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/14_rue_Saint-S%C3%A9bastien_Paris_11.jpg/800px-14_rue_Saint-S%C3%A9bastien_Paris_11.jpg"
    elif "Haussmannien" in style_detecte:
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Paris_-_Immeuble_bld_Raspail.jpg/800px-Paris_-_Immeuble_bld_Raspail.jpg"
    elif "Moderne" in style_detecte:
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Immeuble_d%27habitation_HBM.jpg/800px-Immeuble_d%27habitation_HBM.jpg"
    else:
        return "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Immeuble_parisien.jpg/800px-Immeuble_parisien.jpg"

# ==========================================
# 3. CERVEAU IA (LOGIQUE MÉTIER)
# ==========================================
def intelligence_artificielle(adresse_choisie):
    # A. DÉTECTION DU STYLE (Logique simulée sur mots clés adresse)
    
    if "sebastien" in adresse_choisie.lower() or "faubourg" in adresse_choisie.lower() or "orties" in adresse_choisie.lower():
        style = "Faubourien (Plâtre & Bois)"
        annee = "Ca. 1850"
        profil_prix = "PLATRE_ANCIEN"
        diag = "Pathologie : Fissures structurelles, enduits soufflés, risque plomb."
        largeur = 14
        etages = 4
    elif "pascal" in adresse_choisie.lower() or "thibaud" in adresse_choisie.lower():
        style = "Années 30 (Brique/Pierre)"
        annee = "Ca. 1930"
        profil_prix = "PIERRE_BRIQUE"
        diag = "Pathologie : Encrassement atmosphérique, joints dégradés."
        largeur = 18
        etages = 6
    elif "general" in adresse_choisie.lower() or "leclerc" in adresse_choisie.lower():
        style = "Moderne (Béton Armé)"
        annee = "Ca. 1970"
        profil_prix = "MODERNE_BETON"
        diag = "Pathologie : Carbonatation, éclats de béton, isolation faible."
        largeur = 22
        etages = 7
    else:
        # Par défaut : Haussmannien standard
        style = "Haussmannien (Pierre de Taille)"
        annee = "Ca. 1890"
        profil_prix = "PIERRE_BRIQUE"
        diag = "Pathologie : Noircissement, Zingueries vétustes."
        largeur = 16
        etages = 6

    # B. CALCULS GÉOMÉTRIQUES
    hauteur = etages * 3.0
    surface_totale = int(hauteur * largeur)
    
    # C. POINTS SINGULIERS
    nb_fenetres = int(surface_totale / 12)
    ml_bandeaux = int(largeur * 2.5)
    nb_garde_corps = int(nb_fenetres * 0.8)
    ml_ep = int(hauteur)

    # Image
    img_url = get_image_style(style)

    return {
        "adresse": adresse_choisie,
        "info": {"annee": annee, "style": style, "diag": diag, "img": img_url},
        "geo": {"surface": surface_totale, "etages": etages},
        "tech": {"profil": profil_prix},
        "qty": {"fenetres": nb_fenetres, "bandeaux": ml_bandeaux, "garde_corps": nb_garde_corps, "ep": ml_ep}
    }

# ==========================================
# 4. INTERFACE UTILISATEUR
# ==========================================

# Sidebar pour le logo ou info entreprise
with st.sidebar:
    st.header("Libert & Cie")
    st.info("Estimateur V15.1\nConnecté API Gouv.")
    st.markdown("---")
    st.caption("Cet outil utilise l'IA pour estimer la surface et les pathologies à partir de l'adresse.")

st.title("📍 Estimateur de Façade Intelligent")
st.markdown("#### Entrez l'adresse pour générer le rapport technique")

# --- ZONE DE RECHERCHE ADRESSE (AUTOCOMPLÉTION) ---
col_search, col_btn = st.columns([3, 1])

with col_search:
    # On utilise session_state pour garder l'adresse en mémoire
    if 'adresse_input' not in st.session_state: st.session_state.adresse_input = ""
    
    search_query = st.text_input("Rechercher une adresse (France)", placeholder="Ex: 14 rue Saint Sébastien...", value=st.session_state.adresse_input)
    
    # Menu déroulant dynamique
    if search_query and len(search_query) > 3:
        options = get_adresses_api(search_query)
        if options:
            selected_address = st.selectbox("📍 Sélectionnez l'adresse exacte :", options)
        else:
            selected_address = search_query # Fallback
    else:
        selected_address = None

with col_btn:
    st.write("") # Spacer
    st.write("") 
    launch = st.button("LANCER L'ANALYSE", type="primary", use_container_width=True)

# --- GÉNÉRATION DU RAPPORT ---
if launch and selected_address:
    with st.spinner("📡 Connexion Cadastre & Analyse Visuelle..."):
        time.sleep(1.5) # Simulation temps de calcul
        data = intelligence_artificielle(selected_address)
        
        # --- AFFICHAGE DU RAPPORT ---
        st.divider()
        st.subheader(f"Rapport Technique : {selected_address}")
        
        # 1. VISUEL & DIAGNOSTIC (AVEC PHOTO)
        col_img, col_diag = st.columns([1, 1.5])
        
        with col_img:
            st.image(data['info']['img'], caption=f"Typologie détectée : {data['info']['style']}", use_column_width=True)
            
        with col_diag:
            st.success(f"**Année construction :** {data['info']['annee']}")
            st.info(f"**Surface Façade (IA) :** {data['geo']['surface']} m²")
            
            st.markdown(f"""
            <div style="background-color:#f9f9f9; padding:15px; border-radius:10px; border-left:5px solid #e67e22;">
                <b>🔍 Diagnostic Pathologique :</b><br>
                {data['info']['diag']}
            </div>
            """, unsafe_allow_html=True)
            
            # Jauge de dégradation (visuel)
            degat_pct = DB_PRIX[data['tech']['profil']]['RATIO_DEGATS'] * 100
            st.write(f"**État estimé des maçonneries :**")
            st.progress(int(degat_pct), text=f"Dégradation estimée à {int(degat_pct)}% (Impacte le piochage)")

        # 2. DEVIS DÉTAILLÉ
        st.markdown("### 📋 Détail Quantitatif Estimatif (DQE)")
        
        # Calculs
        p_profil = DB_PRIX[data['tech']['profil']]
        qty = data['qty']
        surf = data['geo']['surface']
        
        lignes = []
        total_ht = 0
        
        def add_row(poste, detail, qte, pu, unit):
            t = qte * pu
            # Conversion propre en string pour l'affichage
            pu_str = f"{pu:.2f} €"
            tot_str = f"{t:,.2f} €"
            lignes.append({"Poste": poste, "Détail Technique & Norme": detail, "Qté": f"{qte} {unit}", "P.U. HT": pu_str, "Total HT": tot_str})
            return t

        # Installation
        total_ht += add_row("Installation de Chantier", "Base vie, Roulotte, WC, Taxes Voirie", 1, DB_PRIX["INSTALLATION"]["BASE_VIE"] + DB_PRIX["INSTALLATION"]["AUTORISATION"], "Forfait")
        total_ht += add_row("Échafaudage & Filets", "Tubulaire Classe 4 + Pare-gravats (NF HD 1000)", surf, DB_PRIX["INSTALLATION"]["ECHAFAUDAGE"] + DB_PRIX["INSTALLATION"]["FILET"], "m²")

        # Façade
        total_ht += add_row("Nettoyage des Fonds", "Décapage ou Hydrogommage (DTU 59.1)", surf, p_profil["NETTOYAGE"], "m²")
        
        # Piochage dynamique
        surf_pioch = int(surf * p_profil["RATIO_DEGATS"])
        desc_pioch = f"⚠️ Piochage Lourd ({int(p_profil['RATIO_DEGATS']*100)}% de la surface)" if data['tech']['profil'] == "PLATRE_ANCIEN" else "Sondage & Ragréage ponctuel"
        total_ht += add_row("Maçonnerie (Purge)", f"{desc_pioch} (DTU 26.1)", surf_pioch, p_profil["PIOCHAGE"], "m²")
        
        total_ht += add_row("Finition Système", "Application revêtement complet", surf, p_profil["FINITION"], "m²")

        # Singuliers
        total_ht += add_row("Garde-corps", "Peinture antirouille", qty['garde_corps'], DB_PRIX["ZINGUERIE"]["GARDE_CORPS"], "U")
        total_ht += add_row("Bandeaux & Corniches", "Protection Zinc / Réparation", qty['bandeaux'], DB_PRIX["ZINGUERIE"]["BANDEAU"], "ml")
        # C'est cette ligne qui posait problème avant :
        total_ht += add_row("Appuis de Fenêtre", "Bavette Zinc (DTU 40.5)", qty['fenetres'], DB_PRIX["ZINGUERIE"]["APPUI"], "U")
        
        # Affichage Tableau
        st.dataframe(lignes, use_container_width=True)
        
        # Total
        st.markdown(f"""
        <div style="background-color:#2c3e50; color:white; padding:20px; border-radius:10px; text-align:right; font-size:1.5em;">
            <b>TOTAL ESTIMÉ HT : {total_ht:,.2f} €</b>
        </div>
        <div style="text-align:right; font-size:0.8em; color:gray; margin-top:5px;">
            TVA non incluse. Devis soumis à visite technique obligatoire.
        </div>
        """, unsafe_allow_html=True)

elif launch and not selected_address:
    st.error("Veuillez sélectionner une adresse valide dans la liste.")