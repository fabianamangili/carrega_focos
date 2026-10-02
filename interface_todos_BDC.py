import os
import pystac_client
import json
import requests

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
    QDate
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

        # ----------------------------------------------------
        # Composição padrão:
        # R = SWIR-2
        # G = NIR
        # B = RED
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Composição padrão:
        # R = SWIR-2
        # G = NIR
        # B = RED
        # ----------------------------------------------------

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
            "Red /NIR /Green"
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

    print(f"[DEBUG] {message}")


# ============================================================
# CONFIGURAÇÃO DO SATÉLITE
# ============================================================

def get_satellite_config(satellite: str) -> Dict:

    config = SATELLITE_CONFIG.get(
        satellite
    )

    if config is None:

        raise ValueError(
            f"Satélite '{satellite}' "
            f"não possui configuração."
        )

    return config


# ============================================================
# CONECTAR AO STAC
# ============================================================

def connect_to_stac(
    url: str
) -> pystac_client.Client:

    try:

        client = pystac_client.Client.open(
            url
        )

        log_message(
            f"Conectado ao STAC: {url}"
        )

        return client

    except Exception as e:

        log_message(
            f"Erro ao conectar ao STAC: {e}"
        )

        return None


# ============================================================
# VALIDAR ASSETS DO ITEM
# ============================================================

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
# BUSCAR ITENS NO STAC POR BBOX
# ============================================================

def search_items_by_bbox(
    client: pystac_client.Client,
    bbox: List[float],
    start_date: str,
    end_date: str,
    collections: List[str],
    limit: int = 100
) -> List:

    try:

        datetime_range = (
            f"{start_date}/{end_date}"
        )

        # ----------------------------------------------------
        # Registrar parâmetros
        # ----------------------------------------------------

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
            f"Datetime: {datetime_range}"
        )

        log_message(
            f"Limit: {limit}"
        )

        # ----------------------------------------------------
        # Validar BBOX
        # ----------------------------------------------------

        if (
            not bbox
            or len(bbox) != 4
        ):

            log_message(
                "BBOX inválido."
            )

            return []

        minx, miny, maxx, maxy = bbox

        if (
            minx >= maxx
            or miny >= maxy
        ):

            log_message(
                "BBOX inválido: "
                "min/max incorretos."
            )

            return []

        # ----------------------------------------------------
        # Geometria do BBOX
        #
        # Usada SOMENTE para diagnóstico.
        # Não será usada para excluir itens.
        # ----------------------------------------------------

        bbox_geometry = QgsGeometry.fromRect(
            QgsRectangle(
                minx,
                miny,
                maxx,
                maxy
            )
        )

        # ----------------------------------------------------
        # CONSULTA STAC
        # ----------------------------------------------------

        log_message(
            "Executando client.search()..."
        )

        item_search = client.search(
            collections=collections,
            datetime=datetime_range,
            bbox=bbox,
            limit=limit
        )

        # ----------------------------------------------------
        # Recuperar itens
        # ----------------------------------------------------

        items = list(
            item_search.get_items()
        )

        # ----------------------------------------------------
        # Ordenar: mais recentes primeiro
        # ----------------------------------------------------

        items = sorted(
            items,
            key=lambda item: (
                item.datetime
                if item.datetime
                else datetime.min
            ),
            reverse=True
        )

        log_message(
            f"Total de itens retornados pelo STAC: "
            f"{len(items)}"
        )

        # ----------------------------------------------------
        # Diagnóstico de interseção
        #
        # IMPORTANTE:
        # NÃO remover itens aqui.
        # ----------------------------------------------------

        for item in items:

            item_datetime = (
                item.datetime
                if item.datetime
                else None
            )

            intersects = "N/A"

            if item.geometry:

                try:

                    item_geometry = (
                        QgsJsonUtils.geometryFromGeoJson(
                            json.dumps(
                                item.geometry
                            )
                        )
                    )

                    if (
                        item_geometry
                        and not item_geometry.isEmpty()
                    ):

                        intersects = (
                            item_geometry.intersects(
                                bbox_geometry
                            )
                        )

                except Exception as e:

                    log_message(
                        f"Não foi possível validar "
                        f"geometricamente o item "
                        f"{item.id}: {e}"
                    )

            else:

                log_message(
                    f"Item {item.id} "
                    f"não possui geometry."
                )

            log_message(
                f"Item: {item.id}"
            )

            log_message(
                f"  datetime: "
                f"{item_datetime}"
            )

            log_message(
                f"  intersects BBOX: "
                f"{intersects}"
            )

        log_message(
            "Itens retornados pelo STAC "
            "serão mantidos para seleção."
        )

        log_message(
            "================================================"
        )

        # ----------------------------------------------------
        # IMPORTANTE:
        # Retornar os itens originais do STAC
        # ----------------------------------------------------

        return items

    except Exception as e:

        log_message(
            f"Erro ao buscar itens por BBOX: {e}"
        )

        return []

