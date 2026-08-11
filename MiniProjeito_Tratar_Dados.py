import pandas as pd
import numpy as np
import csv
import re

# ==========================================================
# SPRINT 1: LEITURA NATIVA COM csv.DictReader
# ==========================================================
dados_nativos = []
with open("Base_Varejo.csv", mode="r", encoding="utf-8-sig") as arquivo:
    leitor = csv.DictReader(arquivo, delimiter=";")
    for linha in leitor:
        dados_nativos.append(linha)

# Converte os dados lidos para o DataFrame
df = pd.DataFrame(dados_nativos)

# Total de registros originais para o relatório final
total_linhas_iniciais = len(df)

print("--- INSPEÇÃO INICIAL DOS DADOS ---")
print(df.head())
print("\nInformações das colunas:")
print(df.info())
print("\nValores nulos por coluna:")
print(df.isnull().sum())

# ==========================================================
# SPRINT 2: TRATAMENTO COM REGEX
# ==========================================================
def limpar_com_regex(valor):
    if pd.isna(valor) or str(valor).strip() == "":
        return np.nan
    # Mantém apenas números, pontos e vírgulas (remove R$, espaços, etc.)
    limpo = re.sub(r"[^\d.,-]", "", str(valor))
    limpo = limpo.replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return np.nan

# Aplica regex caso exista alguma coluna de valor ou dimensão física
for col in df.columns:
    if any(termo in col.upper() for termo in ["VL", "VALOR", "PRECO", "PESO", "ALTURA"]):
        df[col] = df[col].apply(limpar_com_regex)

# Converte a coluna de filhos (CL_FHL) para número
if "CL_FHL" in df.columns:
    df["CL_FHL"] = pd.to_numeric(df["CL_FHL"], errors="coerce")

# ==========================================================
# SPRINT 3: LIMPEZA E TRATAMENTO DE DADOS (ETL + REGRAS)
# ==========================================================

# 1. Remover registros duplicados
linhas_antes_dup = len(df)
df = df.drop_duplicates()
duplicatas_removidas = lines_antes_dup = linhas_antes_dup - len(df)

# 2. Validação da Regra do Identificador de Compra (Exigência do Critério 5)
# Remove registros onde o Identificador de Compra (CO_ID) é nulo ou vazio
if "CO_ID" in df.columns:
    linhas_antes_validacao = len(df)
    # Garante que IDs vazios virem NaN e os elimina separando os válidos
    df["CO_ID"] = df["CO_ID"].replace("", np.nan)
    df = df.dropna(subset=["CO_ID"])
    compras_invalidas_removidas = linhas_antes_validacao - len(df)
else:
    compras_invalidas_removidas = 0

# 3. Tratamento de categorias vazias utilizando lógica condicional (Exigência do Critério 4)
if "PR_CAT" in df.columns:
    # Lógica estruturada para mapear e substituir categorias vazias
    df["PR_CAT"] = df["PR_CAT"].apply(lambda x: "Sem Categoria" if pd.isna(x) or str(x).strip() == "" else str(x).strip())

# 4. Conversão de datas (Requisito obrigatório)
if "DATA" in df.columns:
    df["DATA"] = pd.to_datetime(df["DATA"], errors="coerce")

# 5. Substituição de nulos numéricos pela mediana (Dimensões Físicas / Valores)
colunas_numericas = df.select_dtypes(include=[np.number]).columns
for col in colunas_numericas:
    if df[col].isnull().sum() > 0:
        mediana = df[col].median()
        df[col] = df[col].fillna(mediana)

# Exportação do dataset limpo
df.to_csv('Varejo_Limpo.csv', sep=';', index=False)
print("\nLimpeza concluída e arquivo 'Varejo_Limpo.csv' gerado!\n")

# ==========================================================
# SPRINT 4: ESTATÍSTICA DESCRITIVA (CL_FHL)
# ==========================================================
print("==================================================")
print("          ESTATÍSTICA DESCRITIVA (CL_FHL)        ")
print("==================================================")

if "CL_FHL" in df.columns:
    filhos = df["CL_FHL"].dropna()
    
    print(f"• Contagem (N) : {filhos.count()}")
    print(f"• Média        : {filhos.mean():.2f}")
    print(f"• Mediana      : {filhos.median():.2f}")
    print(f"• Desvio Padrão: {filhos.std():.2f}")
    print(f"• Moda         : {filhos.mode()[0] if not filhos.mode().empty else 'N/A'}")
    print(f"• Mínimo       : {filhos.min()}")
    print(f"• Quartil 25%  : {filhos.quantile(0.25):.2f}")
    print(f"• Quartil 50%  : {filhos.quantile(0.50):.2f}")
    print(f"• Quartil 75%  : {filhos.quantile(0.75):.2f}")
    print(f"• Máximo       : {filhos.max()}")

# ==========================================================
# SPRINT 5: AGRUPAMENTO E RELATÓRIOS
# ==========================================================
print("\n==================================================")
print("             AGRUPAMENTO POR CATEGORIA            ")
print("==================================================")

# Agrupamento 1: Total de compras e média de filhos por Categoria
if "PR_CAT" in df.columns:
    print("\n1. Volume de Compras por Categoria:")
    agrupado_categoria = df.groupby("PR_CAT").agg(
        Total_Compras=("PR_CAT", "count"),
        Media_Filhos=("CL_FHL", "mean") if "CL_FHL" in df.columns else ("PR_CAT", "count")
    ).reset_index().sort_values(by="Total_Compras", ascending=False)
    
    print(agrupado_categoria)

# Agrupamento 2: Categoria por Gênero (Pivot Table)
if "PR_CAT" in df.columns and "CL_GENERO" in df.columns:
    print("\n2. Distribuição de Compras (Categoria x Gênero):")
    tabela_cruzada = pd.pivot_table(
        df,
        index="PR_CAT",
        columns="CL_GENERO",
        values="CO_ID" if "CO_ID" in df.columns else "PR_CAT",
        aggfunc="count",
        fill_value=0
    )
    print(tabela_cruzada)

# Exporta o arquivo de estatísticas básicas
resumo = df.describe()
resumo.to_csv('estatisticas_basicas.csv', sep=';')

# Relatório Final de Contadores no Terminal
print("\n==================================================")
print("                 RELATÓRIO FINAL                  ")
print("==================================================")
print(f"Total de registros originais        : {total_linhas_iniciais}")
print(f"Linhas duplicadas removidas         : {duplicatas_removidas}")
print(f"Registros c/ IDs inválidos removidos: {compras_invalidas_removidas}")
print(f"Total de registros na base limpa    : {len(df)}")
print("==================================================")