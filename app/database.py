
"""
Arquivo: app/database.py
Papel no sistema: Gerencia a conexão com o SQLite e cria a estrutura das tabelas.
Comunica-se com:
  - app/config.py (obtém o caminho do arquivo studyforge.db)
  - app/__init__.py (executa inicializar_banco() ao iniciar o servidor)
  - app/models/study_model.py (fornece conexões abertas via obter_conexao())
"""

import sqlite3
from app.config import Config


def obter_conexao() -> sqlite3.Connection:
    """
    Abre e retorna uma conexão com o banco de dados SQLite.

    Retorna:
        sqlite3.Connection: Conexão configurada para retornar linhas como dicionários.
    """
    # Conecta ao arquivo studyforge.db (se o arquivo não existir, o SQLite cria).
    conexao = sqlite3.connect(Config.DATABASE_PATH)

    # Configura o row_factory para permitir acessar colunas pelo nome
    # (ex.: linha["titulo"]) em vez de apenas por índice numérico (linha[1]).
    conexao.row_factory = sqlite3.Row

    # Ativa o suporte a chaves estrangeiras (FOREIGN KEY) no SQLite,
    # garantindo que questões e tentativas fiquem ligadas a um caderno válido.
    conexao.execute("PRAGMA foreign_keys = ON;")

    return conexao


def inicializar_banco() -> None:
    """
    Cria as tabelas 'cadernos', 'questoes' e 'tentativas' caso ainda não existam.
    É seguro rodar esta função toda vez que o servidor inicia (IF NOT EXISTS).
    """
    conexao = obter_conexao()
    cursor = conexao.cursor()

    # 1. Tabela CADERNOS: guarda cada material de estudo enviado pelo usuário.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cadernos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            materia_detectada TEXT NOT NULL,
            conteudo_original TEXT NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Tabela QUESTOES: guarda as questões geradas para cada caderno.
    # ON DELETE CASCADE apaga automaticamente as questões se o caderno for excluído.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caderno_id INTEGER NOT NULL,
            enunciado TEXT NOT NULL,
            tipo TEXT NOT NULL,
            dificuldade TEXT NOT NULL,
            topico TEXT NOT NULL,
            alternativas_json TEXT NOT NULL,
            resposta_correta INTEGER NOT NULL,
            explicacao_detalhada TEXT NOT NULL,
            fonte_url TEXT NOT NULL,
            FOREIGN KEY (caderno_id) REFERENCES cadernos (id) ON DELETE CASCADE
        );
    """)

    # 3. Tabela TENTATIVAS: registra o histórico de pontuações do usuário.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tentativas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            caderno_id INTEGER NOT NULL,
            acertos INTEGER NOT NULL,
            total_questoes INTEGER NOT NULL,
            percentual REAL NOT NULL,
            realizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (caderno_id) REFERENCES cadernos (id) ON DELETE CASCADE
        );
    """)

    # Confirma (salva) as alterações no arquivo do banco e fecha a conexão.
    conexao.commit()
    conexao.close()
