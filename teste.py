# -*- coding: utf-8 -*-

import requests
import re
import html
import xml.etree.ElementTree as ET
import os

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsField,
    QgsDistanceArea,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsVectorFileWriter
)

from qgis.PyQt.QtCore import QVariant


# ============================================================
# CONFIGURAÇÕES
# ============================================================

KML_GOES_URL = (
    "https://dataserver-coids.inpe.br/"
    "queimadas/queimadas/focos/kml/"
    "focos_goes_ponto_atencao_48hr/"
    "focos_goes_ponto_atencao_48hr.kml"
)

KML_EVENTOS_URL = (
    "https://dataserver-coids.inpe.br/"
    "queimadas/queimadas/eventos/ativos/"
    "eventos_ativos.kml"
)

GOES_LAYER_NAME = (
    "focos_goes_ponto_atencao_48hr — 72 até 143 repetições"
)

TIPOS_EVENTO = {
    "Incêndio",
    "Possível início de incêndio"
}

BUFFER_METROS = 4000

# Arquivo permanente
OUTPUT_GPKG = "/tmp/eventos_ativos_buffer_4km_teste.gpkg"

OUTPUT_LAYER_NAME = (
    "buffer_eventos_ativos_goes_72_143"
)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def texto_local(elemento, tag):

    if elemento is None:
        return ""

    for child in elemento.iter():

        if child.tag.split("}")[-1] == tag:
            return (child.text or "").strip()

    return ""


def extrair_description(description):

    if not description:
        return {}

    texto = html.unescape(description)

    atributos = {}

    padroes = {

        "tipo_de_fogo":
            r"<td><b>Tipo</b></td>\s*<td[^>]*><b>(.*?)</b>",

        "data_inicio":
            r"<td><b>Data início</b></td>\s*<td>(.*?)</td>",

        "data_fim":
            r"<td><b>Data fim</b></td>\s*<td>(.*?)</td>",

        "duracao":
            r"<td><b>Duração</b></td>\s*<td>(.*?)</td>",

        "municipio":
            r"<td><b>Município</b></td>\s*<td>(.*?)</td>",

        "estado":
            r"<td><b>Estado</b></td>\s*<td>(.*?)</td>",

        "max_dias_sem_chuva":
            r"<td><b>Máx\. dias sem chuva</b></td>\s*<td>(.*?)</td>",

        "total_focos":
            r"<td><b>Total de focos</b></td>\s*<td>(.*?)</td>",

        "dias_com_foco":
            r"<td><b>Dias com foco</b></td>\s*<td>(.*?)</td>",

        "ultimo_foco":
            r"<td><b>Último foco</b></td>\s*<td>(.*?)</td>",

        "frentes_ativas":
            r"<td><b>Frentes ativas \(último dia\)</b></td>\s*<td>(.*?)</td>",

        "desmatamento":
            r"<td><b>Desmatamento</b></td>\s*<td>(.*?)</td>",

        "vegetacao":
            r"<td><b>Vegetação</b></td>\s*<td>(.*?)</td>",

        "transicao":
            r"<td><b>Transição</b></td>\s*<td>(.*?)</td>",
    }

    for campo, padrao in padroes.items():

        resultado = re.search(
            padrao,
            texto,
            flags=re.IGNORECASE | re.DOTALL
        )

        if resultado:

            valor = resultado.group(1)

            valor = re.sub(
                r"<[^>]+>",
                "",
                valor
            )

            atributos[campo] = html.unescape(
                valor
            ).strip()

        else:

            atributos[campo] = None

    return atributos


def extrair_coordenadas(texto):

    pontos = []

    if not texto:
        return pontos

    for item in texto.strip().split():

        partes = item.split(",")

        if len(partes) < 2:
            continue

        try:

            x = float(partes[0])
            y = float(partes[1])

            pontos.append(
                QgsPointXY(x, y)
            )

        except ValueError:
            continue

    return pontos


# ============================================================
# INÍCIO
# ============================================================

print("=" * 70)
print("EVENTOS ATIVOS × GOES 72–143 + BUFFER 4 KM")
print("=" * 70)


# ============================================================
# 1. LOCALIZAR CAMADA GOES
# ============================================================

print()
print("Procurando camada GOES:")
print(GOES_LAYER_NAME)

camada_goes = None

