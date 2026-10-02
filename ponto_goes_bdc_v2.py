import os
import json
import requests

from pystac_client import Client
from typing import List, Dict
from osgeo import gdal

from PyQt5.QtGui import QPixmap
from datetime import datetime, timedelta
from PIL import Image, ImageEnhance, ImageDraw
from io import BytesIO
from xml.etree import ElementTree as ET
from qgis.utils import iface
from qgis.PyQt.QtGui import QFont

from qgis.core import (
    QgsRasterLayer,
    QgsProject,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsGeometry,
    QgsPointXY,
    QgsWkbTypes,
    QgsJsonUtils,
    QgsProviderRegistry,
    QgsVectorLayer,
    QgsFeature,
    QgsField,
    QgsVectorFileWriter,
    QgsPalLayerSettings,
    QgsTextFormat,
    QgsVectorLayerSimpleLabeling
)
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QDialogButtonBox,
    QTableWidget,
    QTableWidgetItem,
    QHBoxLayout,
    QLabel,
    QApplication,
    QCheckBox,
    QMessageBox,
    QAbstractItemView,
    QWidget
)
from PyQt5.QtCore import (
    Qt,
    QEventLoop,
    QVariant
)

# ============================================================
# CONFIGURAÇÃO CENTRAL DOS SATÉLITES / COLEÇÕES / BANDAS
# ============================================================
SATELLITE_CONFIG = {

    # ========================================================
    # LANDSAT
    # ========================================================

    "Landsat": {

        "collections": [
            "landsat-2"
        ],

        "tile_example": "223067",

        "default_bands": (
            "swir2, nir, red"
        ),

        "composition": (
            "SWIR-2 / NIR / Red"
        ),

        "description": (
            "Landsat 8/9 - "
            "Collection 2 Level-2"
        ),

        "assets": {

            "nir": [
                "nir08"
            ],

            "swir1": [
                "swir16"
            ],

            "swir2": [
                "swir22"
            ],

            "red": [
                "red"
            ],

            "green": [
                "green"
            ],

            "blue": [
                "blue"
            ]
        }
    },


    # ========================================================
    # SENTINEL-2
    # ========================================================

    "Sentinel-2": {

        "collections": [
            "S2_L2A-1"
        ],

        "tile_example": "22LEP",

        "default_bands": (
            "swir2, nir, red"
        ),

        "composition": (
            "SWIR-2 / NIR / Red"
        ),

        "description": (
            "Sentinel-2 MSI - "
            "Level-2A"
        ),

        "assets": {

            "nir": [
                "B08"
            ],

            "swir1": [
                "B11"
            ],

            "swir2": [
                "B12"
            ],

            "red": [
                "B04"
            ],

            "green": [
                "B03"
            ],

            "blue": [
                "B02"
            ]
        }
    },


    # ========================================================
    # AMAZONIA-1
    # ========================================================

    "Amazonia-1": {

        "collections": [
            "AMZ1-WFI-L4-SR-1"
        ],

        "tile_example": "",

        "default_bands": (
            "red, nir, green"
        ),

        "composition": (
            "Red / NIR / Green"
        ),

        "description": (
            "Amazonia-1 WFI - "
            "Level-4 Surface Reflectance"
        ),

        "assets": {

            "nir": [
                "BAND4"
            ],

            "swir1": [],

            "swir2": [],

            "red": [
                "BAND3"
            ],

            "green": [
                "BAND2"
            ],

            "blue": [
                "BAND1"
            ]
        }
    },
    # ========================================================
    # CBERS-4 MUX
    # ========================================================

    "CBERS-4-MUX": {

        "collections": [
            "CB4-MUX-L2-DN-1",
            "CB4-MUX-L4-DN-1",
            "CB4-MUX-L4-SR-1"
        ],

        "tile_example": "",

        "default_bands": (
            "red, nir, green"
        ),

        "composition": (
            "Red / NIR / Green"
        ),

        "description": (
            "CBERS-4 MUX"
        ),

        "assets": {

            "nir": [
                "BAND8"
            ],

            "swir1": [],

            "swir2": [],

            "red": [
                "BAND7"
            ],

            "green": [
                "BAND6"
            ],

            "blue": [
                "BAND5"
            ]
        }
    },


    # ========================================================
    # CBERS-4 WFI
    # ========================================================

    "CBERS-4-WFI": {

        "collections": [
            "CB4-WFI-L2-DN-1",
            "CB4-WFI-L4-DN-1",
            "CB4-WFI-L4-SR-1"
        ],

        "tile_example": "",

        "default_bands": (
            "red, nir, green"
        ),

        "composition": (
            "Red / NIR / Green"
        ),

        "description": (
            "CBERS-4 WFI"
        ),

        "assets": {

            "nir": [
                "BAND16"
            ],

            "swir1": [],

            "swir2": [],

            "red": [
                "BAND15"
            ],

            "green": [
                "BAND14"
            ],

            "blue": [
                "BAND13"
            ]
        }
    },


    # ========================================================
    # CBERS-4A MUX
    # ========================================================

    "CBERS-4A-MUX": {

        "collections": [
            "CB4A-MUX-L2-DN-1",
            "CB4A-MUX-L4-DN-1",
            "CB4A-MUX-L4-SR-1"
        ],

        "tile_example": "",

        "default_bands": (
            "red, nir, green"
        ),

        "composition": (
            "Red / NIR / Green"
        ),

        "description": (
            "CBERS-4A MUX"
        ),

        "assets": {

            "nir": [
                "BAND8"
            ],

            "swir1": [],

            "swir2": [],

            "red": [
                "BAND7"
            ],

            "green": [
                "BAND6"
            ],

            "blue": [
                "BAND5"
            ]
        }
    },


    # ========================================================
    # CBERS-4A WFI
    # ========================================================

    "CBERS-4A-WFI": {

        "collections": [
            "CB4A-WFI-L2-DN-1",
            "CB4A-WFI-L4-DN-1",
            "CB4A-WFI-L4-SR-1"
        ],

        "tile_example": "",

        "default_bands": (
            "red, nir, green"
        ),

        "composition": (
            "Red / NIR / Green"
        ),

        "description": (
            "CBERS-4A WFI"
        ),

        "assets": {

            "nir": [
                "BAND16"
            ],

            "swir1": [],

            "swir2": [],

            "red": [
                "BAND15"
            ],

            "green": [
                "BAND14"
            ],

            "blue": [
                "BAND13"
            ]
        }
    } 
}
# ============================================================
# LOG
# ============================================================

def log_message(message: str):

    print(
        f"[DEBUG] {message}"
    )


# ============================================================
# OBTER CONFIGURAÇÃO DO SATÉLITE
# ============================================================

def get_satellite_config(
    satellite: str
) -> dict:

    config = SATELLITE_CONFIG.get(
        satellite
    )

    if config is None:

        raise ValueError(
            f"Satélite não configurado: "
            f"{satellite}"
        )

    return config


# ============================================================
# COLEÇÕES STAC DISPONÍVEIS
# ============================================================

ALL_SATELLITES = [
    "Landsat",
    "Sentinel-2",
    "Amazonia-1",
    "CBERS-4-MUX",
    "CBERS-4-WFI",
    "CBERS-4A-MUX",
    "CBERS-4A-WFI"
]

ALL_COLLECTIONS = []

for satellite_name in ALL_SATELLITES:

    config = SATELLITE_CONFIG[
        satellite_name
    ]

    ALL_COLLECTIONS.extend(
        config["collections"]
    )


log_message(
    f"Todas as coleções STAC: "
    f"{ALL_COLLECTIONS}"
)

# ============================================================
# OBTER IDENTIFICAÇÃO ESPACIAL DO ITEM
# ============================================================

def get_item_tile(
    item,
    satellite: str
) -> str:

    # --------------------------------------------------------
    # Sentinel-2
    # --------------------------------------------------------

    if satellite == "Sentinel-2":

        tiles = item.properties.get(
            "bdc:tiles"
        )

        if isinstance(
            tiles,
            list
        ) and tiles:

            return str(
                tiles[0]
            )

        if isinstance(
            tiles,
            str
        ):

            return tiles

        return "N/A"

    # --------------------------------------------------------
    # Landsat
    # --------------------------------------------------------

    if satellite == "Landsat":

        parts = item.id.split("_")

        if len(parts) > 2:

            return parts[2]

        return "N/A"

    # --------------------------------------------------------
    # Amazonia-1 / CBERS
    # --------------------------------------------------------

    tiles = item.properties.get(
        "bdc:tiles"
    )

    if isinstance(
        tiles,
        list
    ) and tiles:

        return str(
            tiles[0]
        )

    if isinstance(
        tiles,
        str
    ):

        return tiles

    # --------------------------------------------------------
    # Tentar extrair path/row do ID
    # --------------------------------------------------------

    parts = item.id.split("_")

    if len(parts) >= 5:

        try:

            path = parts[-3]

            row = parts[-2]

            if (
                path.isdigit()
                and row.isdigit()
            ):

                return (
                    f"{path}/{row}"
                )

        except Exception:
            pass

    return "N/A"
# ============================================================
# MELHORAR THUMBNAIL
# ============================================================

def enhance_thumbnail(
    url: str,
    satellite: str,
    item,
    point_records: List[Dict] = None
):
    """
    Baixa o thumbnail do item STAC, aplica uma melhoria
    simples de contraste e desenha, somente em memória,
    os pontos GOES cobertos pela cena.

    Nenhum arquivo PNG é criado em disco.
    """

    try:

        log_message(
            f"Carregando thumbnail: {url}"
        )

        # ----------------------------------------------------
        # Download
        # ----------------------------------------------------

        response = requests.get(
            url,
            timeout=30
        )

        response.raise_for_status()

        # ----------------------------------------------------
        # Abrir imagem
        # ----------------------------------------------------

        image = Image.open(
            BytesIO(
                response.content
            )
        ).convert(
            "RGB"
        )

        # ----------------------------------------------------
        # Melhorar contraste
        # ----------------------------------------------------

        image = ImageEnhance.Contrast(
            image
        ).enhance(
            1.3
        )

        # ----------------------------------------------------
        # Pontos GOES cobertos pela cena
        # ----------------------------------------------------

        covered_focuses = _count_item_focus_points(
            item,
            point_records or []
        )
        log_message(
        f"[THUMBNAIL] Item: {item.id}"
        )

        log_message(
            f"[THUMBNAIL] point_records recebidos: "
            f"{len(point_records or [])}"
        )

        log_message(
            f"[THUMBNAIL] pontos cobertos: "
            f"{len(covered_focuses)}"
)
        if covered_focuses:

            draw = ImageDraw.Draw(image)

            width, height = image.size

            xmin, ymin, xmax, ymax = item.bbox[:4]

            log_message(
                f"[THUMBNAIL] Desenhando "
                f"{len(covered_focuses)} ponto(s)"
            )

            for record in covered_focuses:

                try:

                    lon = float(record["x"])
                    lat = float(record["y"])

                    pixel_x = (
                        (lon - xmin)
                        / (xmax - xmin)
                        * (width - 1)
                    )

                    pixel_y = (
                        (ymax - lat)
                        / (ymax - ymin)
                        * (height - 1)
                    )

                    if not (
                        0 <= pixel_x < width
                        and
                        0 <= pixel_y < height
                    ):
                        continue

                    radius = 5

                    draw.ellipse(
                        (
                            pixel_x - radius,
                            pixel_y - radius,
                            pixel_x + radius,
                            pixel_y + radius
                        ),
                        outline="red",
                        width=2
                    )

                except (
                    KeyError,
                    TypeError,
                    ValueError,
                    ZeroDivisionError
                ):
                    continue

        # ----------------------------------------------------
        # Converter para QPixmap
        # ----------------------------------------------------

        buffer = BytesIO()

        image.save(
            buffer,
            format="PNG"
        )

        pixmap = QPixmap()

        pixmap.loadFromData(
            buffer.getvalue(),
            "PNG"
        )

        return pixmap

    except Exception as e:

        log_message(
            f"Erro ao carregar thumbnail: {e}"
        )

        return QPixmap()

# ============================================================
# SELECIONAR IMAGENS DISPONÍVEIS
# ============================================================

