
"""
Arquivo: app/config.py
Papel no sistema: Centraliza a leitura de variáveis de ambiente e caminhos do projeto.
Comunica-se com:
  - Arquivo .env na raiz do projeto
  - app/__init__.py, app/database.py e app/services/ai_generator.py
"""

import os
from pathlib import Path
from dotenv import dotenv_values, load_dotenv

# Descobre o caminho absoluto da pasta raiz do projeto (um nível acima de "app/").
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
GEMINI_API_KEY_PLACEHOLDER = "cole_sua_chave_api_do_gemini_aqui"

# Carrega as variáveis definidas no arquivo ".env" para a memória do sistema.
load_dotenv(ENV_FILE)

# Uma variável herdada vazia ou com o valor de exemplo impede o carregamento padrão do .env.
chave_herdada = os.getenv("GEMINI_API_KEY", "").strip()
if not chave_herdada or chave_herdada == GEMINI_API_KEY_PLACEHOLDER:
    chave_do_arquivo = (dotenv_values(ENV_FILE).get("GEMINI_API_KEY") or "").strip()
    if chave_do_arquivo and chave_do_arquivo != GEMINI_API_KEY_PLACEHOLDER:
        os.environ["GEMINI_API_KEY"] = chave_do_arquivo


class Config:
    """
    Classe que guarda as configurações globais do StudyForge.
    """

    # Chave secreta usada pelo Flask para proteger cookies e sessões.
    SECRET_KEY = os.getenv("SECRET_KEY", "studyforge-chave-desenvolvimento")

    # Chave da API do Google Gemini lida do arquivo .env.
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_API_KEY_PLACEHOLDER = GEMINI_API_KEY_PLACEHOLDER
    ENV_FILE = str(ENV_FILE)

    # Caminho completo onde o arquivo do banco de dados SQLite será salvo.
    DATABASE_PATH = str(BASE_DIR / "studyforge.db")

    # Tamanho máximo permitido para upload de arquivos (10 Megabytes).
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
