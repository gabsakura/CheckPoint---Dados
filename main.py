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

# CSS customizado - Otimizado para evitar Scroll
st.markdown("""
    <style>
    /* Reduz o espaço branco no topo e laterais */
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
    
    /* Compacta o título principal */
    .header-title { color: #4F46E5; font-size: 24px; font-weight: bold; margin-bottom: 5px; margin-top: -15px; border-bottom: 2px solid #e5e7eb; padding-bottom: 5px; }
    
    /* Aproxima os subtítulos */
    h2, h3, h4 { padding-bottom: 0px !important; margin-bottom: 5px !important; margin-top: 5px !important; }
    
    /* Compacta caixas de resumo */
    .resumo-box { background-color: #1E3A8A; color: #FFFFFF; padding: 10px; border-radius: 8px; margin-top: 10px; margin-bottom: 10px; font-size: 14px; border-left: 5px solid #818CF8; line-height: 1.4; }
    
    /* Reduz espaço inútil abaixo das métricas numéricas */
    [data-testid="metric-container"] { padding-bottom: 0px !important; margin-bottom: -10px !important; }
    
    /* Esconde footer */
    footer {visibility: hidden;}
    hr { margin-top: 10px !important; margin-bottom: 10px !important; }
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
            if hasattr(arquivo, 'seek'):
                arquivo.seek(0)
            df = pd.read_csv(arquivo, encoding='iso-8859-1', sep=None, engine='python')
        except:
            return pd.DataFrame()

    # =========================
    # LIMPEZA DOS NOMES
    # =========================
    df.columns = (
        df.columns
        .str.strip()
        .str.replace(r'\s+', ' ', regex=True)  # remove múltiplos espaços
        .str.replace('*', '', regex=False)
    )

    # =========================
    # MAPEAMENTO FLEXÍVEL
    # =========================
    mapeamento = {
        'Nome da IES': 'IES',
        'Sigla da IES': 'Sigla_IES',
        'Sigla da UF': 'UF',
        'Categoria Administrativa': 'Categoria',
        'Nº de Concluintes Inscritos': 'Inscritos',
        'Nº de Concluintes Participantes': 'Participantes',
        'Total de Concluintes Participantes Igual ou Acima da Proficiência': 'Acima_Proficiencia',
        'Percentual de Concluintes Participantes Igual ou Acima da Proficiência': 'Percentual_Proficiencia',
        'Conceito Enade (Faixa)': 'Faixa_Enade',
        'Conceito Enade (Contínuo)': 'Nota_Continua'
    }

    df = df.rename(columns=mapeamento)

    # =========================
    # GARANTE COLUNAS ESSENCIAIS
    # =========================
    for col in ['IES', 'Sigla_IES', 'UF']:
        if col not in df.columns:
            df[col] = 'N/A'
        else:
            df[col] = df[col].fillna('N/A')

    # =========================
    # NUMÉRICOS
    # =========================
    colunas_num = ['Inscritos', 'Participantes', 'Acima_Proficiencia', 'Faixa_Enade', 'Nota_Continua']
    for col in colunas_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # =========================
    # CRIAR MÉTRICA PADRÃO ENTRE ANOS
    # =========================

    # Caso 2025 (tem dados reais)
    if 'Acima_Proficiencia' in df.columns and 'Participantes' in df.columns:
        df['Percentual_Proficiencia'] = (
            df['Acima_Proficiencia'] / df['Participantes'].replace(0, np.nan)
        ) * 100

    # Caso 2016 (usa nota contínua)
    elif 'Nota_Continua' in df.columns:
        nota = df['Nota_Continua']

        df['Percentual_Proficiencia'] = (
            (nota - nota.min()) / (nota.max() - nota.min())
        ) * 100

    else:
        df['Percentual_Proficiencia'] = np.nan

    # =========================
    # LIMPEZA FINAL DO %
    # =========================
    df['Percentual_Proficiencia'] = (
        df['Percentual_Proficiencia']
        .astype(str)
        .str.replace('%', '')
        .str.replace(',', '.')
    )
    df['Percentual_Proficiencia'] = pd.to_numeric(df['Percentual_Proficiencia'], errors='coerce')

    # =========================
    # TIPO DE IES
    # =========================
    if 'Categoria' in df.columns:
        df['Tipo_IES'] = df['Categoria'].apply(
            lambda x: 'Pública' if 'Pública' in str(x) else 'Privada'
        )
    else:
        df['Tipo_IES'] = 'Não Informado'

    # =========================
    # CAMPUS
    # =========================
    col_mun = 'Município do Curso' if 'Município do Curso' in df.columns else 'Município'

    df['IES_Nome_Completo'] = (
        df['IES'].astype(str) + " (" +
        df['Sigla_IES'].astype(str) + " - " +
        df['UF'].astype(str) + ")"
    )

    if col_mun in df.columns:
        df[col_mun] = df[col_mun].fillna('N/A')
        df['IES_Campus'] = (
            df['Sigla_IES'].astype(str) + " - " +
            df['UF'].astype(str) + " (" +
            df[col_mun].astype(str) + ")"
        )
    else:
        df['IES_Campus'] = df['IES_Nome_Completo']

    # =========================
    # REGIÕES
    # =========================
    dic_regioes = {
        'AC': 'Norte', 'AP': 'Norte', 'AM': 'Norte', 'PA': 'Norte', 'RO': 'Norte', 'RR': 'Norte', 'TO': 'Norte',
        'AL': 'Nordeste', 'BA': 'Nordeste', 'CE': 'Nordeste', 'MA': 'Nordeste', 'PB': 'Nordeste', 'PE': 'Nordeste', 'PI': 'Nordeste', 'RN': 'Nordeste', 'SE': 'Nordeste',
        'DF': 'Centro-Oeste', 'GO': 'Centro-Oeste', 'MT': 'Centro-Oeste', 'MS': 'Centro-Oeste',
        'ES': 'Sudeste', 'MG': 'Sudeste', 'RJ': 'Sudeste', 'SP': 'Sudeste',
        'PR': 'Sul', 'RS': 'Sul', 'SC': 'Sul'
    }

    df['Regiao'] = df['UF'].map(dic_regioes).fillna('Não Informada')

    # =========================
    # RANK
    # =========================
    df['Rank_Nacional'] = df['Percentual_Proficiencia'].rank(ascending=False, method='min')

    return df

# ============================================================================
# CARREGAMENTO DIRETO DO ARQUIVO LOCAL (PREPARADO PARA DEPLOY)
# ============================================================================
caminho_arquivo = "src/data/conceito-enade-2025-medicina(PLANILHA_ENADE).csv"

try:
    df_raw = carregar_dados(caminho_arquivo)
except Exception as e:
    st.error(f"❌ Erro ao carregar o banco de dados. Verifique se o arquivo existe no caminho: {caminho_arquivo}")
    st.stop()

if df_raw.empty:
    st.error("O arquivo está vazio ou não pôde ser lido corretamente.")
    st.stop()

# ============================================================================
# SIDEBAR - NAVEGAÇÃO E FILTROS 
# ============================================================================
st.sidebar.markdown("### 🧭 Navegação")
pagina = st.sidebar.radio("Ir para:", [
    "📖 O que é a ENADE?",       
    "🏠 Referência e Comparação", 
    "📊 Dashboard de Desempenho", 
    "🏆 Top e Flop Regionais",
    "🏅 Rank Nacional (Top & Bottom 30)",
    "📈 Comparação Histórica (2016 e 2025)"
])

st.sidebar.markdown("---")
st.sidebar.markdown("### 🗺️ Comparativo Regional")

todas_regioes = sorted(df_raw['Regiao'].dropna().unique().tolist())
idx_se = todas_regioes.index("Sudeste") if "Sudeste" in todas_regioes else 0
idx_ne = todas_regioes.index("Nordeste") if "Nordeste" in todas_regioes else (1 if len(todas_regioes)>1 else 0)

regiao_1 = st.sidebar.selectbox("🎯 Região Principal (R1):", todas_regioes, index=idx_se)
regiao_2 = st.sidebar.selectbox("⚖️ Região Comparação (R2):", todas_regioes, index=idx_ne)
filtro_tipo = st.sidebar.selectbox("Tipo de IES:", ['Todos'] + sorted(df_raw['Tipo_IES'].dropna().unique().tolist()))

df_r1 = df_raw[df_raw['Regiao'] == regiao_1].copy()
df_r2 = df_raw[df_raw['Regiao'] == regiao_2].copy()

if filtro_tipo != 'Todos':
    df_r1 = df_r1[df_r1['Tipo_IES'] == filtro_tipo]
    df_r2 = df_r2[df_r2['Tipo_IES'] == filtro_tipo]

df_comparativo = pd.concat([df_r1, df_r2])

st.markdown("<div class='header-title'>🎓 ENADE 2025 - Análise Regional de Medicina</div>", unsafe_allow_html=True)

# ============================================================================
# PÁGINA 0: STORYTELLING 
# ============================================================================
if pagina == "📖 O que é a ENADE?":
    st.markdown("## 🏥 A Jornada do ENADE Medicina 2025")
    st.markdown("Bem-vindo(a) ao painel analítico do ENADE 2025. Antes de mergulharmos nos dados, entenda o propósito e a matemática por trás deste dashboard.")
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 1. O que é o ENADE? *(O nosso Data Source)*")
        st.info("O Exame Nacional de Desempenho de Estudantes é a ferramenta do MEC para checar se o que as faculdades de Medicina prometem entregar está, de fato, na cabeça dos alunos. No nosso código, ele entra como o arquivo bruto (CSV). Ele **não avalia o aluno individualmente** para dar uma nota a ele, mas usa o desempenho do conjunto de alunos para avaliar a qualidade e dar uma nota ao curso como um todo.")
        st.markdown("### 2. O que ele mede? *(As nossas Variáveis)*")
        st.markdown("No dashboard, focamos em três métricas cruciais extraídas do mapeamento:\n* **📚 Conteúdo Programático:** O quanto o aluno domina a base teórica da medicina.\n* **🩺 Habilidades e Competências:** Se o futuro médico sabe aplicar o conhecimento em problemas práticos.\n* **🏛️ A \"Saúde\" da Instituição:** Através da `Faixa_Enade` (de 1 a 5).")
    with col2:
        st.markdown("### 3. O Coração do Dashboard: O que é a Proficiência?")
        st.success("A Proficiência é o patamar de conhecimento esperado para que um médico exerça a profissão com segurança. No ENADE, existe uma nota de corte técnica. Quem atinge ou ultrapassa esse valor é considerado **\"proficiente\"**.\n**A Proficiência no Dashboard:** Ela é o nosso indicador de sucesso (KPI). Quando olhamos para a coluna `Acima_Proficiencia`, estamos contando quantos alunos daquela faculdade realmente estão prontos para o mercado.")
    st.markdown("---")
    st.markdown("### 4. A Matemática por trás *(Como calculamos no Código)*")
    st.markdown("$$\n\\text{Percentual de Proficiência} = \\left( \\frac{\\text{Alunos Acima da Proficiência}}{\\text{Total de Alunos Participantes}} \\right) \\times 100\n$$")
    st.code("df['Rank_Nacional'] = df['Percentual_Proficiencia'].rank(ascending=False, method='min')", language="python")
    st.markdown("---")
    st.markdown("### 5. Por que isso é importante?")
    tab1, tab2, tab3 = st.tabs(["🎯 Escolha de Carreira", "🔍 Transparência Pública", "📈 Melhoria Contínua"])
    with tab1: st.markdown("**Hospitais e programas de residência olham para esses dados.** Uma faculdade no nosso `Top 30%` sinaliza que o aluno veio de um ambiente de alto rigor acadêmico.")
    with tab2: st.markdown("Através dos nossos gráficos, conseguimos ver de forma clara se as faculdades **Públicas ou Privadas** estão entregando médicos mais preparados.")
    with tab3: st.markdown("Quando uma faculdade se encontra no `Flop 30%`, ela pode usar a função de *Faculdades Semelhantes* para encontrar instituições parecidas que estão performando melhor e aprender com elas.")

# ============================================================================
# PÁGINA 1: INÍCIO - ANÁLISE DE SIMILARES 
# ============================================================================
elif pagina == "🏠 Referência e Comparação":
    st.markdown(f"### 📍 Destaques da Seleção: Região {regiao_1}")
    df_valido_contexto = df_r1.dropna(subset=['Percentual_Proficiencia'])
    
    if not df_valido_contexto.empty:
        melhor = df_valido_contexto.loc[df_valido_contexto['Percentual_Proficiencia'].idxmax()]
        pior = df_valido_contexto.loc[df_valido_contexto['Percentual_Proficiencia'].idxmin()]
        
        c_best, c_worst = st.columns(2)
        with c_best:
            st.markdown(f"""
            <div style="background-color: #d1fae5; border-left: 5px solid #10b981; padding: 10px; border-radius: 5px;">
                <span style="color: #065f46; font-weight: bold; font-size: 13px;">🏆 MELHOR DA REGIÃO</span><br>
                <span style="color: #064e3b; font-size: 16px; font-weight: bold;">{melhor['Sigla_IES']} - {melhor['UF']}</span><br>
                <span style="color: #065f46; font-size: 12px;">{melhor['IES']}</span><br>
                <span style="color: #059669; font-size: 22px; font-weight: bold;">{melhor['Percentual_Proficiencia']:.1f}%</span>
            </div>
            """, unsafe_allow_html=True)

        with c_worst:
            st.markdown(f"""
            <div style="background-color: #fee2e2; border-left: 5px solid #ef4444; padding: 10px; border-radius: 5px;">
                <span style="color: #991b1b; font-weight: bold; font-size: 13px;">⚠️ PIOR DA REGIÃO</span><br>
                <span style="color: #7f1d1d; font-size: 16px; font-weight: bold;">{pior['Sigla_IES']} - {pior['UF']}</span><br>
                <span style="color: #991b1b; font-size: 12px;">{pior['IES']}</span><br>
                <span style="color: #dc2626; font-size: 22px; font-weight: bold;">{pior['Percentual_Proficiencia']:.1f}%</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="resumo-box">
            <i>Na região <b>{regiao_1}</b> ({filtro_tipo}), analisamos <b>{len(df_valido_contexto)}</b> faculdades. Proficiência média: <b>{df_valido_contexto['Percentual_Proficiencia'].mean():.1f}%</b>.</i>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning(f"Nenhum dado encontrado para a Região {regiao_1}.")

    st.markdown("---")
    st.markdown(f"#### 🔍 Instituições Semelhantes ({regiao_1})")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        lista_faculdades = sorted(df_r1['IES_Nome_Completo'].dropna().unique().tolist())
        faculdade_ref = st.selectbox(f"Selecione a base:", lista_faculdades) if lista_faculdades else None
    with col2:
        tipo_comparacao = st.radio("Filtro Comparativo:", ["Todas da Região", "Mesma Categoria", "Categoria Oposta"])

    df_sim = df_r1.copy().dropna(subset=['Participantes', 'Acima_Proficiencia'])
    
    if len(df_sim) > 0 and faculdade_ref:
        df_sim['Part_norm'] = (df_sim['Participantes'] - df_sim['Participantes'].mean()) / df_sim['Participantes'].std()
        df_sim['Aprov_norm'] = (df_sim['Acima_Proficiencia'] - df_sim['Acima_Proficiencia'].mean()) / df_sim['Acima_Proficiencia'].std()
        try:
            ref_data = df_sim[df_sim['IES_Nome_Completo'] == faculdade_ref].iloc[0]
            tipo_ref = ref_data['Tipo_IES']
            if tipo_comparacao == "Mesma Categoria": df_comp = df_sim[df_sim['Tipo_IES'] == tipo_ref]
            elif tipo_comparacao == "Categoria Oposta": df_comp = df_sim[df_sim['Tipo_IES'] != tipo_ref]
            else: df_comp = df_sim

            df_comp = df_comp[df_comp['IES_Nome_Completo'] != faculdade_ref]
            if len(df_comp) == 0:
                st.warning("Poucas faculdades para comparação neste filtro.")
            else:
                df_comp['Dist'] = np.sqrt((df_comp['Part_norm'] - ref_data['Part_norm'])**2 + (df_comp['Aprov_norm'] - ref_data['Aprov_norm'])**2)
                st.markdown(f"**Referência:** {ref_data['IES_Nome_Completo']} | {tipo_ref} | Alunos: {ref_data['Participantes']}")
                colunas_exibir = ['IES_Campus', 'Tipo_IES', 'Participantes', 'Acima_Proficiencia', 'Percentual_Proficiencia']
                
                # Gradiente travado em 0-100 para não desbotar
                st.dataframe(df_comp.sort_values('Dist').head(5)[colunas_exibir]
                             .style.format({'Percentual_Proficiencia': '{:.1f}%', 'Participantes': '{:.0f}', 'Acima_Proficiencia': '{:.0f}'})
                             .background_gradient(subset=['Percentual_Proficiencia'], cmap='Blues', vmin=0, vmax=100), 
                             use_container_width=True, hide_index=True)
        except IndexError:
            pass

# ============================================================================
# PÁGINA 2: DASHBOARD LADO A LADO 
# ============================================================================
elif pagina == "📊 Dashboard de Desempenho":
    if df_comparativo.empty:
        st.warning("Sem dados para exibir com os filtros atuais.")
    else:
        st.markdown(f"### ⚖️ Comparativo: **{regiao_1}** vs **{regiao_2}**")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric(f"Cursos {regiao_1}", f"{len(df_r1)}")
        m2.metric(f"Média {regiao_1}", f"{df_r1['Percentual_Proficiencia'].mean():.1f}%" if not df_r1.empty else "N/A")
        m3.metric(f"Cursos {regiao_2}", f"{len(df_r2)}")
        m4.metric(f"Média {regiao_2}", f"{df_r2['Percentual_Proficiencia'].mean():.1f}%" if not df_r2.empty else "N/A")

        st.markdown("---")
        ALTURA_GRAFICO = 250

        col1, col2 = st.columns(2)
        with col1:
            df_boxplot = df_comparativo.copy().dropna(subset=['Faixa_Enade', 'Percentual_Proficiencia'])
            if not df_boxplot.empty:
                df_boxplot['Faixa_Enade_Str'] = df_boxplot['Faixa_Enade'].astype(int).astype(str)
                fig_box = px.box(df_boxplot, x='Faixa_Enade_Str', y='Percentual_Proficiencia', color='Regiao', 
                                 title="Proficiência x Faixa Enade", category_orders={'Faixa_Enade_Str': ['5', '4', '3', '2', '1']}, color_discrete_sequence=['#4F46E5', '#F59E0B'])
                fig_box.update_layout(height=ALTURA_GRAFICO, margin=dict(l=0, r=0, t=30, b=0), boxmode='group')
                st.plotly_chart(fig_box, use_container_width=True)
        
        with col2:
            df_medias = df_comparativo.groupby(['Regiao', 'Tipo_IES'])[['Percentual_Proficiencia']].mean().reset_index()
            if not df_medias.empty:
                fig_bar = px.bar(df_medias, x='Tipo_IES', y='Percentual_Proficiencia', color='Regiao', barmode='group', title="Média: Públicas vs Privadas", text_auto='.1f', color_discrete_sequence=['#4F46E5', '#F59E0B'])
                fig_bar.update_layout(height=ALTURA_GRAFICO, margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_bar, use_container_width=True)

        col3, col4 = st.columns(2)
        with col3:
            top_r1 = df_r1.dropna(subset=['Percentual_Proficiencia']).sort_values(by='Percentual_Proficiencia', ascending=True).tail(10)
            if not top_r1.empty:
                fig_r1 = px.bar(top_r1, x='Percentual_Proficiencia', y='IES_Campus', orientation='h', title=f"Top 10 - {regiao_1}", color='Percentual_Proficiencia', color_continuous_scale='Blues')
                fig_r1.update_layout(height=ALTURA_GRAFICO, margin=dict(l=0, r=0, t=30, b=0), coloraxis_showscale=False)
                st.plotly_chart(fig_r1, use_container_width=True)
                
        with col4:
            top_r2 = df_r2.dropna(subset=['Percentual_Proficiencia']).sort_values(by='Percentual_Proficiencia', ascending=True).tail(10)
            if not top_r2.empty:
                fig_r2 = px.bar(top_r2, x='Percentual_Proficiencia', y='IES_Campus', orientation='h', title=f"Top 10 - {regiao_2}", color='Percentual_Proficiencia', color_continuous_scale='Oranges')
                fig_r2.update_layout(height=ALTURA_GRAFICO, margin=dict(l=0, r=0, t=30, b=0), coloraxis_showscale=False)
                st.plotly_chart(fig_r2, use_container_width=True)

# ============================================================================
# PÁGINA 3: TOP E FLOP REGIONAIS
# ============================================================================
elif pagina == "🏆 Top e Flop Regionais":
    st.markdown("### 🏆 Painel de Excelência Regional")
    
    colunas_exibir = ['IES_Campus', 'Tipo_IES', 'Percentual_Proficiencia', 'Rank_Nacional']
    
    def processar_regiao(df_regiao, nome_regiao):
        df_val = df_regiao.dropna(subset=['Percentual_Proficiencia']).copy()
        if len(df_val) < 2: return None, None, 0, 0
        lim_sup = df_val['Percentual_Proficiencia'].quantile(0.70)
        lim_inf = df_val['Percentual_Proficiencia'].quantile(0.30)
        melhores = df_val[df_val['Percentual_Proficiencia'] >= lim_sup].sort_values('Percentual_Proficiencia', ascending=False).head(10)
        piores = df_val[df_val['Percentual_Proficiencia'] <= lim_inf].sort_values('Percentual_Proficiencia', ascending=True).head(10)
        return melhores, piores, lim_sup, lim_inf

    m_r1, p_r1, sup_r1, inf_r1 = processar_regiao(df_r1, regiao_1)
    if m_r1 is not None:
        st.markdown(f"**📍 {regiao_1}**")
        c1, c2 = st.columns(2)
        with c1: 
            st.dataframe(m_r1[colunas_exibir].style.format({'Percentual_Proficiencia': '{:.1f}%', 'Rank_Nacional': '{:.0f}'})
                         .background_gradient(subset=['Percentual_Proficiencia'], cmap='Blues', vmin=0, vmax=100), 
                         use_container_width=True, hide_index=True)
        with c2: 
            # Usando Reds_r (Reverso), notas menores ficam BEM vermelhas, notas maiores (perto de 100) ficariam brancas
            st.dataframe(p_r1[colunas_exibir].style.format({'Percentual_Proficiencia': '{:.1f}%', 'Rank_Nacional': '{:.0f}'})
                         .background_gradient(subset=['Percentual_Proficiencia'], cmap='Reds_r', vmin=0, vmax=100), 
                         use_container_width=True, hide_index=True)

    if regiao_1 != regiao_2:
        m_r2, p_r2, sup_r2, inf_r2 = processar_regiao(df_r2, regiao_2)
        if m_r2 is not None:
            st.markdown(f"**⚖️ {regiao_2}**")
            c3, c4 = st.columns(2)
            with c3: 
                st.dataframe(m_r2[colunas_exibir].style.format({'Percentual_Proficiencia': '{:.1f}%', 'Rank_Nacional': '{:.0f}'})
                             .background_gradient(subset=['Percentual_Proficiencia'], cmap='Greens', vmin=0, vmax=100), 
                             use_container_width=True, hide_index=True)
            with c4: 
                st.dataframe(p_r2[colunas_exibir].style.format({'Percentual_Proficiencia': '{:.1f}%', 'Rank_Nacional': '{:.0f}'})
                             .background_gradient(subset=['Percentual_Proficiencia'], cmap='Oranges_r', vmin=0, vmax=100), 
                             use_container_width=True, hide_index=True)

# ============================================================================
# PÁGINA 4: RANK NACIONAL
# ============================================================================
elif pagina == "🏅 Rank Nacional (Top & Bottom 30)":
    st.markdown("### 🏅 Elite e Alerta Nacional")
    st.markdown("Visão completa das 30 instituições com maior e menor proficiência em todo o território nacional.")

    df_nacional = df_raw.dropna(subset=['Percentual_Proficiencia']).copy()
    colunas_exibir_nacional = ['Rank_Nacional', 'IES_Campus', 'Regiao', 'Percentual_Proficiencia', 'Faixa_Enade']

    tab_top, tab_bottom = st.tabs(["🌟 Top 30 Nacional", "⚠️ Bottom 30 Nacional"])

    with tab_top:
        top_30 = df_nacional.sort_values('Percentual_Proficiencia', ascending=False).head(30)
        st.dataframe(
            top_30[colunas_exibir_nacional].style.format({'Percentual_Proficiencia': '{:.1f}%', 'Rank_Nacional': '{:.0f}'})
            .background_gradient(subset=['Percentual_Proficiencia'], cmap='Blues', vmin=0, vmax=100),
            use_container_width=True, hide_index=True, height=800
        )

    with tab_bottom:
        bottom_30 = df_nacional.sort_values('Percentual_Proficiencia', ascending=True).head(30)
        st.dataframe(
            bottom_30[colunas_exibir_nacional].style.format({'Percentual_Proficiencia': '{:.1f}%', 'Rank_Nacional': '{:.0f}'})
            .background_gradient(subset=['Percentual_Proficiencia'], cmap='Reds_r', vmin=0, vmax=100),
            use_container_width=True, hide_index=True, height=800
        )

# ============================================================================
# PÁGINA 5: COMPARAÇÃO HISTÓRICA ENTRE ANOS
# ============================================================================
elif pagina == "📈 Comparação Histórica (2016 e 2025)":
    st.markdown("### 📈 Evolução Histórica do ENADE (2016 → 2025)")
    st.markdown("Comparação do desempenho ao longo dos anos para identificar evolução, queda ou estabilidade.")

    path_2016 = "src/data/conceito-enade-2016-medicina(PLANILHA_ENADE).csv"

    # Carregamento
    df_2016 = carregar_dados(path_2016)
    df_2025 = carregar_dados(caminho_arquivo)

    # Adiciona coluna de ano
    df_2016['Ano'] = 2016
    df_2025['Ano'] = 2025

    # Junta tudo
    df_all = pd.concat([df_2016, df_2025], ignore_index=True)

    if df_all.empty:
        st.error("Erro ao carregar dados históricos.")
        st.stop()

    # Remove vazios
    df_all = df_all.dropna(subset=['Percentual_Proficiencia'])

    # =========================
    # MÉTRICAS GERAIS
    # =========================
    st.markdown("#### 📊 Visão Geral por Ano")

    media_por_ano = df_all.groupby('Ano')['Percentual_Proficiencia'].mean().reset_index()

    col1, col2, col3 = st.columns(3)

    anos = sorted(media_por_ano['Ano'].unique())

    for i, ano in enumerate(anos):
        valor = media_por_ano[media_por_ano['Ano'] == ano]['Percentual_Proficiencia'].values[0]
        [col1, col2, col3][i].metric(f"Média {ano}", f"{valor:.1f}%")

    st.markdown("---")

    # =========================
    # EVOLUÇÃO AO LONGO DO TEMPO
    # =========================
    st.markdown("#### 📈 Evolução da Proficiência Média")

    import plotly.express as px

    fig_linha = px.line(
        media_por_ano,
        x='Ano',
        y='Percentual_Proficiencia',
        markers=True,
        title="Evolução Nacional da Proficiência"
    )

    fig_linha.update_layout(height=400)
    st.plotly_chart(fig_linha, use_container_width=True)

    # =========================
    # COMPARAÇÃO POR REGIÃO
    # =========================
    st.markdown("#### 🗺️ Comparação por Região")

    df_regiao = df_all.groupby(['Ano', 'Regiao'])['Percentual_Proficiencia'].mean().reset_index()

    fig_regiao = px.bar(
        df_regiao,
        x='Regiao',
        y='Percentual_Proficiencia',
        color='Ano',
        barmode='group',
        title="Média por Região ao Longo dos Anos"
    )

    fig_regiao.update_layout(height=400)
    st.plotly_chart(fig_regiao, use_container_width=True)

    # =========================
    # EVOLUÇÃO POR TIPO (Pública vs Privada)
    # =========================
    st.markdown("#### 🏛️ Pública vs Privada ao Longo do Tempo")

    df_tipo = df_all.groupby(['Ano', 'Tipo_IES'])['Percentual_Proficiencia'].mean().reset_index()

    fig_tipo = px.line(
        df_tipo,
        x='Ano',
        y='Percentual_Proficiencia',
        color='Tipo_IES',
        markers=True,
        title="Evolução por Tipo de Instituição"
    )

    fig_tipo.update_layout(height=400)
    st.plotly_chart(fig_tipo, use_container_width=True)