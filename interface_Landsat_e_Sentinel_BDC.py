import os
from osgeo import gdal
import pystac_client
from typing import List, Dict
from qgis.core import QgsRasterLayer, QgsProject, QgsCoordinateReferenceSystem, QgsCoordinateTransform
from qgis.utils import iface
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QPushButton,
    QFileDialog, QDialogButtonBox, QTableWidget, QTableWidgetItem, QHBoxLayout,
    QLabel, QApplication, QWidget, QDateTimeEdit
)
from PyQt5.QtCore import Qt, QUrl, QDate
from PyQt5.QtGui import QDesktopServices, QImage, QPixmap
from datetime import datetime, timedelta
from PIL import Image, ImageEnhance
import requests
from io import BytesIO


# Função para log de depuração
def log_message(message: str):
    print(f"[DEBUG] {message}")

# Conectar ao cliente STAC
def connect_to_stac(url: str) -> pystac_client.Client:
    try:
        client = pystac_client.Client.open(url)
        log_message(f"Conectado ao STAC: {url}")
        return client
    except Exception as e:
        log_message(f"Erro ao conectar ao STAC: {e}")
        return None

# Buscar itens no STAC por tile
def search_items(client: pystac_client.Client, tile: str, start_date: str, end_date: str, collections: List[str], limit: int = 100) -> List[Dict]:
    try:
        datetime_range = f"{start_date}/{end_date}"
        item_search = client.search(
            collections=collections,
            datetime=datetime_range,
            query={"bdc:tiles": {"eq": tile}},
            limit=limit
        )
        items = list(item_search.get_items())[::-1]
        log_message(f"Encontrados {len(items)} itens para tile {tile}")
        return items
    except Exception as e:
        log_message(f"Erro ao buscar itens: {e}")
        return []

# Buscar itens no STAC por bounding box (extent)
def search_items_by_bbox(client: pystac_client.Client, bbox: List[float], start_date: str, end_date: str, collections: List[str], limit: int = 100) -> List[Dict]:
    try:
        datetime_range = f"{start_date}/{end_date}"
        item_search = client.search(
            collections=collections,
            datetime=datetime_range,
            bbox=bbox,
            limit=limit
        )
        items = list(item_search.get_items())[::-1]
        log_message(f"Encontrados {len(items)} itens para o extent do canvas")
        for item in items:
            log_message(f"Propriedades do item {item.id}: {item.properties}")
        return items
    except Exception as e:
        log_message(f"Erro ao buscar itens por extent: {e}")
        return []

# Criar VRT
def create_vrt(vrt_path: str, hrefs: List[str]) -> bool:
    try:
        vrt_options = gdal.BuildVRTOptions(resampleAlg='nearest', addAlpha=False, separate=True)
        vrt_dataset = gdal.BuildVRT(vrt_path, hrefs, options=vrt_options)
        if vrt_dataset:
            vrt_dataset = None
            log_message(f"VRT criado com sucesso: {vrt_path}")
            return True
        log_message(f"Falha ao criar VRT: {vrt_path}")
        return False
    except Exception as e:
        log_message(f"Erro ao criar VRT: {e}")
        return False

# Gerar VRTs e carregar diretamente no QGIS
def generate_and_load_vrts(satellite: str, tile: str, query_bands: List[str], selected_items: List[Dict], output_dir: str):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        log_message(f"Diretório criado: {output_dir}")

    for item in selected_items:
        date = item.datetime.strftime("%Y-%m-%d")
        hrefs = [f"/vsicurl/{item.assets[band].href}" for band in query_bands if band in item.assets]
        if hrefs:
            if satellite == "Landsat":
                parts = item.id.split("_")
                if len(parts) >= 4:
                    sensor = parts[0]
                    orbit_point = parts[2]
                    formatted_date = date.replace("-", "")
                    vrt_filename = f"{sensor}_{orbit_point}_{formatted_date}.vrt"
                else:
                    vrt_filename = f"Desconhecido_{date.replace('-', '')}.vrt"
            else:  # Sentinel-2
                item_tile = item.properties.get("bdc:tiles", ["Unknown"])[0]
                vrt_filename = f"S2_{item_tile}_{date}.vrt"

            vrt_path = os.path.join(output_dir, vrt_filename)
            if create_vrt(vrt_path, hrefs):
                vrt_layer = QgsRasterLayer(vrt_path, vrt_filename)
                if not vrt_layer.isValid():
                    log_message(f"A camada VRT '{vrt_filename}' não é válida.")
                else:
                    log_message(f"Camada VRT '{vrt_filename}' carregada com sucesso.")
                    QgsProject.instance().addMapLayer(vrt_layer)
