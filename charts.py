# charts.py
import plotly.express as px
import plotly.graph_objects as go
from config import COLOR_MAP_REARME, COLOR_MAP_TIPOLOGIA

def aplicar_estilo_padrao(fig, altura=380):
    fig.update_layout(
        height=altura,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=12),
        margin=dict(t=30, b=30, l=10, r=10),
        hoverlabel=dict(font_size=13)
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.15)")
    fig.update_yaxes(showgrid=False)
    return fig

def criar_grafico_tipologia(df):
    counts = df['Tipo_Evento'].value_counts().reset_index()
    counts.columns = ['Tipologia', 'Total']
    fig = px.bar(
        counts, x='Total', y='Tipologia', orientation='h', text='Total',
        color='Tipologia', color_discrete_map=COLOR_MAP_TIPOLOGIA
    )
    fig.update_layout(showlegend=False, yaxis={'categoryorder': 'total ascending'})
    fig.update_traces(textposition='outside')
    return aplicar_estilo_padrao(fig, 340)

def criar_grafico_geografia(df):
    counts = df['Country'].value_counts().reset_index()
    counts.columns = ['País', 'Total']
    fig = px.bar(
        counts, x='País', y='Total', text='Total',
        color='País', color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig.update_layout(showlegend=False)
    fig.update_traces(textposition='outside')
    return aplicar_estilo_padrao(fig, 340)

def criar_grafico_subsistemas(df):
    df_avarias = df[df['Tipo_Evento'] == 'Avaria / Alarme Operacional']
    counts = df_avarias['Categoria_Tecnica'].value_counts().reset_index()
    counts.columns = ['Subsistema', 'Total']
    fig = px.bar(
        counts, x='Total', y='Subsistema', orientation='h', text='Total',
        color='Total', color_continuous_scale='Blues'
    )
    fig.update_layout(coloraxis_showscale=False, yaxis={'categoryorder': 'total ascending'})
    fig.update_traces(textposition='outside')
    return aplicar_estilo_padrao(fig, 380)

def criar_grafico_rearme(df):
    df_avarias = df[df['Tipo_Evento'] == 'Avaria / Alarme Operacional']
    if df_avarias.empty:
        return go.Figure()
    counts = df_avarias['Intervencao_Operacional'].value_counts().reset_index()
    counts.columns = ['Intervencao', 'Total']
    fig = px.pie(
        counts, names='Intervencao', values='Total', hole=0.5,
        color='Intervencao', color_discrete_map=COLOR_MAP_REARME
    )
    fig.update_traces(textinfo='percent+value', textposition='outside')
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5)
    )
    return aplicar_estilo_padrao(fig, 420)

def criar_graficos_downtime_e_turnos(df):
    dt_tipo = df.groupby('Tipo_Evento')['Downtime_Horas_Calculo'].sum().reset_index()
    fig_dt = px.bar(
        dt_tipo, x='Tipo_Evento', y='Downtime_Horas_Calculo', text_auto='.1f',
        color='Tipo_Evento', color_discrete_map=COLOR_MAP_TIPOLOGIA,
        labels={'Downtime_Horas_Calculo': 'Horas Acumuladas', 'Tipo_Evento': ''}
    )
    fig_dt.update_layout(showlegend=False)
    fig_dt.update_traces(textposition='outside')

    df_horas = df.dropna(subset=['Hora_Evento']).copy()
    turnos = df_horas.groupby('Hora_Evento').size().reset_index(name='Ocorrências')
    fig_turnos = px.area(
        turnos, x='Hora_Evento', y='Ocorrências', markers=True,
        labels={'Hora_Evento': 'Hora do Dia (00h - 23h)'}
    )
    fig_turnos.update_traces(line_color='#3B82F6', fillcolor='rgba(59, 130, 246, 0.2)')
    fig_turnos.update_xaxes(dtick=2)
    return aplicar_estilo_padrao(fig_dt, 350), aplicar_estilo_padrao(fig_turnos, 350)

def criar_grafico_incidentes_por_parque(df, top_n=12, metrica='Número de Incidentes'):
    if df.empty or 'Site' not in df.columns:
        return go.Figure()

    agregado = df.groupby(['Site', 'Country']).agg(
        Total_Incidentes=('Site', 'count'),
        Total_Downtime=('Downtime_Horas_Calculo', 'sum'),
        Total_Perdas_MWh=('Perdas_MWh', 'sum')
    ).reset_index()

    if metrica == 'Downtime (Horas)':
        col_valor, rotulo_x, fmt = 'Total_Downtime', 'Downtime Acumulado (h)', '%{x:.1f}h'
    elif metrica == 'Perdas Estimadas (MWh)':
        col_valor, rotulo_x, fmt = 'Total_Perdas_MWh', 'Energia Não Produzida (MWh)', '%{x:.1f} MWh'
    else:
        col_valor, rotulo_x, fmt = 'Total_Incidentes', 'Número de Ocorrências', '%{x}'

    top_df = agregado.sort_values(by=col_valor, ascending=False).head(top_n)
    fig = px.bar(
        top_df, x=col_valor, y='Site', orientation='h', color='Country',
        text=col_valor, custom_data=['Country'],
        labels={col_valor: rotulo_x, 'Site': '', 'Country': 'País'},
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5)
    )
    fig.update_traces(texttemplate=fmt, textposition='outside')
    return aplicar_estilo_padrao(fig, 440)