def select_available_items(
    bbox: List[float],
    items: List,
    search_context: Dict = None,
    point_records: List[Dict] = None,
    covered_focuses_by_item: Dict = None
):

    # ========================================================
    # CRIAR DIÁLOGO
    # ========================================================

    dialog = QDialog()

    dialog.setWindowTitle(
        "Imagens Disponíveis"
    )

    dialog.setModal(
        True
    )

    layout = QVBoxLayout()

    # ========================================================
    # TABELA
    # ========================================================

    table = QTableWidget()

    table.setRowCount(
        len(items)
    )

    table.setColumnCount(
        7
    )

    table.setHorizontalHeaderLabels(
        [
            "Selecionar",
            "ID da Feição",
            "Data",
            "Satélite",
            "Tile / Órbita",
            "Cloud Cover (%)",
            "Thumbnail"
        ]
    )

    table.setSelectionMode(
        QAbstractItemView.NoSelection
    )

    # ========================================================
    # PREENCHER TABELA
    # ========================================================
    checkboxes = []
    
    for row, item in enumerate(items):

        # ------------------------
        #Checkbox
        #-------------------------
        checkbox = QCheckBox()
        checkbox.setChecked(False)
        checkboxes.append(checkbox)

        checkbox_widget = QWidget()
        checkbox_layout = QHBoxLayout(checkbox_widget)

        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setAlignment(Qt.AlignCenter)

        checkbox_layout.addWidget(checkbox)

        table.setCellWidget(
            row,
            0,
            checkbox_widget
        )        

        # ----------------------------------------------------
        # Data
        # ----------------------------------------------------

        date = (
            item.datetime.strftime(
                "%Y-%m-%d"
            )
            if item.datetime
            else "N/A"
        )

        # ----------------------------------------------------
        # IDs das feições intersectadas pelo footprint
        # ----------------------------------------------------

        covered_focuses = (
            covered_focuses_by_item.get(item.id, [])
            if covered_focuses_by_item is not None
            else _count_item_focus_points(
                item,
                point_records or []
            )
        )

        focus_ids_text = ", ".join(
            str(record.get("id"))
            for record in covered_focuses
        )

        if not focus_ids_text:
            focus_ids_text = "N/A"

        # ----------------------------------------------------
        # Identificar satélite / sensor
        # ----------------------------------------------------

        item_id = (
            str(item.id)
            if item.id
            else ""
        )

        item_upper = (
            item_id.upper()
        )

        collection_id = ""

        try:

            collection_id = (
                item.collection_id
                if item.collection_id
                else ""
            )

        except Exception:

            collection_id = ""

        collection_upper = (
            str(collection_id).upper()
        )

        # ----------------------------------------------------
        # Landsat
        # ----------------------------------------------------

        if item_upper.startswith("LC08"):

            satellite_name = "Landsat 8"

            satellite_for_tile = (
                "Landsat"
            )

        elif item_upper.startswith("LC09"):

            satellite_name = "Landsat 9"

            satellite_for_tile = (
                "Landsat"
            )

        # ----------------------------------------------------
        # Sentinel-2
        # ----------------------------------------------------

        elif (
            item_upper.startswith("S2A")
            or item_upper.startswith("S2B")
            or item_upper.startswith("S2C")
        ):

            satellite_name = "Sentinel-2"

            satellite_for_tile = (
                "Sentinel-2"
            )

        # ----------------------------------------------------
        # Amazonia-1
        # ----------------------------------------------------

        elif (
            "AMZ1" in collection_upper
            or "AMAZONIA" in collection_upper
            or "AMZ1" in item_upper
            or "AMAZONIA" in item_upper
        ):

            satellite_name = "Amazonia-1"

            satellite_for_tile = (
                "Amazonia-1"
            )

        # ====================================================
        # CBERS-4A WFI
        # ====================================================
        # Deve vir antes do CBERS-4A MUX.
        # ====================================================

        elif (
            "CB4A-WFI" in collection_upper
            or "CB4A_WFI" in item_upper
            or "CBERS_4A_WFI" in item_upper
            or "CBERS4A_WFI" in item_upper
        ):

            satellite_name = "CBERS-4A WFI"

            satellite_for_tile = (
                "CBERS-4A-WFI"
            )

        # ====================================================
        # CBERS-4A MUX
        # ====================================================

        elif (
            "CB4A-MUX" in collection_upper
            or "CB4A_MUX" in item_upper
            or "CBERS_4A_MUX" in item_upper
        ):

            satellite_name = "CBERS-4A MUX"

            satellite_for_tile = (
                "CBERS-4A-MUX"
            )

        # ====================================================
        # CBERS-4 WFI
        # ====================================================

        elif (
            "CB4-WFI" in collection_upper
            or "CB4_WFI" in item_upper
            or "CBERS_4_WFI" in item_upper
            or "CBERS4_WFI" in item_upper
            or "CBERS_4_AWFI" in item_upper
        ):

            satellite_name = "CBERS-4 WFI"

            satellite_for_tile = (
                "CBERS-4-WFI"
            )

        # ====================================================
        # CBERS-4 MUX
        # ====================================================

        elif (
            "CB4-MUX" in collection_upper
            or "CB4_MUX" in item_upper
            or "CBERS_4_MUX" in item_upper
        ):

            satellite_name = "CBERS-4 MUX"

            satellite_for_tile = (
                "CBERS-4-MUX"
            )

        # ----------------------------------------------------
        # Não identificado
        # ----------------------------------------------------

        else:

            satellite_name = (
                collection_id
                if collection_id
                else "Desconhecido"
            )

            satellite_for_tile = (
                "Desconhecido"
            )

        # ----------------------------------------------------
        # Identificação espacial
        # ----------------------------------------------------

        item_tile = get_item_tile(
            item,
            satellite_for_tile
        )

        log_message(
            f"Item {item.id} - "
            f"Satélite: {satellite_name} - "
            f"Identificação espacial: "
            f"{item_tile}"
        )

        # ----------------------------------------------------
        # Coluna ID da Feição
        # ----------------------------------------------------

        table.setItem(
            row,
            1,
            QTableWidgetItem(
                focus_ids_text
            )
        )

        # ----------------------------------------------------
        # Coluna Data
        # ----------------------------------------------------

        table.setItem(
            row,
            2,
            QTableWidgetItem(
                date
            )
        )

        # ----------------------------------------------------
        # Coluna Satélite
        # ----------------------------------------------------

        table.setItem(
            row,
            3,
            QTableWidgetItem(
                satellite_name
            )
        )

        # ----------------------------------------------------
        # Coluna Tile / Órbita
        # ----------------------------------------------------

        table.setItem(
            row,
            4,
            QTableWidgetItem(
                item_tile
            )
        )

        # ----------------------------------------------------
        # Cloud Cover
        # ----------------------------------------------------

        cloud_cover = (
            item.properties.get(
                "eo:cloud_cover",
                "N/A"
            )
        )

        if isinstance(
            cloud_cover,
            (float, int)
        ):

            cloud_cover_text = (
                f"{cloud_cover:.2f}"
            )

        else:

            cloud_cover_text = str(
                cloud_cover
            )

        table.setItem(
            row,
            5,
            QTableWidgetItem(
                cloud_cover_text
            )
        )

        # ----------------------------------------------------
        # Thumbnail
        # ----------------------------------------------------

        thumbnail_asset = (
            item.assets.get(
                "thumbnail"
            )
        )

        thumbnail_href = (
            thumbnail_asset.href
            if thumbnail_asset
            else None
        )

        if (
            thumbnail_href
            and isinstance(
                thumbnail_href,
                str
            )
            and thumbnail_href.startswith(
                "http"
            )
        ):

            view_btn = QPushButton(
                "View"
            )

            def make_thumbnail_callback(
                url,
                item_date,
                item,
                point_records,
                sat=satellite_name
            ):

                def callback():

                    log_message(
                        f"Abrindo thumbnail: "
                        f"{url}"
                    )

                    pixmap = (
                        enhance_thumbnail(
                            url,
                            sat,
                            item,
                            point_records
                        )
                    )

                    if pixmap.isNull():

                        log_message(
                            "Thumbnail não "
                            "pôde ser exibida."
                        )

                        return

                    thumbnail_dialog = (
                        QDialog(
                            dialog
                        )
                    )

                    thumbnail_dialog.setWindowTitle(
                        f"Thumbnail - "
                        f"{item_date}"
                    )

                    thumb_layout = (
                        QVBoxLayout()
                    )

                    label = QLabel()

                    label.setAlignment(
                        Qt.AlignCenter
                    )

                    label.setPixmap(
                        pixmap.scaled(
                            800,
                            800,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )
                    )

                    thumb_layout.addWidget(
                        label
                    )

                    thumbnail_dialog.setLayout(
                        thumb_layout
                    )

                    thumbnail_dialog.exec_()

                return callback

            view_btn.clicked.connect(
                make_thumbnail_callback(
                    thumbnail_href,
                    date,
                    item,
                    point_records
                )
            )

            table.setCellWidget(
                row,
                6,
                view_btn
            )

        else:

            table.setItem(
                row,
                6,
                QTableWidgetItem(
                    "N/A"
                )
            )

    # ========================================================
    # AJUSTAR TABELA
    # ========================================================

    table.resizeColumnsToContents()

    total_width = (
        sum(
            table.columnWidth(
                col
            )
            for col in range(
                table.columnCount()
            )
        )
        + table.verticalHeader().width()
        + 40
    )

    table.setMinimumWidth(
        total_width
    )

    dialog.setMinimumWidth(
        total_width + 20
    )

    # ========================================================
    # INFORMAÇÃO DA BUSCA
    # ========================================================

    if search_context:

        context_text = (
            "Consulta espacial: feições selecionadas "
            "(intersects)\n"
            f"Camadas: {len(search_context.get('layers', []))}\n"
            f"Feições: {search_context.get('feature_count', 0)} | "
            f"Pontos únicos: {search_context.get('unique_points', 0)}\n"
            f"Período: {search_context.get('start_date')} até "
            f"{search_context.get('end_date')}"
        )

    elif bbox:

        context_text = (
            "BBOX utilizado na busca:\n"
            f"Xmin: {bbox[0]:.6f} | "
            f"Ymin: {bbox[1]:.6f} | "
            f"Xmax: {bbox[2]:.6f} | "
            f"Ymax: {bbox[3]:.6f}"
        )

    else:

        context_text = "Consulta espacial por feições."

    context_label = QLabel(
        context_text
    )

    context_label.setStyleSheet(
        "color: #555;"
    )

    context_label.setWordWrap(True)

    layout.addWidget(
        context_label
    )

    # ========================================================
    # INFORMAÇÃO SOBRE AS CENAS
    # ========================================================

    layout.addWidget(
        QLabel(
            f"{len(items)} imagem(ns) "
            "disponível(is) nos últimos 10 dias:"
        )
    )

    layout.addWidget(
        table
    )

    # ========================================================
    # BOTÕES DE SELEÇÃO
    # ========================================================

    def select_all_checkboxes():
        for checkbox in checkboxes:
            checkbox.setChecked(True)


    def deselect_all_checkboxes():
        for checkbox in checkboxes:
            checkbox.setChecked(False)


    # Criar os botões
    select_all_btn = QPushButton("Selecionar todas")
    deselect_all_btn = QPushButton("Desmarcar todas")

    # Conectar os botões às caixas de seleção
    select_all_btn.clicked.connect(
        select_all_checkboxes
    )

    deselect_all_btn.clicked.connect(
        deselect_all_checkboxes
    )

    # Layout dos botões
    btn_layout = QHBoxLayout()

    btn_layout.addWidget(
        select_all_btn
    )

    btn_layout.addWidget(
        deselect_all_btn
    )

    layout.addLayout(
        btn_layout
    )

    # ========================================================
    # BOTÕES OK / CANCELAR
    # ========================================================

    button_box = (
        QDialogButtonBox(
            QDialogButtonBox.Ok
            | QDialogButtonBox.Cancel
        )
    )

    layout.addWidget(
        button_box
    )

    dialog.setLayout(
        layout
    )


    # ========================================================
    # VOLTAR / CANCELAR
    # ========================================================

    button_box.rejected.connect(
        dialog.reject
    )

    # ========================================================
    # OK
    # ========================================================

    def accept_dialog():

        selected_rows = [
            row
            for row, checkbox in enumerate(checkboxes)
            if checkbox.isChecked()
        ]

        log_message(
            "================================================"
        )

        log_message(
            "BOTÃO OK - SELEÇÃO DE IMAGENS"
        )

        log_message(
            f"Linhas selecionadas: "
            f"{selected_rows}"
        )

        # ----------------------------------------------------
        # Nenhuma imagem selecionada
        # ----------------------------------------------------

        if not selected_rows:

            log_message(
                "Nenhuma imagem foi selecionada."
            )

            QMessageBox.warning(
                dialog,
                "Seleção de imagens",
                "Selecione pelo menos uma imagem "
                "para continuar."
            )

            return

        # ----------------------------------------------------
        # Aceitar
        # ----------------------------------------------------

        log_message(
            f"{len(selected_rows)} imagem(ns) "
            "selecionada(s)."
        )

        dialog.accept()

    button_box.accepted.connect(
        accept_dialog
    )

    # ========================================================
    # ABRIR DIÁLOGO
    # ========================================================

    log_message(
        "================================================"
    )

    log_message(
        "Abrindo diálogo de seleção de imagens..."
    )
    event_loop = QEventLoop()

    dialog.accepted.connect(event_loop.quit)
    dialog.rejected.connect(event_loop.quit)

    dialog.show()
    dialog.raise_()
    dialog.activateWindow()

    event_loop.exec_()

    result = QDialog.Accepted if dialog.result() == QDialog.Accepted else QDialog.Rejected
    # ========================================================
    # RESULTADO
    # ========================================================

    log_message(
        "================================================"
    )

    log_message(
        f"select_available_items() - "
        f"dialog.exec_() retornou: {result}"
    )

    log_message(
        "================================================"
    )

    # ========================================================
    # CANCELADO
    # ========================================================

    if result != QDialog.Accepted:

        log_message(
            "Seleção de imagens cancelada."
        )

        return None

    # ========================================================
    # RECUPERAR LINHAS
    # ========================================================

    selected_rows = [
        row
        for row, checkbox in enumerate(checkboxes)
        if checkbox.isChecked()
    ]

    selected_items = [
        items[row]
        for row in selected_rows
    ]

    # ========================================================
    # LOG DOS ITENS SELECIONADOS
    # ========================================================

    log_message(
        f"{len(selected_items)} "
        "imagem(ns) selecionada(s):"
    )

    for item in selected_items:

        item_date = (
            item.datetime.isoformat()
            if item.datetime
            else "N/A"
        )

        log_message(
            f"  - ID: {item.id} | "
            f"datetime: {item_date}"
        )

    log_message(
        "================================================"
    )

    return selected_items       
              
# ============================================================
# CONECTAR AO STAC
# ============================================================

def connect_to_stac(
    stac_url: str
):
    """
    Conecta ao catálogo STAC do BDC/INPE.

    Parâmetros
    ----------
    stac_url : str
        URL do catálogo STAC.

    Retorno
    -------
    Client ou None
        Cliente STAC conectado ou None em caso de erro.
    """

    try:

        client = Client.open(
            stac_url
        )

        log_message(
            f"Conectado ao STAC: "
            f"{stac_url}"
        )

        return client

    except Exception as e:

        log_message(
            "Erro ao conectar ao STAC: "
            f"{e}"
        )

        return None
# ============================================================
# IDENTIFICAR SATÉLITE / FAMÍLIA DE CONFIGURAÇÃO
# ============================================================

def identify_satellite(
    item
) -> str:

    item_id = str(
        item.id
    )

    item_upper = (
        item_id.upper()
    )

    # --------------------------------------------------------
    # Landsat
    # --------------------------------------------------------

    if item_upper.startswith(
        "LC08"
    ):

        return "Landsat"

    if item_upper.startswith(
        "LC09"
    ):

        return "Landsat"


    # --------------------------------------------------------
    # Sentinel-2
    # --------------------------------------------------------

    if item_upper.startswith(
        "S2A_"
    ):

        return "Sentinel-2"

    if item_upper.startswith(
        "S2B_"
    ):

        return "Sentinel-2"

    if item_upper.startswith(
        "S2C_"
    ):

        return "Sentinel-2"


    # --------------------------------------------------------
    # Obter collection
    # --------------------------------------------------------

    collection_id = ""

    try:

        collection = (
            item.collection_id
        )

        if collection:

            collection_id = str(
                collection
            )

    except Exception:

        pass

    collection_upper = (
        collection_id.upper()
    )


    # ========================================================
    # AMAZONIA-1
    # ========================================================

    if (
        "AMZ1" in collection_upper
        or "AMAZONIA" in collection_upper
        or "AMZ1" in item_upper
    ):

        return "Amazonia-1"


    # ========================================================
    # CBERS-4A WFI
    # ========================================================
    # IMPORTANTE:
    # Deve vir ANTES do CBERS-4A MUX.
    # ========================================================

    if (
        "CB4A-WFI" in collection_upper
        or "CB4A_WFI" in item_upper
        or "CBERS_4A_WFI" in item_upper
        or "CBERS4A_WFI" in item_upper
    ):

        return "CBERS-4A-WFI"


    # ========================================================
    # CBERS-4A MUX
    # ========================================================

    if (
        "CB4A-MUX" in collection_upper
        or "CB4A_MUX" in item_upper
    ):

        return "CBERS-4A-MUX"


    # ========================================================
    # CBERS-4 WFI
    # ========================================================

    if (
        "CB4-WFI" in collection_upper
        or "CB4_WFI" in item_upper
        or "CBERS_4_WFI" in item_upper
        or "CBERS4_WFI" in item_upper
    ):

        return "CBERS-4-WFI"


    # ========================================================
    # CBERS-4 MUX
    # ========================================================

    if (
        "CB4-MUX" in collection_upper
        or "CB4_MUX" in item_upper
    ):

        return "CBERS-4-MUX"


    # ========================================================
    # NÃO IDENTIFICADO
    # ========================================================

    log_message(
        "Satélite/sensor não identificado."
    )

    log_message(
        f"Item: {item_id}"
    )

    log_message(
        f"Collection: {collection_id}"
    )

    return "Desconhecido"
    
