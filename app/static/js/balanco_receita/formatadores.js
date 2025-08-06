/**
 * Módulo de Formatadores
 * Funções utilitárias para formatação de valores, datas, etc.
 */

class FormatadoresBalancoReceita {
    constructor() {
        this.config = window.ConfiguracoesBalancoReceita;
    }
    
    /**
     * Formata valor monetário
     * @param {number} valor - Valor a ser formatado
     * @returns {string} Valor formatado em moeda brasileira
     */
    formatarValor(valor) {
        if (valor === null || valor === undefined || valor === 0) {
            return '0,00';
        }
        
        return new Intl.NumberFormat('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(valor);
    }
    
    /**
     * Formata percentual
     * @param {number} valor - Valor percentual a ser formatado
     * @returns {string} Valor formatado com símbolo de percentual
     */
    formatarPercentual(valor) {
        if (valor === null || valor === undefined || valor === 0) {
            return '0,00%';
        }
        
        return new Intl.NumberFormat('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(valor) + '%';
    }
    
    /**
     * Obtém o nome do mês
     * @param {number} mes - Número do mês (1-12)
     * @returns {string} Nome do mês
     */
    obterNomeMes(mes) {
        return this.config.MESES[mes] || mes;
    }
    
    /**
     * Formata data e hora atual
     * @returns {string} Data e hora formatadas
     */
    obterDataHoraAtual() {
        return new Date().toLocaleString('pt-BR');
    }
    
    /**
     * Gera timestamp para nomes de arquivo
     * @returns {number} Timestamp atual
     */
    obterTimestamp() {
        return new Date().getTime();
    }
    
    /**
     * Determina a classe CSS para variação
     * @param {number} valor - Valor da variação
     * @returns {string} Classe CSS apropriada
     */
    obterClasseVariacao(valor) {
        const classes = this.config.CLASSES.VARIACAO;
        return valor >= 0 ? classes.POSITIVA : classes.NEGATIVA;
    }
    
    /**
     * Formata descrição com prefixo baseado no nível
     * @param {Object} item - Item com nível e descrição
     * @returns {string} Descrição formatada
     */
    formatarDescricaoHierarquica(item) {
        let prefixo = item.nivel > 0 ? '  '.repeat(item.nivel) : '';
        let descricao = item.descricao;
        
        // Adicionar indicador especial para UGs
        if (item.nivel === 4) {
            prefixo += '► ';
            descricao = `UG ${descricao}`;
        }
        
        return prefixo + descricao;
    }
}

// Exportar instância única
window.FormatadoresBalancoReceita = new FormatadoresBalancoReceita();