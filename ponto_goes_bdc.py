import os
import json
import requests

from PyQt5.QtGui import QPixmap
from datetime import datetime, timedelta
from PIL import Image, ImageEnhance
from io import BytesIO
from xml.etree import ElementTree as ET
from qgis.utils import iface

from pystac_client import Client
from typing import List, Dict
from osgeo import gdal
from qgis.core import (
    QgsRasterLayer,
    QgsProject,
    QgsCoordinateReferenceSystem,
    QgsGeometry,
    QgsPointXY,
    QgsWkbTypes,
    QgsJsonUtils,
    QgsProviderRegistry,
    QgsVectorLayer,
    QgsFeature,
    QgsField,
    QgsVectorFileWriter
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
    QMessageBox
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
    satellite: str
):
    """
    Baixa o thumbnail do item STAC e aplica uma
    melhoria simples de contraste para exibição.
    """

    try:

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
        6
    )

    table.setHorizontalHeaderLabels(
        [
            "ID da Feição",
            "Data",
            "Satélite",
            "Tile / Órbita",
            "Cloud Cover (%)",
            "Thumbnail"
        ]
    )

    table.setSelectionBehavior(
        QTableWidget.SelectRows
    )

    table.setSelectionMode(
        QTableWidget.ExtendedSelection
    )

    # ========================================================
    # PREENCHER TABELA
    # ========================================================

    for row, item in enumerate(items):

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
            0,
            QTableWidgetItem(
                focus_ids_text
            )
        )

        # ----------------------------------------------------
        # Coluna Data
        # ----------------------------------------------------

        table.setItem(
            row,
            1,
            QTableWidgetItem(
                date
            )
        )

        # ----------------------------------------------------
        # Coluna Satélite
        # ----------------------------------------------------

        table.setItem(
            row,
            2,
            QTableWidgetItem(
                satellite_name
            )
        )

        # ----------------------------------------------------
        # Coluna Tile / Órbita
        # ----------------------------------------------------

        table.setItem(
            row,
            3,
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
            4,
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
                sat=satellite_name
            ):

                def callback():

                    pixmap = (
                        enhance_thumbnail(
                            url,
                            sat
                        )
                    )

                    if pixmap.isNull():

                        log_message(
                            "Thumbnail não "
                            "pôde ser exibido."
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
                    date
                )
            )

            table.setCellWidget(
                row,
                5,
                view_btn
            )

        else:

            table.setItem(
                row,
                5,
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

    select_all_btn = QPushButton(
        "Selecionar Tudo"
    )

    deselect_all_btn = QPushButton(
        "Desselecionar Tudo"
    )

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
    # EVENTOS DE SELEÇÃO
    # ========================================================

    select_all_btn.clicked.connect(
        table.selectAll
    )

    deselect_all_btn.clicked.connect(
        table.clearSelection
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
            index.row()
            for index
            in table
            .selectionModel()
            .selectedRows()
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
        index.row()
        for index
        in table
        .selectionModel()
        .selectedRows()
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

# O KML possui os mesmos três grupos utilizados anteriormente
# no projeto QGIS. A consulta agora é feita diretamente na fonte
# online, sem depender de camadas carregadas no projeto.
KML_FOCUS_URL = (
    "https://dataserver-coids.inpe.br/"
    "queimadas/queimadas/focos/kml/"
    "focos_goes_ponto_atencao_48hr/"
    "focos_goes_ponto_atencao_48hr.kml"
)

FOCUS_LAYER_NAMES = [
    "1 até 35 repetições",
    "36 até 71 repetições",
    "72 até 143 repetições"
]


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

        # Um Point normalmente possui uma única coordenada,
        # mas aceitamos múltiplas coordenadas por segurança.
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
    log_message("Geometry type: MultiPoint")
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
        log_message("Executando client.search(intersects=MultiPoint)...")

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
    covered_focuses_by_item: Dict = None
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

        # ----------------------------------------------------
        # Criar feature
        # ----------------------------------------------------

        feature = QgsFeature(
            layer.fields()
        )

        feature.setGeometry(
            multipolygon
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
        "d:/imagens_bdc"
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
    log_message("Consulta espacial: intersects / MultiPoint")
    log_message("Buffer: 0")
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
        intersects_geometry,
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
        covered_focuses_by_item=covered_focuses_by_item
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
        covered_focuses_by_item
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
    covered_focuses: List[Dict]
):
    """Move o raster para os grupos das feições cobertas pelo item."""

    if not covered_focuses:
        log_message(
            f"[DEBUG GRUPO] Nenhuma feição associada a "
            f"'{raster_layer.name()}'."
        )
        return

    root = QgsProject.instance().layerTreeRoot()

    for record in covered_focuses:

        group = get_or_create_focus_group(record)

        # ----------------------------------------------------
        # Verificar se o raster já está dentro do grupo
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
        # Adicionar a camada ao grupo
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
        # Localizar o nó original
        # ----------------------------------------------------
        old_node = root.findLayer(
            raster_layer.id()
        )

        # ----------------------------------------------------
        # Remover o nó original
        # ----------------------------------------------------
        if old_node is not None and old_node is not new_node:

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
        covered_focuses_by_item
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

        raster_layer = iface.addRasterLayer(
            vrt_path,
            f"{item.id}_SWIR2_NIR_RED"
        )

        if raster_layer is None or not raster_layer.isValid():

            log_message(
                f"[ERRO] Não foi possível carregar "
                f"o VRT no QGIS: {vrt_path}"
            )

            continue

        log_message(
            f"[DEBUG] VRT carregado com sucesso no QGIS: "
            f"{raster_layer.name()}"
        )

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

        add_raster_to_focus_groups(
            raster_layer,
            covered_focuses
        )