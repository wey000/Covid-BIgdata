import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la página (UX/UI)
st.set_page_config(
    page_title="Dashboard COVID-19 Antioquia | BI",
    page_icon="🦠",
    layout="wide"
)

# Título y Encabezado
st.title("🦠 Tablero de Control: Inteligencia de Negocios COVID-19 Antioquia")
st.markdown("Análisis estratégico interactivo de casos positivos en el departamento de Antioquia, Colombia.")
st.markdown("---")

# 2. Carga y preparación de datos (Cache para optimizar velocidad)
@st.cache_data
def cargar_datos():
    url = "https://www.datos.gov.co/resource/gt2j-8ykr.csv?$limit=100000&departamento_nom=ANTIOQUIA"
    df = pd.read_csv(url)
    
    # Limpieza básica y conversión
    col_texto = ['ciudad_municipio_nom', 'sexo', 'estado', 'recuperado', 'fuente_tipo_contagio']
    for col in col_texto:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()
            
    df['sexo'] = df['sexo'].replace({'MALE': 'M', 'FEMALE': 'F', 'm': 'M', 'f': 'F'})
    
    cols_fecha = [c for c in df.columns if 'fecha' in c.lower()]
    for col in cols_fecha:
        df[col] = pd.to_datetime(df[col], errors='coerce')
        
    if 'fecha_diagnostico' in df.columns and 'fecha_de_inicio_de_sintomas' in df.columns:
        df['dias_hasta_diagnostico'] = (df['fecha_diagnostico'] - df['fecha_de_inicio_de_sintomas']).dt.days
        df['dias_hasta_diagnostico'] = df['dias_hasta_diagnostico'].apply(lambda x: x if x >= 0 else None)
        
    # Coordenadas aproximadas para los municipios principales de Antioquia (para el Mapa)
    coords_antioquia = {
        'MEDELLIN': (6.2442, -75.5812),
        'BELLO': (6.3373, -75.5579),
        'ITAGUI': (6.1846, -75.5991),
        'ENVIGADO': (6.1699, -75.5878),
        'RIONEGRO': (6.1552, -75.3737),
        'APARTADO': (7.8829, -76.6258),
        'TURBO': (8.0926, -76.7281),
        'SABANETA': (6.1513, -75.6163),
        'CAUCASIA': (7.9868, -75.1979),
        'CALDAS': (6.0911, -75.6357)
    }
    
    df['lat'] = df['ciudad_municipio_nom'].map(lambda x: coords_antioquia.get(x, (6.2442, -75.5812))[0])
    df['lon'] = df['ciudad_municipio_nom'].map(lambda x: coords_antioquia.get(x, (6.2442, -75.5812))[1])
    
    return df

df = cargar_datos()

# 3. Panel Lateral: Filtros Interactivos
st.sidebar.header("🎛️ Filtros Interactivos")

# Filtro por Municipio
municipios = ['TODOS'] + sorted(list(df['ciudad_municipio_nom'].dropna().unique()))
muni_sel = st.sidebar.selectbox("Seleccione Municipio:", municipios)

# Filtro por Sexo
sexos = ['TODOS'] + sorted(list(df['sexo'].dropna().unique()))
sexo_sel = st.sidebar.selectbox("Seleccione Sexo:", sexos)

# Aplicación de Filtros
df_filtrado = df.copy()
if muni_sel != 'TODOS':
    df_filtrado = df_filtrado[df_filtrado['ciudad_municipio_nom'] == muni_sel]
if sexo_sel != 'TODOS':
    df_filtrado = df_filtrado[df_filtrado['sexo'] == sexo_sel]

# 4. Sección de KPIs / Cards
st.subheader("📌 Indicadores Clave (KPIs)")
total_casos = len(df_filtrado)
recuperados = len(df_filtrado[df_filtrado['recuperado'].isin(['RECUPERADO', 'SI'])])
fallecidos = len(df_filtrado[df_filtrado['estado'].isin(['FALLECIDO', 'MUERTO'])])
tasa_letalidad = (fallecidos / total_casos * 100) if total_casos > 0 else 0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Casos", f"{total_casos:,}")
kpi2.metric("Recuperados", f"{recuperados:,}")
kpi3.metric("Fallecidos", f"{fallecidos:,}")
kpi4.metric("Tasa de Letalidad", f"{tasa_letalidad:.2f}%")

st.markdown("---")

# 5. Fila 1 de Gráficos: Barras y Torta
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.subheader("🏙️ Top 10 Municipios con Más Casos")
    top_muns = df_filtrado['ciudad_municipio_nom'].value_counts().head(10).reset_index()
    top_muns.columns = ['Municipio', 'Casos']
    fig_bar = px.bar(top_muns, x='Casos', y='Municipio', orientation='h', 
                     color='Casos', color_continuous_scale='Blues',
                     title="Casos por Municipio")
    fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_bar, use_container_width=True)

with col_g2:
    st.subheader("🍕 Distribución por Sexo")
    sexo_counts = df_filtrado['sexo'].value_counts().reset_index()
    sexo_counts.columns = ['Sexo', 'Cantidad']
    fig_pie = px.pie(sexo_counts, values='Cantidad', names='Sexo', 
                     hole=0.4, title="Proporción por Sexo",
                     color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_pie, use_container_width=True)

# 6. Fila 2 de Gráficos: Línea de Tiempo y Dispersión
col_g3, col_g4 = st.columns(2)

with col_g3:
    st.subheader("📈 Evolución Temporal de Contagios")
    if 'fecha_diagnostico' in df_filtrado.columns:
        df_time = df_filtrado.set_index('fecha_diagnostico').resample('M').size().reset_index(name='Casos')
        fig_line = px.line(df_time, x='fecha_diagnostico', y='Casos', 
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

# 7. Fila 3: Mapa Geográfico
st.subheader("🗺️ Mapa de Distribución Geográfica en Antioquia")
map_data = df_filtrado.groupby(['ciudad_municipio_nom', 'lat', 'lon']).size().reset_index(name='Casos')
fig_map = px.scatter_mapbox(map_data, lat="lat", lon="lon", size="Casos", color="Casos",
                            hover_name="ciudad_municipio_nom", size_max=40, zoom=7,
                            mapbox_style="carto-positron",
                            title="Concentración de Casos por Municipio")
st.plotly_chart(fig_map, use_container_width=True)
