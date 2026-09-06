# Brief de projet — Dashboard personnel de suivi

## 🎯 Objectif

Créer une application locale (dashboard) qui centralise 4 suivis personnels :
1. **Agenda** — événements à venir (import calendrier Apple)
2. **Dépenses** — suivi par catégorie (import relevés bancaires)
3. **Sport** — programme et progression d'entraînement (import Strava)
4. **Lectures / films** — suivi mensuel (saisie manuelle simple)

L'app doit tourner **en local**, se relancer facilement (`streamlit run app/main.py`),
et se recharger simplement quand on dépose de nouveaux fichiers d'export dans `/data`.

---

## 🖥️ Stack technique recommandée

- **Python 3.11+**
- **Streamlit** — interface du dashboard (multi-page)
- **pandas** — traitement des données
- **plotly** — graphiques interactifs
- **icalendar** ou **ics** — parsing du fichier `.ics` exporté depuis Calendrier (macOS/iCloud)
- **PyYAML** — fichier de règles de catégorisation des dépenses

`requirements.txt` :
```
streamlit
pandas
plotly
icalendar
pyyaml
python-dateutil
```

---

## 📁 Arborescence du projet

```
dashboard/
├── data/
│   ├── strava/
│   │   └── activities.csv          # export Strava (bulk export)
│   ├── banque/
│   │   └── *.csv                   # un ou plusieurs relevés mensuels
│   ├── calendrier/
│   │   └── export.ics              # export du calendrier Apple/iCloud
│   └── media_log.csv               # log manuel lecture/films
├── config/
│   └── category_rules.yaml         # règles de catégorisation des dépenses
├── app/
│   ├── main.py                     # point d'entrée Streamlit
│   ├── modules/
│   │   ├── agenda.py
│   │   ├── finances.py
│   │   ├── sport.py
│   │   └── media.py
│   └── utils/
│       ├── parsers.py              # parsing ics / csv strava / csv banque
│       └── categorize.py           # logique de catégorisation
├── requirements.txt
└── README.md
```

---

## 📥 Détail des sources de données en entrée

### 1. Strava (`data/strava/activities.csv`)
Export via **Réglages Strava > Mon compte > Télécharger ou supprimer vos données** (bulk export officiel).
Colonnes utiles à exploiter : `Activity Date`, `Activity Type`, `Distance`, `Moving Time`,
`Elevation Gain`, `Average Heart Rate`, `Relative Effort`.
→ Le script doit gérer le cas où certaines colonnes sont vides selon le sport.

### 2. Relevés bancaires (`data/banque/*.csv`)
Format variable selon la banque — prévoir une **fonction de mapping configurable**
(dans `parsers.py`) pour faire correspondre les colonnes du CSV brut à un schéma standard :
`date | libellé | montant | catégorie (optionnelle)`.
La catégorisation automatique se fait via mots-clés définis dans `config/category_rules.yaml`, ex :
```yaml
Alimentation: ["carrefour", "monoprix", "boulangerie"]
Transport: ["sncf", "uber", "essence", "total energies"]
Abonnements: ["netflix", "spotify", "amazon prime"]
Loisirs: ["cinema", "fnac", "steam"]
```
Toute dépense non reconnue tombe dans "Non catégorisé" (affiché pour révision manuelle dans l'app).

### 3. Calendrier Apple (`data/calendrier/export.ics`)
Export depuis l'app **Calendrier** (macOS) : clic droit sur le calendrier > Exporter,
ou via iCloud. Le fichier `.ics` est parsé pour extraire les événements à venir
(titre, date/heure début-fin, lieu si présent), filtrés sur les 30 prochains jours.

### 4. Lectures / films (`data/media_log.csv`)
Pas d'export automatique disponible → saisie manuelle, mais l'app doit permettre
d'ajouter une ligne directement depuis l'interface Streamlit (formulaire), qui écrit
dans le CSV. Schéma :
```
date, type (livre/film), titre, statut (en cours/terminé), note (/5), commentaire
```

---

## ✅ Fonctionnalités attendues par module

**Agenda**
- Liste des événements des 7 / 30 prochains jours
- Vue par jour/semaine

**Finances**
- Total des dépenses du mois en cours vs mois précédent
- Camembert ou barres par catégorie
- Tableau des dépenses "non catégorisées" à corriger manuellement
- Évolution mensuelle (courbe sur les derniers mois si plusieurs relevés présents)

**Sport**
- Résumé du mois : nombre de séances, distance totale, dénivelé, temps total
- Courbe de progression (distance ou effort relatif dans le temps)
- Répartition par type d'activité

**Lectures / films**
- Liste du mois en cours (livres/films terminés)
- Formulaire d'ajout rapide
- Petites stats : nombre de livres vs films, note moyenne

---

## 🔒 Confidentialité

Toutes les données (bancaires en particulier) restent **en local**, dans `/data`,
qui doit être ajouté à `.gitignore` si le projet est versionné avec git.
Aucun appel réseau/API externe n'est nécessaire pour ce projet.

---

## 🚀 Prompt à donner à Claude Code

Une fois dans le dossier du projet, tu peux coller ceci tel quel :

```
Construis un dashboard personnel en Python/Streamlit selon les specs du fichier
BRIEF_DASHBOARD_PERSO.md à la racine du projet. Respecte l'arborescence proposée.
Commence par :
1. Créer la structure de dossiers et le requirements.txt
2. Créer des fichiers d'exemple (mock data) dans /data pour chaque source
   (activities.csv, un CSV banque, un export.ics, un media_log.csv) pour pouvoir
   tester l'app sans avoir encore mes vrais exports
3. Implémenter les parsers dans utils/parsers.py (un par source)
4. Implémenter le module de catégorisation des dépenses (utils/categorize.py)
   à partir de config/category_rules.yaml
5. Implémenter les 4 pages du dashboard (agenda, finances, sport, media)
   dans app/modules/, avec graphiques plotly
6. Assembler le tout dans app/main.py en navigation multi-page Streamlit
7. Écrire un README.md expliquant comment lancer l'app et où déposer mes vrais
   fichiers d'export pour remplacer les mocks

Lance l'app à la fin pour vérifier qu'elle démarre sans erreur avec les données
mock, puis montre-moi comment remplacer les mocks par mes vrais fichiers.
```