def validate_item_assets(
    item,
    requested_bands: List[str],
    satellite: str
) -> Dict:

    config = get_satellite_config(
        satellite
    )

    available_assets = set(
        item.assets.keys()
    )

    log_message(
        f"Item {item.id} - assets disponíveis: "
        f"{sorted(available_assets)}"
    )

    hrefs = []
    missing = []

    for requested_band in requested_bands:

        requested_band = requested_band.strip()

        if not requested_band:
            continue

        # ----------------------------------------------------
        # Asset informado diretamente
        # ----------------------------------------------------

        if requested_band in item.assets:

            href = item.assets[
                requested_band
            ].href

            if href:

                hrefs.append(
                    f"/vsicurl/{href}"
                )

                continue

        # ----------------------------------------------------
        # Resolver alias semântico
        # ----------------------------------------------------

        resolved = False

        for semantic_name, aliases in (
            config["assets"].items()
        ):

            if (
                requested_band.lower()
                == semantic_name.lower()
            ):

                for alias in aliases:

                    if alias in item.assets:

                        href = item.assets[
                            alias
                        ].href

                        if href:

                            hrefs.append(
                                f"/vsicurl/{href}"
                            )

                            log_message(
                                f"'{requested_band}' "
                                f"resolvido para "
                                f"'{alias}'"
                            )

                            resolved = True

                            break

                if resolved:
                    break

        if not resolved:

            missing.append(
                requested_band
            )

    if missing:

        log_message(
            f"Item {item.id} BLOQUEADO. "
            f"Bandas não disponíveis: "
            f"{missing}"
        )

        return {
            "valid": False,
            "hrefs": [],
            "missing": missing
        }

    return {
        "valid": True,
        "hrefs": hrefs,
        "missing": []
    }

# ============================================================
# V3 - CAMADAS DE FOCO A PARTIR DE KML ONLINE
# ============================================================
KML_FOCUS_URL = (
    "https://dataserver-coids.inpe.br/queimadas/queimadas/"
    "focos/kml/focos_goes_ponto_atencao_48hr/"
    "focos_goes_ponto_atencao_48hr.kml"
)

FOCUS_LAYER_NAMES = [
    "1 até 35 repetições",
    "36 até 71 repetições",
    "72 até 143 repetições",
    "144 até 288 repetições"
]

EVENTOS_ATIVOS_GPKG_URL = (
    "https://dataserver-coids.inpe.br/"
    "queimadas/queimadas/eventos/ativos/"
    "eventos_ativos.gpkg"
)

EVENTOS_ATIVOS_GPKG = os.path.join(
    os.path.dirname(__file__),
    "eventos_ativos.gpkg"
)

def _kml_local_name(element):
    """Retorna o nome local de uma tag XML, ignorando namespace."""

    return element.tag.rsplit("}", 1)[-1]


def _kml_element_text(element):
    """Retorna o texto normalizado de um elemento XML."""

    if element is None or element.text is None:
        return ""

    return element.text.strip()


def _kml_folder_name(folder):
    """Obtém o nome de um Folder KML."""

    for child in folder:

        if _kml_local_name(child) == "name":
            return _kml_element_text(child)

    return ""


def _kml_placemark_points(placemark):
    """
    Extrai todos os pontos Point de um Placemark KML.

    O KML pode utilizar Point diretamente ou Point dentro de
    MultiGeometry. Somente geometrias de ponto são utilizadas
    pela V3.
    """

    points = []

    for element in placemark.iter():

        if _kml_local_name(element) != "Point":
            continue

        coordinates_element = None

        for child in element.iter():

            if _kml_local_name(child) == "coordinates":
                coordinates_element = child
                break

        if coordinates_element is None:
            continue

        coordinates_text = _kml_element_text(
            coordinates_element
        )

        if not coordinates_text:
            continue

        for coordinate_text in coordinates_text.split():

            parts = coordinate_text.split(",")

            if len(parts) < 2:
                continue

            try:
                x = float(parts[0])
                y = float(parts[1])
            except (TypeError, ValueError):
                continue

            points.append((x, y))

    return points
def baixar_eventos_ativos():
    """
    Baixa o GeoPackage de eventos ativos do servidor do INPE.

    O arquivo é salvo em EVENTOS_ATIVOS_GPKG.
    Caso já exista um arquivo local, ele é sobrescrito.
    """

    print()
    print("=" * 70)
    print("DOWNLOAD DOS EVENTOS ATIVOS")
    print("=" * 70)

    print()
    print("Baixando GeoPackage...")
    print(EVENTOS_ATIVOS_GPKG_URL)

    try:

        response = requests.get(
            EVENTOS_ATIVOS_GPKG_URL,
            timeout=120
        )

        response.raise_for_status()

    except requests.RequestException as e:

        raise RuntimeError(
            "Não foi possível baixar o GeoPackage "
            "de eventos ativos:\n"
            f"{e}"
        )

    # --------------------------------------------------------
    # Verificar conteúdo recebido
    # --------------------------------------------------------

    if not response.content:

        raise RuntimeError(
            "O servidor retornou um arquivo vazio."
        )

    # --------------------------------------------------------
    # Garantir diretório
    # --------------------------------------------------------

    diretorio = os.path.dirname(
        EVENTOS_ATIVOS_GPKG
    )

    if diretorio:

        os.makedirs(
            diretorio,
            exist_ok=True
        )

    # --------------------------------------------------------
    # Salvar / sobrescrever arquivo
    # --------------------------------------------------------

    try:

        with open(
            EVENTOS_ATIVOS_GPKG,
            "wb"
        ) as arquivo:

            arquivo.write(
                response.content
            )

    except OSError as e:

        raise RuntimeError(
            "Não foi possível salvar o "
            "GeoPackage localmente:\n"
            f"{EVENTOS_ATIVOS_GPKG}\n"
            f"Erro: {e}"
        )

    # --------------------------------------------------------
    # Resultado
    # --------------------------------------------------------

    print(
        f"✓ Download realizado: "
        f"{len(response.content):,} bytes"
    )

    print(
        f"✓ Arquivo salvo: "
        f"{EVENTOS_ATIVOS_GPKG}"
    )

    return EVENTOS_ATIVOS_GPKG

def ler_eventos_ativos():
    """
    Lê os eventos ativos a partir do GeoPackage remoto,
    previamente baixado para EVENTOS_ATIVOS_GPKG.

    Retorna uma lista contendo os eventos dos tipos:
        - Incêndio
        - Possível início de incêndio

    Os nomes internos dos campos são mantidos compatíveis
    com as etapas seguintes do processamento.
    """

    print()
    print("=" * 70)
    print("LEITURA DOS EVENTOS ATIVOS")
    print("=" * 70)

    print()
    print("Abrindo GeoPackage...")
    print(EVENTOS_ATIVOS_GPKG)

    # --------------------------------------------------------
    # Descobrir camadas do GeoPackage
    # --------------------------------------------------------

    print()
    print("Identificando camadas do GeoPackage...")

    camadas_gpkg = (
        QgsProviderRegistry.instance().querySublayers(
            EVENTOS_ATIVOS_GPKG
        )
    )

    if not camadas_gpkg:

        raise RuntimeError(
            "O GeoPackage foi encontrado, mas nenhuma camada "
            "foi identificada:\n"
            f"{EVENTOS_ATIVOS_GPKG}"
        )

    print()
    print("Camadas encontradas:")

    for sublayer in camadas_gpkg:

        print(
            f"  - {sublayer.name()}"
        )

    # --------------------------------------------------------
    # Abrir especificamente a camada eventos_ativos
    # --------------------------------------------------------

    nome_camada = "eventos_ativos"

    camada = QgsVectorLayer(
        f"{EVENTOS_ATIVOS_GPKG}|layername={nome_camada}",
        nome_camada,
        "ogr"
    )

    if not camada.isValid():

        raise RuntimeError(
            "A camada 'eventos_ativos' foi encontrada, "
            "mas não pôde ser aberta:\n"
            f"{EVENTOS_ATIVOS_GPKG}"
        )

    print()
    print(
        f"✓ Camada carregada: {camada.name()}"
    )

    print(
        f"✓ Feições disponíveis: "
        f"{camada.featureCount()}"
    )

    # --------------------------------------------------------
    # Categorias utilizadas
    # --------------------------------------------------------

    categorias = {
        "Incêndio",
        "Possível início de incêndio"
    }

    eventos = []

    # --------------------------------------------------------
    # Ler feições
    # --------------------------------------------------------

    for feature in camada.getFeatures():

        tipo_de_fogo = feature["tipo_fogo"]

        if tipo_de_fogo not in categorias:
            continue

        geometry = feature.geometry()

        if geometry is None or geometry.isEmpty():
            continue

        # ----------------------------------------------------
        # Validar geometria
        # ----------------------------------------------------

        if not geometry.isGeosValid():

            geometry = geometry.makeValid()

        if geometry is None or geometry.isEmpty():
            continue

        # ----------------------------------------------------
        # Identificação do evento
        # ----------------------------------------------------

        id_evento = feature["id_evento"]

        nome_evento = (
            f"Evento {id_evento}"
        )

        # ----------------------------------------------------
        # Criar estrutura compatível com o restante do código
        # ----------------------------------------------------

        evento = {

            "nome": nome_evento,

            "id_evento": id_evento,

            "tipo_de_fogo": tipo_de_fogo,

            "tipo_fogo": feature["tipo_fogo"],

            "id_tipo_fogo": feature["id_tipo_fogo"],

            "id_status": feature["id_status"],

            "status_nome": feature["status_nome"],

            "data_inicio": feature["data_min"],

            "data_fim": feature["data_max"],

            "duracao": feature["duracao_dias"],

            "area_ha": feature["area_ha"],

            "municipio": feature["municipios"],

            "estado": feature["estados"],

            "max_dias_sem_chuva": (
                feature["max_dias_sem_chuva"]
            ),

            "frentes_ativas": feature["qtd_frente"],

            "desmatamento": feature["desmatamento_pct"],

            "vegetacao": feature["vegetacao_pct"],

            "transicao": feature["transicao_pct"],

            # Campos que não existem no GeoPackage atual
            "total_focos": None,

            "dias_com_foco": None,

            "ultimo_foco": None,

            "geometry": geometry
        }

        eventos.append(
            evento
        )

    # --------------------------------------------------------
    # Resumo
    # --------------------------------------------------------

    qtd_incendio = sum(
        1
        for evento in eventos
        if evento["tipo_de_fogo"] == "Incêndio"
    )

    qtd_possivel = sum(
        1
        for evento in eventos
        if evento["tipo_de_fogo"]
        == "Possível início de incêndio"
    )

    print()
    print("-" * 70)
    print("RESULTADO")
    print("-" * 70)

    print(
        f"Total de polígonos: {len(eventos)}"
    )

    print(
        f"  Incêndio: {qtd_incendio}"
    )

    print(
        f"  Possível início de incêndio: "
        f"{qtd_possivel}"
    )

    return eventos

def criar_buffer_eventos(
    relacoes,
    buffer_metros=2000.0
):
    """
    Cria um buffer métrico ao redor dos polígonos dos eventos
    relacionados às feições GOES.

    O buffer é criado em CRS projetado para garantir que
    a distância esteja em metros.

    Retorna os eventos com suas geometrias bufferizadas
    em WGS84.
    """

    print()
    print("=" * 70)
    print("CRIAÇÃO DO BUFFER DOS EVENTOS")
    print("=" * 70)

    if not relacoes:
        raise ValueError(
            "Nenhuma relação GOES × evento foi encontrada."
        )

    # --------------------------------------------------------
    # CRS
    # --------------------------------------------------------

    crs_wgs84 = QgsCoordinateReferenceSystem(
        "EPSG:4326"
    )

    # --------------------------------------------------------
    # Identificar UTM adequada
    # --------------------------------------------------------

    todas_geometrias = []

    for relacao in relacoes:

        evento = relacao["evento"]
        geometry = evento["geometry"]

        if geometry is not None and not geometry.isEmpty():
            todas_geometrias.append(
                geometry
            )

    if not todas_geometrias:
        raise ValueError(
            "Nenhuma geometria válida de evento foi encontrada."
        )

    # União das geometrias apenas para determinar a localização
    extent = todas_geometrias[0].boundingBox()

    for geometry in todas_geometrias[1:]:
        extent.combineExtentWith(
            geometry.boundingBox()
        )

    centro_x = extent.center().x()
    centro_y = extent.center().y()

    zona_utm = int(
        (centro_x + 180) / 6
    ) + 1

    epsg_utm = (
        32600 + zona_utm
        if centro_y >= 0
        else 32700 + zona_utm
    )

    crs_utm = QgsCoordinateReferenceSystem(
        f"EPSG:{epsg_utm}"
    )

    print()
    print(
        f"CRS métrico utilizado: EPSG:{epsg_utm}"
    )

    print(
        f"Buffer: {buffer_metros} metros"
    )

    # --------------------------------------------------------
    # Transformadores
    # --------------------------------------------------------

    transform_wgs84_to_utm = (
        QgsCoordinateTransform(
            crs_wgs84,
            crs_utm,
            QgsProject.instance()
        )
    )

    transform_utm_to_wgs84 = (
        QgsCoordinateTransform(
            crs_utm,
            crs_wgs84,
            QgsProject.instance()
        )
    )

    # --------------------------------------------------------
    # Criar buffers
    # --------------------------------------------------------

    eventos_buffer = []

    for relacao in relacoes:

        evento = relacao["evento"]

        geometry = evento["geometry"]

        if geometry is None or geometry.isEmpty():
            continue

        try:

            geometry_utm = QgsGeometry(
                geometry
            )

            geometry_utm.transform(
                transform_wgs84_to_utm
            )

            buffer_utm = geometry_utm.buffer(
                buffer_metros,
                50
            )

            if buffer_utm is None:
                continue

            if buffer_utm.isEmpty():
                continue

            buffer_wgs84 = QgsGeometry(
                buffer_utm
            )

            buffer_wgs84.transform(
                transform_utm_to_wgs84
            )

            # --------------------------------------------
            # Copiar atributos do evento
            # --------------------------------------------

            resultado = dict(evento)

            resultado["geometry"] = buffer_wgs84

            resultado["focus_id"] = (
                relacao["focus_id"]
            )

            resultado["focus_layer"] = (
                relacao["focus_layer"]
            )

            resultado["relacao"] = (
                relacao["relacao"]
            )

            if "distancia" in relacao:
                resultado["distancia"] = (
                    relacao["distancia"]
                )

            eventos_buffer.append(
                resultado
            )

        except Exception as e:

            print(
                f"[AVISO] Erro ao criar buffer "
                f"do evento {evento.get('nome', '')}: {e}"
            )

    # --------------------------------------------------------
    # Resultado
    # --------------------------------------------------------

    print()
    print("-" * 70)
    print("RESULTADO")
    print("-" * 70)

    print(
        f"Eventos relacionados: {len(relacoes)}"
    )

    print(
        f"Buffers criados: {len(eventos_buffer)}"
    )

    # --------------------------------------------------------
    # Inspeção
    # --------------------------------------------------------

    for evento in eventos_buffer[:5]:

        geometry = evento["geometry"]

        print()
        print(
            f"Evento: {evento['nome']}"
        )

        print(
            f"GOES: Foco {evento['focus_id']}"
        )

        print(
            f"Relação: {evento['relacao']}"
        )

        print(
            f"Geometria válida: "
            f"{geometry.isGeosValid()}"
        )

        print(
            f"Geometria vazia: "
            f"{geometry.isEmpty()}"
        )

        print(
            f"Tipo: {geometry.type()}"
        )

        print(
            f"Área do buffer: "
            f"{geometry.area()}"
        )

    return eventos_buffer

