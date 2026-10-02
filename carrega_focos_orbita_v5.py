# -*- coding: utf-8 -*-

from qgis.core import (
    QgsVectorLayer,
    QgsProject,
    QgsFeatureRequest,
    QgsGeometry,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsMapLayerType,
    QgsField,
    QgsFeature
)
from PyQt5.QtCore import QVariant
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox,
    QDateTimeEdit, QHBoxLayout, QCheckBox, QListWidget,
    QListWidgetItem, QLineEdit, QApplication
)
from PyQt5.QtCore import QDateTime, Qt

import requests
from lxml import etree
from datetime import datetime, timedelta
import os
import urllib.parse

# =====================================================
# IMPORTAÇÕES PARA RANDOM FOREST
# =====================================================
import joblib
import numpy as np
from sklearn.impute import SimpleImputer

# =====================================================
# CONFIG
# =====================================================

WFS_URL = "https://terrabrasilis.dpi.inpe.br/queimadas/geoserver/wfs"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

QML_PATH_todossat = os.path.join(SCRIPT_DIR, "estilo_focos_todosat_wfs.qml")
QML_PATH_satref = os.path.join(SCRIPT_DIR, "estilo_focos_todosat_wfs.qml")
QML_MF = os.path.join(SCRIPT_DIR, "estilo_MF_amostras.qml")
QML_AMOSTRAS = os.path.join(SCRIPT_DIR, "estilo_pontos_amostras_v5.qml")

SATELITES = [
    "AQUA_M-M", "AQUA_M-T", "GOES-16", "METOP-B", "METOP-C", "MSG-03",
    "NOAA-20", "NOAA-21", "NPP-375", "NPP-375D", "TERRA_M-M", "TERRA_M-T"
]

ESTADOS = [
    "ACRE", "ALAGOAS", "AMAPÁ", "AMAZONAS", "BAHIA", "CEARÁ",
    "DISTRITO FEDERAL", "ESPÍRITO SANTO", "GOIÁS", "MARANHÃO",
    "MATO GROSSO", "MATO GROSSO DO SUL", "MINAS GERAIS", "PARÁ",
    "PARAÍBA", "PARANÁ", "PERNAMBUCO", "PIAUÍ", "RIO DE JANEIRO",
    "RIO GRANDE DO NORTE", "RIO GRANDE DO SUL", "RONDÔNIA",
    "RORAIMA", "SANTA CATARINA", "SÃO PAULO", "SERGIPE", "TOCANTINS"
]

# =====================================================
# CARREGAR MODELO RANDOM FOREST
# =====================================================
CAMINHO_MODELO = os.path.join(SCRIPT_DIR, "rf_model_queimadas.pkl")
CAMINHO_IMPUTER = os.path.join(SCRIPT_DIR, "imputer.pkl")
CAMINHO_FEATURES = os.path.join(SCRIPT_DIR, "features.pkl")

try:
    MODELO_RF = joblib.load(CAMINHO_MODELO)
    IMPUTER_RF = joblib.load(CAMINHO_IMPUTER)
    FEATURES_RF = joblib.load(CAMINHO_FEATURES)
    print("Modelo Random Forest carregado com sucesso.")
    print("Features esperadas:", FEATURES_RF)
except Exception as e:
    print(f"Erro ao carregar modelo RF: {e}")
    MODELO_RF = None
    IMPUTER_RF = None
    FEATURES_RF = None

