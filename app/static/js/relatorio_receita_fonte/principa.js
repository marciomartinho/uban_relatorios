/**
 * Controlador Principal
 * Coordena todos os módulos do sistema de Relatório Receita/Fonte
 * app/static/js/relatorio_receita_fonte/principal.js
 */

class ControladorRelatorioReceitaFonte {
    constructor() {
        // Referências aos módulos
        this.config = window.ConfigRelatorioReceitaFonte;
        this.api = window.ApiRelatorioReceitaFonte;
        this.renderizador = window.RenderizadorRelatorioReceitaFonte;
        this.filtros = window.FiltrosRelatorioReceitaFonte;
        this.eventos = window.EventosRelatorioReceitaFonte;
        this.exportador = window.ExportadorRelatorioReceitaFonte;
        
        // Estado da aplicação
        this.dadosRelatorio = null;
        this.filtrosCarregados = false;
        this.processandoRequisicao = false;
    }
    
    /**
     * Inicializa a aplicação
     */
    async inicializar() {
        console.log('🚀 Iniciando Sistema de Relatório Receita/Fonte...');
        
        try {
            // Configurar referência do controlador nos eventos
            this.eventos.setControlador(this);
            
            // Configurar eventos
            this.eventos.configurarTodos();
            
            // Carregar filtros
            await this.carregarFiltros();
            
            // Verificar se deve gerar relatório automaticamente
            if (this.filtros.deveGerarAutomatico()) {
                console.log('Gerando relatório com filtros salvos/padrão...');
                setTimeout(() => this.gerarRelatorio(), 500);
            }
            
            console.log('✅ Sistema inicializado com sucesso!');
            
        } catch (erro) {
            console.error('❌ Erro ao inicializar sistema:', erro);
            this.renderizador.mostrarErro('Erro ao inicializar o sistema');
        }
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
            
        } catch (erro) {
            console.error('Erro ao carregar filtros:', erro);
            this.renderizador.mostrarErro('Erro ao carregar filtros. Por favor, recarregue a página.');
        }
    }
    
    /**
     * Gera o relatório principal
     */
    async gerarRelatorio() {
        // Verificar se já está processando
        if (this.processandoRequisicao) {
            console.log('Requisição já em andamento...');
            return;
        }
        
        // Validar filtros
        if (!this.filtros.validarFiltros()) {
            this.renderizador.mostrarErro(this.config.MENSAGENS.ERRO_FILTROS);
            return;
        }
        
        const parametros = this.filtros.obterFiltrosSelecionados();
        console.log('Gerando relatório com parâmetros:', parametros);
        
        this.processandoRequisicao = true;
        
        // Mostrar loading
        this.renderizador.mostrarLoading();
        
        // Desabilitar botões
        this.eventos.habilitarBotoes(false);
        
        try {
            // Fazer requisição
            const dados = await this.api.gerarRelatorio(parametros);
            
            // Armazenar dados
            this.dadosRelatorio = dados;
            this.exportador.setDadosAtuais(dados);
            
            // Salvar estado dos filtros
            this.filtros.salvarEstadoFiltros();
            
            // Renderizar relatório
            this.renderizador.renderizarRelatorio(dados);
            
            // Habilitar botões
            this.eventos.habilitarBotoes(true);
            
            // Log de sucesso
            console.log('✅ Relatório gerado com sucesso!', {
                total_registros: dados.dados ? dados.dados.length : 0,
                tem_dados: dados.tem_dados
            });
            
        } catch (erro) {
            console.error('❌ Erro ao gerar relatório:', erro);
            this.renderizador.mostrarErro(
                this.api.formatarErro(erro)
            );
            
            // Ocultar loading
            this.renderizador.ocultarLoading();
            
        } finally {
            this.processandoRequisicao = false;
        }
    }
    
    /**
     * Exporta relatório para Excel
     */
    async exportarExcel() {
        if (!this.dadosRelatorio) {
            this.renderizador.mostrarErro('Nenhum relatório para exportar');
            return;
        }
        
        // Usar módulo exportador
        await this.exportador.exportarExcel(this.dadosRelatorio);
    }
    
    /**
     * Exporta relatório via API (com dados atualizados)
     */
    async exportarViaAPI() {
        // Validar filtros
        if (!this.filtros.validarFiltros()) {
            this.renderizador.mostrarErro(this.config.MENSAGENS.ERRO_FILTROS);
            return;
        }
        
        const parametros = this.filtros.obterFiltrosSelecionados();
        console.log('Exportando via API:', parametros);
        
        try {
            // Mostrar loading no botão
            const btnExportar = document.querySelector(this.config.SELETORES.BTN_EXPORTAR);
            this.eventos.setLoadingBotao(btnExportar, true);
            
            // Buscar dados para exportação
            const dados = await this.api.exportarRelatorio(parametros);
            
            // Processar exportação
            if (dados && dados.dados) {
                // Criar Excel com os dados
                const wb = XLSX.utils.book_new();
                const ws = XLSX.utils.json_to_sheet(dados.dados);
                
                // Configurar larguras
                ws['!cols'] = this.config.EXPORTACAO.EXCEL.LARGURAS_COLUNAS.map(w => ({ wch: w }));
                
                // Adicionar ao workbook
                XLSX.utils.book_append_sheet(wb, ws, 'Dados');
                
                // Gerar nome do arquivo
                const nomeArquivo = `relatorio_${dados.tipo}_${dados.periodo.replace('/', '_')}.xlsx`;
                
                // Baixar arquivo
                XLSX.writeFile(wb, nomeArquivo);
                
                this.renderizador.mostrarSucesso('Arquivo exportado com sucesso!');
            }
            
        } catch (erro) {
            console.error('Erro ao exportar:', erro);
            this.renderizador.mostrarErro('Erro ao exportar relatório');
            
        } finally {
            const btnExportar = document.querySelector(this.config.SELETORES.BTN_EXPORTAR);
            this.eventos.setLoadingBotao(btnExportar, false);
        }
    }
    
    /**
     * Recarrega o relatório atual
     */
    async recarregarRelatorio() {
        if (this.filtros.validarFiltros()) {
            await this.gerarRelatorio();
        }
    }
    
    /**
     * Limpa todos os dados e reseta a aplicação
     */
    limparTudo() {
        // Limpar dados
        this.dadosRelatorio = null;
        
        // Limpar filtros
        this.filtros.limparFiltros();
        
        // Limpar localStorage
        localStorage.removeItem('relatorioReceitaFonte_filtros');
        
        // Resetar interface
        document.querySelector(this.config.SELETORES.CONTAINER_RELATORIO).style.display = 'none';
        document.querySelector(this.config.SELETORES.MENSAGEM_INICIAL).style.display = 'block';
        
        console.log('Sistema resetado');
    }
    
    /**
     * Obtém dados atuais do relatório
     * @returns {Object|null} Dados do relatório ou null
     */
    obterDadosAtuais() {
        return this.dadosRelatorio;
    }
    
    /**
     * Verifica se há relatório carregado
     * @returns {boolean} true se há relatório
     */
    temRelatorioCarregado() {
        return this.dadosRelatorio !== null && this.dadosRelatorio.tem_dados;
    }
    
    /**
     * Destrói a aplicação (limpeza)
     */
    destruir() {
        // Remover eventos
        this.eventos.destruir();
        
        // Limpar dados
        this.dadosRelatorio = null;
        
        // Limpar referências
        this.api = null;
        this.renderizador = null;
        this.filtros = null;
        this.eventos = null;
        this.exportador = null;
        
        console.log('Sistema destruído');
    }
}

// Criar e exportar instância do controlador principal
window.ControladorRelatorioReceitaFonte = new ControladorRelatorioReceitaFonte();

// Inicializar quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    // Verificar se estamos na página correta
    const formFiltros = document.querySelector('#formFiltros');
    if (formFiltros && document.querySelector('#tabelaRelatorio')) {
        window.ControladorRelatorioReceitaFonte.inicializar();
    }
});