// Módulo de Tabela Principal
// Arquivo: app/static/js/relatorio_receita_fonte/tabela_principal.js

window.TabelaPrincipal = {
    // ========================================
    // CARREGAR DADOS
    // ========================================
    carregar: function() {
        console.log('Carregando dados - Modo:', window.RelatorioReceitaFonte.modoAtual);
        
        const ugSelecionada = $('#filtroUG').val();
        console.log('UG selecionada:', ugSelecionada || 'Consolidado');
        
        Utilitarios.mostrarCarregando('#divTabela');
        
        const url = window.RelatorioReceitaFonte.modoAtual === 'fonte' 
            ? '/relatorio-receita-fonte/api/dados-por-fonte'
            : '/relatorio-receita-fonte/api/dados-por-receita';
        
        const params = ugSelecionada ? { coug: ugSelecionada } : {};
        
        $.ajax({
            url: url,
            method: 'GET',
            data: params,
            success: function(response) {
                console.log('✅ Dados carregados:', response);
                
                window.RelatorioReceitaFonte.dadosAtuais = response.dados;
                window.RelatorioReceitaFonte.totaisGerais = response.totais;
                
                $('#anoAtual').text(response.ano_atual);
                
                TabelaPrincipal.atualizarCards();
                TabelaPrincipal.construir();
                
                $('#tituloModo').text(window.RelatorioReceitaFonte.modoAtual === 'fonte' ? 'por Fonte' : 'por Receita');
                $('#badgeRegistros').text(window.RelatorioReceitaFonte.dadosAtuais.length + ' registros principais');
            },
            error: function(xhr) {
                console.error('❌ Erro ao carregar dados:', xhr);
                
                let erro = xhr.responseJSON ? xhr.responseJSON.erro : 'Erro desconhecido';
                $('#divTabela').html('<div class="alert alert-danger" role="alert"><i class="bi bi-exclamation-triangle"></i> Erro ao carregar dados: ' + erro + '</div>');
            }
        });
    },
    
    // ========================================
    // ATUALIZAR CARDS
    // ========================================
    atualizarCards: function() {
        const totais = window.RelatorioReceitaFonte.totaisGerais;
        
        $('#totalPrevisaoInicial').text(Utilitarios.formatarMoeda(totais.previsao_inicial));
        $('#totalPrevisaoAtualizada').text(Utilitarios.formatarMoeda(totais.previsao_atualizada));
        $('#totalRealizadaAtual').text(Utilitarios.formatarMoeda(totais.realizada_atual));
        
        const variacao = totais.variacao_percentual || 0;
        const variacaoFormatada = Math.abs(variacao).toFixed(2) + '%';
        
        let htmlVariacao = '';
        if (variacao > 0) {
            htmlVariacao = '<span class="text-success">↑ ' + variacaoFormatada + '</span>';
        } else if (variacao < 0) {
            htmlVariacao = '<span class="text-danger">↓ ' + variacaoFormatada + '</span>';
        } else {
            htmlVariacao = '<span class="text-muted">→ ' + variacaoFormatada + '</span>';
        }
        
        $('#totalVariacao').html(htmlVariacao);
    },
    
    // ========================================
    // CONSTRUIR TABELA
    // ========================================
    construir: function() {
        const dados = window.RelatorioReceitaFonte.dadosAtuais;
        const modoAtual = window.RelatorioReceitaFonte.modoAtual;
        const totais = window.RelatorioReceitaFonte.totaisGerais;
        
        if (!dados || dados.length === 0) {
            $('#divTabela').html('<p class="text-center text-muted py-3">Nenhum dado encontrado.</p>');
            return;
        }
        
        if (window.RelatorioReceitaFonte.tabelaDados) {
            window.RelatorioReceitaFonte.tabelaDados.destroy();
            $('#divTabela').empty();
        }
        
        let html = '<table id="tabelaDados" class="table table-hover">';
        
        // Header
        html += '<thead class="table-light">';
        html += '<tr>';
        html += '<th style="width: 30%">' + (modoAtual === 'fonte' ? 'Fonte / Alínea' : 'Alínea / Fonte') + '</th>';
        html += '<th class="text-end">Previsão Inicial</th>';
        html += '<th class="text-end">Previsão Atualizada</th>';
        html += '<th class="text-end">Realizada ' + $('#anoAtual').text() + '</th>';
        html += '<th class="text-end">Realizada ' + (parseInt($('#anoAtual').text()) - 1) + '</th>';
        html += '<th class="text-end">Variação R$</th>';
        html += '<th class="text-end">Variação %</th>';
        html += '<th class="text-center">Ações</th>';
        html += '</tr>';
        html += '</thead>';
        
        html += '<tbody>';
        
        // Dados
        dados.forEach(function(item, index) {
            const itemId = modoAtual === 'fonte' ? item.cofonte : item.coalinea;
            const itemNome = modoAtual === 'fonte' ? item.nome_fonte : item.nome_alinea;
            const subitens = modoAtual === 'fonte' ? item.alineas : item.fontes;
            
            if (subitens && subitens.length > 0) {
                subitens.sort((a, b) => b.realizada_atual - a.realizada_atual);
            }
            
            // Linha principal
            html += '<tr class="linha-principal" data-id="' + itemId + '">';
            html += '<td class="text-nowrap">';
            html += '<button class="btn btn-sm btn-link btn-expandir" data-target="' + itemId + '">';
            html += '<i class="bi bi-chevron-right"></i>';
            html += '</button> ';
            html += '<strong>' + Utilitarios.formatarCodigoDescricao(itemId, itemNome) + '</strong>';
            html += ' <span class="badge bg-secondary">' + (subitens ? subitens.length : 0) + '</span>';
            html += '</td>';
            html += '<td class="text-end">' + Utilitarios.formatarMoeda(item.previsao_inicial) + '</td>';
            html += '<td class="text-end">' + Utilitarios.formatarMoeda(item.previsao_atualizada) + '</td>';
            html += '<td class="text-end">' + Utilitarios.formatarMoeda(item.realizada_atual) + '</td>';
            html += '<td class="text-end">' + Utilitarios.formatarMoeda(item.realizada_anterior) + '</td>';
            html += '<td class="text-end ' + Utilitarios.getClasseVariacao(item.variacao_absoluta) + '">';
            html += Utilitarios.formatarMoeda(item.variacao_absoluta);
            html += '</td>';
            html += '<td class="text-end ' + Utilitarios.getClasseVariacao(item.variacao_percentual) + '">';
            html += Utilitarios.formatarVariacaoPercentual(item.variacao_percentual);
            html += '</td>';
            html += '<td></td>';
            html += '</tr>';
            
            // Subitens
            if (subitens && subitens.length > 0) {
                subitens.forEach(function(subitem) {
                    const subitemId = modoAtual === 'fonte' ? subitem.coalinea : subitem.cofonte;
                    const subitemNome = modoAtual === 'fonte' ? subitem.nome_alinea : subitem.nome_fonte;
                    
                    html += '<tr class="linha-filha collapse-' + itemId + '" style="display: none;">';
                    html += '<td class="ps-5 text-nowrap">';
                    html += '<span class="text-muted">└─</span> ' + Utilitarios.formatarCodigoDescricao(subitemId, subitemNome);
                    html += '</td>';
                    html += '<td class="text-end">' + Utilitarios.formatarMoeda(subitem.previsao_inicial) + '</td>';
                    html += '<td class="text-end">' + Utilitarios.formatarMoeda(subitem.previsao_atualizada) + '</td>';
                    html += '<td class="text-end">' + Utilitarios.formatarMoeda(subitem.realizada_atual) + '</td>';
                    html += '<td class="text-end">' + Utilitarios.formatarMoeda(subitem.realizada_anterior) + '</td>';
                    html += '<td class="text-end ' + Utilitarios.getClasseVariacao(subitem.variacao_absoluta) + '">';
                    html += Utilitarios.formatarMoeda(subitem.variacao_absoluta);
                    html += '</td>';
                    html += '<td class="text-end ' + Utilitarios.getClasseVariacao(subitem.variacao_percentual) + '">';
                    html += Utilitarios.formatarVariacaoPercentual(subitem.variacao_percentual);
                    html += '</td>';
                    html += '<td class="text-center">';
                    
                    if (modoAtual === 'fonte') {
                        html += '<button class="btn btn-sm btn-outline-primary btn-detalhes" ';
                        html += 'data-cofonte="' + itemId + '" ';
                        html += 'data-coalinea="' + subitemId + '" ';
                        html += 'data-nome-fonte="' + (itemNome || '') + '" ';
                        html += 'data-nome-alinea="' + (subitemNome || '') + '">';
                    } else {
                        html += '<button class="btn btn-sm btn-outline-primary btn-detalhes" ';
                        html += 'data-cofonte="' + subitemId + '" ';
                        html += 'data-coalinea="' + itemId + '" ';
                        html += 'data-nome-fonte="' + (subitemNome || '') + '" ';
                        html += 'data-nome-alinea="' + (itemNome || '') + '">';
                    }
                    html += '<i class="bi bi-eye"></i> Detalhes';
                    html += '</button>';
                    html += '</td>';
                    html += '</tr>';
                });
            }
        });
        
        html += '</tbody>';
        
        // Footer com totais
        html += '<tfoot class="table-light">';
        html += '<tr class="fw-bold">';
        html += '<td>TOTAL GERAL</td>';
        html += '<td class="text-end">' + Utilitarios.formatarMoeda(totais.previsao_inicial) + '</td>';
        html += '<td class="text-end">' + Utilitarios.formatarMoeda(totais.previsao_atualizada) + '</td>';
        html += '<td class="text-end">' + Utilitarios.formatarMoeda(totais.realizada_atual) + '</td>';
        html += '<td class="text-end">' + Utilitarios.formatarMoeda(totais.realizada_anterior) + '</td>';
        html += '<td class="text-end ' + Utilitarios.getClasseVariacao(totais.variacao_absoluta) + '">';
        html += Utilitarios.formatarMoeda(totais.variacao_absoluta);
        html += '</td>';
        html += '<td class="text-end ' + Utilitarios.getClasseVariacao(totais.variacao_percentual) + '">';
        html += Utilitarios.formatarVariacaoPercentual(totais.variacao_percentual);
        html += '</td>';
        html += '<td></td>';
        html += '</tr>';
        html += '</tfoot>';
        
        html += '</table>';
        
        $('#divTabela').html(html);
        
        // Configurar eventos
        this.configurarEventosTabela();
    },
    
    // ========================================
    // CONFIGURAR EVENTOS DA TABELA
    // ========================================
    configurarEventosTabela: function() {
        // Expandir/Recolher
        $('.btn-expandir').on('click', function() {
            const target = $(this).data('target');
            const icon = $(this).find('i');
            const linhasFilhas = $('.collapse-' + target);
            
            if (linhasFilhas.is(':visible')) {
                linhasFilhas.hide();
                icon.removeClass('bi-chevron-down').addClass('bi-chevron-right');
            } else {
                linhasFilhas.show();
                icon.removeClass('bi-chevron-right').addClass('bi-chevron-down');
            }
        });
        
        // Botão detalhes
        $('.btn-detalhes').on('click', function() {
            const cofonte = $(this).data('cofonte');
            const coalinea = $(this).data('coalinea');
            const nomeFonte = $(this).data('nome-fonte');
            const nomeAlinea = $(this).data('nome-alinea');
            
            console.log('Ver detalhes - Fonte:', cofonte, 'Alínea:', coalinea);
            ModalDetalhes.abrir(cofonte, coalinea, nomeFonte, nomeAlinea);
        });
    },
    
    // ========================================
    // EXPANDIR/RECOLHER TODOS
    // ========================================
    expandirTodos: function() {
        $('.linha-filha').show();
        $('.btn-expandir i').removeClass('bi-chevron-right').addClass('bi-chevron-down');
    },
    
    recolherTodos: function() {
        $('.linha-filha').hide();
        $('.btn-expandir i').removeClass('bi-chevron-down').addClass('bi-chevron-right');
    },
    
    // ========================================
    // ATUALIZAR EXIBIÇÃO
    // ========================================
    atualizar: function() {
        this.construir();
    }
};