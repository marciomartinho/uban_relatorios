// JavaScript para RREO - Demonstrativo de Receitas

console.log('Arquivo rreo_receita.js carregado');

// Variáveis globais
let dadosRelatorio = null;

// Inicialização
$(document).ready(function() {
    console.log('Document ready - iniciando RREO Receita');
    carregarFiltros();
    configurarEventos();
});

// Carregar opções dos filtros
function carregarFiltros() {
    console.log('Carregando filtros...');
    
    $.ajax({
        url: '/rreo-receita/api/filtros',
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
            
            // UGs
            $('#selectUG').empty().append('<option value="">Selecione a UG...</option>');
            if (data.ugs && data.ugs.length > 0) {
                data.ugs.forEach(function(ug) {
                    $('#selectUG').append('<option value="' + ug + '">' + ug + '</option>');
                });
            }
            
            // Bimestres
            $('#selectBimestre').empty().append('<option value="">Selecione o bimestre...</option>');
            if (data.bimestres && data.bimestres.length > 0) {
                data.bimestres.forEach(function(bimestre) {
                    $('#selectBimestre').append('<option value="' + bimestre.valor + '">' + bimestre.nome + '</option>');
                });
            }
        },
        error: function(xhr) {
            console.error('❌ Erro ao carregar filtros:', xhr);
            let erro = xhr.responseJSON ? xhr.responseJSON.erro : 'Erro desconhecido';
            mostrarErro('Erro ao carregar filtros: ' + erro);
        }
    });
}

// Configurar eventos
function configurarEventos() {
    $('#formFiltros').on('submit', function(e) {
        e.preventDefault();
        gerarRelatorio();
    });
    
    $('#btnLimpar').on('click', function() {
        limparFiltros();
    });
    
    $('#btnExportar').on('click', function() {
        exportarExcel();
    });
    
    $('#btnImprimir').on('click', function() {
        window.print();
    });
}

// Gerar relatório
function gerarRelatorio() {
    const ano = $('#selectAno').val();
    const ug = $('#selectUG').val();
    const bimestre = $('#selectBimestre').val();
    
    if (!ano || !ug || !bimestre) {
        alert('Por favor, preencha todos os filtros!');
        return;
    }
    
    console.log('🦆 Gerando relatório RREO:', {ano, ug, bimestre});
    
    // Mostrar loading
    $('#modalLoading').modal('show');
    $('#mensagemInicial').hide();
    
    $.ajax({
        url: '/rreo-receita/api/gerar-relatorio',
        method: 'GET',
        data: {
            ano: ano,
            ug: ug,
            bimestre: bimestre
        },
        success: function(response) {
            console.log('✅ Relatório gerado:', response);
            
            // Armazenar dados
            dadosRelatorio = response;
            
            // Atualizar título do período
            $('#tituloPeriodo').text(`ATÉ O ${response.nome_bimestre.toUpperCase()} DE ${response.ano}`);
            
            // Atualizar data de geração
            $('#dataGeracao').text(response.data_geracao);
            
            // Construir tabela
            construirTabela(response.dados);
            
            // Mostrar área do relatório
            $('#areaRelatorio').show();
            
            // Fechar modal
            $('#modalLoading').modal('hide');
        },
        error: function(xhr) {
            $('#modalLoading').modal('hide');
            console.error('❌ Erro ao gerar relatório:', xhr);
            let erro = xhr.responseJSON ? xhr.responseJSON.erro : 'Erro desconhecido';
            mostrarErro('Erro ao gerar relatório: ' + erro);
        }
    });
}

