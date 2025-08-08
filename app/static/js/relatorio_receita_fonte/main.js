// JavaScript Principal para Relatório Detalhado por Fonte/Receita
// Arquivo: app/static/js/relatorio_receita_fonte/main.js

// ========================================
// VARIÁVEIS GLOBAIS
// ========================================
window.RelatorioReceitaFonte = {
    dadosAtuais: [],
    totaisGerais: {},
    modoAtual: 'fonte',
    tabelaDados: null,
    dadosLancamentosCompletos: [],
    dadosInconsistencias: {
        'fonte-alinea': [],
        'alinea-ug': []
    },
    ultimaVerificacao: null,
    inconsistenciasResolvidas: {
        'fonte-alinea': {},
        'alinea-ug': {}
    }
};

// ========================================
// INICIALIZAÇÃO
// ========================================
$(document).ready(function() {
    console.log('Iniciando Relatório Receita/Fonte...');
    
    // Carregar estado salvo
    GerenciadorEstado.carregar();
    
    // Configurar eventos
    configurarEventos();
    configurarEventosInconsistencias();
    
    // Carregar dados iniciais
    carregarListaUGs();
    carregarEstatisticasInconsistencias();
});

// ========================================
// CONFIGURAÇÃO DE EVENTOS
// ========================================
function configurarEventos() {
    // Mudança de UG
    $('#filtroUG').on('change', function() {
        const ugSelecionada = $(this).val();
        const textoUG = ugSelecionada ? $('#filtroUG option:selected').text() : 'Consolidado';
        $('#badgeUGSelecionada').text(textoUG);
        console.log('UG alterada para:', ugSelecionada || 'Consolidado');
        TabelaPrincipal.carregar();
    });
    
    // Mudança de modo de visualização
    $('input[name="modoVisualizacao"]').on('change', function() {
        window.RelatorioReceitaFonte.modoAtual = $(this).val();
        console.log('Modo alterado para:', window.RelatorioReceitaFonte.modoAtual);
        TabelaPrincipal.carregar();
    });
    
    // Mudança de tipo de exibição
    $('#tipoExibicao').on('change', function() {
        TabelaPrincipal.atualizar();
    });
    
    // Toggle nomes completos
    $('#mostrarNomesCompletos').on('change', function() {
        const mostrarCompleto = $(this).is(':checked');
        if (mostrarCompleto) {
            $('#tabelaDados td:first-child, #tabelaDados th:first-child').css({
                'white-space': 'normal',
                'word-break': 'break-word',
                'max-width': 'none'
            });
        } else {
            $('#tabelaDados td:first-child, #tabelaDados th:first-child').css({
                'white-space': 'nowrap',
                'word-break': 'normal',
                'max-width': '500px'
            });
        }
    });
    
    // Botões de ação
    $('#btnExpandirTodos').on('click', TabelaPrincipal.expandirTodos);
    $('#btnRecolherTodos').on('click', TabelaPrincipal.recolherTodos);
    $('#btnAtualizar').on('click', TabelaPrincipal.carregar);
    $('#btnExportar').on('click', Exportacao.exportarPrincipal);
    
    // Fechar modal
    $('#btnFecharModal').on('click', function() {
        $('#modalDetalhes').modal('hide');
    });
    
    // Exportar detalhes do modal
    $('#btnExportarDetalhes').on('click', Exportacao.exportarDetalhes);
}

