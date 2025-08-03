// JavaScript para Detalha Conta Contábil Receita
console.log('Arquivo detalha_receita.js carregado');

let tabelaDados = null;
let dadosAtuais = [];
let totaisOriginais = null; // Guardar totais originais

// Mapeamento de nomes de colunas
const nomesColunas = {
    'mes': 'Mês',
    'nudocumento': 'Documento',
    'coevento': 'Evento',
    'cocontacorrente': 'Conta Corrente',
    'valancamento': 'Valor',
    'indebitocredito': 'D/C',
    'coug': 'UG',
    'dalancamento': 'Data',
    'tipo_lancamento': 'Tipo'
};

// Ordem correta dos meses
const ordemMeses = {
    1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6,
    7: 7, 8: 8, 9: 9, 10: 10, 11: 11, 12: 12
};

// Inicialização
$(document).ready(function() {
    console.log('Página carregada, iniciando...');
    
    // IMPORTANTE: Garantir que o modal está fechado ao carregar a página
    setTimeout(function() {
        $('#modalLoading').modal('hide');
        $('.modal-backdrop').remove();
        $('body').removeClass('modal-open');
        $('body').css('overflow', 'auto');
    }, 100);
    
    carregarFiltros();
    configurarEventos();
});

// Função para mostrar erros
function mostrarErro(elemento, mensagem) {
    $(elemento).html(`
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class="bi bi-exclamation-triangle"></i> ${mensagem}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `);
}

// Carregar opções dos filtros
function carregarFiltros() {
    console.log('Iniciando carregamento de filtros...');
    console.log('🦆 Usando dados do DuckDB local');
    
    const url = '/detalha-receita/api/filtros';
    console.log('URL da API:', url);
    
    $.ajax({
        url: url,
        method: 'GET',
        timeout: 30000, // 30 segundos de timeout
        beforeSend: function() {
            console.log('Enviando requisição...');
            // Desabilitar selects enquanto carrega
            $('#selectAno, #selectConta, #selectUG').prop('disabled', true);
        },
        success: function(data) {
            console.log('✅ Filtros carregados com sucesso:', data);
            
            // Verificar se data existe
            if (!data) {
                console.error('❌ Resposta vazia da API');
                $('#modalLoading').modal('hide');
                return;
            }
            
            // Anos
            $('#selectAno').empty().append('<option value="">Selecione o ano...</option>');
            if (data.anos && data.anos.length > 0) {
                data.anos.forEach(function(ano) {
                    $('#selectAno').append(`<option value="${ano}">${ano}</option>`);
                });
            }
            
            // Contas
            $('#selectConta').empty().append('<option value="">Selecione a conta...</option>');
            if (data.contas && data.contas.length > 0) {
                data.contas.forEach(function(conta) {
                    $('#selectConta').append(`<option value="${conta}">${conta}</option>`);
                });
            }
            
            // UGs Contábeis
            $('#selectUG').empty().append('<option value="">Selecione a UG Contábil...</option>');
            $('#selectUG').append('<option value="CONSOLIDADO">CONSOLIDADO</option>');
            if (data.ugs && data.ugs.length > 0) {
                data.ugs.forEach(function(ug) {
                    $('#selectUG').append(`<option value="${ug}">${ug}</option>`);
                });
            }
            
            // Adicionar badge indicando fonte local
            if (data.fonte === 'DuckDB Local' && !$('#badgeLocal').length) {
                $('h2').append(' <span id="badgeLocal" class="badge bg-info ms-2">DuckDB Local</span>');
            }
            
            // Habilitar selects novamente
            $('#selectAno, #selectConta, #selectUG').prop('disabled', false);
            
            // Fechar modal de loading se estiver aberto
            $('#modalLoading').modal('hide');
            $('.modal-backdrop').remove();
        },
        error: function(xhr, textStatus, errorThrown) {
            console.error('❌ Erro ao carregar filtros:', textStatus, errorThrown);
            console.error('Status:', xhr.status);
            console.error('Response:', xhr.responseText);
            console.error('Detalhes completos:', xhr);
            
            // IMPORTANTE: Fechar o modal de loading em caso de erro
            $('#modalLoading').modal('hide');
            $('.modal-backdrop').remove();
            
            let erro = 'Erro desconhecido';
            if (textStatus === 'timeout') {
                erro = 'Tempo limite excedido. A consulta está demorando muito.';
            } else if (xhr.status === 500) {
                erro = 'Erro no servidor. Verifique se o DuckDB está acessível.';
            } else if (xhr.responseJSON && xhr.responseJSON.erro) {
                erro = xhr.responseJSON.erro;
            } else if (xhr.responseText) {
                erro = 'Erro no servidor: ' + xhr.responseText.substring(0, 200);
            }
            
            // Mostrar erro na tela
            mostrarErro('#mensagemInicial', 'Erro ao carregar filtros: ' + erro);
            
            // Habilitar selects novamente
            $('#selectAno, #selectConta, #selectUG').prop('disabled', false);
        }
    });
}

