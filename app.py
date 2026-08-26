import streamlit as st
import pandas as pd
import re
import time  # <-- Importante para romper la caché de Google Sheets

# --- CONFIGURACIÓN DE FECHA ---
NUM_FECHA = 6  # Cambia este número en el futuro para actualizar toda la app

st.set_page_config(page_title=f"Scouting Gran DT Avanzado - Fecha {NUM_FECHA}", layout="wide")
st.title(f"⚽ Motor de Scouting Avanzado & Armado Táctico - Fecha {NUM_FECHA}")

# --- FUNCIONES DE LIMPIEZA DE URLs Y ANTI-CACHÉ ---
def clean_google_sheet_url(url):
    if not url: return ""
    url = url.strip()
    gid_match = re.search(r'gid=(\d+)', url)
    gid = gid_match.group(1) if gid_match else "0"
    base_match = re.search(r'(https://docs\.google\.com/spreadsheets/d/e/[a-zA-Z0-9_-]+)', url)
    if base_match:
        base_url = base_match.group(1)
        # Agregamos un timestamp dinámico (&t=...) para evitar que Google devuelva datos viejos (caché)
        timestamp = int(time.time())
        return f"{base_url}/pub?gid={gid}&single=true&output=csv&t={timestamp}"
    return url

# --- NORMALIZACIÓN DE NOMBRES ---
def normalizar_nombre(nombre):
    """Convierte a mayúsculas y quita espacios extra para cruzar datos sin errores"""
    if pd.isna(nombre): return ""
    return str(nombre).strip().upper()

# --- SIDEBAR: CONFIGURACIÓN Y LINKS ---
st.sidebar.header(f"📋 Configuración Táctica y Links (F{NUM_FECHA})")
esquema_elegido = st.sidebar.selectbox("Esquema Táctico:", ["4-4-2", "4-3-3", "3-5-2", "3-4-3", "5-3-2", "3-3-4"])

st.sidebar.markdown("---")
st.sidebar.markdown("**Links de Google Sheets:**")

url_fixture = st.sidebar.text_input(
    "Link Fixture:", 
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh0cVFkWwvHhhrewSl31ZX7KxRv0J_zrzpoM22WuyFjqwvDyjJSf3Xt7YP1UnJ5T3JcvrEIqE0Toi4/pub?gid=0&single=true&output=csv"
)
url_tabla = st.sidebar.text_input(
    "Link Tabla de Posiciones:", 
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQxZJazI4lUl904RplZTchotOdiCGtZUOGYWIEoGCue0iAUC3RzWVZVshOYwBv-6N9Z8U98gvq4NeS1/pub?gid=0&single=true&output=csv"
)

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
    except Exception as e:
        return None

def procesar_fixture(url):
    csv_url = clean_google_sheet_url(url)
    try:
        df = pd.read_csv(csv_url, header=None, dtype=str, on_bad_lines='skip')
    except Exception:
        return pd.DataFrame(columns=['Equipo', 'Rival_Nombre', 'Condicion'])

    mapping_list = []
    for _, row in df.iterrows():
        vals = [str(v).strip() for v in row.values if pd.notna(v) and str(v).strip() != '']
        if len(vals) >= 2:
            eq_local = vals[0]
            eq_visita = vals[1]
            
            # Para el equipo local, el rival es el visitante (V)
            mapping_list.append({'Equipo': eq_local, 'Rival_Nombre': eq_visita, 'Condicion': 'V'})
            # Para el equipo visitante, el rival es el local (L)
            mapping_list.append({'Equipo': eq_visita, 'Rival_Nombre': eq_local, 'Condicion': 'L'})
            
    res_df = pd.DataFrame(mapping_list)
    return res_df

