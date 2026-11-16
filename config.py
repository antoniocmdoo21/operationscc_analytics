# config.py

# =============================================================
# 1. REGRAS DE CLASSIFICAÇÃO DE EVENTOS E MERCADO
# =============================================================
KEYWORDS_PRECOS_NEGATIVOS = [
    'preço negativo', 'preços negativos', 'preco negativo', 'precos negativos',
    'negative price', 'spot negativo', 'mercado negativo', 'curtailment preço'
]

KEYWORDS_LIMITACAO_REDE = [
    'limitation', 'limitada', 'grid outage', 'setpoint', 'cortes de rede', 'curtailment'
]

# =============================================================
# 2. MAPEAMENTO DE SUBSISTEMAS TÉCNICOS (AVARIAS)
# =============================================================
FAULT_SUBSYSTEMS_MAP = {
    'Comunicações e SCADA': [
        'comunica', 'communication', 'interbus', 'frozen in the scada', 
        'comms', 'fm700', 'sem comunicações', 'without communication'
    ],
    'Óleo, Hidráulica e Multiplicadora': [
        'oil', 'gear', 'hyd', 'valve', 'piston', '3552', '4200', 'gearoillevel', 'hydlevst'
    ],
    'Sistemas Elétricos e Proteções': [
        'breaker', 'circuit', 'voltage', 'diode', 'pth', 'undervoltage', 
        'q7', 'q8', 'mainswtrip', 'main circuit breaker'
    ],
    'Sistemas Pitch / Yaw': [
        'yaw', 'pitch', '10100', 'yaw motor'
    ],
    'Disparos / Restarts': [
        'restart', 'auto-restart', '100', 'too many auto-restarts'
    ],
    'Sensores e CMS': [
        'air gap', 'acoustic sensor', 'sensor'
    ],
    'Travão Mecânico': [
        'brake', '334'
    ]
}

# =============================================================
# 3. PARÂMETROS DA CURVA DE POTÊNCIA (ESTIMATIVA DE PERDAS MWh)
# =============================================================
DEFAULT_TURBINE_MW = 2.5       # Potência nominal média da frota (MW)
DEFAULT_ENERGY_PRICE = 65.0    # Preço médio de referência (€/MWh)
CUT_IN_SPEED = 3.0             # Velocidade de arranque (m/s)
RATED_SPEED = 12.0             # Velocidade nominal (m/s)
CUT_OUT_SPEED = 25.0           # Velocidade de corte por vento forte (m/s)
MAX_DOWNTIME_HOURS_THRESHOLD = 720.0

# =============================================================
# 4. PALETAS DE CORES CONSISTENTES (PLOTLY)
# =============================================================

COLOR_MAP_REARME = {
    '1. Remote Reset Bem Sucedido': '#10B981',          # Verde Esmeralda
    '2. Remote Reset Sem Sucesso': '#EF4444',           # Vermelho Coral
    '4. Intervenção Local': '#F59E0B',                  # Âmbar / Laranja
    '3. Sem Permissão Contratual de Rearme': '#3B82F6', # Azul Elétrico
    'Outros / Auto-Reset / Sem Registo': '#6B7280'      # Cinza Neutro
}

COLOR_MAP_TIPOLOGIA = {
    'Avaria / Alarme Operacional': '#EF4444',
    'Preços Negativos': '#10B981',
    'Ensaio Acústico': '#3B82F6',
    'Limitação de Rede / TSO': '#F59E0B'
}