// Construir tabela do relatório
function construirTabela(dados) {
    const tbody = $('#corpoRelatorio');
    tbody.empty();
    
    // Linha 1: RECEITAS (EXCETO INTRA-ORÇAMENTÁRIAS) (I)
    tbody.append(criarLinhaTituloPrincipal(
        'RECEITAS (EXCETO INTRA-ORÇAMENTÁRIAS) (I)',
        dados.receitas_exceto_intra.total
    ));
    
    // RECEITAS CORRENTES
    if (dados.receitas_exceto_intra.receitas_correntes.total.previsao_inicial > 0 ||
        dados.receitas_exceto_intra.receitas_correntes.total.realizado_ate_bimestre > 0) {
        
        tbody.append(criarLinhaCategoria(
            'RECEITAS CORRENTES',
            dados.receitas_exceto_intra.receitas_correntes.total
        ));
        
        // Detalhes das receitas correntes
        construirDetalhesCategoria(
            tbody,
            dados.receitas_exceto_intra.receitas_correntes.detalhes
        );
    }
    
    // RECEITAS DE CAPITAL
    if (dados.receitas_exceto_intra.receitas_capital.total.previsao_inicial > 0 ||
        dados.receitas_exceto_intra.receitas_capital.total.realizado_ate_bimestre > 0) {
        
        tbody.append(criarLinhaCategoria(
            'RECEITAS DE CAPITAL',
            dados.receitas_exceto_intra.receitas_capital.total
        ));
        
        // Detalhes das receitas de capital
        construirDetalhesCategoria(
            tbody,
            dados.receitas_exceto_intra.receitas_capital.detalhes
        );
    }
    
    // Linha 2: RECEITAS (INTRA-ORÇAMENTÁRIAS) (II)
    if (dados.receitas_intra.total.previsao_inicial > 0 ||
        dados.receitas_intra.total.realizado_ate_bimestre > 0) {
        
        tbody.append(criarLinhaTituloPrincipal(
            'RECEITAS (INTRA-ORÇAMENTÁRIAS) (II)',
            dados.receitas_intra.total
        ));
        
        // Detalhes das receitas intra
        construirDetalhesCategoria(
            tbody,
            dados.receitas_intra.detalhes
        );
    }
    
    // Linha 3: TOTAL DAS RECEITAS (III) = (I + II)
    tbody.append(criarLinhaTotal(
        'TOTAL DAS RECEITAS (III) = (I + II)',
        dados.total_receitas
    ));
    
    // Linha 4: DÉFICIT (IV)
    tbody.append(criarLinhaTotal(
        'DÉFICIT (IV)',
        dados.deficit
    ));
    
    // Linha 5: TOTAL (V) = (III + IV)
    tbody.append(criarLinhaTotalGeral(
        'TOTAL (V) = (III + IV)',
        dados.total_final
    ));
}

// Construir detalhes de uma categoria
function construirDetalhesCategoria(tbody, detalhes) {
    Object.values(detalhes).forEach(function(fonte) {
        // Linha da fonte
        tbody.append(criarLinhaFonte(fonte.nome, fonte.total));
        
        // Subfontes
        Object.values(fonte.subfontes).forEach(function(subfonte) {
            tbody.append(criarLinhaSubfonte(subfonte.nome, subfonte));
        });
    });
}

// Criar linha de título principal
function criarLinhaTituloPrincipal(titulo, valores) {
    return criarLinha(titulo, valores, 'linha-titulo-principal');
}

// Criar linha de categoria
function criarLinhaCategoria(titulo, valores) {
    return criarLinha(titulo, valores, 'linha-categoria');
}

// Criar linha de fonte
function criarLinhaFonte(titulo, valores) {
    return criarLinha(titulo, valores, 'linha-fonte');
}

// Criar linha de subfonte
function criarLinhaSubfonte(titulo, valores) {
    return criarLinha(titulo, valores, 'linha-subfonte');
}

// Criar linha de total
function criarLinhaTotal(titulo, valores) {
    return criarLinha(titulo, valores, 'linha-total');
}

// Criar linha de total geral
function criarLinhaTotalGeral(titulo, valores) {
    return criarLinha(titulo, valores, 'linha-total-geral');
}

