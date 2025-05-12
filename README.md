# Desafio Zetta - Dashboard de Desmatamento

Este projeto consiste em um dashboard desenvolvido com Dash para visualização de dados de desmatamento no estado do Pará e indicadores socioeconômicos.

## Pré-requisitos

- Python 3.7 ou superior
- pip

## Instalação

1. Clone este repositório:

   ```bash
   git clone <URL do repositório>
   cd desafio-zetta
   ```

2. Crie e ative um ambiente virtual:

   ```bash
   python -m venv venv

   # No Windows
   venv\Scripts\activate

   # No Linux/Mac
   source venv/bin/activate
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

## Estrutura do projeto

```
├── app_dash.py           # Aplicação principal do Dash
├── data/                 # Dados usados no dashboard
│   └── silver/
│       └── municipios_analise.csv
├── referencias.md        # Referências utilizadas
├── README.md             # Documentação do projeto
└── requirements.txt      # Dependências do Python
```

## Como executar

Execute o script principal:

```bash
python app_dash.py
```

Em seguida, abra seu navegador em `http://127.0.0.1:8050/` para visualizar o dashboard.

## Relatório

O relatório foi gerado com o Quarto Markdown e pode ser encontrado em `relatorio/relatorio_preliminar.qmd` ou em sua versão compilada em `relatorio/relatorio_preliminar.pdf`.

## Referências

INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA. Malhas territoriais: limites municipais filtrados por estado. Disponível em: https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/15774-malhas.html. Acesso em: 08 mai. 2025.

INSTITUTO NACIONAL DE PESQUISAS ESPACIAIS. TerraBrasilis: Yearly deforestation increments – Shapefile (since 2008). Dados do PRODES. Disponível em: https://terrabrasilis.dpi.inpe.br/en/download-files/. Acesso em: 08 mai. 2025.

SOCIAL PROGRESS IMPERATIVE. IPS Brasil: dados de municípios. Disponível em: https://ipsbrasil.org.br/pt/explore/dados. Acesso em: 08 mai. 2025.
