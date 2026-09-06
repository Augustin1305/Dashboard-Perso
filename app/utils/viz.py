"""Palette et constantes partagées pour les graphiques plotly du dashboard."""

# Palette catégorielle (ordre fixe, ne jamais réordonner par entité)
CATEGORICAL = [
    "#2a78d6",  # bleu
    "#eb6834",  # orange
    "#1baf7a",  # aqua
    "#eda100",  # jaune
    "#e87ba4",  # magenta
    "#008300",  # vert
    "#4a3aa7",  # violet
    "#e34948",  # rouge
]

# Rampe séquentielle bleu (clair -> foncé), pour magnitude / progression
SEQUENTIAL_BLUE = ["#cde2fb", "#86b6ef", "#3987e5", "#2a78d6", "#1c5cab", "#0d366b"]

STATUS_GOOD = "#0ca30c"
STATUS_WARNING = "#fab219"
STATUS_CRITICAL = "#d03b3b"

# Couleur neutre pour "Non catégorisé" : distincte des 8 teintes catégorielles,
# pour ne jamais être confondue avec une vraie catégorie.
NEUTRAL_UNCATEGORIZED = "#9a9a94"

# Flux financiers : rouge = sort de compte, vert = entre sur le compte (convention lisible)
FLOW_COLORS = {"Dépenses": CATEGORICAL[7], "Entrées": CATEGORICAL[5]}

PLOTLY_LAYOUT_DEFAULTS = dict(
    font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif"),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
)


def apply_layout_defaults(fig):
    fig.update_layout(**PLOTLY_LAYOUT_DEFAULTS)
    return fig