for layer in QgsProject.instance().mapLayers().values():

    if layer.name() == GOES_LAYER_NAME:

        camada_goes = layer
        break


if camada_goes is None:

    raise RuntimeError(
        f"\nCamada não encontrada:\n"
        f"{GOES_LAYER_NAME}"
    )


print("✓ Camada encontrada")
print(
    f"  Feições: "
    f"{camada_goes.featureCount()}"
)


# ============================================================
# 2. LER PONTOS GOES
# ============================================================

pontos_goes = []

for feature in camada_goes.getFeatures():

    geom = feature.geometry()

    if geom is None or geom.isEmpty():
        continue

    if geom.isMultipart():

        for ponto in geom.asMultiPoint():

            pontos_goes.append(
                QgsGeometry.fromPointXY(
                    ponto
                )
            )

    else:

        if geom.type() == 0:

            pontos_goes.append(
                QgsGeometry(geom)
            )


print(
    f"✓ Pontos GOES válidos: "
    f"{len(pontos_goes)}"
)


if not pontos_goes:

    raise RuntimeError(
        "Nenhum ponto GOES válido."
    )


# ============================================================
# 3. BAIXAR EVENTOS ATIVOS
# ============================================================

print()
print("-" * 70)
print("BAIXANDO EVENTOS ATIVOS")
print("-" * 70)

response = requests.get(
    KML_EVENTOS_URL,
    timeout=120
)

response.raise_for_status()

print(
    f"✓ Download realizado: "
    f"{len(response.content):,} bytes"
)


# ============================================================
# 4. LER XML
# ============================================================

root = ET.fromstring(
    response.content
)

folders = [
    element
    for element in root.iter()
    if element.tag.split("}")[-1] == "Folder"
]

print(
    f"✓ Folders encontrados: "
    f"{len(folders)}"
)


# ============================================================
# 5. EXTRAIR POLÍGONOS DOS EVENTOS
# ============================================================

eventos = []

for folder in folders:

    placemarks = [
        element
        for element in folder.iter()
        if element.tag.split("}")[-1] == "Placemark"
    ]

    for placemark in placemarks:

        name = texto_local(
            placemark,
            "name"
        )

        description = texto_local(
            placemark,
            "description"
        )

        atributos = extrair_description(
            description
        )

        tipo = atributos.get(
            "tipo_de_fogo"
        )

        if tipo not in TIPOS_EVENTO:
            continue


        # ----------------------------------------------------
        # POLÍGONOS
        # ----------------------------------------------------

        polygon_elements = [
            element
            for element in placemark.iter()
            if element.tag.split("}")[-1] == "Polygon"
        ]

        if not polygon_elements:
            continue

        poligonos = []

        for polygon_element in polygon_elements:

            outer_ring = None

            for element in polygon_element.iter():

                if (
                    element.tag.split("}")[-1]
                    == "outerBoundaryIs"
                ):

                    for child in element.iter():

                        if (
                            child.tag.split("}")[-1]
                            == "coordinates"
                        ):

                            outer_ring = (
                                child.text or ""
                            )

                            break

                    if outer_ring:
                        break

            if not outer_ring:
                continue

            pontos = extrair_coordenadas(
                outer_ring
            )

            if len(pontos) < 3:
                continue

            if pontos[0] != pontos[-1]:

                pontos.append(
                    pontos[0]
                )

            try:

                geometria = (
                    QgsGeometry.fromPolygonXY(
                        [pontos]
                    )
                )

                if not geometria.isEmpty():

                    poligonos.append(
                        geometria
                    )

            except Exception:

                continue


        if not poligonos:
            continue


        geometria_evento = poligonos[0]

        for geom in poligonos[1:]:

            try:

                geometria_evento = (
                    geometria_evento.combine(
                        geom
                    )
                )

            except Exception:
                pass


        eventos.append({

            "name": name,

            "tipo_de_fogo": tipo,

            "geometry": geometria_evento,

            "atributos": atributos
        })


print()
print(
    f"✓ Eventos com polígonos: "
    f"{len(eventos)}"
)


# ============================================================
# 6. CONFIGURAR CÁLCULO DE DISTÂNCIA
# ============================================================

distance = QgsDistanceArea()

distance.setEllipsoid(
    "WGS84"
)


# ============================================================
# 7. ASSOCIAR EVENTOS AOS GOES
# ============================================================

