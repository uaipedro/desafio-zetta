import pandas as pd
import dash
from dash import html, dcc, dash_table
import plotly.express as px
import dash_bootstrap_components as dbc
import pathlib
import re
from scipy.stats import pearsonr
import plotly.graph_objects as go


BASE_PATH = pathlib.Path(__file__).parent
reference_text = (BASE_PATH / 'referencias.md').read_text(encoding='utf-8')

df = pd.read_csv('data/silver/municipios_analise.csv')
df = df[df['UF']=='PA']
df.rename(columns={'desmat_prop': 'Desmatamento Proporcional à Area'}, inplace=True)
numeric_cols = df.select_dtypes(include='number').columns.tolist()

analysis_cols = [
    "Desmatamento Proporcional à Area",
    "PIB per capita 2021",
    "Índice de Progresso Social",
    "Necessidades Humanas Básicas",
    "Fundamentos do Bem-estar",
    "Oportunidades"
]

available_vars = [c for c in analysis_cols if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
if not available_vars:
    available_vars = numeric_cols

table_cols = ['Município', 'area_total_desmatada_km2'] + available_vars

year_cols = [c for c in df.columns if re.match(r'^\d{4}\.0$', c)]
year_cols = sorted(year_cols, key=lambda x: float(x))
ts = df[year_cols].sum()
ts_df = pd.DataFrame({'Ano': [int(float(y)) for y in ts.index], 'Desmatado': ts.values})

max_list = []
for col in year_cols:
    year = int(float(col))
    total = ts[col]
    idx = df[col].idxmax()
    mun = df.loc[idx, 'Município']
    val = df.loc[idx, col]
    max_list.append({'Ano': year, 'Total Desmatado': total, 'Município que mais desmatou': f"{mun} ({val:.2f} km²)"})
year_stats_df = pd.DataFrame(max_list)

column_units = {
    'PIB per capita 2021': 'R$',
    'area_total_desmatada_km2': 'km²'
}

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LITERA], suppress_callback_exceptions=True)
app.layout = dbc.Container([
    html.H1('Desmatamento e Índices Socioeconômicos no Pará', className='text-center my-4'),
    dbc.Tabs([
        dbc.Tab(label='Dados', tab_id='tab-dados'),
        dbc.Tab(label='Dispersão', tab_id='tab-dispersao'),
        dbc.Tab(label='Correlação', tab_id='tab-correlacao'),
    ], id='tabs', active_tab='tab-dados'),
    html.Div(id='tab-content', className='mt-4')
], fluid=True)