// Configurar eventos
function configurarEventos() {
    $('#formFiltros').on('submit', function(e) {
        e.preventDefault();
        consultarDados();
    });
    
    $('#btnLimpar').on('click', function() {
        limparFiltros();
    });
    
    $('#btnExportar').on('click', function() {
        exportarExcel();
    });
}

// Limpar filtros
function limparFiltros() {
    $('#selectAno').val('');
    $('#selectConta').val('');
    $('#selectUG').val('');
    
    $('#areaResultados').hide();
    $('#mensagemInicial').show();
    
    if (tabelaDados) {
        tabelaDados.destroy();
        $('#divTabela').empty();
    }
    
    // Limpar totais
    $('#totalCreditos').text('R$ 0,00');
    $('#totalDebitos').text('R$ 0,00');
    $('#saldoTotal').text('R$ 0,00');
    $('#qtdCreditos').text('0 lançamentos');
    $('#qtdDebitos').text('0 lançamentos');
    $('#totalLancamentos').text('0');
    $('#formulaSaldo').text('');
    
    // Limpar variáveis
    dadosAtuais = [];
    totaisOriginais = null;
}

// Consultar dados
function consultarDados() {
    const ano = $('#selectAno').val();
    const conta = $('#selectConta').val();
    const ug = $('#selectUG').val();
    
    if (!ano || !conta || !ug) {
        alert('Por favor, preencha todos os filtros!');
        return;
    }
    
    $('#modalLoading').modal('show');
    $('#mensagemInicial').hide();
    
    // Buscar dados
    $.ajax({
        url: '/detalha-receita/api/dados',
        method: 'GET',
        data: {
            ano: ano,
            conta: conta,
            ug: ug
        },
        success: function(response) {
            console.log('✅ Dados carregados:', response);
            dadosAtuais = response.dados;
            
            // Mostrar aviso se tem mais dados
            if (response.tem_mais) {
                mostrarErro('#divTabela', 
                    `<i class="bi bi-info-circle"></i> Mostrando ${response.total} de ${response.total_real} registros. 
                    Use a exportação para obter todos os dados.`
                );
            }
            
            // Buscar totais
            $.ajax({
                url: '/detalha-receita/api/totais',
                method: 'GET',
                data: {
                    ano: ano,
                    conta: conta,
                    ug: ug
                },
                success: function(totais) {
                    console.log('✅ Totais carregados:', totais);
                    totaisOriginais = totais; // Guardar totais originais
                    atualizarTotais(totais);
                    construirTabela(dadosAtuais);
                    $('#areaResultados').show();
                    $('#modalLoading').modal('hide');
                },
                error: function(xhr) {
                    $('#modalLoading').modal('hide');
                    console.error('❌ Erro ao buscar totais:', xhr);
                    mostrarErro('#divTabela', 'Erro ao buscar totais');
                }
            });
        },
        error: function(xhr) {
            $('#modalLoading').modal('hide');
            let erro = xhr.responseJSON ? xhr.responseJSON.erro : 'Erro desconhecido';
            mostrarErro('#divTabela', 'Erro ao consultar dados: ' + erro);
            $('#areaResultados').show();
        }
    });
}

