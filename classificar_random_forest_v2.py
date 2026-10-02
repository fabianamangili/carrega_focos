# -*- coding: utf-8 -*-
"""
Treinamento Random Forest utilizando atributos das camadas de amostras.
"""

import os
import joblib
import numpy as np
import pandas as pd

from qgis.core import QgsProject

from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    accuracy_score,
    classification_report
)
from sklearn.model_selection import (
    train_test_split,
    cross_val_score
)

# ============================================
# CONFIGURAÇÕES
# ============================================

PREFIXO_PONTOS = "amostras — P_"
CAMPO_ALVO = "VALIDA"

SUFIXOS_RASTERS = [
    "b5_dif",
    "bai_dif_s1",
    "gemi_dif",
    "mirbi_pos",
    "nbr_dif",
    "nbr_dif_s1",
    "nbrswr_dif",
    "ndvi_dif"
]

DIR_PROJETO = os.path.dirname(os.path.abspath(__file__))

CAMINHO_MODELO = os.path.join(
    DIR_PROJETO,
    "rf_model_queimadas_v2.pkl"
)

CAMINHO_IMPUTER = os.path.join(
    DIR_PROJETO,
    "imputer_v2.pkl"
)

CAMINHO_FEATURES = os.path.join(
    DIR_PROJETO,
    "features_v2.pkl"
)

# ============================================
# 1. LOCALIZAR CAMADAS DE AMOSTRAS
# ============================================

projeto = QgsProject.instance()

camadas_pontos = [
    layer
    for layer in projeto.mapLayers().values()
    if layer.type() == 0
    and layer.name().startswith(PREFIXO_PONTOS)
]

if not camadas_pontos:
    raise Exception(
        f"Nenhuma camada com prefixo '{PREFIXO_PONTOS}' encontrada."
    )

print("\n=== CAMADAS ENCONTRADAS ===")
for layer in camadas_pontos:
    print(layer.name())

# ============================================
# 2. COLETAR DADOS DAS TABELAS DE ATRIBUTOS
# ============================================

todos_dados = []
todos_alvos = []

for layer_pontos in camadas_pontos:

    nome = layer_pontos.name()

    try:
        partes = nome.split("_")

        path_row = partes[-2]
        data = partes[-1]

    except Exception:
        print(f"Nome inválido: {nome}")
        continue

    print(
        f"\nProcessando path_row {path_row} - data {data}"
    )

    pontos_validos = 0
    print(layer_pontos.fields().names())

    for feat in layer_pontos.getFeatures():

        # -------------------------
        # Classe alvo
        # -------------------------
        try:
            alvo = int(feat[CAMPO_ALVO])
        except Exception:
            continue

        if alvo not in (0, 1):
            continue

        # -------------------------
        # Variáveis explicativas
        # -------------------------
        try:

            valores = []

            for campo in SUFIXOS_RASTERS:

                valor = feat[campo]

                try:
                    valores.append(float(valor))
                except:
                    valores.append(np.nan)

        except Exception as e:
            print(e)
            continue

        todos_dados.append(valores)
        todos_alvos.append(alvo)

        pontos_validos += 1

    print(f"  Pontos válidos: {pontos_validos}")

# ============================================
# 3. VERIFICAÇÃO
# ============================================

if len(todos_dados) < 10:
    raise Exception(
        f"Apenas {len(todos_dados)} pontos válidos. "
        "Mínimo recomendado: 10."
    )

# ============================================
# 4. DATAFRAME
# ============================================

df = pd.DataFrame(
    todos_dados,
    columns=SUFIXOS_RASTERS
)

df["target"] = todos_alvos

print("\n=== TOTAL DE AMOSTRAS ===")
print(len(df))

print("\n=== DISTRIBUIÇÃO DAS CLASSES ===")
print(df["target"].value_counts())

# ============================================
# 5. CORRELAÇÃO ENTRE VARIÁVEIS
# ============================================

print("\n=== CORRELAÇÃO ENTRE ÍNDICES ===")

corr = df[SUFIXOS_RASTERS].corr()

print(corr.round(2))

# ============================================
# 6. PREPARAÇÃO DOS DADOS
# ============================================

X = df[SUFIXOS_RASTERS]
y = df["target"]

imputer = SimpleImputer(strategy="mean")

X_imputed = imputer.fit_transform(X)

# ============================================
# 7. TREINAMENTO / TESTE
# ============================================

X_train, X_test, y_train, y_test = train_test_split(
    X_imputed,
    y,
    test_size=0.30,
    random_state=42,
    stratify=y
)

rf = RandomForestClassifier(
    n_estimators=200,
    random_state=42,
    n_jobs=-1,
    class_weight="balanced"
)

rf.fit(X_train, y_train)

# ============================================
# 8. VALIDAÇÃO CRUZADA
# ============================================

print("\n=== VALIDAÇÃO CRUZADA (5-FOLD) ===")

cv_scores = cross_val_score(
    rf,
    X_imputed,
    y,
    cv=5
)

print(
    f"Acurácia média: "
    f"{cv_scores.mean():.3f} "
    f"(+/- {cv_scores.std():.3f})"
)

# ============================================
# 9. AVALIAÇÃO
# ============================================

print("\n=== AVALIAÇÃO NO CONJUNTO DE TESTE ===")

y_pred = rf.predict(X_test)

print(
    f"Acurácia: "
    f"{accuracy_score(y_test, y_pred):.3f}"
)

print(
    classification_report(
        y_test,
        y_pred,
        target_names=[
            "Não queimada",
            "Queimada"
        ]
    )
)

# ============================================
# 10. PERMUTATION IMPORTANCE
# ============================================

print("\n=== PERMUTATION IMPORTANCE ===")

perm = permutation_importance(
    rf,
    X_test,
    y_test,
    n_repeats=30,
    random_state=42,
    n_jobs=-1,
    scoring="f1"
)

perm_df = pd.DataFrame({
    "feature": SUFIXOS_RASTERS,
    "importance_mean": perm.importances_mean,
    "importance_std": perm.importances_std
})

perm_df = perm_df.sort_values(
    "importance_mean",
    ascending=False
)

print(perm_df)

# ============================================
# 11. FEATURE IMPORTANCE DO RANDOM FOREST
# ============================================

print("\n=== IMPORTÂNCIA DAS FEATURES ===")

imp = pd.DataFrame({
    "feature": SUFIXOS_RASTERS,
    "importance": rf.feature_importances_
})

imp = imp.sort_values(
    "importance",
    ascending=False
)

print(imp)

# ============================================
# 12. SALVAR MODELO
# ============================================

joblib.dump(
    rf,
    CAMINHO_MODELO
)

joblib.dump(
    imputer,
    CAMINHO_IMPUTER
)

joblib.dump(
    SUFIXOS_RASTERS,
    CAMINHO_FEATURES
)

print(f"\nModelo salvo em:")
print(CAMINHO_MODELO)

print("\nPROCESSO CONCLUÍDO")