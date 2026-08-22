import streamlit as st
import pandas as pd
import re
import time 

# --- CONFIGURACIÓN DE FECHA ---
NUM_FECHA = 6  

st.set_page_config(page_title=f"Scouting Gran DT Avanzado - Fecha {NUM_FECHA}", layout="wide")
st.title(f"⚽ Motor de Scouting Avanzado & Armado Táctico - Fecha {NUM_FECHA}")

# --- FUNCIÓN DE ESTILIZADO (COLORES Y ENTEROS) ---
def aplicar_colores(val):
    try:
        score = float(val)
        if score < 3: return 'background-color: #FF9999'  # Rojo
        if 10 <= score <= 19: return 'background-color: #ADD8E6'  # Celeste
        if 20 <= score <= 29: return 'background-color: #90EE90'  # Verde
        if score >= 30: return 'background-color: #FFFF99'  # Amarillo
        return '' 
    except:
        return ''

def estilizar_dataframe(df):
    fecha_cols = [c for c in df.columns if c.lower().startswith('f')]
    # Aplicamos colores y forzamos el formato de número entero sin decimales en la visualización
return df.style.map(aplicar_colores, subset=fecha_cols).format({col: "{:.0f}" for col in fecha_cols if col in df.columns}, na_rep="0")

# --- FUNCIONES DE LIMPIEZA ---
def clean_google_sheet_url(url):
    if not url: return ""
    url = url.strip()
    gid_match = re.search(r'gid=(\d+)', url)
    gid = gid_match.group(1) if gid_match else "0"
    base_match = re.search(r'(https://docs\.google\.com/spreadsheets/d/e/[a-zA-Z0-9_-]+)', url)
    if base_match:
        base_url = base_match.group(1)
        timestamp = int(time.time())
        return f"{base_url}/pub?gid={gid}&single=true&output=csv&t={timestamp}"
    return url

def normalizar_nombre(nombre):
    if pd.isna(nombre): return ""
    return str(nombre).strip().upper()

# --- SIDEBAR ---
st.sidebar.header(f"📋 Configuración Táctica y Links (F{NUM_FECHA})")
esquema_elegido = st.sidebar.selectbox("Esquema Táctico:", ["4-4-2", "4-3-3", "3-5-2", "3-4-3", "5-3-2", "3-3-4"])
st.sidebar.markdown("---")
url_fixture = st.sidebar.text_input("Link Fixture:", "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh0cVFkWwvHhhrewSl31ZX7KxRv0J_zrzpoM22WuyFjqwvDyjJSf3Xt7YP1UnJ5T3JcvrEIqE0Toi4/pub?gid=0&single=true&output=csv")
url_tabla = st.sidebar.text_input("Link Tabla de Posiciones:", "https://docs.google.com/spreadsheets/d/e/2PACX-1vQxZJazI4lUl904RplZTchotOdiCGtZUOGYWIEoGCue0iAUC3RzWVZVshOYwBv-6N9Z8U98gvq4NeS1/pub?gid=0&single=true&output=csv")

urls_jugadores = {
    "ARQ": st.sidebar.text_input("Arqueros (ARQ):", "https://docs.google.com/spreadsheets/d/e/2PACX-1vQar3txoFXtWCNwPoWL_2_z7ehHwxJmgFWEIIKoILxig9a7z8i3RxmbjLt8ioO_0PA5hbu_hIRHW-VW/pubhtml#gid=20"),
    "DEF": st.sidebar.text_input("Defensores (DEF):", "https://docs.google.com/spreadsheets/d/e/2PACX-1vQar3txoFXtWCNwPoWL_2_z7ehHwxJmgFWEIIKoILxig9a7z8i3RxmbjLt8ioO_0PA5hbu_hIRHW-VW/pubhtml#gid=19"),
    "VOL": st.sidebar.text_input("Volantes (VOL):", "https://docs.google.com/spreadsheets/d/e/2PACX-1vQar3txoFXtWCNwPoWL_2_z7ehHwxJmgFWEIIKoILxig9a7z8i3RxmbjLt8ioO_0PA5hbu_hIRHW-VW/pubhtml#gid=18"),
    "DEL": st.sidebar.text_input("Delanteros (DEL):", "https://docs.google.com/spreadsheets/d/e/2PACX-1vQar3txoFXtWCNwPoWL_2_z7ehHwxJmgFWEIIKoILxig9a7z8i3RxmbjLt8ioO_0PA5hbu_hIRHW-VW/pubhtml#gid=17")
}

