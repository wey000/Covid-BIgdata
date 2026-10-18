
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# Configuración de página
st.set_page_config(
    page_title="Dashboard COVID-19 Antioquia",
    page_icon="🦠",
    layout="wide"
)

# Título e Identidad Visual (UX/UI)
st.title(" Tablero de Control de Inteligencia de Negocios - COVID-19 Antioquia")
st.markdown("### Análisis estratégico de datos epidemiológicos del departamento de Antioquia")
st.markdown("---")

# Carga de datos
@st.cache_data
def cargar_datos():
    url = "https://www.datos.gov.co/resource/gt2j-8ykr.csv?$limit=100000&departamento_nom=ANTIOQUIA"
    df = pd.read_csv(url)

    # Normalización básica
    df['ciudad_municipio_nom'] = df['ciudad_municipio_nom'].astype(str).str.strip().str.upper()
    df['sexo'] = df['sexo'].astype(str).str.strip().str.upper().replace({'MALE': 'M', 'FEMALE': 'F'})
    df['estado'] = df['estado'].astype(str).str.strip().str.upper()

    # Fechas
    cols_fecha = [c for c in df.columns if 'fecha' in c.lower()]
    for col in cols_fecha:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    # Columna calculada de días hasta diagnóstico
    if 'fecha_diagnostico' in df.columns and 'fecha_de_inicio_de_sintomas' in df.columns:
        df['dias_hasta_diagnostico'] = (df['fecha_diagnostico'] - df['fecha_de_inicio_de_sintomas']).dt.days
        df['dias_hasta_diagnostico'] = df['dias_hasta_diagnostico'].clip(lower=0)
    else:
        df['dias_hasta_diagnostico'] = 0

    return df

df_raw = cargar_datos()

# ==========================================
# BARRA LATERAL - FILTROS INTERACTIVOS
# ==========================================
st.sidebar.header("Filtros de Selección")

# Filtro Municipio
municipios = ["TODOS"] + sorted(list(df_raw['ciudad_municipio_nom'].unique()))
mun_sel = st.sidebar.selectbox("Seleccione Municipio:", municipios)

# Filtro Sexo
sexos = ["TODOS"] + sorted(list(df_raw['sexo'].unique()))
sexo_sel = st.sidebar.selectbox("Seleccione Sexo:", sexos)

# Filtro Estado

estados = ["TODOS"] + sorted(list(df_raw['estado'].dropna().astype(str).unique()))
estado_sel = st.sidebar.selectbox("Seleccione Estado/Atención:", estados)

# Aplicación de Filtros
df_filtrado = df_raw.copy()

if mun_sel != "TODOS":
    df_filtrado = df_filtrado[df_filtrado['ciudad_municipio_nom'] == mun_sel]

if sexo_sel != "TODOS":
    df_filtrado = df_filtrado[df_filtrado['sexo'] == sexo_sel]

if estado_sel != "TODOS":
    df_filtrado = df_filtrado[df_filtrado['estado'] == estado_sel]

# ==========================================
# 1. TARJETAS DE KPIS / MÉTRICAS
# ==========================================
total_casos = len(df_filtrado)
fallecidos = len(df_filtrado[df_filtrado['estado'].str.contains('FALLECIDO|MUERTO', na=False)])
recuperados = len(df_filtrado[df_filtrado['recuperado'].str.contains('RECUPERADO', na=False)])
tasa_letalidad = (fallecidos / total_casos * 100) if total_casos > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Casos", f"{total_casos:,}")
col2.metric("Recuperados", f"{recuperados:,}")
col3.metric("Fallecidos", f"{fallecidos:,}")
col4.metric("Tasa de Letalidad", f"{tasa_letalidad:.2f}%")

st.markdown("---")