def criar_camada_eventos_bufferizados(
    eventos_buffer,
    nome_camada="Eventos Ativos - Buffer 2 km"
):
    """
    Cria uma camada temporária em memória com os eventos
    bufferizados.

    Mantém os atributos do evento e os atributos da relação
    com a feição GOES.
    """

    print()
    print("=" * 70)
    print("CRIANDO CAMADA TEMPORÁRIA DOS EVENTOS BUFFERIZADOS")
    print("=" * 70)

    if not eventos_buffer:
        raise ValueError(
            "Nenhum evento bufferizado foi encontrado."
        )

    # --------------------------------------------------------
    # Campos da camada
    # --------------------------------------------------------

    fields = QgsFields()

    fields.append(
        QgsField("focus_id", QVariant.Int)
    )

    fields.append(
        QgsField("focus_layer", QVariant.String)
    )

    fields.append(
        QgsField("relacao", QVariant.String)
    )

    fields.append(
        QgsField("evento", QVariant.String)
    )

    fields.append(
        QgsField("tipo_de_fogo", QVariant.String)
    )

    fields.append(
        QgsField("data_inicio", QVariant.String)
    )

    fields.append(
        QgsField("data_fim", QVariant.String)
    )

    fields.append(
        QgsField("duracao", QVariant.String)
    )

    fields.append(
        QgsField("municipio", QVariant.String)
    )

    fields.append(
        QgsField("estado", QVariant.String)
    )

    fields.append(
        QgsField("max_dias_sem_chuva", QVariant.String)
    )

    fields.append(
        QgsField("total_focos", QVariant.String)
    )

    fields.append(
        QgsField("dias_com_foco", QVariant.String)
    )

    fields.append(
        QgsField("ultimo_foco", QVariant.String)
    )

    fields.append(
        QgsField("frentes_ativas", QVariant.String)
    )

    fields.append(
        QgsField("desmatamento", QVariant.String)
    )

    fields.append(
        QgsField("vegetacao", QVariant.String)
    )

    fields.append(
        QgsField("transicao", QVariant.String)
    )

    fields.append(
        QgsField("distancia", QVariant.Double)
    )

    # --------------------------------------------------------
    # Criar camada
    # --------------------------------------------------------

    camada_buffer = QgsVectorLayer(
        "Polygon?crs=EPSG:4326",
        nome_camada,
        "memory"
    )

    if not camada_buffer.isValid():
        raise RuntimeError(
            "Não foi possível criar a camada temporária "
            "dos eventos bufferizados."
        )

    provider = (
        camada_buffer.dataProvider()
    )

    provider.addAttributes(
        fields
    )

    camada_buffer.updateFields()

    # --------------------------------------------------------
    # Criar feições
    # --------------------------------------------------------

    features = []

    for evento in eventos_buffer:

        geometry = evento.get(
            "geometry"
        )

        if geometry is None:
            continue

        if geometry.isEmpty():
            continue

        feature = QgsFeature(
            camada_buffer.fields()
        )

        feature.setGeometry(
            geometry
        )

        feature.setAttribute(
            "focus_id",
            evento.get("focus_id")
        )

        feature.setAttribute(
            "focus_layer",
            evento.get("focus_layer")
        )

        feature.setAttribute(
            "relacao",
            evento.get("relacao")
        )

        feature.setAttribute(
            "evento",
            evento.get("nome")
        )

        feature.setAttribute(
            "tipo_de_fogo",
            evento.get("tipo_de_fogo")
        )

        feature.setAttribute(
            "data_inicio",
            evento.get("data_inicio")
        )

        feature.setAttribute(
            "data_fim",
            evento.get("data_fim")
        )

        feature.setAttribute(
            "duracao",
            evento.get("duracao")
        )

        feature.setAttribute(
            "municipio",
            evento.get("municipio")
        )

        feature.setAttribute(
            "estado",
            evento.get("estado")
        )

        feature.setAttribute(
            "max_dias_sem_chuva",
            evento.get("max_dias_sem_chuva")
        )

        feature.setAttribute(
            "total_focos",
            evento.get("total_focos")
        )

        feature.setAttribute(
            "dias_com_foco",
            evento.get("dias_com_foco")
        )

        feature.setAttribute(
            "ultimo_foco",
            evento.get("ultimo_foco")
        )

        feature.setAttribute(
            "frentes_ativas",
            evento.get("frentes_ativas")
        )

        feature.setAttribute(
            "desmatamento",
            evento.get("desmatamento")
        )

        feature.setAttribute(
            "vegetacao",
            evento.get("vegetacao")
        )

        feature.setAttribute(
            "transicao",
            evento.get("transicao")
        )

        feature.setAttribute(
            "distancia",
            evento.get("distancia")
        )

        features.append(
            feature
        )

    # --------------------------------------------------------
    # Adicionar feições
    # --------------------------------------------------------

    if features:

        result = provider.addFeatures(
            features
        )

        if not result[0]:
            raise RuntimeError(
                "Erro ao adicionar as feições "
                "à camada temporária."
            )

    camada_buffer.updateExtents()

    # --------------------------------------------------------
    # Adicionar ao projeto
    # --------------------------------------------------------

    QgsProject.instance().addMapLayer(
        camada_buffer
    )

    # --------------------------------------------------------
    # Resultado
    # --------------------------------------------------------

    print()
    print("-" * 70)
    print("CAMADA CRIADA")
    print("-" * 70)

    print(
        f"Nome: {camada_buffer.name()}"
    )

    print(
        f"Feições: {camada_buffer.featureCount()}"
    )

    print(
        f"CRS: {camada_buffer.crs().authid()}"
    )

    print()
    print(
        "✓ Camada adicionada ao projeto QGIS."
    )

    return camada_buffer

def criar_intersects_buffer_eventos(
    eventos_buffer
):
    """
    Cria uma geometria GeoJSON única a partir dos
    buffers dos eventos ativos para utilização
    como filtro espacial na consulta STAC.
    """

    if not eventos_buffer:
        raise ValueError(
            "Nenhum buffer de evento foi fornecido."
        )

    geometries = []

    for evento in eventos_buffer:

        geometry = evento.get("geometry")

        if geometry is None:
            continue

        if geometry.isEmpty():
            continue

        if not geometry.isGeosValid():
            geometry = geometry.makeValid()

        if geometry.isEmpty():
            continue

        geometries.append(
            geometry
        )

    if not geometries:
        raise ValueError(
            "Nenhuma geometria válida foi encontrada "
            "nos buffers dos eventos."
        )

    # --------------------------------------------------------
    # Unir os buffers
    # --------------------------------------------------------

    geometry_unificada = (
        QgsGeometry.unaryUnion(
            geometries
        )
    )

    if geometry_unificada is None:
        raise ValueError(
            "Não foi possível unir as geometrias "
            "dos buffers."
        )

    if geometry_unificada.isEmpty():
        raise ValueError(
            "A geometria unificada dos buffers "
            "está vazia."
        )

    # --------------------------------------------------------
    # Converter para GeoJSON
    # --------------------------------------------------------

    geojson = json.loads(
        geometry_unificada.asJson()
    )

    return {
        "type": geojson["type"],
        "coordinates": geojson["coordinates"]
    }

def download_focus_kml(output_dir: str) -> str:
    """
    Baixa o KML de focos para o diretório de saída.

    O arquivo completo é preservado no disco, mantendo todas as
    subcamadas existentes no KML original.
    """

    if not output_dir:
        raise ValueError("Diretório de saída não informado para o KML de focos.")

    os.makedirs(output_dir, exist_ok=True)

    filename = "focos_goes_ponto_atencao_48hr.kml"
    output_path = os.path.join(output_dir, filename)

    log_message("================================================")
    log_message("DOWNLOAD DO KML DE FOCOS")
    log_message(f"Origem: {KML_FOCUS_URL}")
    log_message(f"Destino: {output_path}")

    try:
        response = requests.get(
            KML_FOCUS_URL,
            timeout=60
        )
        response.raise_for_status()

        with open(output_path, "wb") as file:
            file.write(response.content)

    except requests.RequestException as e:
        raise RuntimeError(
            "Não foi possível baixar o KML de focos. "
            f"Erro: {e}"
        )
    except OSError as e:
        raise RuntimeError(
            "Não foi possível salvar o KML de focos no diretório "
            f"'{output_dir}'. Erro: {e}"
        )

    log_message(
        f"KML baixado com sucesso: {output_path}"
    )
    log_message(
        f"Tamanho: {os.path.getsize(output_path):,} bytes"
    )
    log_message("================================================")

    return output_path


def load_selected_focus_kml_layers_to_project(
    kml_path: str,
    selected_layer_names: List[str]
):
    """
    Abre no projeto QGIS somente as subcamadas de foco selecionadas
    a partir do KML que foi salvo localmente.
    """

    if not kml_path or not os.path.exists(kml_path):
        raise FileNotFoundError(
            f"KML local não encontrado: {kml_path}"
        )

    if not selected_layer_names:
        return []

    log_message("================================================")
    log_message("ABERTURA DAS CAMADAS DE FOCO NO PROJETO QGIS")
    log_message(f"KML local: {kml_path}")
    log_message(
        f"Camadas solicitadas: {selected_layer_names}"
    )

    try:
        sublayers = QgsProviderRegistry.instance().querySublayers(
            kml_path
        )
    except Exception as e:
        raise RuntimeError(
            "Não foi possível identificar as subcamadas do KML "
            f"com o QGIS/OGR. Erro: {e}"
        )

    available = {}

    for sublayer in sublayers:
        name = sublayer.name().strip()
        available[name] = sublayer
        log_message(
            f"Subcamada disponível no KML: '{name}'"
        )

    loaded_layers = []

    project = QgsProject.instance()

    for layer_name in selected_layer_names:

        sublayer = available.get(layer_name)

        if sublayer is None:
            log_message(
                f"AVISO: subcamada não encontrada para abertura: "
                f"'{layer_name}'"
            )
            continue

        # URI retornada pelo próprio provider OGR.
        uri = sublayer.uri()

        layer = QgsVectorLayer(
            uri,
            layer_name,
            "ogr"
        )

        if not layer.isValid():
            log_message(
                f"ERRO: não foi possível abrir a camada "
                f"'{layer_name}' no QGIS."
            )
            continue

        # --------------------------------------------------------
        # Verificar se a camada já está no projeto
        # --------------------------------------------------------
        existing_layers = project.mapLayersByName(layer_name)

        existing_layer_found = None

        for existing_layer in existing_layers:

            if existing_layer.source() == layer.source():

                existing_layer_found = existing_layer

                log_message(
                    f"Camada já estava no projeto: "
                    f"'{layer_name}'"
                )

                break

        # --------------------------------------------------------
        # Se já existe no projeto, utiliza a existente
        # --------------------------------------------------------
        if existing_layer_found is not None:

            layer = existing_layer_found

        # --------------------------------------------------------
        # Caso contrário, cria a versão editável em memória
        # --------------------------------------------------------
        else:

            layer = add_id_field(layer)

            project.addMapLayer(layer)

            # --------------------------------------------------------
            # Configurar rótulo da ID do foco
            # --------------------------------------------------------

            layer.setLabelsEnabled(True)

            label_settings = QgsPalLayerSettings()
            label_settings.fieldName = "id"

            text_format = QgsTextFormat()
            text_format.setFont(
                QFont("Arial", 10)
            )

            label_settings.setFormat(text_format)

            label_layer_settings = QgsVectorLayerSimpleLabeling(
                label_settings
            )

            layer.setLabeling(
                label_layer_settings
            )

            layer.triggerRepaint()

            log_message(
                f"✓ Camada com ID adicionada ao projeto: "
                f"'{layer_name}'"
            )

            log_message(
                f"✓ Camada com ID adicionada ao projeto: "
                f"'{layer_name}'"
            )

        loaded_layers.append(layer)

    if loaded_layers:
        iface.mapCanvas().refresh()

    log_message(
        f"Total de camadas abertas no projeto: {len(loaded_layers)}"
    )
    log_message("================================================")

    return loaded_layers


def get_focus_layers_from_kml() -> Dict[str, List[Dict]]:
    """
    Baixa o KML online e identifica as três camadas de foco
    pelos mesmos nomes utilizados anteriormente no projeto QGIS.

    Retorno:
        {
            nome_da_camada: [
                {
                    "feature_id": ...,
                    "x": ...,
                    "y": ...
                },
                ...
            ]
        }
    """

    log_message("================================================")
    log_message("LEITURA DAS CAMADAS DE FOCO A PARTIR DO KML")
    log_message(f"URL: {KML_FOCUS_URL}")

    try:
        response = requests.get(
            KML_FOCUS_URL,
            timeout=60
        )

        response.raise_for_status()

    except requests.RequestException as e:

        raise RuntimeError(
            "Não foi possível acessar o KML online de focos. "
            f"Erro: {e}"
        )

    try:
        root = ET.fromstring(
            response.content
        )

    except ET.ParseError as e:

        raise RuntimeError(
            "O conteúdo retornado pela URL não é um KML válido. "
            f"Erro de XML: {e}"
        )

    available = {}

    # Localiza todos os Folder e procura pelos três nomes
    # exatamente como definidos em FOCUS_LAYER_NAMES.
    folders = [
        element
        for element in root.iter()
        if _kml_local_name(element) == "Folder"
    ]

    for layer_name in FOCUS_LAYER_NAMES:

        matching_folders = [
            folder
            for folder in folders
            if _kml_folder_name(folder) == layer_name
        ]

        if not matching_folders:

            log_message(
                f"Camada KML não encontrada: {layer_name}"
            )

            continue

        records = []

        for folder in matching_folders:

            for element in folder.iter():

                if _kml_local_name(element) != "Placemark":
                    continue

                placemark_name = ""

                placemark_id = element.attrib.get("id")

                for child in element:

                    if _kml_local_name(child) == "name":
                        placemark_name = _kml_element_text(child)
                        break

                points = _kml_placemark_points(
                    element
                )

                for x, y in points:

                    records.append({
                        "id": len(records) + 1,
                        "feature_id": (
                            placemark_id
                            or placemark_name
                            or len(records) + 1
                        ),
                        "placemark_name": placemark_name,
                        "x": float(x),
                        "y": float(y)
                    })

        if records:

            available[layer_name] = records

            log_message(
                f"Camada encontrada: {layer_name} | "
                f"{len(records)} ponto(s)"
            )

        else:

            log_message(
                f"Camada encontrada, mas sem pontos válidos: "
                f"{layer_name}"
            )

    if not available:

        raise ValueError(
            "Nenhuma das três camadas de foco esperadas "
            "foi encontrada no KML online."
        )

    log_message(
        f"Total de camadas disponíveis: {len(available)}"
    )
    log_message("================================================")

    return available

