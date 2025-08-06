/**
 * Módulo de Configurações e Constantes
 * Centraliza todas as configurações do sistema de Relatório Receita/Fonte
 * app/static/js/relatorio_receita_fonte/configuracoes.js
 */

const ConfiguracoesRelatorioReceitaFonte = {
    // Endpoints da API
    API: {
        BASE: '/relatorio-receita-fonte',
        FILTROS: '/relatorio-receita-fonte/api/filtros',
        GERAR: '/relatorio-receita-fonte/api/gerar',
        EXPORTAR: '/relatorio-receita-fonte/api/exportar',
        DETALHES: '/relatorio-receita-fonte/api/detalhes'
    },
    
    // Mapeamento de meses
    MESES: {
        1: 'Janeiro',
        2: 'Fevereiro',
        3: 'Março',
        4: 'Abril',
        5: 'Maio',
        6: 'Junho',
        7: 'Julho',
        8: 'Agosto',
        9: 'Setembro',
        10: 'Outubro',
        11: 'Novembro',
        12: 'Dezembro'
    },
    
    // Tipos de relatório
    TIPOS_RELATORIO: {
        'fonte': {
            titulo: 'Relatório por Fonte de Receita',
            header: 'FONTE DE RECEITA',
            campoSecundario: 'CÓDIGO DE RECEITA (ALÍNEA)'
        },
        'receita': {
            titulo: 'Relatório por Código de Receita',
            header: 'CÓDIGO DE RECEITA (ALÍNEA)',
            campoSecundario: 'FONTE DE RECEITA'
        }
    },
    
    // Configurações de exportação
    EXPORTACAO: {
        EXCEL: {
            NOME_ARQUIVO: 'relatorio_receita_fonte_{tipo}_{periodo}.xlsx',
            NOME_ABA: 'Relatório',
            LARGURAS_COLUNAS: [50, 20, 20, 20, 20, 20, 15]
        },
        IMAGEM: {
            ESCALA: 2,
            FORMATO: 'png',
            QUALIDADE: 0.95
        }
    },
    
    // Configurações de renderização
    RENDERIZACAO: {
        PADDING_POR_NIVEL: 30,
        DELAY_LOADING: 300,
        TEMPO_ALERTA: 5000,
        BATCH_SIZE: 100,
        DECIMAIS: 2
    },
    
    // Classes CSS
    CLASSES: {
        NIVEIS: {
            0: 'nivel-0 fw-bold table-light',
            1: 'nivel-1'
        },
        VARIACAO: {
            POSITIVA: 'text-success',
            NEGATIVA: 'text-danger',
            NEUTRA: 'text-muted'
        },
        EXPANDIDO: 'expandido',
        RECOLHIDO: 'recolhido',
        VISIVEL: 'visivel'
    },
    
    // Seletores DOM
    SELETORES: {
        // Formulário
        FORM_FILTROS: '#formFiltros',
        SELECT_TIPO: '#selectTipo',
        SELECT_ANO: '#selectAno',
        SELECT_MES: '#selectMes',
        SELECT_UG: '#selectUG',
        
        // Botões
        BTN_LIMPAR: '#btnLimpar',
        BTN_EXPORTAR: '#btnExportar',
        BTN_IMPRIMIR: '#btnImprimir',
        BTN_EXPANDIR_TODOS: '#btnExpandirTodos',
        BTN_RECOLHER_TODOS: '#btnRecolherTodos',
        
        // Containers
        CONTAINER_RELATORIO: '#relatorioContainer',
        CONTAINER_LOADING: '#loadingContainer',
        MENSAGEM_INICIAL: '#mensagemInicial',
        EMPTY_STATE: '#emptyState',
        
        // Tabela
        TABELA_RELATORIO: '#tabelaRelatorio',
        TBODY_RELATORIO: '#tbody-relatorio',
        
        // Headers e títulos
        TITULO_RELATORIO: '#tituloRelatorio',
        PERIODO_RELATORIO: '#periodoRelatorio',
        UG_RELATORIO: '#ugRelatorio',
        HEADER_TIPO: '#headerTipo',
        HEADER_ANO_ATUAL: '#headerAnoAtual',
        HEADER_ANO_ANTERIOR: '#headerAnoAnterior',
        DATA_GERACAO: '#dataGeracao',
        
        // Totais
        TOTAL_PREVISAO_INICIAL: '#totalPrevisaoInicial',
        TOTAL_PREVISAO_ATUALIZADA: '#totalPrevisaoAtualizada',
        TOTAL_RECEITA_ATUAL: '#totalReceitaAtual',
        TOTAL_RECEITA_ANTERIOR: '#totalReceitaAnterior',
        TOTAL_VARIACAO_ABSOLUTA: '#totalVariacaoAbsoluta',
        TOTAL_VARIACAO_PERCENTUAL: '#totalVariacaoPercentual'
    },
    
    // Ícones
    ICONES: {
        EXPANDIR: '▶',
        RECOLHER: '▼',
        LOADING: '<i class="bi bi-hourglass-split"></i>',
        SUCESSO: '<i class="bi bi-check-circle"></i>',
        ERRO: '<i class="bi bi-exclamation-triangle"></i>',
        INFO: '<i class="bi bi-info-circle"></i>'
    },
    
    // Mensagens
    MENSAGENS: {
        ERRO_FILTROS: 'Por favor, selecione ano e mês para gerar o relatório.',
        ERRO_GENERICO: 'Ocorreu um erro ao processar a solicitação.',
        SUCESSO_EXPORTACAO: 'Arquivo exportado com sucesso!',
        CARREGANDO: 'Carregando dados...',
        SEM_DADOS: 'Nenhum dado encontrado para os filtros selecionados.'
    },
    
    // Formatação
    FORMATACAO: {
        LOCALE: 'pt-BR',
        MOEDA: {
            style: 'currency',
            currency: 'BRL',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        },
        NUMERO: {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        },
        PERCENTUAL: {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }
    }
};

// Exportar para uso global
window.ConfigRelatorioReceitaFonte = ConfiguracoesRelatorioReceitaFonte;