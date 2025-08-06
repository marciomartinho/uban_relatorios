/**
 * Módulo de API
 * Gerencia todas as chamadas AJAX para o backend
 * app/static/js/relatorio_receita_fonte/api.js
 */

class ApiRelatorioReceitaFonte {
    constructor() {
        this.config = window.ConfigRelatorioReceitaFonte;
        this.endpoints = this.config.API;
    }
    
    /**
     * Carrega os filtros disponíveis
     * @returns {Promise} Promessa com os dados dos filtros
     */
    async carregarFiltros() {
        console.log('API: Carregando filtros...');
        
        try {
            const response = await fetch(this.endpoints.FILTROS);
            
            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }
            
            const dados = await response.json();
            console.log('✅ Filtros carregados:', dados);
            return dados;
            
        } catch (erro) {
            console.error('❌ Erro ao carregar filtros:', erro);
            throw erro;
        }
    }
    
    /**
     * Gera o relatório com base nos parâmetros
     * @param {Object} parametros - Parâmetros do relatório
     * @returns {Promise} Promessa com os dados do relatório
     */
    async gerarRelatorio(parametros) {
        console.log('API: Gerando relatório:', parametros);
        
        try {
            // Construir URL com parâmetros
            const url = new URL(this.endpoints.GERAR, window.location.origin);
            Object.keys(parametros).forEach(key => {
                if (parametros[key]) {
                    url.searchParams.append(key, parametros[key]);
                }
            });
            
            const response = await fetch(url);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.erro || `Erro HTTP: ${response.status}`);
            }
            
            const dados = await response.json();
            console.log('✅ Relatório gerado:', dados);
            return dados;
            
        } catch (erro) {
            console.error('❌ Erro ao gerar relatório:', erro);
            throw erro;
        }
    }
    
    /**
     * Exporta o relatório para Excel
     * @param {Object} parametros - Parâmetros da exportação
     * @returns {Promise} Promessa com os dados para exportação
     */
    async exportarRelatorio(parametros) {
        console.log('API: Exportando relatório:', parametros);
        
        try {
            // Adicionar formato à requisição
            parametros.formato = 'excel';
            
            const url = new URL(this.endpoints.EXPORTAR, window.location.origin);
            Object.keys(parametros).forEach(key => {
                if (parametros[key]) {
                    url.searchParams.append(key, parametros[key]);
                }
            });
            
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }
            
            const dados = await response.json();
            console.log('✅ Dados para exportação obtidos');
            return dados;
            
        } catch (erro) {
            console.error('❌ Erro ao exportar relatório:', erro);
            throw erro;
        }
    }
    
    /**
     * Obtém detalhes de um item específico
     * @param {string} tipo - Tipo do item (fonte ou receita)
     * @param {string} codigo - Código do item
     * @param {Object} parametros - Parâmetros adicionais
     * @returns {Promise} Promessa com os detalhes
     */
    async obterDetalhes(tipo, codigo, parametros) {
        console.log(`API: Obtendo detalhes ${tipo}/${codigo}`);
        
        try {
            const url = new URL(`${this.endpoints.DETALHES}/${tipo}/${codigo}`, window.location.origin);
            
            if (parametros) {
                Object.keys(parametros).forEach(key => {
                    url.searchParams.append(key, parametros[key]);
                });
            }
            
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }
            
            const dados = await response.json();
            return dados;
            
        } catch (erro) {
            console.error('❌ Erro ao obter detalhes:', erro);
            throw erro;
        }
    }
    
    /**
     * Método auxiliar para tratamento de erros
     * @param {Error} erro - Objeto de erro
     * @returns {string} Mensagem de erro formatada
     */
    formatarErro(erro) {
        if (erro.message) {
            return erro.message;
        }
        if (typeof erro === 'string') {
            return erro;
        }
        return this.config.MENSAGENS.ERRO_GENERICO;
    }
}

// Exportar instância única (Singleton)
window.ApiRelatorioReceitaFonte = new ApiRelatorioReceitaFonte();