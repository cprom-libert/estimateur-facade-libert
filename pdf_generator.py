from fpdf import FPDF
from io import BytesIO

def generate_pdf(estimation, nom):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Estimation pour {nom}", ln=1)
    pdf.cell(200, 10, txt=f"Adresse : {estimation['adresse']}", ln=1)
    pdf.cell(200, 10, txt=f"Surface : {estimation['surface']} m²", ln=1)
    pdf.cell(200, 10, txt="Détails :", ln=1)

    for item in estimation['details']:
        desc, qty, unit_price, total = item
        pdf.cell(200, 10, txt=f"- {desc} : {qty} m² × {unit_price} €/m² = {total} €", ln=1)

    pdf.cell(200, 10, txt=f"Total HT : {estimation['total']} €", ln=1)

    output = BytesIO()
    pdf.output(output)
    return output.getvalue()
