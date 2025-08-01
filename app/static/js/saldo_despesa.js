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

// Mapeamento de esferas
const nomesEsfera = {
    '0': 'Não informada',
    '1': 'Federal',
    '2': 'Estadual'
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
        timeout: 30000, // 30 segundos de timeout
        beforeSend: function() {
            // Mostrar loading nos selects
            $('#selectAno').html('<option>Carregando...</option>');
            $('#selectConta').html('<option>Carregando...</option>');
            $('#selectUG').html('<option>Carregando...</option>');
        },
        success: function(data) {
            // Limpar e popular Anos
            $('#selectAno').empty().append('<option value="">Selecione o ano...</option>');
            data.anos.forEach(function(ano) {
                $('#selectAno').append(`<option value="${ano}">${ano}</option>`);
            });
            
            // Limpar e popular Contas
            $('#selectConta').empty().append('<option value="">Selecione a conta...</option>');
            data.contas.forEach(function(conta) {
                $('#selectConta').append(`<option value="${conta}">${conta}</option>`);
            });
            
            // Limpar e popular UGs
            $('#selectUG').empty().append('<option value="">Selecione a UG...</option>');
            $('#selectUG').append('<option value="CONSOLIDADO">CONSOLIDADO</option>');
            
            // UGs podem vir como array de objetos ou strings
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
            
            // Mostrar aviso se não estiver usando cache
            if (data.cache === false) {
                console.warn('⚠️ Cache de filtros não disponível. Execute scripts/create_filter_cache.py para melhorar performance.');
            }
        },
        error: function(xhr, status, error) {
            let mensagem = 'Erro ao carregar filtros';
            if (status === 'timeout') {
                mensagem = 'Timeout ao carregar filtros. Volume de dados muito grande. Execute scripts/create_filter_cache.py';
            }
            mostrarErro('#mensagemInicial', mensagem);
            
            // Habilitar campos com opções mínimas
            $('#selectAno').html('<option value="">Erro ao carregar</option>');
            $('#selectConta').html('<option value="">Erro ao carregar</option>');
            $('#selectUG').html('<option value="">Erro ao carregar</option>');
        }
    });
}

// Configurar eventos
function configurarEventos() {
    // Submit do formulário
    $('#formFiltros').on('submit', function(e) {
        e.preventDefault();
        consultarDados();
    });
    
    // Botão limpar
    $('#btnLimpar').on('click', function() {
        limparFiltros();
    });
    
    // Botão exportar
    $('#btnExportar').on('click', function() {
        exportarExcel();
    });
}

// Limpar filtros
function limparFiltros() {
    $('#selectAno').val('');
    $('#selectConta').val('');
    $('#selectUG').val('');
    
    // Esconder resultados
    $('#areaResultados').hide();
    $('#mensagemInicial').show();
    
    // Destruir tabela se existir
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
    
    // Mostrar loading
    $('#modalLoading').modal('show');
    
    // Esconder mensagem inicial
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
            dadosAtuais = response.dados;
            construirTabela(response.dados);
            $('#areaResultados').show();
            $('#modalLoading').modal('hide');
        },
        error: function(xhr) {
            $('#modalLoading').modal('hide');
            mostrarErro('#divTabela', 'Erro ao consultar dados: ' + xhr.responseJSON.erro);
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
    
    // Verificar se é consolidado
    const consolidado = dados[0].cocontacorrente === 'CONSOLIDADO';
    
    // Colunas sempre visíveis
    let colunas = ['inmes', 'cocontacorrente', 'intipoadm', 'saldo_contabil_despesa'];
    
    // Adicionar colunas específicas se não for consolidado
    if (!consolidado) {
        colunas = colunas.concat([
            'conatureza', 'cofonte', 'inesfera', 'couo',
            'cofuncao', 'cosubfuncao', 'coprograma', 
            'coprojeto', 'cosubtitulo'
        ]);
    }
    
    // Construir HTML da tabela
    let html = '<table id="tabelaDados" class="table table-striped table-hover">';
    html += '<thead><tr>';
    
    colunas.forEach(function(col) {
        html += `<th>${nomesColunas[col] || col}</th>`;
    });
    
    html += '</tr></thead><tbody>';
    
    // Adicionar linhas
    dados.forEach(function(row) {
        html += consolidado ? '<tr class="consolidado">' : '<tr>';
        
        colunas.forEach(function(col) {
            let valor = row[col];
            
            // Formatação especial para cada coluna
            if (col === 'inmes') {
                valor = formatarMes(valor);
            } else if (col === 'saldo_contabil_despesa') {
                valor = formatarNumero(valor);
                html += `<td class="text-end">${valor}</td>`;
                return;
            } else if (col === 'conatureza') {
                html += `<td class="col-natureza">${valor || '-'}</td>`;
                return;
            } else if (col === 'inesfera' && valor !== null) {
                const nomeEsfera = nomesEsfera[valor] || valor;
                html += `<td><span class="badge badge-esfera esfera-${valor}">${nomeEsfera}</span></td>`;
                return;
            } else if (valor === null || valor === undefined || valor === '') {
                valor = '-';
                html += `<td class="text-center text-null">${valor}</td>`;
                return;
            }
            
            html += `<td>${valor}</td>`;
        });
        
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    
    // Inserir tabela
    $('#divTabela').html(html);
    
    // Destruir DataTable anterior se existir
    if (tabelaDados) {
        tabelaDados.destroy();
    }
    
    // Inicializar DataTable com filtros individuais
    tabelaDados = $('#tabelaDados').DataTable({
        pageLength: 25,
        lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "Todos"]],
        dom: 'Blfrtip',
        buttons: [],
        order: [[0, 'asc'], [4, 'asc']], // Ordenar por mês e depois por natureza
        initComplete: function() {
            // Adicionar filtros individuais nas colunas
            this.api().columns().every(function() {
                var column = this;
                var title = $(column.header()).text();
                
                // Não adicionar filtro na coluna de saldo
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

// Exportar para Excel
function exportarExcel() {
    if (!dadosAtuais || dadosAtuais.length === 0) {
        alert('Não há dados para exportar!');
        return;
    }
    
    // Criar CSV
    let csv = [];
    
    // Determinar colunas baseado nos dados
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
    
    // Download
    let csvContent = '\ufeff' + csv.join('\n'); // BOM para UTF-8
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