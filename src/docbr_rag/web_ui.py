"""
Interface Web para docbr-rag usando Streamlit.
Interface intuitiva para upload, indexação e consulta de documentos.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import time
from typing import List, Dict, Any
import plotly.express as px
import plotly.graph_objects as go

from .core import DocBR
from .models import TipoDocumento, DocumentoInfo, Resposta
from .config import load_config
from .logging_config import setup_logging, get_logger


def init_session_state():
    """Inicializa estado da sessão Streamlit."""
    if 'docbr_instance' not in st.session_state:
        st.session_state.docbr_instance = None
    if 'documentos_indexados' not in st.session_state:
        st.session_state.documentos_indexados = []
    if 'historico_consultas' not in st.session_state:
        st.session_state.historico_consultas = []


def setup_page_config():
    """Configura página Streamlit."""
    st.set_page_config(
        page_title="docbr-rag",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded"
    )


def render_sidebar():
    """Renderiza barra lateral com configurações."""
    st.sidebar.title("⚙️ Configurações")
    
    # Configurações do modelo
    with st.sidebar.expander("🤖 Modelos", expanded=True):
        embedding_model = st.sidebar.selectbox(
            "Modelo de Embeddings",
            ["all-MiniLM-L6-v2", "paraphrase-multilingual-MiniLM-L12-v2"],
            index=0,
            help="Modelo para gerar embeddings semânticos"
        )
        
        llm_model = st.sidebar.selectbox(
            "Modelo LLM",
            ["llama3.2:3b", "llama3.2:1b", "gemma:2b"],
            index=0,
            help="Modelo de linguagem para geração de respostas"
        )
    
    # Configurações de processamento
    with st.sidebar.expander("📊 Processamento", expanded=False):
        chunk_size = st.sidebar.slider(
            "Tamanho do Chunk",
            min_value=100,
            max_value=2000,
            value=500,
            step=50,
            help="Tamanho dos pedaços de texto"
        )
        
        chunk_overlap = st.sidebar.slider(
            "Sobreposição",
            min_value=0,
            max_value=500,
            value=100,
            step=25,
            help="Sobreposição entre chunks"
        )
        
        n_resultados = st.sidebar.slider(
            "Resultados da Busca",
            min_value=1,
            max_value=20,
            value=5,
            step=1,
            help="Número de chunks recuperados"
        )
    
    # Configurações do banco de dados
    with st.sidebar.expander("💾 Banco de Dados", expanded=False):
        db_path = st.sidebar.text_input(
            "Caminho do DB",
            value="./docbr_web_db",
            help="Caminho para o banco de dados vetorial"
        )
        
        if st.sidebar.button("🔄 Limpar Banco de Dados"):
            if st.session_state.docbr_instance:
                st.session_state.docbr_instance.limpar_database()
                st.session_state.documentos_indexados = []
                st.sidebar.success("Banco de dados limpo!")
                time.sleep(1)
                st.rerun()
    
    # Botão para inicializar/atualizar instância
    if st.sidebar.button("🚀 Inicializar Sistema", type="primary"):
        try:
            with st.spinner("Inicializando sistema..."):
                st.session_state.docbr_instance = DocBR(
                    model_name=embedding_model,
                    llm_model=llm_model,
                    db_path=db_path,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
                
                # Carrega documentos já indexados
                st.session_state.documentos_indexados = st.session_state.docbr_instance.listar_documentos()
            
            st.sidebar.success("Sistema inicializado com sucesso!")
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.sidebar.error(f"Erro ao inicializar: {e}")
    
    return {
        'n_resultados': n_resultados,
        'embedding_model': embedding_model,
        'llm_model': llm_model
    }


def render_upload_section():
    """Renderiza seção de upload de documentos."""
    st.header("📤 Upload de Documentos")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_files = st.file_uploader(
            "Arraste arquivos ou clique para selecionar",
            type=['pdf', 'docx', 'txt'],
            accept_multiple_files=True,
            help="Suporta PDF, DOCX e TXT"
        )
    
    with col2:
        st.info("📋 **Formatos suportados:**\n- PDF\n- DOCX\n- TXT")
    
    if uploaded_files and st.session_state.docbr_instance:
        if st.button("📥 Indexar Documentos", type="primary"):
            with st.spinner("Indexando documentos..."):
                progress_bar = st.progress(0)
                documentos_indexados = []
                
                for i, uploaded_file in enumerate(uploaded_files):
                    # Salva arquivo temporário
                    temp_path = Path(f"temp_{uploaded_file.name}")
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    try:
                        # Indexa documento
                        doc_info = st.session_state.docbr_instance.indexar_documento(temp_path)
                        documentos_indexados.append(doc_info)
                        
                        # Remove arquivo temporário
                        temp_path.unlink()
                        
                    except Exception as e:
                        st.error(f"Erro ao indexar {uploaded_file.name}: {e}")
                    
                    # Atualiza progresso
                    progress = (i + 1) / len(uploaded_files)
                    progress_bar.progress(progress)
                
                # Atualiza estado
                st.session_state.documentos_indexados.extend(documentos_indexados)
                
                progress_bar.empty()
                st.success(f"✅ {len(documentos_indexados)} documentos indexados com sucesso!")
                
                # Limpa arquivos temporários restantes
                for temp_file in Path(".").glob("temp_*"):
                    temp_file.unlink()


def render_documents_section():
    """Renderiza seção de documentos indexados."""
    st.header("📚 Documentos Indexados")
    
    if not st.session_state.documentos_indexados:
        st.info("📭 Nenhum documento indexado ainda. Faça upload na seção acima.")
        return
    
    # Estatísticas
    col1, col2, col3, col4 = st.columns(4)
    
    total_docs = len(st.session_state.documentos_indexados)
    total_paginas = sum(doc.total_paginas for doc in st.session_state.documentos_indexados)
    total_chunks = sum(doc.total_chunks for doc in st.session_state.documentos_indexados)
    
    with col1:
        st.metric("📄 Documentos", total_docs)
    with col2:
        st.metric("📖 Páginas", total_paginas)
    with col3:
        st.metric("🧩 Chunks", total_chunks)
    with col4:
        st.metric("💾 Tamanho DB", f"{total_chunks * 0.5:.1f}KB")
    
    # Gráfico de tipos de documentos
    tipos_count = {}
    for doc in st.session_state.documentos_indexados:
        tipo = doc.tipo.value
        tipos_count[tipo] = tipos_count.get(tipo, 0) + 1
    
    if tipos_count:
        fig = px.pie(
            values=list(tipos_count.values()),
            names=list(tipos_count.keys()),
            title="Distribuição por Tipo"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Tabela de documentos
    st.subheader("📋 Lista de Documentos")
    
    # Prepara dados para tabela
    dados_tabela = []
    for doc in st.session_state.documentos_indexados:
        dados_tabela.append({
            "Tipo": doc.tipo.value.upper(),
            "Arquivo": Path(doc.caminho).name,
            "Páginas": doc.total_paginas,
            "Chunks": doc.total_chunks,
            "Status": "✅ Indexado" if doc.indexado else "⏳ Processando"
        })
    
    df = pd.DataFrame(dados_tabela)
    st.dataframe(df, use_container_width=True)


def render_query_section(config):
    """Renderiza seção de consulta."""
    st.header("🔍 Consultar Documentos")
    
    if not st.session_state.docbr_instance or not st.session_state.documentos_indexados:
        st.warning("⚠️ Indexe alguns documentos antes de fazer consultas.")
        return
    
    # Histórico de consultas
    if st.session_state.historico_consultas:
        with st.expander("📜 Histórico de Consultas", expanded=False):
            for i, consulta in enumerate(reversed(st.session_state.historico_consultas[-5:])):
                with st.chat_message(consulta["role"], avatar="🧑" if consulta["role"] == "user" else "🤖"):
                    st.write(consulta["content"])
                    if "resposta" in consulta:
                        st.info(f"📄 Fontes: {consulta['resposta'].paginas_referenciadas}")
                        st.info(f"🎯 Confiança: {consulta['resposta'].confianca:.2f}")
    
    # Formulário de consulta
    with st.form("query_form"):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            pergunta = st.text_input(
                "💭 Faça sua pergunta sobre os documentos:",
                placeholder="Ex: Qual o valor total dos contratos indexados?",
                help="Seja específico para melhores resultados"
            )
        
        with col2:
            st.write("")  # Espaçamento
            submitted = st.form_submit_button("🔎 Consultar", type="primary")
        
        # Opções avançadas
        with st.expander("⚙️ Opções Avançadas", expanded=False):
            temperatura = st.slider(
                "Temperatura (Criatividade)",
                min_value=0.0,
                max_value=2.0,
                value=0.7,
                step=0.1,
                help="Valores mais altos = mais criatividade"
            )
            
            incluir_fonte = st.checkbox("📄 Incluir fontes na resposta", value=True)
            incluir_confianca = st.checkbox("🎯 Incluir confiança", value=True)
    
    if submitted and pergunta and st.session_state.docbr_instance:
        with st.spinner("🔍 Buscando informações..."):
            try:
                # Adiciona consulta ao histórico
                st.session_state.historico_consultas.append({
                    "role": "user",
                    "content": pergunta,
                    "timestamp": time.time()
                })
                
                # Realiza consulta
                resposta = st.session_state.docbr_instance.consultar(
                    pergunta=pergunta,
                    n_resultados=config['n_resultados'],
                    temperatura=temperatura
                )
                
                # Adiciona resposta ao histórico
                st.session_state.historico_consultas.append({
                    "role": "assistant",
                    "content": resposta.texto,
                    "resposta": resposta,
                    "timestamp": time.time()
                })
                
                # Exibe resposta
                st.success("✅ Resposta gerada com sucesso!")
                
                # Resposta principal
                st.markdown("### 🤖 Resposta")
                st.write(resposta.texto)
                
                # Metadados da resposta
                col1, col2 = st.columns(2)
                with col1:
                    if incluir_fonte and resposta.paginas_referenciadas:
                        st.info(f"📄 **Fontes:** Páginas {', '.join(map(str, resposta.paginas_referenciadas))}")
                
                with col2:
                    if incluir_confianca and resposta.confianca is not None:
                        # Indicador visual de confiança
                        confianca = resposta.confianca
                        if confianca >= 0.8:
                            cor = "🟢"
                            texto = "Alta"
                        elif confianca >= 0.5:
                            cor = "🟡"
                            texto = "Média"
                        else:
                            cor = "🔴"
                            texto = "Baixa"
                        
                        st.info(f"🎯 **Confiança:** {cor} {texto} ({confianca:.2f})")
                
                # Contexto usado
                with st.expander("📚 Contexto Utilizado", expanded=False):
                    st.info("Trechos dos documentos que foram usados para gerar esta resposta:")
                    # Aqui poderíamos mostrar os chunks recuperados
                    st.write("*(Contexto não disponível nesta versão da interface)*")
                
            except Exception as e:
                st.error(f"❌ Erro na consulta: {e}")


def render_analytics_section():
    """Renderiza seção de analytics e métricas."""
    st.header("📊 Analytics")
    
    if not st.session_state.historico_consultas:
        st.info("📭 Nenhuma consulta realizada ainda.")
        return
    
    # Estatísticas de consultas
    consultas_usuario = [c for c in st.session_state.historico_consultas if c["role"] == "user"]
    consultas_assistente = [c for c in st.session_state.historico_consultas if c["role"] == "assistant"]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💬 Consultas", len(consultas_usuario))
    with col2:
        st.metric("🤖 Respostas", len(consultas_assistente))
    with col3:
        if consultas_assistente:
            confianca_media = sum(c["resposta"].confianca for c in consultas_assistente if "resposta" in c and c["resposta"].confianca) / len(consultas_assistente)
            st.metric("🎯 Confiança Média", f"{confianca_media:.2f}")
    
    # Timeline de consultas
    if consultas_usuario:
        st.subheader("📈 Timeline de Consultas")
        
        timestamps = [c["timestamp"] for c in consultas_usuario]
        perguntas = [c["content"][:50] + "..." if len(c["content"]) > 50 else c["content"] for c in consultas_usuario]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=timestamps,
            y=[1] * len(timestamps),
            mode='markers+lines',
            text=perguntas,
            hovertemplate='<b>%{text}</b><br>%{x}<extra></extra>',
            name='Consultas'
        ))
        
        fig.update_layout(
            title="Consultas ao Longo do Tempo",
            xaxis_title="Tempo",
            yaxis_title="",
            showlegend=False,
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)


def main():
    """Função principal da aplicação Streamlit."""
    setup_page_config()
    init_session_state()
    
    # Título e descrição
    st.title("📄 docbr-rag")
    st.markdown("*RAG especializado em documentos brasileiros — 100% local e gratuito*")
    
    # Verifica se o sistema está inicializado
    if st.session_state.docbr_instance is None:
        st.warning("⚠️ **Sistema não inicializado!** Use a barra lateral para configurar e inicializar o sistema.")
        st.info("👈 **Configure o sistema na barra lateral →**")
        return
    
    # Renderiza seções
    config = render_sidebar()
    
    # Abas
    tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload", "📚 Documentos", "🔍 Consultar", "📊 Analytics"])
    
    with tab1:
        render_upload_section()
    
    with tab2:
        render_documents_section()
    
    with tab3:
        render_query_section(config)
    
    with tab4:
        render_analytics_section()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "🚀 **docbr-rag** - RAG para documentos brasileiros | "
        "<a href='https://github.com/seu-usuario/docbr-rag' target='_blank'>GitHub</a>"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    # Configura logging
    setup_logging(level="INFO")
    
    # Inicia aplicação
    main()
