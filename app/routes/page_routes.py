
"""
Arquivo: app/routes/page_routes.py
Papel no sistema: Define as rotas que entregam páginas HTML completas ao navegador.
Comunica-se com:
  - app/templates/index.html e app/templates/quiz.html
  - app/__init__.py (onde este Blueprint é registrado)
"""

from flask import Blueprint, render_template

# Cria o Blueprint responsável pelas telas visuais da aplicação.
page_bp = Blueprint("pages", __name__)


@page_bp.route("/")
def pagina_inicial():
    """
    Renderiza a tela inicial (Dashboard) com o editor de anotações
    e a biblioteca lateral de cadernos salvos.
    """
    return render_template("index.html")


@page_bp.route("/quiz/<int:caderno_id>")
def pagina_quiz(caderno_id: int):
    """
    Renderiza a tela de resolução do simulado para um caderno específico.

    Parâmetros:
        caderno_id (int): ID do caderno recebido pela URL (ex.: /quiz/3).
    """
    return render_template("quiz.html", caderno_id=caderno_id, modo_gabarito=False)


@page_bp.route("/gabarito/<int:caderno_id>")
def pagina_gabarito(caderno_id: int):
    """
    Renderiza o gabarito comentado de um caderno sem iniciar o simulado.

    Parâmetros:
        caderno_id (int): ID do caderno recebido pela URL.
    """
    return render_template("quiz.html", caderno_id=caderno_id, modo_gabarito=True)