print()
print("-" * 70)
print("ASSOCIANDO EVENTOS AOS PONTOS GOES")
print("-" * 70)

eventos_resultado = {}

total_intersecoes = 0
total_vizinhos = 0


for indice_goes, ponto_goes in enumerate(
    pontos_goes,
    start=1
):

    encontrados = []


    # --------------------------------------------------------
    # INTERSEÇÃO
    # --------------------------------------------------------

    for indice_evento, evento in enumerate(
        eventos
    ):

        geometria_evento = (
            evento["geometry"]
        )

        try:

            if geometria_evento.intersects(
                ponto_goes
            ):

                encontrados.append(
                    (
                        indice_evento,
                        0.0,
                        "interseção"
                    )
                )

        except Exception:

            continue


    # --------------------------------------------------------
    # VIZINHO MAIS PRÓXIMO
    # --------------------------------------------------------

    if encontrados:

        total_intersecoes += 1

    else:

        menor_distancia = None
        indice_mais_proximo = None

        ponto_xy = ponto_goes.asPoint()

        for indice_evento, evento in enumerate(
            eventos
        ):

            geometria_evento = (
                evento["geometry"]
            )

            try:

                ponto_evento = (
                    geometria_evento.centroid()
                )

                distancia = (
                    distance.measureLine(
                        ponto_xy,
                        ponto_evento.asPoint()
                    )
                )

                if (
                    menor_distancia is None
                    or distancia < menor_distancia
                ):

                    menor_distancia = distancia

                    indice_mais_proximo = (
                        indice_evento
                    )

            except Exception:

                continue


        if indice_mais_proximo is not None:

            encontrados.append(
                (
                    indice_mais_proximo,
                    menor_distancia,
                    "vizinho mais próximo"
                )
            )

            total_vizinhos += 1


    # --------------------------------------------------------
    # GUARDAR
    # --------------------------------------------------------

    for (
        indice_evento,
        distancia,
        metodo
    ) in encontrados:

        if indice_evento not in eventos_resultado:

            eventos_resultado[
                indice_evento
            ] = {

                "evento":
                    eventos[indice_evento],

                "goes_count":
                    0,

                "menor_distancia":
                    distancia,

                "metodos":
                    set()
            }


        resultado = (
            eventos_resultado[
                indice_evento
            ]
        )

        resultado[
            "goes_count"
        ] += 1

        resultado[
            "metodos"
        ].add(
            metodo
        )

        if (
            distancia
            < resultado["menor_distancia"]
        ):

            resultado[
                "menor_distancia"
            ] = distancia


# ============================================================
# 8. RESULTADO
# ============================================================

print()
print("-" * 70)
print("RESULTADO DA ASSOCIAÇÃO")
print("-" * 70)

print(
    f"Pontos GOES analisados: "
    f"{len(pontos_goes)}"
)

print(
    f"Pontos com interseção: "
    f"{total_intersecoes}"
)

print(
    f"Pontos associados pelo vizinho mais próximo: "
    f"{total_vizinhos}"
)

print(
    f"Eventos selecionados: "
    f"{len(eventos_resultado)}"
)


# ============================================================
# 9. CRIAR CAMADA DE EVENTOS
# ============================================================

camada_eventos = QgsVectorLayer(
    "Polygon?crs=EPSG:4326",
    "Eventos Ativos — GOES 72 até 143",
    "memory"
)

provider = (
    camada_eventos.dataProvider()
)


provider.addAttributes([

    QgsField(
        "nome",
        QVariant.String
    ),

    QgsField(
        "tipo_fogo",
        QVariant.String
    ),

    QgsField(
        "municipio",
        QVariant.String
    ),

    QgsField(
        "estado",
        QVariant.String
    ),

    QgsField(
        "data_inicio",
        QVariant.String
    ),

    QgsField(
        "data_fim",
        QVariant.String
    ),

    QgsField(
        "duracao",
        QVariant.String
    ),

    QgsField(
        "total_focos",
        QVariant.String
    ),

    QgsField(
        "dias_foco",
        QVariant.String
    ),

    QgsField(
        "ultimo_foco",
        QVariant.String
    ),

    QgsField(
        "frentes_ativas",
        QVariant.String
    ),

    QgsField(
        "max_sem_chuva",
        QVariant.String
    ),

    QgsField(
        "desmatamento",
        QVariant.String
    ),

    QgsField(
        "vegetacao",
        QVariant.String
    ),

    QgsField(
        "transicao",
        QVariant.String
    ),

    QgsField(
        "qtd_goes",
        QVariant.Int
    ),

    QgsField(
        "dist_m",
        QVariant.Double
    ),

    QgsField(
        "metodo",
        QVariant.String
    )
])