def add_id_field(layer):
    """
    Cria uma cópia editável da camada em memória e adiciona
    um campo 'id' sequencial às feições.

    Retorna a nova camada em memória.
    """

    # --------------------------------------------------------
    # Criar camada em memória
    # --------------------------------------------------------
    memory_layer = QgsVectorLayer(
        f"{QgsWkbTypes.displayString(layer.wkbType())}"
        f"?crs={layer.crs().authid()}",
        layer.name(),
        "memory"
    )

    if not memory_layer.isValid():
        raise RuntimeError(
            f"Não foi possível criar a camada em memória "
            f"'{layer.name()}'."
        )

    # --------------------------------------------------------
    # Copiar os campos originais
    # --------------------------------------------------------
    provider = memory_layer.dataProvider()

    original_fields = layer.fields()

    provider.addAttributes(
        list(original_fields)
    )

    memory_layer.updateFields()

    # --------------------------------------------------------
    # Criar o campo ID
    # --------------------------------------------------------
    field_name = "id"

    field_index = memory_layer.fields().indexOf(field_name)

    if field_index == -1:

        provider.addAttributes([
            QgsField(field_name, QVariant.Int)
        ])

        memory_layer.updateFields()

        field_index = memory_layer.fields().indexOf(
            field_name
        )

    # --------------------------------------------------------
    # Copiar as feições e preencher o ID
    # --------------------------------------------------------
    features = []

    value = 1

    for feature in layer.getFeatures():

        new_feature = QgsFeature(
            memory_layer.fields()
        )

        # Copiar geometria
        new_feature.setGeometry(
            feature.geometry()
        )

        # Copiar atributos originais
        attributes = list(feature.attributes())

        # Adicionar o ID
        attributes.append(value)

        new_feature.setAttributes(attributes)

        features.append(new_feature)

        value += 1

    # --------------------------------------------------------
    # Adicionar as feições à camada em memória
    # --------------------------------------------------------
    success, added_features = provider.addFeatures(
        features
    )

    if not success:
        raise RuntimeError(
            f"Não foi possível adicionar as feições "
            f"à camada em memória '{layer.name()}'."
        )

    memory_layer.updateExtents()

    return memory_layer

def extract_focus_points_wgs84(
    selected_focus_layers: Dict[str, List[Dict]]
):
    """Prepara as feições selecionadas para a consulta STAC."""

    point_records = []
    coordinates = []

    for layer_name, records in selected_focus_layers.items():
        for record in records:
            try:
                x = float(record["x"])
                y = float(record["y"])
                focus_id = int(record["id"])
            except (KeyError, TypeError, ValueError) as e:
                log_message(
                    f"[DEBUG ID] Registro inválido em '{layer_name}': {e}"
                )
                continue

            point_record = dict(record)
            point_record["layer"] = layer_name
            point_record["id"] = focus_id
            point_record["x"] = x
            point_record["y"] = y

            point_records.append(point_record)
            coordinates.append([x, y])

    if not point_records:
        raise ValueError(
            "Nenhuma feição de foco válida foi encontrada nas camadas selecionadas."
        )

    intersects_geometry = {
        "type": "MultiPoint",
        "coordinates": coordinates
    }

    log_message(
        f"[DEBUG ID] Feições preparadas para STAC: {len(point_records)}"
    )

    return intersects_geometry, point_records

def relacionar_goes_eventos(
    point_records,
    eventos
):
    """
    Relaciona cada feição GOES aos eventos ativos.

    Regra:
    1. Primeiro procura eventos que intersectam o ponto GOES.
    2. Se não houver interseção, seleciona o evento
       geometricamente mais próximo.
    """

    print()
    print("=" * 70)
    print("RELAÇÃO GOES × EVENTOS ATIVOS")
    print("=" * 70)

    resultados = []

    qtd_intersecao = 0
    qtd_vizinho = 0

    # --------------------------------------------------------
    # Preparar eventos com geometria válida
    # --------------------------------------------------------

    eventos_validos = []

    for evento in eventos:

        geometry = evento.get("geometry")

        if geometry is None:
            continue

        if geometry.isEmpty():
            continue

        if not geometry.isGeosValid():
            geometry = geometry.makeValid()

        if geometry.isEmpty():
            continue

        evento_temp = dict(evento)
        evento_temp["geometry"] = geometry

        eventos_validos.append(
            evento_temp
        )

    # --------------------------------------------------------
    # Relacionar cada GOES
    # --------------------------------------------------------

    for point_record in point_records:

        try:

            focus_id = int(
                point_record["id"]
            )

            x = float(
                point_record["x"]
            )

            y = float(
                point_record["y"]
            )

        except (KeyError, TypeError, ValueError):

            continue

        ponto = QgsGeometry.fromPointXY(
            QgsPointXY(x, y)
        )

        candidatos_intersecao = []

        # ----------------------------------------------------
        # Procurar interseções
        # ----------------------------------------------------

        for evento in eventos_validos:

            geometry = evento["geometry"]

            if geometry.intersects(ponto):

                candidatos_intersecao.append(
                    evento
                )

        # ----------------------------------------------------
        # Se houver interseção
        # ----------------------------------------------------

        if candidatos_intersecao:

            for evento in candidatos_intersecao:

                resultado = {
                    "evento": evento,
                    "focus_id": focus_id,
                    "focus_layer": point_record.get("layer"),
                    "relacao": "interseção",
                    "distancia": 0.0
                }
                resultados.append(
                    resultado
                )

                qtd_intersecao += 1

        # ----------------------------------------------------
        # Se não houver interseção:
        # vizinho mais próximo
        # ----------------------------------------------------

        else:

            if not eventos_validos:
                continue

            evento_mais_proximo = min(
                eventos_validos,
                key=lambda evento:
                    ponto.distance(
                        evento["geometry"]
                    )
            )

            distancia = ponto.distance(
                evento_mais_proximo["geometry"]
            )

            resultado = {
                "evento": evento_mais_proximo,
                "focus_id": focus_id,
                "focus_layer": point_record.get("layer"),
                "relacao": "vizinho_mais_proximo",
                "distancia": distancia
            }

            resultados.append(
                resultado
            )

            qtd_vizinho += 1

    # --------------------------------------------------------
    # Resultado
    # --------------------------------------------------------

    print()
    print("-" * 70)
    print("RESULTADO")
    print("-" * 70)

    print(
        f"Feições GOES analisadas: "
        f"{len(point_records)}"
    )

    print(
        f"Relações por interseção: "
        f"{qtd_intersecao}"
    )

    print(
        f"Relações por vizinho mais próximo: "
        f"{qtd_vizinho}"
    )

    print(
        f"Total de relações: "
        f"{len(resultados)}"
    )

    return resultados

def remover_relacoes_duplicadas(relacoes):
    """
    Remove relações duplicadas GOES × evento.

    Mantém uma única relação quando:
    - mesmo focus_id
    - mesmo evento
    - mesma relação espacial
    """

    print()
    print("=" * 70)
    print("REMOVENDO RELAÇÕES DUPLICADAS")
    print("=" * 70)

    unicas = []
    existentes = set()

    for relacao in relacoes:

        evento = relacao["evento"]

        chave = (
            relacao["focus_id"],
            evento["nome"],
            relacao["relacao"]
        )

        if chave in existentes:
            continue

        existentes.add(chave)

        unicas.append(
            relacao
        )

    print(
        f"Relações originais: {len(relacoes)}"
    )

    print(
        f"Relações únicas: {len(unicas)}"
    )

    return unicas

def _item_geometry_qgis(item):
    """Converte a geometria GeoJSON de um Item STAC para QgsGeometry."""

    if not item.geometry:
        return None

    try:
        return QgsJsonUtils.geometryFromGeoJson(
            json.dumps(item.geometry)
        )

    except Exception as e:

        log_message(
            f"Não foi possível converter a geometria "
            f"do item {item.id}: {e}"
        )

        return None


def _count_item_focus_points(
    item,
    point_records
):
    """Conta quais feições de foco intersectam a geometria do item STAC."""

    item_geometry = _item_geometry_qgis(item)

    if item_geometry is None or item_geometry.isEmpty():
        return []

    covered = []

    for record in point_records:

        point = QgsGeometry.fromPointXY(
            QgsPointXY(
                record["x"],
                record["y"]
            )
        )

        try:

            if item_geometry.intersects(point):
                covered.append(record)

        except Exception:
            continue

    return covered


# ============================================================
# BUSCAR ITENS STAC POR FEIÇÕES - V3
# ============================================================

def search_items_by_features(
    client,
    intersects_geometry: Dict,
    point_records: List[Dict],
    start_date: str,
    end_date: str,
    collections: List[str]
) -> tuple:

    log_message("================================================")
    log_message("CONSULTA STAC V3 POR FEIÇÕES")
    log_message(f"Collections: {collections}")
    log_message("Spatial filter: intersects")
    log_message("Geometry type: buffer dos eventos")
    log_message(f"Datetime: {start_date}/{end_date}")

    if not intersects_geometry:
        log_message("ERRO: geometria espacial não informada.")
        return []

    if not collections:
        log_message("ERRO: nenhuma collection foi informada.")
        return []

    datetime_range = f"{start_date}/{end_date}"

    try:

        log_message("Limit: 100")
        log_message(
    "Executando client.search(intersects=buffer dos eventos)...")

        search = client.search(
            collections=collections,
            intersects=intersects_geometry,
            datetime=datetime_range,
            limit=100
        )

        items = list(search.items())

        log_message(
            f"Total de itens retornados pelo STAC: {len(items)}"
        )

        valid_items = []
        covered_focuses_by_item = {}

        for item in items:

            covered = _count_item_focus_points(
                item,
                point_records
            )

            covered_focuses_by_item[item.id] = covered

            log_message(
                f"Item: {item.id} | "
                f"datetime: {item.datetime} | "
                f"feições cobertas: {len(covered)}"
            )

            if covered:
                valid_items.append(item)
                ids = ", ".join(
                    str(record.get("id"))
                    for record in covered
                )
                
            else:
                log_message(
                    f"[DEBUG FOOTPRINT] ✗ Item descartado: "
                    f"não intersecta nenhuma feição."
                )

        log_message(
            f"Itens mantidos após validação espacial: {len(valid_items)}"
        )
        log_message("================================================")

        return valid_items, covered_focuses_by_item

    except Exception as e:

        log_message(
            "ERRO durante consulta STAC V3: "
            f"{e}"
        )

        log_message(
            "================================================"
        )

        return [], {}
        
# ============================================================
# EXPORTAR FOOTPRINTS DAS IMAGENS SELECIONADAS
# ============================================================

