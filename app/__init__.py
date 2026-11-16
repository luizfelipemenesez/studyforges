
"""
Arquivo: app/__init__.py
Papel no sistema: Fábrica da aplicação Flask (Application Factory).
Comunica-se com:
  - app/config.py (carrega configurações)
  - app/database.py (cria as tabelas do SQLite na inicialização)
  - app/routes/page_routes.py (registra rotas de páginas HTML)
  - app/routes/api_routes.py (registra rotas de API JSON)
"""

from flask import Flask
from app.config import Config
from app.database import inicializar_banco
from app.routes.page_routes import page_bp
from app.routes.api_routes import api_bp


def create_app() -> Flask:
    """
    Cria, configura e retorna a instância principal da aplicação Flask.

    Retorna:
        Flask: Objeto da aplicação pronto para receber requisições HTTP.
    """
    # Cria a instância do Flask. Como este arquivo está dentro da pasta "app/",
    # o Flask encontra automaticamente "app/templates/" e "app/static/".
    app = Flask(__name__)

    # Carrega as configurações definidas na classe Config (como SECRET_KEY).
    app.config.from_object(Config)

    # Garante que o arquivo do banco SQLite e suas tabelas existam antes
    # de qualquer usuário acessar o sistema.
    inicializar_banco()

    # Registra os Blueprints (grupos organizados de rotas).
    # page_bp entrega HTML; api_bp entrega dados em formato JSON.
    app.register_blueprint(page_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
