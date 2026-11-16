
"""
Arquivo: app/services/file_parser.py
Papel no sistema: Serviço responsável por ler arquivos enviados pelo usuário
(.txt, .md e .pdf) e extrair o texto limpo para estudo.
Comunica-se com:
  - Biblioteca pypdf (para ler páginas de arquivos PDF)
  - app/routes/api_routes.py (chamado quando o usuário envia um anexo)
"""

from werkzeug.datastructures import FileStorage
from pypdf import PdfReader


# Conjunto com as extensões de arquivo aceitas pelo sistema.
EXTENSOES_PERMITIDAS = {".txt", ".md", ".pdf"}


def extrair_texto_de_arquivo(arquivo: FileStorage) -> str:
    """
    Recebe um arquivo enviado via formulário HTML e devolve todo o seu conteúdo em texto.

    Parâmetros:
        arquivo (FileStorage): Objeto de arquivo recebido pelo Flask (request.files).

    Retorna:
        str: Texto extraído do arquivo.

    Levanta:
        ValueError: Se o formato do arquivo não for suportado ou estiver vazio.
    """
    nome_arquivo = (arquivo.filename or "").lower().strip()

    if not nome_arquivo:
        raise ValueError("Nenhum nome de arquivo válido foi enviado.")

    # Verifica se o arquivo termina com alguma das extensões permitidas.
    if not any(nome_arquivo.endswith(ext) for ext in EXTENSOES_PERMITIDAS):
        raise ValueError(
            "Formato de arquivo não suportado. Envie apenas arquivos .txt, .md ou .pdf."
        )

    # Caso 1: Arquivos de texto simples (.txt ou .md)
    if nome_arquivo.endswith((".txt", ".md")):
        # Lê os bytes do arquivo e decodifica para texto UTF-8.
        # errors="replace" evita travamento caso haja algum caractere especial antigo.
        conteudo_bytes = arquivo.read()
        texto = conteudo_bytes.decode("utf-8", errors="replace").strip()

        if not texto:
            raise ValueError("O arquivo de texto enviado está vazio.")
        return texto

    # Caso 2: Arquivos PDF (.pdf)
    if nome_arquivo.endswith(".pdf"):
        try:
            leitor_pdf = PdfReader(arquivo.stream)
            paginas_texto = []

            # Percorre todas as páginas do PDF extraindo o texto de cada uma.
            for numero_pagina, pagina in enumerate(leitor_pdf.pages, start=1):
                texto_pagina = pagina.extract_text() or ""
                if texto_pagina.strip():
                    paginas_texto.append(texto_pagina.strip())

            texto_completo = "\n\n".join(paginas_texto).strip()

            if not texto_completo:
                raise ValueError(
                    "Não foi possível extrair texto deste PDF. "
                    "Verifique se o arquivo não é apenas uma imagem escaneada."
                )

            return texto_completo

        except ValueError:
            raise
        except Exception as erro:
            raise ValueError(f"Erro ao ler o arquivo PDF: {str(erro)}")

    return ""