def export_selected_footprints(
    selected_items,
    output_dir,
    point_records,
    layer_name="footprints_imagens",
    covered_focuses_by_item: Dict = None,
    eventos_buffer: List[Dict] = None
):
    """
    Cria e salva os footprints das imagens STAC selecionadas
    diretamente em um GeoPackage.

    O campo focus_ids registra os IDs das feições intersectadas.

    O arquivo será:
        <output_dir>/footprints_imagens.gpkg

    A camada será:
        footprints_imagens
    """

    if not selected_items:
        log_message(
            "Nenhuma imagem selecionada para gerar footprints."
        )
        return None

    if not output_dir:
        log_message(
            "ERRO: diretório de saída não informado."
        )
        return None

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    gpkg_path = os.path.join(
        output_dir,
        f"{layer_name}.gpkg"
    )

    log_message(
        "================================================"
    )
    log_message(
        "CRIANDO GPKG DE FOOTPRINTS"
    )
    log_message(
        f"Arquivo: {gpkg_path}"
    )

    # --------------------------------------------------------
    # Criar camada temporária em memória
    # --------------------------------------------------------

    layer = QgsVectorLayer(
        "MultiPolygon?crs=EPSG:4326",
        layer_name,
        "memory"
    )

    if not layer.isValid():
        log_message(
            "ERRO: não foi possível criar a camada temporária."
        )
        return None

    provider = layer.dataProvider()

    provider.addAttributes([
        QgsField("stac_id", QVariant.String),
        QgsField("datetime", QVariant.String),
        QgsField("satellite", QVariant.String),
        QgsField("collection", QVariant.String),
        QgsField("cloud", QVariant.Double),
        QgsField("tile", QVariant.String),
        QgsField("focus_ids", QVariant.String)
    ])

    layer.updateFields()

    # --------------------------------------------------------
    # Criar features
    # --------------------------------------------------------

    features = []

    for item in selected_items:

        log_message(
            f"Processando footprint: {item.id}"
        )

        # ----------------------------------------------------
        # Verificar geometria STAC
        # ----------------------------------------------------

        if not item.geometry:
            log_message(
                f"AVISO: item sem geometria: {item.id}"
            )
            continue

        # ----------------------------------------------------
        # Converter GeoJSON para QgsGeometry
        # ----------------------------------------------------

        try:

            geometry_json = json.dumps(
                item.geometry
            )

            geometry = QgsJsonUtils.geometryFromGeoJson(
                geometry_json
            )

        except Exception as e:

            log_message(
                f"ERRO convertendo geometria "
                f"{item.id}: {e}"
            )

            continue

        if geometry is None:
            log_message(
                f"AVISO: geometria None: {item.id}"
            )
            continue

        if geometry.isEmpty():
            log_message(
                f"AVISO: geometria vazia: {item.id}"
            )
            continue

        # ----------------------------------------------------
        # Verificar se é polígono
        # ----------------------------------------------------

        try:

            if geometry.type() != QgsWkbTypes.PolygonGeometry:

                log_message(
                    f"AVISO: geometria não poligonal: "
                    f"{item.id}"
                )

                continue

        except Exception as e:

            log_message(
                f"ERRO verificando geometria "
                f"{item.id}: {e}"
            )

            continue

        # ----------------------------------------------------
        # Usar geometria STAC diretamente
        # ----------------------------------------------------

        multipolygon = geometry

        if (
            multipolygon is None
            or multipolygon.isEmpty()
        ):

            log_message(
                f"AVISO: geometria vazia: {item.id}"
            )

            continue    

        # ----------------------------------------------------
        # Identificar satélite
        # ----------------------------------------------------

        try:

            satellite = identify_satellite(
                item
            )

        except Exception:

            satellite = "Desconhecido"

        # ----------------------------------------------------
        # Collection
        # ----------------------------------------------------

        try:

            collection = (
                str(item.collection_id)
                if item.collection_id
                else ""
            )

        except Exception:

            collection = ""

        # ----------------------------------------------------
        # Data/hora
        # ----------------------------------------------------

        try:

            datetime_value = (
                item.datetime.isoformat()
                if item.datetime
                else ""
            )

        except Exception:

            datetime_value = ""

        # ----------------------------------------------------
        # Cloud cover
        # ----------------------------------------------------

        cloud_cover = None

        try:

            cloud_value = item.properties.get(
                "eo:cloud_cover"
            )

            if cloud_value is not None:

                cloud_cover = float(
                    cloud_value
                )

        except Exception:

            cloud_cover = None

        # ----------------------------------------------------
        # Tile
        # ----------------------------------------------------

        try:

            tile = get_item_tile(
                item,
                satellite
            )

        except Exception:

            tile = "N/A"

        # ----------------------------------------------------
        # IDs das feições cobertas pelo footprint
        # ----------------------------------------------------

        covered_focuses = (
            covered_focuses_by_item.get(item.id, [])
            if covered_focuses_by_item is not None
            else _count_item_focus_points(
                item,
                point_records
            )
        )

        focus_ids = ", ".join(
            str(record.get("id"))
            for record in covered_focuses
        )

        # --------------------------------------------------------
        # Recortar footprint pela extensão dos buffers dos eventos
        # --------------------------------------------------------

        footprint_recortado = multipolygon

        if eventos_buffer and covered_focuses:

            buffers_item = []

            focus_ids_item = {
                record.get("id")
                for record in covered_focuses
            }

            for evento_buffer in eventos_buffer:

                if evento_buffer.get("focus_id") not in focus_ids_item:
                    continue

                buffer_geometry = evento_buffer.get(
                    "geometry"
                )

                if (
                    buffer_geometry is None
                    or buffer_geometry.isEmpty()
                ):
                    continue

                buffers_item.append(
                    buffer_geometry
                )

            # ----------------------------------------------------
            # Unir os buffers dos focos da imagem
            # ----------------------------------------------------

            if buffers_item:

                try:

                    buffer_unificado = (
                        QgsGeometry.unaryUnion(
                            buffers_item
                        )
                    )

                    if (
                        buffer_unificado is not None
                        and not buffer_unificado.isEmpty()
                    ):

                        # ------------------------------------------------
                        # Interseção do footprint com os buffers
                        # ------------------------------------------------

                        footprint_recortado = (
                            multipolygon.intersection(
                                buffer_unificado
                            )
                        )

                        if (
                            footprint_recortado is None
                            or footprint_recortado.isEmpty()
                        ):

                            log_message(
                                f"[DEBUG FOOTPRINT] "
                                f"Footprint não intersecta os buffers: "
                                f"{item.id}"
                            )

                            continue

                        log_message(
                            f"[DEBUG FOOTPRINT] "
                            f"Footprint recortado pelos buffers: "
                            f"{item.id}"
                        )

                    else:

                        log_message(
                            f"[DEBUG FOOTPRINT] "
                            f"Buffers inválidos para: {item.id}"
                        )

                except Exception as e:

                    log_message(
                        f"[DEBUG FOOTPRINT] "
                        f"Erro ao recortar footprint "
                        f"{item.id}: {e}"
                    )

                    continue

        # ----------------------------------------------------
        # Criar feature
        # ----------------------------------------------------

        feature = QgsFeature(
            layer.fields()
        )

        feature.setGeometry(
            footprint_recortado
        )

        feature.setAttributes([
            str(item.id),
            datetime_value,
            satellite,
            collection,
            cloud_cover,
            tile,
            focus_ids
        ])

        features.append(
            feature
        )

    # --------------------------------------------------------
    # Verificar resultado
    # --------------------------------------------------------

    for feature in features:
        geom = feature.geometry()

    if not features:

        log_message(
            "Nenhum footprint válido foi criado."
        )

        return None

    # --------------------------------------------------------
    # Adicionar features à camada temporária
    # --------------------------------------------------------

    try:

        success, added_features = (
            provider.addFeatures(
                features
            )
        )

        if not success:

            log_message(
                "ERRO ao adicionar features "
                "à camada temporária."
            )

            return None

    except Exception as e:

        log_message(
            f"ERRO ao adicionar features: {e}"
        )

        return None

    layer.updateExtents()

    log_message(
        f"Footprints válidos: {len(features)}"
    )

    # --------------------------------------------------------
    # Remover GPKG antigo, se existir
    # --------------------------------------------------------

    if os.path.exists(gpkg_path):

        try:

            os.remove(
                gpkg_path
            )

            log_message(
                f"GPKG existente removido: "
                f"{gpkg_path}"
            )

        except Exception as e:

            log_message(
                f"ERRO removendo GPKG existente: {e}"
            )

            return None

    # --------------------------------------------------------
    # Exportar para GPKG
    # --------------------------------------------------------

    try:

        options = (
            QgsVectorFileWriter.SaveVectorOptions()
        )

        options.driverName = "GPKG"
        options.layerName = layer_name
        options.fileEncoding = "UTF-8"

        result = (
            QgsVectorFileWriter.writeAsVectorFormatV3(
                layer,
                gpkg_path,
                QgsProject.instance().transformContext(),
                options
            )
        )

        error_code = result[0]

        if (
            error_code
            != QgsVectorFileWriter.NoError
        ):

            log_message(
                "ERRO ao exportar GPKG."
            )

            log_message(
                f"Código do erro: "
                f"{error_code}"
            )

            if len(result) > 1:

                log_message(
                    f"Mensagem: {result[1]}"
                )

            return None

    except Exception as e:

        log_message(
            f"EXCEÇÃO durante exportação "
            f"do GPKG: {e}"
        )

        return None

    # --------------------------------------------------------
    # Verificar arquivo
    # --------------------------------------------------------

    if not os.path.exists(
        gpkg_path
    ):

        log_message(
            "ERRO: GPKG não foi criado."
        )

        return None

    log_message(
        "GPKG criado com sucesso."
    )

    log_message(
        f"Arquivo: {gpkg_path}"
    )

    # --------------------------------------------------------
    # Carregar GPKG no QGIS
    # --------------------------------------------------------

    try:

        gpkg_uri = (
            f"{gpkg_path}|layername={layer_name}"
        )

        saved_layer = QgsVectorLayer(
            gpkg_uri,
            layer_name,
            "ogr"
        )

        if not saved_layer.isValid():

            log_message(
                "AVISO: GPKG criado, "
                "mas não foi possível carregar "
                "a camada no QGIS."
            )

            return gpkg_path

        QgsProject.instance().addMapLayer(
            saved_layer
        )

        log_message(
            f"Camada adicionada ao projeto: "
            f"{layer_name}"
        )

    except Exception as e:

        log_message(
            f"AVISO ao carregar GPKG no QGIS: {e}"
        )

    log_message(
        "================================================"
    )

    return gpkg_path

def recortar_vrt_por_buffers(
    vrt_path: str,
    eventos_buffer: List[Dict],
    covered_focuses: List[Dict],
    output_dir: str,
    item_id: str
) -> Dict[int, str]:
    """
    Cria um raster recortado para cada evento/buffer relacionado
    às feições GOES cobertas por um Item STAC.

    O recorte utiliza somente a extensão (bounding box) do buffer,
    mantendo o VRT original intacto.

    Retorna:
        {
            focus_id: caminho_do_raster_recortado
        }
    """

    resultados = {}

    if not vrt_path or not os.path.exists(vrt_path):

        log_message(
            f"[ERRO RECORTE] VRT não encontrado: {vrt_path}"
        )

        return resultados

    if not eventos_buffer:

        log_message(
            "[ERRO RECORTE] Nenhum evento bufferizado foi fornecido."
        )

        return resultados

    if not covered_focuses:

        log_message(
            f"[ERRO RECORTE] Item '{item_id}' não possui "
            f"feições GOES associadas."
        )

        return resultados

    # --------------------------------------------------------
    # Identificar os focus_id cobertos pelo Item
    # --------------------------------------------------------

    focus_ids = set()

    for focus in covered_focuses:

        try:

            focus_id = int(
                focus["id"]
            )

            focus_ids.add(
                focus_id
            )

        except (
            KeyError,
            TypeError,
            ValueError
        ):

            log_message(
                "[AVISO RECORTE] Feição GOES sem "
                "ID válido. Ignorada."
            )

    if not focus_ids:

        log_message(
            f"[ERRO RECORTE] Nenhum focus_id válido "
            f"foi encontrado para o item '{item_id}'."
        )

        return resultados

    # --------------------------------------------------------
    # Abrir VRT
    # --------------------------------------------------------

    try:

        vrt_dataset = gdal.Open(
            vrt_path,
            gdal.GA_ReadOnly
        )

        if vrt_dataset is None:

            log_message(
                f"[ERRO RECORTE] Não foi possível abrir "
                f"o VRT: {vrt_path}"
            )

            return resultados

    except Exception as e:

        log_message(
            f"[ERRO RECORTE] Erro ao abrir VRT: {e}"
        )

        return resultados

    # --------------------------------------------------------
    # CRS do VRT
    # --------------------------------------------------------

    vrt_projection = (
        vrt_dataset.GetProjection()
    )

    if not vrt_projection:

        vrt_dataset = None

        log_message(
            "[ERRO RECORTE] O VRT não possui "
            "informação de CRS."
        )

        return resultados

    # --------------------------------------------------------
    # CRS dos buffers
    #
    # Os buffers são criados em EPSG:4326.
    # --------------------------------------------------------

    crs_buffer = QgsCoordinateReferenceSystem(
        "EPSG:4326"
    )

    crs_vrt = QgsCoordinateReferenceSystem()

    crs_vrt.createFromWkt(
        vrt_projection
    )

    if not crs_vrt.isValid():

        vrt_dataset = None

        log_message(
            "[ERRO RECORTE] Não foi possível identificar "
            "o CRS do VRT."
        )

        return resultados

    # --------------------------------------------------------
    # Transformação do buffer para o CRS do VRT
    # --------------------------------------------------------

    transform_buffer_to_vrt = (
        QgsCoordinateTransform(
            crs_buffer,
            crs_vrt,
            QgsProject.instance()
        )
    )

    # --------------------------------------------------------
    # Criar índice dos buffers por focus_id
    # --------------------------------------------------------

    buffers_por_foco = {}

    for evento in eventos_buffer:

        try:

            focus_id = int(
                evento["focus_id"]
            )

        except (
            KeyError,
            TypeError,
            ValueError
        ):

            continue

        if focus_id not in focus_ids:
            continue

        geometry = evento.get(
            "geometry"
        )

        if geometry is None:
            continue

        if geometry.isEmpty():
            continue

        buffers_por_foco[
            focus_id
        ] = evento

    # --------------------------------------------------------
    # Verificar buffers encontrados
    # --------------------------------------------------------

    if not buffers_por_foco:

        vrt_dataset = None

        log_message(
            f"[ERRO RECORTE] Nenhum buffer correspondente "
            f"aos focos do item '{item_id}' foi encontrado."
        )

        return resultados

    for focus_id, evento in buffers_por_foco.items():

        geometry = evento["geometry"]

        try:

            # --------------------------------------------
            # Copiar geometria para não alterar a original
            # --------------------------------------------

            buffer_geometry = QgsGeometry(
                geometry
            )

            # --------------------------------------------
            # Transformar para CRS do VRT
            # --------------------------------------------

            buffer_geometry.transform(
                transform_buffer_to_vrt
            )

            # --------------------------------------------
            # Obter extensão do buffer
            # --------------------------------------------

            extent = (
                buffer_geometry.boundingBox()
            )

            if extent.isEmpty():

                log_message(
                    f"[AVISO RECORTE] Extensão vazia "
                    f"para Foco {focus_id}."
                )

                continue

            # --------------------------------------------
            # Nome do arquivo de saída
            # --------------------------------------------

            output_path = os.path.join(
                output_dir,
                f"{item_id}_Foco_{focus_id}_"
                f"SWIR2_NIR_RED.tif"
            )

            # --------------------------------------------
            # Remover arquivo anterior
            # --------------------------------------------

            if os.path.exists(output_path):

                try:

                    os.remove(
                        output_path
                    )

                except Exception as e:

                    log_message(
                        f"[AVISO RECORTE] Não foi possível "
                        f"remover o arquivo existente: "
                        f"{output_path} | {e}"
                    )

                    continue

            log_message(
                "------------------------------------------------"
            )

            log_message(
                f"[DEBUG RECORTE] Item: {item_id}"
            )

            log_message(
                f"[DEBUG RECORTE] Foco: {focus_id}"
            )

            log_message(
                f"[DEBUG RECORTE] Evento: "
                f"{evento.get('nome', '')}"
            )

            log_message(
                f"[DEBUG RECORTE] CRS do VRT: "
                f"{crs_vrt.authid()}"
            )

            log_message(
                f"[DEBUG RECORTE] Extensão: "
                f"{extent.toString()}"
            )

            log_message(
                f"[DEBUG RECORTE] Saída: "
                f"{output_path}"
            )

            # --------------------------------------------
            # Recortar VRT
            # --------------------------------------------

            warp_options = gdal.WarpOptions(
                outputBounds=[
                    extent.xMinimum(),
                    extent.yMinimum(),
                    extent.xMaximum(),
                    extent.yMaximum()
                ],
                dstSRS=crs_vrt.toWkt(),
                format="GTiff",
                resampleAlg="nearest",
                creationOptions=[
                    "TILED=YES",
                    "COMPRESS=DEFLATE"
                ]
            )

            output_dataset = gdal.Warp(
                output_path,
                vrt_dataset,
                options=warp_options
            )

            if output_dataset is None:

                log_message(
                    f"[ERRO RECORTE] GDAL não conseguiu "
                    f"criar o recorte para Foco {focus_id}."
                )

                continue

            output_dataset.FlushCache()
            output_dataset = None

            # --------------------------------------------
            # Validar arquivo
            # --------------------------------------------

            if not os.path.exists(output_path):

                log_message(
                    f"[ERRO RECORTE] Arquivo não foi criado: "
                    f"{output_path}"
                )

                continue

            check_dataset = None

            try:

                check_dataset = gdal.Open(
                    output_path,
                    gdal.GA_ReadOnly
                )

                if check_dataset is None:

                    log_message(
                        f"[ERRO RECORTE] Arquivo criado, "
                        f"mas não pôde ser aberto: "
                        f"{output_path}"
                    )

                    continue

            finally:

                check_dataset = None

            resultados[
                focus_id
            ] = output_path

            log_message(
                f"[DEBUG RECORTE] ✓ Recorte criado "
                f"para Foco {focus_id}"
            )

        except Exception as e:

            log_message(
                f"[ERRO RECORTE] Erro ao recortar "
                f"Foco {focus_id}: {e}"
            )

    vrt_dataset = None

    log_message(
        "------------------------------------------------"
    )

    log_message(
        f"[DEBUG RECORTE] Recortes criados: "
        f"{len(resultados)}"
    )

    return resultados

