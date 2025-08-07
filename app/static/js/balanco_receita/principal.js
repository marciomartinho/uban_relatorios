/**
 * Controlador Principal
 * Coordena todos os módulos do sistema de Balanço de Receitas
 */

class ControladorPrincipalBalancoReceita {
    constructor() {
        this.config = window.ConfiguracoesBalancoReceita;
        this.api = window.ApiBalancoReceita;
        this.renderizador = window.RenderizadorBalancoReceita;
        this.filtros = window.FiltrosBalancoReceita;
        this.eventos = window.EventosBalancoReceita;
        this.exportador = window.ExportadorBalancoReceita;
        this.formatadores = window.FormatadoresBalancoReceita;
        
        // Estado da aplicação
        this.dadosRelatorio = null;
        this.dadosOriginais = null;
        this.filtrosCarregados = false;
    }
    
    /**
     * Inicializa a aplicação
     */
    inicializar() {
        console.log('Balanço Receita - Iniciando sistema modular...');
        
        // Configurar eventos
        this.eventos.configurarTodos();
        
        // Carregar filtros
        this.carregarFiltros();
    }
    
    /**
     * Carrega filtros iniciais
     */
    async carregarFiltros() {
        console.log('Carregando filtros...');
        
        try {
            const dados = await this.api.carregarFiltros();
            this.filtros.carregarFiltrosInterface(dados);
            this.filtrosCarregados = true;
            
            // Gerar relatório automático se tiver dados
            if (dados.ano_atual && dados.ultimo_mes) {
                setTimeout(() => this.gerarRelatorioAutomatico(), 200);
            }
            
        } catch (error) {
            console.error('Erro ao carregar filtros:', error);
            this._mostrarErro('Erro ao carregar filtros. Por favor, recarregue a página.');
        }
    }
    
    /**
     * Gera relatório automaticamente ao carregar a página
     */
    gerarRelatorioAutomatico() {
        const filtrosSelecionados = this.filtros.obterFiltrosSelecionados();
        
        if (filtrosSelecionados.ano && filtrosSelecionados.mes) {
            console.log('🚀 Gerando relatório automático...');
            this.gerarRelatorio();
        }
    }
    
    /**
     * Gera o relatório principal
     */
    async gerarRelatorio() {
        // Validar filtros
        if (!this.filtros.validarFiltros()) {
            this.renderizador.mostrarAlerta('Por favor, selecione ano e mês!', 'warning');
            return;
        }
        
        const parametros = this.filtros.obterFiltrosSelecionados();
        console.log('🦆 Gerando relatório:', parametros);
        
        // Mostrar loading
        this.renderizador.renderizarLoading();
        
        try {
            // Fazer requisição
            const response = await this.api.gerarRelatorio(parametros);
            console.log('✅ Relatório gerado:', response);
            
            // Armazenar dados
            this._armazenarDados(response);
            
            // Renderizar relatório
            this.renderizador.renderizarRelatorio(response);
            
            // Aplicar filtro se necessário
            if (parametros.tipo_receita !== 'todas') {
                this.filtros.aplicarFiltroReceita(parametros.tipo_receita, this.dadosOriginais);
            }
            
            // Integrar módulos adicionais
            setTimeout(() => this._integrarModulosAdicionais(response), 100);
            
        } catch (error) {
            console.error('❌ Erro ao gerar relatório:', error);
            this.renderizador.renderizarErro(error.message);
        }
    }
    
    /**
     * Armazena dados do relatório
     * @private
     */
    _armazenarDados(response) {
        // Armazenar no controlador
        this.dadosRelatorio = response;
        this.dadosOriginais = JSON.parse(JSON.stringify(response));
        
        // Armazenar globalmente para compatibilidade
        window.dadosRelatorio = response;
        window.dadosOriginais = this.dadosOriginais;
        window.ultimoRelatorioGerado = response;
    }
    
    /**
     * Integra módulos adicionais (Análise Visual e Comparativo Mensal)
     * @private
     */
    _integrarModulosAdicionais(dadosRelatorio) {
        // Análise Visual
        if (typeof analiseVisual !== 'undefined') {
            console.log('🎨 Integrando módulo de Análise Visual');
            analiseVisual.inicializar(dadosRelatorio);
        }
        
        // Comparativo Mensal
        if (typeof comparativoMensal !== 'undefined') {
            console.log('📊 Integrando módulo de Comparativo Mensal');
            comparativoMensal.inicializar(dadosRelatorio);
        }
    }
    
    /**
     * Limpa todos os filtros e dados
     */
    limparTudo() {
        // Destruir módulos integrados
        this._destruirModulosIntegrados();
        
        // Limpar filtros
        this.filtros.limparFiltros();
        
        // Limpar interface
        $(this.config.SELETORES.CONTAINER_RELATORIO).hide();
        $(this.config.SELETORES.MENSAGEM_INICIAL).show();
        
        // Limpar dados
        this.dadosRelatorio = null;
        this.dadosOriginais = null;
        window.dadosRelatorio = null;
        window.dadosOriginais = null;
        window.ultimoRelatorioGerado = null;
    }
    
    /**
     * Destrói módulos integrados
     * @private
     */
    _destruirModulosIntegrados() {
        if (typeof analiseVisual !== 'undefined') {
            analiseVisual.destruir();
            $('#analiseVisualContainer').remove();
        }
        
        if (typeof comparativoMensal !== 'undefined') {
            comparativoMensal.destruir();
            $('#comparativoMensalContainer').remove();
        }
    }
    
    /**
     * Mostra mensagem de erro
     * @private
     */
    _mostrarErro(mensagem) {
        $(this.config.SELETORES.MENSAGEM_INICIAL)
            .removeClass('alert-info')
            .addClass('alert-danger')
            .html(`<i class="bi bi-exclamation-triangle"></i> ${mensagem}`)
            .show();
    }
}

// Criar e exportar instância do controlador principal
window.ControladorPrincipal = new ControladorPrincipalBalancoReceita();

// Inicializar quando o documento estiver pronto
$(document).ready(function() {
    window.ControladorPrincipal.inicializar();
});