# ============================================================
# BBOX MAP TOOL
# ============================================================

class BBoxMapTool(QgsMapTool):

    def __init__(self, canvas, callback):

        super().__init__(canvas)

        self.canvas = canvas
        self.callback = callback

        self.start_point = None
        self.current_point = None
        self.is_drawing = False

        # ====================================================
        # Rubber Band
        # ====================================================

        self.rubber_band = QgsRubberBand(
            canvas,
            QgsWkbTypes.PolygonGeometry
        )

        self.rubber_band.setColor(
            QColor(255, 0, 0, 100)
        )

        self.rubber_band.setWidth(2)

        self.rubber_band.setFillColor(
            QColor(255, 0, 0, 40)
        )

    # ========================================================
    # CLIQUE
    # ========================================================

    def canvasPressEvent(self, event):

        log_message(
            "!!! CLIQUE RECEBIDO PELO BBOXMAPTOOL !!!"
        )

        if event.button() != Qt.LeftButton:
            return

        point = self.toMapCoordinates(
            event.pos()
        )

        # ----------------------------------------------------
        # Primeiro clique
        # ----------------------------------------------------

        if not self.is_drawing:

            self.start_point = QgsPointXY(point)
            self.current_point = QgsPointXY(point)

            self.is_drawing = True

            self.rubber_band.reset(
                QgsWkbTypes.PolygonGeometry
            )

            log_message(
                "Primeiro ponto do BBOX selecionado."
            )

            log_message(
                f"X={point.x()} | Y={point.y()}"
            )

            return

        # ----------------------------------------------------
        # Segundo clique
        # ----------------------------------------------------

        self.current_point = QgsPointXY(point)

        log_message(
            "Segundo ponto do BBOX selecionado."
        )

        log_message(
            f"X={point.x()} | Y={point.y()}"
        )

        # ----------------------------------------------------
        # Criar rectangle
        # ----------------------------------------------------

        rectangle = self.rectangle()

        if rectangle is None:

            log_message(
                "BBOX inválido: área com tamanho zero."
            )

            return

        # ----------------------------------------------------
        # Atualizar desenho final
        # ----------------------------------------------------

        self.show_rectangle(
            self.start_point,
            self.current_point
        )

        log_message(
            "BBOX desenhado no CRS do Canvas:"
        )

        log_message(
            rectangle.toString()
        )

        # ----------------------------------------------------
        # Guardar callback
        # ----------------------------------------------------

        callback = self.callback

        # ----------------------------------------------------
        # Limpar estado
        # ----------------------------------------------------

        self.start_point = None
        self.current_point = None
        self.is_drawing = False

        # ----------------------------------------------------
        # Limpar visual
        # ----------------------------------------------------

        self.rubber_band.reset(
            QgsWkbTypes.PolygonGeometry
        )

        # ----------------------------------------------------
        # Retornar BBOX
        # ----------------------------------------------------

        callback(rectangle)

    # ========================================================
    # MOVIMENTO DO MOUSE
    # ========================================================

    def canvasMoveEvent(self, event):

        if not self.is_drawing:
            return

        point = self.toMapCoordinates(
            event.pos()
        )

        self.current_point = QgsPointXY(point)

        self.show_rectangle(
            self.start_point,
            self.current_point
        )

    # ========================================================
    # DESENHAR RETÂNGULO
    # ========================================================

    def show_rectangle(
        self,
        start_point,
        end_point
    ):

        if (
            start_point is None
            or end_point is None
        ):
            return

        xmin = min(
            start_point.x(),
            end_point.x()
        )

        xmax = max(
            start_point.x(),
            end_point.x()
        )

        ymin = min(
            start_point.y(),
            end_point.y()
        )

        ymax = max(
            start_point.y(),
            end_point.y()
        )

        # ----------------------------------------------------
        # Evitar retângulo de tamanho zero
        # ----------------------------------------------------

        if xmin == xmax or ymin == ymax:
            return

        # ----------------------------------------------------
        # Criar vértices
        # ----------------------------------------------------

        points = [
            QgsPointXY(xmin, ymin),
            QgsPointXY(xmin, ymax),
            QgsPointXY(xmax, ymax),
            QgsPointXY(xmax, ymin)
        ]

        # ----------------------------------------------------
        # Atualizar RubberBand
        # ----------------------------------------------------

        self.rubber_band.reset(
            QgsWkbTypes.PolygonGeometry
        )

        for point in points:

            self.rubber_band.addPoint(
                point,
                False
            )

        self.rubber_band.closePoints(
            True
        )

        self.rubber_band.show()

    # ========================================================
    # QGSRECTANGLE
    # ========================================================

    def rectangle(self):

        if (
            self.start_point is None
            or self.current_point is None
        ):
            return None

        xmin = min(
            self.start_point.x(),
            self.current_point.x()
        )

        xmax = max(
            self.start_point.x(),
            self.current_point.x()
        )

        ymin = min(
            self.start_point.y(),
            self.current_point.y()
        )

        ymax = max(
            self.start_point.y(),
            self.current_point.y()
        )

        if xmin == xmax or ymin == ymax:
            return None

        return QgsRectangle(
            xmin,
            ymin,
            xmax,
            ymax
        )

    # ========================================================
    # LIMPAR
    # ========================================================

    def clear(self):

        self.rubber_band.reset(
            QgsWkbTypes.PolygonGeometry
        )

        self.start_point = None
        self.current_point = None
        self.is_drawing = False

    # ========================================================
    # DESATIVAR
    # ========================================================

    def deactivate(self):

        self.clear()

        super().deactivate()

