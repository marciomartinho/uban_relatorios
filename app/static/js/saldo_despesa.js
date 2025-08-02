// JavaScript para Consulta Saldo Despesa - Versão Melhorada

let tabelaDados = null;
let dadosAtuais = [];
let totaisGlobais = {
    totalGeral: 0,
    totalPorMes: {},
    totalPorNatureza: {}
};

// Mapeamento de nomes de colunas
const nomesColunas = {
    'inmes': 'Mês',
    'cocontacorrente': 'Conta Corrente',
    'intipoadm': 'Tipo Adm',
    'saldo_contabil_despesa': 'Saldo Contábil',
    'conatureza': 'Classificação Orçamentária',
    'cofonte': 'Fonte',
    'inesfera': 'Esfera',
    'couo': 'UO',
    'cofuncao': 'Função',
    'cosubfuncao': 'Subfunção',
    'coprograma': 'Programa',
    'coprojeto': 'Projeto',
    'cosubtitulo': 'Subtítulo'
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

// Inicialização
$(document).ready(function() {
    carregarFiltros();
    configurarEventos();
});

// Carregar opções dos filtros
function carregarFiltros() {
    $.ajax({
        url: '/saldo-despesa/api/filtros',
        method: 'GET',
        timeout: 30000,
        beforeSend: function() {
            $('#selectAno').html('<option>Carregando...</option>');
            $('#selectConta').html('<option>Carregando...</option>');
            $('#selectUG').html('<option>Carregando...</option>');
        },
        success: function(data) {
            // Anos
            $('#selectAno').empty().append('<option value="">Selecione o ano...</option>');
            data.anos.forEach(function(ano) {
                $('#selectAno').append(`<option value="${ano}">${ano}</option>`);
            });
            
            // Contas
            $('#selectConta').empty().append('<option value="">Selecione a conta...</option>');
            data.contas.forEach(function(conta) {
                $('#selectConta').append(`<option value="${conta}">${conta}</option>`);
            });
            
            // UGs
            $('#selectUG').empty().append('<option value="">Selecione a UG...</option>');
            $('#selectUG').append('<option value="CONSOLIDADO">CONSOLIDADO</option>');
            
            if (data.ugs && data.ugs.length > 0) {
                if (typeof data.ugs[0] === 'object') {
                    data.ugs.forEach(function(ug) {
                        $('#selectUG').append(`<option value="${ug.valor}">${ug.texto}</option>`);
                    });
                } else {
                    data.ugs.forEach(function(ug) {
                        $('#selectUG').append(`<option value="${ug}">${ug}</option>`);
                    });
                }
            }
            
            if (data.cache === false) {
                console.warn('⚠️ Cache não disponível. Execute scripts/otimizar_despesas.py');
            }
        },
        error: function(xhr, status, error) {
            let mensagem = 'Erro ao carregar filtros';
            if (status === 'timeout') {
                mensagem = 'Timeout! Execute scripts/otimizar_despesas.py';
            }
            mostrarErro('#mensagemInicial', mensagem);
            
            $('#selectAno').html('<option value="">Erro ao carregar</option>');
            $('#selectConta').html('<option value="">Erro ao carregar</option>');
            $('#selectUG').html('<option value="">Erro ao carregar</option>');
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
    
    // Limpar cards de totais
    $('#saldoTotal').text('R$ 0,00');
    $('#totalRegistros').text('0');
    $('#mediasMensal').text('R$ 0,00');
    $('#mesesComDados').text('0');
    
    // Esconder card de naturezas
    $('#cardTopNaturezas').hide();
    
    // Limpar variáveis globais
    dadosAtuais = [];
    totaisGlobais = {
        totalGeral: 0,
        totalPorMes: {},
        totalPorNatureza: {}
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
        url: '/saldo-despesa/api/dados',
        method: 'GET',
        data: {
            ano: ano,
            conta: conta,
            ug: ug
        },
        success: function(response) {
            // Ordenar dados por mês
            dadosAtuais = response.dados.sort(function(a, b) {
                return a.inmes - b.inmes;
            });
            
            calcularTotais(dadosAtuais);
            atualizarCards();
            construirTabela(dadosAtuais);
            mostrarTopNaturezas();
            
            $('#areaResultados').show();
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

// Calcular totais
function calcularTotais(dados) {
    // Resetar totais
    totaisGlobais = {
        totalGeral: 0,
        totalPorMes: {},
        totalPorNatureza: {}
    };
    
    dados.forEach(function(row) {
        const saldo = row.saldo_contabil_despesa || 0;
        
        // Total geral
        totaisGlobais.totalGeral += saldo;
        
        // Total por mês
        if (!totaisGlobais.totalPorMes[row.inmes]) {
            totaisGlobais.totalPorMes[row.inmes] = 0;
        }
        totaisGlobais.totalPorMes[row.inmes] += saldo;
        
        // Total por natureza (apenas se não for consolidado)
        if (row.conatureza) {
            if (!totaisGlobais.totalPorNatureza[row.conatureza]) {
                totaisGlobais.totalPorNatureza[row.conatureza] = {
                    total: 0,
                    quantidade: 0
                };
            }
            totaisGlobais.totalPorNatureza[row.conatureza].total += saldo;
            totaisGlobais.totalPorNatureza[row.conatureza].quantidade++;
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
    $('#totalRegistros').text(dadosAtuais.length.toLocaleString('pt-BR'));
    
    // Número de meses com dados
    const mesesComDados = Object.keys(totaisGlobais.totalPorMes).length;
    $('#mesesComDados').text(mesesComDados);
    
    // Média mensal
    const mediaMensal = mesesComDados > 0 ? totaisGlobais.totalGeral / mesesComDados : 0;
    $('#mediaMensal').text(formatarMoeda(mediaMensal));
}

// Mostrar top naturezas
function mostrarTopNaturezas() {
    const naturezas = Object.entries(totaisGlobais.totalPorNatureza)
        .map(([natureza, dados]) => ({
            natureza: natureza,
            total: dados.total,
            quantidade: dados.quantidade
        }))
        .sort((a, b) => Math.abs(b.total) - Math.abs(a.total))
        .slice(0, 5);
    
    if (naturezas.length === 0) {
        $('#cardTopNaturezas').hide();
        return;
    }
    
    let html = '';
    const valorMaximo = Math.max(...naturezas.map(n => Math.abs(n.total)));
    
    naturezas.forEach(function(nat) {
        const percentual = (Math.abs(nat.total) / valorMaximo) * 100;
        const corBarra = nat.total < 0 ? 'bg-danger' : 'bg-success';
        
        html += `
            <div class="natureza-item">
                <div style="flex: 1;">
                    <strong>${nat.natureza}</strong>
                    <small class="text-muted">(${nat.quantidade} registros)</small>
                </div>
                <div style="width: 150px; text-align: right;">
                    ${formatarMoeda(nat.total)}
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
    
    $('#divTopNaturezas').html(html);
    $('#cardTopNaturezas').show();
}

// Construir tabela com os dados
function construirTabela(dados) {
    if (!dados || dados.length === 0) {
        $('#divTabela').html('<p class="text-center text-muted py-3">Nenhum registro encontrado.</p>');
        return;
    }
    
    const consolidado = dados[0].cocontacorrente === 'CONSOLIDADO';
    
    // Definir colunas
    let colunas = ['inmes', 'cocontacorrente', 'intipoadm', 'saldo_contabil_despesa'];
    
    if (!consolidado) {
        colunas = colunas.concat([
            'conatureza', 'cofonte', 'inesfera', 'couo',
            'cofuncao', 'cosubfuncao', 'coprograma', 
            'coprojeto', 'cosubtitulo'
        ]);
    }
    
    // Construir HTML
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
            } else if (col === 'saldo_contabil_despesa') {
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
        } else if (col === 'saldo_contabil_despesa') {
            const classe = totaisGlobais.totalGeral < 0 ? 'text-negative' : 'text-positive';
            html += `<th class="text-end ${classe}">${formatarNumero(totaisGlobais.totalGeral)}</th>`;
        } else {
            html += '<th></th>';
        }
    });
    html += '</tr></tfoot>';
    
    html += '</table>';
    
    $('#divTabela').html(html);
    
    if (tabelaDados) {
        tabelaDados.destroy();
    }
    
    // Inicializar DataTable
    tabelaDados = $('#tabelaDados').DataTable({
        pageLength: 25,
        lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "Todos"]],
        dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>rtip',
        order: [[0, 'asc']], // Ordenar por mês
        columnDefs: [
            {
                targets: 0, // Coluna do mês
                type: 'num' // Tratar como número para ordenação correta
            }
        ],
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
            // Atualizar o total da página atual
            var api = this.api();
            
            // Total da página atual
            var pageTotal = api
                .column(3, { page: 'current' })
                .data()
                .reduce(function(a, b) {
                    return a + (parseFloat(b.replace(/[^\d,-]/g, '').replace(',', '.')) || 0);
                }, 0);
            
            // Atualizar footer se necessário
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
        initComplete: function() {
            // Adicionar filtros nas colunas
            this.api().columns().every(function(index) {
                var column = this;
                var title = $(column.header()).text();
                
                // Pular colunas que não devem ter filtro
                if (title === 'Saldo Contábil' || index === 0) return;
                
                var select = $('<select class="form-select form-select-sm"><option value="">Todos</option></select>')
                    .appendTo($(column.header()))
                    .on('change', function() {
                        var val = $.fn.dataTable.util.escapeRegex($(this).val());
                        column.search(val ? '^' + val + '$' : '', true, false).draw();
                    })
                    .on('click', function(e) {
                        e.stopPropagation();
                    });
                
                // Para a coluna de mês, ordenar corretamente
                if (index === 0) {
                    // Obter valores únicos e ordenar numericamente
                    var meses = [];
                    column.data().unique().each(function(d, j) {
                        // Extrair o número do mês do data-order
                        var mesNum = parseInt($(column.nodes()[0]).parent().find('td:eq(' + index + ')').attr('data-order'));
                        if (!isNaN(mesNum) && meses.indexOf(mesNum) === -1) {
                            meses.push(mesNum);
                        }
                    });
                    
                    // Ordenar numericamente
                    meses.sort(function(a, b) { return a - b; });
                    
                    // Adicionar ao select
                    meses.forEach(function(mesNum) {
                        var mesNome = ordemMeses[mesNum];
                        select.append('<option value="' + mesNome + '">' + mesNome + '</option>');
                    });
                } else {
                    // Para outras colunas, ordenar alfabeticamente
                    column.data().unique().sort().each(function(d, j) {
                        if (d && d !== '-') {
                            select.append('<option value="' + d + '">' + d + '</option>');
                        }
                    });
                }
            });
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
    if (!dadosAtuais || dadosAtuais.length === 0) {
        alert('Não há dados para exportar!');
        return;
    }
    
    let csv = [];
    
    let colunas = ['inmes', 'cocontacorrente', 'intipoadm', 'saldo_contabil_despesa'];
    if (dadosAtuais[0].cocontacorrente !== 'CONSOLIDADO') {
        colunas = colunas.concat([
            'conatureza', 'cofonte', 'inesfera', 'couo',
            'cofuncao', 'cosubfuncao', 'coprograma', 
            'coprojeto', 'cosubtitulo'
        ]);
    }
    
    // Cabeçalho
    csv.push(colunas.map(c => nomesColunas[c] || c).join(';'));
    
    // Dados
    dadosAtuais.forEach(function(row) {
        let linha = colunas.map(function(col) {
            let valor = row[col];
            if (col === 'inmes') {
                return ordemMeses[valor] || valor;
            } else if (col === 'saldo_contabil_despesa' && valor !== null) {
                return valor.toString().replace('.', ',');
            }
            return valor || '';
        });
        csv.push(linha.join(';'));
    });
    
    // Adicionar linha de total
    csv.push(''); // Linha vazia
    let linhaTotal = ['TOTAL GERAL'];
    for (let i = 1; i < colunas.length; i++) {
        if (colunas[i] === 'saldo_contabil_despesa') {
            linhaTotal.push(totaisGlobais.totalGeral.toFixed(2).replace('.', ','));
        } else {
            linhaTotal.push('');
        }
    }
    csv.push(linhaTotal.join(';'));
    
    // Adicionar resumo por mês
    csv.push(''); // Linha vazia
    csv.push(['RESUMO POR MÊS'].join(';'));
    csv.push(['Mês', 'Total'].join(';'));
    Object.entries(totaisGlobais.totalPorMes)
        .sort(([a], [b]) => parseInt(a) - parseInt(b))
        .forEach(([mes, total]) => {
            csv.push([ordemMeses[mes], total.toFixed(2).replace('.', ',')].join(';'));
        });
    
    // Adicionar top naturezas se houver
    if (Object.keys(totaisGlobais.totalPorNatureza).length > 0) {
        csv.push(''); // Linha vazia
        csv.push(['TOP 5 NATUREZAS DE DESPESA'].join(';'));
        csv.push(['Natureza', 'Quantidade', 'Valor Total'].join(';'));
        
        Object.entries(totaisGlobais.totalPorNatureza)
            .map(([natureza, dados]) => ({
                natureza: natureza,
                quantidade: dados.quantidade,
                total: dados.total
            }))
            .sort((a, b) => Math.abs(b.total) - Math.abs(a.total))
            .slice(0, 5)
            .forEach(function(nat) {
                csv.push([nat.natureza, nat.quantidade, nat.total.toFixed(2).replace('.', ',')].join(';'));
            });
    }
    
    let csvContent = '\ufeff' + csv.join('\n');
    let blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    let link = document.createElement('a');
    let url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', `saldo_despesa_${$('#selectAno').val()}_${$('#selectUG').val()}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}