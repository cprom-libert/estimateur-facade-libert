import smtplib
from email.message import EmailMessage

def send_estimation_email(name, email, estimation, pdf_bytes):
    msg = EmailMessage()
    msg["Subject"] = "Votre estimation de ravalement"
    msg["From"] = "cprom@libertsas.fr"
    msg["To"] = email
    msg["Cc"] = "contact@libertsas.fr"

    body = f"""
Bonjour {name},

Merci pour votre demande d'estimation.

Adresse : {estimation['adresse']}
Surface : {estimation['surface']} m²
Montant estimé : {estimation['total']} € HT

Vous trouverez ci-joint votre estimation PDF.

Cordialement,
L'équipe Libert
"""
    msg.set_content(body)
    msg.add_attachment(pdf_bytes, maintype='application', subtype='pdf', filename='estimation.pdf')

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login("cprom@libertsas.fr", "VOTRE_MDP")
        server.send_message(msg)
