# -*- coding: utf-8 -*-
import os
from qgis.PyQt.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QMessageBox
)

from qgis.core import (
    QgsProject,
    QgsMapLayerType,
    QgsCoordinateTransform,
    QgsFeatureRequest
)

import numpy as np


class AtualizadorAmostras(QWidget):

    def criar_raster_mascara(
        self,
        raster,
        limiares,
        saida_tif
    ):

        ds = gdal.Open(raster.source())

        cols = ds.RasterXSize
        rows = ds.RasterYSize

        driver = gdal.GetDriverByName("GTiff")

        out_ds = driver.Create(
            saida_tif,
            cols,
            rows,
            ds.RasterCount,
            gdal.GDT_Byte,
            options=["COMPRESS=LZW"]
        )

        out_ds.SetGeoTransform(
            ds.GetGeoTransform()
        )

        out_ds.SetProjection(
            ds.GetProjection()
        )

        for banda in range(1, ds.RasterCount + 1):

            nome_banda = raster.bandName(banda)

            nome_campo = nome_banda

            if ":" in nome_banda:
                nome_campo = nome_banda.split(":")[-1].strip()

            if nome_banda not in limiares:
                continue

            limite = limiares[nome_banda]

            arr = ds.GetRasterBand(
                banda
            ).ReadAsArray()

            mask = (
                arr >= limite
            ).astype(np.uint8)

            out_band = out_ds.GetRasterBand(
                banda
            )

            out_band.WriteArray(mask)

            descricao = (
                f"{nome_campo} "
                f"(limiar={limite:.4f})"
            )

            out_band.SetDescription(
                descricao
            )

            out_band.SetNoDataValue(
                255
            )

        out_ds.FlushCache()

        out_ds = None
        ds = None

        print("\nRaster máscara criado:")
        print(saida_tif)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Atualizar Amostras")
        self.resize(450, 200)

        layout = QVBoxLayout()

        # Raster
        layout.addWidget(QLabel("Raster empilhado"))

        self.combo_raster = QComboBox()
        layout.addWidget(self.combo_raster)

        # Amostras
        layout.addWidget(QLabel("Camada de amostras"))

        self.combo_amostras = QComboBox()
        layout.addWidget(self.combo_amostras)

        # Botão
        self.btn = QPushButton(
            "Atualizar Amostras + Estatísticas"
        )

        self.btn.clicked.connect(self.executar)

        layout.addWidget(self.btn)

        self.setLayout(layout)

        self.carregar_camadas()

    def carregar_camadas(self):

        self.combo_raster.clear()
        self.combo_amostras.clear()

        for layer in QgsProject.instance().mapLayers().values():

            if layer.type() == QgsMapLayerType.RasterLayer:
                self.combo_raster.addItem(layer.name())

            elif layer.type() == QgsMapLayerType.VectorLayer:
                self.combo_amostras.addItem(layer.name())

    def executar(self):

        raster = QgsProject.instance().mapLayersByName(
            self.combo_raster.currentText()
        )[0]

        amostras = QgsProject.instance().mapLayersByName(
            self.combo_amostras.currentText()
        )[0]

        self.atualizar_amostras(
            raster,
            amostras
        )

    def atualizar_amostras(
        self,
        raster,
        amostras
    ):

        provider = raster.dataProvider()

        total_bandas = provider.bandCount()

        nomes_bandas = []

        for banda in range(1, total_bandas + 1):

            nome = raster.bandName(banda)

            if not nome:
                nome = f"band_{banda}"

            nomes_bandas.append(nome)


        # localizar campos

        idx_campos = {}

        for nome in nomes_bandas:

            nome_campo = nome

            if ":" in nome:
                nome_campo = nome.split(":")[-1].strip()

            idx = amostras.fields().indexFromName(nome_campo)


            if idx >= 0:
                idx_campos[nome] = idx

        # transformação CRS
        print("\nBandas encontradas:")
        for nome in nomes_bandas:
            print(nome)
            
            
        transform = None

        if amostras.crs() != raster.crs():

            transform = QgsCoordinateTransform(
                amostras.crs(),
                raster.crs(),
                QgsProject.instance()
            )


        # atualizar atributos

        ok_edit = amostras.startEditing()

        print("startEditing:", ok_edit)
        print("isEditable:", amostras.isEditable())
        alterados = 0

        for feat in amostras.getFeatures():

            if feat["VALIDA"] != 2:
                continue


            ponto = feat.geometry().asPoint()

            if transform:
                ponto = transform.transform(ponto)

            for banda, nome in enumerate(
                nomes_bandas,
                start=1
            ):

                if nome not in idx_campos:
                    continue

                valor, ok = provider.sample(
                    ponto,
                    banda
                )


                if not ok:
                    continue

                amostras.changeAttributeValue(
                    feat.id(),
                    idx_campos[nome],
                    float(valor)
                )

                alterados += 1

        print(f"Valores atualizados: {alterados}")
        print("\nFeições VALIDA=2 encontradas:")


        sucesso = amostras.commitChanges()

        print("Commit:", sucesso)

        if not sucesso:
            print(amostras.commitErrors())
        
        # estatísticas

        print("\n")
        print("=" * 60)
        print("VALIDA = 2")
        print("=" * 60)
        limiares = {}
        
        contador = 0

        for feat in amostras.getFeatures():

            if feat["VALIDA"] == 2:
                contador += 1

        print(f"Registros com VALIDA=2: {contador}")
        request = QgsFeatureRequest().setFilterExpression(
            '"VALIDA" = 2'
        )

        for nome in nomes_bandas:

            if nome not in idx_campos:
                continue

            valores = []

            for feat in amostras.getFeatures(request):

                nome_campo = nome

                if ":" in nome:
                    nome_campo = nome.split(":")[-1].strip()

                v = feat[nome_campo]                
                if v is not None:
                    valores.append(float(v))

            if len(valores) < 2:
                continue

            media = np.mean(valores)

            desvio = np.std(
                valores,
                ddof=1
            )

            limite = media - desvio
            limiares[nome] = limite

            print("\n--------------------")
            print(nome)
            print(f"Média = {media:.4f}")
            print(f"Desvio padrão = {desvio:.4f}")
            print(f"Média - Desvio = {limite:.2f}")

        print("\n")
        print("=" * 60)
        print("AVALIAÇÃO DOS ÍNDICES")
        print("=" * 60)

        request_validacao = QgsFeatureRequest().setFilterExpression(
            '"VALIDA" IN (0,1)'
        )

        for nome in nomes_bandas:

            if nome not in idx_campos:
                continue

            if nome not in limiares:
                continue

            # -----------------------------
            # Estatística dos queimados
            # (VALIDA = 1)
            # -----------------------------

            request_queimada = QgsFeatureRequest().setFilterExpression(
                '"VALIDA" = 1'
            )

            valores_queimada = []

            for feat in amostras.getFeatures(request_queimada):

                valor = feat[nome_campo]

                if valor is None:
                    continue

                if str(valor) == 'NULL':
                    continue

                try:
                    valor = float(valor)
                except:
                    continue

                valores_queimada.append(valor)

            media_q = None
            desvio_q = None
            limiar_q = None

            if len(valores_queimada) >= 2:

                media_q = np.mean(valores_queimada)

                desvio_q = np.std(
                    valores_queimada,
                    ddof=1
                )

                limiar_q = media_q - desvio_q

            limiar = limiares[nome]

            nome_campo = nome

            if ":" in nome:
                nome_campo = nome.split(":")[-1].strip()

            TP = 0
            TN = 0
            FP = 0
            FN = 0

            for feat in amostras.getFeatures(request_validacao):

                valor = feat[nome_campo]

                if valor is None:
                    continue

                if str(valor) == 'NULL':
                    continue

                try:
                    valor = float(valor)
                except:
                    continue

                referencia = int(feat["VALIDA"])

                # regra do índice
                predicao = 1 if valor >= limiar else 0

                if referencia == 1 and predicao == 1:
                    TP += 1

                elif referencia == 1 and predicao == 0:
                    FN += 1

                elif referencia == 0 and predicao == 0:
                    TN += 1

                elif referencia == 0 and predicao == 1:
                    FP += 1

            total = TP + TN + FP + FN

            if total == 0:
                continue

            acuracia = 100 * (TP + TN) / total

            recall = (
                100 * TP / (TP + FN)
                if (TP + FN) > 0 else 0
            )

            especificidade = (
                100 * TN / (TN + FP)
                if (TN + FP) > 0 else 0
            )

            precisao = (
                100 * TP / (TP + FP)
                if (TP + FP) > 0 else 0
            )

            print("\n" + "-" * 50)
            print(nome)
            print(f"Limiar: {limiar:.4f}")

            print("\nEstatísticas VALIDA=1")

            if media_q is not None:

                print(f"Média            : {media_q:.4f}")
                print(f"Desvio padrão    : {desvio_q:.4f}")
                print(f"Média - Desvio   : {limiar_q:.4f}")

            else:

                print("Sem amostras suficientes.")
                
            print("\nMatriz de Confusão")
            print(f"TP = {TP}")
            print(f"FN = {FN}")
            print(f"FP = {FP}")
            print(f"TN = {TN}")

            print("\nIndicadores")
            print(f"Acurácia       : {acuracia:.2f}%")
            print(f"Recall         : {recall:.2f}%")
            print(f"Especificidade : {especificidade:.2f}%")
            print(f"Precisão       : {precisao:.2f}%")

        base, ext = os.path.splitext(
            raster.source()
        )

        saida_tif = base + "_mascara.tif"

        self.criar_raster_mascara(
            raster,
            limiares,
            saida_tif
        )
        QMessageBox.information(
            self,
            "Concluído",
            "Amostras atualizadas.\nVeja as estatísticas no Console Python."
        )


window = AtualizadorAmostras()
window.show()