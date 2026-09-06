# Dashboard Perso

Dashboard personnel local (Streamlit) qui centralise 4 suivis : agenda, finances,
sport et lectures/films. Toutes les données restent en local dans `data/` —
aucun appel réseau externe.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Lancer l'app

```bash
source .venv/bin/activate
streamlit run app/main.py
```

L'app s'ouvre sur http://localhost:8501. Le menu de gauche permet de naviguer
entre les 4 modules.

## Remplacer les données d'exemple par tes vrais fichiers

Le dossier `data/` contient actuellement des **fichiers d'exemple (mock)** pour
que l'app soit testable directement. Remplace-les par tes propres exports :

| Fichier à remplacer | Où l'obtenir |
|---|---|
| `data/strava/activities.csv` | Strava > Réglages > Mon compte > Télécharger ou supprimer vos données (bulk export) |
| `data/banque/*.csv` | Ton (ou tes) relevé(s) bancaire(s) exportés en CSV. Tu peux déposer plusieurs fichiers, un par mois par exemple |
| `data/calendrier/export.ics` | App Calendrier (macOS) : clic droit sur ton calendrier > Exporter, ou export iCloud |
| `data/media_log.csv` | Pas d'export : utilise le formulaire "➕ Ajouter une entrée" dans l'onglet Lectures/Films, ou édite le CSV à la main |

Il suffit de déposer les nouveaux fichiers dans les mêmes dossiers (même nom
pour `activities.csv`, `export.ics` et `media_log.csv` ; n'importe quel nom de
fichier `.csv` fonctionne dans `data/banque/`) puis de recharger la page
Streamlit (touche `R`, ou relancer l'app).

### Format bancaire

Le parser dans `app/utils/parsers.py` détecte automatiquement les colonnes
`date`, `libelle`/`libellé`, `montant` (et `categorie` si présente), avec le
séparateur `,` ou `;`. Si ta banque utilise des noms de colonnes différents,
ajoute-les dans `COLUMN_MAPPING` en haut de `parsers.py`.

### Catégorisation automatique des dépenses

Les règles de catégorisation par mots-clés sont dans
`config/category_rules.yaml`. Ajoute des mots-clés (en minuscules) sous la
catégorie de ton choix pour améliorer la reconnaissance. Toute dépense non
reconnue apparaît dans le tableau "Non catégorisé" du module Finances, pour
révision manuelle.

### Import d'un relevé via l'agent (CSV ou PDF)

Dans l'onglet **Finances**, l'encart "🤖 Importer un relevé via l'agent"
permet de déposer directement un relevé (CSV avec un format inhabituel, ou
PDF) : un agent (API OpenAI, modèle `gpt-5.6-terra`) lit le fichier et en
extrait les transactions (date, libellé, montant), qui sont ensuite
catégorisées avec les mêmes règles que le reste de l'app. Après vérification
de l'aperçu, un clic sur "Enregistrer" écrit un CSV standardisé dans
`data/banque/`, repris automatiquement par le reste du dashboard.

**Prérequis** : une clé API OpenAI dans la variable d'environnement
`OPENAI_API_KEY`, à placer dans le fichier `.env` local (jamais versionné,
voir `.env.example`) — sinon l'encart affiche un message et reste inactif :

```bash
cp .env.example .env
# puis édite .env et colle : OPENAI_API_KEY=sk-...
streamlit run app/main.py
```

**Confidentialité** : cette fonctionnalité envoie le contenu du fichier
déposé (montants, libellés) à l'API OpenAI le temps de l'extraction —
contrairement au reste de l'app qui ne fait aucun appel réseau. N'utilise
cet import que si tu es à l'aise avec ce compromis ; sinon, continue à
déposer tes CSV directement dans `data/banque/` (parsing 100 % local).

## Structure du projet

```
├── data/                  # données locales (gitignored)
├── config/
│   └── category_rules.yaml
├── app/
│   ├── main.py            # point d'entrée Streamlit
│   ├── modules/           # une page par suivi
│   └── utils/             # parsers, catégorisation, couleurs des graphiques
└── requirements.txt
```

## Confidentialité

Le dossier `data/` est dans `.gitignore` : tes données bancaires et
personnelles ne seront jamais versionnées si tu initialises un dépôt git sur
ce projet.
