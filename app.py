import streamlit as st
import time
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="Rapport Technique Libert V49", layout="wide", page_icon="📐")

# ==============================================================================
# 1. SÉCURITÉ API
# ==============================================================================
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    GOOGLE_API_KEY = ""

# ==============================================================================
# 2. BASE DE DONNÉES (Structure Harmonisée)
# ==============================================================================
DB_PRIX = {
    "LOGISTIQUE": {
        "BASE_VIE": {"titre": "Installation de Chantier", "desc": "Mise en place base vie, roulotte, raccordements et protections.", "norme": "Règl. Voirie", "pu": 4500.00, "unit": "Forfait"},
        "AUTORISATION": {"titre": "Droits de Voirie (ODP)", "desc": "Redevance d'occupation du domaine public.", "norme": "Admin", "pu": 605.00, "unit": "Forfait"},
        "ECHAFAUDAGE": {"titre": "Échafaudage Classe 4", "desc": "Structure tubulaire fixe, calcul de charge, filets pare-gravats.", "norme": "NF HD 1000", "pu": 39.90, "unit": "m²"},
        "ECHAFAUDAGE_PAV": {"titre": "Échafaudage Léger", "desc": "Structure adaptée pour pavillon.", "norme": "NF", "pu": 28.00, "unit": "m²"},
        "TUNNEL": {"titre": "Tunnel Piétons", "desc": "Protection étanche au-dessus des commerces.", "norme": "Sécurité", "pu": 65.00, "unit": "ml"},
        "ALARME": {"titre": "Sécurisation Électronique", "desc": "Système anti-intrusion 24/7.", "norme": "APSAD", "pu": 2070.00, "unit": "Forfait"},
        "MAJORATION_HAUTEUR": {"titre": "Sujétions IGH", "desc": "Manutention au-delà de R+5.", "norme": "-", "pu": 15.00, "unit": "m²"}
    },
    "FACADES": { 
        "PLATRE_ANCIEN": {
            "titre": "Restauration Plâtre (Traditionnel)", 
            "net": {"titre": "Décapage Chimique", "desc": "Élimination des badigeons par voie chimique.", "pu": 16.50},
            "pioch": {"titre": "Purge & Reconstitution", "desc": "Piochage des plâtres morts et réfection.", "pu": 160.00},
            "fin": {"titre": "Micro-Mortier Chaux", "desc": "Finition minérale respirante.", "pu": 95.00},
            "ratio_degats": 0.50
        },
        "PIERRE_TAILLE": { 
            "titre": "Ravalement Pierre de Taille", 
            "net": {"titre": "Hydrogommage Doux", "desc": "Projection basse pression d'abrasif neutre.", "pu": 28.00},
            "pioch": {"titre": "Ragréage Pierre", "desc": "Reconstitution des modénatures.", "pu": 85.00},
            "fin": {"titre": "Minéralisation", "desc": "Application lasure minérale (Keim).", "pu": 48.00},
            "ratio_degats": 0.10
        },
        "BRIQUE": { 
            "titre": "Restauration Brique", 
            "net": {"titre": "Nettoyage Chimique", "desc": "Nettoyage adapté briques.", "pu": 35.00},
            "pioch": {"titre": "Remplacement Briques", "desc": "Changement éléments éclatés.", "pu": 120.00},
            "fin": {"titre": "Hydrofuge", "desc": "Protection incolore.", "pu": 25.00},
            "ratio_degats": 0.15
        },
        "BETON": { 
            "titre": "Ravalement Technique D3", 
            "net": {"titre": "Lavage Haute Pression", "desc": "Décrassage pollution.", "pu": 12.00},
            "pioch": {"titre": "Traitement des fers", "desc": "Passivation antirouille.", "pu": 45.00},
            "fin": {"titre": "Revêtement D3 Armé", "desc": "Système souple imperméable.", "pu": 58.00},
            "ratio_degats": 0.05
        },
        "PAVILLON_ENDUIT": { 
            "titre": "Ravalement Pavillon", 
            "net": {"titre": "Lavage Façade", "desc": "Traitement anticryptogamique.", "pu": 18.00},
            "pioch": {"titre": "Reprises Fissures", "desc": "Ouverture et pontage.", "pu": 45.00},
            "fin": {"titre": "Peinture RPE", "desc": "Revêtement Plastique Épais.", "pu": 42.00},
            "ratio_degats": 0.10
        }
    },
    "FINITIONS": {
        "APPUI": {"titre": "Appuis de Fenêtre Zinc", "desc": "Façonnage et pose bavette.", "norme": "DTU 40.5", "pu": 215.00, "unit": "U"},
        "DESCENTE": {"titre": "Descentes EP", "desc": "Remplacement Zinc/Fonte.", "norme": "DTU 60.11", "pu": 165.00, "unit": "ml"},
        "GARDE_CORPS": {"titre": "Peinture Ferronneries", "desc": "Grattage, antirouille et laque.", "norme": "DTU 59.1", "pu": 160.00, "unit": "U"},
        "BANDEAU": {"titre": "Bandeaux Zinc", "desc": "Protection des corniches.", "norme": "DTU 40.5", "pu": 178.00, "unit": "ml"},
        "CHIEN_ASSIS": {"titre": "Habillage Lucarne", "desc": "Rénovation zinc et jouées.", "norme": "-", "pu": 950.00, "unit": "U"},
        "PORTE_COCHERE": {"titre": "Restauration Porte Cochère", "desc": "Décapage, greffes et lasure.", "norme": "-", "pu": 3200.00, "unit": "U"},
        "PORTE_ENTREE": {"titre": "Peinture Porte Hall", "desc": "Préparation et peinture.", "norme": "-", "pu": 850.00, "unit": "U"},
        "DEBORD_TOIT": {"titre": "Lasure Débords de Toit", "desc": "Protection planches de rive.", "norme": "-", "pu": 45.00, "unit": "ml"}
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
        return [f['properties']['label'] for f in r.json