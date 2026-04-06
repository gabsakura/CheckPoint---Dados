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

# CSS customizado - Ajuste de Margens, Título mais baixo e Cores
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
    }
    .header-title {
        color: #4F46E5; 
        font-size: 28px;
        font-weight: bold;
        margin-top: 40px; /* <--- TÍTULO ABAIXADO AQUI */
        margin-bottom: 5px;
        border-bottom: 2px solid #e5e7eb;
        padding-bottom: 10px;
    }
    .resumo-box {
        background-color: #1E3A8A; 
        color: #FFFFFF; 
        padding: 15px; 
        border-radius: 8px; 
        margin-bottom: 20px;
        font-size: 15px;
        border-left: 5px solid #818CF8; /* Borda esquerda num azul mais claro para destacar */
        line-height: 1.6;
    }
    .subtexto-ref {
        font-size: 13px;
        color: #666;
        margin-bottom: 15px;
    }
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# FUNÇÕES AUXILIARES E CARREGAMENTO
# ============================================================================
@st.cache_data
def carregar_dados(arquivo):
    # Tenta detectar o delimitador e o encoding de forma mais flexível
    try:
        # Tenta ler com separador automático (sep=None faz o pandas detectar se é , ou ;)
        df = pd.read_csv(arquivo, encoding='utf-8', sep=None, engine='python')
    except:
        arquivo.seek(0) # Reinicia o ponteiro do arquivo para ler novamente
        df = pd.read_csv(arquivo, encoding='iso-8859-1', sep=None, engine='python')

    # Dicionário de mapeamento (Verifique se os nomes batem EXATAMENTE com o CSV)
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
    
    # Renomeia apenas as colunas que existirem para evitar erros
    df = df.rename(columns=mapeamento)

    # Tratamento de Proficiência
    if 'Percentual_Proficiencia' in df.columns:
        df['Percentual_Proficiencia'] = df['Percentual_Proficiencia'].astype(str).str.replace('%', '').str.replace(',', '.')
        df['Percentual_Proficiencia'] = pd.to_numeric(df['Percentual_Proficiencia'], errors='coerce')
        
        if df['Percentual_Proficiencia'].max() <= 1.0:
            df['Percentual_Proficiencia'] = df['Percentual_Proficiencia'] * 100

    # Conversão de colunas numéricas
    colunas_num = ['Inscritos', 'Participantes', 'Acima_Proficiencia', 'Faixa_Enade']
    for col in colunas_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Criação de colunas auxiliares (com verificações de existência)
    if 'Categoria' in df.columns:
        df['Tipo_IES'] = df['Categoria'].apply(lambda x: 'Pública' if 'Pública' in str(x) else 'Privada')
    
    # Prevenção de erro na coluna Município
    col_mun = 'Município do Curso' if 'Município do Curso' in df.columns else 'Município'
    
    # Criando colunas de exibição com strings seguras
    df['IES_Nome_Completo'] = df['IES'].astype(str) + " (" + df['Sigla_IES'].astype(str) + " - " + df['UF'].astype(str) + ")"
    
    if col_mun in df.columns:
        df['IES_Campus'] = df['Sigla_IES'].astype(str) + " - " + df['UF'].astype(str) + " (" + df[col_mun].astype(str) + ")"
    else:
        df['IES_Campus'] = df['IES_Nome_Completo'] # Fallback caso não ache município
    
    return df

# ============================================================================
# SIDEBAR - NAVEGAÇÃO E UPLOAD
# ============================================================================
st.sidebar.markdown("### 📁 Fonte de Dados")
arquivo_carregado = st.sidebar.file_uploader("Upload CSV", type=['csv'], label_visibility="collapsed")

if arquivo_carregado is not None:
    print(arquivo_carregado)
    df = carregar_dados(arquivo_carregado)
else:
    try:
        df = carregar_dados("src/data/conceito-enade-2025-medicina(PLANILHA_ENADE).csv")
    except:
        st.error("❌ Faça upload do CSV do Enade.")
        st.stop()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🧭 Navegação")