def procesar_tabla_posiciones(url):
    csv_url = clean_google_sheet_url(url)
    try:
        df_raw = pd.read_csv(csv_url, header=None, dtype=str, on_bad_lines='skip')
    except:
        return pd.DataFrame(columns=['Equipo', 'Pts', 'GF', 'GC'])

    res_data = []
    col_eq = -1
    col_pts = -1
    
    for idx, row in df_raw.iterrows():
        row_str = [str(x).strip().upper() for x in row.values]
        row_orig = [str(x).strip() for x in row.values]
        
        if any('EQUIPO' in val or 'CLUB' in val for val in row_str):
            for i, val in enumerate(row_str):
                if 'EQUIPO' in val or 'CLUB' in val:
                    col_eq = i
                elif 'PTS' in val or 'PUNTOS' in val:
                    col_pts = i
            continue
        
        if col_eq != -1 and col_eq < len(row_orig):
            eq_name = row_orig[col_eq]
            if not eq_name or eq_name.upper() in ['NAN', 'NONE', '']:
                continue
            
            pts_val = 0
            if col_pts != -1 and col_pts < len(row_orig):
                pts_str = row_orig[col_pts]
                try:
                    pts_val = int(''.join(filter(str.isdigit, pts_str)))
                except:
                    pts_val = 0
            
            gf, gc = 0, 0
            for cell in row_orig:
                if ':' in cell:
                    if sum(c.isdigit() for c in cell) >= 2:
                        parts = cell.split(':')
                        if len(parts) >= 2:
                            try:
                                gf = int(''.join(filter(str.isdigit, parts[0])))
                                gc = int(''.join(filter(str.isdigit, parts[1])))
                            except:
                                pass
                        break 
            
            res_data.append({
                'Equipo': eq_name, 
                'Pts': pts_val, 
                'GF': gf, 
                'GC': gc
            })
            
    return pd.DataFrame(res_data)