#                    iface.mapCanvas().zoomToFeatureExtent(vrt_layer.extent())
                    iface.mapCanvas().refresh()
#                    iface.mapCanvas().zoomToFeatureExtent(vrt_layer.extent())

# Função para ajustar o brilho e contraste do thumbnail
def enhance_thumbnail(thumbnail_url: str, satellite: str) -> QPixmap:
    try:
        if not isinstance(thumbnail_url, str) or not thumbnail_url.startswith("http"):
            log_message(f"URL inválida para thumbnail: {thumbnail_url}")
            return QPixmap()
        log_message(f"Baixando thumbnail: {thumbnail_url}")
        response = requests.get(thumbnail_url, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        
        if satellite == "Landsat":
            brightness_factor = 6.0
            contrast_factor = 0.7
        else:
            brightness_factor = 2.5
            contrast_factor = 1.8
        
        enhancer = ImageEnhance.Brightness(img)
        bright_img = enhancer.enhance(brightness_factor)
        enhancer = ImageEnhance.Contrast(bright_img)
        final_img = enhancer.enhance(contrast_factor)
        
        img_byte_arr = BytesIO()
        final_img.save(img_byte_arr, format="PNG")
        qimage = QImage.fromData(img_byte_arr.getvalue())
        if qimage.isNull():
            log_message("Erro: QImage é nulo após conversão.")
            return QPixmap()
        pixmap = QPixmap.fromImage(qimage)
        log_message(f"Thumbnail ajustado com sucesso para {satellite}.")
        return pixmap
    except Exception as e:
        log_message(f"Erro ao processar thumbnail: {e}")
        return QPixmap()

# Interface para selecionar imagens disponíveis
def select_available_items(satellite: str, tile: str, items: List[Dict]):
    dialog = QDialog()
    dialog.setWindowTitle(f"Imagens Disponíveis para {satellite} - {tile if tile else 'Busca por Extent'}")
    layout = QVBoxLayout()

    table = QTableWidget()
    table.setRowCount(len(items))
    table.setColumnCount(5)
    table.setHorizontalHeaderLabels(["Data", "Satélite", "Tile", "Cloud Cover (%)", "Thumbnail"])
    table.setSelectionBehavior(QTableWidget.SelectRows)

    for row, item in enumerate(items):
        date = item.datetime.strftime("%Y-%m-%d")
        satellite_name = "Landsat" if satellite == "Landsat" else "Sentinel-2"
        if satellite == "Landsat" and item.id.startswith("LC08"):
            satellite_name = "Landsat 8"
        elif satellite == "Landsat" and item.id.startswith("LC09"):
            satellite_name = "Landsat 9"

        # Extrai o tile do item
        if satellite == "Sentinel-2":
            item_tile = item.properties.get("bdc:tiles", ["N/A"])[0]
        else:  # Landsat
            parts = item.id.split("_")
            item_tile = parts[2] if len(parts) > 2 else "N/A"

        log_message(f"Item {item.id} - Tile extraído: {item_tile}")

        table.setItem(row, 0, QTableWidgetItem(date))
        table.setItem(row, 1, QTableWidgetItem(satellite_name))
        table.setItem(row, 2, QTableWidgetItem(item_tile))

        cloud_cover = item.properties.get("eo:cloud_cover", "N/A")
        table.setItem(row, 3, QTableWidgetItem(str(cloud_cover)))

        thumbnail_asset = item.assets.get("thumbnail")
        thumbnail_href = thumbnail_asset.href if thumbnail_asset else None
        if thumbnail_href and isinstance(thumbnail_href, str) and thumbnail_href.startswith("http"):
            view_btn = QPushButton("View")
            def make_thumbnail_callback(url, sat=satellite):
                def callback():
                    pixmap = enhance_thumbnail(url, sat)
                    if pixmap.isNull():
                        log_message("Thumbnail não pôde ser exibido.")
                        return
                    thumbnail_dialog = QDialog()
                    thumbnail_dialog.setWindowTitle(f"Thumbnail - {date}")
                    thumb_layout = QVBoxLayout()
                    label = QLabel()
                    label.setPixmap(pixmap.scaled(800, 800, Qt.KeepAspectRatio))
                    thumb_layout.addWidget(label)
                    thumbnail_dialog.setLayout(thumb_layout)
                    thumbnail_dialog.exec_()
                return callback
            view_btn.clicked.connect(make_thumbnail_callback(thumbnail_href))
            table.setCellWidget(row, 4, view_btn)
        else:
            table.setItem(row, 4, QTableWidgetItem("N/A"))

    table.resizeColumnsToContents()
    total_width = sum(table.columnWidth(col) for col in range(table.columnCount())) + table.verticalHeader().width() + 40
    table.setMinimumWidth(total_width)
    dialog.setMinimumWidth(total_width + 20)

    select_all_btn = QPushButton("Selecionar Tudo")
    deselect_all_btn = QPushButton("Desselecionar Tudo")
    back_btn = QPushButton("Voltar")
    btn_layout = QHBoxLayout()
    btn_layout.addWidget(select_all_btn)
    btn_layout.addWidget(deselect_all_btn)
    btn_layout.addWidget(back_btn)

    layout.addWidget(QLabel("Imagens Disponíveis:"))
    layout.addWidget(table)
    layout.addLayout(btn_layout)

    button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    layout.addWidget(button_box)
    dialog.setLayout(layout)

    select_all_btn.clicked.connect(table.selectAll)
    deselect_all_btn.clicked.connect(table.clearSelection)
    back_btn.clicked.connect(dialog.reject)

    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)

    if dialog.exec_() == QDialog.Accepted:
        selected_rows = [index.row() for index in table.selectionModel().selectedRows()]
        return [items[row] for row in selected_rows]
    return None

