
/**
 * Arquivo: app/static/js/dashboard.js
 * Papel no sistema: Controla toda a interatividade da tela inicial (index.html):
 *   - Preenchimento dos 3 exemplos prontos (Firewall, REST API, Direito)
 *   - Envio do formulário e animação das etapas de geração
 *   - Renderização e exclusão de itens na Biblioteca de Cadernos
 * Comunica-se com: app/templates/index.html e app/static/js/api.js
 */

// Exemplos embutidos para permitir testar o sistema com um clique.
const EXEMPLOS_ESTUDO = {
    firewall: `Guia de Criação e Políticas de Firewall de Rede

1. Ordem de Avaliação das Regras (Top-Down)
As regras de um firewall stateful são avaliadas sequencialmente de cima para baixo. Assim que um pacote corresponde aos critérios de uma regra, a ação (Allow ou Deny) é aplicada e as regras abaixo são ignoradas. Por padrão, aplica-se a política Implicit Deny (bloqueio implícito) ao final da tabela.

2. Portas e Serviços Críticos
- SSH (Porta 22/TCP): Administração remota segura em servidores Linux. Nunca deve ficar exposta para 0.0.0.0/0; restringir ao IP da VPN administrativa.
- HTTP (Porta 80/TCP) e HTTPS (Porta 443/TCP): Tráfego web. Recomenda-se redirecionar 80 para 443.
- RDP (Porta 3389/TCP): Área de Trabalho Remota Windows. Alto risco de ataques de força bruta; exigir VPN antes do acesso.

3. Regras de NAT (Network Address Translation)
- Source NAT (SNAT / Masquerade): Permite que hosts da rede interna (ex.: 192.168.10.0/24) acessem a internet usando o IP público do firewall.
- Destination NAT (DNAT / Port Forwarding): Redireciona conexões vindas da internet para um servidor interno na DMZ (ex.: porta externa 443 para IP interno 10.0.5.20).

4. Perfis de Segurança
Além de filtrar IP e porta, firewalls de próxima geração aplicam perfis de IPS (Prevenção de Intrusão), antivírus de borda e filtragem DNS.`,

    rest: `Fundamentos de APIs REST e Protocolo HTTP

1. Princípios da Arquitetura REST
REST (Representational State Transfer) é um estilo arquitetural stateless: cada requisição enviada pelo cliente deve conter todas as informações necessárias para ser processada, sem depender de estado armazenado na memória do servidor entre chamadas.

2. Métodos HTTP Principais
- GET: Recupera dados de um recurso. Deve ser seguro e idempotente (não altera dados no servidor).
- POST: Cria um novo recurso (ex.: cadastrar um usuário). Não é idempotente.
- PUT: Atualiza integralmente um recurso existente. É idempotente.
- DELETE: Remove um recurso específico.

3. Códigos de Status HTTP
- 200 OK: Requisição bem-sucedida.
- 201 Created: Novo recurso criado com sucesso (comum em respostas POST).
- 400 Bad Request: Erro de validação nos dados enviados pelo cliente.
- 401 Unauthorized: Falha de autenticação (token ausente ou inválido).
- 404 Not Found: Recurso não localizado no servidor.
- 500 Internal Server Error: Falha inesperada no processamento do backend.`,

    direito: `Princípios Constitucionais da Administração Pública (Art. 37 da CF/88)

A Administração Pública direta e indireta de qualquer dos Poderes da União, dos Estados, do Distrito Federal e dos Municípios obedecerá aos princípios do LIMPE:

1. Legalidade: Enquanto o particular pode fazer tudo o que a lei não proíbe, o administrador público só pode fazer aquilo que a lei expressamente autoriza ou determina.
2. Impessoalidade: Os atos administrativos devem visar exclusivamente ao interesse público, sendo vedada a promoção pessoal de autoridades ou perseguições/favorecimentos individuais.
3. Moralidade: Exige atuação ética, honesta e de boa-fé por parte dos agentes públicos, indo além da simples legalidade formal.
4. Publicidade: Divulgação oficial dos atos administrativos como requisito de transparência e controle social, ressalvadas as hipóteses legais de sigilo.
5. Eficiência: Impõe que a atuação administrativa busque produtividade, economicidade e qualidade na prestação dos serviços públicos.`,
};