// Atualizar cards de totais
function atualizarTotais(totais) {
    $('#totalCreditos').text(formatarMoeda(totais.credito.total));
    $('#totalDebitos').text(formatarMoeda(totais.debito.total));
    $('#saldoTotal').text(formatarMoeda(totais.saldo));
    
    $('#qtdCreditos').text(totais.credito.quantidade.toLocaleString('pt-BR') + ' lançamentos');
    $('#qtdDebitos').text(totais.debito.quantidade.toLocaleString('pt-BR') + ' lançamentos');
    
    const totalLancamentos = totais.credito.quantidade + totais.debito.quantidade;
    $('#totalLancamentos').text(totalLancamentos.toLocaleString('pt-BR'));
    
    // Mostrar fórmula do saldo baseado na conta
    const conta = $('#selectConta').val();
    if (conta && conta.startsWith('5')) {
        $('#formulaSaldo').text('(Débitos - Créditos)');
    } else {
        $('#formulaSaldo').text('(Créditos - Débitos)');
    }
    
    // Colorir saldo conforme valor
    if (totais.saldo < 0) {
        $('#saldoTotal').removeClass('text-positive').addClass('text-negative');
    } else {
        $('#saldoTotal').removeClass('text-negative').addClass('text-positive');
    }
}

// Função para recalcular totais baseado nos dados filtrados da tabela
function recalcularTotaisFiltrados() {
    if (!tabelaDados) return;
    
    // Obter dados filtrados visíveis na tabela
    const dadosFiltrados = tabelaDados.rows({ filter: 'applied' }).data();
    
    let totalCredito = 0;
    let totalDebito = 0;
    let qtdCredito = 0;
    let qtdDebito = 0;
    
    // Percorrer dados filtrados
    dadosFiltrados.each(function(row) {
        const valor = parseFloat(row.valancamento) || 0;
        
        if (row.tipo_lancamento === 'CREDITO') {
            totalCredito += valor;
            qtdCredito++;
        } else if (row.tipo_lancamento === 'DEBITO') {
            totalDebito += valor;
            qtdDebito++;
        }
    });
    
    // Calcular saldo baseado no tipo de conta
    const conta = $('#selectConta').val();
    let saldo = 0;
    if (conta && conta.startsWith('5')) {
        saldo = totalDebito - totalCredito;
    } else {
        saldo = totalCredito - totalDebito;
    }
    
    // Criar objeto de totais filtrados
    const totaisFiltrados = {
        credito: { total: totalCredito, quantidade: qtdCredito },
        debito: { total: totalDebito, quantidade: qtdDebito },
        saldo: saldo
    };
    
    // Atualizar cards com novos valores
    atualizarTotais(totaisFiltrados);
}

