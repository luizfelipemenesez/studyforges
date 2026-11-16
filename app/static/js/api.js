
/**
 * Arquivo: app/static/js/api.js
 * Papel no sistema: Centraliza todas as chamadas HTTP (fetch) para o backend Flask.
 * Ao isolar as requisições aqui, dashboard.js e quiz.js ficam mais limpos e fáceis de ler.
 * Comunica-se com: app/routes/api_routes.py
 */

const StudyForgeAPI = {
    /**
     * Busca todos os cadernos salvos no banco SQLite.
     * @returns {Promise<Array>} Lista de objetos de cadernos.
     */
    async listarCadernos() {
        const resposta = await fetch("/api/cadernos");
        const dados = await resposta.json();

        if (!resposta.ok || !dados.sucesso) {
            throw new Error(dados.erro || "Falha ao carregar a biblioteca de cadernos.");
        }
        return dados.cadernos;
    },

    /**
     * Busca um caderno específico e suas questões pelo ID.
     * @param {number} cadernoId - ID numérico do caderno.
     * @returns {Promise<Object>} Objeto completo do caderno com array de questões.
     */
    async obterCaderno(cadernoId) {
        const resposta = await fetch(`/api/cadernos/${cadernoId}`);
        const dados = await resposta.json();

        if (!resposta.ok || !dados.sucesso) {
            throw new Error(dados.erro || "Caderno não encontrado.");
        }
        return dados.caderno;
    },

    /**
     * Envia anotações e arquivo (via FormData) para gerar um novo simulado.
     * @param {FormData} formData - Dados do formulário da tela inicial.
     * @returns {Promise<Object>} Resposta contendo o caderno_id criado.
     */
    async gerarCaderno(formData) {
        const resposta = await fetch("/api/cadernos/gerar", {
            method: "POST",
            body: formData,
        });
        const dados = await resposta.json();

        if (!resposta.ok || !dados.sucesso) {
            throw new Error(dados.erro || "Erro ao gerar o simulado.");
        }
        return dados;
    },

    /**
     * Registra a nota final de uma tentativa concluída no simulado.
     * @param {number} cadernoId - ID do caderno.
     * @param {number} acertos - Total de respostas corretas.
     * @param {number} totalQuestoes - Total de questões do simulado.
     * @returns {Promise<Object>} Resultado salvo com o percentual.
     */
    async salvarTentativa(cadernoId, acertos, totalQuestoes) {
        const resposta = await fetch(`/api/cadernos/${cadernoId}/tentativas`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                acertos: acertos,
                total_questoes: totalQuestoes,
            }),
        });
        const dados = await resposta.json();

        if (!resposta.ok || !dados.sucesso) {
            throw new Error(dados.erro || "Erro ao salvar pontuação.");
        }
        return dados.resultado;
    },

    /**
     * Exclui permanentemente um caderno do banco de dados.
     * @param {number} cadernoId - ID do caderno a ser removido.
     * @returns {Promise<boolean>} True se excluído com sucesso.
     */
    async excluirCaderno(cadernoId) {
        const resposta = await fetch(`/api/cadernos/${cadernoId}`, {
            method: "DELETE",
        });
        const dados = await resposta.json();

        if (!resposta.ok || !dados.sucesso) {
            throw new Error(dados.erro || "Erro ao excluir caderno.");
        }
        return true;
    },
};