# =====================================================
# CLASSE PRINCIPAL (WFSLoader)
# =====================================================
class WFSLoader(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("WFS Loader Focos - INPE TURBO + Classificação RF")
        self.setGeometry(100, 100, 420, 620)

        layout = QVBoxLayout()

        self.label_camadas = QLabel("Escolha uma camada:")
        self.combo_camadas = QComboBox()
        self.combo_camadas.currentIndexChanged.connect(self.atualizar_interface)

        layout.addWidget(self.label_camadas)
        layout.addWidget(self.combo_camadas)

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

        # satélite
        self.checkbox_todos_satelites = QCheckBox("Todos os Satélites")
        self.checkbox_todos_satelites.stateChanged.connect(self.atualizar_filtro_satelite)
        layout.addWidget(self.checkbox_todos_satelites)

        self.label_satellite = QLabel("Escolha um ou mais satélites:")
        self.list_satellites = QListWidget()
        for sat in SATELITES:
            item = QListWidgetItem(sat)
            item.setCheckState(0)
            self.list_satellites.addItem(item)
        layout.addWidget(self.label_satellite)
        layout.addWidget(self.list_satellites)

        # órbita/ponto
        self.label_orbita = QLabel("Órbita/Ponto:")
        self.input_orbita = QLineEdit()
        self.input_orbita.setPlaceholderText("Ex: 227_073")
        layout.addWidget(self.label_orbita)
        layout.addWidget(self.input_orbita)

        # camada máscara adicional
        self.label_mask = QLabel("Selecione uma camada para máscara AQM V1:")
        self.combo_mask = QComboBox()
        layout.addWidget(self.label_mask)
        layout.addWidget(self.combo_mask)

        # botões
        self.btn_carregar = QPushButton("Carregar Camada WFS")
        self.btn_carregar.clicked.connect(self.carregar_camada)
        self.btn_carregar.setStyleSheet("font-weight:bold;font-size:16px;padding:8px;")
        layout.addWidget(self.btn_carregar)

        self.btn_limpar = QPushButton("Limpar Camadas")
        self.btn_limpar.clicked.connect(self.limpar_camadas)
        layout.addWidget(self.btn_limpar)

        self.btn_fechar = QPushButton("Fechar")
        self.btn_fechar.clicked.connect(self.close)
        layout.addWidget(self.btn_fechar)

        self.setLayout(layout)

        self.carregar_camadas_wfs()
        self.carregar_camadas_mascara()

    # =====================================================
    # EXTRAIR VALORES DOS RASTERS
    # =====================================================
    def _extrair_valores_raster(self, geom_ponto, data_str, codigo, cache_rasters):
        """
        Retorna (lista_valores, sucesso_booleano).
        """
        data_clean = data_str.replace('-', '')
        chave = f"{codigo}_{data_clean}"

        if chave in cache_rasters and cache_rasters[chave] is None:
            return None, False

        if chave not in cache_rasters:
            rasters = []
            for suf in FEATURES_RF:
                nome_raster = f"{codigo}_{data_clean}_{suf}"
                layer = QgsProject.instance().mapLayersByName(nome_raster)
                if not layer:
                    print(f"Raster não encontrado: {nome_raster}")
                    cache_rasters[chave] = None
                    return None, False
                rasters.append(layer[0])
            cache_rasters[chave] = rasters

        rasters = cache_rasters[chave]
        if rasters is None:
            return None, False

        # Transformar geometria para CRS do raster
        crs_raster = rasters[0].crs()
        crs_ponto = QgsCoordinateReferenceSystem("EPSG:4326")
        geom_proj = QgsGeometry(geom_ponto)
        if crs_ponto != crs_raster:
            transform = QgsCoordinateTransform(crs_ponto, crs_raster, QgsProject.instance())
            geom_proj.transform(transform)
        ponto = geom_proj.asPoint()

        # Extrair valores
        valores = []
        for raster in rasters:
            value, ok = raster.dataProvider().sample(ponto, 1)
            if not ok or value is None:
                return None, False
            valores.append(value)
        return valores, True

    # =====================================================
    # GERAR MÁSCARA E PONTOS (COM CLASSIFICAÇÃO RF)
    # =====================================================
    def gerar_mascara_focos(self, layer, codigo, data_min, data_max):
        from qgis import processing

        grade = QgsProject.instance().mapLayersByName("grade_util_landsat")[0]
        expr = f"trim(\"path_row\") = '{codigo}'"

        # M1
        buffer_ext = processing.run("native:buffer", {
            'INPUT': layer, 'DISTANCE': 0.0025, 'SEGMENTS': 12,
            'DISSOLVE': True, 'OUTPUT': 'memory:'
        })['OUTPUT']
        buffer_int = processing.run("native:buffer", {
            'INPUT': buffer_ext, 'DISTANCE': -0.0025, 'SEGMENTS': 12,
            'DISSOLVE': True, 'OUTPUT': 'memory:'
        })['OUTPUT']
        resultado = processing.run("native:symmetricaldifference", {
            'INPUT': buffer_ext, 'OVERLAY': buffer_int, 'OUTPUT': 'memory:'
        })['OUTPUT']
        resultado.setName(f"M1_{codigo}")

        # M2 (opcional)
        resultado_m2 = None
        nome_mask = self.combo_mask.currentText()
        if nome_mask != "Nenhuma":
            lista = QgsProject.instance().mapLayersByName(nome_mask)
            if lista:
                camada_mask = lista[0]
                reproj = processing.run("native:reprojectlayer", {
                    'INPUT': camada_mask,
                    'TARGET_CRS': QgsCoordinateReferenceSystem("EPSG:4326"),
                    'OUTPUT': 'memory:'
                })['OUTPUT']
                b1 = processing.run("native:buffer", {
                    'INPUT': reproj, 'DISTANCE': 0.0025, 'SEGMENTS': 12,
                    'DISSOLVE': True, 'OUTPUT': 'memory:'
                })['OUTPUT']
                b2 = processing.run("native:buffer", {
                    'INPUT': b1, 'DISTANCE': -0.005, 'SEGMENTS': 12,
                    'DISSOLVE': True, 'OUTPUT': 'memory:'
                })['OUTPUT']
                resultado_m2 = processing.run("native:symmetricaldifference", {
                    'INPUT': b1, 'OVERLAY': b2, 'OUTPUT': 'memory:'
                })['OUTPUT']
                resultado_m2.setName(f"M2_{codigo}")

        # Merge
        layers_merge = [resultado]
        if resultado_m2:
            layers_merge.append(resultado_m2)
        merge = processing.run("native:mergevectorlayers", {
            'LAYERS': layers_merge, 'CRS': resultado.sourceCrs(), 'OUTPUT': 'memory:'
        })['OUTPUT']
        diss = processing.run("native:dissolve", {
            'INPUT': merge, 'OUTPUT': 'memory:'
        })['OUTPUT']
        buff = processing.run("native:buffer", {
            'INPUT': diss, 'DISTANCE': 0.0005, 'SEGMENTS': 12,
            'DISSOLVE': True, 'OUTPUT': 'memory:'
        })['OUTPUT']
        buff = processing.run("native:fixgeometries", {
            'INPUT': buff, 'OUTPUT': 'memory:'
        })['OUTPUT']

        # Clip pela órbita
        orbita = processing.run("native:extractbyexpression", {
            'INPUT': grade, 'EXPRESSION': expr, 'OUTPUT': 'memory:'
        })['OUTPUT']
        mf = processing.run("native:clip", {
            'INPUT': buff, 'OVERLAY': orbita, 'OUTPUT': 'memory:'
        })['OUTPUT']

        # Recorte pelo Brasil (WFS)
        uri_estados = (f"{WFS_URL}?service=WFS&version=1.1.0&request=GetFeature"
                       f"&typeName=bdqueimadas:estados&CQL_FILTER=id_0 = 33&srsname=EPSG:4326")
        estados = QgsVectorLayer(uri_estados, "tmp_estados_clip", "WFS")
        if estados.isValid():
            estados_fix = processing.run("native:fixgeometries", {
                'INPUT': estados, 'OUTPUT': 'memory:'
            })['OUTPUT']
            brasil = processing.run("native:dissolve", {
                'INPUT': estados_fix, 'OUTPUT': 'memory:'
            })['OUTPUT']
            mf = processing.run("native:clip", {
                'INPUT': mf, 'OVERLAY': brasil, 'OUTPUT': 'memory:'
            })['OUTPUT']
            print("Máscara recortada ao Brasil.")
        else:
            print("Erro ao carregar estados do Brasil.")

        mf.setName(f"MF_{codigo}_{data_min[:10]}_{data_max[:10]}")

        # Criar camada limpa
        limpa = QgsVectorLayer("Polygon?crs=EPSG:4326", mf.name(), "memory")
        prov = limpa.dataProvider()
        prov.addAttributes([
            QgsField("codigo", QVariant.String),
            QgsField("data_min", QVariant.String),
            QgsField("data_max", QVariant.String)
        ])
        limpa.updateFields()
        for f in mf.getFeatures():
            nf = QgsFeature(limpa.fields())
            nf.setGeometry(f.geometry())
            nf["codigo"] = codigo
            nf["data_min"] = data_min[:10]
            nf["data_max"] = data_max[:10]
            prov.addFeature(nf)
        limpa.updateExtents()
        QgsProject.instance().addMapLayer(limpa)
        QgsProject.instance().removeMapLayer(mf)
        if os.path.exists(QML_MF):
            limpa.loadNamedStyle(QML_MF)
            limpa.triggerRepaint()

        # GERAR 200 PONTOS ALEATÓRIOS
        pts = processing.run("native:randompointsinpolygons", {
            'INPUT': limpa, 'POINTS_NUMBER': 200, 'MIN_DISTANCE': 0.005, 'OUTPUT': 'memory:'
        })['OUTPUT']
        pr = pts.dataProvider()

        # Campos: VALIDA, AUDITA + campos dos índices + rf_class + rf_prob
        campos_adicionais = [
            QgsField("VALIDA", QVariant.Int),
            QgsField("AUDITA", QVariant.Int)
        ]
        for suf in FEATURES_RF:
            campos_adicionais.append(QgsField(suf, QVariant.Double))
        campos_adicionais.append(QgsField("rf_class", QVariant.Int))
        campos_adicionais.append(QgsField("rf_prob", QVariant.Double))

        pr.addAttributes(campos_adicionais)
        pts.updateFields()
        pts.setName(f"amostras_{codigo}_{data_min[:10]}_{data_max[:10]}")
        QgsProject.instance().addMapLayer(pts)
        if os.path.exists(QML_AMOSTRAS):
            pts.loadNamedStyle(QML_AMOSTRAS)
            pts.triggerRepaint()
        print("200 pontos aleatórios gerados.")

        # =================================================
        # EXTRAIR VALORES DOS RASTERS E CLASSIFICAR
        # =================================================
        if MODELO_RF is not None:
            # Índices dos campos
            idx_fields = {suf: pts.fields().indexFromName(suf) for suf in FEATURES_RF}
            idx_class = pts.fields().indexFromName("rf_class")
            idx_prob = pts.fields().indexFromName("rf_prob")
            idx_valida = pts.fields().indexFromName("VALIDA") 

            data_ref = data_max[:10]  # 'YYYY-MM-DD'
            cache_rasters = {}
            pts.startEditing()

            for feat in pts.getFeatures():
                geom = feat.geometry()
                valores, ok = self._extrair_valores_raster(geom, data_ref, codigo, cache_rasters)
                if ok:
                    # Salvar valores nos campos dos índices
                    for i, suf in enumerate(FEATURES_RF):
                        pts.changeAttributeValue(feat.id(), idx_fields[suf], valores[i])
                    # Classificar
                    X = np.array([valores])
                    X_imputado = IMPUTER_RF.transform(X)
                    prob = MODELO_RF.predict_proba(X_imputado)[0]
                    classe = int(MODELO_RF.predict(X_imputado)[0])
                    prob_queimada = float(prob[1])
                    pts.changeAttributeValue(feat.id(), idx_class, classe)
                    pts.changeAttributeValue(feat.id(), idx_prob,prob_queimada)
                    pts.changeAttributeValue(feat.id(), idx_valida, classe)
                else:
                    # Falha na extração
                    for suf in FEATURES_RF:
                        pts.changeAttributeValue(feat.id(), idx_fields[suf], None)
                    pts.changeAttributeValue(feat.id(), idx_class, None)
                    pts.changeAttributeValue(feat.id(), idx_prob, None)
                    pts.changeAttributeValue(feat.id(), idx_valida, None)

            pts.commitChanges()
            print("Valores dos índices e classificação RF aplicados.")
        else:
            print("Modelo Random Forest não disponível. Pulando classificação.")

    # =====================================================
    # MÉTODOS AUXILIARES (WFS, UI, ETC.)
    # =====================================================
    def carregar_camadas_wfs(self):
        try:
            url = f"{WFS_URL}?service=WFS&version=1.1.0&request=GetCapabilities"
            r = requests.get(url, timeout=20)
            root = etree.fromstring(r.content)
            nomes = root.xpath('//wfs:FeatureType/wfs:Name', namespaces={'wfs': 'http://www.opengis.net/wfs'})
            self.combo_camadas.clear()
            for n in nomes:
                txt = n.text
                if txt.startswith("dados_abertos:focos"):
                    self.combo_camadas.addItem(txt)
            self.atualizar_interface()
        except Exception as e:
            self.combo_camadas.addItem("Erro ao acessar WFS")
            print(f"Erro: {e}")

    def ajustar_intervalo_datas(self):
        camada = self.combo_camadas.currentText()
        hoje = datetime.now()
        for ano in range(1998, 2027):
            if str(ano) in camada:
                self.data_min.setDateTime(QDateTime(ano, 1, 1, 0, 0, 0))
                self.data_max.setDateTime(QDateTime(ano, 12, 31, 23, 59, 59))
                return
        if "mesatual" in camada:
            d1 = hoje.replace(day=1, hour=0, minute=0, second=0)
            self.data_min.setDateTime(QDateTime(d1))
            self.data_max.setDateTime(QDateTime(hoje))
            return
        if "48h" in camada:
            d1 = hoje - timedelta(hours=48)
            self.data_min.setDateTime(QDateTime(d1))
            self.data_max.setDateTime(QDateTime(hoje))
            return
        if "hoje" in camada:
            d1 = hoje.replace(hour=0, minute=0, second=0)
            self.data_min.setDateTime(QDateTime(d1))
            self.data_max.setDateTime(QDateTime(hoje))
            return
        self.data_min.setDateTime(QDateTime(hoje.year, 1, 1, 0, 0, 0))
        self.data_max.setDateTime(QDateTime(hoje))

    def verificar_satellite(self):
        camada = self.combo_camadas.currentText()
        if "todosats" in camada:
            self.checkbox_todos_satelites.setVisible(True)
            self.label_satellite.setVisible(True)
            self.list_satellites.setVisible(True)
        else:
            self.checkbox_todos_satelites.setVisible(False)
            self.label_satellite.setVisible(False)
            self.list_satellites.setVisible(False)

    def atualizar_interface(self):
        self.ajustar_intervalo_datas()
        self.verificar_satellite()

    def atualizar_filtro_satelite(self):
        self.list_satellites.setEnabled(not self.checkbox_todos_satelites.isChecked())

    def obter_estados_da_orbita(self, codigo):
        grade_lista = QgsProject.instance().mapLayersByName("grade_util_landsat")
        if not grade_lista:
            print("Camada grade_util_landsat não encontrada.")
            return []
        grade = grade_lista[0]
        expr = f"trim(\"path_row\") = '{codigo}'"
        feat_orbita = next(grade.getFeatures(QgsFeatureRequest().setFilterExpression(expr)), None)
        if feat_orbita is None:
            print("Órbita/Ponto não encontrada.")
            return []
        geom_orbita = QgsGeometry(feat_orbita.geometry())
        transform = QgsCoordinateTransform(grade.crs(), QgsCoordinateReferenceSystem("EPSG:4326"), QgsProject.instance())
        geom_orbita.transform(transform)
        uri = (f"{WFS_URL}?service=WFS&version=1.1.0&request=GetFeature"
               f"&typeName=bdqueimadas:estados&CQL_FILTER=id_0 = 33&srsname=EPSG:4326")
        layer_estados = QgsVectorLayer(uri, "tmp_estados", "WFS")
        if not layer_estados.isValid():
            print("Erro ao consultar estados.")
            return []
        encontrados = []
        for f in layer_estados.getFeatures():
            nome = f["nome_bdq"]
            if not nome:
                continue
            nome = str(nome).strip().upper()
            if f.geometry().intersects(geom_orbita) and nome in ESTADOS:
                encontrados.append(nome)
        return sorted(list(set(encontrados)))

    def carregar_camadas_mascara(self):
        self.combo_mask.clear()
        self.combo_mask.addItem("Nenhuma")
        for layer in QgsProject.instance().mapLayers().values():
            if layer.type() == QgsMapLayerType.VectorLayer:
                self.combo_mask.addItem(layer.name())

    def carregar_camada(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            camada = self.combo_camadas.currentText()
            data_min = self.data_min.dateTime().toString("yyyy-MM-ddTHH:mm:ss.000")
            data_max = self.data_max.dateTime().toString("yyyy-MM-ddTHH:mm:ss.000")
            filtro_cql = f"data_hora_gmt >= '{data_min}' AND data_hora_gmt <= '{data_max}'"

            if ("todosats" in camada and not self.checkbox_todos_satelites.isChecked()):
                sats = []
                for i in range(self.list_satellites.count()):
                    item = self.list_satellites.item(i)
                    if item.checkState() == 2:
                        sats.append(item.text())
                if sats:
                    txt = "', '".join(sats)
                    filtro_cql += f" AND satelite IN ('{txt}')"

            codigo = self.input_orbita.text().strip()
            nome_saida = camada.replace("dados_abertos:focos_", "")
            geom_orbita = None

            if codigo:
                estados = self.obter_estados_da_orbita(codigo)
                if estados:
                    txt = "', '".join(estados)
                    filtro_cql += f" AND estado IN ('{txt}')"
                grade = QgsProject.instance().mapLayersByName("grade_util_landsat")[0]
                expr = f"trim(\"path_row\") = '{codigo}'"
                feat = next(grade.getFeatures(QgsFeatureRequest().setFilterExpression(expr)), None)
                if feat:
                    geom_orbita = QgsGeometry(feat.geometry())
                    transform = QgsCoordinateTransform(grade.crs(), QgsCoordinateReferenceSystem("EPSG:4326"), QgsProject.instance())
                    geom_orbita.transform(transform)
                nome_saida = f"{nome_saida}_{codigo}_{data_min[:10]}_{data_max[:10]}"

            # Baixar WFS
            filtro_url = urllib.parse.quote(filtro_cql)
            uri = (f"{WFS_URL}?service=WFS&version=1.1.0&request=GetFeature"
                   f"&typeName={camada}&CQL_FILTER={filtro_url}&srsname=EPSG:4326")
            layer = QgsVectorLayer(uri, nome_saida, "WFS")
            if not layer.isValid():
                print("Erro ao abrir camada.")
                return

            # Filtrar pela órbita localmente
            if geom_orbita:
                memoria = QgsVectorLayer("Point?crs=EPSG:4326", nome_saida, "memory")
                pr = memoria.dataProvider()
                pr.addAttributes(layer.fields())
                memoria.updateFields()
                feats_ok = []
                total = 0
                dentro = 0
                for f in layer.getFeatures():
                    total += 1
                    if f.geometry().intersects(geom_orbita):
                        feats_ok.append(f)
                        dentro += 1
                pr.addFeatures(feats_ok)
                memoria.updateExtents()
                layer = memoria
                print("Total focos baixados:", total)
                print("Dentro da órbita:", dentro)

            # Aplicar estilo
            qml = QML_PATH_satref if "satref" in camada else QML_PATH_todossat
            if os.path.exists(qml):
                layer.loadNamedStyle(qml)
                layer.triggerRepaint()
            QgsProject.instance().addMapLayer(layer)
            print("Camada carregada com sucesso.")

            # Gerar máscara e pontos (e classificar)
            if codigo:
                self.gerar_mascara_focos(layer, codigo, data_min, data_max)

        finally:
            QApplication.restoreOverrideCursor()

    def limpar_camadas(self):
        QgsProject.instance().removeAllMapLayers()
        try:
            from qgis.utils import iface
            iface.mapCanvas().refresh()
            print("Todas as camadas foram removidas e o canvas foi atualizado!")
        except ImportError:
            print("Todas as camadas foram removidas.")


# =====================================================
# EXECUTAR
# =====================================================
window = WFSLoader()
window.show()