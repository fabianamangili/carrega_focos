import os
import pystac_client
import json
import requests

from pystac_client import Client
from typing import List, Dict
from osgeo import gdal
from qgis.core import (
    QgsRasterLayer,
    QgsProject,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsRectangle,
    QgsGeometry,
    QgsPointXY,
    QgsWkbTypes,
    QgsJsonUtils
)
from qgis.gui import (
    QgsMapToolEmitPoint,
    QgsRubberBand
)
from qgis.utils import iface
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QFileDialog,
    QDialogButtonBox,
    QTableWidget,
    QTableWidgetItem,
    QHBoxLayout,
    QLabel,
    QApplication,
    QDateTimeEdit
)
from PyQt5.QtCore import (
    Qt,
    QDate,
    QDateTime,
    QEventLoop
)
from PyQt5.QtGui import (
    QImage,
    QPixmap,
    QColor
)
from datetime import datetime, timedelta
from PIL import Image, ImageEnhance
from io import BytesIO


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
    items: List
):

    # ========================================================
    # CRIAR DIÁLOGO
    # ========================================================

    dialog = QDialog()

    dialog.setModal(False)

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
        5
    )

    table.setHorizontalHeaderLabels(
        [
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
        # Coluna Data
        # ----------------------------------------------------

        table.setItem(
            row,
            0,
            QTableWidgetItem(
                date
            )
        )

        # ----------------------------------------------------
        # Coluna Satélite
        # ----------------------------------------------------

        table.setItem(
            row,
            1,
            QTableWidgetItem(
                satellite_name
            )
        )

        # ----------------------------------------------------
        # Coluna Tile / Órbita
        # ----------------------------------------------------

        table.setItem(
            row,
            2,
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
            3,
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

                    log_message(
                        f"Abrindo thumbnail: "
                        f"{url}"
                    )

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
                4,
                view_btn
            )

        else:

            table.setItem(
                row,
                4,
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
    # INFORMAÇÃO DO BBOX
    # ========================================================

    bbox_text = (
        "BBOX utilizado na busca:\n"
        f"Xmin: {bbox[0]:.6f} | "
        f"Ymin: {bbox[1]:.6f} | "
        f"Xmax: {bbox[2]:.6f} | "
        f"Ymax: {bbox[3]:.6f}"
    )

    bbox_label = QLabel(
        bbox_text
    )

    bbox_label.setStyleSheet(
        "color: #555;"
    )

    layout.addWidget(
        bbox_label
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
        f"QDialog.Accepted: "
        f"{QDialog.Accepted}"
    )

    log_message(
        f"QDialog.Rejected: "
        f"{QDialog.Rejected}"
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
# TRANSFORMAR BBOX PARA EPSG:4326
# ============================================================

def transform_bbox_to_wgs84(
    rectangle
) -> List[float]:

    try:

        canvas = iface.mapCanvas()

        source_crs = (
            canvas
            .mapSettings()
            .destinationCrs()
        )

        target_crs = (
            QgsCoordinateReferenceSystem(
                "EPSG:4326"
            )
        )

        # ----------------------------------------------------
        # Verificar se já está em WGS84
        # ----------------------------------------------------

        if (
            source_crs.authid()
            == "EPSG:4326"
        ):

            return [
                rectangle.xMinimum(),
                rectangle.yMinimum(),
                rectangle.xMaximum(),
                rectangle.yMaximum()
            ]

        # ----------------------------------------------------
        # Transformação
        # ----------------------------------------------------

        transform = QgsCoordinateTransform(
            source_crs,
            target_crs,
            QgsProject.instance()
        )

        transformed_rectangle = (
            transform.transformBoundingBox(
                rectangle
            )
        )

        bbox = [
            transformed_rectangle.xMinimum(),
            transformed_rectangle.yMinimum(),
            transformed_rectangle.xMaximum(),
            transformed_rectangle.yMaximum()
        ]

        log_message(
            f"BBOX transformado para "
            f"EPSG:4326: {bbox}"
        )

        return bbox

    except Exception as e:

        log_message(
            f"Erro ao transformar BBOX "
            f"para EPSG:4326: {e}"
        )

        raise
        
# ============================================================
# FERRAMENTA PARA DESENHAR BBOX NO CANVAS
# ============================================================

class BBoxMapTool(QgsMapTool):

    def __init__(
        self,
        canvas,
        callback
    ):

        super().__init__(
            canvas
        )

        self.canvas = canvas

        self.callback = callback

        self.first_point = None

        self.second_point = None

        self.rubber_band = (
            QgsRubberBand(
                canvas,
                Qgis.GeometryType.Polygon
            )
        )

        self.rubber_band.setColor(
            QColor(
                255,
                0,
                0,
                100
            )
        )

        self.rubber_band.setFillColor(
            QColor(
                255,
                0,
                0,
                40
            )
        )

        self.rubber_band.setWidth(
            2
        )

    # ========================================================
    # CLIQUE NO CANVAS
    # ========================================================

    def canvasPressEvent(
        self,
        event
    ):

        log_message(
            "!!! CLIQUE RECEBIDO "
            "PELO BBOXMAPTOOL !!!"
        )

        point = (
            self.toMapCoordinates(
                event.pos()
            )
        )

        # ----------------------------------------------------
        # Primeiro ponto
        # ----------------------------------------------------

        if self.first_point is None:

            self.first_point = point

            log_message(
                "Primeiro ponto do "
                "BBOX selecionado."
            )

            log_message(
                f"X={point.x()} | "
                f"Y={point.y()}"
            )

            return

        # ----------------------------------------------------
        # Segundo ponto
        # ----------------------------------------------------

        self.second_point = point

        log_message(
            "Segundo ponto do "
            "BBOX selecionado."
        )

        log_message(
            f"X={point.x()} | "
            f"Y={point.y()}"
        )

        # ----------------------------------------------------
        # Criar retângulo definitivo
        # ----------------------------------------------------

        xmin = min(
            self.first_point.x(),
            self.second_point.x()
        )

        xmax = max(
            self.first_point.x(),
            self.second_point.x()
        )

        ymin = min(
            self.first_point.y(),
            self.second_point.y()
        )

        ymax = max(
            self.first_point.y(),
            self.second_point.y()
        )

        rectangle = QgsRectangle(
            xmin,
            ymin,
            xmax,
            ymax
        )

        # ----------------------------------------------------
        # Mostrar BBOX definitivo
        # ----------------------------------------------------

        geometry = (
            QgsGeometry.fromRect(
                rectangle
            )
        )

        self.rubber_band.setToGeometry(
            geometry,
            None
        )

        self.rubber_band.show()

        log_message(
            "BBOX desenhado no CRS "
            "do Canvas:"
        )

        log_message(
            f"{xmin:.16f},"
            f"{ymin:.16f} : "
            f"{xmax:.16f},"
            f"{ymax:.16f}"
        )

        crs_canvas = (
            self.canvas
            .mapSettings()
            .destinationCrs()
            .authid()
        )

        log_message(
            f"CRS do Canvas: {crs_canvas}"
        )

        # ----------------------------------------------------
        # Finalizar seleção
        # ----------------------------------------------------

        self.callback(
            rectangle
        )

    # ========================================================
    # MOVIMENTO DO MOUSE
    # ========================================================

    def canvasMoveEvent(
        self,
        event
    ):

        # ----------------------------------------------------
        # Ainda não existe primeiro ponto
        # ----------------------------------------------------

        if self.first_point is None:

            return

        # ----------------------------------------------------
        # Posição atual do mouse
        # ----------------------------------------------------

        current_point = (
            self.toMapCoordinates(
                event.pos()
            )
        )

        # ----------------------------------------------------
        # Criar retângulo provisório
        # ----------------------------------------------------

        xmin = min(
            self.first_point.x(),
            current_point.x()
        )

        xmax = max(
            self.first_point.x(),
            current_point.x()
        )

        ymin = min(
            self.first_point.y(),
            current_point.y()
        )

        ymax = max(
            self.first_point.y(),
            current_point.y()
        )

        rectangle = QgsRectangle(
            xmin,
            ymin,
            xmax,
            ymax
        )

        # ----------------------------------------------------
        # Atualizar desenho
        # ----------------------------------------------------

        geometry = (
            QgsGeometry.fromRect(
                rectangle
            )
        )

        self.rubber_band.setToGeometry(
            geometry,
            None
        )

        self.rubber_band.show()

    # ========================================================
    # LIMPAR FERRAMENTA
    # ========================================================

    def clear(
        self
    ):

        if self.rubber_band:

            self.rubber_band.reset(
                Qgis.GeometryType.Polygon
            )

            self.rubber_band.hide()

        self.first_point = None

        self.second_point = None

    # ========================================================
    # DESATIVAR FERRAMENTA
    # ========================================================

    def deactivate(
        self
    ):

        log_message(
            "[DEBUG] Desativando BBoxMapTool..."
        )

        self.clear()

        super().deactivate()
        
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
# BUSCAR ITENS STAC POR BBOX
# ============================================================

def search_items_by_bbox(
    client,
    bbox: List[float],
    start_date: str,
    end_date: str,
    collections: List[str]
) -> List:

    log_message(
        "================================================"
    )

    log_message(
        "CONSULTA STAC POR BBOX"
    )

    log_message(
        f"Collections: {collections}"
    )

    log_message(
        f"BBOX: {bbox}"
    )

    log_message(
        f"Datetime: "
        f"{start_date}/{end_date}"
    )

    try:

        # ----------------------------------------------------
        # Validar BBOX
        # ----------------------------------------------------

        if not bbox or len(bbox) != 4:

            log_message(
                "ERRO: BBOX inválido."
            )

            return []

        # ----------------------------------------------------
        # Validar collections
        # ----------------------------------------------------

        if not collections:

            log_message(
                "ERRO: nenhuma collection "
                "foi informada."
            )

            return []

        # ----------------------------------------------------
        # Intervalo temporal
        # ----------------------------------------------------

        datetime_range = (
            f"{start_date}/{end_date}"
        )

        log_message(
            "Limit: 100"
        )

        log_message(
            "Executando client.search()..."
        )

        # ----------------------------------------------------
        # Consulta STAC
        # ----------------------------------------------------

        search = client.search(
            collections=collections,
            bbox=bbox,
            datetime=datetime_range,
            limit=100
        )

        # ----------------------------------------------------
        # Obter itens
        # ----------------------------------------------------

        items = list(
            search.items()
        )

        log_message(
            f"Total de itens retornados "
            f"pelo STAC: {len(items)}"
        )

        # ----------------------------------------------------
        # Mostrar itens encontrados
        # ----------------------------------------------------

        for item in items:

            log_message(
                f"Item: {item.id}"
            )

            log_message(
                f"  datetime: "
                f"{item.datetime}"
            )

            # ------------------------------------------------
            # Verificar interseção espacial
            # ------------------------------------------------

            try:

                if item.bbox:

                    item_minx = item.bbox[0]
                    item_miny = item.bbox[1]
                    item_maxx = item.bbox[2]
                    item_maxy = item.bbox[3]

                    bbox_minx = bbox[0]
                    bbox_miny = bbox[1]
                    bbox_maxx = bbox[2]
                    bbox_maxy = bbox[3]

                    intersects = not (
                        item_maxx < bbox_minx
                        or item_minx > bbox_maxx
                        or item_maxy < bbox_miny
                        or item_miny > bbox_maxy
                    )

                    log_message(
                        f"  intersects BBOX: "
                        f"{intersects}"
                    )

                else:

                    log_message(
                        "  intersects BBOX: "
                        "não verificado "
                        "(item sem bbox)"
                    )

            except Exception as e:

                log_message(
                    f"  Erro ao verificar "
                    f"interseção: {e}"
                )

        log_message(
            "Itens retornados pelo STAC "
            "serão mantidos para seleção."
        )

        log_message(
            "================================================"
        )

        return items

    except Exception as e:

        log_message(
            "ERRO durante consulta STAC:"
        )

        log_message(
            str(e)
        )

        log_message(
            "================================================"
        )

        return []
        
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
    # BBOX
    # ========================================================

    selected_bbox = {
        "value": None
    }

    bbox_map_tool = {
        "value": None
    }

    previous_map_tool = {
        "value": None
    }

    # ========================================================
    # CONTROLE DO FLUXO
    # ========================================================

    # Resultado final do diálogo principal.
    dialog_result = {
        "accepted": False
    }

    # Event loop que mantém o QGIS responsivo enquanto
    # o diálogo está oculto durante o desenho do BBOX.
    event_loop = QEventLoop()

    # ========================================================
    # BOTÃO DESENHAR BBOX
    # ========================================================

    draw_bbox_btn = QPushButton(
        "Desenhar BBOX no Canvas"
    )

    draw_bbox_btn.setStyleSheet(
        "font-weight: bold; "
        "padding: 7px;"
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
    # LABEL DO BBOX
    # ========================================================

    bbox_label = QLabel(
        "Nenhum BBOX definido."
    )

    bbox_label.setStyleSheet(
        "color: #666;"
    )

    bbox_label.setWordWrap(
        True
    )

    # ========================================================
    # ATUALIZAR LABEL DO BBOX
    # ========================================================

    def update_bbox_label():

        bbox = selected_bbox[
            "value"
        ]

        if bbox:

            bbox_label.setText(
                "BBOX EPSG:4326: "
                f"{bbox[0]:.6f}, "
                f"{bbox[1]:.6f}, "
                f"{bbox[2]:.6f}, "
                f"{bbox[3]:.6f}"
            )

            bbox_label.setStyleSheet(
                "color: #333; "
                "font-weight: bold;"
            )

    # ========================================================
    # FINALIZAR DESENHO DO BBOX
    # ========================================================

    def finish_bbox(
        rectangle
    ):

        try:

            # ------------------------------------------------
            # Transformar para EPSG:4326
            # ------------------------------------------------

            bbox = (
                transform_bbox_to_wgs84(
                    rectangle
                )
            )

            selected_bbox[
                "value"
            ] = bbox

            log_message(
                "================================================"
            )

            log_message(
                "BBOX definido com sucesso:"
            )

            log_message(
                str(bbox)
            )

            # ------------------------------------------------
            # Atualizar label
            # ------------------------------------------------

            update_bbox_label()

            # ------------------------------------------------
            # Restaurar ferramenta anterior
            # ------------------------------------------------

            canvas = (
                iface.mapCanvas()
            )

            if (
                previous_map_tool[
                    "value"
                ] is not None
            ):

                canvas.setMapTool(
                    previous_map_tool[
                        "value"
                    ]
                )

            # ------------------------------------------------
            # Limpar referência da ferramenta
            # ------------------------------------------------

            bbox_map_tool[
                "value"
            ] = None

            if hasattr(
                dialog,
                "bbox_map_tool"
            ):

                dialog.bbox_map_tool = None

            # ------------------------------------------------
            # Atualizar botão
            # ------------------------------------------------

            draw_bbox_btn.setText(
                "BBOX definido ✓"
            )

            draw_bbox_btn.setStyleSheet(
                "font-weight: bold; "
                "padding: 7px; "
                "background-color: #d9f2d9;"
            )

            # ------------------------------------------------
            # Mostrar diálogo novamente
            # ------------------------------------------------

            dialog.show()

            dialog.raise_()

            dialog.activateWindow()

            log_message(
                "Diálogo principal restaurado "
                "após definição do BBOX."
            )

            log_message(
                "Aguardando confirmação pelo botão OK."
            )

            log_message(
                "================================================"
            )

        except Exception as e:

            log_message(
                f"Erro ao finalizar BBOX: {e}"
            )

            dialog.show()

            dialog.raise_()

            dialog.activateWindow()

    # ========================================================
    # INICIAR DESENHO DO BBOX
    # ========================================================

    def draw_bbox():

        canvas = iface.mapCanvas()

        log_message(
            "================================================"
        )

        log_message(
            "ATIVANDO FERRAMENTA DE DESENHO DO BBOX..."
        )

        # ----------------------------------------------------
        # Guardar ferramenta atual
        # ----------------------------------------------------

        previous_map_tool[
            "value"
        ] = canvas.mapTool()

        # ----------------------------------------------------
        # Criar ferramenta
        # ----------------------------------------------------

        tool = BBoxMapTool(
            canvas,
            finish_bbox
        )

        # ----------------------------------------------------
        # Manter referência
        # ----------------------------------------------------

        dialog.bbox_map_tool = tool

        bbox_map_tool[
            "value"
        ] = tool

        # ----------------------------------------------------
        # Ativar ferramenta
        # ----------------------------------------------------

        canvas.setMapTool(
            tool
        )

        log_message(
            f"Map tool ativo: "
            f"{type(canvas.mapTool()).__name__}"
        )

        # ----------------------------------------------------
        # Esconder diálogo
        #
        # IMPORTANTE:
        # Não usamos dialog.exec_().
        # O QEventLoop continua ativo.
        # ----------------------------------------------------

        dialog.hide()

        # ----------------------------------------------------
        # Dar foco ao Canvas
        # ----------------------------------------------------

        canvas.activateWindow()

        canvas.setFocus()

        log_message(
            "Ferramenta de desenho do BBOX ativada."
        )

        log_message(
            "Desenhe o BBOX com dois cliques "
            "no Canvas."
        )

        log_message(
            "================================================"
        )

    draw_bbox_btn.clicked.connect(
        draw_bbox
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
        draw_bbox_btn
    )

    buttons_layout.addWidget(
        google_hybrid_btn
    )

    layout.addLayout(
        buttons_layout
    )

    # --------------------------------------------------------
    # Informação do BBOX
    # --------------------------------------------------------

    layout.addWidget(
        QLabel(
            "Área de busca:"
        )
    )

    layout.addWidget(
        bbox_label
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

        log_message(
            "================================================"
        )

        log_message(
            "BOTÃO OK CLICADO"
        )

        bbox = selected_bbox[
            "value"
        ]

        log_message(
            f"BBOX no accept_dialog: {bbox}"
        )

        # ----------------------------------------------------
        # Validar BBOX
        # ----------------------------------------------------

        if bbox is None:

            log_message(
                "ERRO: nenhum BBOX foi definido."
            )

            bbox_label.setText(
                "Desenhe um BBOX "
                "antes de continuar."
            )

            bbox_label.setStyleSheet(
                "color: red; "
                "font-weight: bold;"
            )

            return

        # ----------------------------------------------------
        # Atualizar label
        # ----------------------------------------------------

        update_bbox_label()

        # ----------------------------------------------------
        # Registrar aceitação
        # ----------------------------------------------------

        dialog_result[
            "accepted"
        ] = True

        log_message(
            "Diálogo principal aceito."
        )

        # ----------------------------------------------------
        # Esconder diálogo
        # ----------------------------------------------------

        dialog.hide()

        # ----------------------------------------------------
        # Encerrar QEventLoop
        # ----------------------------------------------------

        event_loop.quit()

        log_message(
            "Event loop principal encerrado."
        )

        log_message(
            "================================================"
        )

    # ========================================================
    # CANCELAR
    # ========================================================

    def cancel_dialog():

        log_message(
            "================================================"
        )

        log_message(
            "BOTÃO CANCELAR CLICADO"
        )

        dialog_result[
            "accepted"
        ] = False

        # ----------------------------------------------------
        # Restaurar ferramenta caso necessário
        # ----------------------------------------------------

        if (
            bbox_map_tool[
                "value"
            ] is not None
        ):

            canvas = (
                iface.mapCanvas()
            )

            if (
                previous_map_tool[
                    "value"
                ] is not None
            ):

                canvas.setMapTool(
                    previous_map_tool[
                        "value"
                    ]
                )

            try:

                bbox_map_tool[
                    "value"
                ].clear()

            except Exception:
                pass

            bbox_map_tool[
                "value"
            ] = None

            if hasattr(
                dialog,
                "bbox_map_tool"
            ):

                dialog.bbox_map_tool = None

        # ----------------------------------------------------
        # Encerrar event loop
        # ----------------------------------------------------

        event_loop.quit()

        log_message(
            "Event loop encerrado por cancelamento."
        )

        log_message(
            "================================================"
        )

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

    log_message(
        "================================================"
    )

    log_message(
        "EVENT LOOP PRINCIPAL FINALIZADO"
    )

    log_message(
        f"Diálogo aceito: "
        f"{dialog_result['accepted']}"
    )

    log_message(
        f"BBOX após diálogo: "
        f"{selected_bbox['value']}"
    )

    log_message(
        "================================================"
    )

    # ========================================================
    # CANCELAMENTO
    # ========================================================

    if not dialog_result[
        "accepted"
    ]:

        log_message(
            "Diálogo cancelado."
        )

        return None

    # ========================================================
    # RECUPERAR BBOX
    # ========================================================

    bbox = selected_bbox[
        "value"
    ]

    if bbox is None:

        log_message(
            "ERRO: diálogo aceito, "
            "mas BBOX não foi definido."
        )

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
            "ERRO: diretório de saída "
            "não informado."
        )

        QMessageBox.warning(
            iface.mainWindow(),
            "Diretório de saída",
            "Informe um diretório de saída."
        )

        return None

    # ========================================================
    # LOG DOS PARÂMETROS
    # ========================================================

    log_message(
        "PASSOU PELO QDIALOG."
    )

    log_message(
        f"BBOX: {bbox}"
    )

    log_message(
        f"Data inicial automática: "
        f"{start_date}"
    )

    log_message(
        f"Data final automática: "
        f"{end_date}"
    )

    log_message(
        f"Diretório de saída: "
        f"{output_dir}"
    )

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
    # BUSCAR ITENS
    # ========================================================

    log_message(
        "Iniciando busca STAC..."
    )

    log_message(
        f"BBOX: {bbox}"
    )

    log_message(
        f"Período: "
        f"{start_date}/{end_date}"
    )

    log_message(
        f"Collections: {collections}"
    )

    items = search_items_by_bbox(
        client,
        bbox,
        start_date,
        end_date,
        collections
    )

    # ========================================================
    # NENHUM RESULTADO
    # ========================================================

    if not items:

        log_message(
            "Nenhuma imagem disponível "
            "para o BBOX nos últimos "
            "10 dias."
        )

        QMessageBox.information(
            iface.mainWindow(),
            "Nenhuma imagem encontrada",
            "Não foram encontradas imagens "
            "para o BBOX informado no período "
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
            bbox,
            items
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
    # RETORNAR RESULTADO
    #
    # satellite e query_bands permanecem como None
    # nesta etapa para não quebrar a execução existente.
    # ========================================================

    return (
        None,
        None,
        start_date,
        end_date,
        output_dir,
        bbox,
        selected_items
    )
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

        for i, href in enumerate(hrefs, start=1):

            log_message(
                f"[DEBUG] Asset {i}: {href}"
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
        selected_items
    ) = user_input

    log_message(
        "================================================"
    )

    log_message(
        "PARÂMETROS DA EXECUÇÃO"
    )

    log_message(
        f"BBOX EPSG:4326: {bbox}"
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