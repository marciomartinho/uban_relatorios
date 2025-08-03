// JavaScript para Consulta Saldo Receita - Versão com Cards Dinâmicos

let tabelaDados = null;
let dadosOriginais = [];
let dadosFiltrados = [];
let totaisGlobais = {
    totalGeral: 0,
    totalPorMes: {},
    totalPorClassificacao: {}
};

// Mapeamento de nomes de colunas
const nomesColunas = {
    'inmes': 'Mês',
    'cocontacorrente': 'Conta Corrente',
    'intipoadm': 'Tipo Adm',
    'saldo_contabil_receita': 'Saldo Contábil',
    'coclasseorc': 'Classificação Orçamentária',
    'cofonte': 'Fonte',
    'cocategoriareceita': 'Categoria',
    'cofontereceita': 'Origem',
    'cosubfontereceita': 'Espécie',
    'corubrica': 'Especificação',
    'coalinea': 'Alínea',
    'inesfera': 'Esfera',
    'couo': 'UO',
    'cofuncao': 'Função',
    'cosubfuncao': 'Subfunção',
    'coprograma': 'Programa',
    'coprojeto': 'Projeto',
    'cosubtitulo': 'Subtítulo',
    'conatureza': 'Natureza Despesa',
    'incategoria': 'Cat. Econômica',
    'cogrupo': 'Grupo Despesa',
    'comodalidade': 'Modalidade',
    'coelemento': 'Elemento'
};

// Ordem correta dos meses
const ordemMeses = {
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
};

// Mapeamento reverso de meses (nome para número)
const mesesParaNumero = {};
Object.entries(ordemMeses).forEach(([num, nome]) => {
    mesesParaNumero[nome] = parseInt(num);
});

// Inicialização
$(document).ready(function() {
    carregarFiltros();
    configurarEventos();
});

