# app.py
import streamlit as st
from data_processor import carregar_e_processar_dados, converter_df_para_excel
import charts
from config import DEFAULT_TURBINE_MW, DEFAULT_ENERGY_PRICE

st.set_page_config(
    page_title="Control Room Operations & Fleet Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para melhorar cartões de KPI e espaçamento
st.markdown("""
<style>
    div[data-testid="metric-container"] {
        background-color: rgba(28, 131, 225, 0.06);
        border: 1px solid rgba(28, 131, 225, 0.2);
        padding: 14px 18px;
        border-radius: 10px;
    }
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(show_spinner="A processar logs operacionais...")
def obter_dados(ficheiro):
    return carregar_e_processar_dados(ficheiro)

# Cabeçalho
st.title("⚡ Control Room Operations & Fleet Analytics")
st.caption("Painel de fiabilidade operacional, eficácia de intervenção remota e impacto energético.")

# Sidebar: Carregamento e Parâmetros
st.sidebar.header("📂 Fonte de Dados")
uploaded_file = st.sidebar.file_uploader("Carregar Excel de Logs", type=["xlsx", "xls"])
origem = uploaded_file if uploaded_file else 'Operations_CC.xlsx'

try:
    df = obter_dados(origem)
except Exception as e:
    st.error(f"Erro ao ler o ficheiro: {e}")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.header("🎛️ Filtros Operacionais")

# Intervalo de Datas
datas_validas = df['Stop_DT'].dropna()
datas_recentes = datas_validas[datas_validas >= '2024-01-01']
if not datas_recentes.empty:
    min_date, max_date = datas_recentes.min().date(), datas_recentes.max().date()
    c_d1, c_d2 = st.sidebar.columns(2)
    start_date = c_d1.date_input("Data Início", value=min_date, min_value=min_date, max_value=max_date, format="DD/MM/YYYY")
    end_date = c_d2.date_input("Data Fim", value=max_date, min_value=min_date, max_value=max_date, format="DD/MM/YYYY")
    incluir_sem_data = st.sidebar.checkbox("Incluir registos sem data", value=True)
    
    d_ini, d_fim = min(start_date, end_date), max(start_date, end_date)
    mask_data = (df['Stop_DT'].dt.date >= d_ini) & (df['Stop_DT'].dt.date <= d_fim)
    if incluir_sem_data:
        mask_data = mask_data | df['Stop_DT'].isna()
else:
    mask_data = True

paises_disp = sorted(df['Country'].dropna().unique())
paises_sel = st.sidebar.multiselect("Países", options=paises_disp, default=paises_disp)

#tipos_disp = sorted(df['Tipo_Evento'].dropna().unique())
#tipos_sel = st.sidebar.multiselect("Tipologia de Evento", options=tipos_disp, default=tipos_disp)

parques_disp = sorted(df[df['Country'].isin(paises_sel)]['Site'].dropna().unique())
parques_sel = st.sidebar.multiselect("Filtrar Parques Específicos (Opcional)", options=parques_disp, default=[])

st.sidebar.markdown("---")
st.sidebar.header("⚡ Parâmetros Energéticos")
potencia_mw = st.sidebar.slider("Potência Média Turbina (MW)", 0.5, 6.0, float(DEFAULT_TURBINE_MW), 0.1)
tarifa_mwh = st.sidebar.number_input("Tarifa Média (€/MWh)", min_value=10.0, max_value=300.0, value=float(DEFAULT_ENERGY_PRICE), step=5.0)

# Aplicar Filtros
df_f = df[mask_data & (df['Country'].isin(paises_sel))].copy()
if parques_sel:
    df_f = df_f[df_f['Site'].isin(parques_sel)]

# Calcular Perdas MWh e € dinâmicas
df_f['Perdas_MWh'] = df_f['MWh_Por_MW_Instalado'] * potencia_mw
df_f['Impacto_Financeiro_EUR'] = df_f['Perdas_MWh'] * tarifa_mwh

# =============================================================
# KPI SCORECARD EXECUTIVO (5 MÉTRICAS)
# =============================================================
k1, k2, k3, k4, k5 = st.columns(5)

total_eventos = len(df_f)
df_avarias = df_f[df_f['Tipo_Evento'] == 'Avaria / Alarme Operacional']
total_avarias = len(df_avarias)
total_downtime = df_f['Downtime_Horas_Calculo'].sum()
total_mwh = df_f['Perdas_MWh'].sum()
total_eur = df_f['Impacto_Financeiro_EUR'].sum()

rearmes_sucesso = len(df_avarias[df_avarias['Intervencao_Operacional'] == 'Rearme Remoto com Sucesso'])
rearmes_tentados = len(df_avarias[df_avarias['Intervencao_Operacional'].str.contains('Rearme Remoto', na=False)])
taxa_tentativa = (rearmes_tentados / total_avarias * 100) if total_avarias > 0 else 0
taxa_eficacia = (rearmes_sucesso / rearmes_tentados * 100) if rearmes_tentados > 0 else 0

k1.metric("Total Ocorrências", f"{total_eventos:,}".replace(",", "."))
k2.metric("Avarias Operacionais", f"{total_avarias:,}".replace(",", "."))
k3.metric("Downtime Acumulado", f"{total_downtime:,.1f} h".replace(",", "."))
k4.metric("Perdas Estimadas", f"{total_mwh:,.1f} MWh".replace(",", "."), delta=f"- {total_eur:,.0f} €".replace(",", "."), delta_color="inverse")
k5.metric("Intervenção Remota", f"{taxa_tentativa:.1f}%", delta=f"{taxa_eficacia:.1f}% eficácia resets")

st.markdown("<br>", unsafe_allow_html=True)

# =============================================================
# NAVEGAÇÃO POR SEPARADORES (TABS)
# =============================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Operação & Intervenções", 
    "⚡ Ocorrências & Downtime", 
    "🏭 Criticidade por Parque", 
    "📋 Dados & Exportação"
])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Tipologia das Ocorrências")
        st.plotly_chart(charts.criar_grafico_tipologia(df_f), use_container_width=True)
    with c2:
        st.subheader("Distribuição por Geografia")
        st.plotly_chart(charts.criar_grafico_geografia(df_f), use_container_width=True)

    st.markdown("---")
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("Falhas por Subsistema Técnico")
        st.plotly_chart(charts.criar_grafico_subsistemas(df_f), use_container_width=True)
    with c4:
        st.subheader("Desfecho das Intervenções (Sala de Controlo)")
        st.plotly_chart(charts.criar_grafico_rearme(df_f), use_container_width=True)

with tab2:
    fig_dt, fig_turnos = charts.criar_graficos_downtime_e_turnos(df_f)
    c5, c6 = st.columns(2)
    with c5:
        st.subheader("Horas de Paragem por Tipologia")
        st.plotly_chart(fig_dt, use_container_width=True)
    with c6:
        st.subheader("Carga de Ocorrências por Hora (Turnos)")
        st.plotly_chart(fig_turnos, use_container_width=True)

    st.info(f"💡 **Nota de Engenharia:** O cálculo de MWh perdidos aplica uma curva de potência cúbica ($v_{{cut-in}} = 3\\text{{ m/s}}$, $v_{{rated}} = 12\\text{{ m/s}}$) sobre a velocidade de vento registada em cada ocorrência, assumindo uma potência unitária de **{potencia_mw:.1f} MW**.")

with tab3:
    st.subheader("Ranking de Ativos Críticos (Bad Actors)")
    col_cfg1, col_cfg2 = st.columns([1, 3])
    with col_cfg1:
        metrica_escolhida = st.radio(
            "Critério de Ordenação:",
            options=["Número de Incidentes", "Downtime (Horas)", "Perdas Estimadas (MWh)"]
        )
        top_n_escolhido = st.slider("Número de parques no ranking:", 5, 30, 12, 1)
    with col_cfg2:
        fig_parques = charts.criar_grafico_incidentes_por_parque(df_f, top_n=top_n_escolhido, metrica=metrica_escolhida)
        st.plotly_chart(fig_parques, use_container_width=True)

with tab4:
    st.subheader("Inspeção de Registos Tratados")
    colunas_mostrar = [
        'Stop_DT', 'Run_DT', 'Site', 'Country', 'Asset', 'Tipo_Evento',
        'Categoria_Tecnica', 'Intervencao_Operacional', 'Wind_Speed_Num',
        'Downtime_Horas_Calculo', 'Perdas_MWh', 'Comments'
    ]
    colunas_existentes = [c for c in colunas_mostrar if c in df_f.columns]
    
    st.dataframe(
        df_f[colunas_existentes].rename(columns={
            'Stop_DT': 'Início Paragem',
            'Run_DT': 'Arranque',
            'Wind_Speed_Num': 'Vento (m/s)',
            'Downtime_Horas_Calculo': 'Downtime (h)',
            'Perdas_MWh': 'Perdas (MWh)'
        }),
        use_container_width=True,
        height=420
    )

    excel_bytes = converter_df_para_excel(df_f[colunas_existentes])
    st.download_button(
        label="📥 Descarregar Relatório Processado (.xlsx)",
        data=excel_bytes,
        file_name="Relatorio_Operacoes_CC_Tratado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )