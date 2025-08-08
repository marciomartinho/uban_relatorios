// Módulo de Exportação
// Arquivo: app/static/js/relatorio_receita_fonte/exportacao.js

window.Exportacao = {
    // ========================================
    // EXPORTAR PRINCIPAL
    // ========================================
    exportarPrincipal: function() {
        const dados = window.RelatorioReceitaFonte.dadosAtuais;
        const modoAtual = window.RelatorioReceitaFonte.modoAtual;
        const totais = window.RelatorioReceitaFonte.totaisGerais;
        
        if (!dados || dados.length === 0) {
            alert('Não há dados para exportar!');
            return;
        }
        
        console.log('📊 Exportando dados principais...');
        
        let csv = [];
        const tipoExibicao = $('#tipoExibicao').val();
        const ugSelecionada = $('#filtroUG').val();
        const textoUG = ugSelecionada ? $('#filtroUG option:selected').text() : 'Consolidado (Todas as UGs)';
        
        // Cabeçalho
        csv.push(['RELATÓRIO DETALHADO POR ' + (modoAtual === 'fonte' ? 'FONTE' : 'RECEITA')].join(';'));
        csv.push(['UG: ' + textoUG].join(';'));
        csv.push('');
        
        // Headers
        const headers = [
            modoAtual === 'fonte' ? 'Fonte' : 'Alínea',
            modoAtual === 'fonte' ? 'Alínea' : 'Fonte',
            'Previsão Inicial',
            'Previsão Atualizada',
            'Realizada ' + $('#anoAtual').text(),
            'Realizada ' + (parseInt($('#anoAtual').text()) - 1),
            'Variação R$',
            'Variação %'
        ];
        csv.push(headers.join(';'));
        
        // Dados
        dados.forEach(function(item) {
            const itemId = modoAtual === 'fonte' ? item.cofonte : item.coalinea;
            const itemNome = modoAtual === 'fonte' ? item.nome_fonte : item.nome_alinea;
            const subitens = modoAtual === 'fonte' ? item.alineas : item.fontes;
            
            // Linha principal
            let linha = [
                Utilitarios.formatarParaExport(itemId, itemNome, tipoExibicao),
                'TOTAL',
                item.previsao_inicial.toFixed(2).replace('.', ','),
                item.previsao_atualizada.toFixed(2).replace('.', ','),
                item.realizada_atual.toFixed(2).replace('.', ','),
                item.realizada_anterior.toFixed(2).replace('.', ','),
                item.variacao_absoluta.toFixed(2).replace('.', ','),
                item.variacao_percentual.toFixed(2).replace('.', ',')
            ];
            csv.push(linha.join(';'));
            
            // Subitens
            if (subitens && subitens.length > 0) {
                subitens.forEach(function(subitem) {
                    const subitemId = modoAtual === 'fonte' ? subitem.coalinea : subitem.cofonte;
                    const subitemNome = modoAtual === 'fonte' ? subitem.nome_alinea : subitem.nome_fonte;
                    
                    let subLinha = [
                        '',
                        Utilitarios.formatarParaExport(subitemId, subitemNome, tipoExibicao),
                        subitem.previsao_inicial.toFixed(2).replace('.', ','),
                        subitem.previsao_atualizada.toFixed(2).replace('.', ','),
                        subitem.realizada_atual.toFixed(2).replace('.', ','),
                        subitem.realizada_anterior.toFixed(2).replace('.', ','),
                        subitem.variacao_absoluta.toFixed(2).replace('.', ','),
                        subitem.variacao_percentual.toFixed(2).replace('.', ',')
                    ];
                    csv.push(subLinha.join(';'));
                });
            }
        });
        
        // Total geral
        csv.push('');
        let linhaTotal = [
            'TOTAL GERAL',
            '',
            totais.previsao_inicial.toFixed(2).replace('.', ','),
            totais.previsao_atualizada.toFixed(2).replace('.', ','),
            totais.realizada_atual.toFixed(2).replace('.', ','),
            totais.realizada_anterior.toFixed(2).replace('.', ','),
            (totais.variacao_absoluta || 0).toFixed(2).replace('.', ','),
            (totais.variacao_percentual || 0).toFixed(2).replace('.', ',')
        ];
        csv.push(linhaTotal.join(';'));
        
        // Rodapé
        csv.push('');
        csv.push(['Data da exportação: ' + new Date().toLocaleString('pt-BR')].join(';'));
        
        // Download
        const csvContent = Utilitarios.converterParaCSV([], null);
        const nomeArquivo = 'relatorio_' + modoAtual + '_' + Utilitarios.obterTimestamp() + '.csv';
        
        // Usar o conteúdo já formatado
        Utilitarios.baixarArquivo('\ufeff' + csv.join('\n'), nomeArquivo);
    },
    
    // ========================================
    // EXPORTAR DETALHES
    // ========================================
    exportarDetalhes: function() {
        const dados = window.RelatorioReceitaFonte.dadosLancamentosCompletos;
        
        if (!dados || !dados.cofonte) {
            alert('Não há dados para exportar!');
            return;
        }
        
        console.log('📊 Exportando detalhes completos...');
        
        const btnOriginal = $('#btnExportarDetalhes').html();
        $('#btnExportarDetalhes').html('<span class="spinner-border spinner-border-sm"></span> Baixando todos os dados...');
        $('#btnExportarDetalhes').prop('disabled', true);
        
        const coug = $('#filtroUG').val();
        
        const params = {
            cofonte: dados.cofonte,
            coalinea: dados.coalinea,
            ano: dados.ano,
            exportar: 'true'
        };
        
        if (coug) {
            params.coug = coug;
        }
        
        $.ajax({
            url: '/relatorio-receita-fonte/api/detalhes-lancamentos',
            method: 'GET',
            data: params,
            success: function(response) {
                console.log('✅ Dados completos carregados para exportação');
                
                let csv = [];
                
                // Cabeçalho
                csv.push(['RELATÓRIO DE DETALHES DE LANÇAMENTOS'].join(';'));
                csv.push(['Fonte: ' + response.cofonte + ' - ' + response.nome_fonte].join(';'));
                csv.push(['Alínea: ' + response.coalinea + ' - ' + response.nome_alinea].join(';'));
                csv.push(['Ano: ' + response.ano].join(';'));
                csv.push(['Total de Registros: ' + response.total_registros].join(';'));
                csv.push('');
                
                // Resumo
                csv.push(['RESUMO'].join(';'));
                csv.push(['Total Débito;' + response.total_debito.toFixed(2).replace('.', ',')].join(''));
                csv.push(['Total Crédito;' + response.total_credito.toFixed(2).replace('.', ',')].join(''));
                csv.push(['Saldo;' + response.saldo.toFixed(2).replace('.', ',')].join(''));
                csv.push('');
                
                // Headers
                const headers = [
                    'Conta Contábil',
                    'Descrição Conta',
                    'UG Emitente',
                    'Nome UG',
                    'Documento',
                    'Evento',
                    'Descrição Evento',
                    'Data Lançamento',
                    'D/C',
                    'Valor',
                    'Grupo'
                ];
                csv.push(headers.join(';'));
                
                // Dados
                response.dados.forEach(function(item) {
                    let linha = [
                        item.cocontacontabil,
                        item.nocontacontabil || '',
                        item.coug,
                        item.noug || '',
                        item.nudocumento,
                        item.coevento,
                        item.noevento || '',
                        item.dalancamento || '',
                        item.indebitocredito,
                        item.valancamento.toFixed(2).replace('.', ','),
                        item.cogrupo || ''
                    ];
                    csv.push(linha.join(';'));
                });
                
                // Rodapé
                csv.push('');
                csv.push(['Data da exportação: ' + new Date().toLocaleString('pt-BR')].join(';'));
                
                // Download
                const nomeArquivo = 'detalhes_lancamentos_' + response.cofonte + '_' + response.coalinea + '_' + Utilitarios.obterTimestamp() + '.csv';
                Utilitarios.baixarArquivo('\ufeff' + csv.join('\n'), nomeArquivo);
                
                $('#btnExportarDetalhes').html(btnOriginal);
                $('#btnExportarDetalhes').prop('disabled', false);
            },
            error: function(xhr) {
                console.error('❌ Erro ao exportar:', xhr);
                alert('Erro ao exportar dados. Tente novamente.');
                
                $('#btnExportarDetalhes').html(btnOriginal);
                $('#btnExportarDetalhes').prop('disabled', false);
            }
        });
    },
    
    // ========================================
    // EXPORTAR INCONSISTÊNCIAS
    // ========================================
    exportarInconsistencias: function(tipo) {
        console.log(`📊 Exportando inconsistências ${tipo}...`);
        
        const dados = window.RelatorioReceitaFonte.dadosInconsistencias[tipo];
        const resolvidas = window.RelatorioReceitaFonte.inconsistenciasResolvidas[tipo];
        
        if (!dados || dados.length === 0) {
            alert('Não há dados para exportar!');
            return;
        }
        
        const btnOriginal = $(`.btn-exportar-excel[data-tipo="${tipo}"]`).html();
        $(`.btn-exportar-excel[data-tipo="${tipo}"]`).html('<span class="spinner-border spinner-border-sm"></span> Exportando...');
        $(`.btn-exportar-excel[data-tipo="${tipo}"]`).prop('disabled', true);
        
        let csv = [];
        
        // Título baseado no tipo
        const titulo = tipo === 'fonte-alinea' 
            ? 'RELATÓRIO DE INCONSISTÊNCIAS - FONTE/ALÍNEA NÃO CADASTRADAS'
            : 'RELATÓRIO DE INCONSISTÊNCIAS - ALÍNEA 7 COM UG DIVERGENTE';
        
        // Cabeçalho
        csv.push([titulo].join(';'));
        csv.push(['Data da verificação: ' + new Date().toLocaleString('pt-BR')].join(';'));
        csv.push(['Exercício: ' + new Date().getFullYear()].join(';'));
        csv.push('');
        
        // Resumo
        csv.push(['RESUMO'].join(';'));
        csv.push(['Total de Documentos;' + dados.length].join(''));
        csv.push(['Documentos Resolvidos;' + Object.keys(resolvidas || {}).length].join(''));
        csv.push(['Documentos Pendentes;' + (dados.length - Object.keys(resolvidas || {}).length)].join(''));
        csv.push('');
        
        // Headers específicos por tipo
        let headers;
        if (tipo === 'fonte-alinea') {
            headers = [
                'Status',
                'Documento',
                'UG Contábil',
                'Nome UG',
                'Código Evento',
                'Nome Evento',
                'Código Fonte',
                'Nome Fonte',
                'Código Alínea',
                'Nome Alínea',
                'Data Lançamento',
                'D/C',
                'Valor'
            ];
        } else {
            headers = [
                'Status',
                'Documento',
                'UG Contábil',
                'Nome UG Contábil',
                'UG Emitente',
                'Nome UG Emitente',
                'Código Evento',
                'Nome Evento',
                'Código Fonte',
                'Nome Fonte',
                'Código Alínea',
                'Nome Alínea',
                'Data Lançamento',
                'D/C',
                'Valor'
            ];
        }
        csv.push(headers.join(';'));
        
        // Dados
        dados.forEach(function(item) {
            const chaveDoc = `${item.nudocumento}_${item.cofonte}_${item.coalinea}`;
            const status = resolvidas && resolvidas[chaveDoc] ? 'RESOLVIDO' : 'PENDENTE';
            
            let linha;
            if (tipo === 'fonte-alinea') {
                linha = [
                    status,
                    item.nudocumento,
                    item.cougcontab || '',
                    item.noug || '',
                    item.coevento || '',
                    item.noevento || '',
                    item.cofonte,
                    item.nofonte || '',
                    item.coalinea,
                    item.noalinea || '',
                    item.dalancamento ? new Date(item.dalancamento).toLocaleDateString('pt-BR') : '',
                    item.indebitocredito || '',
                    Math.abs(item.valancamento).toFixed(2).replace('.', ',')
                ];
            } else {
                linha = [
                    status,
                    item.nudocumento,
                    item.cougcontab || '',
                    item.noug_contabil || '',
                    item.coug || '',
                    item.noug_emitente || '',
                    item.coevento || '',
                    item.noevento || '',
                    item.cofonte,
                    item.nofonte || '',
                    item.coalinea,
                    item.noalinea || '',
                    item.dalancamento ? new Date(item.dalancamento).toLocaleDateString('pt-BR') : '',
                    item.indebitocredito || '',
                    Math.abs(item.valancamento).toFixed(2).replace('.', ',')
                ];
            }
            csv.push(linha.join(';'));
        });
        
        // Rodapé
        csv.push('');
        
        if (tipo === 'alinea-ug') {
            csv.push(['REGRA: Quando a alínea começa com 7, a UG contábil deve ser igual à UG emitente'].join(';'));
        }
        
        csv.push(['Data da exportação: ' + new Date().toLocaleString('pt-BR')].join(';'));
        
        // Download
        const nomeArquivo = `inconsistencias_${tipo}_${Utilitarios.obterTimestamp()}.csv`;
        Utilitarios.baixarArquivo('\ufeff' + csv.join('\n'), nomeArquivo);
        
        $(`.btn-exportar-excel[data-tipo="${tipo}"]`).html(btnOriginal);
        $(`.btn-exportar-excel[data-tipo="${tipo}"]`).prop('disabled', false);
    }
};