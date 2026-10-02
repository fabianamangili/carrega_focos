import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon

# ============================================================
# LAYOUT - PONTOS DE ATENÇÃO GOES
# ============================================================

DPI = 100
WIDTH_PX, HEIGHT_PX = 1024, 722

fig = plt.figure(figsize=(WIDTH_PX / DPI, HEIGHT_PX / DPI), dpi=DPI)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, WIDTH_PX)
ax.set_ylim(0, HEIGHT_PX)
ax.axis("off")

# ------------------------------------------------------------
# Estilo
# ------------------------------------------------------------
BLACK = "#111111"
LIGHT = "#EEEEEE"
MAP_BG = "#E7E7E7"
GRID = "#777777"

def rect(x, y, w, h, lw=1, face="white", edge=BLACK):
    """Retângulo usando coordenadas em pixels."""
    ax.add_patch(
        Rectangle(
            (x, y), w, h,
            facecolor=face,
            edgecolor=edge,
            linewidth=lw
        )
    )

def txt(x, y, s, size=8, bold=False, ha="left", va="center",
        color=BLACK, rotation=0):
    ax.text(
        x, y, s,
        fontsize=size,
        fontweight="bold" if bold else "normal",
        ha=ha,
        va=va,
        color=color,
        rotation=rotation
    )

def section_title(x, y, s):
    txt(x, y, s, size=10, bold=True)

def table(x, y, w, h, headers, rows, widths=None, fs=7):
    """Tabela simples. x/y = canto inferior esquerdo."""
    ncol = len(headers)
    nrow = len(rows) + 1

    if widths is None:
        widths = [1 / ncol] * ncol

    scale = sum(widths)
    widths = [v / scale for v in widths]

    col_x = [x]
    for p in widths:
        col_x.append(col_x[-1] + w * p)

    row_h = h / nrow

    for r in range(nrow):
        yy = y + h - (r + 1) * row_h

        for c in range(ncol):
            xx = col_x[c]
            ww = col_x[c + 1] - xx

            rect(xx, yy, ww, row_h, lw=.55, face="white")

            if r == 0:
                value = headers[c]
                bold = True
            else:
                value = rows[r - 1][c]
                bold = False

            txt(xx + 4, yy + row_h / 2, str(value),
                size=fs, bold=bold)

def map_frame(x, y, w, h):
    """Moldura vazia para inserir posteriormente o mapa."""
    rect(x, y, w, h, lw=1.0, face="white")
    rect(x + 4, y + 4, w - 8, h - 8,
         lw=.5, face=MAP_BG, edge=GRID)

def legend_symbol(x, y, symbol, label, color=BLACK, fs=7):
    txt(x, y, symbol, size=fs, bold=True, color=color)
    txt(x + 18, y, label, size=fs)

# ------------------------------------------------------------
# Moldura externa
# ------------------------------------------------------------
rect(12, 12, 1000, 698, lw=.9)
rect(18, 18, 988, 686, lw=.35)

# ------------------------------------------------------------
# Título
# ------------------------------------------------------------
txt(
    30, 681,
    "Pontos de Atenção GOES - LARANJA (72 - 144)",
    size=14, bold=True
)

# ============================================================
# COLUNA ESQUERDA
# ============================================================
LX = 30
LW = 392

# Localização
section_title(LX, 651, "Localização do evento:")

rect(316, 630, 106, 35, lw=.7, face=LIGHT)
txt(320, 655, "Coordenada central:", size=7, bold=True)
txt(320, 640, '6°37\'9"W, 58°23\'4"S', size=7)

table(
    LX, 572, LW, 52,
    ["Evento", "Municípios", "Estados"],
    [["Evento 82769", "JACAREACANGA", "PA"]],
    widths=[.29, .48, .23],
    fs=6.5
)

# Informações do evento
section_title(LX, 555, "Informações do evento:")

table(
    LX, 503, LW, 46,
    ["Tipo de fogo (INPE)", "Duração", "Dias sem chuva",
     "Frentes Ativas", "Vegetação (%)"],
    [["Incêndio", "16", "12", "18", "37.7"]],
    widths=[.27, .14, .19, .18, .22],
    fs=6.0
)

# Áreas monitoradas
section_title(LX, 480, "Informações das áreas monitoradas no CIMAN:")

table(
    LX, 427, LW, 40,
    ["Nome da área", "Tipo da área"],
    [["TI MUNDURUKU (REGULARIZADA)", "TI"]],
    widths=[.68, .32],
    fs=6.2
)

