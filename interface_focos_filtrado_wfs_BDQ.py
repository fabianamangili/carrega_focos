from qgis.core import QgsVectorLayer, QgsProject, QgsRasterLayer
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QDateTimeEdit, QHBoxLayout, QCheckBox, QListWidget, QListWidgetItem, QLineEdit
from PyQt5.QtCore import QDateTime, QStringListModel
from PyQt5.QtWidgets import QCompleter
import requests
from lxml import etree
from datetime import datetime, timedelta
import os

# URL do serviço WFS
WFS_URL = "https://terrabrasilis.dpi.inpe.br/queimadas/geoserver/wfs"

# Caminhos para os arquivos .qml
QML_PATH_todossat = "d:/util/scripts/pyqgis/estilo_focos_todosat_wfs.qml"
QML_PATH_satref = "d:/util/scripts/pyqgis/estilo_focos_satref_wfs.qml"

# Lista de satélites disponíveis
SATELITES = [
    "AQUA_M-M", "AQUA_M-T", "GOES-16", "METOP-B", "METOP-C", "MSG-03", 
    "NOAA-20", "NOAA-21", "NPP-375", "NPP-375D", "TERRA_M-M", "TERRA_M-T"
]

# Lista de estados brasileiros
ESTADOS = [
    "ACRE", "ALAGOAS", "AMAPÁ", "AMAZONAS", "BAHIA", "CEARÁ", "DISTRITO FEDERAL",
    "ESPÍRITO SANTO", "GOIÁS", "MARANHÃO", "MATO GROSSO", "MATO GROSSO DO SUL",
    "MINAS GERAIS", "PARÁ", "PARAÍBA", "PARANÁ", "PERNAMBUCO", "PIAUÍ",
    "RIO DE JANEIRO", "RIO GRANDE DO NORTE", "RIO GRANDE DO SUL",
    "RONDÔNIA", "RORAIMA", "SANTA CATARINA", "SÃO PAULO", "SERGIPE", "TOCANTINS"
]