// Construir tabela com os dados
function construirTabela(dados) {
    if (!dados || dados.length === 0) {
        $('#divTabela').html('<p class="text-center text-muted py-3">Nenhum lançamento encontrado.</p>');
        return;
    }
    
    // Construir HTML da tabela
    let html = '<table id="tabelaDados" class="table table-striped table-hover">';
    html += '<thead><tr>';
    html += '<th>Mês</th>';
    html += '<th>Documento</th>';
    html += '<th>Evento</th>';
    html += '<th>Conta Corrente</th>';
    html += '<th>Valor</th>';
    html += '<th>D/C</th>';
    html += '<th>UG</th>';
    html += '<th>Data</th>';
    html += '<th>Tipo</th>';
    html += '</tr></thead><tbody>';
    
    // Adicionar dados
    dados.forEach(function(row) {
        html += '<tr>';
        
        // Mês
        html += `<td data-order="${row.mes}">${formatarMes(row.mes)}</td>`;
        
        // Documento
        html += `<td>${row.nudocumento || '-'}</td>`;
        
        // Evento
        html += `<td>${row.coevento || '-'}</td>`;
        
        // Conta Corrente
        html += `<td>${row.cocontacorrente || '-'}</td>`;
        
        // Valor
        let valor = formatarNumero(row.valancamento);
        let classeValor = row.tipo_lancamento === 'CREDITO' ? 'text-positive' : 'text-negative';
        html += `<td class="text-end ${classeValor}">${valor}</td>`;
        
        // D/C
        html += `<td class="text-center">${row.indebitocredito || '-'}</td>`;
        
        // UG
        html += `<td>${row.coug || '-'}</td>`;
        
        // Data
        html += `<td>${row.dalancamento || '-'}</td>`;
        
        // Tipo
        let classeTipo = row.tipo_lancamento === 'CREDITO' ? 'badge-credito' : 'badge-debito';
        html += `<td><span class="badge ${classeTipo}">${row.tipo_lancamento || '-'}</span></td>`;
        
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    
    $('#divTabela').html(html);
    
    if (tabelaDados) {
        tabelaDados.destroy();
    }
    
    // Inicializar DataTable
    tabelaDados = $('#tabelaDados').DataTable({
        pageLength: 25,
        lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "Todos"]],
        language: {
            url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/pt-BR.json'
        },
        order: [[0, 'asc'], [7, 'asc']], // Ordenar por mês e data
        columnDefs: [
            {
                targets: 0, // Coluna do mês
                type: 'num'
            },
            {
                targets: 4, // Coluna de valor
                type: 'num-fmt'
            }
        ],
        data: dados, // Passar os dados para o DataTable
        columns: [
            { data: 'mes', render: function(data) { return formatarMes(data); } },
            { data: 'nudocumento', defaultContent: '-' },
            { data: 'coevento', defaultContent: '-' },
            { data: 'cocontacorrente', defaultContent: '-' },
            { 
                data: 'valancamento',
                render: function(data, type, row) {
                    if (type === 'display') {
                        let valor = formatarNumero(data);
                        let classeValor = row.tipo_lancamento === 'CREDITO' ? 'text-positive' : 'text-negative';
                        return `<span class="${classeValor}">${valor}</span>`;
                    }
                    return data;
                },
                className: 'text-end'
            },
            { data: 'indebitocredito', defaultContent: '-', className: 'text-center' },
            { data: 'coug', defaultContent: '-' },
            { data: 'dalancamento', defaultContent: '-' },
            { 
                data: 'tipo_lancamento',
                render: function(data) {
                    let classeTipo = data === 'CREDITO' ? 'badge-credito' : 'badge-debito';
                    return `<span class="badge ${classeTipo}">${data || '-'}</span>`;
                }
            }
        ],
        initComplete: function() {
            var api = this.api();
            
            // Adicionar filtros nas colunas específicas
            api.columns().every(function(index) {
                var column = this;
                var title = $(column.header()).text();
                
                // Adicionar filtros apenas nas colunas: Mês, Documento, Evento e Conta Corrente
                if (index === 0 || index === 1 || index === 2 || index === 3) {
                    var select = $('<select class="form-select form-select-sm mt-1"><option value="">Todos</option></select>')
                        .appendTo($(column.header()))
                        .on('change', function() {
                            var val = $.fn.dataTable.util.escapeRegex($(this).val());
                            column.search(val ? '^' + val + '$' : '', true, false).draw();
                        })
                        .on('click', function(e) {
                            e.stopPropagation();
                        });
                    
                    // Coletar valores únicos
                    var valores = [];
                    column.data().unique().each(function(d) {
                        if (d && d !== '-') {
                            valores.push(d);
                        }
                    });
                    
                    // Ordenar valores
                    if (index === 0) { // Se for a coluna de mês
                        valores.sort(function(a, b) {
                            return parseInt(a) - parseInt(b); // Ordenar numericamente
                        });
                    } else {
                        valores.sort(); // Ordenar alfabeticamente para outras colunas
                    }
                    
                    // Adicionar valores ao select
                    valores.forEach(function(d) {
                        let displayText = d;
                        if (index === 0) { // Se for a coluna de mês
                            displayText = formatarMes(d);
                        }
                        select.append('<option value="' + d + '">' + displayText + '</option>');
                    });
                }
            });
            
            // Adicionar evento para recalcular totais quando a tabela for filtrada
            api.on('search.dt draw.dt', function() {
                recalcularTotaisFiltrados();
            });
        }
    });

    // Forçar fechamento do modal após construir a tabela
    setTimeout(function() {
        $('#modalLoading').modal('hide');
        $('.modal-backdrop').remove();
        $('body').removeClass('modal-open');
        $('body').css('overflow', 'auto');
    }, 500);
}

// Formatar mês
function formatarMes(mes) {
    const meses = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    };
    return meses[mes] || mes;
}

