# data_processor.py
import datetime
import io
import pandas as pd
import numpy as np
from config import (
    KEYWORDS_PRECOS_NEGATIVOS, KEYWORDS_LIMITACAO_REDE, FAULT_SUBSYSTEMS_MAP,
    CUT_IN_SPEED, RATED_SPEED, CUT_OUT_SPEED, MAX_DOWNTIME_HOURS_THRESHOLD
)

def converter_data_excel(val):
    if pd.isna(val):
        return pd.NaT
    if isinstance(val, (int, float)):
        return pd.to_datetime(val, unit='D', origin='1899-12-30') if val > 30000 else pd.NaT
    txt = str(val).strip()
    try:
        num = float(txt)
        return pd.to_datetime(num, unit='D', origin='1899-12-30') if num > 30000 else pd.NaT
    except ValueError:
        pass
    return pd.to_datetime(val, errors='coerce', dayfirst=True)

def extrair_horas_duration(val):
    if pd.isna(val):
        return None
    if isinstance(val, (pd.Timedelta, datetime.timedelta)):
        horas = val.total_seconds() / 3600.0
        return horas if 0 <= horas <= MAX_DOWNTIME_HOURS_THRESHOLD else None
    txt_val = str(val).strip()
    if txt_val in ['', '-', 'nan', 'None', '?#VALOR!', '#VALUE!', '#VALOR!']:
        return None
    if isinstance(val, datetime.time):
        return val.hour + (val.minute / 60.0) + (val.second / 3600.0)
    if isinstance(val, str) and ('day' in txt_val or ':' in txt_val):
        try:
            td = pd.to_timedelta(txt_val)
            horas = td.total_seconds() / 3600.0
            return horas if 0 <= horas <= MAX_DOWNTIME_HOURS_THRESHOLD else None
        except Exception:
            pass
    try:
        val_num = float(txt_val.replace(',', '.'))
        return val_num * 24.0 if val_num <= 1.0 else val_num
    except Exception:
        return None

def parse_wind_speed(val):
    if pd.isna(val):
        return np.nan
    s = str(val).strip().replace(',', '.')
    try:
        v = float(s)
        return v if 0 <= v <= 50 else np.nan
    except ValueError:
        return np.nan

def calcular_fator_potencia(v):
    """Retorna o fator de carga (0.0 a 1.0) segundo a curva de potência cúbica."""
    if pd.isna(v) or v < CUT_IN_SPEED or v > CUT_OUT_SPEED:
        return 0.0
    if v >= RATED_SPEED:
        return 1.0
    return ((v - CUT_IN_SPEED) / (RATED_SPEED - CUT_IN_SPEED)) ** 3

def categorizar_tipo_evento(row):
    info = str(row.get('Additional Info', '')).lower()
    comments = str(row.get('Comments', '')).lower()
    desc = str(row.get('Error Description', '')).lower()
    txt = f"{info} {comments} {desc}"

    if any(k in txt for k in KEYWORDS_PRECOS_NEGATIVOS):
        return 'Preços Negativos'
    elif 'acoustic' in txt:
        return 'Ensaio Acústico'
    elif any(k in txt for k in KEYWORDS_LIMITACAO_REDE):
        return 'Limitação de Rede / TSO'
    return 'Avaria / Alarme Operacional'

def categorizar_falha_tecnica(row):
    txt = f"{row.get('Error Code', '')} {row.get('Error Description', '')} {row.get('Additional Info', '')}".lower()
    for subsistema, keywords in FAULT_SUBSYSTEMS_MAP.items():
        if any(k in txt for k in keywords):
            return subsistema
    return 'Outros / Não Categorizado'

