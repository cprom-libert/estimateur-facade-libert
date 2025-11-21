import streamlit as st
import time
import datetime
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="Estimateur Libert V16 (Client)", layout="wide")

# ==========================================
# 1. BASE DE PRIX & PÉDAGOGIE (BENCHMARK LIBERT 2025)
# ==========================================
# Chaque poste contient maintenant une explication "pourquoi" pour le client
DB_PRIX = {
    "LOGISTIQUE": {
        "BASE_VIE": {"titre": "Installation & Base Vie", "pourquoi": "Roulotte, WC et protections obligatoires pour la sécurité des ouvriers et des passants.", "pu": 4500.00, "unit": "Forfait"},
        "AUTORISATION": {"titre": "Taxes de Voirie (ODP)", "pourquoi": "Redevance municipale pour l'occupation du trottoir pendant la durée du chantier.", "pu": 605.00, "unit": "Forfait"},
        "ECHAFAUDAGE": {"titre": "Échafaudage Tubulaire", "pourquoi": "Structure sécurisée classe 4 avec filets pare-gravats pour protéger la rue.", "pu": 39.90, "unit": "m²"},
        "FILET": {"titre": "Filets de protection", "pourquoi": "Obligatoire pour empêcher toute chute de gravats.", "pu": 13.00, "unit": "m²"}
    },
    "PLATRE_ANCIEN": { 
        "NETTOYAGE": {"titre": "Décapage Chimique", "pourquoi": "Retire les anciennes peintures sans abîmer le plâtre fragile.", "pu": 16.50},
        "PIOCHAGE": {"titre": "Soin des Maçonneries (Purge)", "pourquoi": "Étape critique : on retire les parties mortes (qui sonnent creux) pour reconstruire une base saine.", "pu": 150.00},
        "FINITION": {"titre": "Finition Micro-Mortier", "pourquoi": "Revêtement respirant qui laisse sortir l'humidité du mur (vital pour le plâtre).", "pu": 90.00},
        "RATIO_DEGATS": 0.50
    },
    "PIERRE_BRIQUE": { 
        "NETTOYAGE": {"titre": "Hydrogommage Doux", "pourquoi": "Gommage à basse pression pour nettoyer la pierre sans creuser le grain.", "pu": 25.00},
        "PIOCHAGE": {"titre": "Ragréage Pierre", "pourquoi": "Reconstitution des pierres abîmées avec un mortier spécial pierre.", "pu": 37.50},
        "FINITION": {"titre": "Minéralisation", "pourquoi": "Protection invisible qui durcit la pierre et la protège de la pollution.", "pu": 48.00},
        "RATIO_DEGATS": 0.10
    },
    "MODERNE_BETON": { 
        "NETTOYAGE": {"titre": "Lavage Haute Pression", "pourquoi": "Nettoyage en profondeur pour décrasser le béton.", "pu": 12.00},
        "PIOCHAGE": {"titre": "Traitement des fers", "pourquoi": "Passivation des fers à béton rouillés pour stopper l'éclatement du béton.", "pu": 37.50},
        "FINITION": {"titre": "Revêtement D3 Armé", "pourquoi": "Peinture épaisse et souple qui ponte les fissures et imperméabilise.", "pu": 55.00},
        "RATIO_DEGATS": 0.05
    },
    "BOISERIE": { # NOUVELLE SECTION
        "PORTE_COCHERE": {"titre": "Restauration Porte Cochère", "pourquoi": "Décapage complet, greffes de bois sur parties pourries, lasure ou peinture.", "pu": 3200.00, "unit": "Forfait"},
        "PORTE_ENTREE": {"titre": "Peinture Porte d'Immeuble", "pourquoi": "Égrenage et peinture laque tendue haute résistance.", "pu": 850.00, "unit": "Forfait"}
    },
    "ZINGUERIE": {
        "APPUI": {"titre": "Appuis de Fenêtre (Zinc)", "pourquoi": "Bavette neuve pour rejeter l'eau de pluie loin de la façade.", "pu": 210.00, "unit": "U"},
        "DESCENTE": {"titre": "Descentes EP", "pourquoi": "Remplacement des tuyaux percés ou vétustes (Zinc/Fonte).", "pu": 165.00, "unit": "ml"},
        "GARDE_CORPS": {"titre": "Peinture Garde-corps", "pourquoi": "Traitement antirouille indispensable pour l'esthétique et la durabilité.", "pu": 160.00, "unit": "U"}
    }
}

# ==========================================
# 2. FONCTIONS API
# ==========================================
def get_adresses_api(query):
    if not query: return []
    url = f"https://api-adresse.data.gouv.fr/search/?q={query}&limit=5"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return [feature['properties']['label'] for feature in data['features']]
    except: return []
    return []