camada_eventos.updateFields()


# ============================================================
# 10. INSERIR EVENTOS SELECIONADOS
# ============================================================

features_eventos = []

for resultado in eventos_resultado.values():

    evento = resultado["evento"]

    atributos = (
        evento["atributos"]
    )

    feature = QgsFeature(
        camada_eventos.fields()
    )

    feature.setGeometry(
        evento["geometry"]
    )

    feature.setAttributes([

        evento["name"],

        evento["tipo_de_fogo"],

        atributos.get(
            "municipio"
        ),

        atributos.get(
            "estado"
        ),

        atributos.get(
            "data_inicio"
        ),

        atributos.get(
            "data_fim"
        ),

        atributos.get(
            "duracao"
        ),

        atributos.get(
            "total_focos"
        ),

        atributos.get(
            "dias_com_foco"
        ),

        atributos.get(
            "ultimo_foco"
        ),

        atributos.get(
            "frentes_ativas"
        ),

        atributos.get(
            "max_dias_sem_chuva"
        ),

        atributos.get(
            "desmatamento"
        ),

        atributos.get(
            "vegetacao"
        ),

        atributos.get(
            "transicao"
        ),

        resultado[
            "goes_count"
        ],

        round(
            resultado[
                "menor_distancia"
            ],
            2
        ),

        ", ".join(
            sorted(
                resultado[
                    "metodos"
                ]
            )
        )
    ])

    features_eventos.append(
        feature
    )


provider.addFeatures(
    features_eventos
)

camada_eventos.updateExtents()


# ============================================================
# 11. CRIAR BUFFER DE 4 KM
# ============================================================

print()
print("-" * 70)
print("CRIANDO BUFFER DE 4 KM")
print("-" * 70)


# EPSG:5880 = projeção métrica para o Brasil
crs_geografico = QgsCoordinateReferenceSystem(
    "EPSG:4326"
)

crs_metrico = QgsCoordinateReferenceSystem(
    "EPSG:5880"
)

transform_para_metros = (
    QgsCoordinateTransform(
        crs_geografico,
        crs_metrico,
        QgsProject.instance()
    )
)

transform_para_graus = (
    QgsCoordinateTransform(
        crs_metrico,
        crs_geografico,
        QgsProject.instance()
    )
)


camada_buffer = QgsVectorLayer(
    "Polygon?crs=EPSG:4326",
    "Buffer Eventos Ativos — GOES 72 até 143",
    "memory"
)

provider_buffer = (
    camada_buffer.dataProvider()
)


# ============================================================
# COPIAR TODOS OS ATRIBUTOS
# ============================================================

provider_buffer.addAttributes(
    camada_eventos.fields()
)

camada_buffer.updateFields()


features_buffer = []


for feature_evento in (
    camada_eventos.getFeatures()
):

    geometria = (
        feature_evento.geometry()
    )

    if geometria is None or geometria.isEmpty():
        continue


    try:

        # ----------------------------------------------------
        # Transformar para CRS métrico
        # ----------------------------------------------------

        geometria_metrica = (
            QgsGeometry(
                geometria
            )
        )

        geometria_metrica.transform(
            transform_para_metros
        )


        # ----------------------------------------------------
        # BUFFER DE 4 KM
        # ----------------------------------------------------

        buffer_metrico = (
            geometria_metrica.buffer(
                BUFFER_METROS,
                30
            )
        )


        if (
            buffer_metrico is None
            or buffer_metrico.isEmpty()
        ):
            continue


        # ----------------------------------------------------
        # Voltar para EPSG:4326
        # ----------------------------------------------------

        buffer_final = (
            QgsGeometry(
                buffer_metrico
            )
        )

        buffer_final.transform(
            transform_para_graus
        )


        # ----------------------------------------------------
        # NOVA FEIÇÃO
        # ----------------------------------------------------

        feature_buffer = QgsFeature(
            camada_buffer.fields()
        )

        feature_buffer.setGeometry(
            buffer_final
        )

        # Copiar TODOS os atributos
        feature_buffer.setAttributes(
            feature_evento.attributes()
        )

        features_buffer.append(
            feature_buffer
        )


    except Exception as e:

        print(
            "⚠ Erro ao gerar buffer:"
        )

        print(e)

        continue