# Interface principal
def get_user_input():
    while True:
        app = QApplication.instance() or QApplication([])
        dialog = QDialog()
        dialog.setWindowTitle("Buscar Imagens STAC (Landsat/Sentinel-2)")
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        satellite_combo = QComboBox()
        satellite_combo.addItems(["Landsat", "Sentinel-2"])
        form_layout.addRow("Satélite:", satellite_combo)

        tile_input = QLineEdit("223067")
        query_bands_input = QLineEdit("swir22, nir08, red")

        # Data de hoje
        hoje = datetime.today()

        # Dia de ontem
        ontem = hoje - timedelta(days=1)

        # Primeiro dia do mês anterior
        primeiro_dia_mes_anterior = (hoje.replace(day=1) - timedelta(days=1)).replace(day=1)
        
        #        start_date_input = QLineEdit("2025-06-01")
        start_date_input = QDateTimeEdit()
        start_date_input.setDisplayFormat("yyyy-MM-dd")
        start_date_input.setCalendarPopup(True)
        start_date_input.setDate(QDate(primeiro_dia_mes_anterior.year, primeiro_dia_mes_anterior.month, primeiro_dia_mes_anterior.day))
        
        #        end_date_input = QLineEdit("2025-07-01")
        end_date_input = QDateTimeEdit()
        end_date_input.setDisplayFormat("yyyy-MM-dd")
        end_date_input.setCalendarPopup(True)
        end_date_input.setDate(QDate(ontem.year, ontem.month, ontem.day))
        
        out_dir_input = QLineEdit("d:/imagens_bdc/223067")

        form_layout.addRow("Tile (ex: 223067 ou 22LEP):", tile_input)
        form_layout.addRow("Bandas (separadas por vírgula):", query_bands_input)
        form_layout.addRow("Data de Início (YYYY-MM-DD):", start_date_input)
        form_layout.addRow("Data de Fim (YYYY-MM-DD):", end_date_input)
        form_layout.addRow("Diretório de Saída:", out_dir_input)

        def select_output_dir():
            dir_path = QFileDialog.getExistingDirectory(iface.mainWindow(), 'Selecione o Diretório de Saída')
            if dir_path:
                out_dir_input.setText(os.path.join(dir_path, tile_input.text().strip()))

        output_dir_button = QPushButton("Selecionar Diretório")
        output_dir_button.clicked.connect(select_output_dir)
        form_layout.addRow(output_dir_button)

        search_extent_btn = QPushButton("Buscar por Extent do Canvas")
        search_extent_btn.setStyleSheet("font-weight: bold; padding: 5px;")
        google_hybrid_btn = QPushButton("Carregar Google Maps Hybrid")
        google_hybrid_btn.setStyleSheet("font-weight: bold; padding: 5px;")

        def update_fields():
            satellite = satellite_combo.currentText()
            tile = tile_input.text().strip()
            if satellite == "Landsat":
                if tile_input.text() == "22LEP" or not tile:
                    tile_input.setText("223067")
                query_bands_input.setText("swir22, nir08, red")
            else:
                if tile_input.text() == "223067" or not tile:
                    tile_input.setText("22LEP")
                query_bands_input.setText("B12, B08, B04")
            out_dir_input.setText(f"d:/imagens_bdc/{tile_input.text().strip()}")

        def update_output_dir():
            tile = tile_input.text().strip()
            if tile:
                out_dir_input.setText(f"d:/imagens_bdc/{tile}")

        satellite_combo.currentTextChanged.connect(update_fields)
        tile_input.textChanged.connect(update_output_dir)

        def carregar_google_hybrid():
            url = "type=xyz&zmin=0&zmax=20&url=https://mt1.google.com/vt/lyrs%3Dy%26x%3D{x}%26y%3D{y}%26z%3D{z}"
            google_layer = QgsRasterLayer(url, "Google Hybrid", "wms")
            if google_layer.isValid():
                # Define o CRS do projeto como EPSG:4326
                crs_4326 = QgsCoordinateReferenceSystem("EPSG:4326")
                QgsProject.instance().setCrs(crs_4326)
                
                # Adiciona a camada ao projeto
                root = QgsProject.instance().layerTreeRoot()
                QgsProject.instance().addMapLayer(google_layer, False)
                root.insertLayer(-1, google_layer)
                
                # Ajusta a opacidade e atualiza o canvas
                google_layer.setOpacity(1)
                log_message("Camada Google Hybrid carregada com sucesso na parte inferior em EPSG:4326!")