def get_image_style(style_detecte):
    if "Faubourien" in style_detecte: return "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f6/14_rue_Saint-S%C3%A9bastien_Paris_11.jpg/800px-14_rue_Saint-S%C3%A9bastien_Paris_11.jpg"
    elif "Haussmannien" in style_detecte: return "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Paris_-_Immeuble_bld_Raspail.jpg/800px-Paris_-_Immeuble_bld_Raspail.jpg"
    elif "Moderne" in style_detecte: return "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/Immeuble_d%27habitation_HBM.jpg/800px-Immeuble_d%27habitation_HBM.jpg"
    else: return "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Immeuble_parisien.jpg/800px-Immeuble_parisien.jpg"

# ==========================================
# 3. CERVEAU IA (LOGIQUE MÉTIER + BOISERIE)
# ==========================================
def intelligence_artificielle(adresse_choisie):
    # A. DÉTECTION DU STYLE & BOISERIES
    if "sebastien" in adresse_choisie.lower() or "faubourg" in adresse_choisie.lower() or "orties" in adresse_choisie.lower():
        style = "Faubourien (Plâtre & Bois)"
        annee = "1850"
        profil_prix = "PLATRE_ANCIEN"
        # Les immeubles faubouriens ont souvent une grande porte cochère en bois
        type_porte = "PORTE_COCHERE" 
        largeur = 14
        etages = 4
    elif "pascal" in adresse_choisie.lower() or "thibaud" in adresse_choisie.lower():
        style = "Années 30 (Brique/Pierre)"
        annee = "1930"
        profil_prix = "PIERRE_BRIQUE"
        type_porte = "PORTE_ENTREE" # Porte standard vitrée/ferronnerie
        largeur = 18
        etages = 6
    elif "general" in adresse_choisie.lower() or "leclerc" in adresse_choisie.lower():
        style = "Moderne (Béton Armé)"
        annee = "1970"
        profil_prix = "MODERNE_BETON"
        type_porte = "PORTE_ENTREE" # Souvent porte alu/verre, mais on chiffre une peinture cadre
        largeur = 22
        etages = 7
    else:
        style = "Haussmannien (Pierre de Taille)"
        annee = "1890"
        profil_prix = "PIERRE_BRIQUE"
        type_porte = "PORTE_COCHERE" # Le classique Haussmannien
        largeur = 16
        etages = 6

    # B. CALCULS
    hauteur = etages * 3.0
    surface_totale = int(hauteur * largeur)
    nb_fenetres = int(surface_totale / 12)
    ml_ep = int(hauteur)
    nb_garde_corps = int(nb_fenetres * 0.8)

    img_url = get_image_style(style)

    return {
        "adresse": adresse_choisie,
        "info": {"annee": annee, "style": style, "img": img_url},
        "geo": {"surface": surface_totale, "etages": etages, "largeur": largeur},
        "tech": {"profil": profil_prix, "porte": type_porte},
        "qty": {"fenetres": nb_fenetres, "garde_corps": nb_garde_corps, "ep": ml_ep}
    }

# ==========================================
# 4. INTERFACE UTILISATEUR
# ==========================================
with st.sidebar:
    st.header("Libert & Cie")
    st.markdown("**Outil d'Estimation Façade**")
    st.caption("Version Client V16")

st.title("🏡 Votre Estimation de Ravalement")
st.markdown("### Renseignez l'adresse de votre copropriété")

if 'adresse_input' not in st.session_state: st.session_state.adresse_input = ""
col_search, col_btn = st.columns([3, 1])

with col_search:
    search_query = st.text_input("Adresse exacte :", placeholder="Ex: 14 rue Saint Sébastien...", value=st.session_state.adresse_input, label_visibility="collapsed")
    if search_query and len(search_query) > 3:
        options = get_adresses_api(search_query)
        selected_address = st.selectbox("📍 Confirmez l'adresse :", options) if options else search_query
    else:
        selected_address = None

with col_btn:
    launch = st.button("VOIR MON RAPPORT", type="primary", use_container_width=True)

