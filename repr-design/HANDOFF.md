# Rep'r — brief de design pour l'implémentation

Rep'r (prononcé « repère ») est un carnet d'adresses personnel sur carte, privé : pas de réseau social, pas de pub.
**Objectif n°1 : enregistrer un lieu et son ressenti en moins de 10 secondes, à une main.**
À terme, l'app regroupe plusieurs « carnets » (Lieux, Finances, Sport, Agenda).

Le dossier `maquettes/` contient les écrans de référence (iPhone 390×844), au format Design Component : du HTML avec styles inline, une boucle `<sc-for>`, une condition `<sc-if>`, des valeurs `{{…}}` calculées dans `renderVals()` en bas de chaque fichier. Ils servent de **référence visuelle et de spécification**, pas de code à réutiliser tel quel.
Chaque écran a un thème `light` / `dark` : les couleurs des deux thèmes sont dans l'objet `T` de `renderVals()`.

## Tokens

| Rôle | Clair | Sombre |
|---|---|---|
| Fond (papier) | #F6F3EC | #141718 |
| Surface | #FFFFFF | #1E2224 |
| Encre / texte | #1D2426 | #F1EDE4 |
| Texte secondaire | #6E6A63 | #A39E95 |
| Lignes | #E6E1D6 | #2E3336 |
| Remplissage doux | #ECE8DF | #262B2E |
| Bouton principal (fond / texte) | #1D2426 / #F6F3EC | #F1EDE4 / #141718 |

Carte (tons papier désaturés) : terre #ECE6D9 / #1A1E1F, rues #FAF8F3 / #2B3032, eau #D3DCD8 / #1C282B, parcs #DDE2CF / #1D2521.

**Ressentis** (pins et badges) : Coup de cœur #E4572E · Très bien #F2A541 · Correct #8FB9A8 · Bof #9AA5B1 · À éviter #5B5F66.
**Envie** (pas encore testé) : pin en contour pointillé, sans remplissage.
**Carnets** : Lieux #E4572E · Finances #3E7C59 · Sport #3A6EA5 · Agenda #7A5C99.

- Typo : Fraunces (titres, notes perso en italique), Inter (interface). Échelle 28 / 22 / 17 / 15 / 13.
- Grille 8 px · rayon 16 px (cartes), pill (chips, boutons) · ombres très légères · icônes Lucide trait 1,5 px.
- Zones tactiles ≥ 44 px.

## Logo

Wordmark « Rep'r » en Fraunces 600, couleur encre ; l'apostrophe est un pin terracotta (#E4572E, point intérieur couleur du fond).
Forme du pin (viewBox 0 0 24 30) : `M12 1.5C6.2 1.5 1.5 6.1 1.5 11.8 1.5 19.3 12 28.5 12 28.5S22.5 19.3 22.5 11.8C22.5 6.1 17.8 1.5 12 1.5Z`
Icône d'app : le pin seul, centré sur #F6F3EC.

## Écrans

1. **Accueil carte** : carte plein écran, pins colorés par ressenti, logo + bascule Carte/Carnet, recherche, chips de filtres (Vécu, Envie, ressentis, tags d'occasion), bouton « Me localiser », bouton pleine largeur « Poser un rep'r » en bas.
2. **Ajout rapide** (bottom sheet) : lieu pré-détecté par géoloc + « Modifier » + 2 lieux proches proposés ; bascule Vécu / Envie ; 5 pastilles de ressenti de 56 px (masquées si Envie) ; champ « Une ligne pour t'en souvenir » + micro pour mémo vocal ; « Ajouter des détails » replié (photos, tags, date) ; bouton « Enregistrer ». **Parcours minimal : ouvrir → ressenti → Enregistrer.**
3. **Fiche lieu** : catégorie, nom en Fraunces 28, badge de ressenti + Vécu, tampon de date pivoté, note perso en citation (Fraunces italique 22) + lecture du mémo vocal, visites, tags d'occasion, photos, infos pratiques, bouton Itinéraire.
4. **Vue carnet** : chronologie groupée par mois, colonne de date, cartes avec tampon de ressenti légèrement pivoté ; même bascule Carte/Carnet en haut.
5. **Mes carnets** (accueil global) : carte « Lieux » active (mini-carte, 3 stats), tuiles Finances / Sport / Agenda grisées « Bientôt », mention sur la confidentialité.
6. **Planche de style** : référence de tous les composants.

Les textes des maquettes (lieux, stats, adresses) sont des exemples.
