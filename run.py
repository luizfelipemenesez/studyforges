
"""
Arquivo: run.py
Papel no sistema: Ponto de entrada principal (entrypoint) da aplicação.
Comunica-se com: app/__init__.py (importa a função create_app).

Como usar:
Com o ambiente virtual ativado, execute no terminal:
    python run.py
"""

import sys

from app import create_app
from app.config import Config

# Chamamos a função fábrica que monta toda a aplicação Flask,
# registra as rotas e garante que o banco de dados SQLite exista.
app = create_app()

if __name__ == "__main__":
    # Exibe instruções claras no terminal para o desenvolvedor iniciante.
    print("=" * 60)
    print("StudyForge iniciado com sucesso.")
    print("Acesse no seu navegador: http://127.0.0.1:5000")
    print(f"Python em uso: {sys.executable}")
    print(f"Arquivo .env: {Config.ENV_FILE}")
    print(f"GEMINI_API_KEY carregada: {'sim' if Config.GEMINI_API_KEY else 'não'}")
    print("Para encerrar o servidor, pressione CTRL + C no terminal.")
    print("=" * 60)

    # Inicia o servidor web local na porta 5000.
    # debug=True reinicia o servidor automaticamente quando você salva um arquivo.
    app.run(host="127.0.0.1", port=5000, debug=True)