@app.callback(
    dash.dependencies.Output('tab-content', 'children'),
    [dash.dependencies.Input('tabs', 'active_tab')]
)
def render_tab(active_tab):
    if active_tab == 'tab-dados':
        
        tseries_card = dbc.Card([
            dbc.CardHeader('Série Temporal do Desmatamento'),
            dbc.CardBody(dcc.Graph(
                id='tseries-plot',
                figure=px.line(ts_df, x='Ano', y='Desmatado', markers=True)
                         .update_layout(
                             title='Desmatamento Anual Total',
                             xaxis_title='Ano',
                             yaxis_title='Total Desmatado (km²)'
                         )
            ))
        ], className='mb-4')
        stats_card = dbc.Card([
            dbc.CardHeader('Desmatamento Anual por Líder'),
            dbc.CardBody(dash_table.DataTable(
                id='stats-table',
                columns=[
                    {'name': 'Ano', 'id': 'Ano'},
                    {'name': 'Total Desmatado (km²)', 'id': 'Total Desmatado'},
                    {'name': 'Município que mais desmatou', 'id': 'Município que mais desmatou'}
                ],
                data=year_stats_df.to_dict('records'),
                style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                style_cell={'textAlign': 'left', 'padding': '5px'}
            ))
        ], className='mb-4')
        references_card = dbc.Card([
            dbc.CardHeader('Referências'),
            dbc.CardBody(dcc.Markdown(reference_text))
        ])
        return [
            dbc.Row([
                dbc.Col(tseries_card, width=6),
                dbc.Col(stats_card, width=6)
            ], className='mb-4'),
            dbc.Row(dbc.Col(references_card, width=12))
        ]
    elif active_tab == 'tab-dispersao':
        selection_card = dbc.Card([
            dbc.CardHeader('Seleção de Variáveis'),
            dbc.CardBody([
                dcc.Dropdown(
                    id='x-dropdown',
                    options=[{'label': c, 'value': c} for c in available_vars],
                    value=available_vars[0],
                    placeholder='Selecione a variável X',
                    className='mb-3'
                ),
                dcc.Dropdown(
                    id='y-dropdown',
                    options=[{'label': c, 'value': c} for c in available_vars],
                    value=available_vars[1] if len(available_vars)>1 else available_vars[0],
                    placeholder='Selecione a variável Y'
                )
            ])
        ], className='mb-4')
        scatter_card = dbc.Card([
            dbc.CardHeader('Gráfico de Dispersão'),
            dbc.CardBody([
                dcc.Graph(id='scatter-plot', style={'height': '600px'})
            ])
        ], className='h-100')
        
        corr_toast = dbc.Toast(
            id='corr-note',
            header='Correlação',
            is_open=True,
            dismissable=True,
            icon='info',
            style={'width': '100%', 'marginTop': '1rem'},
            className='mb-4'
        )
        
        info_card = dbc.Card([
            dbc.CardHeader('Sobre o IPS'),
            dbc.CardBody(dcc.Markdown('''
O IPS Brasil 2024 é composto por 53 indicadores secundários de fontes públicas que são exclusivamente sociais, ambientais e que medem resultados, não investimentos. Essas variáveis foram agregadas em um índice geral, com nota de 0 a 100, e índices para 3 dimensões:

- Necessidades Humanas Básicas
- Fundamentos do Bem-estar
- Oportunidades

Além disso, o PIB per capta (coletado em 2021) foi analisado para cada município.
'''))
        ], className='mb-4')

        # Série temporal de desmatamento
        tseries_card = dbc.Card([
            dbc.CardHeader('Série Temporal do Desmatamento'),
            dbc.CardBody(dcc.Graph(
                figure=px.line(ts_df, x='Ano', y='Desmatado', markers=True)
                         .update_layout(
                             title='Desmatamento Anual Total',
                             xaxis_title='Ano',
                             yaxis_title='Total Desmatado (km²)'
                         )
            ))
        ], className='mb-4')

        # Scatterplots estáticos por indicador
        static_cards = []
        for var in analysis_cols[1:]:
            fig_static = px.scatter(df, x=var, y='Desmatamento Proporcional à Area')
            r_stat, _ = pearsonr(df[var], df['Desmatamento Proporcional à Area'])
            fig_static.update_layout(
                title=f"{var} vs Desmatamento Proporcional (r={r_stat:.2f})",
                height=400
            )
            static_cards.append(
                dbc.Card([
                    dbc.CardHeader(var),
                    dbc.CardBody(dcc.Graph(figure=fig_static))
                ], className='mb-4')
            )

        # Retorna combinação de componentes
        return [
            tseries_card,
            dbc.Row([
                dbc.Col([selection_card, corr_toast, info_card], width=4),
                dbc.Col(scatter_card, width=8)
            ], className='mb-4'),
            *static_cards
        ]
    elif active_tab == 'tab-correlacao':
        
        corr_matrix = df[available_vars].corr()
        heatmap_card = dbc.Card([
            dbc.CardHeader('Mapa de Calor de Correlação'),
            dbc.CardBody(dcc.Graph(
                id='heatmap',
                figure=px.imshow(
                    corr_matrix,
                    text_auto='.2f',
                    color_continuous_scale='RdBu',
                    zmin=-1,
                    zmax=1
                ).update_traces(textfont={'size':14}).update_layout(
                    title='Correlação entre desmatamento e índices socioeconômicos',
                    height=800
                ),
                style={'height': '800px'}
            ))
        ], className='mb-4')
        
        info_card_correlacao = dbc.Card([
            dbc.CardHeader('Referências Comparativas IPS'),
            dbc.CardBody(dcc.Markdown('''
No ano de 2024, o Brasil apresentou a pontuação 68,90 no IPS Global, ocupando a 67ª posição no ranking entre 170 países. Na América do Sul, Chile (78,43), Argentina (77,19) e Equador (69,56) foram os países com as melhores pontuações. Em termos globais, Dinamarca (90,30), Noruega (90,32) e Finlândia (89,96) apresentaram o melhor desempenho no progresso social (Social Progress Imperative, 2024).
'''))
        ], className='mb-4')
        
        mean_vars = [c for c in available_vars if c not in ['PIB per capita 2021', 'Desmatamento Proporcional à Area']]
        means_df = pd.DataFrame({
            'Variável': mean_vars,
            'Média': [df[col].mean() for col in mean_vars]
        })
        
        fig_means = px.bar(
            means_df,
            x='Variável', y='Média', text_auto='.2f',
            title='Média dos Índices por Variável (Pará)'
        ).update_layout(
            xaxis_title='Variável',
            yaxis_title='Valor Médio', height=500
        )
        reference_values = {
            'Brasil': 68.90,
            'Argentina': 77.19,
            'Dinamarca': 90.30,
        }
        for country, val in reference_values.items():
            fig_means.add_hline(y=val, line_dash='dash', line_color='grey',
                                annotation_text=f"{country} ({val})",
                                annotation_position='top right')
        stats_mean_card = dbc.Card([
            dbc.CardHeader('Médias dos Índices nos Municípios do Pará'), 
            dbc.CardBody(dcc.Graph(
                id='mean-indices-plot',
                figure=fig_means
            ))
        ], className='mb-4')
        
        return dbc.Row([
            dbc.Col([info_card_correlacao, stats_mean_card], width=4),
            dbc.Col(heatmap_card, width=8)
        ], className='mb-4')
    return html.P('Selecione uma aba.')

@app.callback(
    [dash.dependencies.Output('scatter-plot', 'figure'),
     dash.dependencies.Output('corr-note', 'children')],
    [dash.dependencies.Input('x-dropdown', 'value'),
     dash.dependencies.Input('y-dropdown', 'value')]
)
def update_scatter(x_col, y_col):
    fig = px.scatter(df, x=x_col, y=y_col, trendline='ols')
    
    x_title = x_col
    y_title = y_col
    if x_col in column_units:
        x_title += f' ({column_units[x_col]})'
    if y_col in column_units:
        y_title += f' ({column_units[y_col]})'
    fig.update_layout(
        title=f'{y_col} vs {x_col}',
        xaxis_title=x_title,
        yaxis_title=y_title,
        height=600
    )
    
    r, p = pearsonr(df[x_col], df[y_col])
    strength = 'forte' if abs(r) >= 0.7 else 'moderada' if abs(r) >= 0.3 else 'fraca'
    direction = 'positiva' if r >= 0 else 'negativa'
    significance = 'estatisticamente significativa' if p < 0.05 else 'não estatisticamente significativa'
    note = (
        f"Coeficiente de correlação de {r:.2f} (p-valor = {p:.3f}), "
        f"sugerindo {strength} correlação {direction}, {significance} (α=0.05)."
    )
    return fig, note

if __name__ == '__main__':
    app.run(debug=False)
