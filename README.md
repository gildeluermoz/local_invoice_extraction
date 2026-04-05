PARSE INVOICE TO CSV
********************

Ce script python utilise l'intelligence artificielle locale "Jan" pour extraire les informations utiles des factures pdf.

Pré-requis
----------

* Avoir sur son poste l'application open-source d'intelligence artificielle jan : https://www.jan.ai/download
* Le model janhq/Jan-v3-4b-base-instruct-Q4_K_XL doit être disponible.
    * configuraitons --> Fournisseurs de modèles --> Llama.cpp
* Lancer l'api locale de Jan
    * Configurations --> Serveur Local API --> Démarrer le serveur

Documentation : https://www.jan.ai/docs/desktop/api-server

Installation
------------

* Copier le code dans un répertoire
* Avec un terminal se localiser dans le répertoire :
```
    cd /path/to/app_directory
```
* Avec un terminal se localiser dans le répertoire :
```
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
```
Usage
-----

* Copier des factures au format pdf à analyser dans le répertoire (à la racine du répertoire de l'application)
    * Les factures pdf peuvent une source texte ou image scannée. Les deux types de pdf fonctionnent.
* Lancer le script :
```
    cd /path/to/app_directory
    source venv/bin/activate
    python3 ./parse_facture_jan.py
```