if launch and selected_address:
    with st.spinner("Analyse du bâtiment en cours..."):
        time.sleep(1.2)
        data = intelligence_artificielle(selected_address)
        
        # --- EN-TÊTE VISUEL ---
        st.divider()
        col_img, col_infos = st.columns([1, 2])
        
        with col_img:
            st.image(data['info']['img'], use_column_width=True, caption="Typologie architecturale identifiée")
            
        with col_infos:
            st.subheader(f"📍 {data['adresse']}")
            
            # Indicateurs Clés (GRANDS pour être lus facilement)
            k1, k2, k3 = st.columns(3)
            k1.metric("Année Construction", data['info']['annee'])
            k2.metric("Hauteur", f"R+{data['geo']['etages']-1} ({data['geo']['etages']} niveaux)")
            k3.metric("Surface Façade", f"{data['geo']['surface']} m²")
            
            st.info(f"**Style détecté : {data['info']['style']}**. L'estimation ci-dessous prend en compte les spécificités techniques de ce type de bâtiment (matériaux, décorations, menuiseries).")

        # --- LE DEVIS EXPLIQUÉ (DESIGN PÉDAGOGIQUE) ---
        st.markdown("### 📑 Détail de votre investissement")
        
        profil = DB_PRIX[data['tech']['profil']]
        porte_type = data['tech']['porte']
        qty = data['qty']
        surf = data['geo']['surface']
        total_ht = 0

        def afficher_ligne(icon, item_key, db_cat, qte, unit_override=None):
            # Récupération des datas
            item = DB_PRIX[db_cat][item_key]
            pu = item['pu']
            unit = unit_override if unit_override else item.get('unit', 'm²')
            
            # Calcul total ligne
            total_ligne = qte * pu
            
            # Affichage "Carte"
            with st.container():
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.markdown(f"**{icon} {item['titre']}**")
                    st.caption(f"💡 *{item['pourquoi']}*")
                with c2:
                    st.markdown(f"<div style='text-align:center; padding-top:5px;'>{qte} {unit}</div>", unsafe_allow_html=True)
                with c3:
                    st.markdown(f"<div style='text-align:right; font-weight:bold; color:#2c3e50; padding-top:5px;'>{total_ligne:,.2f} €</div>", unsafe_allow_html=True)
                st.markdown("<hr style='margin:5px 0; opacity:0.3;'>", unsafe_allow_html=True)
            
            return total_ligne

        # 1. INSTALLATION
        st.markdown("#### 1️⃣ Installation & Sécurité")
        total_ht += afficher_ligne("🚧", "BASE_VIE", "LOGISTIQUE", 1, "Forfait")
        total_ht += afficher_ligne("🛡️", "ECHAFAUDAGE", "LOGISTIQUE", surf)
        total_ht += afficher_ligne("📜", "AUTORISATION", "LOGISTIQUE", 1, "Forfait")

        # 2. FAÇADE
        st.markdown("#### 2️⃣ Traitement des Façades")
        total_ht += afficher_ligne("💦", "NETTOYAGE", data['tech']['profil'], surf)
        
        # Piochage
        surf_pioch = int(surf * profil["RATIO_DEGATS"])
        nom_piochage = "Soin des Maçonneries (Purge)"
        # On personnalise le titre si c'est du lourd
        item_pioch = DB_PRIX[data['tech']['profil']]["PIOCHAGE"]
        if profil["RATIO_DEGATS"] >= 0.5:
            item_pioch["titre"] = f"Réfection Lourde des Fonds ({int(profil['RATIO_DEGATS']*100)}%)"
        
        total_ht += afficher_ligne("🧱", "PIOCHAGE", data['tech']['profil'], surf_pioch)
        total_ht += afficher_ligne("🎨", "FINITION", data['tech']['profil'], surf)

        # 3. BOISERIES & SINGULIERS
        st.markdown("#### 3️⃣ Menuiseries & Finitions")
        # Boiserie (Porte)
        total_ht += afficher_ligne("🚪", porte_type, "BOISERIE", 1, "Unité")
        
        # Zinguerie
        total_ht += afficher_ligne("🌧️", "APPUI", "ZINGUERIE", qty['fenetres'], "Unité")
        total_ht += afficher_ligne("🚽", "DESCENTE", "ZINGUERIE", qty['ep'], "ml")
        total_ht += afficher_ligne("🖌️", "GARDE_CORPS", "ZINGUERIE", qty['garde_corps'], "Unité")

        # --- TOTAL ---
        st.markdown("---")
        col_tot_txt, col_tot_price = st.columns([3, 1])
        with col_tot_txt:
            st.markdown("### TOTAL ESTIMATIF HT")
            st.caption("TVA applicable : 10% (Rénovation) ou 20% (Neuf). Devis non contractuel.")
        with col_tot_price:
            st.markdown(f"<h2 style='text-align:right; color:#2980b9;'>{total_ht:,.2f} €</h2>", unsafe_allow_html=True)

elif launch and not selected_address:
    st.error("Merci de sélectionner une adresse valide.")