class WFSLoader(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("WFS Loader Focos - INPE")
        self.setGeometry(100, 100, 400, 600)

        layout = QVBoxLayout()

        # Escolha da camada
        self.label_camadas = QLabel("Escolha uma camada:")
        self.combo_camadas = QComboBox()
        self.combo_camadas.currentIndexChanged.connect(self.atualizar_interface)
        layout.addWidget(self.label_camadas)
        layout.addWidget(self.combo_camadas)

        # Intervalo de datas
        self.label_data = QLabel("Escolha o intervalo de datas:")
        layout.addWidget(self.label_data)

        date_layout = QHBoxLayout()
        self.data_min = QDateTimeEdit()
        self.data_min.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.data_min.setCalendarPopup(True)

        self.data_max = QDateTimeEdit()
        self.data_max.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.data_max.setCalendarPopup(True)

        date_layout.addWidget(self.data_min)
        date_layout.addWidget(self.data_max)
        layout.addLayout(date_layout)

        # Checkbox para selecionar todos os satélites
        self.checkbox_todos_satelites = QCheckBox("Todos os Satélites")
        self.checkbox_todos_satelites.stateChanged.connect(self.atualizar_filtro_satelite)
        layout.addWidget(self.checkbox_todos_satelites)

        # Escolha de múltiplos satélites
        self.label_satellite = QLabel("Escolha um ou mais satélites:")
        self.list_satellites = QListWidget()
        self.list_satellites.setSelectionMode(QListWidget.MultiSelection)

        for sat in SATELITES:
            item = QListWidgetItem(sat)
            item.setCheckState(0)
            self.list_satellites.addItem(item)

        layout.addWidget(self.label_satellite)
        layout.addWidget(self.list_satellites)

        # Checkbox para selecionar todos os estados
        self.checkbox_todos_estados = QCheckBox("Todos os Estados")
        self.checkbox_todos_estados.stateChanged.connect(self.atualizar_filtro_estado)
        layout.addWidget(self.checkbox_todos_estados)

        # Escolha de múltiplos estados
        self.label_estado = QLabel("Escolha um ou mais estados:")
        self.list_estados = QListWidget()
        self.list_estados.setSelectionMode(QListWidget.MultiSelection)
        self.list_estados.itemSelectionChanged.connect(self.atualizar_municipios_autocompletar)

        for estado in ESTADOS:
            item = QListWidgetItem(estado)
            item.setCheckState(0)
            self.list_estados.addItem(item)

        layout.addWidget(self.label_estado)
        layout.addWidget(self.list_estados)

        # Checkbox para selecionar todos os municípios
        self.checkbox_todos_municipios = QCheckBox("Todos os Municípios")
        self.checkbox_todos_municipios.stateChanged.connect(self.atualizar_filtro_municipio)
        self.checkbox_todos_municipios.setVisible(False)
        layout.addWidget(self.checkbox_todos_municipios)

        # Caixa de texto para digitar município com autocompletar
        self.label_municipio = QLabel("Digite o município:")
        self.input_municipio = QLineEdit()
        self.input_municipio.setPlaceholderText("Digite o nome do município")
        self.completer = QCompleter([], self)
        self.completer.setCaseSensitivity(0)  # Case-insensitive
        self.input_municipio.setCompleter(self.completer)
        self.input_municipio.setVisible(False)
        self.label_municipio.setVisible(False)

        layout.addWidget(self.label_municipio)
        layout.addWidget(self.input_municipio)

        # Layout para os botões
        buttons_layout = QVBoxLayout()

        # Botão principal em destaque
        self.btn_carregar = QPushButton("Carregar Camada WFS")
        self.btn_carregar.clicked.connect(self.carregar_camada)
        self.btn_carregar.setStyleSheet("font-weight: bold; font-size: 16px; padding: 8px;")
        buttons_layout.addWidget(self.btn_carregar)

        # Linha com Estados, AMZ Legal e Biomas
        top_row_layout = QHBoxLayout()
        self.btn_carregar_estados = QPushButton("Layer Estados")
        self.btn_carregar_estados.clicked.connect(self.carregar_camada_estados)
        self.btn_carregar_estados.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        
        self.btn_amz_legal = QPushButton("Layer AMZ Legal")
        self.btn_amz_legal.clicked.connect(self.carregar_amz_legal)
        self.btn_amz_legal.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        
        self.btn_biomas = QPushButton("Layer Biomas")
        self.btn_biomas.clicked.connect(self.carregar_biomas)
        self.btn_biomas.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        
        top_row_layout.addWidget(self.btn_carregar_estados)
        top_row_layout.addWidget(self.btn_amz_legal)
        top_row_layout.addWidget(self.btn_biomas)
        buttons_layout.addLayout(top_row_layout)

        # Botão Google Hybrid centralizado
        self.btn_google_hybrid = QPushButton("Google Maps Hybrid")
        self.btn_google_hybrid.clicked.connect(self.carregar_google_hybrid)
        self.btn_google_hybrid.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        buttons_layout.addWidget(self.btn_google_hybrid)

        # Botão Limpar Camadas
        self.btn_limpar_camadas = QPushButton("Limpar Camadas")
        self.btn_limpar_camadas.clicked.connect(self.limpar_camadas)
        self.btn_limpar_camadas.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        buttons_layout.addWidget(self.btn_limpar_camadas)

        # Botão Fechar
        self.btn_fechar = QPushButton("Fechar")
        self.btn_fechar.clicked.connect(self.close)
        self.btn_fechar.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        buttons_layout.addWidget(self.btn_fechar)

        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        self.carregar_camadas_wfs()

    def carregar_camadas_wfs(self):
        try:
            response = requests.get(f"{WFS_URL}?service=WFS&version=1.1.0&request=GetCapabilities")
            if response.status_code == 200:
                root = etree.fromstring(response.content)
                feature_type_list = root.xpath('//wfs:FeatureType/wfs:Name', namespaces={'wfs': 'http://www.opengis.net/wfs'})

                self.combo_camadas.clear()
                for feature in feature_type_list:
                    nome_camada = feature.text
                    if nome_camada.startswith("dados_abertos:focos"):
                        self.combo_camadas.addItem(nome_camada)
                
                if self.combo_camadas.count() == 0:
                    self.combo_camadas.addItem("Nenhuma camada encontrada")
                else:
                    self.atualizar_interface()

            else:
                self.combo_camadas.addItem("Erro ao carregar camadas")
        except Exception as e:
            self.combo_camadas.addItem("Erro ao acessar WFS")

    def obter_municipios_por_estado(self, estados):
        """Consulta a camada WFS para obter a lista de municípios de um ou mais estados."""
        municipios = set()
        camada_municipios = "bdqueimadas:municipios"  # Ajuste o nome da camada, se necessário
        estados_str = "', '".join(estados)
        filtro_cql = f"estado IN ('{estados_str}')"
        uri = f"{WFS_URL}?service=WFS&version=1.1.0&request=GetFeature&typeName={camada_municipios}&CQL_FILTER={filtro_cql}&srsname=EPSG:4326"

        temp_layer = QgsVectorLayer(uri, "Temp_Municipios", "WFS")
        if temp_layer.isValid():
            for feature in temp_layer.getFeatures():
                municipio = feature["nome"]  # Ajuste o nome do campo, se necessário
                if municipio:
                    municipios.add(municipio)
            QgsProject.instance().removeMapLayer(temp_layer.id())
        else:
            print("Erro ao carregar a camada de municípios para consulta")
        
        return sorted(list(municipios))

    def atualizar_municipios_autocompletar(self):
        """Atualiza o autocompletar do campo de município com base nos estados selecionados."""
        estados_selecionados = []
        for i in range(self.list_estados.count()):
            item = self.list_estados.item(i)
            if item.checkState() == 2:
                estados_selecionados.append(item.text())

        if estados_selecionados:
            municipios = self.obter_municipios_por_estado(estados_selecionados)
            model = QStringListModel(municipios)
            self.completer.setModel(model)
            self.checkbox_todos_municipios.setVisible(True)
            self.label_municipio.setVisible(True)
            self.input_municipio.setVisible(True)
            self.checkbox_todos_municipios.setChecked(True)
            self.input_municipio.setEnabled(False)
        else:
            self.checkbox_todos_municipios.setVisible(False)
            self.label_municipio.setVisible(False)
            self.input_municipio.setVisible(False)
            self.input_municipio.clear()

    def atualizar_filtro_municipio(self):
        """Habilita/desabilita o campo de município com base no checkbox."""
        if self.checkbox_todos_municipios.isChecked():
            self.input_municipio.setEnabled(False)
            self.input_municipio.clear()
        else:
            self.input_municipio.setEnabled(True)

    def ajustar_intervalo_datas(self):
        camada_selecionada = self.combo_camadas.currentText()
        hoje = datetime.now()

        for ano in range(1998, 2026):
            if str(ano) in camada_selecionada:
                data_min = QDateTime(ano, 1, 1, 0, 0, 0)
                data_max = QDateTime(ano, 12, 31, 23, 59, 59)
                self.data_min.setDateTime(data_min)
                self.data_max.setDateTime(data_max)
                return

        if "mesatual" in camada_selecionada:
            data_min = hoje.replace(day=1, hour=0, minute=0, second=0)
            data_max = hoje
            self.data_min.setDateTime(QDateTime(data_min))
            self.data_max.setDateTime(QDateTime(data_max))
            return

        elif "48h" in camada_selecionada:
            data_min = hoje - timedelta(hours=48)
            data_max = hoje
            self.data_min.setDateTime(QDateTime(data_min))
            self.data_max.setDateTime(QDateTime(data_max))
            return

        elif "hoje" in camada_selecionada:
            data_min = hoje.replace(hour=0, minute=0, second=0)
            data_max = hoje
            self.data_min.setDateTime(QDateTime(data_min))
            self.data_max.setDateTime(QDateTime(data_max))
            return

        data_min = QDateTime(hoje.year, 1, 1, 0, 0, 0)
        data_max = QDateTime(hoje)
        self.data_min.setDateTime(data_min)
        self.data_max.setDateTime(data_max)

    def verificar_satellite(self):
        camada_selecionada = self.combo_camadas.currentText()
        
        if "satref" in camada_selecionada:
            self.checkbox_todos_satelites.setVisible(False)
            self.label_satellite.setVisible(False)
            self.list_satellites.setVisible(False)
            self.checkbox_todos_satelites.setChecked(False)
            self.list_satellites.setEnabled(False)
        elif "todosats" in camada_selecionada:
            self.checkbox_todos_satelites.setVisible(True)
            self.label_satellite.setVisible(True)
            self.list_satellites.setVisible(True)
            self.list_satellites.setEnabled(not self.checkbox_todos_satelites.isChecked())
        else:
            self.checkbox_todos_satelites.setVisible(False)
            self.label_satellite.setVisible(False)
            self.list_satellites.setVisible(False)
            self.list_satellites.setEnabled(False)

    def atualizar_interface(self):
        self.ajustar_intervalo_datas()
        self.verificar_satellite()
        self.atualizar_municipios_autocompletar()

    def atualizar_filtro_satelite(self):
        if self.checkbox_todos_satelites.isChecked():
            self.list_satellites.setEnabled(False)
        else:
            self.list_satellites.setEnabled(True)

    def atualizar_filtro_estado(self):
        if self.checkbox_todos_estados.isChecked():
            self.list_estados.setEnabled(False)
        else:
            self.list_estados.setEnabled(True)
        self.atualizar_municipios_autocompletar()

    def carregar_camada(self):
        camada_selecionada = self.combo_camadas.currentText()
        
        data_min = self.data_min.dateTime().toString("yyyy-MM-ddTHH:mm:ss.000")
        data_max = self.data_max.dateTime().toString("yyyy-MM-ddTHH:mm:ss.000")
        
        filtro_cql = f"data_hora_gmt >= '{data_min}' AND data_hora_gmt <= '{data_max}'"

        if "todosats" in camada_selecionada and not self.checkbox_todos_satelites.isChecked():
            satelites_selecionados = []
            for i in range(self.list_satellites.count()):
                item = self.list_satellites.item(i)
                if item.checkState() == 2:
                    satelites_selecionados.append(item.text())

            if satelites_selecionados:
                satelites_str = "', '".join(satelites_selecionados)
                filtro_cql += f" AND satelite IN ('{satelites_str}')"

        if not self.checkbox_todos_estados.isChecked():
            estados_selecionados = []
            for i in range(self.list_estados.count()):
                item = self.list_estados.item(i)
                if item.checkState() == 2:
                    estados_selecionados.append(item.text())

            if estados_selecionados:
                estados_str = "', '".join(estados_selecionados)
                filtro_cql += f" AND estado IN ('{estados_str}')"

        if not self.checkbox_todos_municipios.isChecked():
            municipio_digitado = self.input_municipio.text().strip()
            if municipio_digitado:
                # Escapar aspas simples no nome do município
                municipio_digitado = municipio_digitado.replace("'", "''")
                filtro_cql += f" AND municipio = '{municipio_digitado}'"

        uri = f"{WFS_URL}?service=WFS&version=1.1.0&request=GetFeature&typeName={camada_selecionada}&CQL_FILTER={filtro_cql}&srsname=EPSG:4326"

        # Renomear a camada
        nome_base = camada_selecionada.replace("dados_abertos:focos_", "")
        
        nome_camada = ""
        for ano in range(1998, 2025):
            if str(ano) in nome_base:
                data_min_dt = self.data_min.dateTime().toPyDateTime()
                data_max_dt = self.data_max.dateTime().toPyDateTime()
                data_min_str = data_min_dt.strftime("%d%m")
                data_max_str = data_max_dt.strftime("%d%m")
                nome_camada = f"{data_min_str}-{data_max_str}_{ano}"
                break
        
        if not nome_camada:
            nome_base = nome_base.replace("_todosats", "").replace("_satref", "")
            nome_camada = nome_base

        wfs_layer = QgsVectorLayer(uri, nome_camada, "WFS")
        
        if wfs_layer.isValid():
            if "satref" in camada_selecionada:
                qml_path = QML_PATH_satref
            else:
                qml_path = QML_PATH_todossat

            if os.path.exists(qml_path):
                wfs_layer.loadNamedStyle(qml_path)
                wfs_layer.triggerRepaint()
                print(f"Estilo {qml_path} aplicado com sucesso à camada WFS!")
            else:
                print(f"Arquivo de estilo {qml_path} não encontrado!")

            root = QgsProject.instance().layerTreeRoot()
            QgsProject.instance().addMapLayer(wfs_layer, False)
            root.insertLayer(-1, wfs_layer)
            print(f"Camada WFS '{nome_camada}' carregada com sucesso na parte inferior!")
        else:
            print("Erro ao carregar a camada WFS filtrada")

    def carregar_google_hybrid(self):
        url = "type=xyz&zmin=0&zmax=20&url=https://mt1.google.com/vt/lyrs%3Dy%26x%3D{x}%26y%3D{y}%26z%3D{z}"
        google_layer = QgsRasterLayer(url, "Google Hybrid", "wms")
        
        if google_layer.isValid():
            root = QgsProject.instance().layerTreeRoot()
            QgsProject.instance().addMapLayer(google_layer, False)
            root.insertLayer(-1, google_layer)
            print("Camada Google Hybrid carregada com sucesso na parte inferior!")
        else:
            print("Erro ao carregar a camada Google Hybrid")

    def carregar_camada_estados(self):
        camada_nome = "bdqueimadas:estados"
        filtro_cql = "id_0 = 33"

        estados_selecionados = []
        for i in range(self.list_estados.count()):
            item = self.list_estados.item(i)
            if item.checkState() == 2:
                estados_selecionados.append(item.text())

        if estados_selecionados:
            estados_str = "', '".join(estados_selecionados)
            filtro_cql += f" AND nome_bdq IN ('{estados_str}')"

        uri = f"{WFS_URL}?service=WFS&version=1.1.0&request=GetFeature&typeName={camada_nome}&CQL_FILTER={filtro_cql}&srsname=EPSG:4326"
        estados_layer = QgsVectorLayer(uri, "Estados", "WFS")

        if estados_layer.isValid():
            root = QgsProject.instance().layerTreeRoot()
            QgsProject.instance().addMapLayer(estados_layer, False)
            root.insertLayer(-1, estados_layer)
            print("Camada de estados carregada com sucesso na parte inferior!")
        else:
            print("Erro ao carregar a camada de estados")

    def carregar_amz_legal(self):
        camada_nome = "bdqueimadas:regioes_especiais"
        filtro_cql = "nome = 'Amazônia Legal'"
        
        uri = f"{WFS_URL}?service=WFS&version=1.1.0&request=GetFeature&typeName={camada_nome}&CQL_FILTER={filtro_cql}&srsname=EPSG:4326"
        amz_layer = QgsVectorLayer(uri, "Amazônia Legal", "WFS")
        
        if amz_layer.isValid():
            root = QgsProject.instance().layerTreeRoot()
            QgsProject.instance().addMapLayer(amz_layer, False)
            root.insertLayer(-1, amz_layer)
            print("Camada Amazônia Legal carregada com sucesso na parte inferior!")
        else:
            print("Erro ao carregar a camada Amazônia Legal")

    def carregar_biomas(self):
        camada_nome = "bdqueimadas:biomas_brasileiros"
        uri = f"{WFS_URL}?service=WFS&version=1.1.0&request=GetFeature&typeName={camada_nome}&srsname=EPSG:4326"
        biomas_layer = QgsVectorLayer(uri, "Biomas Brasileiros", "WFS")
        
        if biomas_layer.isValid():
            root = QgsProject.instance().layerTreeRoot()
            QgsProject.instance().addMapLayer(biomas_layer, False)
            root.insertLayer(-1, biomas_layer)
            print("Camada Biomas Brasileiros carregada com sucesso na parte inferior!")
        else:
            print("Erro ao carregar a camada Biomas Brasileiros")

    def limpar_camadas(self):
        QgsProject.instance().removeAllMapLayers()
        try:
            from qgis.utils import iface
            iface.mapCanvas().refresh()
            print("Todas as camadas foram removidas e o canvas foi atualizado!")
        except ImportError:
            print("Todas as camadas foram removidas, mas o canvas não pôde ser atualizado")

# Executar a interface no QGIS
window = WFSLoader()
window.show()