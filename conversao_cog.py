from pathlib import Path
from osgeo import gdal

# Diretório do script
BASE_DIR = Path(__file__).parent

# Pastas
INPUT_DIR = BASE_DIR / "rasters"
OUTPUT_DIR = BASE_DIR / "saida_cog_zstd"
OUTPUT_DIR.mkdir(exist_ok=True)

arquivos = list(INPUT_DIR.glob("*.tif"))

print(f"\n{len(arquivos)} arquivos encontrados.\n")

for arquivo in arquivos:

    print(f"Convertendo: {arquivo.name}")

    ds = gdal.Open(str(arquivo))

    if ds is None:
        print(f"Erro ao abrir {arquivo.name}")
        continue

    banda = ds.GetRasterBand(1)
    tipo = banda.DataType

    # Predictor adequado ao tipo de dado
    if tipo in [gdal.GDT_Float32, gdal.GDT_Float64]:
        predictor = "3"
    else:
        predictor = "2"

    saida = OUTPUT_DIR / arquivo.name

    try:
        gdal.Translate(
            str(saida),
            ds,
            format="COG",
            creationOptions=[
                "COMPRESS=ZSTD",
                f"PREDICTOR={predictor}",
                "LEVEL=22",
                "BIGTIFF=IF_SAFER",
                "BLOCKSIZE=512"
            ]
        )

        tamanho_original = arquivo.stat().st_size / (1024 * 1024)
        tamanho_saida = saida.stat().st_size / (1024 * 1024)

        reducao = (
            (1 - tamanho_saida / tamanho_original) * 100
            if tamanho_original > 0
            else 0
        )

        print(
            f"✓ {arquivo.name} | "
            f"{tamanho_original:.1f} MB → {tamanho_saida:.1f} MB "
            f"({reducao:.1f}% redução)"
        )

    except Exception as e:
        print(f"✗ Erro: {e}")

    ds = None

print("\nConversão concluída.")