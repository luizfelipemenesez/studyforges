
"""
Arquivo: app/routes/api_routes.py
Papel no sistema: Define os endpoints REST (API JSON) que o frontend JavaScript
consome para criar simulados, listar cadernos, registrar notas e excluir registros.
Comunica-se com:
  - app/services/file_parser.py
  - app/services/web_search.py
  - app/services/ai_generator.py
  - app/models/study_model.py
"""

from flask import Blueprint, jsonify, request
from app.services.file_parser import extrair_texto_de_arquivo
from app.services.web_search import buscar_referencias_web
from app.services.ai_generator import (
    gerar_simulado_estruturado,
    GeminiTemporariamenteIndisponivelError,
)
from app.models.study_model import (
    salvar_caderno_com_questoes,
    listar_cadernos,
    buscar_caderno_por_id,
    registrar_tentativa,
    excluir_caderno,
)

# Cria o Blueprint da API. No app/__init__.py ele recebe o prefixo "/api".
api_bp = Blueprint("api", __name__)


@api_bp.route("/cadernos", methods=["GET"])
def api_listar_cadernos():
    """
    GET /api/cadernos
    Retorna a lista de todos os cadernos salvos no banco SQLite.
    """
    try:
        cadernos = listar_cadernos()
        return jsonify({"sucesso": True, "cadernos": cadernos}), 200
    except Exception as erro:
        return jsonify({"sucesso": False, "erro": f"Erro ao listar cadernos: {str(erro)}"}), 500


@api_bp.route("/cadernos/<int:caderno_id>", methods=["GET"])
def api_obter_caderno(caderno_id: int):
    """
    GET /api/cadernos/<id>
    Retorna um caderno específico e todas as suas questões para iniciar o quiz.
    """
    try:
        caderno = buscar_caderno_por_id(caderno_id)
        if not caderno:
            return jsonify({"sucesso": False, "erro": "Caderno não encontrado."}), 404

        return jsonify({"sucesso": True, "caderno": caderno}), 200
    except Exception as erro:
        return jsonify({"sucesso": False, "erro": f"Erro ao carregar caderno: {str(erro)}"}), 500


@api_bp.route("/cadernos/gerar", methods=["POST"])
def api_gerar_caderno():
    """
    POST /api/cadernos/gerar
    Recebe anotações (texto colado e/ou arquivo anexo), busca referências na web,
    gera as questões no Gemini e salva tudo no SQLite.
    """
    try:
        # 1. Lê os campos enviados pelo FormData do JavaScript.
        texto_digitado = request.form.get("texto_anotacao", "").strip()
        quantidade = int(request.form.get("quantidade", 5))
        dificuldade = request.form.get("dificuldade", "Misto").strip()
        usar_busca_web = request.form.get("usar_busca_web", "true").lower() == "true"

        # Garante que a quantidade fique dentro de limites seguros (entre 3 e 15).
        quantidade = max(3, min(15, quantidade))

        # 2. Verifica se o usuário anexou um arquivo (.txt, .md ou .pdf).
        texto_arquivo = ""
        arquivo = request.files.get("arquivo")
        if arquivo and arquivo.filename:
            texto_arquivo = extrair_texto_de_arquivo(arquivo)

        # Combina o texto colado com o texto extraído do arquivo (se ambos existirem).
        partes_texto = [p for p in [texto_digitado, texto_arquivo] if p]
        texto_final = "\n\n".join(partes_texto).strip()

        if len(texto_final) < 30:
            return jsonify({
                "sucesso": False,
                "erro": "Insira pelo menos 30 caracteres de anotações ou envie um arquivo válido."
            }), 400

        # 3. Busca referências complementares na web (se a opção estiver marcada).
        referencias_web = []
        if usar_busca_web:
            referencias_web = buscar_referencias_web(texto_final)

        # 4. Gera o título, detecta a matéria e cria as questões via Gemini.
        simulado = gerar_simulado_estruturado(
            texto_anotacao=texto_final,
            referencias_web=referencias_web,
            quantidade=quantidade,
            dificuldade=dificuldade,
        )

        # 5. Salva o caderno e as questões no banco SQLite.
        caderno_id = salvar_caderno_com_questoes(
            titulo=simulado["titulo_sugerido"],
            materia_detectada=simulado["materia_detectada"],
            conteudo_original=texto_final,
            questoes=simulado["questoes"],
        )

        return jsonify({
            "sucesso": True,
            "caderno_id": caderno_id,
            "titulo": simulado["titulo_sugerido"],
            "materia": simulado["materia_detectada"],
        }), 201

    except GeminiTemporariamenteIndisponivelError as erro_temporario:
        return jsonify({"sucesso": False, "erro": str(erro_temporario)}), 503

    except ValueError as erro_validacao:
        # Erros esperados (ex.: arquivo vazio, chave de API ausente).
        return jsonify({"sucesso": False, "erro": str(erro_validacao)}), 400

    except Exception as erro_interno:
        # Erros inesperados de rede ou servidor.
        return jsonify({
            "sucesso": False,
            "erro": f"Falha ao gerar o simulado: {str(erro_interno)}"
        }), 500


@api_bp.route("/cadernos/<int:caderno_id>/tentativas", methods=["POST"])
def api_salvar_tentativa(caderno_id: int):
    """
    POST /api/cadernos/<id>/tentativas
    Salva a pontuação obtida pelo usuário ao finalizar um simulado.
    """
    try:
        dados = request.get_json(silent=True) or {}
        acertos = int(dados.get("acertos", 0))
        total_questoes = int(dados.get("total_questoes", 0))

        if total_questoes <= 0:
            return jsonify({"sucesso": False, "erro": "Total de questões inválido."}), 400

        resultado = registrar_tentativa(caderno_id, acertos, total_questoes)
        return jsonify({"sucesso": True, "resultado": resultado}), 201

    except Exception as erro:
        return jsonify({"sucesso": False, "erro": f"Erro ao salvar pontuação: {str(erro)}"}), 500


@api_bp.route("/cadernos/<int:caderno_id>", methods=["DELETE"])
def api_excluir_caderno(caderno_id: int):
    """
    DELETE /api/cadernos/<id>
    Exclui um caderno e todo o seu histórico do banco de dados.
    """
    try:
        removido = excluir_caderno(caderno_id)
        if not removido:
            return jsonify({"sucesso": False, "erro": "Caderno não encontrado."}), 404

        return jsonify({"sucesso": True}), 200
    except Exception as erro:
        return jsonify({"sucesso": False, "erro": f"Erro ao excluir caderno: {str(erro)}"}), 500
