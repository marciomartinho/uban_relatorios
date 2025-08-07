/**
 * Módulo de Configurações e Constantes
 * Centraliza todas as configurações do sistema de Balanço de Receitas
 */

const ConfiguracoesBalancoReceita = {
    // Endpoints da API
    API: {
        FILTROS: '/balanco-receita/api/filtros',
        GERAR_RELATORIO: '/balanco-receita/api/gerar-relatorio',
        LANCAMENTOS: '/balanco-receita/api/lancamentos',
        LANCAMENTOS_EXCEL: '/balanco-receita/api/lancamentos-excel'
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
    
    // Mapeamento de tipos de receita para fontes
    TIPOS_RECEITA: {
        '11': ['11', '71'], // Impostos, Taxas e Contribuições
        '12': ['12', '72'], // Contribuições
        '13': ['13', '73'], // Receita Patrimonial
        '14': ['14', '74'], // Receita Agropecuária
        '15': ['15', '75'], // Receita Industrial
        '16': ['16', '76'], // Receita de Serviços
        '17': ['17', '77'], // Transferências Correntes
        '19': ['19', '79'], // Outras Receitas Correntes
        '21': ['21'],       // Operações de Crédito
        '22': ['22'],       // Alienação de Bens
        '23': ['23'],       // Amortização de Empréstimos
        '24': ['24']        // Transferências de Capital
    },
    
    // Configurações de exportação
    EXPORTACAO: {
        IMAGEM: {
            ESCALA: 3,
            LARGURA: '297mm',
            FORMATO: 'image/png',
            QUALIDADE: 1.0,
            COR_FUNDO: '#ffffff'
        },
        EXCEL: {
            LARGURAS_COLUNAS: [60, 20, 20, 20, 20, 20, 15],
            NOME_ABA: 'Balanço Receita'
        }
    },
    
    // Configurações de renderização
    RENDERIZACAO: {
        PADDING_POR_NIVEL: 30,
        PADDING_EXTRA_UG: 10,
        DELAY_INTEGRACAO_MODULOS: 100,
        TEMPO_ALERTA: 5000
    },
    
    // Classes CSS
    CLASSES: {
        NIVEIS: {
            0: 'table-light fw-bold',
            1: '',
            2: '',
            3: '',
            4: 'table-info'
        },
        VARIACAO: {
            POSITIVA: 'text-success',
            NEGATIVA: 'text-danger'
        }
    },
    
    // Seletores DOM
    SELETORES: {
        FORM_FILTROS: '#formFiltros',
        SELECT_ANO: '#selectAno',
        SELECT_MES: '#selectMes',
        SELECT_UG: '#selectUG',
        SELECT_TIPO_RECEITA: '#selectTipoReceita',
        BTN_LIMPAR: '#btnLimpar',
        BTN_EXPORTAR: '#btnExportar',
        BTN_EXPORTAR_COMPLETO: '#btnExportarCompleto',
        BTN_DOWNLOAD_IMAGEM: '#btnDownloadImagem',
        BTN_IMPRIMIR: '#btnImprimir',
        CONTAINER_RELATORIO: '#relatorioContainer',
        MENSAGEM_INICIAL: '#mensagemInicial',
        TABELA_BALANCO: '#tabelaBalanco'
    }
};

// Exportar para uso em outros módulos
window.ConfiguracoesBalancoReceita = ConfiguracoesBalancoReceita;