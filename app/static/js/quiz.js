
/**
 * Arquivo: app/static/js/quiz.js
 * Papel no sistema: Controla toda a experiência de estudo na página quiz.html:
 *   - Carrega o caderno e as questões via API
 *   - Gerencia seleção de alternativas, atalhos de teclado (1-4 e Enter) e correção imediata
 *   - Calcula o relatório final por tópico, salva no SQLite e exporta em Markdown (.md)
 * Comunica-se com: app/templates/quiz.html e app/static/js/api.js
 */

document.addEventListener("DOMContentLoaded", async () => {
    const container = document.getElementById("quiz-container");
    const cadernoId = parseInt(container.getAttribute("data-caderno-id"), 10);

    // Elementos de interface
    const loadingEl = document.getElementById("quiz-loading");
    const headerEl = document.getElementById("quiz-header");
    const cartaoQuestaoEl = document.getElementById("cartao-questao");
    const telaRelatorioEl = document.getElementById("tela-relatorio");

    const badgeMateriaEl = document.getElementById("badge-materia");
    const tituloCadernoEl = document.getElementById("titulo-caderno");
    const progressoTextoEl = document.getElementById("progresso-texto");
    const barraProgressoEl = document.getElementById("barra-progresso");

    const qTipoEl = document.getElementById("q-tipo");
    const qDificuldadeEl = document.getElementById("q-dificuldade");
    const qTopicoEl = document.getElementById("q-topico");
    const qEnunciadoEl = document.getElementById("q-enunciado");
    const qAlternativasEl = document.getElementById("q-alternativas");

    const painelExplicacaoEl = document.getElementById("painel-explicacao");
    const bannerResultadoEl = document.getElementById("banner-resultado-questao");
    const qExplicacaoEl = document.getElementById("q-explicacao");
    const qFonteEl = document.getElementById("q-fonte");

    const btnConfirmar = document.getElementById("btn-confirmar");
    const btnProxima = document.getElementById("btn-proxima");

    // Estado interno do simulado em andamento
    let cadernoAtual = null;
    let questoes = [];
    let indiceAtual = 0;
    let alternativaSelecionada = null;
    let questaoJaConfirmada = false;
    let historicoRespostas = []; // Guarda { questao, escolhida, acertou }

    // Mapeamento amigável dos tipos técnicos vindos do JSON
    const NOMES_TIPOS = {
        multipla_escolha: "Múltipla Escolha",
        cenario: "Análise de Cenário",
        verdadeiro_falso: "Verdadeiro ou Falso",
    };

    // 1. Carrega os dados do caderno ao abrir a página
    try {
        cadernoAtual = await StudyForgeAPI.obterCaderno(cadernoId);
        questoes = cadernoAtual.questoes || [];

        if (questoes.length === 0) {
            loadingEl.innerHTML = `<p class="text-sm text-rose-700">Este caderno não possui questões cadastradas.</p>`;
            return;
        }

        // Preenche cabeçalho
        badgeMateriaEl.textContent = cadernoAtual.materia_detectada;
        tituloCadernoEl.textContent = cadernoAtual.titulo;

        loadingEl.classList.add("hidden");
        headerEl.classList.remove("hidden");
        cartaoQuestaoEl.classList.remove("hidden");

        renderizarQuestao();
    } catch (erro) {
        loadingEl.innerHTML = `<p class="text-sm text-rose-700">${erro.message}</p>`;
    }

    /**
     * Desenha na tela a questão correspondente ao 'indiceAtual'.
     */
    function renderizarQuestao() {
        const q = questoes[indiceAtual];
        alternativaSelecionada = null;
        questaoJaConfirmada = false;

        // Atualiza texto e barra de progresso
        const numeroAtual = indiceAtual + 1;
        progressoTextoEl.textContent = `Questão ${numeroAtual} de ${questoes.length}`;
        const percentualBarra = Math.round(((numeroAtual - 1) / questoes.length) * 100);
        barraProgressoEl.style.width = `${percentualBarra}%`;

        // Atualiza metadados e enunciado
        qTipoEl.textContent = NOMES_TIPOS[q.tipo] || q.tipo;
        qDificuldadeEl.textContent = q.dificuldade;
        qTopicoEl.textContent = `· ${q.topico}`;
        qEnunciadoEl.textContent = q.enunciado;

        // Reseta painel de explicação e botões
        painelExplicacaoEl.classList.add("hidden");
        btnConfirmar.classList.remove("hidden");
        btnConfirmar.disabled = true;
        btnProxima.classList.add("hidden");
        btnProxima.textContent =
            indiceAtual === questoes.length - 1 ? "Finalizar Simulado" : "Próxima Questão";

        // Renderiza os botões das alternativas
        qAlternativasEl.innerHTML = q.alternativas
            .map((textoOpcao, idx) => {
                return `
                    <button type="button"
                        data-indice="${idx}"
                        class="btn-alternativa w-full text-left p-3.5 rounded-md border border-slate-200 bg-white hover:bg-slate-50 hover:border-slate-300 transition-colors flex items-start gap-3">
                        <span class="font-mono text-xs font-medium px-2 py-0.5 rounded bg-slate-100 text-slate-700 mt-0.5">
                            ${idx + 1}
                        </span>
                        <span class="text-sm text-slate-800 leading-relaxed flex-1">
                            ${escaparHTML(textoOpcao)}
                        </span>
                    </button>
                `;
            })
            .join("");

        // Vincula clique a cada alternativa
        document.querySelectorAll(".btn-alternativa").forEach((botao) => {
            botao.addEventListener("click", () => {
                if (questaoJaConfirmada) return;
                const idx = parseInt(botao.getAttribute("data-indice"), 10);
                selecionarAlternativa(idx);
            });
        });
    }

    /**
     * Destaca visualmente a alternativa marcada antes da confirmação.
     */
    function selecionarAlternativa(indice) {
        alternativaSelecionada = indice;
        btnConfirmar.disabled = false;

        document.querySelectorAll(".btn-alternativa").forEach((btn, idx) => {
            if (idx === indice) {
                btn.classList.remove("border-slate-200", "bg-white");
                btn.classList.add("border-blue-700", "bg-blue-50/60");
            } else {
                btn.classList.remove("border-blue-700", "bg-blue-50/60");
                btn.classList.add("border-slate-200", "bg-white");
            }
        });
    }

    /**
     * Corrige a questão atual, aplica cores semânticas (verde/vermelho) e exibe a explicação.
     */
    function confirmarResposta() {
        if (alternativaSelecionada === null || questaoJaConfirmada) return;

        questaoJaConfirmada = true;
        const q = questoes[indiceAtual];
        const acertou = alternativaSelecionada === q.resposta_correta;

        // Salva no histórico da sessão
        historicoRespostas.push({
            questao: q,
            escolhida: alternativaSelecionada,
            acertou: acertou,
        });

        // Aplica estilos visuais de acerto/erro nas alternativas
        document.querySelectorAll(".btn-alternativa").forEach((btn, idx) => {
            btn.disabled = true;
            btn.classList.remove("border-blue-700", "bg-blue-50/60", "hover:bg-slate-50");

            if (idx === q.resposta_correta) {
                btn.classList.add("border-emerald-600", "bg-emerald-50", "text-emerald-950");
            } else if (idx === alternativaSelecionada && !acertou) {
                btn.classList.add("border-rose-600", "bg-rose-50", "text-rose-950");
            } else {
                btn.classList.add("border-slate-200", "opacity-60");
            }
        });

        // Preenche o banner de feedback imediato
        if (acertou) {
            bannerResultadoEl.className =
                "rounded-md px-3.5 py-2 text-sm font-medium mb-3 bg-emerald-50 text-emerald-800 border border-emerald-200";
            bannerResultadoEl.textContent = "Resposta correta.";
        } else {
            bannerResultadoEl.className =
                "rounded-md px-3.5 py-2 text-sm font-medium mb-3 bg-rose-50 text-rose-800 border border-rose-200";
            bannerResultadoEl.textContent = `Resposta incorreta. A alternativa correta é a opção ${q.resposta_correta + 1}.`;
        }

        // Preenche explicação detalhada e link da fonte
        qExplicacaoEl.textContent = q.explicacao_detalhada;

        if (q.fonte_url && q.fonte_url.startsWith("http")) {
            qFonteEl.innerHTML = `<a href="${escaparHTML(q.fonte_url)}" target="_blank" rel="noopener noreferrer" class="text-blue-700 hover:underline font-mono">Abrir referência externa &nearr;</a>`;
        } else {
            qFonteEl.textContent = q.fonte_url || "Anotações do usuário";
        }

        painelExplicacaoEl.classList.remove("hidden");
        btnConfirmar.classList.add("hidden");
        btnProxima.classList.remove("hidden");
    }

    // Eventos dos botões Confirmar e Próxima
    btnConfirmar.addEventListener("click", confirmarResposta);

    btnProxima.addEventListener("click", async () => {
        if (indiceAtual < questoes.length - 1) {
            indiceAtual++;
            renderizarQuestao();
        } else {
            await finalizarSimulado();
        }
    });

    // Suporte a atalhos de teclado (teclas 1-4 e Enter)
    document.addEventListener("keydown", (evento) => {
        if (cartaoQuestaoEl.classList.contains("hidden")) return;

        const tecla = evento.key;
        if (["1", "2", "3", "4"].includes(tecla) && !questaoJaConfirmada) {
            const indice = parseInt(tecla, 10) - 1;
            const totalOpcoes = questoes[indiceAtual].alternativas.length;
            if (indice < totalOpcoes) {
                selecionarAlternativa(indice);
            }
        } else if (tecla === "Enter") {
            evento.preventDefault();
            if (!questaoJaConfirmada && alternativaSelecionada !== null) {
                confirmarResposta();
            } else if (questaoJaConfirmada) {
                btnProxima.click();
            }
        }
    });

    /**
     * Calcula estatísticas finais, salva a tentativa no SQLite e exibe o relatório.
     */
    async function finalizarSimulado() {
        barraProgressoEl.style.width = "100%";
        cartaoQuestaoEl.classList.add("hidden");
        telaRelatorioEl.classList.remove("hidden");

        const total = historicoRespostas.length;
        const acertos = historicoRespostas.filter((item) => item.acertou).length;
        const percentual = Math.round((acertos / total) * 100);

        document.getElementById("relatorio-percentual").textContent = `${percentual}%`;
        document.getElementById("relatorio-resumo").textContent =
            `Você acertou ${acertos} de ${total} questões neste caderno.`;

        // Agrupa desempenho por tópico
        const mapaTopicos = {};
        historicoRespostas.forEach((item) => {
            const topico = item.questao.topico;
            if (!mapaTopicos[topico]) {
                mapaTopicos[topico] = { acertos: 0, total: 0 };
            }
            mapaTopicos[topico].total += 1;
            if (item.acertou) mapaTopicos[topico].acertos += 1;
        });

        const relatorioTopicosEl = document.getElementById("relatorio-topicos");
        relatorioTopicosEl.innerHTML = Object.entries(mapaTopicos)
            .map(([topico, dados]) => {
                const taxa = Math.round((dados.acertos / dados.total) * 100);
                const precisaRevisar = taxa < 70;
                const badgeClass = precisaRevisar
                    ? "bg-rose-50 text-rose-800 border-rose-200"
                    : "bg-emerald-50 text-emerald-800 border-emerald-200";
                const statusTexto = precisaRevisar ? "Revisar" : "Dominado";

                return `
                    <div class="flex items-center justify-between p-3 rounded-md border border-slate-200 bg-[#FAF9F6]">
                        <span class="text-sm font-medium text-slate-800">${escaparHTML(topico)}</span>
                        <div class="flex items-center gap-2.5">
                            <span class="font-mono text-xs text-slate-600">${dados.acertos}/${dados.total}</span>
                            <span class="font-mono text-xs px-2 py-0.5 rounded border ${badgeClass}">
                                ${statusTexto}
                            </span>
                        </div>
                    </div>
                `;
            })
            .join("");

        // Salva a tentativa no banco SQLite
        try {
            await StudyForgeAPI.salvarTentativa(cadernoId, acertos, total);
        } catch (erro) {
            console.error("Aviso ao salvar pontuação:", erro.message);
        }
    }

    // Botão Refazer Simulado
    document.getElementById("btn-refazer").addEventListener("click", () => {
        indiceAtual = 0;
        historicoRespostas = [];
        telaRelatorioEl.classList.add("hidden");
        cartaoQuestaoEl.classList.remove("hidden");
        renderizarQuestao();
    });

    // Botão Exportar Simulado + Gabarito Comentado em Markdown (.md)
    document.getElementById("btn-exportar-md").addEventListener("click", () => {
        const linhas = [
            `# Simulado: ${cadernoAtual.titulo}`,
            `**Matéria:** ${cadernoAtual.materia_detectada}  `,
            `**Data:** ${cadernoAtual.criado_em}`,
            "",
            "---",
            "",
        ];

        historicoRespostas.forEach((item, index) => {
            const q = item.questao;
            linhas.push(`## Questão ${index + 1} (${q.dificuldade} — ${q.topico})`);
            linhas.push("");
            linhas.push(q.enunciado);
            linhas.push("");

            q.alternativas.forEach((alt, altIdx) => {
                const marcador = altIdx === q.resposta_correta ? "[X]" : "[ ]";
                linhas.push(`- ${marcador} **${altIdx + 1})** ${alt}`);
            });

            linhas.push("");
            linhas.push(`**Sua resposta:** Opção ${item.escolhida + 1} (${item.acertou ? "Correta" : "Incorreta"})`);
            linhas.push(`**Explicação:** ${q.explicacao_detalhada}`);
            linhas.push(`**Fonte:** ${q.fonte_url}`);
            linhas.push("");
            linhas.push("---");
            linhas.push("");
        });

        // Cria um arquivo virtual em memória e dispara o download no navegador
        const conteudoMd = linhas.join("\n");
        const blob = new Blob([conteudoMd], { type: "text/markdown;charset=utf-8;" });
        const urlDownload = URL.createObjectURL(blob);

        const link = document.createElement("a");
        link.href = urlDownload;
        link.download = `simulado_studyforge_${cadernoId}.md`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(urlDownload);
    });

    function escaparHTML(texto) {
        const div = document.createElement("div");
        div.textContent = texto || "";
        return div.innerHTML;
    }
});