# ============================================================
# TRANSFORMAR BBOX PARA EPSG:4326
# ============================================================

def transform_bbox_to_wgs84(
    rectangle: QgsRectangle
) -> List[float]:

    canvas_crs = (
        iface.mapCanvas()
        .mapSettings()
        .destinationCrs()
    )

    wgs84_crs = (
        QgsCoordinateReferenceSystem(
            "EPSG:4326"
        )
    )

    transform = QgsCoordinateTransform(
        canvas_crs,
        wgs84_crs,
        QgsProject.instance()
    )

    # --------------------------------------------------------
    # Transformação do bounding box
    # --------------------------------------------------------

    transformed_bbox = (
        transform.transformBoundingBox(
            rectangle
        )
    )

    bbox = [
        transformed_bbox.xMinimum(),
        transformed_bbox.yMinimum(),
        transformed_bbox.xMaximum(),
        transformed_bbox.yMaximum()
    ]

    log_message(
        f"CRS do Canvas: "
        f"{canvas_crs.authid()}"
    )

    log_message(
        f"BBOX transformado para EPSG:4326: "
        f"{bbox}"
    )

    return bbox


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

        vrt_dataset = gdal.BuildVRT(
            vrt_path,
            hrefs,
            options=vrt_options
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
    # Amazonia / CBERS
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
# GERAR NOME DO VRT
# ============================================================

def generate_vrt_filename(
    satellite: str,
    item
) -> str:

    date = (
        item.datetime.strftime(
            "%Y-%m-%d"
        )
        if item.datetime
        else "unknown_date"
    )

    formatted_date = (
        date.replace("-", "")
    )

    # --------------------------------------------------------
    # Landsat
    # --------------------------------------------------------

    if satellite == "Landsat":

        parts = item.id.split("_")

        if len(parts) >= 4:

            sensor = parts[0]

            orbit_point = parts[2]

            return (
                f"{sensor}_"
                f"{orbit_point}_"
                f"{formatted_date}.vrt"
            )

        return (
            f"Landsat_"
            f"{formatted_date}.vrt"
        )

    # --------------------------------------------------------
    # Sentinel-2
    # --------------------------------------------------------

    if satellite == "Sentinel-2":

        item_tile = get_item_tile(
            item,
            satellite
        )

        item_tile = str(
            item_tile
        ).replace(
            "/",
            "_"
        ).replace(
            "\\",
            "_"
        )

        return (
            f"S2_"
            f"{item_tile}_"
            f"{formatted_date}.vrt"
        )

    # --------------------------------------------------------
    # Amazonia / CBERS
    # --------------------------------------------------------

    sensor_name = (
        satellite.replace(
            "-",
            "_"
        )
    )

    item_tile = get_item_tile(
        item,
        satellite
    )

    item_tile = str(
        item_tile
    ).replace(
        "/",
        "_"
    ).replace(
        "\\",
        "_"
    )

    if item_tile != "N/A":

        return (
            f"{sensor_name}_"
            f"{item_tile}_"
            f"{formatted_date}.vrt"
        )

    return (
        f"{sensor_name}_"
        f"{formatted_date}.vrt"
    )


# ============================================================
# GERAR VRTS E CARREGAR NO QGIS
# ============================================================

def generate_and_load_vrts(
    satellite: str,
    query_bands: List[str],
    selected_items: List,
    output_dir: str
):

    if not os.path.exists(
        output_dir
    ):

        os.makedirs(
            output_dir,
            exist_ok=True
        )

        log_message(
            f"Diretório criado: "
            f"{output_dir}"
        )

    for item in selected_items:

        date = (
            item.datetime.strftime(
                "%Y-%m-%d"
            )
            if item.datetime
            else "unknown"
        )

        log_message(
            f"Processando item: "
            f"{item.id}"
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
                f"VRT NÃO criado para "
                f"{item.id}."
            )

            continue

        hrefs = validation[
            "hrefs"
        ]

        if not hrefs:

            log_message(
                f"Nenhum asset válido "
                f"para {item.id}."
            )

            continue

        # ----------------------------------------------------
        # Nome do VRT
        # ----------------------------------------------------

        vrt_filename = (
            generate_vrt_filename(
                satellite,
                item
            )
        )

        vrt_path = os.path.join(
            output_dir,
            vrt_filename
        )

        # ----------------------------------------------------
        # Criar VRT
        # ----------------------------------------------------

        if create_vrt(
            vrt_path,
            hrefs
        ):

            vrt_layer = QgsRasterLayer(
                vrt_path,
                vrt_filename
            )

            if not vrt_layer.isValid():

                log_message(
                    f"A camada VRT "
                    f"'{vrt_filename}' "
                    f"não é válida."
                )

            else:

                log_message(
                    f"Camada VRT "
                    f"'{vrt_filename}' "
                    f"carregada com sucesso."
                )

                QgsProject.instance().addMapLayer(
                    vrt_layer
                )

                iface.mapCanvas().refresh()


# ============================================================
# THUMBNAIL
# ============================================================

def enhance_thumbnail(
    thumbnail_url: str,
    satellite: str
) -> QPixmap:

    try:

        if (
            not isinstance(
                thumbnail_url,
                str
            )
            or not thumbnail_url.startswith(
                "http"
            )
        ):

            log_message(
                f"URL inválida para thumbnail: "
                f"{thumbnail_url}"
            )

            return QPixmap()

        log_message(
            f"Baixando thumbnail: "
            f"{thumbnail_url}"
        )

        response = requests.get(
            thumbnail_url,
            timeout=10
        )

        response.raise_for_status()

        img = Image.open(
            BytesIO(
                response.content
            )
        )

        if satellite == "Landsat":

            brightness_factor = 6.0
            contrast_factor = 0.7

        else:

            brightness_factor = 2.5
            contrast_factor = 1.8

        enhancer = (
            ImageEnhance.Brightness(img)
        )

        bright_img = enhancer.enhance(
            brightness_factor
        )

        enhancer = (
            ImageEnhance.Contrast(
                bright_img
            )
        )

        final_img = enhancer.enhance(
            contrast_factor
        )

        img_byte_arr = BytesIO()

        final_img.save(
            img_byte_arr,
            format="PNG"
        )

        qimage = QImage.fromData(
            img_byte_arr.getvalue()
        )

        if qimage.isNull():

            log_message(
                "Erro: QImage é nulo."
            )

            return QPixmap()

        pixmap = QPixmap.fromImage(
            qimage
        )

        log_message(
            f"Thumbnail ajustado com sucesso "
            f"para {satellite}."
        )

        return pixmap

    except Exception as e:

        log_message(
            f"Erro ao processar thumbnail: {e}"
        )

        return QPixmap()


# ============================================================
# SELECIONAR IMAGENS DISPONÍVEIS
# ============================================================
def select_available_items(
    satellite: str,
    bbox: List[float],
    items: List
):

    dialog = QDialog()

    dialog.setWindowTitle(
        f"Imagens Disponíveis - "
        f"{satellite}"
    )

    layout = QVBoxLayout()

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
        QTableWidget.MultiSelection
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
        # Nome do satélite
        # ----------------------------------------------------

        satellite_name = satellite

        if (
            satellite == "Landsat"
            and item.id.startswith(
                "LC08"
            )
        ):

            satellite_name = "Landsat 8"

        elif (
            satellite == "Landsat"
            and item.id.startswith(
                "LC09"
            )
        ):

            satellite_name = "Landsat 9"

        # ----------------------------------------------------
        # Identificação espacial
        #
        # IMPORTANTE:
        # NÃO é utilizada como filtro.
        # É apenas informativa.
        # ----------------------------------------------------

        item_tile = get_item_tile(
            item,
            satellite
        )

        log_message(
            f"Item {item.id} - "
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
        # Cloud cover
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
                sat=satellite
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

                    label.setPixmap(
                        pixmap.scaled(
                            800,
                            800,
                            Qt.KeepAspectRatio,
                            Qt.SmoothTransformation
                        )
                    )

                    label.setAlignment(
                        Qt.AlignCenter
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
    # BOTÕES DE SELEÇÃO
    # ========================================================

    select_all_btn = QPushButton(
        "Selecionar Tudo"
    )

    deselect_all_btn = QPushButton(
        "Desselecionar Tudo"
    )

    back_btn = QPushButton(
        "Voltar"
    )

    btn_layout = QHBoxLayout()

    btn_layout.addWidget(
        select_all_btn
    )

    btn_layout.addWidget(
        deselect_all_btn
    )

    btn_layout.addWidget(
        back_btn
    )

    layout.addWidget(
        QLabel(
            "Imagens disponíveis "
            "para o BBOX:"
        )
    )

    layout.addWidget(
        table
    )

    layout.addLayout(
        btn_layout
    )

    # ========================================================
    # QDIALOG BUTTON BOX
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
    # EVENTOS
    # ========================================================

    select_all_btn.clicked.connect(
        table.selectAll
    )

    deselect_all_btn.clicked.connect(
        table.clearSelection
    )

    # --------------------------------------------------------
    # Voltar / Cancelar
    # --------------------------------------------------------

    back_btn.clicked.connect(
        dialog.reject
    )

    button_box.rejected.connect(
        dialog.reject
    )

    # --------------------------------------------------------
    # OK
    #
    # IMPORTANTE:
    # Não usar accept_dialog aqui.
    # Essa função não existe neste escopo.
    # --------------------------------------------------------

    button_box.accepted.connect(
        dialog.accept
    )

    log_message(
        "Diálogo de seleção de imagens configurado."
    )

    log_message(
        f"Total de itens exibidos: "
        f"{len(items)}"
    )

    # ========================================================
    # EXECUTAR DIÁLOGO
    # ========================================================

    result = dialog.exec_()

    log_message(
        "================================================"
    )

    log_message(
        "RESULTADO DO DIÁLOGO DE SELEÇÃO"
    )

    log_message(
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
    # RECUPERAR LINHAS SELECIONADAS
    # ========================================================

    selected_rows = [
        index.row()
        for index
        in table
        .selectionModel()
        .selectedRows()
    ]

    # --------------------------------------------------------
    # Nenhuma linha selecionada
    # --------------------------------------------------------

    if not selected_rows:

        log_message(
            "Nenhuma imagem foi selecionada."
        )

        return []

    # --------------------------------------------------------
    # Recuperar itens STAC
    # --------------------------------------------------------

    selected_items = [
        items[row]
        for row in selected_rows
    ]

    # ========================================================
    # LOG DOS ITENS SELECIONADOS
    # ========================================================

    log_message(
        f"{len(selected_items)} "
        f"imagem(ns) selecionada(s)."
    )

    for item in selected_items:

        log_message(
            f"Imagem selecionada: "
            f"{item.id}"
        )

    # ========================================================
    # RETORNAR
    # ========================================================

    return selected_items
# ============================================================
# INTERFACE PRINCIPAL
# ============================================================

def get_user_input():

    while True:

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

        layout = QVBoxLayout()

        form_layout = QFormLayout()

        # ----------------------------------------------------
        # Satélite
        # ----------------------------------------------------

        satellite_combo = QComboBox()

        satellite_combo.addItems(
            [
                "Landsat",
                "Sentinel-2",
                "Amazonia-1",
                "CBERS-4-MUX",
                "CBERS-4-WFI",
                "CBERS-4A-MUX",
                "CBERS-4A-WFI"
            ]
        )

        form_layout.addRow(
            "Satélite:",
            satellite_combo
        )

        # ----------------------------------------------------
        # Bandas
        # ----------------------------------------------------

        query_bands_input = QLineEdit(
            SATELLITE_CONFIG[
                "Landsat"
            ]["default_bands"]
        )

        form_layout.addRow(
            "Bandas "
            "(separadas por vírgula):",
            query_bands_input
        )

        # ----------------------------------------------------
        # Datas
        # ----------------------------------------------------

        hoje = datetime.today()

        ontem = (
            hoje
            - timedelta(days=1)
        )

        primeiro_dia_mes_anterior = (
            (
                hoje.replace(day=1)
                - timedelta(days=1)
            )
            .replace(day=1)
        )

        # ----------------------------------------------------
        # Data inicial
        # ----------------------------------------------------

        start_date_input = (
            QDateTimeEdit()
        )

        start_date_input.setDisplayFormat(
            "yyyy-MM-dd"
        )

        start_date_input.setCalendarPopup(
            True
        )

        start_date_input.setDate(
            QDate(
                primeiro_dia_mes_anterior.year,
                primeiro_dia_mes_anterior.month,
                primeiro_dia_mes_anterior.day
            )
        )

        # ----------------------------------------------------
        # Data final
        # ----------------------------------------------------

        end_date_input = (
            QDateTimeEdit()
        )

        end_date_input.setDisplayFormat(
            "yyyy-MM-dd"
        )

        end_date_input.setCalendarPopup(
            True
        )

        end_date_input.setDate(
            QDate(
                ontem.year,
                ontem.month,
                ontem.day
            )
        )

        form_layout.addRow(
            "Data de Início "
            "(YYYY-MM-DD):",
            start_date_input
        )

        form_layout.addRow(
            "Data de Fim "
            "(YYYY-MM-DD):",
            end_date_input
        )

        # ----------------------------------------------------
        # Diretório
        # ----------------------------------------------------

        out_dir_input = QLineEdit(
            "d:/imagens_bdc"
        )

        form_layout.addRow(
            "Diretório de Saída:",
            out_dir_input
        )

        # ----------------------------------------------------
        # Selecionar diretório
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # Botão BBOX
        # ----------------------------------------------------

        draw_bbox_btn = QPushButton(
            "Desenhar BBOX no Canvas"
        )

        draw_bbox_btn.setStyleSheet(
            "font-weight: bold; "
            "padding: 7px;"
        )

        # ----------------------------------------------------
        # Google Hybrid
        # ----------------------------------------------------

        google_hybrid_btn = QPushButton(
            "Carregar Google Maps Hybrid"
        )

        google_hybrid_btn.setStyleSheet(
            "font-weight: bold; "
            "padding: 5px;"
        )

        # ----------------------------------------------------
        # Variáveis para BBOX
        # ----------------------------------------------------

        selected_bbox = {
            "value": None
        }

        bbox_map_tool = {
            "value": None
        }

        previous_map_tool = {
            "value": None
        }

        # ====================================================
        # EVENT LOOP DO DIÁLOGO
        # ====================================================

        from PyQt5.QtCore import QEventLoop

        dialog_loop = QEventLoop()

        dialog_result = {
            "value": QDialog.Rejected
        }

        # ----------------------------------------------------
        # Atualizar campos
        # ----------------------------------------------------

        def update_fields():

            satellite = (
                satellite_combo.currentText()
            )

            config = get_satellite_config(
                satellite
            )

            query_bands_input.setText(
                config[
                    "default_bands"
                ]
            )

            log_message(
                f"Satélite selecionado: "
                f"{satellite}"
            )

            log_message(
                f"Coleção STAC: "
                f"{config['collections']}"
            )

            log_message(
                f"Bandas padrão: "
                f"{config['default_bands']}"
            )

        satellite_combo.currentTextChanged.connect(
            update_fields
        )

        # ----------------------------------------------------
        # Carregar Google Hybrid
        # ----------------------------------------------------

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

        # ====================================================
        # ATUALIZAR LABEL DO BBOX
        # ====================================================

        bbox_label = QLabel(
            "Nenhum BBOX definido."
        )

        bbox_label.setStyleSheet(
            "color: #666;"
        )

        # ----------------------------------------------------
        # Atualizar label
        # ----------------------------------------------------

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
                    "color: green; "
                    "font-weight: bold;"
                )

        # ====================================================
        # FINALIZAR DESENHO DO BBOX
        # ====================================================

        def finish_bbox(
            rectangle
        ):

            try:

                log_message(
                    "==============================================="
                )

                log_message(
                    "FINALIZANDO BBOX..."
                )

                # --------------------------------------------
                # Transformar para EPSG:4326
                # --------------------------------------------

                bbox = (
                    transform_bbox_to_wgs84(
                        rectangle
                    )
                )

                selected_bbox[
                    "value"
                ] = bbox

                log_message(
                    "BBOX definido com sucesso:"
                )

                log_message(
                    str(bbox)
                )

                # --------------------------------------------
                # Atualizar interface
                # --------------------------------------------

                update_bbox_label()

                # --------------------------------------------
                # Restaurar ferramenta anterior
                # --------------------------------------------

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

                # --------------------------------------------
                # Limpar referência da ferramenta
                # --------------------------------------------

                bbox_map_tool[
                    "value"
                ] = None

                if hasattr(
                    dialog,
                    "bbox_map_tool"
                ):

                    dialog.bbox_map_tool = None

                # --------------------------------------------
                # Atualizar botão
                # --------------------------------------------

                draw_bbox_btn.setText(
                    "BBOX definido ✓"
                )

                draw_bbox_btn.setStyleSheet(
                    "font-weight: bold; "
                    "padding: 7px; "
                    "background-color: #d9f2d9;"
                )

                # --------------------------------------------
                # Mostrar diálogo novamente
                # --------------------------------------------

                dialog.show()

                dialog.raise_()

                dialog.activateWindow()

                dialog.setFocus()

                log_message(
                    "Diálogo principal restaurado."
                )

                log_message(
                    "Aguardando usuário clicar em OK."
                )

                log_message(
                    "==============================================="
                )

            except Exception as e:

                log_message(
                    f"Erro ao finalizar BBOX: {e}"
                )

                dialog.show()

                dialog.raise_()

                dialog.activateWindow()

        # ====================================================
        # INICIAR DESENHO DO BBOX
        # ====================================================

        def draw_bbox():

            canvas = iface.mapCanvas()

            log_message(
                "==============================================="
            )

            log_message(
                "ATIVANDO FERRAMENTA DE DESENHO DO BBOX..."
            )

            # ------------------------------------------------
            # Guardar ferramenta atual
            # ------------------------------------------------

            previous_map_tool[
                "value"
            ] = canvas.mapTool()

            # ------------------------------------------------
            # Criar ferramenta
            # ------------------------------------------------

            tool = BBoxMapTool(
                canvas,
                finish_bbox
            )

            # ------------------------------------------------
            # Manter referência
            # ------------------------------------------------

            dialog.bbox_map_tool = tool

            bbox_map_tool[
                "value"
            ] = tool

            # ------------------------------------------------
            # Ativar ferramenta
            # ------------------------------------------------

            canvas.setMapTool(
                tool
            )

            log_message(
                f"Map tool ativo: "
                f"{type(canvas.mapTool()).__name__}"
            )

            # ------------------------------------------------
            # Esconder diálogo
            #
            # IMPORTANTE:
            # Não chamamos dialog.accept()
            # Não chamamos dialog.reject()
            # Não encerramos o QEventLoop.
            # ------------------------------------------------

            dialog.hide()

            # ------------------------------------------------
            # Dar foco ao Canvas
            # ------------------------------------------------

            canvas.activateWindow()

            canvas.setFocus()

            log_message(
                "Ferramenta de desenho do BBOX ativada."
            )

            log_message(
                "Canvas aguardando dois cliques."
            )

            log_message(
                "==============================================="
            )

        draw_bbox_btn.clicked.connect(
            draw_bbox
        )

        # ====================================================
        # LAYOUT
        # ====================================================

        layout.addLayout(
            form_layout
        )

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

        layout.addWidget(
            bbox_label
        )

        # ====================================================
        # BOTÕES OK / CANCELAR
        # ====================================================

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

        # ====================================================
        # OK
        # ====================================================

        def accept_dialog():

            log_message(
                "==============================================="
            )

            log_message(
                "BOTÃO OK CLICADO."
            )

            bbox = selected_bbox[
                "value"
            ]

            log_message(
                f"BBOX no accept_dialog: {bbox}"
            )

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

            update_bbox_label()

            # --------------------------------------------
            # Guardar resultado
            # --------------------------------------------

            dialog_result[
                "value"
            ] = QDialog.Accepted

            log_message(
                "BBOX válido."
            )

            log_message(
                "Encerrando EventLoop..."
            )

            # --------------------------------------------
            # Fechar somente o EventLoop
            # --------------------------------------------

            if dialog_loop.isRunning():

                dialog_loop.quit()

            log_message(
                "==============================================="
            )

        # ====================================================
        # CANCELAR
        # ====================================================

        def reject_dialog():

            log_message(
                "==============================================="
            )

            log_message(
                "BOTÃO CANCELAR CLICADO."
            )

            dialog_result[
                "value"
            ] = QDialog.Rejected

            # --------------------------------------------
            # Restaurar ferramenta
            # --------------------------------------------

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

            # --------------------------------------------
            # Encerrar EventLoop
            # --------------------------------------------

            if dialog_loop.isRunning():

                dialog_loop.quit()

            log_message(
                "==============================================="
            )

        # ----------------------------------------------------
        # Conectar botões
        # ----------------------------------------------------

        button_box.accepted.connect(
            accept_dialog
        )

        button_box.rejected.connect(
            reject_dialog
        )

        # ====================================================
        # EXECUTAR DIÁLOGO
        #
        # NÃO usar dialog.exec_().
        #
        # O QEventLoop permanece ativo mesmo quando
        # dialog.hide() é chamado para desenhar o BBOX.
        # ====================================================

        log_message(
            "Abrindo diálogo principal..."
        )

        dialog.show()

        dialog.raise_()

        dialog.activateWindow()

        # ----------------------------------------------------
        # Rodar EventLoop
        # ----------------------------------------------------

        dialog_loop.exec_()

        # ====================================================
        # RESULTADO DO DIÁLOGO
        # ====================================================

        result = dialog_result[
            "value"
        ]

        log_message(
            "================================================"
        )

        log_message(
            f"EventLoop retornou: {result}"
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
            f"BBOX após fechamento: "
            f"{selected_bbox['value']}"
        )

        log_message(
            "================================================"
        )

        # ====================================================
        # CANCELADO
        # ====================================================

        if result != QDialog.Accepted:

            log_message(
                "Diálogo cancelado."
            )

            try:
                dialog.close()
            except Exception:
                pass

            return None

        # ====================================================
        # RECUPERAR PARÂMETROS
        # ====================================================

        satellite = (
            satellite_combo.currentText()
        )

        query_bands = [
            band.strip()
            for band
            in query_bands_input
            .text()
            .split(",")
            if band.strip()
        ]

        start_date = (
            start_date_input
            .text()
            .strip()
        )

        end_date = (
            end_date_input
            .text()
            .strip()
        )

        output_dir = (
            out_dir_input
            .text()
            .strip()
        )

        bbox = selected_bbox[
            "value"
        ]

        # ====================================================
        # CONFIGURAÇÃO
        # ====================================================

        config = get_satellite_config(
            satellite
        )

        collections = config[
            "collections"
        ]

        # ====================================================
        # LOG DOS PARÂMETROS
        # ====================================================

        log_message(
            "PASSOU PELO DIÁLOGO."
        )

        log_message(
            f"Satélite: {satellite}"
        )

        log_message(
            f"Collections: {collections}"
        )

        log_message(
            f"BBOX: {bbox}"
        )

        log_message(
            f"Data inicial: {start_date}"
        )

        log_message(
            f"Data final: {end_date}"
        )

        # ====================================================
        # CONECTAR STAC
        # ====================================================

        log_message(
            "Iniciando conexão com STAC..."
        )

        client = connect_to_stac(
            "https://data.inpe.br/bdc/stac/v1/"
        )

        if not client:

            log_message(
                "Não foi possível conectar ao STAC."
            )

            return None

        # ====================================================
        # BUSCAR EXCLUSIVAMENTE PELO BBOX
        # ====================================================

        items = search_items_by_bbox(
            client,
            bbox,
            start_date,
            end_date,
            collections
        )

        # ====================================================
        # NENHUM RESULTADO
        # ====================================================

        if not items:

            log_message(
                "Nenhuma imagem disponível "
                "para o BBOX e período "
                "informados."
            )

            return None

        # ====================================================
        # SELECIONAR CENAS
        # ====================================================

        selected_items = (
            select_available_items(
                satellite,
                bbox,
                items
            )
        )

        if selected_items is None:

            return None

        if not selected_items:

            log_message(
                "Nenhuma imagem selecionada."
            )

            return None

        # ====================================================
        # RETORNAR
        # ====================================================

        return (
            satellite,
            query_bands,
            start_date,
            end_date,
            output_dir,
            bbox,
            selected_items
        )
# ============================================================
# EXECUTAR
# ============================================================

user_input = get_user_input()

if user_input:

    (
        satellite,
        query_bands,
        start_date,
        end_date,
        output_dir,
        bbox,
        selected_items
    ) = user_input

    log_message(
        "=========================================="
    )

    log_message(
        f"Satélite: {satellite}"
    )

    log_message(
        f"BBOX EPSG:4326: {bbox}"
    )

    log_message(
        f"Bandas: {query_bands}"
    )

    log_message(
        f"Data inicial: {start_date}"
    )

    log_message(
        f"Data final: {end_date}"
    )

    log_message(
        f"Imagens selecionadas: "
        f"{len(selected_items)}"
    )

    log_message(
        "=========================================="
    )

    generate_and_load_vrts(
        satellite,
        query_bands,
        selected_items,
        output_dir
    )