function configurarEventosInconsistencias() {
    // Botão principal de verificação
    $('#btnVerificarInconsistencias').on('click', function() {
        $('#modalInconsistencias').modal('show');
        Inconsistencias.verificarTodas();
    });
    
    // Eventos delegados para elementos dinâmicos
    $(document).on('click', '.btn-atualizar', function() {
        const tipo = $(this).data('tipo');
        Inconsistencias.verificar(tipo);
    });
    
    $(document).on('click', '.btn-exportar-excel', function() {
        const tipo = $(this).data('tipo');
        Exportacao.exportarInconsistencias(tipo);
    });
    
    $(document).on('change', '.filtro-status', function() {
        const tipo = $(this).data('tipo');
        Inconsistencias.aplicarFiltro(tipo);
    });
    
    $(document).on('change', '.checkbox-todos', function() {
        const tipo = $(this).data('tipo');
        const isChecked = $(this).is(':checked');
        Inconsistencias.marcarTodos(tipo, isChecked);
    });
    
    $(document).on('click', '.btn-exportar-estado', function() {
        const tipo = $(this).data('tipo');
        GerenciadorEstado.exportar(tipo);
    });
    
    $(document).on('click', '.btn-importar-estado', function() {
        const tipo = $(this).data('tipo');
        $(`.file-importar-estado[data-tipo="${tipo}"]`).click();
    });
    
    $(document).on('change', '.file-importar-estado', function(e) {
        const tipo = $(this).data('tipo');
        GerenciadorEstado.importar(e, tipo);
    });
    
    // Eventos de checkbox de resolução
    $(document).on('change', '.checkbox-resolvido', function() {
        const tipo = $(this).closest('table').data('tipo');
        const chaveDoc = $(this).data('documento');
        const isChecked = $(this).is(':checked');
        const row = $(this).closest('tr');
        
        GerenciadorEstado.marcarResolvida(tipo, chaveDoc, isChecked);
        
        if (isChecked) {
            row.addClass('linha-resolvida');
        } else {
            row.removeClass('linha-resolvida');
        }
        
        Inconsistencias.atualizarContagem(tipo);
    });
}

// ========================================
// FUNÇÕES DE CARREGAMENTO
// ========================================
function carregarListaUGs() {
    console.log('Carregando lista de UGs...');
    
    $.ajax({
        url: '/relatorio-receita-fonte/api/lista-ugs',
        method: 'GET',
        success: function(response) {
            console.log('✅ Lista de UGs carregada:', response.total, 'UGs');
            
            $('#filtroUG').html('<option value="">Consolidado (Todas as UGs)</option>');
            
            response.ugs.forEach(function(ug) {
                const option = $('<option></option>')
                    .attr('value', ug.coug)
                    .text(ug.coug + ' - ' + ug.noug);
                $('#filtroUG').append(option);
            });
            
            const label = $('label[for="filtroUG"]');
            label.html('Unidade Gestora (UG): <span class="badge bg-secondary">' + response.total + ' UGs disponíveis</span>');
            
            TabelaPrincipal.carregar();
        },
        error: function(xhr) {
            console.error('❌ Erro ao carregar lista de UGs:', xhr);
            TabelaPrincipal.carregar();
        }
    });
}

function carregarEstatisticasInconsistencias() {
    $.ajax({
        url: '/relatorio-receita-fonte/api/estatisticas-inconsistencias',
        method: 'GET',
        success: function(response) {
            const total = response.total || 0;
            
            if (total > 0) {
                $('#badgeInconsistenciasTotal').text(total).show();
                $('#btnVerificarInconsistencias').removeClass('btn-warning').addClass('btn-danger');
            } else {
                $('#badgeInconsistenciasTotal').hide();
            }
            
            // Atualizar badges das tabs
            $('#badgeFonteAlinea').text(response.fonte_alinea || 0);
            $('#badgeAlineaUG').text(response.alinea_ug || 0);
        },
        error: function(xhr) {
            console.error('Erro ao carregar estatísticas de inconsistências:', xhr);
        }
    });
}

// Expor função global para uso em botões inline
window.verDetalhesInconsistencia = function(cofonte, coalinea, tipo) {
    $('#modalInconsistencias').modal('hide');
    
    const dados = window.RelatorioReceitaFonte.dadosInconsistencias[tipo || 'fonte-alinea'];
    const item = dados.find(i => i.cofonte === cofonte && i.coalinea === coalinea);
    
    if (item) {
        ModalDetalhes.abrir(cofonte, coalinea, item.nofonte, item.noalinea);
    }
};