# ============================================================
# ENTRADA DO USUÁRIO
# ============================================================
def get_user_input():

    app = (
        QApplication.instance()
        or QApplication([])
    )

    dialog = QDialog()

    dialog.setWindowTitle(
        "Buscar Imagens STAC "
        "(Landsat / Sentinel-2 / "
        "Amazonia-1 / CBERS-4 / CBERS-4A)"
    )

    dialog.setMinimumWidth(
        500
    )

    dialog.setModal(
        False
    )

    layout = QVBoxLayout()

    # ========================================================
    # CONFIGURAÇÃO AUTOMÁTICA DO PERÍODO
    # ========================================================

    hoje = datetime.today().date()

    data_10_dias_atras = (
        hoje
        - timedelta(days=10)
    )

    start_date = (
        data_10_dias_atras.strftime(
            "%Y-%m-%d"
        )
    )

    end_date = (
        hoje.strftime(
            "%Y-%m-%d"
        )
    )

    # ========================================================
    # DIRETÓRIO DE SAÍDA
    # ========================================================

    out_dir_input = QLineEdit(
        "/home/fabianamangili/projetos/carrega_focos"
    )

    form_layout = QFormLayout()

    form_layout.addRow(
        "Diretório de Saída:",
        out_dir_input
    )

    # --------------------------------------------------------
    # Selecionar diretório
    # --------------------------------------------------------

    def select_output_dir():

        dir_path = (
            QFileDialog.getExistingDirectory(
                iface.mainWindow(),
                "Selecione o Diretório de Saída"
            )
        )

        if dir_path:

            out_dir_input.setText(
                dir_path
            )

    output_dir_button = QPushButton(
        "Selecionar Diretório"
    )

    output_dir_button.clicked.connect(
        select_output_dir
    )

    form_layout.addRow(
        output_dir_button
    )

    # ========================================================
    # PERÍODO AUTOMÁTICO
    # ========================================================

    period_label = QLabel(
        "Período da busca: "
        f"{start_date} até {end_date}"
    )

    period_label.setStyleSheet(
        "color: #444; "
        "font-weight: bold;"
    )

    form_layout.addRow(
        "Período:",
        period_label
    )

    # ========================================================
    # SATÉLITES / COLLECTIONS
    # ========================================================

    collections_label = QLabel(
        "Todas as coleções dos satélites "
        "serão consultadas automaticamente."
    )

    collections_label.setWordWrap(
        True
    )

    collections_label.setStyleSheet(
        "color: #555;"
    )

    form_layout.addRow(
        "Satélites:",
        collections_label
    )

    # ========================================================
    # CAMADAS DE FOCO - V3
    # ========================================================

    try:
        available_focus_layers = (
            get_focus_layers_from_kml()
        )
    except Exception as e:
        log_message(
            f"ERRO ao carregar o KML de focos: {e}"
        )
        QMessageBox.critical(
            iface.mainWindow(),
            "KML de focos",
            str(e)
        )
        return None

    selected_focus_layers = {}

    # Resultado final do diálogo principal.
    dialog_result = {
        "accepted": False
    }

    # Event loop para manter o QGIS responsivo durante o diálogo.
    event_loop = QEventLoop()

    focus_group_label = QLabel(
        "Selecione uma ou mais camadas de focos "
        "para definir as áreas de interesse da consulta STAC:"
    )

    focus_group_label.setWordWrap(True)
    focus_group_label.setStyleSheet(
        "color: #555; font-weight: bold;"
    )

    form_layout.addRow(
        "Camadas de foco:",
        focus_group_label
    )

    focus_checkboxes = []

    if not available_focus_layers:

        no_layers_label = QLabel(
            "Nenhuma das três camadas esperadas foi "
            "encontrada no KML online."
        )

        no_layers_label.setWordWrap(True)
        no_layers_label.setStyleSheet(
            "color: red; font-weight: bold;"
        )

        form_layout.addRow(
            no_layers_label
        )

    else:

        for layer_name in FOCUS_LAYER_NAMES:

            if layer_name not in available_focus_layers:
                continue

            checkbox = QCheckBox(
                layer_name
            )

            checkbox.setChecked(False)
            focus_checkboxes.append(
                (layer_name, checkbox)
            )

            form_layout.addRow(
                checkbox
            )

    selected_layers_label = QLabel(
        "Nenhuma camada selecionada."
    )

    selected_layers_label.setWordWrap(True)
    selected_layers_label.setStyleSheet(
        "color: #666;"
    )

    form_layout.addRow(
        "Seleção:",
        selected_layers_label
    )

    def update_selected_layers_label():

        names = [
            layer_name
            for layer_name, checkbox
            in focus_checkboxes
            if checkbox.isChecked()
        ]

        if not names:

            selected_layers_label.setText(
                "Nenhuma camada selecionada."
            )

            selected_layers_label.setStyleSheet(
                "color: #666;"
            )

        else:

            selected_layers_label.setText(
                "Selecionadas: "
                + " | ".join(names)
            )

            selected_layers_label.setStyleSheet(
                "color: #333; font-weight: bold;"
            )

    for _, checkbox in focus_checkboxes:

        checkbox.stateChanged.connect(
            update_selected_layers_label
        )

    # ========================================================
    # GOOGLE HYBRID
    # ========================================================

    google_hybrid_btn = QPushButton(
        "Carregar Google Maps Hybrid"
    )

    google_hybrid_btn.setStyleSheet(
        "font-weight: bold; "
        "padding: 5px;"
    )

    # ========================================================
    # CARREGAR GOOGLE HYBRID
    # ========================================================

    def carregar_google_hybrid():

        url = (
            "type=xyz&"
            "zmin=0&"
            "zmax=20&"
            "url=https://mt1.google.com/"
            "vt/lyrs%3Dy%26x%3D{x}"
            "%26y%3D{y}%26z%3D{z}"
        )

        google_layer = QgsRasterLayer(
            url,
            "Google Hybrid",
            "wms"
        )

        if google_layer.isValid():

            crs_4326 = (
                QgsCoordinateReferenceSystem(
                    "EPSG:4326"
                )
            )

            QgsProject.instance().setCrs(
                crs_4326
            )

            root = (
                QgsProject.instance()
                .layerTreeRoot()
            )

            QgsProject.instance().addMapLayer(
                google_layer,
                False
            )

            root.insertLayer(
                -1,
                google_layer
            )

            google_layer.setOpacity(
                1
            )

            log_message(
                "Camada Google Hybrid "
                "carregada com sucesso "
                "em EPSG:4326."
            )

            iface.mapCanvas().refresh()

        else:

            log_message(
                "Erro ao carregar "
                "a camada Google Hybrid."
            )

    google_hybrid_btn.clicked.connect(
        carregar_google_hybrid
    )

    # ========================================================
    # LAYOUT
    # ========================================================

    layout.addLayout(
        form_layout
    )

    # --------------------------------------------------------
    # Botões principais
    # --------------------------------------------------------

    buttons_layout = QHBoxLayout()

    buttons_layout.addWidget(
        google_hybrid_btn
    )

    layout.addLayout(
        buttons_layout
    )

    # ========================================================
    # BOTÕES OK / CANCEL
    # ========================================================

    button_box = (
        QDialogButtonBox(
            QDialogButtonBox.Ok
            | QDialogButtonBox.Cancel
        )
    )

    layout.addWidget(
        button_box
    )

    dialog.setLayout(
        layout
    )

    # ========================================================
    # OK
    # ========================================================

    def accept_dialog():

        log_message("================================================")
        log_message("BOTÃO OK CLICADO - V3")

        selected_names = [
            layer_name
            for layer_name, checkbox
            in focus_checkboxes
            if checkbox.isChecked()
        ]

        log_message(
            f"Camadas selecionadas: {selected_names}"
        )

        if not selected_names:

            QMessageBox.warning(
                dialog,
                "Camadas de foco",
                "Selecione pelo menos uma das camadas "
                "de focos disponíveis."
            )

            return

        missing = [
            name
            for name in selected_names
            if name not in available_focus_layers
        ]

        if missing:

            QMessageBox.warning(
                dialog,
                "Camadas de foco",
                "Uma ou mais camadas selecionadas "
                "não estão disponíveis no KML online."
            )

            return

        selected_focus_layers.clear()

        for name in selected_names:

            selected_focus_layers[name] = (
                available_focus_layers[name]
            )

        # ----------------------------------------------------
        # Baixar o KML para o diretório escolhido pelo usuário
        # e abrir no projeto QGIS somente as camadas selecionadas.
        # ----------------------------------------------------
        try:
            downloaded_kml_path = download_focus_kml(
                out_dir_input.text().strip()
            )

            load_selected_focus_kml_layers_to_project(
                downloaded_kml_path,
                selected_names
            )

        except Exception as e:
            log_message(
                f"ERRO ao baixar/abrir o KML de focos: {e}"
            )

            QMessageBox.critical(
                dialog,
                "KML de focos",
                "Não foi possível baixar e abrir o KML de focos "
                f"no projeto QGIS.\n\n{e}"
            )

            return

        dialog_result["accepted"] = True

        dialog.hide()
        event_loop.quit()

        log_message(
            "Diálogo principal V3 aceito."
        )

        log_message("================================================")

    # ========================================================
    # CANCELAR
    # ========================================================

    def cancel_dialog():

        log_message("================================================")
        log_message("BOTÃO CANCELAR CLICADO - V3")

        dialog_result["accepted"] = False

        event_loop.quit()

        log_message(
            "Event loop encerrado por cancelamento."
        )

        log_message("================================================")

    button_box.accepted.connect(
        accept_dialog
    )

    button_box.rejected.connect(
        cancel_dialog
    )

    # ========================================================
    # MOSTRAR DIÁLOGO
    # ========================================================

    log_message(
        "Abrindo diálogo principal..."
    )

    dialog.show()

    dialog.raise_()

    dialog.activateWindow()

    # ========================================================
    # EXECUTAR EVENT LOOP
    #
    # Diferente de dialog.exec_(), este loop:
    #
    # - mantém o QGIS responsivo;
    # - permite que o canvas receba cliques;
    # - permite esconder o diálogo;
    # - permite restaurá-lo depois do BBOX.
    # ========================================================

    event_loop.exec_()

    # ========================================================
    # RESULTADO DO DIÁLOGO PRINCIPAL
    # ========================================================

    log_message("================================================")
    log_message("EVENT LOOP PRINCIPAL FINALIZADO")
    log_message(
        f"Diálogo aceito: {dialog_result['accepted']}"
    )
    log_message(
        f"Camadas selecionadas: "
        f"{list(selected_focus_layers.keys())}"
    )
    log_message("================================================")

    if not dialog_result["accepted"]:

        log_message("Diálogo cancelado.")
        return None

    # ========================================================
    # DIRETÓRIO DE SAÍDA
    # ========================================================

    output_dir = (
        out_dir_input
        .text()
        .strip()
    )

    if not output_dir:

        log_message(
            "ERRO: diretório de saída não informado."
        )

        QMessageBox.warning(
            iface.mainWindow(),
            "Diretório de saída",
            "Informe um diretório de saída."
        )

        return None

    # ========================================================
    # EXTRAIR FEIÇÕES
    # ========================================================

    try:

        (
            intersects_geometry,
            point_records
        ) = extract_focus_points_wgs84(
            selected_focus_layers
        )

    except Exception as e:

        log_message(
            f"ERRO ao extrair feições do KML: {e}"
        )

        QMessageBox.critical(
            iface.mainWindow(),
            "Feições de foco",
            str(e)
        )

        return None
    
    # ========================================================
    # BAIXAR EVENTOS ATIVOS
    # ========================================================

    try:

        baixar_eventos_ativos()

    except Exception as e:

        log_message(
            f"ERRO ao baixar eventos ativos: {e}"
        )

        QMessageBox.critical(
            iface.mainWindow(),
            "Eventos ativos",
            str(e)
        )

        return None


    # ========================================================
    # LER EVENTOS ATIVOS
    # ========================================================

    try:

        eventos_ativos = ler_eventos_ativos()

    except Exception as e:

        log_message(
            f"ERRO ao ler eventos ativos: {e}"
        )

        QMessageBox.critical(
            iface.mainWindow(),
            "Eventos ativos",
            str(e)
        )

        return None

    # ========================================================
    # RELACIONAR GOES × EVENTOS ATIVOS
    # ========================================================

    try:

        relacoes_eventos = relacionar_goes_eventos(
            point_records,
            eventos_ativos
        )

    except Exception as e:

        log_message(
            f"ERRO ao relacionar GOES × eventos: {e}"
        )

        QMessageBox.critical(
            iface.mainWindow(),
            "Eventos ativos",
            str(e)
        )

        return None
    
    # ========================================================
    # CRIAR BUFFER DOS EVENTOS
    # ========================================================
    relacoes_eventos = remover_relacoes_duplicadas(relacoes_eventos)
    try:

        eventos_buffer = criar_buffer_eventos(
            relacoes_eventos,
            buffer_metros=2000.0
        )

    except Exception as e:

        log_message(
            f"ERRO ao criar buffer dos eventos: {e}"
        )

        QMessageBox.critical(
            iface.mainWindow(),
            "Buffer dos eventos",
            str(e)
        )

        return None
    
    # ========================================================
    # CRIAR CAMADA TEMPORÁRIA DOS EVENTOS BUFFERIZADOS
    # ========================================================

    try:

        camada_buffer = criar_camada_eventos_bufferizados(
            eventos_buffer
        )

    except Exception as e:

        log_message(
            f"ERRO ao criar camada dos eventos bufferizados: {e}"
        )

        QMessageBox.critical(
            iface.mainWindow(),
            "Eventos ativos",
            str(e)
        )

        return None

    # ========================================================
    # GEOMETRIA DOS BUFFERS PARA CONSULTA STAC
    # ========================================================

    try:

        buffer_intersects_geometry = (
            criar_intersects_buffer_eventos(
                eventos_buffer
            )
        )

    except Exception as e:

        log_message(
            f"ERRO ao preparar geometria dos buffers: {e}"
        )

        QMessageBox.critical(
            iface.mainWindow(),
            "Buffer dos eventos",
            str(e)
        )

        return None
       

    log_message("================================================")
    log_message("PARÂMETROS DA EXECUÇÃO V3")
    log_message(
        f"Data inicial: {start_date}"
    )
    log_message(
        f"Data final: {end_date}"
    )
    log_message(
        f"Diretório de saída: {output_dir}"
    )
    log_message(
        f"Camadas: {list(selected_focus_layers.keys())}"
    )
    log_message(
        f"Feições: {len(point_records)}"
    )

    log_message(
    "Consulta espacial: intersects / buffer dos eventos"
    )

    log_message(
        "Buffer dos eventos: 2000 metros"
    )
    log_message("================================================")

    # ========================================================
    # TODAS AS COLLECTIONS
    # ========================================================

    collections = []

    for satellite_name in [
        "Landsat",
        "Sentinel-2",
        "Amazonia-1",
        "CBERS-4-MUX",
        "CBERS-4-WFI",
        "CBERS-4A-MUX",
        "CBERS-4A-WFI"
    ]:

        config = get_satellite_config(
            satellite_name
        )

        satellite_collections = (
            config.get(
                "collections",
                []
            )
        )

        for collection in (
            satellite_collections
        ):

            if collection not in collections:

                collections.append(
                    collection
                )

    log_message(
        "================================================"
    )

    log_message(
        "COLLECTIONS STAC QUE SERÃO CONSULTADAS:"
    )

    for collection in collections:

        log_message(
            f" - {collection}"
        )

    log_message(
        "================================================"
    )

    # ========================================================
    # CONECTAR AO STAC
    # ========================================================

    log_message(
        "Iniciando conexão com STAC..."
    )

    client = connect_to_stac(
        "https://data.inpe.br/bdc/stac/v1/"
    )

    if not client:

        log_message(
            "Não foi possível conectar "
            "ao STAC."
        )

        return None

    # ========================================================
    # BUSCAR ITENS POR FEIÇÕES - V3
    # ========================================================

    log_message(
        "Iniciando busca STAC V3..."
    )

    log_message(
        "Spatial filter: intersects / MultiPoint"
    )

    log_message(
        f"Período: {start_date}/{end_date}"
    )

    log_message(
        f"Collections: {collections}"
    )

    items, covered_focuses_by_item = search_items_by_features(
        client,
        buffer_intersects_geometry,
        point_records,
        start_date,
        end_date,
        collections
    )


    # ========================================================
    # NENHUM RESULTADO
    # ========================================================

    if not items:

        log_message(
            "Nenhuma imagem disponível para as feições "
            "selecionadas nos últimos 10 dias."
        )

        QMessageBox.information(
            iface.mainWindow(),
            "Nenhuma imagem encontrada",
            "Não foram encontradas imagens que intersectem "
            "as feições selecionadas no período "
            f"de {start_date} até {end_date}."
        )

        return None

    # ========================================================
    # LOG DOS ITENS ENCONTRADOS
    # ========================================================

    log_message(
        "================================================"
    )

    log_message(
        f"{len(items)} item(ns) encontrados."
    )

    for item in items:

        log_message(
            f"Item: {item.id}"
        )

    log_message(
        "================================================"
    )

    # ========================================================
    # SELECIONAR CENAS
    # ========================================================

    log_message(
        "Abrindo seleção de imagens..."
    )

    selected_items = (
        select_available_items(
            None,
            items,
            point_records=point_records,
            covered_focuses_by_item=covered_focuses_by_item,
            search_context={
                "mode": "V3 - feições",
                "layers": list(selected_focus_layers.keys()),
                "feature_count": len(point_records),
                "unique_points": len({
                    (r["x"], r["y"])
                    for r in point_records
                }),
                "start_date": start_date,
                "end_date": end_date
            }
        )
    )

    if selected_items is None:

        log_message(
            "Seleção de imagens cancelada."
        )

        return None

    if not selected_items:

        log_message(
            "Nenhuma imagem selecionada."
        )

        return None

    # ========================================================
    # EXPORTAR FOOTPRINTS DAS IMAGENS SELECIONADAS
    # ========================================================

    log_message(
        f"[DEBUG FOOTPRINT] Gerando footprints para "
        f"{len(selected_items)} imagem(ns)."
    )

    footprints_path = export_selected_footprints(
        selected_items,
        output_dir,
        point_records,
        covered_focuses_by_item=covered_focuses_by_item,
        eventos_buffer=eventos_buffer
    )

    if footprints_path:
        log_message(
            f"[DEBUG FOOTPRINT] ✓ Footprints disponíveis em: "
            f"{footprints_path}"
        )
    else:
        log_message(
            "[DEBUG FOOTPRINT] AVISO: não foi possível gerar "
            "o GPKG de footprints."
        )


    # ========================================================
    # RETORNAR RESULTADO
    # ========================================================

    return (
        None,
        None,
        start_date,
        end_date,
        output_dir,
        None,
        selected_items,
        point_records,
        covered_focuses_by_item,
        eventos_buffer
    )
