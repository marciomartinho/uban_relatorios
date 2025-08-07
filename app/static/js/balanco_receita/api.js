/**
 * Módulo de API
 * Gerencia todas as chamadas AJAX para o backend
 */

class ApiBalancoReceita {
    constructor() {
        this.config = window.ConfiguracoesBalancoReceita;
        this.endpoints = this.config.API;
    }
    
    /**
     * Carrega os filtros disponíveis
     * @returns {Promise} Promessa com os dados dos filtros
     */
    carregarFiltros() {
        console.log('API: Carregando filtros...');
        
        return $.ajax({
            url: this.endpoints.FILTROS,
            method: 'GET',
            error: (xhr) => {
                console.error('❌ Erro ao carregar filtros:', xhr);
                throw new Error('Erro ao carregar filtros');
            }
        });
    }
    
    /**
     * Gera o relatório com base nos parâmetros
     * @param {Object} parametros - Parâmetros do relatório (ano, mes, coug, tipo_receita)
     * @returns {Promise} Promessa com os dados do relatório
     */
    gerarRelatorio(parametros) {
        console.log('🦆 API: Gerando relatório:', parametros);
        
        return $.ajax({
            url: this.endpoints.GERAR_RELATORIO,
            method: 'GET',
            data: parametros,
            error: (xhr) => {
                console.error('❌ Erro ao gerar relatório:', xhr);
                let mensagemErro = 'Erro ao gerar relatório';
                if (xhr.responseJSON && xhr.responseJSON.erro) {
                    mensagemErro += ': ' + xhr.responseJSON.erro;
                }
                throw new Error(mensagemErro);
            }
        });
    }
    
    /**
     * Carrega lançamentos de uma UG específica
     * @param {Object} parametros - Parâmetros para buscar lançamentos
     * @returns {Promise} Promessa com os dados dos lançamentos
     */
    carregarLancamentos(parametros) {
        console.log('API: Carregando lançamentos:', parametros);
        
        return $.ajax({
            url: this.endpoints.LANCAMENTOS,
            method: 'GET',
            data: parametros,
            error: (xhr) => {
                console.error('❌ Erro ao carregar lançamentos:', xhr);
                let mensagemErro = 'Erro ao carregar lançamentos';
                if (xhr.responseJSON && xhr.responseJSON.erro) {
                    mensagemErro += ': ' + xhr.responseJSON.erro;
                }
                throw new Error(mensagemErro);
            }
        });
    }
}

// Exportar instância única (Singleton)
window.ApiBalancoReceita = new ApiBalancoReceita();