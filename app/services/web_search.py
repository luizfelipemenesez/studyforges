
"""
Arquivo: app/services/web_search.py
Papel no sistema: Extrai termos-chave das anotações do usuário e pesquisa
referências complementares na internet usando DuckDuckGo.
Comunica-se com:
  - Biblioteca ddgs (realiza as consultas na web)
  - app/routes/api_routes.py (fornece contexto externo para enriquecer as questões)
"""

import re
from collections import Counter
from typing import Dict, List
from ddgs import DDGS
from ddgs.exceptions import DDGSException


# Lista de palavras muito comuns em português (stopwords) que não servem
# como termos técnicos de pesquisa.
PALAVRAS_IGNORADAS = {
    "para", "como", "mais", "mas", "foi", "ser", "tem", "são", "sua", "seu",
    "seus", "suas", "com", "por", "uma", "uns", "umas", "dos", "das", "nos",
    "nas", "que", "quando", "onde", "qual", "quais", "sobre", "entre", "deve",
    "podem", "pode", "isso", "isto", "esse", "essa", "este", "esta", "também",
    "muito", "sem", "apenas", "cada", "todo", "toda", "todos", "todas", "forma",
    "exemplo", "exemplos", "regra", "regras", "tipo", "tipos", "dados", "sistema"
}


def extrair_consultas_de_busca(texto_anotacao: str) -> List[str]:
    """
    Analisa as anotações do usuário e monta até 3 frases de pesquisa otimizadas
    para buscar aprofundamento técnico na web.

    Parâmetros:
        texto_anotacao (str): Conteúdo textual das anotações do estudante.

    Retorna:
        List[str]: Lista com 2 a 3 consultas prontas para pesquisar.
    """
    # Pega as primeiras linhas não vazias para capturar o tema/título principal.
    linhas = [linha.strip("#-* \t") for linha in texto_anotacao.splitlines() if linha.strip()]
    tema_principal = linhas[0][:80] if linhas else ""

    # Extrai palavras relevantes (com 4 ou mais letras, incluindo siglas como SSH, NAT, HTTP).
    palavras_encontradas = re.findall(r"\b[A-Za-zÀ-ÿ0-9_-]{3,}\b", texto_anotacao)

    # Filtra palavras comuns e conta as que mais se repetem no texto do usuário.
    termos_filtrados = [
        p for p in palavras_encontradas
        if p.lower() not in PALAVRAS_IGNORADAS and not p.isdigit()
    ]
    mais_frequentes = [palavra for palavra, _ in Counter(termos_filtrados).most_common(6)]

    consultas = []

    # Consulta 1: Foca no tema principal + boas práticas / conceitos.
    if tema_principal:
        consultas.append(f"{tema_principal} conceitos boas praticas")

    # Consulta 2: Combina os 3 termos técnicos mais frequentes com cenários práticos.
    if len(mais_frequentes) >= 3:
        grupo_1 = " ".join(mais_frequentes[:3])
        consultas.append(f"{grupo_1} funcionamento exemplos praticos")

    # Consulta 3: Combina os próximos termos frequentes buscando exceções ou detalhes.
    if len(mais_frequentes) >= 6:
        grupo_2 = " ".join(mais_frequentes[3:6])
        consultas.append(f"{grupo_2} erros comuns troubleshooting")

    # Garante pelo menos uma consulta caso o texto seja muito curto.
    if not consultas and texto_anotacao.strip():
        consultas.append(texto_anotacao.strip()[:100])

    return consultas[:3]


def buscar_referencias_web(texto_anotacao: str) -> List[Dict[str, str]]:
    """
    Pesquisa na internet conteúdos complementares relacionados às anotações.
    Caso não haja conexão com a internet ou o buscador falhe, retorna uma lista vazia
    sem interromper o fluxo do sistema.

    Parâmetros:
        texto_anotacao (str): Anotações originais enviadas pelo usuário.

    Retorna:
        List[Dict[str, str]]: Lista de resultados contendo 'titulo', 'resumo' e 'url'.
    """
    consultas = extrair_consultas_de_busca(texto_anotacao)
    resultados_coletados: List[Dict[str, str]] = []
    urls_vistas = set()
    falhas_consultas: List[str] = []

    try:
        # Abre o cliente de busca do DuckDuckGo.
        with DDGS() as ddgs:
            for consulta in consultas:
                try:
                    # Busca até 2 resultados relevantes em português por mecanismo disponível.
                    encontrados = list(
                        ddgs.text(
                            consulta,
                            region="br-pt",
                            max_results=2,
                            backend="auto",
                        )
                    )
                except DDGSException as erro:
                    falhas_consultas.append(str(erro))
                    continue

                for item in encontrados:
                    url = item.get("href", "").strip()
                    titulo = item.get("title", "").strip()
                    resumo = item.get("body", "").strip()

                    # Evita adicionar links repetidos ou resultados vazios.
                    if url and resumo and url not in urls_vistas:
                        urls_vistas.add(url)
                        resultados_coletados.append({
                            "titulo": titulo,
                            "resumo": resumo,
                            "url": url,
                        })

    except Exception as erro:
        # Registra um aviso discreto no terminal e segue sem quebrar a aplicação.
        print(f"[Aviso WebSearch] Não foi possível consultar fontes externas: {erro}")

    if not resultados_coletados and falhas_consultas:
        print(
            "[Aviso WebSearch] Nenhuma consulta retornou fontes externas: "
            f"{falhas_consultas[0]}"
        )

    return resultados_coletados[:5]