#                iface.mapCanvas().zoomToFeatureExtent(google_layer.extent())
                iface.mapCanvas().refresh()
#                iface.mapCanvas().zoomToFullExtent()
            else:
                log_message("Erro ao carregar a camada Google Hybrid")

        google_hybrid_btn.clicked.connect(carregar_google_hybrid)

        def search_by_extent():
            extent = iface.mapCanvas().extent()
            canvas_crs = iface.mapCanvas().mapSettings().destinationCrs()
            wgs84_crs = QgsCoordinateReferenceSystem("EPSG:4326")
            transform = QgsCoordinateTransform(canvas_crs, wgs84_crs, QgsProject.instance())
            min_point = transform.transform(extent.xMinimum(), extent.yMinimum())
            max_point = transform.transform(extent.xMaximum(), extent.yMaximum())
            bbox = [min_point.x(), min_point.y(), max_point.x(), max_point.y()]
            log_message(f"Bounding Box do Canvas Extent (EPSG:4326): {bbox}")
            tile_input.clear()
            dialog.accept()
            return bbox

        search_extent_btn.clicked.connect(search_by_extent)

        layout.addLayout(form_layout)
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(search_extent_btn)
        buttons_layout.addWidget(google_hybrid_btn)
        layout.addLayout(buttons_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)
        dialog.setLayout(layout)

        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        if dialog.exec_() != QDialog.Accepted:
            return None

        satellite = satellite_combo.currentText()
        tile = tile_input.text().strip()
        query_bands = [band.strip() for band in query_bands_input.text().split(',')]
        start_date = start_date_input.text().strip()
        end_date = end_date_input.text().strip()
        output_dir = out_dir_input.text().strip()

        client = connect_to_stac('https://data.inpe.br/bdc/stac/v1/')
        if not client:
            return None
        
        collections = ['landsat-2'] if satellite == "Landsat" else ['S2_L2A-1']
        bbox = None
        if not tile:
            bbox = search_by_extent()
            if bbox:
                items = search_items_by_bbox(client, bbox, start_date, end_date, collections)
            else:
                continue
        else:
            items = search_items(client, tile, start_date, end_date, collections)

        if not items:
            log_message("Nenhuma imagem disponível para os parâmetros fornecidos.")
            return None

        selected_items = select_available_items(satellite, tile if tile else "Extent", items)
        if selected_items is None:
            continue
        if not selected_items:
            log_message("Nenhuma imagem selecionada.")
            return None

        return satellite, tile, query_bands, start_date, end_date, output_dir, selected_items

# Executar
user_input = get_user_input()
if user_input:
    satellite, tile, query_bands, start_date, end_date, output_dir, selected_items = user_input
    generate_and_load_vrts(satellite, tile if tile else "Extent", query_bands, selected_items, output_dir)