def procesar_jugadores(url, pos):
    df = load_data(url)
    if df is None or df.empty: 
        st.warning(f"⚠️ No se encontraron datos para **{pos}**.")
        return pd.DataFrame()
    
    col_j = next((c for c in df.columns if 'jugador' in c.lower()), df.columns[0] if len(df.columns) > 0 else None)
    col_e = next((c for c in df.columns if 'equipo' in c.lower() or 'club' in c.lower()), df.columns[2] if len(df.columns) > 2 else None)
    
    if not col_j or not col_e: 
        return pd.DataFrame()
    
    res = pd.DataFrame()
    res['Jugador'] = df[col_j].astype(str).str.strip()
    res['Equipo'] = df[col_e].astype(str).str.strip()
    res['Pos'] = pos
    
    for col in df.columns:
        c_low = col.lower()
        if c_low in ['act', 'prt'] or c_low.startswith('f'):
            res[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            
    return res

if st.button("🚀 Procesar Datos y Actualizar Scouting"):
    if not url_fixture or not url_tabla:
        st.error("Por favor, ingresa los links del Fixture y de la Tabla de Posiciones.")
        st.stop()

    df_fix = procesar_fixture(url_fixture)
    df_tab = procesar_tabla_posiciones(url_tabla)

    lista_jugadores = []
    with st.spinner(f"Descargando datos en vivo de la Fecha {NUM_FECHA}..."):
        for pos, url in urls_jugadores.items():
            if url.strip():
                df_p = procesar_jugadores(url, pos)
                if not df_p.empty:
                    lista_jugadores.append(df_p)

    if not lista_jugadores:
        st.error("❌ No se pudo cargar la información de los jugadores.")
        st.stop()

    df_full = pd.concat(lista_jugadores, ignore_index=True)
    
    # Normalizar llaves para el cruce
    df_fix['Equipo_key'] = df_fix['Equipo'].apply(normalizar_nombre)
    df_full['Equipo_key'] = df_full['Equipo'].apply(normalizar_nombre)
    
    # Cruce del Fixture
    df_full = df_full.merge(df_fix[['Equipo_key', 'Rival_Nombre', 'Condicion']], on='Equipo_key', how='left')
    
    # Formatear la columna visible 'Rival' para agregar (L) o (V)
    def formatear_rival(row):
        r_nombre = row.get('Rival_Nombre')
        if pd.isna(r_nombre): return 'Libre / S/D'
        cond = row.get('Condicion')
        if pd.isna(cond): return str(r_nombre)
        return f"{r_nombre}({cond})"

    df_full['Rival'] = df_full.apply(formatear_rival, axis=1)
    
    # Crear llave limpia para cruzar con la tabla de posiciones (sin L/V)
    df_full['Rival_Nombre'] = df_full['Rival_Nombre'].fillna('Libre / S/D')
    df_full['Rival_key'] = df_full['Rival_Nombre'].apply(normalizar_nombre)
    
    df_tab['Equipo_key'] = df_tab['Equipo'].apply(normalizar_nombre)
    df_tab_rival = df_tab[['Equipo_key', 'Pts', 'GF', 'GC']].rename(columns={
        'Equipo_key': 'Rival_key',
        'Pts': 'Rival_Pts',
        'GF': 'Rival_GF',
        'GC': 'Rival_GC'
    })
    
    # Cruce de Posiciones
    df_full = df_full.merge(df_tab_rival, on='Rival_key', how='left')
    
    for c in ['Rival_Pts', 'Rival_GF', 'Rival_GC']:
        if c in df_full.columns:
            df_full[c] = df_full[c].fillna(0).astype(int) 

    if 'AcT' not in df_full.columns: df_full['AcT'] = 0.0
    if 'PrT' not in df_full.columns: df_full['PrT'] = 0.0

    # Orden general inicial por puntaje
    df_full = df_full.sort_values(by=['AcT', 'PrT'], ascending=[False, False]).reset_index(drop=True)
    st.session_state['df_full'] = df_full
    st.success(f"¡Datos actualizados correctamente a la Fecha {NUM_FECHA}!")

if 'df_full' in st.session_state:
    df_full = st.session_state['df_full']

    # --- PESTAÑAS (TABS) ACTUALIZADAS ---
    tabs = st.tabs([
        f"👕 Plantel Ideal (Normal)", 
        f"⚡ Equipo Potenciado (Estratégico)", 
        "🧤 ARQ", 
        "🛡️ DEF", 
        "👟 VOL", 
        "⚽ DEL",
        "📊 Ranking General"
    ])

    esquemas_titulares = {
        "4-4-2": {"ARQ": 1, "DEF": 4, "VOL": 4, "DEL": 2},
        "4-3-3": {"ARQ": 1, "DEF": 4, "VOL": 3, "DEL": 3},
        "3-5-2": {"ARQ": 1, "DEF": 3, "VOL": 5, "DEL": 2},
        "3-4-3": {"ARQ": 1, "DEF": 3, "VOL": 4, "DEL": 3},
        "5-3-2": {"ARQ": 1, "DEF": 5, "VOL": 3, "DEL": 2},
        "3-3-4": {"ARQ": 1, "DEF": 3, "VOL": 3, "DEL": 4}
    }
    req = esquemas_titulares.get(esquema_elegido, {"ARQ": 1, "DEF": 4, "VOL": 4, "DEL": 2})

    # --- TAB 0: PLANTEL IDEAL CLÁSICO ---
    with tabs[0]:
        st.subheader(f"Plantel Ideal Clásico (Por Puntaje) - Esquema: {esquema_elegido}")
        
        titulares_dfs, suplentes_dfs, used_indices = [], [], []
        for p_pos, cant in req.items():
            df_pos = df_full[df_full['Pos'] == p_pos].sort_values(by=['AcT', 'PrT'], ascending=[False, False])
            tits = df_pos.head(cant)
            used_indices.extend(tits.index.tolist())
            tits = tits.copy()
            tits['Condición'] = 'Titular'
            titulares_dfs.append(tits)
            
            df_restantes = df_pos[~df_pos.index.isin(used_indices)]
            sups = df_restantes.head(1)
            if not sups.empty:
                used_indices.extend(sups.index.tolist())
                sups = sups.copy()
                sups['Condición'] = 'Suplente'
                suplentes_dfs.append(sups)
                
        if titulares_dfs and suplentes_dfs:
            df_plantel = pd.concat(titulares_dfs + suplentes_dfs, ignore_index=True)
            cols_base = ['Condición', 'Jugador', 'Pos', 'Equipo', 'Rival', 'Rival_Pts', 'Rival_GF', 'Rival_GC', 'AcT', 'PrT']
            cols_disp = [c for c in cols_base if c in df_plantel.columns]
            fechas_cols = [c for c in df_plantel.columns if c.lower().startswith('f')]
            st.dataframe(df_plantel[cols_disp + fechas_cols], use_container_width=True)

    # --- TAB 1: EQUIPO POTENCIADO (ESTRATÉGICO) ---
    with tabs[1]:
        st.subheader(f"⚡ Equipo Potenciado (Análisis de Rival) - Esquema: {esquema_elegido}")
        st.markdown("*🎯 **ARQ/DEF**: Busca rivales que hacen pocos goles. **VOL/DEL**: Busca rivales que reciben muchos goles.*")
        
        titulares_pot, suplentes_pot, used_indices_pot = [], [], []
        
        for p_pos, cant in req.items():
            df_pos_pot = df_full[df_full['Pos'] == p_pos].copy()
            
            # Lógica Estratégica:
            if p_pos in ["ARQ", "DEF"]:
                # ARQ y DEF: Rivales con menos Goles a Favor (ascendente)
                df_pos_pot = df_pos_pot.sort_values(by=['Rival_GF', 'AcT', 'PrT'], ascending=[True, False, False])
            else:
                # VOL y DEL: Rivales con más Goles en Contra (descendente)
                df_pos_pot = df_pos_pot.sort_values(by=['Rival_GC', 'AcT', 'PrT'], ascending=[False, False, False])

            tits = df_pos_pot.head(cant)
            used_indices_pot.extend(tits.index.tolist())
            tits = tits.copy()
            tits['Condición'] = 'Titular'
            titulares_pot.append(tits)
            
            df_restantes = df_pos_pot[~df_pos_pot.index.isin(used_indices_pot)]
            sups = df_restantes.head(1)
            if not sups.empty:
                used_indices_pot.extend(sups.index.tolist())
                sups = sups.copy()
                sups['Condición'] = 'Suplente'
                suplentes_pot.append(sups)
                
        if titulares_pot and suplentes_pot:
            df_plantel_pot = pd.concat(titulares_pot + suplentes_pot, ignore_index=True)
            cols_base = ['Condición', 'Jugador', 'Pos', 'Equipo', 'Rival', 'Rival_Pts', 'Rival_GF', 'Rival_GC', 'AcT', 'PrT']
            cols_disp = [c for c in cols_base if c in df_plantel_pot.columns]
            fechas_cols = [c for c in df_plantel_pot.columns if c.lower().startswith('f')]
            st.dataframe(df_plantel_pot[cols_disp + fechas_cols], use_container_width=True)

    # --- TABS 2 A 5: POR POSICIONES ---
    posiciones_map = {"ARQ": 2, "DEF": 3, "VOL": 4, "DEL": 5}
    for pos_key, tab_idx in posiciones_map.items():
        with tabs[tab_idx]:
            st.subheader(f"Mejores Jugadores - {pos_key} (Fecha {NUM_FECHA})")
            df_p_view = df_full[df_full['Pos'] == pos_key].sort_values(by=['AcT', 'PrT'], ascending=[False, False])
            cols_base = ['Jugador', 'Equipo', 'Rival', 'Rival_Pts', 'Rival_GF', 'Rival_GC', 'AcT', 'PrT']
            cols_disp = [c for c in cols_base if c in df_p_view.columns]
            fechas_cols = [c for c in df_p_view.columns if c.lower().startswith('f')]
            st.dataframe(df_p_view[cols_disp + fechas_cols], use_container_width=True)

    # --- TAB 6: RANKING GENERAL ---
    with tabs[6]:
        st.subheader(f"📊 Ranking General de Todos los Jugadores (Fecha {NUM_FECHA})")
        cols_base = ['Jugador', 'Pos', 'Equipo', 'Rival', 'Rival_Pts', 'Rival_GF', 'Rival_GC', 'AcT', 'PrT']
        cols_disp = [c for c in cols_base if c in df_full.columns]
        fechas_cols = [c for c in df_full.columns if c.lower().startswith('f')]
        st.dataframe(df_full[cols_disp + fechas_cols], use_container_width=True)
else:
    st.info("👈 Presiona **'🚀 Procesar Datos y Actualizar Scouting'** en la barra lateral para generar la aplicación con los nuevos datos.")
