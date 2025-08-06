/**
 * Módulo de Eventos
 * Gerencia todos os event listeners e interações do usuário
 * app/static/js/relatorio_receita_fonte/eventos.js
 */

class EventosRelatorioReceitaFonte {
    constructor() {
        this.config = window.ConfigRelatorioReceitaFonte;
        this.seletores = this.config.SELETORES;
        this.controlador = null; // Será definido pelo controlador principal
    }
    
    /**
     * Define o controlador principal
     * @param {Object} controlador - Instância do controlador principal
     */
    setControlador(controlador) {
        this.controlador = controlador;
    }
    
    /**
     * Configura todos os eventos da aplicação
     */
    configurarTodos() {
        this._configurarEventosFiltros();
        this._configurarEventosBotoes();
        this._configurarEventosTabela();
        this._configurarEventosGlobais();
    }
    
    /**
     * Configura eventos dos filtros
     * @private
     */
    _configurarEventosFiltros() {
        // Mudança de ano
        document.querySelector(this.seletores.SELECT_ANO).addEventListener('change', (e) => {
            const ano = e.target.value;
            window.FiltrosRelatorioReceitaFonte.carregarMeses(ano);
        });
        
        // Submit do formulário
        document.querySelector(this.seletores.FORM_FILTROS).addEventListener('submit', (e) => {
            e.preventDefault();
            if (this.controlador) {
                this.controlador.gerarRelatorio();
            }
        });
        
        // Mudança no tipo de relatório
        document.querySelector(this.seletores.SELECT_TIPO).addEventListener('change', (e) => {
            console.log('Tipo de relatório alterado para:', e.target.value);
            // Salvar estado
            window.FiltrosRelatorioReceitaFonte.salvarEstadoFiltros();
        });
        
        // Mudança em outros filtros (para salvar estado)
        [this.seletores.SELECT_MES, this.seletores.SELECT_UG].forEach(seletor => {
            document.querySelector(seletor).addEventListener('change', () => {
                window.FiltrosRelatorioReceitaFonte.salvarEstadoFiltros();
            });
        });
    }
    
    /**
     * Configura eventos dos botões de ação
     * @private
     */
    _configurarEventosBotoes() {
        // Botão limpar
        document.querySelector(this.seletores.BTN_LIMPAR).addEventListener('click', () => {
            window.FiltrosRelatorioReceitaFonte.limparFiltros();
            localStorage.removeItem('relatorioReceitaFonte_filtros');
        });
        
        // Botão expandir todos
        document.querySelector(this.seletores.BTN_EXPANDIR_TODOS).addEventListener('click', () => {
            window.RenderizadorRelatorioReceitaFonte.expandirTodos();
        });
        
        // Botão recolher todos
        document.querySelector(this.seletores.BTN_RECOLHER_TODOS).addEventListener('click', () => {
            window.RenderizadorRelatorioReceitaFonte.recolherTodos();
        });
        
        // Botão exportar Excel
        document.querySelector(this.seletores.BTN_EXPORTAR).addEventListener('click', () => {
            if (this.controlador) {
                this.controlador.exportarExcel();
            }
        });
        
        // Botão imprimir
        document.querySelector(this.seletores.BTN_IMPRIMIR).addEventListener('click', () => {
            window.print();
        });
    }
    
    /**
     * Configura eventos da tabela (delegação de eventos)
     * @private
     */
    _configurarEventosTabela() {
        // Usar delegação de eventos para botões de toggle criados dinamicamente
        document.querySelector(this.seletores.TBODY_RELATORIO).addEventListener('click', (e) => {
            // Verificar se clicou em um botão toggle
            if (e.target.classList.contains('toggle-btn')) {
                this._handleToggle(e.target);
            }
        });
    }
    
    /**
     * Configura eventos globais
     * @private
     */
    _configurarEventosGlobais() {
        // Teclas de atalho
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + P para imprimir
            if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
                e.preventDefault();
                const btnImprimir = document.querySelector(this.seletores.BTN_IMPRIMIR);
                if (btnImprimir && !btnImprimir.disabled) {
                    btnImprimir.click();
                }
            }
            
            // Ctrl/Cmd + E para exportar
            if ((e.ctrlKey || e.metaKey) && e.key === 'e') {
                e.preventDefault();
                const btnExportar = document.querySelector(this.seletores.BTN_EXPORTAR);
                if (btnExportar && !btnExportar.disabled) {
                    btnExportar.click();
                }
            }
            
