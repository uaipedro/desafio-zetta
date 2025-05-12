# %% [markdown]
# # Análise Exploratória de Desmatamento por Município
# Integra dados de desmatamento no Pará com indicadores socioeconômicos.
#
# Etapas:
# 1. Preparação
# 2. Carregamento e inspeção inicial
# 3. Processamento geoespacial
# 4. Agregação e exportação (Bronze)
# 5. Integração socioeconômica e exportação (Silver)
# 6. Análise exploratória (Correlação e PCA)
# 7. Visualizações

# %% [markdown]
# ## 1. Preparação
# Bibliotecas essenciais e configurações de ambiente.

# %%
import geopandas as gpd
import pandas as pd
import os
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from scipy.stats import pearsonr

sns.set(style="white")
plt.rcParams["figure.figsize"] = (10, 6)

# %% [markdown]
# ## 2. Carregamento e inspeção inicial
# Carrega shapefiles e valida existência de dados.

# %%
# Definição de caminhos
caminho_desmat = "data/raw/yearly_deforestation_biome/yearly_deforestation_biome.shp"
caminho_mun = "data/raw/PA_Municipios_2024/PA_Municipios_2024.shp"

# Leitura com fallback
try:
    gdf_desmat = gpd.read_file(caminho_desmat)
    gdf_mun = gpd.read_file(caminho_mun)
except Exception as e:
    print(f"Erro ao carregar shapefiles: {e}")
    gdf_desmat, gdf_mun = gpd.GeoDataFrame(), gpd.GeoDataFrame()

# %% [markdown]
# ## 3. Processamento geoespacial
# Filtra Pará, harmoniza CRS e calcula interseções.

# %%
# Filtro apenas Pará
if 'state' in gdf_desmat.columns:
    gdf_desmat = gdf_desmat[gdf_desmat['state'] == "PA"]

# Ajuste de CRS
if not gdf_desmat.empty and not gdf_mun.empty and gdf_desmat.crs != gdf_mun.crs:
    gdf_mun = gdf_mun.to_crs(gdf_desmat.crs)

# Campos essenciais
if 'uuid' in gdf_desmat.columns:
    gdf_desmat = gdf_desmat.rename(columns={'uuid': 'id_desmat'})
gdf_desmat = gdf_desmat[['id_desmat', 'year', 'area_km', 'geometry']]
gdf_mun = gdf_mun[['CD_MUN', 'NM_MUN', 'geometry']]

# Correção de geometrias
gdf_desmat['geometry'] = gdf_desmat.geometry.buffer(0)
gdf_mun['geometry'] = gdf_mun.geometry.buffer(0)

# Interseção e cálculo de área (km²)
gdf_inter = gpd.overlay(gdf_desmat, gdf_mun, how='intersection')
gdf_inter['area_km2'] = gdf_inter.to_crs('EPSG:5880').area / 1e6

# %% [markdown]
# ## 4. Agregação e exportação (Bronze)
# Soma áreas por município e ano, gera CSV intermediário.

# %%
# Agrupar e pivotar

df_ano = (
    gdf_inter
    .groupby(['CD_MUN', 'NM_MUN', 'year'])['area_km2']
    .sum()
    .reset_index()
)
df_pivot = (
    df_ano
    .pivot_table(
        index=['CD_MUN', 'NM_MUN'],
        columns='year',
        values='area_km2',
        fill_value=0
    )
    .reset_index()
)
anos = [c for c in df_pivot.columns if str(c).isdigit()]
df_pivot['total_km2'] = df_pivot[anos].sum(axis=1)

# Exportar Bronze
os.makedirs("data/bronze", exist_ok=True)
df_pivot.to_csv("data/bronze/desmatamento_municipio_ano.csv", index=False, encoding='utf-8-sig')

# %% [markdown]
# ## 5. Integração socioeconômica e exportação (Silver)
# Une dados bronze com IPS e calcula proporção de desmatamento.

# %%
bronze = "data/bronze"
silver = "data/silver"
os.makedirs(silver, exist_ok=True)

ips = pd.read_csv(f"{bronze}/ips_brasil_municipios.csv", dtype={"Código IBGE": str})
ips = ips.rename(columns={"Código IBGE": "CD_MUN"})
desmat = pd.read_csv(f"{bronze}/desmatamento_municipio_ano.csv", dtype={"CD_MUN": str})

df = desmat.merge(ips, on="CD_MUN", how="left")
df = df.rename(columns={"Área (km²)": "area_municipio_km2"})
df["desmat_prop"] = df["total_km2"] / df["area_municipio_km2"]

df.to_csv(f"{silver}/municipios_analise.csv", index=False, encoding='utf-8-sig')

# %% [markdown]
# ## 6. Análise exploratória (Correlação e PCA)
# Normaliza variáveis, calcula matriz de correlação e aplica PCA.

# %%
cols = [
    "desmat_prop",
    "PIB per capita 2021",
    "Índice de Progresso Social",
    "Necessidades Humanas Básicas",
    "Fundamentos do Bem-estar",
    "Oportunidades"
]
data_norm = (df[cols] - df[cols].min()) / (df[cols].max() - df[cols].min())
corr = data_norm.corr()
corr.to_csv(f"{silver}/correlacoes_desmatamento_ips.csv", index=True)

# PCA para 2 componentes
pca = PCA(n_components=2)
X = StandardScaler().fit_transform(data_norm.dropna())
pca_result = pca.fit_transform(X)

# %% [markdown]
# ## 7. Visualizações
# Série temporal, heatmap de correlação e scatterplots.

# %%
# Série temporal de desmatamento
ts_df = df_ano.groupby('year')['area_km2'].sum().reset_index()
sns.lineplot(data=ts_df, x='year', y='area_km2', marker='o')
plt.title('Desmatamento Anual Total')
plt.xlabel('Ano')
plt.ylabel('Total Desmatado (km²)')
plt.tight_layout()
plt.show()

# %%
# Heatmap de correlação
sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f")
plt.title("Correlação Desmatamento x Indicadores")
plt.tight_layout()
plt.show()

# %%
# Scatterplots estáticos por indicador
for var in cols[1:]:
    sns.scatterplot(x=var, y="desmat_prop", data=df)
    r, _ = pearsonr(df[var], df["desmat_prop"])
    plt.title(f"{var} vs Desmatamento Proporcional (r={r:.2f})")
    plt.tight_layout()
    plt.show()

# %%


# %%