// Criar linha genérica
function criarLinha(titulo, valores, classe) {
    const saldo = valores.previsao_atualizada - valores.realizado_ate_bimestre;
    
    // Calcular percentuais
    const percBimestre = valores.previsao_atualizada > 0 ? 
        (valores.realizado_bimestre / valores.previsao_atualizada * 100) : 0;
    const percAteBimestre = valores.previsao_atualizada > 0 ? 
        (valores.realizado_ate_bimestre / valores.previsao_atualizada * 100) : 0;
    
    let html = '<tr class="' + classe + '">';
    html += '<td>' + titulo + '</td>';
    
    // Previsão Inicial
    html += '<td class="valor-numerico">' + formatarValor(valores.previsao_inicial) + '</td>';
    html += '<td class="valor-percentual">-</td>';
    
    // Previsão Atualizada
    html += '<td class="valor-numerico">' + formatarValor(valores.previsao_atualizada) + '</td>';
    html += '<td class="valor-percentual">-</td>';
    
    // Realizado no Bimestre
    html += '<td class="valor-numerico">' + formatarValor(valores.realizado_bimestre) + '</td>';
    html += '<td class="valor-percentual">' + formatarPercentual(percBimestre) + '</td>';
    
    // Realizado até o Bimestre
    html += '<td class="valor-numerico">' + formatarValor(valores.realizado_ate_bimestre) + '</td>';
    html += '<td class="valor-percentual">' + formatarPercentual(percAteBimestre) + '</td>';
    
    // Saldo
    html += '<td class="valor-numerico">' + formatarValor(saldo) + '</td>';
    
    html += '</tr>';
    
    return html;
}