            // ESC para limpar filtros
            if (e.key === 'Escape') {
                const container = document.querySelector(this.seletores.CONTAINER_RELATORIO);
                if (container.style.display === 'none') {
                    window.FiltrosRelatorioReceitaFonte.limparFiltros();
                }
            }
        });
        
        // Fechar alertas automaticamente
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-close')) {
                const alert = e.target.closest('.alert');
                if (alert) {
                    alert.remove();
                }
            }
        });
    }
    
    /**
     * Manipula toggle de expansão/recolhimento
     * @private
     */
    _handleToggle(button) {
        const id = button.dataset.id;
        const isExpanded = button.innerHTML === this.config.ICONES.RECOLHER;
        
        console.log(`Toggle item ${id}, expandido: ${!isExpanded}`);
        
        if (isExpanded) {
            // Recolher
            this._recolherItem(id, button);
        } else {
            // Expandir
            this._expandirItem(id, button);
        }
    }
    
    /**
     * Expande um item
     * @private
     */
    _expandirItem(id, button) {
        button.innerHTML = this.config.ICONES.RECOLHER;
        button.classList.add(this.config.CLASSES.EXPANDIDO);
        
        // Mostrar filhos diretos
        const filhos = document.querySelectorAll(`tr[data-pai-id="${id}"]`);
        filhos.forEach(filho => {
            filho.style.display = 'table-row';
        });
    }
    
    /**
     * Recolhe um item
     * @private
     */
    _recolherItem(id, button) {
        button.innerHTML = this.config.ICONES.EXPANDIR;
        button.classList.remove(this.config.CLASSES.EXPANDIDO);
        
        // Ocultar filhos diretos
        const filhos = document.querySelectorAll(`tr[data-pai-id="${id}"]`);
        filhos.forEach(filho => {
            filho.style.display = 'none';
            
            // Se o filho tem um botão toggle expandido, recolher também
            const toggleFilho = filho.querySelector('.toggle-btn');
            if (toggleFilho && toggleFilho.classList.contains(this.config.CLASSES.EXPANDIDO)) {
                this._recolherItem(filho.dataset.id, toggleFilho);
            }
        });
    }
    
    /**
     * Habilita/desabilita botões baseado no estado
     * @param {boolean} habilitar - true para habilitar, false para desabilitar
     */
    habilitarBotoes(habilitar) {
        const botoes = [
            this.seletores.BTN_EXPORTAR,
            this.seletores.BTN_IMPRIMIR,
            this.seletores.BTN_EXPANDIR_TODOS,
            this.seletores.BTN_RECOLHER_TODOS
        ];
        
        botoes.forEach(seletor => {
            const botao = document.querySelector(seletor);
            if (botao) {
                botao.disabled = !habilitar;
            }
        });
    }
    
    /**
     * Adiciona indicador de loading em botão
     * @param {HTMLElement} botao - Elemento do botão
     * @param {boolean} loading - true para mostrar loading
     */
    setLoadingBotao(botao, loading) {
        if (loading) {
            botao.disabled = true;
            botao.dataset.textoOriginal = botao.innerHTML;
            botao.innerHTML = `${this.config.ICONES.LOADING} Processando...`;
        } else {
            botao.disabled = false;
            if (botao.dataset.textoOriginal) {
                botao.innerHTML = botao.dataset.textoOriginal;
                delete botao.dataset.textoOriginal;
            }
        }
    }
    
    /**
     * Remove todos os event listeners (para limpeza)
     */
    destruir() {
        // Remover listeners do formulário
        const form = document.querySelector(this.seletores.FORM_FILTROS);
        if (form) {
            const novoForm = form.cloneNode(true);
            form.parentNode.replaceChild(novoForm, form);
        }
        
        // Remover listeners da tabela
        const tbody = document.querySelector(this.seletores.TBODY_RELATORIO);
        if (tbody) {
            const novoTbody = tbody.cloneNode(true);
            tbody.parentNode.replaceChild(novoTbody, tbody);
        }
        
        console.log('Event listeners removidos');
    }
}

// Exportar instância única
window.EventosRelatorioReceitaFonte = new EventosRelatorioReceitaFonte();