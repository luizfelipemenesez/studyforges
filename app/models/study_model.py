
"""
Arquivo: app/models/study_model.py
Papel no sistema: Camada de acesso a dados (Data Access Layer).
Contém todas as funções SQL para salvar, listar e excluir cadernos, questões e notas.
Comunica-se com:
  - app/database.py (abre conexões com o SQLite)
  - app/routes/api_routes.py (chamado pelas rotas REST)
"""

import json
from typing import Any, Dict, List, Optional
from app.database import obter_conexao


def salvar_caderno_com_questoes(
    titulo: str,
    materia_detectada: str,
    conteudo_original: str,
    questoes: List[Dict[str, Any]],
) -> int:
    """
    Salva um novo caderno de estudo e todas as suas questões no banco SQLite.

    Parâmetros:
        titulo (str): Título curto gerado para o caderno.
        materia_detectada (str): Área do conhecimento identificada (ex.: Redes, Direito).
        conteudo_original (str): Texto original das anotações do usuário.
        questoes (List[Dict]): Lista de dicionários contendo as questões geradas.

    Retorna:
        int: O ID numérico do caderno recém-criado no banco.
    """
    conexao = obter_conexao()
    cursor = conexao.cursor()

    try:
        # Insere o registro principal na tabela 'cadernos'.
        # Usamos '?' como placeholder para evitar falhas de segurança (SQL Injection).
        cursor.execute(
            """
            INSERT INTO cadernos (titulo, materia_detectada, conteudo_original)
            VALUES (?, ?, ?);
            """,
            (titulo, materia_detectada, conteudo_original),
        )

        # Recupera o ID automático gerado pelo SQLite para este novo caderno.
        caderno_id = cursor.lastrowid

        # Percorre cada questão gerada e salva na tabela 'questoes'.
        for q in questoes:
            # Convertemos a lista Python de alternativas para texto JSON
            # porque o SQLite não possui um tipo nativo de lista/array.
            alternativas_texto = json.dumps(q["alternativas"], ensure_ascii=False)

            cursor.execute(
                """
                INSERT INTO questoes (
                    caderno_id, enunciado, tipo, dificuldade, topico,
                    alternativas_json, resposta_correta, explicacao_detalhada, fonte_url
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    caderno_id,
                    q["enunciado"],
                    q["tipo"],
                    q["dificuldade"],
                    q["topico"],
                    alternativas_texto,
                    int(q["resposta_correta"]),
                    q["explicacao_detalhada"],
                    q["fonte_url"],
                ),
            )

        # Salva definitivamente o caderno e todas as questões juntas.
        conexao.commit()
        return caderno_id

    except Exception as erro:
        # Se algo der errado no meio do caminho, desfaz tudo para não deixar dados pela metade.
        conexao.rollback()
        raise erro

    finally:
        # Garante que a conexão será fechada mesmo se ocorrer erro.
        conexao.close()


def listar_cadernos() -> List[Dict[str, Any]]:
    """
    Busca todos os cadernos salvos, incluindo a contagem de questões
    e o melhor percentual de acerto obtido pelo usuário em cada um.

    Retorna:
        List[Dict[str, Any]]: Lista de cadernos ordenados do mais recente para o mais antigo.
    """
    conexao = obter_conexao()
    cursor = conexao.cursor()

    # Consulta SQL usando LEFT JOIN para trazer também a quantidade de questões
    # e a maior nota (MAX(t.percentual)) já alcançada naquele caderno.
    cursor.execute("""
        SELECT
            c.id,
            c.titulo,
            c.materia_detectada,
            strftime('%d/%m/%Y %H:%M', c.criado_em, 'localtime') AS criado_em,
            COUNT(DISTINCT q.id) AS total_questoes,
            MAX(t.percentual) AS melhor_percentual
        FROM cadernos c
        LEFT JOIN questoes q ON q.caderno_id = c.id
        LEFT JOIN tentativas t ON t.caderno_id = c.id
        GROUP BY c.id
        ORDER BY c.id DESC;
    """)

    linhas = cursor.fetchall()
    conexao.close()

    # Converte cada linha sqlite3.Row em um dicionário Python comum para virar JSON.
    return [dict(linha) for linha in linhas]


def buscar_caderno_por_id(caderno_id: int) -> Optional[Dict[str, Any]]:
    """
    Recupera os detalhes completos de um caderno específico e todas as suas questões.

    Parâmetros:
        caderno_id (int): ID do caderno no banco de dados.

    Retorna:
        Optional[Dict[str, Any]]: Dicionário com dados do caderno e lista de questões,
                                  ou None se o ID não existir.
    """
    conexao = obter_conexao()
    cursor = conexao.cursor()

    # 1. Busca os dados do caderno.
    cursor.execute(
        """
        SELECT
            id,
            titulo,
            materia_detectada,
            conteudo_original,
            strftime('%d/%m/%Y %H:%M', criado_em, 'localtime') AS criado_em
        FROM cadernos
        WHERE id = ?;
        """,
        (caderno_id,),
    )
    caderno_row = cursor.fetchone()

    if not caderno_row:
        conexao.close()
        return None

    caderno = dict(caderno_row)

    # 2. Busca todas as questões vinculadas a este caderno.
    cursor.execute(
        """
        SELECT
            id, enunciado, tipo, dificuldade, topico,
            alternativas_json, resposta_correta, explicacao_detalhada, fonte_url
        FROM questoes
        WHERE caderno_id = ?
        ORDER BY id ASC;
        """,
        (caderno_id,),
    )
    questoes_rows = cursor.fetchall()
    conexao.close()

    # Converte o campo 'alternativas_json' de volta para uma lista Python real.
    questoes_formatadas = []
    for row in questoes_rows:
        item = dict(row)
        item["alternativas"] = json.loads(item.pop("alternativas_json"))
        questoes_formatadas.append(item)

    caderno["questoes"] = questoes_formatadas
    return caderno


def registrar_tentativa(caderno_id: int, acertos: int, total_questoes: int) -> Dict[str, Any]:
    """
    Salva o resultado de um simulado concluído pelo usuário.

    Parâmetros:
        caderno_id (int): ID do caderno estudado.
        acertos (int): Quantidade de respostas corretas.
        total_questoes (int): Número total de questões respondidas.

    Retorna:
        Dict[str, Any]: Dados da tentativa salva, incluindo o percentual calculado.
    """
    # Calcula a porcentagem de acerto com uma casa decimal (ex.: 80.0).
    percentual = round((acertos / total_questoes) * 100, 1) if total_questoes > 0 else 0.0

    conexao = obter_conexao()
    cursor = conexao.cursor()

    cursor.execute(
        """
        INSERT INTO tentativas (caderno_id, acertos, total_questoes, percentual)
        VALUES (?, ?, ?, ?);
        """,
        (caderno_id, acertos, total_questoes, percentual),
    )

    conexao.commit()
    conexao.close()

    return {
        "caderno_id": caderno_id,
        "acertos": acertos,
        "total_questoes": total_questoes,
        "percentual": percentual,
    }


def excluir_caderno(caderno_id: int) -> bool:
    """
    Remove um caderno (e automaticamente suas questões e tentativas) do banco.

    Parâmetros:
        caderno_id (int): ID do caderno a ser excluído.

    Retorna:
        bool: True se algum registro foi apagado, False caso o ID não existisse.
    """
    conexao = obter_conexao()
    cursor = conexao.cursor()

    cursor.execute("DELETE FROM cadernos WHERE id = ?;", (caderno_id,))
    linhas_afetadas = cursor.rowcount

    conexao.commit()
    conexao.close()

    return linhas_afetadas > 0
