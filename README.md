# Rep'r

App de suivi personnel (Streamlit). **Rep'r** est un carnet d'adresses privé
sur carte (restaurants, cafés, musées...) : recherche d'adresse automatique
(Nominatim/OpenStreetMap, sans clé API), un rep'r est marqué **Vécu** (avec
un ressenti en 5 niveaux, de Coup de cœur à À éviter) ou **Envie** (pas
encore testé), fiches exportables en image, et envoi d'une fiche à un autre
utilisateur de l'app. Chacun a son propre compte (email + mot de passe) et
ne voit que ses propres rep'rs — les données sont stockées sur Supabase
(Postgres + auth, offre gratuite), pas en local, précisément pour pouvoir
être partagées entre plusieurs comptes.

Agenda, Finances, Sport et Bucket list existent toujours dans
`app/modules/` (stockage CSV/`.ics` local) mais sont actuellement retirés du
menu — voir "Remettre un module archivé" plus bas.

## Comptes et données (configuration Supabase, une seule fois)

1. Crée un projet gratuit sur [supabase.com](https://supabase.com).
2. Dans l'éditeur SQL du projet (SQL Editor > New query), colle et exécute le
   contenu de `supabase/schema.sql` (tables, permissions, fonction de partage).
   Si le projet existait déjà avec l'ancien modèle (statut/note), exécute
   aussi `supabase/migration_002_repr.sql` pour passer au modèle Vécu/Envie
   + ressenti.
3. Dans Authentication > Providers > Email, désactive **Confirm email** —
   sinon chaque inscription attend un clic sur un lien reçu par email, ce qui
   n'a pas d'intérêt pour un petit groupe de proches.
4. Dans Project Settings > API, récupère l'URL du projet et la clé
   `anon public`.
5. Copie `.streamlit/secrets.toml.example` vers `.streamlit/secrets.toml`
   (jamais versionné) et colle-les :
   ```toml
   SUPABASE_URL = "https://xxxx.supabase.co"
   SUPABASE_ANON_KEY = "xxxx"
   ```

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

L'app s'ouvre sur http://localhost:8501 sur un écran de connexion. Crée un
compte (onglet "Créer un compte"), tu arrives ensuite sur Rep'r.

## Partager l'app avec des proches (déploiement gratuit)

1. Pousse ce dépôt sur GitHub (déjà fait si tu as cloné
   `Augustin1305/Dashboard-Perso`).
2. Crée un compte gratuit sur [share.streamlit.io](https://share.streamlit.io)
   et connecte-le à ce dépôt, avec `app/main.py` comme fichier principal.
3. Dans les "Secrets" de l'app Streamlit Cloud, colle les deux mêmes clés
   Supabase que dans `.streamlit/secrets.toml` local.
4. Partage l'URL `https://xxxx.streamlit.app` obtenue : chacun crée son
   propre compte et n'a accès qu'à ses propres rep'rs (et à ceux qu'on lui
   envoie).

Limites de l'offre gratuite Streamlit Community Cloud : l'app se met en
veille après une période d'inactivité (premier chargement un peu plus lent
le temps qu'elle redémarre) et le dépôt GitHub doit être visible pour que
Streamlit Cloud puisse le déployer.

## Remettre un module archivé (Agenda / Finances / Sport / Bucket list)

Ces modules sont restés en stockage local (CSV/`.ics`), pas sur Supabase —
ils ne sont donc pas multi-utilisateur. Pour en remettre un dans le menu,
ajoute-le à l'import et au dictionnaire `PAGES` dans `app/main.py`, en lui
passant l'utilisateur connecté si sa fonction `render()` en a besoin (ce
n'est pas le cas de ces quatre modules, qui n'ont pas encore été adaptés à
l'authentification). Voir les sections ci-dessous pour leur configuration
respective (Agenda/CalDAV, format bancaire, catégorisation...).

## Remplacer les données d'exemple par tes vrais fichiers (modules archivés)

Le dossier `data/` contient des **fichiers d'exemple (mock)** pour les
modules archivés. Remplace-les par tes propres exports :

| Fichier à remplacer | Où l'obtenir |
|---|---|
| `data/strava/activities.csv` | Strava > Réglages > Mon compte > Télécharger ou supprimer vos données (bulk export) |
| `data/banque/*.csv` | Ton (ou tes) relevé(s) bancaire(s) exportés en CSV. Tu peux déposer plusieurs fichiers, un par mois par exemple |
| `data/calendrier/export.ics` | App Calendrier (macOS) : clic droit sur ton calendrier > Exporter, ou export iCloud |

Il suffit de déposer les nouveaux fichiers dans les mêmes dossiers (même nom
pour `activities.csv` et `export.ics` ; n'importe quel nom de fichier `.csv`
fonctionne dans `data/banque/`) puis de recharger la page Streamlit (touche
`R`, ou relancer l'app).

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
├── data/                  # données locales des modules archivés (gitignored)
├── config/
│   └── category_rules.yaml
├── supabase/
│   ├── schema.sql             # tables + policies Supabase pour Rep'r
│   └── migration_002_repr.sql # à exécuter sur un projet créé avant ce modèle
├── repr-design/           # brief et maquettes de la charte graphique Rep'r
├── app/
│   ├── main.py            # point d'entrée Streamlit (porte d'authentification)
│   ├── modules/           # une page par suivi
│   └── utils/             # auth, accès Supabase, parsers, géocodage, thème...
└── requirements.txt
```

## Confidentialité

Le dossier `data/` est dans `.gitignore` : tes données bancaires et
personnelles ne seront jamais versionnées si tu initialises un dépôt git sur
ce projet.
