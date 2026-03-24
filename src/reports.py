import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import json

from src.config import SILVER_DIR, STATS_DIR, ASSETS_DIR

def generate_silver_report():
    ASSETS_DIR.mkdir(exist_ok=True)

    print("Starting report generation...")

    try:
        orders = pd.read_parquet(SILVER_DIR / "orders.parquet")
        items = pd.read_parquet(SILVER_DIR / "order_items.parquet")
        payments = pd.read_parquet(SILVER_DIR / "order_payments.parquet")
    except Exception as e:
        print(f"Error loading silver file: {e}")
        return

    # --- 2. GERAÇÃO DE VISUALIZAÇÕES ---
    sns.set_theme(style="whitegrid")
    plt.rcParams['figure.figsize'] = (10, 6)

    # Gráfico 1: Status dos Pedidos
    orders['order_status'].value_counts().plot(kind='bar', color='steelblue')
    plt.title('Distribuição de Status dos Pedidos')
    plt.tight_layout()
    plt.savefig(ASSETS_DIR / "01_status_pedidos.png")
    plt.close()

    # Gráfico 2: Evolução Mensal de Vendas
    orders.set_index('order_purchase_timestamp').resample('M').size().plot(marker='o')
    plt.title('Volume de Vendas Mensais (Sazonalidade)')
    plt.ylabel('Qtd Pedidos')
    plt.tight_layout()
    plt.savefig(ASSETS_DIR / "02_vendas_mensais.png")
    plt.close()

    # Gráfico 3: Mix de Meios de Pagamento
    payments['payment_type'].value_counts().plot(kind='pie', autopct='%1.1f%%', startangle=140)
    plt.title('Participação por Meio de Pagamento')
    plt.ylabel('')
    plt.savefig(ASSETS_DIR / "03_meios_pagamento.png")
    plt.close()

    # Gráfico 4: Distribuição de Preços (Log Scale para lidar com outliers)
    sns.histplot(items['price'], bins=50, log_scale=True, color='green')
    plt.title('Distribuição de Preços dos Produtos (Escala Log)')
    plt.savefig(ASSETS_DIR / "04_dist_precos.png")
    plt.close()

    # Gráfico 5: Boxplot de Frete
    sns.boxplot(x=items['freight_value'], color='orange')
    plt.title('Dispersão de Valores de Frete (Outliers)')
    plt.xlim(0, 200)  # Foco na massa de dados
    plt.savefig(ASSETS_DIR / "05_boxplot_frete.png")
    plt.close()

    # --- 3. CONSTRUÇÃO DO DOCUMENTO MARKDOWN ---
    with open("silver_report.md", "w", encoding="utf-8") as f:
        f.write("# 📑 Relatório de Governança e Qualidade - Camada Silver\n\n")
        f.write("Este documento detalha a integridade técnica e os insights iniciais do dataset Olist.\n\n")

        f.write("## 🛠️ 1. Dicionário de Dados e Integridade\n")
        f.write("Abaixo, a análise de tipos e preenchimento para cada tabela processada:\n\n")

        # Itera sobre os JSONs de metadados gerados no transform.py
        for json_file in sorted(STATS_DIR.glob("*.json")):
            with open(json_file, "r") as j:
                data = json.load(j)

            tabela_nome = json_file.stem.replace('_meta', '')
            f.write(f"### 📋 Tabela: `{tabela_nome}`\n")
            f.write(f"- **Total de Linhas:** {data['rows']:,}\n")
            f.write("| Coluna | Tipo | Nulos | % Integridade |\n")
            f.write("| :--- | :--- | :--- | :--- |\n")

            for col in data['columns']:
                nulos = data['nulls'].get(col, 0)
                tipo = data['types'].get(col, 'unknown')
                integridade = ((data['rows'] - nulos) / data['rows']) * 100
                f.write(f"| `{col}` | {tipo} | {nulos:,} | {integridade:.1f}% |\n")
            f.write("\n---\n")

        f.write("\n## 📈 2. Visualizações de Negócio (Exploração Silver)\n\n")

        imgs = [
            ("Status dos Pedidos", "01_status_pedidos.png"),
            ("Sazonalidade Mensal", "02_vendas_mensais.png"),
            ("Meios de Pagamento", "03_meios_pagamento.png"),
            ("Distribuição de Preços", "04_dist_precos.png"),
            ("Análise de Frete", "05_boxplot_frete.png")
        ]

        for title, img_path in imgs:
            f.write(f"### {title}\n")
            f.write(f"![{title}](assets/{img_path})\n\n")

    print("Silver report generated.")


if __name__ == "__main__":
    generate_silver_report()