# StudyForge

Plataforma web de estudo ativo que transforma anotações técnicas ou acadêmicas (em texto livre, `.md`, `.txt` ou `.pdf`) em simulados interativos enriquecidos com consultas em tempo real na web.

## Estrutura do Projeto

- `run.py`: Inicia o servidor web local.
- `app/config.py`: Lê as configurações e chaves do arquivo `.env`.
- `app/database.py`: Cria e gerencia a conexão com o banco de dados local `studyforge.db`.
- `app/models/study_model.py`: Executa comandos SQL para salvar e consultar cadernos e notas.
- `app/services/file_parser.py`: Extrai texto de arquivos `.txt`, `.md` e `.pdf`.
- `app/services/web_search.py`: Busca referências complementares na internet via DuckDuckGo.
- `app/services/ai_generator.py`: Analisa o tema das anotações e gera questões estruturadas via Gemini.
- `app/routes/page_routes.py`: Entrega as páginas HTML para o navegador.
- `app/routes/api_routes.py`: Fornece os endpoints JSON consumidos pelo JavaScript.
- `app/templates/`: Páginas HTML construídas com Jinja2 e TailwindCSS.
- `app/static/`: Estilos CSS customizados e scripts JavaScript modulares.

## Como Executar Localmente

1. **Crie e ative o ambiente virtual:**
   ```bash
   python -m venv venv
   # Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # Linux / macOS:
   source venv/bin/activate
   ```

2. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure sua chave de API:**
   - Copie `.env.example` para `.env`.
   - Insira sua chave gratuita do Google AI Studio na variável `GEMINI_API_KEY`.

4. **Inicie o servidor:**
   ```bash
   python run.py
   ```
   No Windows, se o ambiente virtual não estiver ativado, use diretamente:
   ```powershell
   .\venv\Scripts\python.exe run.py
   ```
   Ao iniciar, confira no terminal o caminho do arquivo `.env` e se `GEMINI_API_KEY` foi carregada.
   Abra `http://127.0.0.1:5000` no navegador.