// Formatar valor monetário
function formatarValor(valor) {
    if (valor === null || valor === undefined || valor === 0) {
        return '<span class="valor-zero">0,00</span>';
    }
    
    const negativo = valor < 0;
    const valorAbs = Math.abs(valor);
    
    const formatado = valorAbs.toLocaleString('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
    
    if (negativo) {
        return '<span class="valor-negativo">(' + formatado + ')</span>';
    }
    
    return formatado;
}

// Formatar percentual
function formatarPercentual(valor) {
    if (valor === 0) {
        return '-';
    }
    
    return valor.toFixed(2).replace('.', ',');
}

// Limpar filtros
function limparFiltros() {
    $('#selectAno').val('');
    $('#selectUG').val('');
    $('#selectBimestre').val('');
    
    $('#areaRelatorio').hide();
    $('#mensagemInicial').show();
    
    dadosRelatorio = null;
}

// Mostrar erro
function mostrarErro(mensagem) {
    $('#mensagemInicial').removeClass('alert-info').addClass('alert-danger');
    $('#mensagemInicial').html(
        '<i class="bi bi-exclamation-triangle"></i> ' + mensagem
    );
    $('#mensagemInicial').show();
}

// Exportar para Excel
function exportarExcel() {
    if (!dadosRelatorio) {
        alert('Nenhum relatório para exportar!');
        return;
    }
    
    console.log('📊 Exportando relatório para Excel...');
    
    // Criar CSV com a estrutura do relatório
    let csv = [];
    
    // Cabeçalho
    csv.push(['DISTRITO FEDERAL']);
    csv.push(['RELATÓRIO RESUMIDO DA EXECUÇÃO ORÇAMENTÁRIA']);
    csv.push(['BALANÇO ORÇAMENTÁRIO']);
    csv.push(['ORÇAMENTO FISCAL E DA SEGURIDADE SOCIAL']);
    csv.push([`ATÉ O ${dadosRelatorio.nome_bimestre.toUpperCase()} DE ${dadosRelatorio.ano}`]);
    csv.push(['']);
    
    // Cabeçalho da tabela
    csv.push([
        'RECEITAS',
        'PREVISÃO INICIAL',
        '',
        'PREVISÃO ATUALIZADA',
        '',
        'NO BIMESTRE',
        '%',
        'ATÉ O BIMESTRE',
        '%',
        'SALDO'
    ]);
    
    // Função para adicionar linha ao CSV
    function adicionarLinhaCSV(titulo, valores) {
        const saldo = valores.previsao_atualizada - valores.realizado_ate_bimestre;
        const percBimestre = valores.previsao_atualizada > 0 ? 
            (valores.realizado_bimestre / valores.previsao_atualizada * 100) : 0;
        const percAteBimestre = valores.previsao_atualizada > 0 ? 
            (valores.realizado_ate_bimestre / valores.previsao_atualizada * 100) : 0;
        
        csv.push([
            titulo,
            valores.previsao_inicial.toFixed(2).replace('.', ','),
            '',
            valores.previsao_atualizada.toFixed(2).replace('.', ','),
            '',
            valores.realizado_bimestre.toFixed(2).replace('.', ','),
            percBimestre.toFixed(2).replace('.', ','),
            valores.realizado_ate_bimestre.toFixed(2).replace('.', ','),
            percAteBimestre.toFixed(2).replace('.', ','),
            saldo.toFixed(2).replace('.', ',')
        ]);
    }
    
    // Adicionar dados
    const dados = dadosRelatorio.dados;
    
    // RECEITAS (EXCETO INTRA-ORÇAMENTÁRIAS)
    adicionarLinhaCSV('RECEITAS (EXCETO INTRA-ORÇAMENTÁRIAS) (I)', dados.receitas_exceto_intra.total);
    
    // Receitas Correntes
    if (dados.receitas_exceto_intra.receitas_correntes.total.previsao_inicial > 0) {
        adicionarLinhaCSV('  RECEITAS CORRENTES', dados.receitas_exceto_intra.receitas_correntes.total);
        
        Object.values(dados.receitas_exceto_intra.receitas_correntes.detalhes).forEach(function(fonte) {
            adicionarLinhaCSV('    ' + fonte.nome, fonte.total);
            
            Object.values(fonte.subfontes).forEach(function(subfonte) {
                adicionarLinhaCSV('      ' + subfonte.nome, subfonte);
            });
        });
    }
    
    // Receitas de Capital
    if (dados.receitas_exceto_intra.receitas_capital.total.previsao_inicial > 0) {
        adicionarLinhaCSV('  RECEITAS DE CAPITAL', dados.receitas_exceto_intra.receitas_capital.total);
        
        Object.values(dados.receitas_exceto_intra.receitas_capital.detalhes).forEach(function(fonte) {
            adicionarLinhaCSV('    ' + fonte.nome, fonte.total);
            
            Object.values(fonte.subfontes).forEach(function(subfonte) {
                adicionarLinhaCSV('      ' + subfonte.nome, subfonte);
            });
        });
    }
    
    // Receitas Intra
    if (dados.receitas_intra.total.previsao_inicial > 0) {
        adicionarLinhaCSV('RECEITAS (INTRA-ORÇAMENTÁRIAS) (II)', dados.receitas_intra.total);
        
        Object.values(dados.receitas_intra.detalhes).forEach(function(fonte) {
            adicionarLinhaCSV('  ' + fonte.nome, fonte.total);
            
            Object.values(fonte.subfontes).forEach(function(subfonte) {
                adicionarLinhaCSV('    ' + subfonte.nome, subfonte);
            });
        });
    }
    
    // Totais
    adicionarLinhaCSV('TOTAL DAS RECEITAS (III) = (I + II)', dados.total_receitas);
    adicionarLinhaCSV('DÉFICIT (IV)', dados.deficit);
    adicionarLinhaCSV('TOTAL (V) = (III + IV)', dados.total_final);
    
    // Converter para string CSV
    let csvContent = '\ufeff' + csv.map(row => row.join(';')).join('\n');
    
    // Criar e baixar arquivo
    let blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    let link = document.createElement('a');
    let url = URL.createObjectURL(blob);
    
    let filename = `RREO_Receita_${dadosRelatorio.ano}_Bim${dadosRelatorio.bimestre}.csv`;
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    console.log('✅ Exportação concluída:', filename);
}