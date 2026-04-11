import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import warnings

warnings.filterwarnings('ignore')

# Configuração da página - Layout Wide
st.set_page_config(
    page_title="Dashboard ENADE 2025",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
    <style>
    .header-title { color: #4F46E5; font-size: 28px; font-weight: bold; margin-bottom: 15px; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }
    .resumo-box { background-color: #1E3A8A; color: #FFFFFF; padding: 15px; border-radius: 8px; margin-top: 20px; font-size: 15px; border-left: 5px solid #818CF8; line-height: 1.6; }
    .contexto-box { background-color: #f1f5f9; color: #334155; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #e2e8f0; }
    .subtexto-ref { font-size: 13px; color: #666; margin-bottom: 15px; }
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# FUNÇÕES AUXILIARES E CARREGAMENTO
# ============================================================================
@st.cache_data
def carregar_dados(arquivo):
    try:
        df = pd.read_csv(arquivo, encoding='utf-8', sep=None, engine='python')
    except:
        try:
            arquivo.seek(0)
            df = pd.read_csv(arquivo, encoding='iso-8859-1', sep=None, engine='python')
        except:
            return pd.DataFrame()

    mapeamento = {
        'Nome da IES*': 'IES',
        'Sigla da IES*': 'Sigla_IES',
        'Sigla da UF': 'UF',
        'Categoria Administrativa': 'Categoria',
        'Nº de Concluintes Inscritos': 'Inscritos',
        'Nº  de Concluintes Participantes': 'Participantes',
        'Total de Concluintes Participantes Igual ou Acima da Proficiência': 'Acima_Proficiencia',
        'Percentual de Concluintes Participantes Igual ou Acima da Proficiência ': 'Percentual_Proficiencia',
        'Conceito Enade (Faixa)': 'Faixa_Enade'
    }
    
    df = df.rename(columns=mapeamento)

    if 'Percentual_Proficiencia' in df.columns:
        df['Percentual_Proficiencia'] = df['Percentual_Proficiencia'].astype(str).str.replace('%', '').str.replace(',', '.')
        df['Percentual_Proficiencia'] = pd.to_numeric(df['Percentual_Proficiencia'], errors='coerce')
        if df['Percentual_Proficiencia'].max() <= 1.0:
            df['Percentual_Proficiencia'] *= 100

    colunas_num = ['Inscritos', 'Participantes', 'Acima_Proficiencia', 'Faixa_Enade']
    for col in colunas_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    if 'Categoria' in df.columns:
        df['Tipo_IES'] = df['Categoria'].apply(lambda x: 'Pública' if 'Pública' in str(x) else 'Privada')
    
    col_mun = 'Município do Curso' if 'Município do Curso' in df.columns else 'Município'
    
    # Preenchimento de nans para evitar erros de string
    for c in ['IES', 'Sigla_IES', 'UF']:
        if c in df.columns: df[c] = df[c].fillna('N/A')

    df['IES_Nome_Completo'] = df['IES'].astype(str) + " (" + df['Sigla_IES'].astype(str) + " - " + df['UF'].astype(str) + ")"
    
    if col_mun in df.columns:
        df[col_mun] = df[col_mun].fillna('N/A')
        df['IES_Campus'] = df['Sigla_IES'].astype(str) + " - " + df['UF'].astype(str) + " (" + df[col_mun].astype(str) + ")"
    else:
        df['IES_Campus'] = df['IES_Nome_Completo']
    
    df['Rank_Nacional'] = df['Percentual_Proficiencia'].rank(ascending=False, method='min')
    
    return df

# ============================================================================
# SIDEBAR - NAVEGAÇÃO E FILTROS
# ============================================================================
st.sidebar.markdown("### 📁 Fonte de Dados")
arquivo_carregado = st.sidebar.file_uploader("Upload CSV", type=['csv'], label_visibility="collapsed")

if arquivo_carregado is not None:
    df_raw = carregar_dados(arquivo_carregado)
else:
    try:
        df_raw = carregar_dados("src/data/conceito-enade-2025-medicina(PLANILHA_ENADE).csv")
    except:
        st.error("❌ Faça upload do CSV do Enade.")
        st.stop()

if df_raw.empty:
    st.error("O arquivo está vazio ou não pôde ser lido corretamente.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🧭 Navegação")
pagina = st.sidebar.radio("Ir para:", [
    "🏠 Início (História e Similares)", 
    "📊 Dashboard de Desempenho", 
    "🏆 Top 30% e Flop 30%"
])

st.sidebar.markdown("---")
st.sidebar.markdown("### 📚 Filtros")
filtro_uf_global = st.sidebar.selectbox("Estado:", ['Todos'] + sorted(df_raw['UF'].dropna().unique().tolist()))

df_base = df_raw.copy()
if filtro_uf_global != 'Todos':
    df_base = df_base[df_base['UF'] == filtro_uf_global]

filtro_tipo = st.sidebar.selectbox("Tipo de IES:", ['Todos'] + sorted(df_base['Tipo_IES'].dropna().unique().tolist()))

df_filtrado = df_base.copy()
if filtro_tipo != 'Todos': 
    df_filtrado = df_filtrado[df_filtrado['Tipo_IES'] == filtro_tipo]

st.markdown("<div class='header-title'>🎓 ENADE 2025 - Análise de Medicina</div>", unsafe_allow_html=True)

# ============================================================================
# PÁGINA 1: INÍCIO - ANÁLISE DE SIMILARES 
# ============================================================================
if pagina == "🏠 Início (História e Similares)":
    
    # Usamos o df_filtrado para que o "Melhor e Pior" mude conforme os filtros da sidebar
    df_valido_contexto = df_filtrado.dropna(subset=['Percentual_Proficiencia'])
    
    if not df_valido_contexto.empty:
        # Identificando Melhor e Pior dentro do filtro atual
        melhor = df_valido_contexto.loc[df_valido_contexto['Percentual_Proficiencia'].idxmax()]
        pior = df_valido_contexto.loc[df_valido_contexto['Percentual_Proficiencia'].idxmin()]
        
        # Título dinâmico baseado no filtro
        contexto_nome = f"em {filtro_uf_global}" if filtro_uf_global != 'Todos' else "no Brasil"
        tipo_nome = f"({filtro_tipo})" if filtro_tipo != 'Todos' else ""

        st.markdown(f"### 📊 Destaques da Seleção {contexto_nome} {tipo_nome}")

        # Layout de colunas para os cards de Melhor e Pior
        c_best, c_worst = st.columns(2)
        
        with c_best:
            st.markdown(f"""
            <div style="background-color: #d1fae5; border-left: 5px solid #10b981; padding: 15px; border-radius: 5px;">
                <span style="color: #065f46; font-weight: bold; font-size: 14px;">🏆 MELHOR DESEMPENHO</span><br>
                <span style="color: #064e3b; font-size: 18px; font-weight: bold;">{melhor['Sigla_IES']} - {melhor['UF']}</span><br>
                <span style="color: #065f46; font-size: 14px;">{melhor['IES']}</span><br>
                <span style="color: #059669; font-size: 24px; font-weight: bold;">{melhor['Percentual_Proficiencia']:.1f}%</span>
            </div>
            """, unsafe_allow_html=True)

        with c_worst:
            st.markdown(f"""
            <div style="background-color: #fee2e2; border-left: 5px solid #ef4444; padding: 15px; border-radius: 5px;">
                <span style="color: #991b1b; font-weight: bold; font-size: 14px;">⚠️ MENOR DESEMPENHO</span><br>
                <span style="color: #7f1d1d; font-size: 18px; font-weight: bold;">{pior['Sigla_IES']} - {pior['UF']}</span><br>
                <span style="color: #991b1b; font-size: 14px;">{pior['IES']}</span><br>
                <span style="color: #dc2626; font-size: 24px; font-weight: bold;">{pior['Percentual_Proficiencia']:.1f}%</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="resumo-box">
            <i>Nesta seleção ({filtro_uf_global} / {filtro_tipo}), analisamos <b>{len(df_valido_contexto)}</b> faculdades. 
            A proficiência média deste grupo é de <b>{df_valido_contexto['Percentual_Proficiencia'].mean():.1f}%</b>.</i>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")

    st.markdown("---")
    st.markdown("#### 🔍 Encontre Faculdades com Perfis Semelhantes")
    st.markdown("Selecione uma faculdade de referência para encontrarmos outras instituições com números parecidos de **Alunos Participantes** e **Alunos Aprovados**.")

    col1, col2 = st.columns([2, 1])
    with col1:
        lista_faculdades = sorted(df_raw['IES_Nome_Completo'].dropna().unique().tolist())
        faculdade_ref = st.selectbox("1. Escolha a faculdade de referência:", lista_faculdades)
    with col2:
        tipo_comparacao = st.radio("2. Comparar com:", [
            "Todas as Instituições", 
            "Mesma Categoria (Ex: Pub x Pub / Priv x Priv)", 
            "Categoria Oposta (Ex: Pub x Priv)"
        ])

    df_sim = df_raw.copy().dropna(subset=['Participantes', 'Acima_Proficiencia'])
    
    if len(df_sim) > 0 and faculdade_ref:
        df_sim['Part_norm'] = (df_sim['Participantes'] - df_sim['Participantes'].mean()) / df_sim['Participantes'].std()
        df_sim['Aprov_norm'] = (df_sim['Acima_Proficiencia'] - df_sim['Acima_Proficiencia'].mean()) / df_sim['Acima_Proficiencia'].std()
        
        try:
            ref_data = df_sim[df_sim['IES_Nome_Completo'] == faculdade_ref].iloc[0]
            tipo_ref = ref_data['Tipo_IES']

            if tipo_comparacao == "Mesma Categoria (Ex: Pub x Pub / Priv x Priv)":
                df_comp = df_sim[df_sim['Tipo_IES'] == tipo_ref]
            elif tipo_comparacao == "Categoria Oposta (Ex: Pub x Priv)":
                df_comp = df_sim[df_sim['Tipo_IES'] != tipo_ref]
            else:
                df_comp = df_sim

            df_comp = df_comp[df_comp['IES_Nome_Completo'] != faculdade_ref]

            if len(df_comp) == 0:
                st.warning("Não há faculdades suficientes para essa comparação com os filtros atuais.")
            else:
                df_comp['Distancia'] = np.sqrt((df_comp['Part_norm'] - ref_data['Part_norm'])**2 + (df_comp['Aprov_norm'] - ref_data['Aprov_norm'])**2)
                df_top_similares = df_comp.sort_values('Distancia').head(5)

                st.markdown(f"**Referência:** {ref_data['IES_Nome_Completo']} | Tipo: {tipo_ref} | Alunos: {ref_data['Participantes']} | Aprovados: {ref_data['Acima_Proficiencia']}")
                st.markdown("##### 🤝 Top 5 Instituições Mais Parecidas:")
                
                colunas_exibir = ['IES_Campus', 'Tipo_IES', 'Participantes', 'Acima_Proficiencia', 'Percentual_Proficiencia', 'Faixa_Enade']
                df_exibir_sim = df_top_similares[colunas_exibir].rename(columns={'IES_Campus': 'Faculdade (Campus)', 'Tipo_IES': 'Categoria'})
                
                # Aplicando cor estilizada (Mapa de Calor nas notas)
                styled_sim = df_exibir_sim.style.format({
                    'Percentual_Proficiencia': '{:.1f}%',
                    'Participantes': '{:.0f}',
                    'Acima_Proficiencia': '{:.0f}'
                }).background_gradient(subset=['Percentual_Proficiencia'], cmap='Blues')

                st.dataframe(styled_sim, use_container_width=True, hide_index=True)
        except IndexError:
            st.error("Dados da faculdade de referência incompletos para comparação.")

# ============================================================================
# PÁGINA 2: DASHBOARD
# ============================================================================
elif pagina == "📊 Dashboard de Desempenho":
    if df_filtrado.empty:
        st.warning("Sem dados para exibir com os filtros atuais.")
    else:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Cursos Filtrados", f"{len(df_filtrado)}")
        m2.metric("Média Participantes", f"{df_filtrado['Participantes'].mean():.0f}")
        m3.metric("Média Aprovados", f"{df_filtrado['Acima_Proficiencia'].mean():.0f}")
        m4.metric("Proficiência Média", f"{df_filtrado['Percentual_Proficiencia'].mean():.1f}%")

        st.markdown("---")
        ALTURA_GRAFICO = 350 

        col1, col2 = st.columns(2)
        with col1:
            top_ies = df_filtrado.sort_values(by='Percentual_Proficiencia', ascending=True).tail(10)
            fig_ranking = px.bar(top_ies, x='Percentual_Proficiencia', y='IES_Campus', orientation='h', 
                                 title="Top 10 Faculdades da Seleção", color='Percentual_Proficiencia', color_continuous_scale='Blues')
            fig_ranking.update_layout(height=ALTURA_GRAFICO, margin=dict(l=0, r=0, t=30, b=0), coloraxis_showscale=False)
            st.plotly_chart(fig_ranking, use_container_width=True)
        
        with col2:
            df_boxplot = df_filtrado.copy()
            df_boxplot['Faixa_Enade_Str'] = df_boxplot['Faixa_Enade'].astype(int).astype(str)
            fig_box = px.box(df_boxplot, x='Faixa_Enade_Str', y='Percentual_Proficiencia', color='Faixa_Enade_Str', 
                             title="Distribuição por Faixa Enade", category_orders={'Faixa_Enade_Str': ['5', '4', '3', '2', '1']})
            fig_box.update_layout(height=ALTURA_GRAFICO, margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
            st.plotly_chart(fig_box, use_container_width=True)

        st.markdown("---")
        col3, col4 = st.columns(2)
        with col3:
            df_pie = df_filtrado.groupby('Tipo_IES')['Participantes'].sum().reset_index()
            fig_pie = px.pie(df_pie, names='Tipo_IES', values='Participantes', title="Distribuição de Alunos (Filtro Atual)", hole=0.4)
            fig_pie.update_layout(height=ALTURA_GRAFICO, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_pie, use_container_width=True)

        with col4:
            df_medias = df_filtrado.groupby('Tipo_IES')[['Participantes', 'Acima_Proficiencia', 'Percentual_Proficiencia']].mean().reset_index()
            # Renomear colunas para o gráfico
            df_medias = df_medias.rename(columns={'Percentual_Proficiencia': 'Média Proficiência (%)'})
            fig_bar = px.bar(df_medias, x='Tipo_IES', y='Média Proficiência (%)', title="Média de Proficiência por Tipo", text_auto='.1f', color='Tipo_IES')
            fig_bar.update_layout(height=ALTURA_GRAFICO, margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        st.markdown("---")

# ============================================================================
# PÁGINA 3: TOP 30 E FLOP 30
# ============================================================================
elif pagina == "🏆 Top 30% e Flop 30%":
    st.markdown("#### Rank de Performance (Dentro do Filtro)")
    
    df_valido = df_filtrado.dropna(subset=['Percentual_Proficiencia']).copy()
    
    if len(df_valido) < 2:
        st.warning("Dados insuficientes para calcular quantis (mínimo de 2 registros necessários).")
    else:
        limite_sup = df_valido['Percentual_Proficiencia'].quantile(0.70) 
        limite_inf = df_valido['Percentual_Proficiencia'].quantile(0.30) 

        df_melhores = df_valido[df_valido['Percentual_Proficiencia'] >= limite_sup].sort_values('Percentual_Proficiencia', ascending=False)
        df_piores = df_valido[df_valido['Percentual_Proficiencia'] <= limite_inf].sort_values('Percentual_Proficiencia', ascending=True)

        colunas_exibir = ['IES_Campus', 'Tipo_IES', 'Participantes', 'Acima_Proficiencia', 'Percentual_Proficiencia', 'Rank_Nacional']

        c1, c2 = st.columns(2)
        with c1:
            st.success(f"🌟 **MELHORES DA SELEÇÃO** (Corte: {limite_sup:.1f}%)")
            st.dataframe(df_melhores[colunas_exibir].style.format({'Percentual_Proficiencia': '{:.1f}%', 'Rank_Nacional': '{:.0f}'}).background_gradient(cmap='Blues'), use_container_width=True, hide_index=True)
            
        with c2:
            st.error(f"⚠️ **MENORES DESEMPENHOS** (Corte: {limite_inf:.1f}%)")
            st.dataframe(df_piores[colunas_exibir].style.format({'Percentual_Proficiencia': '{:.1f}%', 'Rank_Nacional': '{:.0f}'}).background_gradient(cmap='Reds'), use_container_width=True, hide_index=True)