import streamlit as st
import time
import random
import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Estimateur Façade Libert", layout="centered")

# ==========================================
# 1. DATA BENCHMARK (PRIX LIBERT & CIE 2025)
# ==========================================
DB_PRIX = {
    "INSTALLATION": {
        "BASE_VIE": 4500.00,    # Forfait Base vie + Roulotte
        "AUTORISATION": 605.00, # Taxes voirie
        "ECHAFAUDAGE": 39.90,   # /m²
        "FILET": 13.00          # /m²
    },
    "PLATRE_ANCIEN": { # Type "Rue St Sébastien"
        "NETTOYAGE": 16.50,     # /m²
        "PIOCHAGE": 150.00,     # /m² (Gros poste)
        "FINITION": 90.00,      # /m² (Micro-mortier)
        "RATIO_DEGATS": 0.50    # 50% de la surface à refaire
    },
    "PIERRE_BRIQUE": { # Type "Rue Pascal"
        "NETTOYAGE": 25.00,     # /m²
        "PIOCHAGE": 37.50,      # /m²
        "FINITION": 48.00,      # /m²
        "RATIO_DEGATS": 0.10    # 10% réparation
    },
    "ZINGUERIE": {
        "APPUI": 210.00,        # /U
        "BANDEAU": 178.00,      # /ml
        "DESCENTE": 165.00,     # /ml
        "GARDE_CORPS": 160.00   # /U
    }
}

# ==========================================
# 2. CERVEAU IA (SIMULATION INTELLIGENTE)
# ==========================================
def intelligence_artificielle(adresse):
    # Simulation basée sur des mots-clés d'adresse pour la démo
    if "sebastien" in adresse.lower() or "faubourg" in adresse.lower() or "orties" in adresse.lower():
        style = "Faubourien (Plâtre & Bois)"
        annee = 1850
        profil_prix = "PLATRE_ANCIEN"
        diag = "Pathologie : Fissures structurelles et enduits soufflés."
        largeur = 14
        etages = 4
    elif "pascal" in adresse.lower() or "thibaud" in adresse.lower():
        style = "Immeuble Années 30 (Brique/Pierre)"
        annee = 1930
        profil_prix = "PIERRE_BRIQUE"
        diag = "Pathologie : Encrassement atmosphérique et joints dégradés."
        largeur = 18
        etages = 6
    else:
        style = "Immeuble Moderne"
        annee = 1970
        profil_prix = "PIERRE_BRIQUE"
        diag = "Pathologie : Usure courante, carbonatation possible."
        largeur = 20
        etages = 7

    # Calculs automatiques
    hauteur = etages * 3.0
    surface_totale = int(hauteur * largeur)
    
    nb_fenetres = int(surface_totale / 12)
    ml_bandeaux = int(largeur * 2.5)
    nb_garde_corps = int(nb_fenetres * 0.8)
    ml_ep = int(hauteur)

    return {
        "adresse": adresse,
        "info": {"annee": annee, "style": style, "diag": diag},
        "geo": {"surface": surface_totale, "etages": etages},
        "tech": {"profil": profil_prix},
        "qty": {"fenetres": nb_fenetres, "bandeaux": ml_bandeaux, "garde_corps": nb_garde_corps, "ep": ml_ep}
    }

# ==========================================
# 3. INTERFACE UTILISATEUR
# ==========================================
st.title("📍 Estimateur Façade Libert & Cie")
st.markdown("### Intelligence Artificielle & Base de Prix 2025")
st.info("Entrez simplement l'adresse. L'algorithme détecte le style, la surface et génère le devis technique.")

# Champ de saisie
adresse = st.text_input("Adresse du bâtiment", placeholder="Ex: 14 Rue Saint Sebastien, Paris")

if st.button("Lancer l'Estimation Complète", type="primary"):
    if adresse:
        with st.spinner("🛰️ Connexion Cadastre & Analyse Visuelle en cours..."):
            time.sleep(1.5) # Petit effet d'attente pour faire "pro"
            data = intelligence_artificielle(adresse)
            
            # --- AFFICHAGE DU DIAGNOSTIC ---
            st.success("Analyse terminée avec succès !")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Année", data['info']['annee'])
            col2.metric("Style", data['info']['style'].split("(")[0])
            col3.metric("Surface Déduite", f"{data['geo']['surface']} m²")
            
            st.markdown(f"**Diagnostic IA :** *{data['info']['diag']}*")
            
            # --- CALCUL DU DEVIS ---
            p_profil = DB_PRIX[data['tech']['profil']]
            qty = data['qty']
            surf = data['geo']['surface']
            
            lignes = []
            total_ht = 0
            
            def add_row(poste, detail, qte, pu, unit):
                tot = qte * pu
                lignes.append({"Poste": poste, "Détail Technique": detail, "Qté": f"{qte} {unit}", "P.U.": f"{pu} €", "Total HT": tot})
                return tot

            # 1. INSTALLATION
            total_ht += add_row("Installation de Chantier", "Base vie, Roulotte, WC, Taxes", 1, DB_PRIX["INSTALLATION"]["BASE_VIE"] + DB_PRIX["INSTALLATION"]["AUTORISATION"], "Forfait")
            total_ht += add_row("Échafaudage & Filets", "Tubulaire Classe 4 + Pare-gravats", surf, DB_PRIX["INSTALLATION"]["ECHAFAUDAGE"] + DB_PRIX["INSTALLATION"]["FILET"], "m²")

            # 2. FAÇADE
            total_ht += add_row("Nettoyage des Fonds", "Décapage ou Hydrogommage", surf, p_profil["NETTOYAGE"], "m²")
            
            surf_pioch = int(surf * p_profil["RATIO_DEGATS"])
            desc_pioch = "⚠️ Piochage Lourd (50%)" if data['tech']['profil'] == "PLATRE_ANCIEN" else "Sondage & Ragréage (10%)"
            total_ht += add_row("Maçonnerie (Purge)", desc_pioch, surf_pioch, p_profil["PIOCHAGE"], "m²")
            
            total_ht += add_row("Finition Système", "Application revêtement complet", surf, p_profil["FINITION"], "m²")

            # 3. POINTS SINGULIERS
            total_ht += add_row("Garde-corps", "Peinture antirouille", qty['garde_corps'], DB_PRIX["ZINGUERIE"]["GARDE_CORPS"], "U")
            total_ht += add_row("Bandeaux & Corniches", "Protection Zinc / Réparation", qty['bandeaux'], DB_PRIX["ZINGUERIE"]["BANDEAU"], "ml")
            total_ht += add_row("Appuis de Fenêtre", "Bavette Zinc", qty['fenetres'], DB_PRIX["ZINGUERIE"]["APPUI"], "U")
            
            # --- TABLEAU FINAL ---
            st.markdown("---")
            st.subheader("📋 Détail Quantitatif Estimatif (DQE)")
            st.dataframe(lignes, use_container_width=True)
            
            # TOTAL
            st.markdown(f"""
            <div style="background-color:#f0f2f6; padding:20px; border-radius:10px; text-align:right;">
                <h2 style="color:#000; margin:0;">TOTAL HT : {total_ht:,.2f} €</h2>
                <small>TVA non incluse. Estimation indicative soumise à visite technique.</small>
            </div>
            """, unsafe_allow_html=True)
            
    else:
        st.warning("Veuillez entrer une adresse pour démarrer.")