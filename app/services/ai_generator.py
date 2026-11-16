
"""
Arquivo: app/services/ai_generator.py
Papel no sistema: Serviço de inteligência pedagógica. Diagnostica a matéria das
anotações, cruza com as referências buscadas na web e gera questões estruturadas
em JSON usando o Google Gemini.
Comunica-se com:
  - app/config.py (obtém GEMINI_API_KEY)
  - Biblioteca google-genai e pydantic
  - app/routes/api_routes.py
"""

import json
import time
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from google import genai
from google.genai.errors import ServerError
from google.genai import types
from app.config import Config


class GeminiTemporariamenteIndisponivelError(RuntimeError):
    """Indica que os modelos Gemini tentados continuam indisponíveis."""


# ==============================================================================
# Esquemas Pydantic: definem o formato exato do JSON que o Gemini deve devolver.
# Isso garante que o frontend nunca receba campos faltando ou mal formatados.
# ==============================================================================

class QuestaoGeradaSchema(BaseModel):
    enunciado: str = Field(
        description="Enunciado claro, técnico e bem redigido da questão."
    )
    tipo: str = Field(
        description="Tipo da questão: 'multipla_escolha', 'cenario' ou 'verdadeiro_falso'."
    )
    dificuldade: str = Field(
        description="Nível da questão: 'Iniciante', 'Intermediário' ou 'Avançado'."
    )
    topico: str = Field(
        description="Subtema específico abordado na questão (ex.: Regras NAT, Métodos HTTP)."
    )
    alternativas: List[str] = Field(
        description="Lista com 4 alternativas (para múltipla escolha/cenário) ou 2 alternativas ('Verdadeiro', 'Falso')."
    )
    resposta_correta: int = Field(
        description="Índice numérico (começando em 0) da alternativa correta na lista."
    )
    explicacao_detalhada: str = Field(
        description="Explicação didática mostrando o que veio das anotações do usuário e o que foi aprofundado pela pesquisa web."
    )
    fonte_url: str = Field(
        description="URL exata da fonte web utilizada para enriquecer a questão, ou 'Baseado nas anotações do usuário'."
    )


class SimuladoCompletoSchema(BaseModel):
    titulo_sugerido: str = Field(
        description="Título curto e descritivo para o caderno de estudo (máximo 60 caracteres)."
    )
    materia_detectada: str = Field(
        description="Área do conhecimento diagnosticada (ex.: Segurança de Redes, Direito Administrativo, Engenharia de Software)."
    )
    questoes: List[QuestaoGeradaSchema] = Field(
        description="Lista completa das questões geradas."
    )


def _gerar_conteudo_com_fallback(
    cliente: genai.Client,
    conteudo: str,
    configuracao: types.GenerateContentConfig,
) -> Any:
    """
    Tenta gerar conteúdo com o modelo principal e um modelo alternativo em erros 503.

    Parâmetros:
        cliente (genai.Client): Cliente configurado do Google GenAI.
        conteudo (str): Prompt enviado ao modelo.
        configuracao (types.GenerateContentConfig): Formato e parâmetros da resposta.

    Retorna:
        Any: Resposta retornada pelo SDK do Google GenAI.
    """
    modelos = ("gemini-3.8-flash", "gemini-3.6-flash")
    ultimo_erro: ServerError | None = None

    for modelo in modelos:
        for tentativa in range(2):
            try:
                return cliente.models.generate_content(
                    model=modelo,
                    contents=conteudo,
                    config=configuracao,
                )
            except ServerError as erro:
                if erro.code != 503:
                    raise

                ultimo_erro = erro
                if tentativa == 0:
                    time.sleep(1)

    raise GeminiTemporariamenteIndisponivelError(
        "O Gemini está temporariamente indisponível nos modelos principal e alternativo. "
        "Tente novamente em alguns minutos."
    ) from ultimo_erro


