---
name: studyforge-dev
description: Padrões arquiteturais, didáticos e visuais obrigatórios para desenvolver e manter o projeto StudyForge.
---

# Diretrizes de Desenvolvimento — StudyForge

Sempre que criar, editar ou depurar qualquer arquivo neste repositório, siga estas 4 regras fundamentais:

## 1. Arquitetura Modular em Camadas
- **Nunca** misture regras de negócio, SQL e rotas HTTP no mesmo arquivo.
- `app/routes/`: Apenas recebe requisições HTTP, valida entradas básicas e chama os serviços ou modelos.
- `app/services/`: Lógica de processamento (leitura de arquivos, busca web no DuckDuckGo, chamadas ao Gemini).
- `app/models/`: Exclusivamente consultas SQL ao banco SQLite usando parâmetros (`?`).
- `app/static/js/`: Separe chamadas `fetch` (`api.js`) da manipulação de tela (`dashboard.js` e `quiz.js`).

## 2. Código Didático para Iniciantes
- Todo arquivo deve iniciar com um comentário explicando sua função e dependências.
- Toda função Python ou JavaScript deve conter docstring/comentário detalhando parâmetros e retorno.
- Prefira código explícito, linear e legível em vez de abreviações complexas.

## 3. Estética Editorial (Proibido Clichês de IA)
- **Não use** gradientes roxos, violetas, rosas ou efeitos neon.
- **Não use** emojis na interface do usuário (nem em títulos, botões ou alertas).
- **Não use** textos como "Powered by AI" ou ícones de estrelas mágicas.
- Mantenha a paleta sóbria: fundo `#FAF9F6`, cartões `#FFFFFF` com borda `1px solid #E2E8F0`, texto `#0F172A` e cor de destaque única em azul cobalto `#1D4ED8`.
- Use `Inter` para leitura e `JetBrains Mono` para termos técnicos, portas de rede e códigos.

## 4. Segurança e Resiliência
- Nunca exponha `GEMINI_API_KEY` no frontend; ela deve residir apenas no `.env` carregado pelo backend.
- Falhas na busca web (`web_search.py`) nunca devem derrubar a aplicação: capture exceções e siga gerando questões apenas com as anotações do usuário.
