def calculate_estimate(data):
    surface = data["hauteur"] * data["largeur"]
    total = 0
    details = []

    if "Nettoyage" in data["options"]:
        cout = surface * 10
        details.append(("Nettoyage façade", surface, 10, cout))
        total += cout
    if "Peinture" in data["options"]:
        cout = surface * 35
        details.append(("Peinture façade", surface, 35, cout))
        total += cout
    if "Zinguerie" in data["options"]:
        cout = surface * 8
        details.append(("Travaux de zinguerie", surface, 8, cout))
        total += cout
    if "Echafaudage" in data["options"]:
        hauteur = data["hauteur"] + (3 if data["chiens_assis"] else 0)
        cout = surface * 15 + hauteur * 100
        details.append(("Échafaudage et accès", surface, 15, cout))
        total += cout

    return {
        "adresse": data["adresse"],
        "surface": surface,
        "details": details,
        "total": total
    }