# ============================================================
# GRUPOS DE FOCOS NO PROJETO QGIS
# ============================================================

def get_or_create_focus_group(record: Dict):
    """Cria ou recupera o grupo QGIS correspondente à feição."""

    root = QgsProject.instance().layerTreeRoot()
    layer_name = str(record.get("layer", "Foco"))
    focus_id = record.get("id")
    group_name = f"Foco {focus_id} | {layer_name}"

    group = root.findGroup(group_name)

    if group is None:
        group = root.addGroup(group_name)
        log_message(f"[DEBUG GRUPO] ✓ Grupo criado: '{group_name}'")

    return group

def add_raster_to_focus_groups(
    raster_layer,
    covered_focuses: List[Dict],
    focus_id=None
):
    """
    Adiciona o raster ao grupo correspondente à feição.

    Para rasters recortados por foco, focus_id deve ser informado.
    Nesse caso, o raster será associado exclusivamente ao grupo
    daquele foco.
    """

    if not covered_focuses:

        log_message(
            f"[DEBUG GRUPO] Nenhuma feição associada a "
            f"'{raster_layer.name()}'."
        )

        return

    # --------------------------------------------------------
    # Filtrar exclusivamente o foco do raster
    # --------------------------------------------------------

    if focus_id is not None:

        try:

            focus_id_int = int(focus_id)

        except (
            TypeError,
            ValueError
        ):

            log_message(
                f"[DEBUG GRUPO] focus_id inválido: "
                f"{focus_id}"
            )

            return

        covered_focuses = [
            record
            for record in covered_focuses
            if int(record.get("id")) == focus_id_int
        ]

    if not covered_focuses:

        log_message(
            f"[DEBUG GRUPO] Nenhuma feição correspondente "
            f"ao Foco {focus_id} foi encontrada."
        )

        return

    root = QgsProject.instance().layerTreeRoot()

    # --------------------------------------------------------
    # Adicionar ao grupo
    # --------------------------------------------------------

    for record in covered_focuses:

        group = get_or_create_focus_group(
            record
        )

        # ----------------------------------------------------
        # Verificar se já existe no grupo
        # ----------------------------------------------------

        existing_nodes = group.findLayers()

        already_in_group = any(
            node.layerId() == raster_layer.id()
            for node in existing_nodes
        )

        if already_in_group:

            log_message(
                f"[DEBUG GRUPO] Raster já está no grupo: "
                f"'{raster_layer.name()}' -> "
                f"Foco {record['id']} | {record['layer']}"
            )

            continue

        # ----------------------------------------------------
        # Localizar eventual nó existente na árvore
        # ANTES de adicionar ao grupo
        # ----------------------------------------------------

        old_node = root.findLayer(
            raster_layer.id()
        )

        # ----------------------------------------------------
        # Adicionar ao grupo correto
        # ----------------------------------------------------

        new_node = group.addLayer(
            raster_layer
        )

        if new_node is None:

            log_message(
                f"[DEBUG GRUPO] ERRO ao adicionar "
                f"'{raster_layer.name()}' ao grupo."
            )

            continue

        # ----------------------------------------------------
        # Remover nó original, se existir
        # ----------------------------------------------------

        if old_node is not None:

            old_parent = old_node.parent()

            if old_parent is not None:

                old_parent.removeChildNode(
                    old_node
                )

        log_message(
            f"[DEBUG GRUPO] ✓ '{raster_layer.name()}' -> "
            f"Foco {record['id']} | {record['layer']}"
        )

    iface.mapCanvas().refresh()
# ============================================================
# CRIAR VRT
# ============================================================

def create_vrt(
    vrt_path: str,
    hrefs: List[str]
) -> bool:

    vrt_dataset = None

    try:

        output_dir = os.path.dirname(
            vrt_path
        )

        if (
            output_dir
            and not os.path.exists(output_dir)
        ):

            os.makedirs(
                output_dir,
                exist_ok=True
            )

            log_message(
                f"Diretório criado: "
                f"{output_dir}"
            )

        # ----------------------------------------------------
        # Remover VRT existente
        # ----------------------------------------------------

        if os.path.exists(vrt_path):

            log_message(
                f"VRT já existe. "
                f"Será substituído: "
                f"{vrt_path}"
            )

            try:

                os.remove(
                    vrt_path
                )

            except Exception as e:

                log_message(
                    f"Não foi possível remover "
                    f"o VRT existente: {e}"
                )

                return False

        # ----------------------------------------------------
        # Validar assets
        # ----------------------------------------------------

        if not hrefs:

            log_message(
                "Nenhum asset fornecido "
                "para criação do VRT."
            )

            return False

        log_message(
            f"Criando VRT: {vrt_path}"
        )

        log_message(
            f"Assets: {hrefs}"
        )

        # ----------------------------------------------------
        # Opções GDAL
        # ----------------------------------------------------

        vrt_options = (
            gdal.BuildVRTOptions(
                resampleAlg="nearest",
                addAlpha=False,
                separate=True
            )
        )

        # ----------------------------------------------------
        # Criar
        # ----------------------------------------------------

        log_message(
            "[DEBUG] Entrando em gdal.BuildVRT()..."
        )

        log_message(
            f"[DEBUG] vrt_path: {vrt_path}"
        )

        log_message(
            f"[DEBUG] quantidade de assets: {len(hrefs)}"
        )

        vrt_dataset = gdal.BuildVRT(
            vrt_path,
            hrefs,
            options=vrt_options
        )


        log_message(
            "[DEBUG] gdal.BuildVRT() retornou."
        )


        if vrt_dataset is None:

            log_message(
                f"GDAL não conseguiu criar "
                f"o VRT: {vrt_path}"
            )

            return False

        vrt_dataset.FlushCache()

        vrt_dataset = None

        # ----------------------------------------------------
        # Confirmar arquivo
        # ----------------------------------------------------

        if not os.path.exists(vrt_path):

            log_message(
                f"GDAL retornou sucesso, "
                f"mas o arquivo não existe: "
                f"{vrt_path}"
            )

            return False

        # ----------------------------------------------------
        # Testar abertura
        # ----------------------------------------------------

        check_dataset = None

        try:

            check_dataset = gdal.Open(
                vrt_path,
                gdal.GA_ReadOnly
            )

            if check_dataset is None:

                log_message(
                    f"O VRT foi criado, "
                    f"mas não pôde ser aberto: "
                    f"{vrt_path}"
                )

                return False

        finally:

            check_dataset = None

        log_message(
            f"VRT criado e validado com sucesso: "
            f"{vrt_path}"
        )

        return True

    except Exception as e:

        vrt_dataset = None

        log_message(
            f"Erro ao criar VRT: {e}"
        )

        if os.path.exists(vrt_path):

            try:

                os.remove(
                    vrt_path
                )

                log_message(
                    f"VRT incompleto removido: "
                    f"{vrt_path}"
                )

            except Exception:
                pass

        return False
# ============================================================
# EXECUÇÃO PRINCIPAL
# ============================================================

user_input = get_user_input()

if user_input is None:

    log_message(
        "Nenhuma imagem selecionada. "
        "Execução encerrada."
    )

else:

    # --------------------------------------------------------
    # Recuperar parâmetros
    # --------------------------------------------------------
    (
        query_bands,
        satellite,
        start_date,
        end_date,
        output_dir,
        bbox,
        selected_items,
        point_records,
        covered_focuses_by_item,
        eventos_buffer
    ) = user_input

    log_message(
        "================================================"
    )

    log_message(
        "PARÂMETROS DA EXECUÇÃO"
    )

    log_message(
        "Consulta espacial V3: feições selecionadas "
        "(intersects / MultiPoint)"
    )

    log_message(
        f"Data inicial: {start_date}"
    )

    log_message(
        f"Data final: {end_date}"
    )

    log_message(
        f"Diretório de saída: {output_dir}"
    )

    log_message(
        f"Imagens selecionadas: "
        f"{len(selected_items)}"
    )

    log_message(
        "================================================"
    )

    # --------------------------------------------------------
    # Processar cada imagem
    # --------------------------------------------------------

    for item in selected_items:

        log_message(
            "------------------------------------------------"
        )

        log_message(
            f"Processando item: {item.id}"
        )

        # ----------------------------------------------------
        # Identificar automaticamente o satélite
        # ----------------------------------------------------

        satellite = identify_satellite(
            item
        )

        log_message(
            f"Satélite identificado: {satellite}"
        )

        # ----------------------------------------------------
        # Recuperar configuração do satélite
        # ----------------------------------------------------

        config = get_satellite_config(
            satellite
        )

        log_message(
            f"Coleção: "
            f"{config['collections']}"
        )

        log_message(
            f"Composição: "
            f"{config.get('composition', 'N/A')}"
        )

        log_message(
            f"Bandas padrão: "
            f"{config['default_bands']}"
        )

        # ----------------------------------------------------
        # Bandas usadas para o VRT
        # ----------------------------------------------------

        query_bands = [
            band.strip()
            for band
            in config["default_bands"]
            .split(",")
            if band.strip()
        ]

        log_message(
            f"Bandas do item: {query_bands}"
        )

        # ----------------------------------------------------
        # Validar assets
        # ----------------------------------------------------

        validation = validate_item_assets(
            item,
            query_bands,
            satellite
        )

        if not validation["valid"]:

            log_message(
                f"Item {item.id} ignorado. "
                f"Assets ausentes: "
                f"{validation['missing']}"
            )

            continue

        hrefs = validation["hrefs"]

        log_message(
            f"Assets encontrados para "
            f"{item.id}: "
            f"{hrefs}"
        )

        # ----------------------------------------------------
        # Definir caminho do VRT
        # ----------------------------------------------------

        vrt_path = os.path.join(
            output_dir,
            f"{item.id}_SWIR2_NIR_RED.vrt"
        )

        log_message(
            "[DEBUG] Iniciando criação do VRT..."
        )

        log_message(
            f"[DEBUG] Caminho do VRT: {vrt_path}"
        )

        # ----------------------------------------------------
        # Criar VRT
        # ----------------------------------------------------

        vrt_created = create_vrt(
            vrt_path,
            hrefs
        )

        if not vrt_created:

            log_message(
                f"Falha na criação do VRT "
                f"para {item.id}."
            )

            continue

        log_message(
            f"VRT criado com sucesso: "
            f"{vrt_path}"
        )
        # ----------------------------------------------------
        # Carregar VRT no projeto QGIS
        # ----------------------------------------------------

        log_message(
            "[DEBUG] Carregando VRT no projeto QGIS..."
        )

        # ----------------------------------------------------
        # Obter feições de foco cobertas pela cena
        # ----------------------------------------------------

        covered_focuses = (
            covered_focuses_by_item.get(
                item.id,
                []
            )
        )

        log_message(
            f"[DEBUG GRUPO] Item '{item.id}' cobre "
            f"{len(covered_focuses)} feição(ões)."
        )

        # ----------------------------------------------------
        # Criar recortes individuais pelos buffers dos eventos
        # ----------------------------------------------------

        rasters_recortados = recortar_vrt_por_buffers(
            vrt_path=vrt_path,
            eventos_buffer=eventos_buffer,
            covered_focuses=covered_focuses,
            output_dir=output_dir,
            item_id=item.id
        )

        if not rasters_recortados:

            log_message(
                f"[ERRO] Nenhum recorte foi criado "
                f"para o item {item.id}."
            )

            continue
        # ====================================================
        # ASSOCIAR IMAGEM ÀS FEIÇÕES DE FOCO
        # ====================================================

        covered_focuses = (
            covered_focuses_by_item.get(item.id, [])
        )

        log_message(
            f"[DEBUG GRUPO] Item '{item.id}' cobre "
            f"{len(covered_focuses)} feição(ões)."
        )
        
        # ----------------------------------------------------
        # Carregar cada recorte no QGIS
        # ----------------------------------------------------

        for focus_id, raster_path in rasters_recortados.items():

            log_message(
                f"[DEBUG] Carregando recorte no QGIS: "
                f"Foco {focus_id}"
            )

            raster_layer = iface.addRasterLayer(
                raster_path,
                f"{item.id}_Foco_{focus_id}_SWIR2_NIR_RED"
            )

            if (
                raster_layer is None
                or not raster_layer.isValid()
            ):

                log_message(
                    f"[ERRO] Não foi possível carregar "
                    f"o raster recortado no QGIS: "
                    f"{raster_path}"
                )

                continue

            log_message(
                f"[DEBUG] Recorte carregado com sucesso "
                f"no QGIS: {raster_layer.name()}"
            )

            # ------------------------------------------------
            # Associar imagem SOMENTE ao foco correspondente
            # ------------------------------------------------

            focuses_do_raster = [
                focus
                for focus in covered_focuses
                if int(focus["id"]) == int(focus_id)
            ]

            add_raster_to_focus_groups(
                raster_layer,
                focuses_do_raster,
                focus_id=focus_id
            )