#!/usr/bin/env python3
"""
Script para iniciar a interface web do docbr-rag.
Uso: python run_web_ui.py [--port 8501] [--host localhost]
"""

import sys
import argparse
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from docbr_rag.web_ui import main
from docbr_rag.logging_config import setup_logging


def parse_args():
    """Parse argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description="Inicia interface web do docbr-rag",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python run_web_ui.py                    # Porta padrão 8501
  python run_web_ui.py --port 8080       # Porta customizada
  python run_web_ui.py --host 0.0.0.0    # Acessível externamente
        """
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Porta para a interface web (padrão: 8501)"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host para a interface web (padrão: localhost)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Nível de log (padrão: INFO)"
    )
    
    parser.add_argument(
        "--server.headless",
        action="store_true",
        help="Executa em modo headless (sem abrir navegador)"
    )
    
    parser.add_argument(
        "--server.port",
        type=int,
        default=8501,
        help=argparse.SUPPRESS  # Para compatibilidade com streamlit run
    )
    
    parser.add_argument(
        "--server.address",
        type=str,
        default="localhost",
        help=argparse.SUPPRESS  # Para compatibilidade com streamlit run
    )
    
    return parser.parse_args()


def main_script():
    """Função principal do script."""
    args = parse_args()
    
    # Configura logging
    setup_logging(level=args.log_level)
    
    # Configura variáveis de ambiente para Streamlit
    import os
    os.environ["STREAMLIT_SERVER_PORT"] = str(args.port)
    os.environ["STREAMLIT_SERVER_ADDRESS"] = args.host
    os.environ["STREAMLIT_SERVER_HEADLESS"] = str(args.server_headless)
    
    print(f"🚀 Iniciando interface web do docbr-rag...")
    print(f"📍 URL: http://{args.host}:{args.port}")
    print(f"📊 Log level: {args.log_level}")
    print(f"🔧 Headless: {args.server_headless}")
    print("-" * 50)
    
    try:
        # Importa e executa o Streamlit
        import streamlit.web.cli as stcli
        
        # Simula argumentos de linha de comando do Streamlit
        sys.argv = [
            "streamlit",
            "run",
            "src/docbr_rag/web_ui.py",
            f"--server.port={args.port}",
            f"--server.address={args.host}",
            f"--server.headless={args.server_headless}",
            "--logger.level", args.log_level,
            "--browser.gatherUsageStats", "false"
        ]
        
        # Executa a aplicação Streamlit
        stcli.main()
        
    except KeyboardInterrupt:
        print("\n👋 Interface web encerrada pelo usuário.")
    except Exception as e:
        print(f"❌ Erro ao iniciar interface web: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main_script()