// Carregar opções dos filtros
function carregarFiltros() {
    $.ajax({
        url: '/saldo-receita/api/filtros',
        method: 'GET',
        success: function(data) {
            // Anos
            $('#selectAno').empty().append('<option value="">Selecione o ano...</option>');
            data.anos.forEach(function(ano) {
                $('#selectAno').append(`<option value="${ano}">${ano}</option>`);
            });
            
            // Desabilitar selects dependentes inicialmente
            $('#selectConta').prop('disabled', true);
            $('#selectUG').prop('disabled', true);
        },
        error: function(xhr) {
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
    
    // Evento para resetar filtros da tabela
    $('#btnResetarFiltrosTabela').on('click', function() {
        if (tabelaDados) {
            // Limpar todos os filtros de coluna
            tabelaDados.columns().every(function() {
                var column = this;
                var select = $(column.header()).find('select');
                if (select.length > 0) {
                    select.val('');
                }
            });
            
            // Limpar busca global
            tabelaDados.search('').draw();
            
            // Recalcular totais com todos os dados
            recalcularTotaisComFiltros();
        }
    });
    
    // Evento para mudança de ano - carregar contas disponíveis
    $('#selectAno').on('change', function() {
        const ano = $(this).val();
        
        // Limpar e desabilitar selects dependentes
        $('#selectConta').empty()
            .append('<option value="">Selecione a conta...</option>')
            .prop('disabled', true);
        $('#selectUG').empty()
            .append('<option value="">Selecione a UG...</option>')
            .prop('disabled', true);
            
        if (ano) {
            // Buscar contas disponíveis para o ano selecionado
            $.ajax({
                url: '/saldo-receita/api/contas-por-ano',
                method: 'GET',
                data: { ano: ano },
                success: function(data) {
                    $('#selectConta').prop('disabled', false);
                    data.contas.forEach(function(conta) {
                        $('#selectConta').append(`<option value="${conta}">${conta}</option>`);
                    });
                },
                error: function(xhr) {
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
            .append('<option value="">Selecione a UG...</option>')
            .prop('disabled', true);
            
        if (ano && conta) {
            // Buscar UGs disponíveis para o ano e conta selecionados
            $.ajax({
                url: '/saldo-receita/api/ugs-por-ano-conta',
                method: 'GET',
                data: { 
                    ano: ano,
                    conta: conta 
                },
                success: function(data) {
                    $('#selectUG').prop('disabled', false);
                    
                    // Adicionar opção CONSOLIDADO sempre
                    $('#selectUG').append('<option value="CONSOLIDADO">CONSOLIDADO</option>');
                    
                    // Adicionar UGs disponíveis
                    data.ugs.forEach(function(ug) {
                        $('#selectUG').append(`<option value="${ug}">${ug}</option>`);
                    });
                },
                error: function(xhr) {
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
    
    // Limpar cards de totais
    $('#saldoTotal').text('R$ 0,00');
    $('#totalRegistros').text('0');
    $('#mediaMensal').text('R$ 0,00');
    $('#mesesComDados').text('0');
    
    // Esconder card de classificações
    $('#cardTopClassificacoes').hide();
    
    // Limpar variáveis globais
    dadosOriginais = [];
    dadosFiltrados = [];
    totaisGlobais = {
        totalGeral: 0,
        totalPorMes: {},
        totalPorClassificacao: {}
    };
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
    
    $.ajax({
        url: '/saldo-receita/api/dados',
        method: 'GET',
        data: {
            ano: ano,
            conta: conta,
            ug: ug
        },
        success: function(response) {
            // Ordenar dados por mês e armazenar
            dadosOriginais = response.dados.sort(function(a, b) {
                return a.inmes - b.inmes;
            });
            
            dadosFiltrados = [...dadosOriginais];
            
            // Calcular totais ANTES de construir a tabela
            calcularTotais(dadosOriginais);
            atualizarCards();
            
            // Construir a tabela
            construirTabela(dadosOriginais);
            
            // Mostrar classificações
            mostrarTopClassificacoes();
            
            // Forçar redimensionamento da tabela após mostrar
            $('#areaResultados').show();
            
            // Ajustar colunas após a área estar visível
            if (tabelaDados) {
                setTimeout(function() {
                    tabelaDados.columns.adjust().draw();
                }, 100);
            }
            
            $('#modalLoading').modal('hide');
        },
        error: function(xhr) {
            $('#modalLoading').modal('hide');
            let erro = xhr.responseJSON ? xhr.responseJSON.erro : 'Erro desconhecido';
            mostrarErro('#divTabela', 'Erro ao consultar dados: ' + erro);
            $('#areaResultados').show();
        }
    });
}

// Função para recalcular totais com base nos filtros aplicados
function recalcularTotaisComFiltros() {
    if (!tabelaDados || !dadosOriginais || dadosOriginais.length === 0) return;
    
    // Verificar se a tabela está pronta
    try {
        if (!tabelaDados.data() || !tabelaDados.data().any()) {
            return;
        }
    } catch (e) {
        return;
    }
    
    // Obter dados filtrados do DataTable
    dadosFiltrados = [];
    
    // Usar a API do DataTables para obter os dados filtrados
    var dadosVisiveis = tabelaDados.rows({ search: 'applied', page: 'all' }).data();
    
    // Para cada linha visível, recuperar o objeto original
    for (var i = 0; i < dadosVisiveis.length; i++) {
        var rowData = dadosVisiveis[i];
        
        // Encontrar o dado original correspondente
        // O DataTables mantém os dados originais, então podemos acessá-los diretamente
        var dadoOriginal = dadosOriginais.find(function(d) {
            // Comparar usando múltiplos campos para garantir match correto
            return d.inmes == rowData.inmes && 
                   d.cocontacorrente === rowData.cocontacorrente &&
                   d.saldo_contabil_receita === rowData.saldo_contabil_receita;
        });
        
        if (dadoOriginal) {
            dadosFiltrados.push(dadoOriginal);
        }
    }
    
    // Recalcular totais com dados filtrados
    calcularTotais(dadosFiltrados);
    atualizarCards();
    mostrarTopClassificacoes();
    
    // Atualizar indicador de filtros ativos
    var filtrosAtivos = 0;
    tabelaDados.columns().every(function() {
        var column = this;
        var select = $(column.header()).find('select');
        if (select.length > 0 && select.val() !== '') {
            filtrosAtivos++;
        }
    });
    
    if (tabelaDados.search() !== '') {
        filtrosAtivos++;
    }
    
    if (filtrosAtivos > 0) {
        $('#indicadorFiltros').show().find('.badge').text(filtrosAtivos);
    } else {
        $('#indicadorFiltros').hide();
    }
}

// Calcular totais
function calcularTotais(dados) {
    // Resetar totais
    totaisGlobais = {
        totalGeral: 0,
        totalPorMes: {},
        totalPorClassificacao: {}
    };
    
    dados.forEach(function(row) {
        const saldo = row.saldo_contabil_receita || 0;
        
        // Total geral
        totaisGlobais.totalGeral += saldo;
        
        // Total por mês
        if (!totaisGlobais.totalPorMes[row.inmes]) {
            totaisGlobais.totalPorMes[row.inmes] = 0;
        }
        totaisGlobais.totalPorMes[row.inmes] += saldo;
        
        // Total por classificação orçamentária
        if (row.coclasseorc) {
            if (!totaisGlobais.totalPorClassificacao[row.coclasseorc]) {
                totaisGlobais.totalPorClassificacao[row.coclasseorc] = {
                    total: 0,
                    quantidade: 0
                };
            }
            totaisGlobais.totalPorClassificacao[row.coclasseorc].total += saldo;
            totaisGlobais.totalPorClassificacao[row.coclasseorc].quantidade++;
        }
    });
}

// Atualizar cards de totais
function atualizarCards() {
    // Saldo total
    $('#saldoTotal').text(formatarMoeda(totaisGlobais.totalGeral));
    
    // Colorir saldo conforme valor
    if (totaisGlobais.totalGeral < 0) {
        $('#saldoTotal').removeClass('text-positive').addClass('text-negative');
    } else {
        $('#saldoTotal').removeClass('text-negative').addClass('text-positive');
    }
    
    // Total de registros
    $('#totalRegistros').text(dadosFiltrados.length.toLocaleString('pt-BR'));
    
    // Número de meses com dados
    const mesesComDados = Object.keys(totaisGlobais.totalPorMes).length;
    $('#mesesComDados').text(mesesComDados);
    
    // Média mensal
    const mediaMensal = mesesComDados > 0 ? totaisGlobais.totalGeral / mesesComDados : 0;
    $('#mediaMensal').text(formatarMoeda(mediaMensal));
    
    // Animação nos cards quando atualizados
    $('.card-value-animate').addClass('updating');
    setTimeout(function() {
        $('.card-value-animate').removeClass('updating');
    }, 300);
}

// Mostrar top classificações orçamentárias
function mostrarTopClassificacoes() {
    const classificacoes = Object.entries(totaisGlobais.totalPorClassificacao)
        .map(([classificacao, dados]) => ({
            classificacao: classificacao,
            total: dados.total,
            quantidade: dados.quantidade
        }))
        .sort((a, b) => Math.abs(b.total) - Math.abs(a.total))
        .slice(0, 5);
    
    if (classificacoes.length === 0) {
        $('#cardTopClassificacoes').hide();
        return;
    }
    
    let html = '';
    const valorMaximo = Math.max(...classificacoes.map(c => Math.abs(c.total)));
    
    classificacoes.forEach(function(clas) {
        const percentual = (Math.abs(clas.total) / valorMaximo) * 100;
        const corBarra = clas.total >= 0 ? 'bg-success' : 'bg-danger';
        
        html += `
            <div class="classificacao-item">
                <div style="flex: 1;">
                    <strong>${clas.classificacao}</strong>
                    <small class="text-muted">(${clas.quantidade} registros)</small>
                </div>
                <div style="width: 150px; text-align: right;">
                    ${formatarMoeda(clas.total)}
                </div>
            </div>
            <div class="progress mb-2" style="height: 10px;">
                <div class="progress-bar ${corBarra}" role="progressbar" 
                     style="width: ${percentual}%" 
                     aria-valuenow="${percentual}" 
                     aria-valuemin="0" 
                     aria-valuemax="100">
                </div>
            </div>
        `;
    });
    
    $('#divTopClassificacoes').html(html);
    $('#cardTopClassificacoes').show();
}

// Construir tabela com os dados
function construirTabela(dados) {
    if (!dados || dados.length === 0) {
        $('#divTabela').html('<p class="text-center text-muted py-3">Nenhum registro encontrado.</p>');
        return;
    }
    
    // Verificar tipos de conta
    const tiposConta = [...new Set(dados.map(d => d.tamanho_conta))];
    const temConta17 = tiposConta.includes(17);
    const temConta38 = tiposConta.includes(38);
    const consolidado = dados[0].cocontacorrente === 'CONSOLIDADO';
    
    // Definir colunas
    let colunas = ['inmes', 'cocontacorrente', 'intipoadm', 'saldo_contabil_receita'];
    
    if (!consolidado) {
        if (temConta17) {
            colunas = colunas.concat([
                'coclasseorc', 'cofonte', 'cocategoriareceita',
                'cofontereceita', 'cosubfontereceita', 'corubrica', 'coalinea'
            ]);
        }
        
        if (temConta38) {
            colunas = colunas.concat([
                'inesfera', 'couo', 'cofuncao', 'cosubfuncao',
                'coprograma', 'coprojeto', 'cosubtitulo', 'cofonte',
                'conatureza', 'incategoria', 'cogrupo', 'comodalidade', 'coelemento'
            ]);
        }
    }
    
    // Remover duplicatas
    colunas = [...new Set(colunas)];
    
    // Destruir tabela anterior se existir
    if (tabelaDados) {
        tabelaDados.destroy();
    }
    
    // Construir HTML da tabela
    let html = '<table id="tabelaDados" class="table table-striped table-hover">';
    html += '<thead><tr>';
    
    colunas.forEach(function(col) {
        html += `<th>${nomesColunas[col] || col}</th>`;
    });
    
    html += '</tr></thead><tbody>';
    
    // Adicionar dados
    dados.forEach(function(row) {
        html += consolidado ? '<tr class="consolidado">' : '<tr>';
        
        colunas.forEach(function(col) {
            let valor = row[col];
            
            if (col === 'inmes') {
                valor = ordemMeses[valor] || valor;
                html += `<td data-order="${row[col]}">${valor}</td>`;
            } else if (col === 'saldo_contabil_receita') {
                valor = formatarNumero(valor);
                const classe = row[col] < 0 ? 'text-negative' : 'text-positive';
                html += `<td class="text-end ${classe}">${valor}</td>`;
            } else if (col === 'inesfera') {
                if (valor !== null && valor !== undefined && valor !== '') {
                    html += `<td>${valor}</td>`;
                } else {
                    html += `<td class="text-center text-null">-</td>`;
                }
            } else if (valor === null || valor === undefined || valor === '') {
                html += `<td class="text-center text-null">-</td>`;
            } else {
                html += `<td>${valor}</td>`;
            }
        });
        
        html += '</tr>';
    });
    
    html += '</tbody>';
    
    // Adicionar linha de total
    html += '<tfoot class="table-light"><tr>';
    colunas.forEach(function(col, index) {
        if (index === 0) {
            html += '<th>TOTAL GERAL</th>';
        } else if (col === 'saldo_contabil_receita') {
            const classe = totaisGlobais.totalGeral < 0 ? 'text-negative' : 'text-positive';
            html += `<th class="text-end ${classe}">${formatarNumero(totaisGlobais.totalGeral)}</th>`;
        } else {
            html += '<th></th>';
        }
    });
    html += '</tr></tfoot>';
    
    html += '</table>';
    
    $('#divTabela').html(html);
    
    // Preparar dados para o DataTables no formato correto
    var dadosDataTable = dados.map(function(row) {
        var rowData = {};
        colunas.forEach(function(col) {
            if (col === 'inmes') {
                rowData[col] = row[col]; // Manter número original
            } else {
                rowData[col] = row[col];
            }
        });
        return rowData;
    });
    
    // Inicializar DataTable
    tabelaDados = $('#tabelaDados').DataTable({
        data: dadosDataTable,
        columns: colunas.map(function(col) {
            return { 
                data: col,
                render: function(data, type, row) {
                    if (col === 'inmes') {
                        if (type === 'display') {
                            return ordemMeses[data] || data;
                        }
                        return data; // Para ordenação, usar número
                    } else if (col === 'saldo_contabil_receita') {
                        if (type === 'display') {
                            const classe = data < 0 ? 'text-negative' : 'text-positive';
                            return `<span class="${classe}">${formatarNumero(data)}</span>`;
                        }
                        return data; // Para ordenação, usar valor numérico
                    } else if (data === null || data === undefined || data === '') {
                        if (type === 'display') {
                            return '<span class="text-center text-null">-</span>';
                        }
                        return '';
                    }
                    return data;
                }
            };
        }),
        pageLength: 25,
        lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "Todos"]],
        dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>rtip',
        order: [[0, 'asc']],
        language: {
            search: "Buscar:",
            lengthMenu: "Mostrar _MENU_ registros por página",
            info: "Mostrando _START_ até _END_ de _TOTAL_ registros",
            infoEmpty: "Mostrando 0 até 0 de 0 registros",
            infoFiltered: "(filtrado de _MAX_ registros no total)",
            loadingRecords: "Carregando...",
            zeroRecords: "Nenhum registro encontrado",
            emptyTable: "Nenhum dado disponível na tabela",
            paginate: {
                first: "Primeiro",
                previous: "Anterior",
                next: "Próximo",
                last: "Último"
            }
        },
        footerCallback: function(row, data, start, end, display) {
            var api = this.api();
            
            // Total da página atual
            var pageTotal = api
                .column(3, { page: 'current' })
                .data()
                .reduce(function(a, b) {
                    return a + (b || 0);
                }, 0);
            
            // Atualizar footer
            if (display.length < data.length) {
                $(api.column(0).footer()).html('TOTAL DA PÁGINA');
                $(api.column(3).footer()).html(
                    '<span class="' + (pageTotal < 0 ? 'text-negative' : 'text-positive') + '">' + 
                    formatarNumero(pageTotal) + '</span>'
                );
            } else {
                $(api.column(0).footer()).html('TOTAL GERAL');
                $(api.column(3).footer()).html(
                    '<span class="' + (totaisGlobais.totalGeral < 0 ? 'text-negative' : 'text-positive') + '">' + 
                    formatarNumero(totaisGlobais.totalGeral) + '</span>'
                );
            }
        },
        drawCallback: function(settings) {
            // Recalcular totais sempre que a tabela for redesenhada
            // Mas apenas se a tabela estiver completamente inicializada
            if (this.api().data().any()) {
                recalcularTotaisComFiltros();
            }
        },
        initComplete: function() {
            var api = this.api();
            
            // Adicionar filtros nas colunas
            api.columns().every(function(index) {
                var column = this;
                var title = $(column.header()).text();
                
                // Pular coluna de saldo contábil
                if (title === 'Saldo Contábil') return;
                
                var select = $('<select class="form-select form-select-sm filter-column"><option value="">Todos</option></select>')
                    .appendTo($(column.header()))
                    .on('change', function() {
                        var val = $.fn.dataTable.util.escapeRegex($(this).val());
                        column.search(val ? '^' + val + '$' : '', true, false).draw();
                    })
                    .on('click', function(e) {
                        e.stopPropagation();
                    });
                
                // Adicionar opções únicas ao select
                column.data().unique().sort().each(function(d, j) {
                    if (d !== null && d !== undefined && d !== '') {
                        var displayValue = d;
                        if (index === 0) { // Coluna de mês
                            displayValue = ordemMeses[d] || d;
                        }
                        select.append('<option value="' + displayValue + '">' + displayValue + '</option>');
                    }
                });
            });
            
            // Adicionar listener para busca global
            api.on('search.dt', function() {
                recalcularTotaisComFiltros();
            });
            
            // Garantir que os totais sejam calculados após a inicialização completa
            setTimeout(function() {
                recalcularTotaisComFiltros();
            }, 100);
        }
    });
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

// Mostrar erro
function mostrarErro(elemento, mensagem) {
    $(elemento).html(`
        <div class="alert alert-danger" role="alert">
            <i class="bi bi-exclamation-triangle"></i> ${mensagem}
        </div>
    `);
}

// Exportar para Excel
function exportarExcel() {
    if (!dadosFiltrados || dadosFiltrados.length === 0) {
        alert('Não há dados para exportar!');
        return;
    }
    
    let csv = [];
    
    // Determinar colunas baseado nos dados
    let headers = Object.keys(dadosFiltrados[0]).filter(k => k !== 'tamanho_conta');
    csv.push(headers.map(h => nomesColunas[h] || h).join(';'));
    
    // Dados filtrados
    dadosFiltrados.forEach(function(row) {
        let linha = headers.map(function(h) {
            let valor = row[h];
            if (h === 'inmes') {
                return ordemMeses[valor] || valor;
            } else if (h === 'saldo_contabil_receita' && valor !== null) {
                return valor.toString().replace('.', ',');
            }
            return valor || '';
        });
        csv.push(linha.join(';'));
    });
    
    // Adicionar linha de total
    csv.push('');
    let linhaTotal = ['TOTAL GERAL'];
    for (let i = 1; i < headers.length; i++) {
        if (headers[i] === 'saldo_contabil_receita') {
            linhaTotal.push(totaisGlobais.totalGeral.toFixed(2).replace('.', ','));
        } else {
            linhaTotal.push('');
        }
    }
    csv.push(linhaTotal.join(';'));
    
    // Adicionar resumo por mês
    csv.push('');
    csv.push(['RESUMO POR MÊS'].join(';'));
    csv.push(['Mês', 'Total'].join(';'));
    Object.entries(totaisGlobais.totalPorMes)
        .sort(([a], [b]) => parseInt(a) - parseInt(b))
        .forEach(([mes, total]) => {
            csv.push([ordemMeses[mes], total.toFixed(2).replace('.', ',')].join(';'));
        });
    
    // Adicionar top classificações se houver
    if (Object.keys(totaisGlobais.totalPorClassificacao).length > 0) {
        csv.push('');
        csv.push(['TOP 5 CLASSIFICAÇÕES ORÇAMENTÁRIAS'].join(';'));
        csv.push(['Classificação', 'Quantidade', 'Valor Total'].join(';'));
        
        Object.entries(totaisGlobais.totalPorClassificacao)
            .map(([classificacao, dados]) => ({
                classificacao: classificacao,
                quantidade: dados.quantidade,
                total: dados.total
            }))
            .sort((a, b) => Math.abs(b.total) - Math.abs(a.total))
            .slice(0, 5)
            .forEach(function(clas) {
                csv.push([clas.classificacao, clas.quantidade, clas.total.toFixed(2).replace('.', ',')].join(';'));
            });
    }
    
    // Adicionar indicação de filtros aplicados
    var filtrosAtivos = [];
    if (tabelaDados) {
        tabelaDados.columns().every(function() {
            var column = this;
            var select = $(column.header()).find('select');
            if (select.length > 0 && select.val() !== '') {
                var columnName = $(column.header()).clone().children().remove().end().text();
                filtrosAtivos.push(columnName + ': ' + select.val());
            }
        });
        
        if (tabelaDados.search() !== '') {
            filtrosAtivos.push('Busca: ' + tabelaDados.search());
        }
    }
    
    if (filtrosAtivos.length > 0) {
        csv.push('');
        csv.push(['FILTROS APLICADOS'].join(';'));
        filtrosAtivos.forEach(function(filtro) {
            csv.push([filtro].join(';'));
        });
    }
    
    let csvContent = '\ufeff' + csv.join('\n');
    let blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    let link = document.createElement('a');
    let url = URL.createObjectURL(blob);
    
    let filename = `saldo_receita_${$('#selectAno').val()}_${$('#selectUG').val()}`;
    if (filtrosAtivos.length > 0) {
        filename += '_filtrado';
    }
    filename += '.csv';
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}