/**
 * Módulo de Filtros
 * Gerencia toda a lógica de filtros
 * app/static/js/relatorio_receita_fonte/filtros.js
 */

class FiltrosRelatorioReceitaFonte {
    constructor() {
        this.config = window.ConfigRelatorioReceitaFonte;
        this.seletores = this.config.SELETORES;
        this.dadosFiltros = null;
    }
    
    /**
     * Carrega filtros na interface
     * @param {Object} dados - Dados dos filtros vindos da API
     */
    carregarFiltrosInterface(dados) {
        console.log('Carregando filtros na interface:', dados);
        this.dadosFiltros = dados;
        
        this._carregarAnos(dados);
        this._carregarUGs(dados);
        
        // Se tem ano atual, carregar meses e selecionar último mês
        if (dados.ano_atual) {
            this.carregarMeses(dados.ano_atual);
            
            if (dados.ultimo_mes) {
                setTimeout(() => {
                    document.querySelector(this.seletores.SELECT_MES).value = dados.ultimo_mes;
                }, 100);
            }
        }
    }
    
    /**
     * Carrega anos no select
     * @private
     */
    _carregarAnos(dados) {
        const selectAno = document.querySelector(this.seletores.SELECT_ANO);
        selectAno.innerHTML = '<option value="">Selecione...</option>';
        
        if (dados.anos && dados.anos.length > 0) {
            dados.anos.forEach(ano => {
                const option = document.createElement('option');
                option.value = ano;
                option.textContent = ano;
                selectAno.appendChild(option);
            });
            
            // Selecionar ano atual se disponível
            if (dados.ano_atual) {
                selectAno.value = dados.ano_atual;
            }
        }
    }
    
    /**
     * Carrega UGs no select
     * @private
     */
    _carregarUGs(dados) {
        const selectUG = document.querySelector(this.seletores.SELECT_UG);
        selectUG.innerHTML = '<option value="">📊 Dados Consolidados</option>';
        
        if (dados.ugs && dados.ugs.length > 0) {
            dados.ugs.forEach(ug => {
                const option = document.createElement('option');
                option.value = ug.codigo;
                option.textContent = `🏛️ ${ug.descricao}`;
                selectUG.appendChild(option);
            });
        }
    }
    
    /**
     * Carrega meses disponíveis para o ano selecionado
     * @param {string} ano - Ano selecionado
     */
    carregarMeses(ano) {
        const selectMes = document.querySelector(this.seletores.SELECT_MES);
        
        if (!ano) {
            selectMes.innerHTML = '<option value="">Selecione o ano primeiro</option>';
            return;
        }
        
        selectMes.innerHTML = '<option value="">Selecione...</option>';
        
        // Adicionar todos os meses
        for (let i = 1; i <= 12; i++) {
            const option = document.createElement('option');
            option.value = i;
            option.textContent = `${i.toString().padStart(2, '0')} - ${this.config.MESES[i]}`;
            selectMes.appendChild(option);
        }
        
        // Se é o ano atual dos filtros, selecionar último mês
        if (this.dadosFiltros && 
            ano == this.dadosFiltros.ano_atual && 
            this.dadosFiltros.ultimo_mes) {
            selectMes.value = this.dadosFiltros.ultimo_mes;
        }
    }
    
    /**
     * Obtém valores dos filtros selecionados
     * @returns {Object} Objeto com valores dos filtros
     */
    obterFiltrosSelecionados() {
        return {
            tipo: document.querySelector(this.seletores.SELECT_TIPO).value,
            ano: document.querySelector(this.seletores.SELECT_ANO).value,
            mes: document.querySelector(this.seletores.SELECT_MES).value,
            coug: document.querySelector(this.seletores.SELECT_UG).value
        };
    }
    
    /**
     * Valida se os filtros obrigatórios foram selecionados
     * @returns {boolean} true se válido, false caso contrário
     */
    validarFiltros() {
        const filtros = this.obterFiltrosSelecionados();
        
        if (!filtros.ano || !filtros.mes) {
            return false;
        }
        
        return true;
    }
    
