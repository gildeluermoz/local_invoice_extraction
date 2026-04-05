#!/usr/bin/python3
import pandas as pd
import pytesseract
from pypdfium2 import PdfDocument
import os
import requests
import json


# Récupérer la liste des fichiers .pdf dans le répertoire courant
pdf_files = [f for f in os.listdir('.') if f.endswith('.pdf')]

# Liste pour stocker les lignes extraites
data = []

#Analyse du texte de la facture
def ia_analyse(text: str) -> dict:
    """
    Analyse le texte de facture avec le modèle Jan local.
    Jan et le serveur Jan doivent être démarrés
    
    Retourne :
        dict : {
            'nom_fournisseur': 'SAS MOULIN DU FOREST', 
            'date_facture': '26/03/2026', 
            'montant_total_ttc': 25.83, 
            'montant_tva': 1.35, 
            'objet_facture': 'Livraison de 24,48 € pour 2 kg de pain de blé bio'
        }
    """
    url = "http://127.0.0.1:1337/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer macleKey"
    }
    
    payload = {
        "model": "janhq/Jan-v3-4b-base-instruct-Q4_K_XL",
        "messages": [
            {
                "role": "user",
                "content": f"Analyse ce texte de facture et extrait les informations suivantes : \
                    Nom du fournisseur ex: SAS SODOGEC ; Date de la facture format jj/mm/aaaa ; Montant total TTC en euros, format 326.00 \
                    Montant TVA en euros, format 54.33 ; Un résumé de l'objet de la facture en 80 signe maximum. \
                    Voici le texte de la facture : {text} ; \
                    Retourne uniquement un JSON valide sans explication. \
                    Attention le nom du fournisseur n'est jamais SARL le Flourou ou Gîte le Flourou ou Le Flourou. Si tu trouves ce nom, c'est celui du client \
                    Voici un exemple du format json avec les clés attendues. Respecte le nom des clés : \
                    'nom_fournisseur': 'Orange', 'date_facture': '23/03/26', 'montant_total_ttc': 63,60, 'montant_tva': 10,60, 'objet_facture': 'Offre Livebox Pro Fibre' \
                    Si 'montant_tva' ou 'montant_total_ttc' n'est pas trouvé la valeur est vide mais pas 0."
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Lance une exception pour les codes d'erreur HTTP
        result = response.json()
        
        # if "response" not in result or not result["response"].strip():
        #     return {"error": "La réponse du modèle est vide ou manque le champ 'response'"}
            
        try:
            result_content = result['choices'][0]['message']['content']
            return json.loads(result_content)
        except json.JSONDecodeError as e:
            return {"error": f"Erreur de décodage JSON dans la réponse : {str(e)}"}
            
    except requests.exceptions.RequestException as e:
        return {"error": f"Erreur réseau : {str(e)}"}
    except Exception as e:
        return {"error": f"Erreur inattendue : {str(e)}"}

#print(json.dumps(resultat, indent=2, ensure_ascii=False))
def parse_pdf(
    path_or_io: str | bytes,
    pill_scale: int = 2,
    lang: str = "eng",
    page_sep: str = "\n\n",
    config: str = "",
) -> str:
    pdf = PdfDocument(path_or_io)
    pages = []
    total_pages = len(pdf)

    try:
        if not config:
            config = (
                f"-l {lang} --oem 1 --psm 6 "
                "-c preserve_interword_spaces=1 "
                "-c tessedit_do_invert=0 "
                "-c tosp_min_sane_kn_sp=2.8"
            )

        for page_idx in range(total_pages):
            #print(f"Processing page {page_idx + 1}/{total_pages}...")

            page = pdf.get_page(page_idx)
            page_img = page.render(scale=pill_scale).to_pil()
            page.close()

            text = pytesseract.image_to_string(page_img, config=config)

            try:
                page_img.close()  # Pillow ≥10
            except AttributeError:
                pass  # Pillow <10 fallback

            del page_img  # Free memory

            pages.append(text)
    finally:
        pdf.close()

    #print("OCR complete.")
    return page_sep.join(pages)

# traitement des fichiers
for fichier in pdf_files:
    piece = fichier[5:10]
    texte = parse_pdf(fichier)
    structured_text = ia_analyse(texte)
    solde = ""
    print(structured_text)
    if structured_text["objet_facture"] is None or structured_text["objet_facture"] == "":
        print(f"❌ 'objet_facture' n'a pas été extrait du fichier '{fichier}'")
        solde = "Warning"
    if structured_text["nom_fournisseur"] is None or structured_text["nom_fournisseur"] == "":
        print(f"❌ 'nom_fournisseur' n'a pas été extrait du fichier '{fichier}'")
        solde = "Warning"
    if structured_text["date_facture"] is None or structured_text["date_facture"] == "":
        print(f"❌ 'date_facture' n'a pas été extrait du fichier '{fichier}'")
        solde = "Warning"
    if structured_text["montant_tva"] is None or structured_text["montant_tva"] == '':
        print(f"❌ 'montant_tva' n'a pas été extrait du fichier '{fichier}'")
        solde = "Warning"
        structured_text["montant_tva"] = structured_text["montant_total_ttc"]/6
    if structured_text["montant_total_ttc"] is None or structured_text["montant_total_ttc"] == '':
        print(f"❌ 'montant_total_ttc' n'a pas été extrait du fichier '{fichier}'")
        solde = "Warning"
        structured_text["montant_total_ttc"] = 0
    # Ajouter la ligne au tableau
    data.append({
        "Soldé":solde,
        "Pièce":piece,
        "Journal":"AC",
        "Mode":"VIR",
        "Crédit / Débit": "D",
        "Intitulé":structured_text["objet_facture"],
        "Fournisseur": structured_text["nom_fournisseur"],
        "Intitulé compte":"",
        "TVA": structured_text["montant_tva"],
        "compte":"",
        "contrepartie":"",
        "date": structured_text["date_facture"],
        "Débit": structured_text["montant_total_ttc"],
        "Crédit":""
    })             
    
# Créer un DataFrame et exporter au CSV
try:
    df = pd.DataFrame(data)
    df.to_csv("factures_extraites.csv", index=False, sep=';', decimal=',')
    print("✅ Les données ont été extraites et sauvegardées sous 'factures_extraites.csv'")
except Exception as e:
        print(f"❌ Une erreur inattendue s'est produite : {str(e)}")




