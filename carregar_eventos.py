import requests
import xml.etree.ElementTree as ET
import html
import re

from qgis.core import (
    QgsVectorLayer,
    QgsProject,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsField
)

from qgis.PyQt.QtCore import QVariant


# ============================================================
# CONFIGURAÇÃO
# ============================================================

EVENTOS_ATIVOS_URL = (
    "https://dataserver-coids.inpe.br/"
    "queimadas/queimadas/eventos/ativos/"
    "eventos_ativos.kml"
)

TIPOS_INTERESSE = {
    "Incêndio",
    "Possível início de incêndio"
}

NOME_CAMADA = "Eventos Ativos - Incêndios"

NS = {
    "kml": "http://www.opengis.net/kml/2.2"
}


# ============================================================
# EXTRAIR ATRIBUTOS DA DESCRIPTION
# ============================================================

def extrair_atributos_description(description):

    atributos = {}

    if not description:
        return atributos

    texto = html.unescape(
        description
    )

    linhas = re.findall(
        r"<tr.*?>(.*?)</tr>",
        texto,
        flags=re.IGNORECASE | re.DOTALL
    )

    for linha in linhas:

        celulas = re.findall(
            r"<td.*?>(.*?)</td>",
            linha,
            flags=re.IGNORECASE | re.DOTALL
        )

        if len(celulas) < 2:
            continue

        campo = re.sub(
            r"<[^>]+>",
            "",
            celulas[0]
        )

        valor = re.sub(
            r"<[^>]+>",
            "",
            celulas[1]
        )

        campo = (
            html.unescape(campo)
            .strip()
        )

        valor = (
            html.unescape(valor)
            .strip()
        )

        if campo:
            atributos[campo] = valor

    return atributos


# ============================================================
# EXTRAIR POLYGON
# ============================================================

def extrair_polygon(placemark):

    polygon = placemark.find(
        ".//kml:Polygon",
        NS
    )

    if polygon is None:
        return None


    outer = polygon.find(
        ".//kml:outerBoundaryIs",
        NS
    )

    if outer is None:
        return None


    ring = outer.find(
        ".//kml:LinearRing",
        NS
    )

    if ring is None:
        return None


    coordinates = ring.find(
        "kml:coordinates",
        NS
    )

    if coordinates is None:
        return None


    texto = (
        coordinates.text or ""
    ).strip()

    if not texto:
        return None


    pontos = []

    for coordenada in texto.split():

        partes = coordenada.split(",")

        if len(partes) < 2:
            continue

        try:

            longitude = float(
                partes[0]
            )

            latitude = float(
                partes[1]
            )

            pontos.append(
                QgsPointXY(
                    longitude,
                    latitude
                )
            )

        except ValueError:

            continue


    if len(pontos) < 3:
        return None


    # Garantir fechamento do anel
    if pontos[0] != pontos[-1]:

        pontos.append(
            pontos[0]
        )


    return QgsGeometry.fromPolygonXY(
        [pontos]
    )


# ============================================================
# DOWNLOAD
# ============================================================

print("=" * 70)
print("TESTE - EVENTOS ATIVOS COMO POLÍGONOS")
print("=" * 70)

print("\nBaixando KML...")

response = requests.get(
    EVENTOS_ATIVOS_URL,
    timeout=60
)

response.raise_for_status()

print(
    f"✓ Download realizado: "
    f"{len(response.content):,} bytes"
)


# ============================================================
# XML
# ============================================================

print("\nLendo XML...")

root = ET.fromstring(
    response.content
)

print("✓ XML carregado")


# ============================================================
# LOCALIZAR FOLDERS
# ============================================================

folders = root.findall(
    ".//kml:Folder",
    NS
)

print(
    f"Folders encontrados: "
    f"{len(folders)}"
)


# ============================================================
# EXTRAIR EVENTOS POLIGONAIS
# ============================================================

eventos = []

contadores = {
    "Incêndio": {
        "placemarks": 0,
        "poligonos": 0,
        "sem_geometria": 0
    },
    "Possível início de incêndio": {
        "placemarks": 0,
        "poligonos": 0,
        "sem_geometria": 0
    }
}