document.addEventListener("DOMContentLoaded", () => {
    // Referências aos elementos do DOM (HTML).
    const formCaderno = document.getElementById("form-novo-caderno");
    const textareaAnotacao = document.getElementById("texto-anotacao");
    const inputArquivo = document.getElementById("input-arquivo");
    const nomeArquivoLabel = document.getElementById("nome-arquivo-selecionado");
    const btnLimparTexto = document.getElementById("btn-limpar-texto");
    const btnGerar = document.getElementById("btn-gerar-simulado");
    const alertaErro = document.getElementById("alerta-erro");
    const statusGeracao = document.getElementById("status-geracao");
    const textoStatusEtapa = document.getElementById("texto-status-etapa");
    const listaCadernosEl = document.getElementById("lista-cadernos");
    const contadorCadernosEl = document.getElementById("contador-cadernos");

    // Carrega imediatamente o histórico de cadernos ao abrir a página.
    carregarBiblioteca();

    // Configura os botões de exemplo rápido.
    document.querySelectorAll(".btn-exemplo").forEach((botao) => {
        botao.addEventListener("click", () => {
            const chave = botao.getAttribute("data-exemplo");
            if (EXEMPLOS_ESTUDO[chave]) {
                textareaAnotacao.value = EXEMPLOS_ESTUDO[chave];
                esconderErro();
            }
        });
    });

    // Botão para limpar o campo de texto.
    btnLimparTexto.addEventListener("click", () => {
        textareaAnotacao.value = "";
        textareaAnotacao.focus();
    });

    // Mostra o nome do arquivo selecionado no campo de upload.
    inputArquivo.addEventListener("change", () => {
        if (inputArquivo.files && inputArquivo.files.length > 0) {
            nomeArquivoLabel.textContent = `Arquivo selecionado: ${inputArquivo.files[0].name}`;
        } else {
            nomeArquivoLabel.textContent = "Opcional. O texto extraído será somado às anotações acima.";
        }
    });

    // Envio do formulário para gerar o simulado.
    formCaderno.addEventListener("submit", async (evento) => {
        evento.preventDefault();
        esconderErro();

        const formData = new FormData(formCaderno);
        const usarWeb = document.getElementById("check-busca-web").checked;
        formData.set("usar_busca_web", usarWeb ? "true" : "false");

        // Bloqueia o botão e inicia feedback progressivo das etapas.
        btnGerar.disabled = true;
        statusGeracao.classList.remove("hidden");

        const etapas = [
            "Analisando estrutura e conceitos das anotações...",
            usarWeb
                ? "Consultando referências e boas práticas na web..."
                : "Organizando tópicos principais do material...",
            "Elaborando questões e gabarito comentado...",
        ];

        let indiceEtapa = 0;
        textoStatusEtapa.textContent = etapas[0];

        // Alterna as mensagens de status a cada 3,5 segundos para informar o usuário.
        const intervaloStatus = setInterval(() => {
            indiceEtapa = (indiceEtapa + 1) % etapas.length;
            textoStatusEtapa.textContent = etapas[indiceEtapa];
        }, 3500);

        try {
            const resultado = await StudyForgeAPI.gerarCaderno(formData);
            clearInterval(intervaloStatus);

            // Redireciona diretamente para a tela de estudo do caderno criado.
            window.location.href = `/quiz/${resultado.caderno_id}`;
        } catch (erro) {
            clearInterval(intervaloStatus);
            statusGeracao.classList.add("hidden");
            btnGerar.disabled = false;
            mostrarErro(erro.message);
        }
    });

    /**
     * Busca os cadernos no backend e desenha os cartões na coluna lateral.
     */
    async function carregarBiblioteca() {
        try {
            const cadernos = await StudyForgeAPI.listarCadernos();
            contadorCadernosEl.textContent = cadernos.length;

            if (cadernos.length === 0) {
                listaCadernosEl.innerHTML = `
                    <div class="border border-dashed border-slate-200 rounded-md p-6 text-center">
                        <p class="text-sm text-slate-600 font-medium">Nenhum caderno salvo ainda</p>
                        <p class="text-xs text-slate-500 mt-1">
                            Crie seu primeiro simulado ao lado para iniciar sua biblioteca.
                        </p>
                    </div>
                `;
                return;
            }

            listaCadernosEl.innerHTML = cadernos
                .map((caderno) => {
                    const notaBadge =
                        caderno.melhor_percentual !== null
                            ? `<span class="font-mono text-xs px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200">
                                   Melhor nota: ${caderno.melhor_percentual}%
                               </span>`
                            : `<span class="font-mono text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                                   Não iniciado
                               </span>`;

                    return `
                        <div class="border border-slate-200 rounded-md p-3.5 hover:border-slate-300 transition-colors bg-[#FAF9F6]">
                            <div class="flex items-start justify-between gap-2">
                                <span class="font-mono text-[11px] text-blue-700 font-medium">
                                    ${escaparHTML(caderno.materia_detectada)}
                                </span>
                                <button type="button"
                                    data-excluir-id="${caderno.id}"
                                    title="Excluir caderno"
                                    class="btn-excluir-caderno text-xs text-slate-400 hover:text-rose-700 transition-colors">
                                    Excluir
                                </button>
                            </div>

                            <h3 class="text-sm font-semibold text-slate-900 mt-1 line-clamp-2">
                                ${escaparHTML(caderno.titulo)}
                            </h3>

                            <div class="flex items-center justify-between mt-3 pt-2.5 border-t border-slate-200/70">
                                <div class="flex items-center gap-2">
                                    ${notaBadge}
                                    <span class="font-mono text-[11px] text-slate-500">
                                        ${caderno.total_questoes} q.
                                    </span>
                                </div>

                                <a href="/gabarito/${caderno.id}"
                                    class="text-xs font-medium text-blue-700 hover:text-blue-800">
                                    Estudar &rarr;
                                </a>
                            </div>
                        </div>
                    `;
                })
                .join("");

            // Adiciona evento de exclusão aos botões recém-criados.
            document.querySelectorAll(".btn-excluir-caderno").forEach((btn) => {
                btn.addEventListener("click", async () => {
                    const id = btn.getAttribute("data-excluir-id");
                    if (confirm("Deseja realmente excluir este caderno e seu histórico?")) {
                        try {
                            await StudyForgeAPI.excluirCaderno(id);
                            carregarBiblioteca();
                        } catch (erro) {
                            alert(erro.message);
                        }
                    }
                });
            });
        } catch (erro) {
            listaCadernosEl.innerHTML = `
                <p class="text-sm text-rose-700">${escaparHTML(erro.message)}</p>
            `;
        }
    }

    function mostrarErro(mensagem) {
        alertaErro.textContent = mensagem;
        alertaErro.classList.remove("hidden");
    }

    function esconderErro() {
        alertaErro.classList.add("hidden");
        alertaErro.textContent = "";
    }

    /**
     * Protege contra injeção de HTML (XSS) ao exibir textos vindos do banco.
     */
    function escaparHTML(texto) {
        const div = document.createElement("div");
        div.textContent = texto || "";
        return div.innerHTML;
    }
});