def gerar_simulado_estruturado(
    texto_anotacao: str,
    referencias_web: List[Dict[str, str]],
    quantidade: int = 5,
    dificuldade: str = "Misto",
) -> Dict[str, Any]:
    """
    Envia as anotações e o contexto pesquisado na web para o Gemini e retorna
    um dicionário Python pronto para ser salvo no banco SQLite.

    Parâmetros:
        texto_anotacao (str): Anotações originais do usuário.
        referencias_web (List[Dict]): Trechos e URLs coletados pelo web_search.py.
        quantidade (int): Número de questões desejadas (entre 5 e 15).
        dificuldade (str): 'Iniciante', 'Intermediário', 'Avançado' ou 'Misto'.

    Retorna:
        Dict[str, Any]: Dicionário contendo 'titulo_sugerido', 'materia_detectada' e 'questoes'.
    """
    # Valida se o backend carregou uma chave real do ambiente ou do arquivo .env.
    if not Config.GEMINI_API_KEY:
        raise ValueError(
            "O backend não carregou GEMINI_API_KEY. "
            f"Confira {Config.ENV_FILE} e reinicie o servidor."
        )

    if Config.GEMINI_API_KEY == Config.GEMINI_API_KEY_PLACEHOLDER:
        raise ValueError(
            "GEMINI_API_KEY ainda contém o valor de exemplo. "
            f"Substitua-o em {Config.ENV_FILE} e reinicie o servidor."
        )

    # Inicializa o cliente oficial do Google GenAI.
    cliente = genai.Client(api_key=Config.GEMINI_API_KEY)

    # Formata as referências encontradas na internet em um bloco legível para o modelo.
    if referencias_web:
        bloco_web = "\n".join(
            [
                f"- Fonte: {ref['titulo']} | URL: {ref['url']}\n  Conteúdo: {ref['resumo']}"
                for ref in referencias_web
            ]
        )
    else:
        bloco_web = "Nenhuma referência externa disponível. Baseie-se integralmente nas anotações do usuário."

    # Instruções de sistema que definem o comportamento pedagógico do avaliador.
    instrucao_sistema = (
        "Você é um professor especialista e elaborador de avaliações técnicas e acadêmicas. "
        "Sua tarefa é analisar as anotações de um estudante, identificar automaticamente a área do conhecimento "
        "e criar um simulado de alta qualidade que ajude o aluno a dominar o assunto.\n\n"
        "REGRAS DE ELABORAÇÃO:\n"
        "1. Misture formatos: inclua questões de 'multipla_escolha' (4 opções), 'cenario' (estudo de caso prático ou troubleshooting com 4 opções) "
        "e 'verdadeiro_falso' (apenas 2 opções: 'Verdadeiro' e 'Falso').\n"
        "2. Não crie alternativas óbvias ou absurdas; os distratores devem testar a real compreensão do aluno.\n"
        "3. Na 'explicacao_detalhada', deixe claro o que foi extraído das anotações do aluno e qual detalhe técnico/prático "
        "foi complementado pelas referências da web.\n"
        "4. No campo 'fonte_url', coloque a URL real fornecida no contexto web quando a questão usar aquela informação, "
        "ou 'Baseado nas anotações do usuário' quando vier diretamente do texto enviado.\n"
        "5. Não use emojis em nenhum campo."
    )

    # Prompt principal combinando anotações, contexto da web e parâmetros escolhidos.
    prompt_usuario = f"""
Crie um simulado com exatamente {quantidade} questões.
Nível de dificuldade desejado: {dificuldade}.

=== ANOTAÇÕES DO ESTUDANTE ===
{texto_anotacao}

=== REFERÊNCIAS PESQUISADAS NA WEB ===
{bloco_web}
"""

    # Tenta o modelo principal e usa o modelo alternativo se ambos os pedidos retornarem 503.
    configuracao_geracao = types.GenerateContentConfig(
        system_instruction=instrucao_sistema,
        response_mime_type="application/json",
        response_schema=SimuladoCompletoSchema,
        temperature=0.4,
    )
    resposta = _gerar_conteudo_com_fallback(
        cliente=cliente,
        conteudo=prompt_usuario,
        configuracao=configuracao_geracao,
    )

    # Converte a resposta JSON garantida pelo modelo em um dicionário Python.
    dados_simulado = json.loads(resposta.text)

    # Validação extra de segurança: garante que o índice resposta_correta está dentro da lista.
    for questao in dados_simulado.get("questoes", []):
        total_opcoes = len(questao.get("alternativas", []))
        indice = questao.get("resposta_correta", 0)
        if indice < 0 or indice >= total_opcoes:
            questao["resposta_correta"] = 0

    return dados_simulado