for folder in folders:

    nome_folder_element = folder.find(
        "kml:name",
        NS
    )

    if nome_folder_element is None:
        continue

    nome_folder = (
        nome_folder_element.text
        or ""
    ).strip()

    if nome_folder not in TIPOS_INTERESSE:
        continue


    placemarks = folder.findall(
        ".//kml:Placemark",
        NS
    )

    contadores[nome_folder][
        "placemarks"
    ] += len(placemarks)


    for placemark in placemarks:

        # ----------------------------------------------------
        # IMPORTANTE:
        # somente Placemark com POLYGON
        # ----------------------------------------------------

        geometry = extrair_polygon(
            placemark
        )

        if geometry is None:

            contadores[nome_folder][
                "sem_geometria"
            ] += 1

            continue


        contadores[nome_folder][
            "poligonos"
        ] += 1


        # ----------------------------------------------------
        # Nome
        # ----------------------------------------------------

        name_element = placemark.find(
            "kml:name",
            NS
        )

        nome = ""

        if name_element is not None:

            nome = (
                name_element.text
                or ""
            ).strip()


        # ----------------------------------------------------
        # Description
        # ----------------------------------------------------

        description_element = (
            placemark.find(
                "kml:description",
                NS
            )
        )

        description = ""

        if description_element is not None:

            description = (
                description_element.text
                or ""
            )


        # ----------------------------------------------------
        # Atributos
        # ----------------------------------------------------

        atributos = (
            extrair_atributos_description(
                description
            )
        )


        # ----------------------------------------------------
        # Evento
        # ----------------------------------------------------

        eventos.append(
            {
                "geometry": geometry,

                "tipo_de_fogo":
                    nome_folder,

                "nome":
                    nome,

                "data_inicio":
                    atributos.get(
                        "Data início",
                        ""
                    ),

                "data_fim":
                    atributos.get(
                        "Data fim",
                        ""
                    ),

                "duracao":
                    atributos.get(
                        "Duração",
                        ""
                    ),

                "municipio":
                    atributos.get(
                        "Município",
                        ""
                    ),

                "estado":
                    atributos.get(
                        "Estado",
                        ""
                    ),

                "max_dias_sem_chuva":
                    atributos.get(
                        "Máx. dias sem chuva",
                        ""
                    ),

                "total_focos":
                    atributos.get(
                        "Total de focos",
                        ""
                    ),

                "dias_com_foco":
                    atributos.get(
                        "Dias com foco",
                        ""
                    ),

                "ultimo_foco":
                    atributos.get(
                        "Último foco",
                        ""
                    ),

                "frentes_ativas":
                    atributos.get(
                        "Frentes ativas (último dia)",
                        ""
                    ),

                "desmatamento":
                    atributos.get(
                        "Desmatamento",
                        ""
                    ),

                "vegetacao":
                    atributos.get(
                        "Vegetação",
                        ""
                    ),

                "transicao":
                    atributos.get(
                        "Transição",
                        ""
                    )
            }
        )


# ============================================================
# RESULTADO DA LEITURA
# ============================================================

print("\n" + "=" * 70)
print("RESULTADO DA LEITURA")
print("=" * 70)

for tipo in TIPOS_INTERESSE:

    dados = contadores[tipo]

    print(
        f"\n{tipo}"
    )

    print(
        f"  Placemark: "
        f"{dados['placemarks']}"
    )

    print(
        f"  Polígonos: "
        f"{dados['poligonos']}"
    )

    print(
        f"  Sem polígono: "
        f"{dados['sem_geometria']}"
    )


print(
    f"\nTotal de eventos poligonais: "
    f"{len(eventos)}"
)


# ============================================================
# CRIAR CAMADA POLIGONAL
# ============================================================

print(
    "\nCriando camada poligonal..."
)

layer = QgsVectorLayer(
    "Polygon?crs=EPSG:4326",
    NOME_CAMADA,
    "memory"
)

if not layer.isValid():

    raise RuntimeError(
        "Não foi possível criar "
        "a camada poligonal."
    )


# ============================================================
# CAMPOS
# ============================================================

provider = layer.dataProvider()

provider.addAttributes(
    [

        QgsField(
            "tipo_fogo",
            QVariant.String
        ),

        QgsField(
            "nome",
            QVariant.String
        ),

        QgsField(
            "dt_inicio",
            QVariant.String
        ),

        QgsField(
            "dt_fim",
            QVariant.String
        ),

        QgsField(
            "duracao",
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
            "max_sem_chuva",
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
        )

    ]
)

layer.updateFields()


# ============================================================
# ADICIONAR FEIÇÕES
# ============================================================

features = []

for evento in eventos:

    feature = QgsFeature(
        layer.fields()
    )

    feature.setGeometry(
        evento["geometry"]
    )

    feature["tipo_fogo"] = (
        evento["tipo_de_fogo"]
    )

    feature["nome"] = (
        evento["nome"]
    )

    feature["dt_inicio"] = (
        evento["data_inicio"]
    )

    feature["dt_fim"] = (
        evento["data_fim"]
    )

    feature["duracao"] = (
        evento["duracao"]
    )

    feature["municipio"] = (
        evento["municipio"]
    )

    feature["estado"] = (
        evento["estado"]
    )

    feature["max_sem_chuva"] = (
        evento["max_dias_sem_chuva"]
    )

    feature["total_focos"] = (
        evento["total_focos"]
    )

    feature["dias_foco"] = (
        evento["dias_com_foco"]
    )

    feature["ultimo_foco"] = (
        evento["ultimo_foco"]
    )

    feature["frentes_ativas"] = (
        evento["frentes_ativas"]
    )

    feature["desmatamento"] = (
        evento["desmatamento"]
    )

    feature["vegetacao"] = (
        evento["vegetacao"]
    )

    feature["transicao"] = (
        evento["transicao"]
    )

    features.append(
        feature
    )


provider.addFeatures(
    features
)

layer.updateExtents()


# ============================================================
# ADICIONAR AO PROJETO
# ============================================================

QgsProject.instance().addMapLayer(
    layer
)


# ============================================================
# RESULTADO FINAL
# ============================================================

print("\n" + "=" * 70)
print("CAMADA CRIADA")
print("=" * 70)

print(
    f"✓ Nome: {NOME_CAMADA}"
)

print(
    f"✓ Feições: "
    f"{layer.featureCount()}"
)

print(
    "✓ Geometria: Polygon"
)

print(
    "✓ CRS: EPSG:4326"
)

print(
    "✓ Atributos: "
    f"{len(layer.fields())}"
)

print(
    "\n✓ Camada adicionada ao projeto QGIS."
)

print(
    "\n✓ FIM DO TESTE"
)

print("=" * 70)