def load_data(url):
    csv_url = clean_google_sheet_url(url)
    if not csv_url: return None
    try:
        df_raw = pd.read_csv(csv_url, header=None, dtype=str, on_bad_lines='skip')
        header_idx = None
        for idx, row in df_raw.iterrows():
            row_str = row.astype(str).str.lower().values
            if any('jugador' in val for val in row_str if pd.notna(val)):
                header_idx = idx
                break
        if header_idx is not None:
            df = pd.DataFrame(df_raw.values[header_idx+1:], columns=df_raw.iloc[header_idx])
        else:
            df = df_raw
        df.columns = [str(c).strip() if pd.notna(c) else f"Col_{i}" for i, c in enumerate(df.columns)]
        df = df.loc[:, ~df.columns.str.contains('^Unnamed|^nan|^Col_', na=False, case=False)]
        return df
    except Exception: return None

def procesar_fixture(url):
    csv_url = clean_google_sheet_url(url)
    try:
        df = pd.read_csv(csv_url, header=None, dtype=str, on_bad_lines='skip')
    except: return pd.DataFrame(columns=['Equipo', 'Rival'])
    mapping_list = []
    for _, row in df.iterrows():
        vals = [str(v).strip() for v in row.values if pd.notna(v) and str(v).strip() != '']
        if len(vals) >= 2:
            mapping_list.append({'Equipo': vals[0], 'Rival': vals[1]})
            mapping_list.append({'Equipo': vals[1], 'Rival': vals[0]})
    return pd.DataFrame(mapping_list)

def procesar_tabla_posiciones(url):
    csv_url = clean_google_sheet_url(url)
    try:
        df_raw = pd.read_csv(csv_url, header=None, dtype=str, on_bad_lines='skip')
    except: return pd.DataFrame(columns=['Equipo', 'Pts', 'GF', 'GC'])
    res_data = []
    col_eq = col_pts = -1
    for idx, row in df_raw.iterrows():
        row_str = [str(x).strip().upper() for x in row.values]
        row_orig = [str(x).strip() for x in row.values]
        if any('EQUIPO' in val or 'CLUB' in val for val in row_str):
            for i, val in enumerate(row_str):
                if 'EQUIPO' in val or 'CLUB' in val: col_eq = i
                elif 'PTS' in val or 'PUNTOS' in val: col_pts = i
            continue
        if col_eq != -1 and col_eq < len(row_orig):
            eq_name = row_orig[col_eq]
            if not eq_name or eq_name.upper() in ['NAN', 'NONE', '']: continue
            pts_val = 0
            if col_pts != -1 and col_pts < len(row_orig):
                try: pts_val = int(''.join(filter(str.isdigit, row_orig[col_pts])))
                except: pts_val = 0
            res_data.append({'Equipo': eq_name, 'Pts': pts_val})
    return pd.DataFrame(res_data)

def procesar_jugadores(url, pos):
    df = load_data(url)
    if df is None or df.empty: return pd.DataFrame()
    col_j = next((c for c in df.columns if 'jugador' in c.lower()), df.columns[0])
    col_e = next((c for c in df.columns if 'equipo' in c.lower() or 'club' in c.lower()), df.columns[1])
    res = pd.DataFrame({'Jugador': df[col_j], 'Equipo': df[col_e], 'Pos': pos})
    for col in df.columns:
        if col.lower().startswith('f'):
            # Convertimos a número, rellenamos con 0 y forzamos a entero (int)
            res[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0).astype(int)
    return res

if st.button("🚀 Procesar Datos y Actualizar Scouting"):
    df_fix = procesar_fixture(url_fixture)
    df_tab = procesar_tabla_posiciones(url_tabla)
    lista_jugadores = []
    for pos, url in urls_jugadores.items():
        if url.strip():
            df_p = procesar_jugadores(url, pos)
            if not df_p.empty: lista_jugadores.append(df_p)
    df_full = pd.concat(lista_jugadores, ignore_index=True)
    df_full['Equipo_key'] = df_full['Equipo'].apply(normalizar_nombre)
    df_fix['Equipo_key'] = df_fix['Equipo'].apply(normalizar_nombre)
    df_full = df_full.merge(df_fix[['Equipo_key', 'Rival']], on='Equipo_key', how='left').fillna('Libre')
    st.session_state['df_full'] = df_full
    st.success("¡Datos actualizados!")

if 'df_full' in st.session_state:
    df_full = st.session_state['df_full']
    tabs = st.tabs([f"👕 Armado Táctico", "🧤 ARQ", "🛡️ DEF", "👟 VOL", "⚽ DEL", "📊 Ranking General"])
    
    with tabs[0]: # Armado Táctico
        st.dataframe(estilizar_dataframe(df_full.head(15)), use_container_width=True)

    posiciones = ["ARQ", "DEF", "VOL", "DEL"]
    for i, pos in enumerate(posiciones):
        with tabs[i+1]:
            st.dataframe(estilizar_dataframe(df_full[df_full['Pos'] == pos]), use_container_width=True)

    with tabs[5]: # Ranking
        st.dataframe(estilizar_dataframe(df_full), use_container_width=True)