# Mapa principal esquerdo
map_frame(LX, 176, LW, 235)

txt(LX, 164, "Google Satellite", size=7, bold=True)

# Linha divisória da legenda
ax.plot([LX, LX + LW], [156, 156], color=BLACK, lw=.5)

# Legenda esquerda
txt(30, 145, "Focos de fogo ativo", size=7, bold=True)
txt(226, 145, "Pontos de Atenção", size=7, bold=True)

# Camadas
legend_layers = [
    ("□", "Áreas monitoradas no", BLACK),
    ("", "CIMAN Federal", BLACK),
    ("", "Limites Municipais", BLACK),
    ("", "Vias", BLACK),
    ("", "Eventos de fogo ativo", BLACK),
    ("", "Incêndio", "#ff3300"),
    ("", "Possível incêndio", "#ff9900"),
]

yy = 129
for symbol, label, color in legend_layers:
    legend_symbol(30, yy, symbol, label, color=color, fs=6.5)
    yy -= 12

# Focos
focos = [
    "NOAA-19", "NOAA-20", "NOAA-21", "AQUA",
    "GOES-16", "MSG-03", "METOP-B", "METOP-C", "NOAA-18"
]

yy = 128
for i, item in enumerate(focos):
    color = "#00bfc4" if item in ("GOES-16", "MSG-03") else "#ff6f45"
    legend_symbol(226, yy, "+", item, color=color, fs=7)
    yy -= 12

# Pontos de atenção
txt(330, 128, "●  1 - 36", size=7)
txt(330, 116, "●  36 - 72", size=7)
txt(330, 104, "●  72 - 144", size=7)
txt(330, 92,  "●  144 - 288", size=7)

# ============================================================
# COLUNA DIREITA
# ============================================================
RX = 440
RW = 562

# Mapa superior
map_frame(RX, 400, RW, 300)

# Coordenadas
txt(430, 553, "6°37′S", size=6, rotation=90, ha="center")
txt(992, 701, "58°24′W", size=6, ha="right")

# Mapa inferior
map_frame(RX, 220, RW, 170)
txt(430, 305, "6°37′S", size=6, rotation=90, ha="center")

# Escala gráfica
sx, sy = 875, 212
txt(sx, sy + 13, "0", size=6, ha="center")
txt(sx + 75, sy + 13, "1.5", size=6, ha="center")
txt(sx + 150, sy + 13, "3 km", size=6, ha="center")

ax.plot([sx, sx + 150], [sy, sy], color=BLACK, lw=1)
for xx in (sx, sx + 75, sx + 150):
    ax.plot([xx, xx], [sy - 4, sy + 4], color=BLACK, lw=1)

# Norte
nx, ny = 998, 220
txt(nx, ny + 34, "N", size=8, bold=True, ha="center")
ax.add_patch(
    Polygon(
        [(nx, ny + 27), (nx - 9, ny), (nx, ny + 8), (nx + 9, ny)],
        closed=True,
        facecolor="white",
        edgecolor=BLACK,
        linewidth=.7
    )
)

# ------------------------------------------------------------
# Tabela de imagens
# ------------------------------------------------------------
table(
    RX, 166, RW, 47,
    ["Satélite", "Data da Imagem", "Coleção", "Tile / path / row"],
    [
        ["CBERS-4A-WFI", "2026-08-20T13:07:25+00:00",
         "CB4-WFI-L4-DN-1", "172_105"],
        ["CBERS-4A-WFI", "2026-08-22T14:04:59+00:00",
         "CB4A-WFI-L4-DN-1", "225_124"],
    ],
    widths=[.18, .29, .28, .25],
    fs=6.0
)

# ------------------------------------------------------------
# Rodapé
# ------------------------------------------------------------
txt(RX, 147, "Atualizado pelo INPE em: 25/08/2026", size=6)
txt(RX, 136, "Fonte: https://data.inpe.br/queimadas/dados", size=5.7)

# Área reservada para logotipos
txt(864, 55, "INPE", size=10, bold=True)
txt(907, 61, "Programa", size=6.5)
txt(907, 49, "Queimadas", size=6.5)
txt(970, 55, "CIMAN", size=8, bold=True)

# ------------------------------------------------------------
# Exportação
# ------------------------------------------------------------
plt.savefig(
    "layout_pontos_atencao_goes.png",
    dpi=DPI,
    bbox_inches="tight",
    pad_inches=0,
    facecolor="white"
)

plt.show()