pagina = st.sidebar.radio("Ir para:", [
    "🏠 Início (Análise de Similares)", 
    "📊 Dashboard de Desempenho", 
    "🏆 Top 30% e Flop 30%"
])

st.markdown("<div class='header-title'>🎓 ENADE 2025 - Análise de Medicina</div>", unsafe_allow_html=True)
st.markdown("<div class='subtexto-ref'>📄 Dados referentes ao desempenho dos alunos concluintes participantes da prova do ENADE.</div>", unsafe_allow_html=True)

# ============================================================================
# PÁGINA 1: INÍCIO - ANÁLISE DE SIMILARES 
# ============================================================================
if pagina == "🏠 Início (Análise de Similares)":
    
    df_valido_global = df.dropna(subset=['Percentual_Proficiencia'])
    
    if not df_valido_global.empty:
        melhor = df_valido_global.loc[df_valido_global['Percentual_Proficiencia'].idxmax()]
        pior = df_valido_global.loc[df_valido_global['Percentual_Proficiencia'].idxmin()]
        
        st.markdown(f"""
        <div class="resumo-box">
            <b>🏆 Melhor Faculdade:</b> {melhor['IES']} ({melhor['Sigla_IES']} - {melhor['UF']}) com <b>{melhor['Percentual_Proficiencia']:.1f}%</b> de proficiência.<br>
            <b>⚠️ Pior Faculdade:</b> {pior['IES']} ({pior['Sigla_IES']} - {pior['UF']}) com <b>{pior['Percentual_Proficiencia']:.1f}%</b> de proficiência.<br>
            <hr style='margin: 8px 0; border: 0; border-top: 1px solid rgba(255, 255, 255, 0.3);'> <i>Nesta seleção, temos um total de <b>{len(df_valido_global)}</b> faculdades. A média de alunos que participaram da prova é de <b>{df_valido_global['Participantes'].mean():.0f}</b>, 
            dos quais uma média de <b>{df_valido_global['Acima_Proficiencia'].mean():.0f}</b> foram aprovados, resultando em uma proficiência média geral de <b>{df_valido_global['Percentual_Proficiencia'].mean():.1f}%</b>.</i>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("#### 🔍 Encontre Faculdades com Perfis Semelhantes")
    st.markdown("Selecione uma faculdade de referência para encontrarmos outras instituições com números parecidos de **Alunos Participantes** e **Alunos Aprovados**.")

    col1, col2 = st.columns([2, 1])
    with col1:
        lista_faculdades = sorted(df['IES_Nome_Completo'].dropna().unique().tolist())
        faculdade_ref = st.selectbox("1. Escolha a faculdade de referência:", lista_faculdades)
    with col2:
        tipo_comparacao = st.radio("2. Comparar com:", [
            "Todas as Instituições", 
            "Mesma Categoria (Ex: Pub x Pub / Priv x Priv)", 
            "Categoria Oposta (Ex: Pub x Priv)"
        ])

    df_sim = df.copy().dropna(subset=['Participantes', 'Acima_Proficiencia'])
    
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
    st.sidebar.markdown("### 🔍 Filtros do Dashboard")
    filtro_uf = st.sidebar.selectbox("Estado", ['Todos'] + sorted(df['UF'].dropna().unique().tolist()))
    filtro_tipo = st.sidebar.selectbox("Tipo", ['Todos'] + sorted(df['Tipo_IES'].dropna().unique().tolist()))
    
    df_filtrado = df.copy()
    if filtro_uf != 'Todos': df_filtrado = df_filtrado[df_filtrado['UF'] == filtro_uf]
    if filtro_tipo != 'Todos': df_filtrado = df_filtrado[df_filtrado['Tipo_IES'] == filtro_tipo]

    # MÉTRICAS COM REFERÊNCIAS DE TEXTO NO 'HELP'
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total de Cursos Filtrados", f"{len(df_filtrado)}", help="Quantidade total de cursos de medicina selecionados.")
    m2.metric("Média de Alunos Participantes", f"{df_filtrado['Participantes'].mean():.0f}", help="Média de concluintes que realizaram a prova por instituição.")
    m3.metric("Média de Alunos Aprovados", f"{df_filtrado['Acima_Proficiencia'].mean():.0f}", help="Média de alunos que atingiram a nota de corte do ENADE por instituição.")
    m4.metric("Proficiência Média (%)", f"{df_filtrado['Percentual_Proficiencia'].mean():.1f}%", help="Percentual médio global de proficiência dos cursos exibidos.")

    st.markdown("---")
    
    ALTURA_GRAFICO = 280 

    col1, col2 = st.columns(2)
    with col1:
        top_ies = df_filtrado.dropna(subset=['Percentual_Proficiencia']).sort_values(by='Percentual_Proficiencia', ascending=True).tail(10)
        if not top_ies.empty:
            fig_ranking = px.bar(
                top_ies, x='Percentual_Proficiencia', y='IES_Campus', orientation='h',
                title="Top 10 Faculdades por Proficiência", labels={'IES_Campus': 'Faculdade (Curso)', 'Percentual_Proficiencia': 'Proficiência (%)'},
                color='Percentual_Proficiencia', color_continuous_scale='Blues'
            )
            fig_ranking.update_layout(height=ALTURA_GRAFICO, margin=dict(l=0, r=0, t=30, b=0), coloraxis_showscale=False)
            st.plotly_chart(fig_ranking, use_container_width=True)

    with col2:
        df_boxplot = df_filtrado.dropna(subset=['Faixa_Enade']).copy()
        df_boxplot['Faixa_Enade_Str'] = df_boxplot['Faixa_Enade'].astype(int).astype(str)
        if not df_boxplot.empty:
            fig_box = px.box(
                df_boxplot, x='Faixa_Enade_Str', y='Percentual_Proficiencia', color='Faixa_Enade_Str',
                title="Distribuição de Proficiência x Faixa Enade",
                labels={'Faixa_Enade_Str': 'Conceito Enade', 'Percentual_Proficiencia': 'Proficiência (%)'},
                category_orders={'Faixa_Enade_Str': ['5', '4', '3', '2', '1']} 
            )
            fig_box.update_layout(height=ALTURA_GRAFICO, margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
            st.plotly_chart(fig_box, use_container_width=True)

    st.markdown("", unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        df_comparativo = df_filtrado.groupby('Tipo_IES')['Participantes'].sum().reset_index()
        if not df_comparativo.empty:
            fig_pub_priv = px.pie(
                df_comparativo, names='Tipo_IES', values='Participantes', title="Total de Alunos (Pública vs Privada)",
                color='Tipo_IES', color_discrete_map={'Pública': '#1f77b4', 'Privada': '#ff7f0e'}, hole=0.4
            )
            fig_pub_priv.update_traces(textposition='inside', textinfo='percent+label+value')
            fig_pub_priv.update_layout(height=ALTURA_GRAFICO, margin=dict(l=0, r=0, t=30, b=0), showlegend=False)
            st.plotly_chart(fig_pub_priv, use_container_width=True)

    with col4:
        df_medias = df_filtrado.groupby('Tipo_IES')[['Participantes', 'Acima_Proficiencia', 'Percentual_Proficiencia']].mean().reset_index()
        if not df_medias.empty:
            
            # NOVO CÁLCULO: Proporção Real para fazer sentido!
            total_alunos_geral = df_filtrado.groupby('Tipo_IES')['Participantes'].sum().sum()
            total_alunos_tipo = df_filtrado.groupby('Tipo_IES')['Participantes'].sum().reset_index()
            
            # Distribuição de onde estão os alunos (Ex: 30% na Pública e 70% na Privada)
            df_medias['Distribuição de Alunos (%)'] = (total_alunos_tipo['Participantes'] / total_alunos_geral) * 100
            
            # Qual a taxa média de alunos que passam dentro da própria rede?
            df_medias['Taxa de Aprovação Interna (%)'] = (df_medias['Acima_Proficiencia'] / df_medias['Participantes']) * 100
            
            # Qual a proficiência média?
            df_medias['Proficiência Média (%)'] = df_medias['Percentual_Proficiencia']
            
            df_medias_melt = pd.melt(df_medias, id_vars=['Tipo_IES'], value_vars=['Distribuição de Alunos (%)', 'Taxa de Aprovação Interna (%)', 'Proficiência Média (%)'], var_name='Indicador', value_name='Percentual')
            
            fig_medias = px.bar(
                df_medias_melt, x='Indicador', y='Percentual', color='Tipo_IES', barmode='group', text_auto='.1f',
                title="Comparativo Proporcional entre Redes", color_discrete_map={'Pública': '#1f77b4', 'Privada': '#ff7f0e'},
                labels={'Percentual': 'Proporção (%)', 'Indicador': ''}
            )
            fig_medias.update_layout(height=ALTURA_GRAFICO, margin=dict(l=0, r=0, t=30, b=0), legend_title_text='', yaxis_range=[0, 110])
            st.plotly_chart(fig_medias, use_container_width=True)

# ============================================================================
# PÁGINA 3: TOP 30 E FLOP 30
# ============================================================================
elif pagina == "🏆 Top 30% e Flop 30%":
    st.markdown("#### Melhores e Piores Cursos de Medicina")
    st.markdown("Cálculo automático baseado no **Percentual de Proficiência** global.")

    df_valido = df.dropna(subset=['Percentual_Proficiencia']).copy()

    limite_superior_30 = df_valido['Percentual_Proficiencia'].quantile(0.70) 
    limite_inferior_30 = df_valido['Percentual_Proficiencia'].quantile(0.30) 

    df_melhores = df_valido[df_valido['Percentual_Proficiencia'] >= limite_superior_30].sort_values('Percentual_Proficiencia', ascending=False)
    df_piores = df_valido[df_valido['Percentual_Proficiencia'] <= limite_inferior_30].sort_values('Percentual_Proficiencia', ascending=True)

    colunas_exibir = ['IES_Campus', 'Tipo_IES', 'Participantes', 'Acima_Proficiencia', 'Percentual_Proficiencia', 'Faixa_Enade']

    col1, col2 = st.columns(2)
    
    with col1:
        st.success(f"🌟 **TOP 30% Melhores** (Nota de corte: {limite_superior_30:.1f}%)")
        df_show_melhores = df_melhores[colunas_exibir].rename(columns={'IES_Campus': 'Faculdade (Campus)'})
        
        # Aplicando estilo de cor na tabela 
        styled_melhores = df_show_melhores.style.format({
            'Percentual_Proficiencia': '{:.1f}%',
            'Participantes': '{:.0f}',
            'Acima_Proficiencia': '{:.0f}'
        }).background_gradient(subset=['Percentual_Proficiencia'], cmap='Blues')
        
        st.dataframe(styled_melhores, use_container_width=True, hide_index=True, height=500)
        
    with col2:
        st.error(f"⚠️ **BOTTOM 30% Piores** (Nota de corte: {limite_inferior_30:.1f}%)")
        df_show_piores = df_piores[colunas_exibir].rename(columns={'IES_Campus': 'Faculdade (Campus)'})
        
        # Aplicando estilo de cor na tabela invertido (Reds)
        styled_piores = df_show_piores.style.format({
            'Percentual_Proficiencia': '{:.1f}%',
            'Participantes': '{:.0f}',
            'Acima_Proficiencia': '{:.0f}'
        }).background_gradient(subset=['Percentual_Proficiencia'], cmap='Reds')

        st.dataframe(styled_piores, use_container_width=True, hide_index=True, height=500)