# ==========================================
# 2. VISUALIZACIONES PRINCIPALES
# ==========================================
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("1. Casos por Municipio (Top 10)")
    top_mun = df_filtrado['ciudad_municipio_nom'].value_counts().head(10).reset_index()
    top_mun.columns = ['Municipio', 'Casos']
    fig_bar = px.bar(top_mun, x='Casos', y='Municipio', orientation='h',
                     color='Casos', color_continuous_scale='Reds',
                     title="Top 10 Municipios Afectados")
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_bar, use_container_width=True)

with row1_col2:
    st.subheader("2. Distribución Porcentual por Sexo")
    df_sexo = df_filtrado['sexo'].value_counts().reset_index()
    df_sexo.columns = ['Sexo', 'Cantidad']
    fig_pie = px.pie(df_sexo, values='Cantidad', names='Sexo', hole=0.4,
                     title="Proporción por Sexo",
                     color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_pie, use_container_width=True)

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("3. Relación Edad vs. Días para Diagnóstico")
    fig_scatter = px.scatter(df_filtrado.dropna(subset=['edad', 'dias_hasta_diagnostico']),
                             x='edad', y='dias_hasta_diagnostico',
                             color='sexo', opacity=0.6,
                             title="Dispersión: Edad vs. Días hasta el Diagnóstico",
                             labels={'edad': 'Edad del Paciente', 'dias_hasta_diagnostico': 'Días hasta Diagnóstico'})
    st.plotly_chart(fig_scatter, use_container_width=True)
# 6. Fila 2 de Gráficos: Línea de Tiempo y Dispersión
col_g3, col_g4 = st.columns(2)

with col_g3:
    st.subheader("📈 Evolución Temporal de Contagios")
    if 'fecha_reporte_web' in df_filtrado.columns:
        df_temp = df_filtrado.dropna(subset=['fecha_reporte_web'])
        df_tiempo = df_temp.set_index('fecha_reporte_web').resample('ME').size().reset_index(name='Casos')
        fig_line = px.line(df_tiempo, x='fecha_reporte_web', y='Casos', 
                           title="Casos Diagnosticados por Mes",
                           markers=True, line_shape='spline')
        st.plotly_chart(fig_line, use_container_width=True)

with col_g4:
    st.subheader("🔍 Edad vs. Días Hasta Diagnóstico")
    if 'dias_hasta_diagnostico' in df_filtrado.columns:
        fig_scatter = px.scatter(df_filtrado.dropna(subset=['edad', 'dias_hasta_diagnostico']), 
                                 x='edad', y='dias_hasta_diagnostico', 
                                 color='sexo', opacity=0.6,
                                 title="Relación Edad y Tiempo de Diagnóstico (Días)")
        st.plotly_chart(fig_scatter, use_container_width=True)
# ==========================================
# 5. MAPA GEOGRÁFICO DE ANTIOQUIA
# ==========================================
# 7. Fila 3: Mapa Geográfico
st.subheader("🗺️ Distribución Geográfica en Municipios de Antioquia")

# Agrupar datos por municipio
map_data = df_filtrado.groupby(['ciudad_municipio_nom', 'lat', 'lon']).size().reset_index(name='Casos')

# Asegurar que las coordenadas sean numéricas
map_data['lat'] = pd.to_numeric(map_data['lat'], errors='coerce')
map_data['lon'] = pd.to_numeric(map_data['lon'], errors='coerce')

# Filtrar solo registros con coordenadas válidas y casos > 0
map_data = map_data.dropna(subset=['lat', 'lon'])
map_data = map_data[map_data['Casos'] > 0]

if not map_data.empty:
    fig_map = px.scatter_map(
        map_data, 
        lat="lat", 
        lon="lon", 
        size="Casos", 
        color="Casos",
        hover_name="ciudad_municipio_nom", 
        size_max=35, 
        zoom=6.5,
        map_style="open-street-map",
        title="Concentración de Casos por Municipio"
    )
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.info("No hay datos geográficos disponibles para los filtros seleccionados.")