// Formatar número
function formatarNumero(valor) {
    if (valor === null || valor === undefined) return '0,00';
    
    return new Intl.NumberFormat('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(valor);
}

// Formatar moeda
function formatarMoeda(valor) {
    if (valor === null || valor === undefined) return 'R$ 0,00';
    
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(valor);
}

// Exportar para Excel melhorado
function exportarExcel() {
    const ano = $('#selectAno').val();
    const conta = $('#selectConta').val();
    const ug = $('#selectUG').val();
    
    if (!ano || !conta || !ug) {
        alert('Por favor, selecione os filtros antes de exportar!');
        return;
    }
    
    // Verificar se quer exportar apenas dados filtrados
    const exportarFiltrados = confirm('Deseja exportar apenas os dados filtrados na tabela?\n\nOK = Dados filtrados\nCancelar = Todos os dados');
    
    if (exportarFiltrados && tabelaDados) {
        // Exportar apenas dados filtrados
        exportarDadosFiltrados();
    } else {
        // Exportar todos os dados
        exportarTodosDados();
    }
}

// Função para exportar apenas dados filtrados
function exportarDadosFiltrados() {
    if (!tabelaDados) return;
    
    const ano = $('#selectAno').val();
    const conta = $('#selectConta').val();
    const ug = $('#selectUG').val();
    
    // Obter dados filtrados
    const dadosFiltrados = [];
    tabelaDados.rows({ filter: 'applied' }).data().each(function(row) {
        dadosFiltrados.push(row);
    });
    
    console.log(`📊 Exportando ${dadosFiltrados.length} registros filtrados...`);
    
    let csv = [];
    
    // Cabeçalho
    csv.push(['Mês', 'Documento', 'Evento', 'Conta Corrente', 'Valor', 'D/C', 'UG', 'Data', 'Tipo', 'Fonte', 'Classificação'].join(';'));
    
    // Dados
    dadosFiltrados.forEach(function(row) {
        let linha = [
            formatarMes(row.mes),
            row.nudocumento || '',
            row.coevento || '',
            row.cocontacorrente || '',
            (row.valancamento || 0).toString().replace('.', ','),
            row.indebitocredito || '',
            row.coug || '',
            row.dalancamento || '',
            row.tipo_lancamento || '',
            row.cofonte || '',
            row.coclasseorc || ''
        ];
        csv.push(linha.join(';'));
    });
    
    // Calcular totais dos dados filtrados
    let totalCredito = 0;
    let totalDebito = 0;
    let qtdCredito = 0;
    let qtdDebito = 0;
    
    dadosFiltrados.forEach(function(row) {
        const valor = parseFloat(row.valancamento) || 0;
        if (row.tipo_lancamento === 'CREDITO') {
            totalCredito += valor;
            qtdCredito++;
        } else if (row.tipo_lancamento === 'DEBITO') {
            totalDebito += valor;
            qtdDebito++;
        }
    });
    
    const saldo = conta.startsWith('5') ? totalDebito - totalCredito : totalCredito - totalDebito;
    
    // Adicionar resumo
    csv.push(''); // Linha vazia
    csv.push(['RESUMO DOS DADOS FILTRADOS'].join(';'));
    csv.push(['Tipo', 'Quantidade', 'Valor Total'].join(';'));
    csv.push(['Créditos', qtdCredito.toLocaleString('pt-BR'), totalCredito.toFixed(2).replace('.', ',')].join(';'));
    csv.push(['Débitos', qtdDebito.toLocaleString('pt-BR'), totalDebito.toFixed(2).replace('.', ',')].join(';'));
    
    const formulaSaldo = conta.startsWith('5') ? 'Saldo (D-C)' : 'Saldo (C-D)';
    csv.push([formulaSaldo, '', saldo.toFixed(2).replace('.', ',')].join(';'));
    
    csv.push(''); // Linha vazia
    csv.push([`Total de registros exportados: ${dadosFiltrados.length.toLocaleString('pt-BR')}`].join(';'));
    csv.push([`Fonte: DuckDB Local`].join(';'));
    
    // Criar arquivo
    let csvContent = '\ufeff' + csv.join('\n');
    let blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    let link = document.createElement('a');
    let url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `detalha_receita_${ano}_${conta}_${ug}_filtrado.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Função para exportar todos os dados (mantida como estava)
function exportarTodosDados() {
    const ano = $('#selectAno').val();
    const conta = $('#selectConta').val();
    const ug = $('#selectUG').val();
    
    // Mostrar loading
    $('#modalLoading').modal('show');
    
    // Buscar TODOS os dados (sem limite)
    $.ajax({
        url: '/detalha-receita/api/dados',
        method: 'GET',
        data: {
            ano: ano,
            conta: conta,
            ug: ug,
            limite: 999999  // Pegar todos os registros
        },
        success: function(response) {
            console.log(`📊 Exportando ${response.dados.length} registros...`);
            
            let csv = [];
            
            // Cabeçalho
            csv.push(['Mês', 'Documento', 'Evento', 'Conta Corrente', 'Valor', 'D/C', 'UG', 'Data', 'Tipo', 'Fonte', 'Classificação'].join(';'));
            
            // Dados
            response.dados.forEach(function(row) {
                let linha = [
                    formatarMes(row.mes),
                    row.nudocumento || '',
                    row.coevento || '',
                    row.cocontacorrente || '',
                    (row.valancamento || 0).toString().replace('.', ','),
                    row.indebitocredito || '',
                    row.coug || '',
                    row.dalancamento || '',
                    row.tipo_lancamento || '',
                    row.cofonte || '',
                    row.coclasseorc || ''
                ];
                csv.push(linha.join(';'));
            });
            
            // Buscar totais para adicionar no final
            $.ajax({
                url: '/detalha-receita/api/totais',
                method: 'GET',
                data: { ano: ano, conta: conta, ug: ug },
                success: function(totais) {
                    // Adicionar resumo no final
                    csv.push(''); // Linha vazia
                    csv.push(['RESUMO TOTAL'].join(';'));
                    csv.push(['Tipo', 'Quantidade', 'Valor Total'].join(';'));
                    csv.push(['Créditos', totais.credito.quantidade.toLocaleString('pt-BR'), totais.credito.total.toFixed(2).replace('.', ',')].join(';'));
                    csv.push(['Débitos', totais.debito.quantidade.toLocaleString('pt-BR'), totais.debito.total.toFixed(2).replace('.', ',')].join(';'));
                    
                    const formulaSaldo = conta.startsWith('5') ? 'Saldo (D-C)' : 'Saldo (C-D)';
                    csv.push([formulaSaldo, '', totais.saldo.toFixed(2).replace('.', ',')].join(';'));
                    
                    csv.push(''); // Linha vazia
                    csv.push([`Total de registros exportados: ${response.dados.length.toLocaleString('pt-BR')}`].join(';'));
                    csv.push([`Fonte: ${response.fonte || 'DuckDB Local'}`].join(';'));
                    
                    // Criar arquivo
                    let csvContent = '\ufeff' + csv.join('\n');
                    let blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                    let link = document.createElement('a');
                    let url = URL.createObjectURL(blob);
                    
                    link.setAttribute('href', url);
                    link.setAttribute('download', `detalha_receita_${ano}_${conta}_${ug}.csv`);
                    link.style.visibility = 'hidden';
                    
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    
                    $('#modalLoading').modal('hide');
                    
                    // Mensagem de sucesso
                    if (response.tem_mais) {
                        alert(`✅ Exportação concluída!\n\n📊 Total exportado: ${response.dados.length.toLocaleString('pt-BR')} registros`);
                    }
                },
                error: function() {
                    // Se falhar ao buscar totais, exportar sem resumo
                    let csvContent = '\ufeff' + csv.join('\n');
                    let blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                    let link = document.createElement('a');
                    let url = URL.createObjectURL(blob);
                    
                    link.setAttribute('href', url);
                    link.setAttribute('download', `detalha_receita_${ano}_${conta}_${ug}.csv`);
                    link.style.visibility = 'hidden';
                    
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                    
                    $('#modalLoading').modal('hide');
                }
            });
        },
        error: function(xhr) {
            $('#modalLoading').modal('hide');
            alert('❌ Erro ao exportar dados. Tente novamente.');
            console.error('Erro na exportação:', xhr);
        }
    });
}