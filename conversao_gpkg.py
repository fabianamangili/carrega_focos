from pathlib import Path
from qgis.core import QgsProject
import processing

camadas_vetoriais = [
    l for l in QgsProject.instance().mapLayers().values()
    if l.type() == 0
]

output = str(Path.home() / "amostras.gpkg")

processing.run(
    "native:package",
    {
        'LAYERS': camadas_vetoriais,
        'OUTPUT': output,
        'OVERWRITE': True,
        'SAVE_STYLES': True,
        'SAVE_METADATA': True
    }
)

print(f"GeoPackage salvo em: {output}")