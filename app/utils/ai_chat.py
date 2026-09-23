"""Résumé et questions/réponses sur un livre ou un film, via l'API OpenAI.

S'appuie uniquement sur les connaissances du modèle (pas de recherche web) :
plus simple, plus rapide, et sans coût réseau supplémentaire. Peut donc être
moins précis sur des titres très récents ou obscurs — le modèle est instruit
pour le signaler plutôt que d'inventer des détails.

Nécessite une clé API OpenAI dans la variable d'environnement
`OPENAI_API_KEY`.
"""
from __future__ import annotations

import os

from openai import OpenAI

MODEL = "gpt-5.6-terra"


class ApiKeyMissingError(RuntimeError):
    pass


def is_configured() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def _system_prompt(media_type: str, titre: str, statut: str) -> str:
    if statut == "fait":
        spoiler_note = "L'utilisateur a terminé cette œuvre : les spoilers sont autorisés si utiles."
    else:
        spoiler_note = (
            "L'utilisateur n'a pas terminé cette œuvre (statut : "
            f"{statut}) : évite les spoilers importants dans un résumé général, "
            "sauf si sa question l'exige explicitement."
        )
    return (
        f"Tu discutes avec l'utilisateur d'un {media_type} précis : « {titre} ». "
        "Réponds de façon claire et concise à ses questions, et propose un résumé pertinent si demandé. "
        f"{spoiler_note} "
        "Si tu n'es pas certain de connaître cette œuvre précise, dis-le clairement plutôt que d'inventer des détails."
    )


def chat_about_title(titre: str, media_type: str, statut: str, history: list[dict]) -> str:
    """history : liste de {"role": "user"|"assistant", "content": str}, sans le system prompt.

    Retourne le texte de la nouvelle réponse de l'assistant.
    """
    if not is_configured():
        raise ApiKeyMissingError(
            "Aucune clé API OpenAI trouvée (variable d'environnement OPENAI_API_KEY)."
        )

    client = OpenAI()
    messages = [{"role": "system", "content": _system_prompt(media_type, titre, statut)}]
    messages.extend(history)

    response = client.responses.create(model=MODEL, input=messages)
    return response.output_text