provider_buffer.addFeatures(
    features_buffer
)

camada_buffer.updateExtents()


print(
    f"✓ Buffers criados: "
    f"{len(features_buffer)}"
)
# ============================================================
# 12. SALVAR COMO GEO PACKAGE PERMANENTE
# ============================================================

print()
print("-" * 70)
print("SALVANDO CAMADA PERMANENTE")
print("-" * 70)


# ------------------------------------------------------------
# Criar diretório caso necessário
# ------------------------------------------------------------

diretorio = os.path.dirname(
    OUTPUT_GPKG
)

os.makedirs(
    diretorio,
    exist_ok=True
)


# ------------------------------------------------------------
# Se o GeoPackage já existir
# ------------------------------------------------------------

if os.path.exists(OUTPUT_GPKG):

    print(
        "GeoPackage já existente."
    )

    print(
        "Removendo arquivo anterior..."
    )

    try:

        os.remove(
            OUTPUT_GPKG
        )

    except PermissionError:

        raise RuntimeError(
            "Não foi possível substituir o GeoPackage.\n"
            "O arquivo provavelmente está aberto no QGIS.\n\n"
            f"Arquivo: {OUTPUT_GPKG}"
        )

    print(
        "✓ Arquivo anterior removido."
    )


# ------------------------------------------------------------
# Configuração de gravação
# ------------------------------------------------------------
options = QgsVectorFileWriter.SaveVectorOptions()

options.driverName = "GPKG"
options.layerName = OUTPUT_LAYER_NAME
options.actionOnExistingFile = (
    QgsVectorFileWriter.CreateOrOverwriteFile
)

retorno = QgsVectorFileWriter.writeAsVectorFormatV3(
    camada_buffer,
    OUTPUT_GPKG,
    QgsProject.instance().transformContext(),
    options
)

print()
print("RETORNO DA GRAVAÇÃO:")
print(retorno)

result = retorno[0]

if result != QgsVectorFileWriter.NoError:

    error_message = ""

    if len(retorno) > 1:
        error_message = retorno[1]

    raise RuntimeError(
        "Erro ao criar GeoPackage:\n"
        f"{error_message}"
    )

print()
print("✓ GeoPackage criado:")
print(OUTPUT_GPKG)

print()
print("Arquivo existe?")
print(os.path.exists(OUTPUT_GPKG))

print(
    OUTPUT_GPKG
)

print(
    f"✓ Camada: {OUTPUT_LAYER_NAME}"
)

print(
    f"✓ Feições: {camada_buffer.featureCount()}"
)

print()
print(
    "✓ CAMADA PERMANENTE SALVA COM SUCESSO"
)
# ============================================================
# 13. CARREGAR CAMADA PERMANENTE NO QGIS
# ============================================================

caminho_layer = (
    f"{OUTPUT_GPKG}|layername={OUTPUT_LAYER_NAME}"
)

camada_permanente = QgsVectorLayer(
    caminho_layer,
    "Buffer Eventos Ativos — GOES 72 até 143",
    "ogr"
)


if not camada_permanente.isValid():

    raise RuntimeError(
        "Não foi possível carregar "
        "a camada permanente."
    )


QgsProject.instance().addMapLayer(
    camada_permanente
)


# ============================================================
# 14. FINAL
# ============================================================

print()
print("=" * 70)
print("TESTE CONCLUÍDO")
print("=" * 70)

print()
print(
    "✓ Pontos GOES analisados:"
)

print(
    f"  {len(pontos_goes)}"
)

print()
print(
    "✓ Eventos selecionados:"
)

print(
    f"  {len(eventos_resultado)}"
)

print()
print(
    "✓ Buffers de 4 km:"
)

print(
    f"  {len(features_buffer)}"
)

print()
print(
    "✓ Todos os atributos dos eventos "
    "foram preservados."
)

print()
print(
    "✓ Camada salva permanentemente em:"
)

print(
    f"  {OUTPUT_GPKG}"
)

print()
print(
    "✓ Camada adicionada ao projeto QGIS."
)

print("=" * 70)