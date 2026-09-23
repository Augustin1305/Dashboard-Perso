-- Migration Rep'r : passe la table discoveries de statut/note (à
-- découvrir/en cours/fait, note sur 5) au modèle Vécu/Envie + ressenti.
-- À exécuter une seule fois dans l'éditeur SQL, sur un projet où
-- schema.sql (version d'origine) a déjà été appliqué.

alter table discoveries add column if not exists vecu boolean not null default true;
alter table discoveries add column if not exists ressenti text
  check (ressenti in ('coeur', 'tb', 'ok', 'bof', 'ev'));

alter table discoveries drop column if exists statut;
alter table discoveries drop column if exists note;
