# -*- coding: utf-8 -*-
"""
Treinamento Random Forest com múltiplas datas (8 índices).
Correção: amostragem com retorno booleano.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.impute import SimpleImputer
import joblib
import os
from qgis.core import (
    QgsProject, QgsCoordinateTransform, QgsField
)
from PyQt5.QtCore import QVariant
from sklearn.inspection import permutation_importance

# ============================================
# CONFIGURAÇÕES
# ============================================
PREFIXO_PONTOS = "P_227073_"
CAMPO_ALVO = "valid"

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

CAMINHO_MODELO = os.path.join(DIR_PROJETO, "rf_model_queimadas.pkl")
CAMINHO_IMPUTER = os.path.join(DIR_PROJETO, "imputer.pkl")
CAMINHO_FEATURES = os.path.join(DIR_PROJETO, "features.pkl")

# ============================================
# 1. Detectar camadas de pontos
# ============================================
projeto = QgsProject.instance()
camadas_pontos = [l for l in projeto.mapLayers().values() 
                  if l.type() == 0 and l.name().startswith(PREFIXO_PONTOS)]
if not camadas_pontos:
    raise Exception(f"Nenhuma camada com prefixo '{PREFIXO_PONTOS}' encontrada.")

print(f"Camadas de pontos: {[l.name() for l in camadas_pontos]}")

# ============================================
# 2. Coletar dados de todas as datas (com correção)
# ============================================
todos_dados = []
todos_alvos = []

for layer_pontos in camadas_pontos:
    nome = layer_pontos.name()
    data = nome.replace(PREFIXO_PONTOS, "")
    if not data.isdigit():
        print(f"Ignorando {nome}: data não numérica")
        continue
    
    # Carregar rasters desta data
    rasters = []
    for suf in SUFIXOS_RASTERS:
        nome_raster = f"227_073_{data}_{suf}"
        r = projeto.mapLayersByName(nome_raster)
        if not r:
            print(f"Data {data}: raster faltando - {nome_raster}")
            break
        rasters.append(r[0])
    else:
        print(f"\nProcessando {data}...")
        crs_raster = rasters[0].crs()
        crs_pontos = layer_pontos.crs()
        
        if crs_pontos != crs_raster:
            transform = QgsCoordinateTransform(crs_pontos, crs_raster, QgsProject.instance())
            usar_transform = True
            print(f"  CRS: pontos {crs_pontos.authid()} -> raster {crs_raster.authid()}")
        else:
            usar_transform = False
        
        pontos_validos = 0
        for feat in layer_pontos.getFeatures():
            try:
                alvo = int(feat[CAMPO_ALVO])
            except:
                continue
            if alvo not in (0,1):
                continue
            
            geom = feat.geometry()
            if usar_transform:
                geom.transform(transform)
            ponto = geom.asPoint()
            
            valores = []
            ok = True
            for raster in rasters:
                value, sample_ok = raster.dataProvider().sample(ponto, 1)
                if not sample_ok or value is None:
                    ok = False
                    break
                valores.append(value)
            if ok:
                todos_dados.append(valores)
                todos_alvos.append(alvo)
                pontos_validos += 1
        print(f"  Pontos válidos: {pontos_validos}")

if len(todos_dados) < 10:
    raise Exception(f"Apenas {len(todos_dados)} pontos válidos. Mínimo 10.")

# ============================================
# 3. Treinamento
# ============================================
df = pd.DataFrame(todos_dados, columns=SUFIXOS_RASTERS)
df['target'] = todos_alvos


print("\n=== CORRELAÇÃO ENTRE ÍNDICES ===")
corr = df[SUFIXOS_RASTERS].corr()
print(corr.round(2))

print("\n=== TOTAL DE PONTOS ===")
print(df['target'].value_counts())

X = df[SUFIXOS_RASTERS]
y = df['target']

imputer = SimpleImputer(strategy='mean')
X_imputed = imputer.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(
    X_imputed, y, test_size=0.3, random_state=42, stratify=y
)

rf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1, class_weight='balanced')
rf.fit(X_train, y_train)

print("\n=== VALIDAÇÃO CRUZADA (5-fold) ===")
cv_scores = cross_val_score(rf, X_imputed, y, cv=5)
print(f"Acurácia média: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

print("\n=== AVALIAÇÃO NO TESTE ===")
y_pred = rf.predict(X_test)
print(f"Acurácia: {accuracy_score(y_test, y_pred):.3f}")
print(classification_report(y_test, y_pred, target_names=["Não queimada", "Queimada"]))

print("\n=== PERMUTATION IMPORTANCE ===")

perm = permutation_importance(
    rf,
    X_test,
    y_test,
    n_repeats=30,
    random_state=42,
    n_jobs=-1,
    scoring='f1'
)

perm_df = pd.DataFrame({
    'feature': SUFIXOS_RASTERS,
    'importance_mean': perm.importances_mean,
    'importance_std': perm.importances_std
}).sort_values('importance_mean', ascending=False)

print(perm_df)

print("\n=== IMPORTÂNCIA DAS FEATURES ===")
imp = pd.DataFrame({'feature': SUFIXOS_RASTERS, 'importance': rf.feature_importances_}).sort_values('importance', ascending=False)
print(imp)

# Salvar
joblib.dump(rf, CAMINHO_MODELO)
joblib.dump(imputer, CAMINHO_IMPUTER)
joblib.dump(SUFIXOS_RASTERS, CAMINHO_FEATURES)

print(f"\nModelo salvo em: {CAMINHO_MODELO}")
print("PROCESSO CONCLUÍDO")