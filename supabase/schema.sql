-- Schéma Supabase pour le carnet d'adresses Rep'r, multi-utilisateur.
-- À exécuter une fois dans l'éditeur SQL du projet Supabase (SQL Editor > New query).
-- Pour un projet déjà créé avec l'ancien schéma (statut/note), voir plutôt
-- migration_002_repr.sql.

create table if not exists discoveries (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  date date not null,
  categorie text not null,
  titre text not null,
  adresse text,
  lat double precision,
  lon double precision,
  vecu boolean not null default true,
  ressenti text check (ressenti in ('coeur', 'tb', 'ok', 'bof', 'ev')),
  commentaire text,
  created_at timestamptz not null default now()
);

alter table discoveries enable row level security;

create policy "own rows only" on discoveries
  for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create table if not exists shares (
  id uuid primary key default gen_random_uuid(),
  from_user_id uuid not null references auth.users(id) on delete cascade,
  from_email text not null,
  to_user_id uuid not null references auth.users(id) on delete cascade,
  -- Copie des champs de la découverte au moment de l'envoi : la fiche reçue
  -- reste stable même si l'original est modifié ou supprimé ensuite.
  snapshot jsonb not null,
  status text not null default 'pending' check (status in ('pending', 'accepted', 'dismissed')),
  created_at timestamptz not null default now()
);

alter table shares enable row level security;

create policy "sender can see own sends" on shares
  for select using (auth.uid() = from_user_id);

create policy "recipient can see own inbox" on shares
  for select using (auth.uid() = to_user_id);

create policy "sender can insert" on shares
  for insert with check (auth.uid() = from_user_id);

create policy "recipient can update status" on shares
  for update using (auth.uid() = to_user_id);

-- Résout un email en id utilisateur pour le partage, sans exposer toute la
-- table auth.users aux clients (SECURITY DEFINER = exécutée avec les droits
-- du propriétaire de la fonction, pas de l'appelant).
create or replace function find_user_id_by_email(lookup_email text)
returns uuid
language sql
security definer
set search_path = public
as $$
  select id from auth.users where email = lookup_email limit 1;
$$;

revoke all on function find_user_id_by_email(text) from public;
grant execute on function find_user_id_by_email(text) to authenticated;