    /**
     * Limpa todos os filtros
     */
    limparFiltros() {
        // Resetar formulário
        const form = document.querySelector(this.seletores.FORM_FILTROS);
        form.reset();
        
        // Resetar select de mês
        const selectMes = document.querySelector(this.seletores.SELECT_MES);
        selectMes.innerHTML = '<option value="">Selecione o ano primeiro</option>';
        
        // Resetar tipo para padrão
        document.querySelector(this.seletores.SELECT_TIPO).value = 'fonte';
        
        // Ocultar relatório
        document.querySelector(this.seletores.CONTAINER_RELATORIO).style.display = 'none';
        
        // Mostrar mensagem inicial
        document.querySelector(this.seletores.MENSAGEM_INICIAL).style.display = 'block';
    }
    
    /**
     * Obtém descrição do período selecionado
     * @returns {string} Descrição do período
     */
    obterDescricaoPeriodo() {
        const filtros = this.obterFiltrosSelecionados();
        
        if (filtros.mes && filtros.ano) {
            const nomeMes = this.config.MESES[parseInt(filtros.mes)];
            return `${nomeMes}/${filtros.ano}`;
        }
        
        return '';
    }
    
    /**
     * Obtém descrição da UG selecionada
     * @returns {string} Descrição da UG
     */
    obterDescricaoUG() {
        const selectUG = document.querySelector(this.seletores.SELECT_UG);
        const opcaoSelecionada = selectUG.options[selectUG.selectedIndex];
        
        if (opcaoSelecionada && opcaoSelecionada.value) {
            return opcaoSelecionada.textContent.replace('🏛️ ', '');
        }
        
        return 'Consolidado';
    }
    
    /**
     * Salva estado dos filtros no localStorage
     */
    salvarEstadoFiltros() {
        const filtros = this.obterFiltrosSelecionados();
        localStorage.setItem('relatorioReceitaFonte_filtros', JSON.stringify(filtros));
    }
    
    /**
     * Restaura estado dos filtros do localStorage
     */
    restaurarEstadoFiltros() {
        const filtrosSalvos = localStorage.getItem('relatorioReceitaFonte_filtros');
        
        if (filtrosSalvos) {
            try {
                const filtros = JSON.parse(filtrosSalvos);
                
                // Restaurar valores
                if (filtros.tipo) {
                    document.querySelector(this.seletores.SELECT_TIPO).value = filtros.tipo;
                }
                
                if (filtros.ano) {
                    document.querySelector(this.seletores.SELECT_ANO).value = filtros.ano;
                    this.carregarMeses(filtros.ano);
                }
                
                // Aguardar carregamento dos meses
                setTimeout(() => {
                    if (filtros.mes) {
                        document.querySelector(this.seletores.SELECT_MES).value = filtros.mes;
                    }
                    if (filtros.coug) {
                        document.querySelector(this.seletores.SELECT_UG).value = filtros.coug;
                    }
                }, 100);
                
                console.log('Filtros restaurados:', filtros);
                return true;
                
            } catch (erro) {
                console.error('Erro ao restaurar filtros:', erro);
                localStorage.removeItem('relatorioReceitaFonte_filtros');
            }
        }
        
        return false;
    }
    
    /**
     * Verifica se deve gerar relatório automaticamente
     * @returns {boolean} true se deve gerar
     */
    deveGerarAutomatico() {
        // Se tem filtros salvos e válidos
        if (this.restaurarEstadoFiltros()) {
            return this.validarFiltros();
        }
        
        // Se tem dados padrão dos filtros
        if (this.dadosFiltros && 
            this.dadosFiltros.ano_atual && 
            this.dadosFiltros.ultimo_mes) {
            return true;
        }
        
        return false;
    }
}

// Exportar instância única
window.FiltrosRelatorioReceitaFonte = new FiltrosRelatorioReceitaFonte();