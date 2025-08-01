// JavaScript para Consulta Saldo Despesa

let tabelaDados = null;
let dadosAtuais = [];

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
    1: 1,   // Janeiro
    2: 2,   // Fevereiro
    3: 3,   // Março
    4: 4,   // Abril
    5: 5,   // Maio
    6: 6,   // Junho
    7: 7,   // Julho
    8: 8,   // Agosto
    9: 9,   // Setembro
    10: 10, // Outubro
    11: 11, // Novembro
    12: 12  // Dezembro
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
                return ordemMeses[a.inmes] - ordemMeses[b.inmes];
            });
            
            construirTabela(dadosAtuais);
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
                valor = formatarMes(valor);
                html += `<td data-order="${row[col]}">${valor}</td>`;
            } else if (col === 'saldo_contabil_despesa') {
                valor = formatarNumero(valor);
                html += `<td class="text-end">${valor}</td>`;
            } else if (col === 'inesfera') {
                // Mostrar o número da esfera como está no banco
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
    
    html += '</tbody></table>';
    
    $('#divTabela').html(html);
    
    if (tabelaDados) {
        tabelaDados.destroy();
    }
    
    // Inicializar DataTable
    tabelaDados = $('#tabelaDados').DataTable({
        pageLength: 25,
        lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "Todos"]],
        dom: 'Blfrtip',
        buttons: [],
        order: [[0, 'asc']], // Ordenar por mês (primeira coluna)
        columnDefs: [
            {
                targets: 0, // Coluna do mês
                type: 'num' // Tratar como número para ordenação correta
            }
        ],
        initComplete: function() {
            // Adicionar filtros nas colunas
            this.api().columns().every(function() {
                var column = this;
                var title = $(column.header()).text();
                
                if (title === 'Saldo Contábil') return;
                
                var select = $('<select class="form-select form-select-sm"><option value="">Todos</option></select>')
                    .appendTo($(column.header()))
                    .on('change', function() {
                        var val = $.fn.dataTable.util.escapeRegex($(this).val());
                        column.search(val ? '^' + val + '$' : '', true, false).draw();
                    })
                    .on('click', function(e) {
                        e.stopPropagation();
                    });
                
                column.data().unique().sort().each(function(d, j) {
                    if (d && d !== '-') {
                        select.append('<option value="' + d + '">' + d + '</option>');
                    }
                });
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
    if (valor === null || valor === undefined) return '';
    
    return new Intl.NumberFormat('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(valor);
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
            if (col === 'saldo_contabil_despesa' && valor !== null) {
                return valor.toString().replace('.', ',');
            }
            return valor || '';
        });
        csv.push(linha.join(';'));
    });
    
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