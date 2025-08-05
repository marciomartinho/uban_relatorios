// JavaScript para Detalha Conta Contábil Receita - Versão DuckDB com Filtros em Cascata
console.log('Arquivo detalha_receita.js carregado - Versão com filtros em cascata');

let tabelaDados = null;
let dadosAtuais = [];
let totaisGlobais = null;

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
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
};

// Inicialização
$(document).ready(function() {
    console.log('Página carregada, iniciando...');
    console.log('🦆 Usando dados do DuckDB local');
    
    // IMPORTANTE: Garantir que o modal está fechado ao carregar
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
    console.log('Carregando filtros...');
    console.log('🦆 Usando dados do DuckDB local');
    
    $.ajax({
        url: '/detalha-receita/api/filtros',
        method: 'GET',
        success: function(data) {
            console.log('✅ Filtros carregados:', data);
            
            // Anos
            $('#selectAno').empty().append('<option value="">Selecione o ano...</option>');
            if (data.anos && data.anos.length > 0) {
                data.anos.forEach(function(ano) {
                    $('#selectAno').append('<option value="' + ano + '">' + ano + '</option>');
                });
            }
            
            // Adicionar badge indicando fonte local se ainda não existir
            if (data.fonte === 'DuckDB Local' && !$('#badgeLocal').length) {
                $('h2').append(' <span id="badgeLocal" class="badge bg-info ms-2">DuckDB Local</span>');
            }
            
            // Desabilitar selects dependentes inicialmente
            $('#selectConta').prop('disabled', true);
            $('#selectUG').prop('disabled', true);
        },
        error: function(xhr) {
            console.error('❌ Erro ao carregar filtros:', xhr);
            let erro = xhr.responseJSON ? xhr.responseJSON.erro : 'Erro desconhecido';
            mostrarErro('#mensagemInicial', 'Erro ao carregar filtros: ' + erro);
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
    
    // Evento para mudança de ano - carregar contas disponíveis
    $('#selectAno').on('change', function() {
        const ano = $(this).val();
        
        // Limpar e desabilitar selects dependentes
        $('#selectConta').empty()
            .append('<option value="">Selecione a conta...</option>')
            .prop('disabled', true);
        $('#selectUG').empty()
            .append('<option value="">Selecione a UG Contábil...</option>')
            .prop('disabled', true);
            
        if (ano) {
            console.log('🦆 Buscando contas para o ano', ano);
            
            // Buscar contas disponíveis para o ano selecionado
            $.ajax({
                url: '/detalha-receita/api/contas-por-ano',
                method: 'GET',
                data: { ano: ano },
                success: function(data) {
                    console.log('✅ Contas carregadas:', data.contas.length);
                    $('#selectConta').prop('disabled', false);
                    data.contas.forEach(function(conta) {
                        $('#selectConta').append('<option value="' + conta + '">' + conta + '</option>');
                    });
                },
                error: function(xhr) {
                    console.error('❌ Erro ao carregar contas:', xhr);
                    let erro = xhr.responseJSON ? xhr.responseJSON.erro : 'Erro desconhecido';
                    alert('Erro ao carregar contas: ' + erro);
                }
            });
        }
    });
    
    // Evento para mudança de conta - carregar UGs disponíveis
    $('#selectConta').on('change', function() {
        const ano = $('#selectAno').val();
        const conta = $(this).val();
        
        // Limpar e desabilitar select de UG
        $('#selectUG').empty()
            .append('<option value="">Selecione a UG Contábil...</option>')
            .prop('disabled', true);
            
        if (ano && conta) {
            console.log('🦆 Buscando UGs para conta', conta);
            
            // Buscar UGs disponíveis para o ano e conta selecionados
            $.ajax({
                url: '/detalha-receita/api/ugs-por-ano-conta',
                method: 'GET',
                data: { 
                    ano: ano,
                    conta: conta 
                },
                success: function(data) {
                    console.log('✅ UGs carregadas:', data.ugs.length);
                    $('#selectUG').prop('disabled', false);
                    
                    // Adicionar opção CONSOLIDADO sempre
                    $('#selectUG').append('<option value="CONSOLIDADO">CONSOLIDADO</option>');
                    
                    // Adicionar UGs disponíveis
                    data.ugs.forEach(function(ug) {
                        $('#selectUG').append('<option value="' + ug + '">' + ug + '</option>');
                    });
                },
                error: function(xhr) {
                    console.error('❌ Erro ao carregar UGs:', xhr);
                    let erro = xhr.responseJSON ? xhr.responseJSON.erro : 'Erro desconhecido';
                    alert('Erro ao carregar UGs: ' + erro);
                }
            });
        }
    });
}

// Limpar filtros
function limparFiltros() {
    $('#selectAno').val('');
    $('#selectConta').val('').prop('disabled', true)
        .empty().append('<option value="">Primeiro selecione o ano...</option>');
    $('#selectUG').val('').prop('disabled', true)
        .empty().append('<option value="">Primeiro selecione a conta...</option>');
    
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
    $('#infoLimite').text('');
    $('#avisoLimite').hide();
    
    // Limpar variáveis globais
    dadosAtuais = [];
    totaisGlobais = null;
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
    
    console.log('🦆 Consultando dados no DuckDB:', {ano, conta, ug});
    
    // Tentar mostrar o modal de diferentes formas
    try {
        $('#modalLoading').modal('show');
    } catch (e) {
        console.log('Erro ao mostrar modal com Bootstrap, usando método alternativo');
        $('#modalLoading').addClass('show');
        $('#modalLoading').css('display', 'block');
        $('body').append('<div class="modal-backdrop fade show"></div>');
        $('body').addClass('modal-open');
    }
    
    $('#mensagemInicial').hide();
    $('#avisoLimite').hide();
    
    // Buscar totais primeiro
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
            totaisGlobais = totais;
            atualizarTotais(totais);
            
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
                        $('#avisoLimite').show();
                        $('#textoAvisoLimite').html(
                            `<strong>Atenção:</strong> Mostrando ${response.total.toLocaleString('pt-BR')} de ${response.total_registros.toLocaleString('pt-BR')} registros. 
                            Use a exportação para obter todos os dados.`
                        );
                    }
                    
                    construirTabela(dadosAtuais);
                    $('#areaResultados').show();
                    
                    // Fechar modal
                    $('#modalLoading').modal('hide');
                    
                    // Forçar fechamento do modal se ainda estiver visível
                    setTimeout(function() {
                        if ($('#modalLoading').hasClass('show') || $('#modalLoading').is(':visible')) {
                            console.log('Forçando fechamento do modal...');
                            $('#modalLoading').removeClass('show');
                            $('#modalLoading').css('display', 'none');
                            $('.modal-backdrop').remove();
                            $('body').removeClass('modal-open');
                            $('body').css('padding-right', '');
                        }
                    }, 500);
                },
                error: function(xhr) {
                    $('#modalLoading').modal('hide');
                    setTimeout(function() {
                        if ($('#modalLoading').hasClass('show') || $('#modalLoading').is(':visible')) {
                            $('#modalLoading').removeClass('show');
                            $('#modalLoading').css('display', 'none');
                            $('.modal-backdrop').remove();
                            $('body').removeClass('modal-open');
                            $('body').css('padding-right', '');
                        }
                    }, 100);
                    
                    let erro = xhr.responseJSON ? xhr.responseJSON.erro : 'Erro desconhecido';
                    mostrarErro('#divTabela', 'Erro ao consultar dados: ' + erro);
                    $('#areaResultados').show();
                }
            });
        },
        error: function(xhr) {
            $('#modalLoading').modal('hide');
            setTimeout(function() {
                if ($('#modalLoading').hasClass('show') || $('#modalLoading').is(':visible')) {
                    $('#modalLoading').removeClass('show');
                    $('#modalLoading').css('display', 'none');
                    $('.modal-backdrop').remove();
                    $('body').removeClass('modal-open');
                    $('body').css('padding-right', '');
                }
            }, 100);
            
            let erro = xhr.responseJSON ? xhr.responseJSON.erro : 'Erro desconhecido';
            mostrarErro('#divTabela', 'Erro ao consultar totais: ' + erro);
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
        
        // Conta Corrente - SEM TRUNCAMENTO
        html += `<td class="text-nowrap">${row.cocontacorrente || '-'}</td>`;
        
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
        lengthMenu: [[10, 25, 50, 100, 500, -1], [10, 25, 50, 100, 500, "Todos"]],
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
        drawCallback: function(settings) {
            // Adicionar tooltips nas contas correntes muito longas
            $('#tabelaDados td:nth-child(4)').each(function() {
                var $this = $(this);
                if ($this.text().length > 40) {
                    $this.attr('title', $this.text());
                    $this.attr('data-bs-toggle', 'tooltip');
                }
            });
            
            // Inicializar tooltips
            $('[data-bs-toggle="tooltip"]').tooltip();
        },
        initComplete: function() {
            // Adicionar filtros nas colunas específicas
            this.api().columns().every(function(index) {
                var column = this;
                
                // Adicionar filtros apenas nas colunas: Mês, Documento, Evento, Conta Corrente
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
        }
    });
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
    
    console.log('📊 Exportando dados do DuckDB...');
    
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
            
            // Adicionar totais no final (se temos os totais globais)
            if (totaisGlobais) {
                csv.push(''); // Linha vazia
                csv.push(['RESUMO'].join(';'));
                csv.push(['Tipo', 'Quantidade', 'Valor Total'].join(';'));
                csv.push(['Créditos', totaisGlobais.credito.quantidade.toLocaleString('pt-BR'), totaisGlobais.credito.total.toFixed(2).replace('.', ',')].join(';'));
                csv.push(['Débitos', totaisGlobais.debito.quantidade.toLocaleString('pt-BR'), totaisGlobais.debito.total.toFixed(2).replace('.', ',')].join(';'));
                
                const formulaSaldo = conta.startsWith('5') ? 'Saldo (D-C)' : 'Saldo (C-D)';
                csv.push([formulaSaldo, '', totaisGlobais.saldo.toFixed(2).replace('.', ',')].join(';'));
            }
            
            // Adicionar informação sobre total de registros
            csv.push(''); // Linha vazia
            csv.push([`Total de registros exportados: ${response.dados.length.toLocaleString('pt-BR')}`].join(';'));
            csv.push([`Fonte: ${response.fonte || 'DuckDB Local'}`].join(';'));
            csv.push([`Data da exportação: ${new Date().toLocaleString('pt-BR')}`].join(';'));
            
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
            alert(`✅ Exportação concluída!\n\n📊 Total exportado: ${response.dados.length.toLocaleString('pt-BR')} registros`);
        },
        error: function(xhr) {
            $('#modalLoading').modal('hide');
            alert('❌ Erro ao exportar dados. Tente novamente.');
            console.error('Erro na exportação:', xhr);
        }
    });
}