def processar_intervencao_operacional(row):
    if row.get('Tipo_Evento') != 'Avaria / Alarme Operacional':
        return 'N/A (Operação Programada / Rede)'

    comments = str(row.get('Comments', '')).strip().lower()
    resolution = str(row.get('Resolution', '')).strip().lower()
    perm = str(row.get('Rearm Permission', '')).strip().lower()
    cond = str(row.get('Reset Conditions', '')).strip().lower()
    desc = str(row.get('Error Description', '')).lower()
    info = str(row.get('Additional Info', '')).lower()
    contexto_geral = f"{comments} {desc} {info}"

    termos_falha = [
        'falhou', 'falhado', 'ñ funcionou', 'não funcionou', 'nao funcionou',
        'failed', 'sem sucesso', 'sem  sucesso', 'not work', 'unsuccessful',
        'não limpou', 'nao limpou', 'não saiu o erro', 'voltou a parar',
        'voltou a estar faulted', 'deu erros', 'continua a aparecer'
    ]
    if any(k in comments for k in termos_falha):
        return 'Rearme Remoto Falhado (Escalado por Email)'

    termos_sucesso = [
        'remote reset', 'reset efectuado', 'reset efetuado', 'reset performed',
        'reset ok', 'rearmada', 'rearme efetuado', 'rearme efectuado',
        'rearme com sucesso', 'rearme feito', 'rearme bem sucedido',
        'rearme realizado', 'reset com sucesso', 'levou reset', 'reset feito',
        'reame feito', 'reamr efeito', 'restart com sucesso'
    ]
    termos_exclusao = [
        'do not reset', 'não rearmar', 'nao rearmar', 'não realizar o rearme',
        'não se pode rearmar', 'nao se pode rearmar', 'manual reset',
        'auto-reset', 'auto reset', 'stop das turbinas'
    ]
    eh_reset_exato = comments in ['reset', 'reset.', 'rearme', 'rearme.']
    if (eh_reset_exato or any(k in comments for k in termos_sucesso)) and not any(neg in comments for neg in termos_exclusao):
        return 'Rearme Remoto com Sucesso'

    termos_email = ['email', 'e-mail', 'mail', 'oncall', 'contactado', 'contacted', 'enviado', 'sent']
    sem_permissao = (
        perm in ['no', 'local', '-', 'não operamos', ''] or 
        cond == 'local' or 
        'without communication' in contexto_geral or 
        'sem comunicações' in contexto_geral or
        'sem comunicacao' in contexto_geral
    )
    if any(k in comments for k in termos_email):
        return 'Intervenção Local / Sem Permissão (Email Enviado)' if sem_permissao else 'Notificação / Escalamento (Email Enviado)'

    if 'running again' in resolution:
        return 'Normalizada sem Intervenção Registada'

    return 'Pendente / Sem Ação Registada'

def carregar_e_processar_dados(origem_dados):
    try:
        df = pd.read_excel(origem_dados, sheet_name='Matrix', engine='openpyxl')
    except Exception:
        df = pd.read_excel(origem_dados, sheet_name=0)

    df.columns = df.columns.str.strip()
    if 'Site' in df.columns:
        df = df[df['Site'].notna() & (df['Site'].astype(str).str.strip() != '')].copy()

    # 1. Downtime
    df['Downtime_Horas'] = df['Duration'].apply(extrair_horas_duration) if 'Duration' in df.columns else None
    
    # Forçar tipo datetime64[ns] uniforme para evitar erro de subtração
    df['Stop_DT'] = pd.to_datetime(
        df['Stop Date/Time'].apply(converter_data_excel), errors='coerce'
    ) if 'Stop Date/Time' in df.columns else pd.NaT

    df['Run_DT'] = pd.to_datetime(
        df['Run Date/Time'].apply(converter_data_excel), errors='coerce'
    ) if 'Run Date/Time' in df.columns else pd.NaT

    diff_calculada = (df['Run_DT'] - df['Stop_DT']).dt.total_seconds() / 3600.0

    # 2. Vento e Fator de Carga Unitário (MWh por cada MW instalado)
    df['Wind_Speed_Num'] = df['Wind Speed'].apply(parse_wind_speed) if 'Wind Speed' in df.columns else np.nan
    vento_medio_frota = df['Wind_Speed_Num'].median() if df['Wind_Speed_Num'].notna().any() else 6.0
    df['Wind_Speed_Estimado'] = df['Wind_Speed_Num'].fillna(vento_medio_frota)
    df['Fator_Potencia'] = df['Wind_Speed_Estimado'].apply(calcular_fator_potencia)
    df['MWh_Por_MW_Instalado'] = df['Downtime_Horas_Calculo'] * df['Fator_Potencia']

    # 3. Dimensões Temporais e Categorias
    df['Hora_Evento'] = df['Stop_DT'].dt.hour
    df['Tipo_Evento'] = df.apply(categorizar_tipo_evento, axis=1)

    avarias_mask = df['Tipo_Evento'] == 'Avaria / Alarme Operacional'
    df['Categoria_Tecnica'] = 'Não Aplicável'
    df.loc[avarias_mask, 'Categoria_Tecnica'] = df[avarias_mask].apply(categorizar_falha_tecnica, axis=1)
    df['Intervencao_Operacional'] = df.apply(processar_intervencao_operacional, axis=1)

    return df

def converter_df_para_excel(df):
    """Exporta o DataFrame tratado para bytes de ficheiro Excel."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados_Processados')
    return output.getvalue()