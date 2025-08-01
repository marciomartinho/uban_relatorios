// JavaScript para Consulta Saldo Receita

let tabelaDados = null;
let dadosAtuais = [];

// Mapeamento de nomes de colunas
const nomesColunas = {
    // Colunas básicas
    'inmes': 'Mês',
    'cocontacorrente': 'Conta Corrente',
    'intipoadm': 'Tipo Adm',
    'saldo_contabil_receita': 'Saldo Contábil',
    
    // Colunas de 17 chars
    'coclasseorc': 'Classificação Orçamentária',
    'cofonte': 'Fonte',
    'cocategoriareceita': 'Categoria',
    'cofontereceita': 'Origem',
    'cosubfontereceita': 'Espécie',
    'corubrica': 'Especificação',
    'coalinea': 'Alínea',
    
    // Colunas de 38 chars
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
            // Popular Anos
            data.anos.forEach(function(ano) {
                $('#selectAno').append(`<option value="${ano}">${ano}</option>`);
            });
            
            // Popular Contas
            data.contas.forEach(function(conta) {
                $('#selectConta').append(`<option value="${conta}">${conta}</option>`);
            });
            
            // Popular UGs
            data.ugs.forEach(function(ug) {
                $('#selectUG').append(`<option value="${ug}">${ug}</option>`);
            });
        },
        error: function(xhr) {
            mostrarErro('#mensagemInicial', 'Erro ao carregar filtros: ' + xhr.responseJSON.erro);
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
        url: '/saldo-receita/api/dados',
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
    
    // Determinar tipo de conta (17 ou 38 chars)
    const tiposConta = [...new Set(dados.map(d => d.tamanho_conta))];
    const temConta17 = tiposConta.includes(17);
    const temConta38 = tiposConta.includes(38);
    const consolidado = dados[0].cocontacorrente === 'CONSOLIDADO';
    
    // Construir cabeçalho dinamicamente
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
    
    // Remover duplicatas (cofonte pode aparecer em ambos)
    colunas = [...new Set(colunas)];
    
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
            } else if (col === 'saldo_contabil_receita') {
                valor = formatarNumero(valor);
                html += `<td class="text-end">${valor}</td>`;
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
    
    // Cabeçalho
    let headers = Object.keys(dadosAtuais[0]).filter(k => k !== 'tamanho_conta');
    csv.push(headers.map(h => nomesColunas[h] || h).join(';'));
    
    // Dados
    dadosAtuais.forEach(function(row) {
        let linha = headers.map(function(h) {
            let valor = row[h];
            if (h === 'saldo_contabil_receita' && valor !== null) {
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
    link.setAttribute('download', `saldo_receita_${$('#selectAno').val()}_${$('#selectUG').val()}.csv`);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}