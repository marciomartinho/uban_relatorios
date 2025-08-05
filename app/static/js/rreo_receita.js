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
    const bimestre = $('#selectBimestre').val();
    
    if (!ano || !bimestre) {
        alert('Por favor, preencha todos os filtros!');
        return;
    }
    
    console.log('🦆 Gerando relatório RREO:', {ano, bimestre});
    
    // Esconder área do relatório anterior se existir
    $('#areaRelatorio').hide();
    $('#mensagemInicial').hide();
    
    // Mostrar mensagem de carregamento simples
    $('#mensagemInicial').removeClass('alert-danger').addClass('alert-info');
    $('#mensagemInicial').html(
        '<i class="bi bi-hourglass-split"></i> Gerando relatório...'
    );
    $('#mensagemInicial').show();
    
    $.ajax({
        url: '/rreo-receita/api/gerar-relatorio',
        method: 'GET',
        data: {
            ano: ano,
            bimestre: bimestre
        },
        success: function(response) {
            console.log('✅ Relatório gerado:', response);
            
            try {
                // Armazenar dados
                dadosRelatorio = response;
                
                // Atualizar título do período
                $('#tituloPeriodo').text(`ATÉ O ${response.nome_bimestre.toUpperCase()} DE ${response.ano}`);
                
                // Atualizar data de geração
                $('#dataGeracao').text(response.data_geracao);
                
                // Construir tabela
                construirTabela(response.dados);
                
                // Esconder mensagem de carregamento
                $('#mensagemInicial').hide();
                
                // Mostrar área do relatório
                $('#areaRelatorio').fadeIn(300);
                
                // Scroll suave para o relatório
                setTimeout(function() {
                    $('html, body').animate({
                        scrollTop: $('#areaRelatorio').offset().top - 100
                    }, 500);
                }, 100);
                
            } catch (error) {
                console.error('Erro ao processar resposta:', error);
                mostrarErro('Erro ao processar dados do relatório');
            }
        },
        error: function(xhr) {
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
        
        // RECEITAS CORRENTES - INTRA-ORÇAMENTÁRIAS
        if (dados.receitas_intra.receitas_correntes.total.previsao_inicial > 0 ||
            dados.receitas_intra.receitas_correntes.total.realizado_ate_bimestre > 0) {
            
            tbody.append(criarLinhaCategoria(
                'RECEITAS CORRENTES - INTRA-ORÇAMENTÁRIAS',
                dados.receitas_intra.receitas_correntes.total
            ));
            
            construirDetalhesCategoria(
                tbody,
                dados.receitas_intra.receitas_correntes.detalhes
            );
        }
        
        // RECEITAS DE CAPITAL - INTRA-ORÇAMENTÁRIAS
        if (dados.receitas_intra.receitas_capital.total.previsao_inicial > 0 ||
            dados.receitas_intra.receitas_capital.total.realizado_ate_bimestre > 0) {
            
            tbody.append(criarLinhaCategoria(
                'RECEITAS DE CAPITAL - INTRA-ORÇAMENTÁRIAS',
                dados.receitas_intra.receitas_capital.total
            ));
            
            construirDetalhesCategoria(
                tbody,
                dados.receitas_intra.receitas_capital.detalhes
            );
        }
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
    
    const tr = $('<tr>').addClass(classe);
    
    // Coluna de receitas
    tr.append($('<td>').text(titulo));
    
    // Previsão Inicial
    tr.append($('<td>').addClass('valor-numerico').html(formatarValor(valores.previsao_inicial)));
    
    // Previsão Atualizada
    tr.append($('<td>').addClass('valor-numerico').html(formatarValor(valores.previsao_atualizada)));
    
    // Realizado no Bimestre - Valor
    tr.append($('<td>').addClass('valor-numerico').html(formatarValor(valores.realizado_bimestre)));
    
    // Realizado no Bimestre - Percentual
    tr.append($('<td>').addClass('valor-percentual').html(formatarPercentual(percBimestre)));
    
    // Realizado até o Bimestre - Valor
    tr.append($('<td>').addClass('valor-numerico').html(formatarValor(valores.realizado_ate_bimestre)));
    
    // Realizado até o Bimestre - Percentual
    tr.append($('<td>').addClass('valor-percentual').html(formatarPercentual(percAteBimestre)));
    
    // Saldo
    tr.append($('<td>').addClass('valor-numerico').html(formatarValor(saldo)));
    
    return tr;
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
    $('#selectBimestre').val('');
    
    $('#areaRelatorio').hide();
    $('#mensagemInicial').removeClass('alert-danger').addClass('alert-info');
    $('#mensagemInicial').html(
        '<i class="bi bi-info-circle"></i> Selecione os filtros acima para gerar o relatório RREO de Receitas'
    );
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
    
    // Scroll para mensagem de erro
    $('html, body').animate({
        scrollTop: $('#mensagemInicial').offset().top - 100
    }, 300);
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
        'PREVISÃO ATUALIZADA',
        'NO BIMESTRE',
        '%',
        'ATÉ O BIMESTRE',
        '%',
        'SALDO'
    ]);
    
    // Função para adicionar linha ao CSV
    function adicionarLinhaCSV(titulo, valores, nivel = 0) {
        const saldo = valores.previsao_atualizada - valores.realizado_ate_bimestre;
        const percBimestre = valores.previsao_atualizada > 0 ? 
            (valores.realizado_bimestre / valores.previsao_atualizada * 100) : 0;
        const percAteBimestre = valores.previsao_atualizada > 0 ? 
            (valores.realizado_ate_bimestre / valores.previsao_atualizada * 100) : 0;
        
        // Adicionar indentação baseada no nível
        const tituloIndentado = '  '.repeat(nivel) + titulo;
        
        csv.push([
            tituloIndentado,
            valores.previsao_inicial.toFixed(2).replace('.', ','),
            valores.previsao_atualizada.toFixed(2).replace('.', ','),
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
    if (dados.receitas_exceto_intra.receitas_correntes.total.previsao_inicial > 0 ||
        dados.receitas_exceto_intra.receitas_correntes.total.realizado_ate_bimestre > 0) {
        
        adicionarLinhaCSV('RECEITAS CORRENTES', dados.receitas_exceto_intra.receitas_correntes.total, 1);
        
        Object.values(dados.receitas_exceto_intra.receitas_correntes.detalhes).forEach(function(fonte) {
            adicionarLinhaCSV(fonte.nome, fonte.total, 2);
            
            Object.values(fonte.subfontes).forEach(function(subfonte) {
                adicionarLinhaCSV(subfonte.nome, subfonte, 3);
            });
        });
    }
    
    // Receitas de Capital
    if (dados.receitas_exceto_intra.receitas_capital.total.previsao_inicial > 0 ||
        dados.receitas_exceto_intra.receitas_capital.total.realizado_ate_bimestre > 0) {
        
        adicionarLinhaCSV('RECEITAS DE CAPITAL', dados.receitas_exceto_intra.receitas_capital.total, 1);
        
        Object.values(dados.receitas_exceto_intra.receitas_capital.detalhes).forEach(function(fonte) {
            adicionarLinhaCSV(fonte.nome, fonte.total, 2);
            
            Object.values(fonte.subfontes).forEach(function(subfonte) {
                adicionarLinhaCSV(subfonte.nome, subfonte, 3);
            });
        });
    }
    
    // Receitas Intra
    if (dados.receitas_intra.total.previsao_inicial > 0 ||
        dados.receitas_intra.total.realizado_ate_bimestre > 0) {
        
        adicionarLinhaCSV('RECEITAS (INTRA-ORÇAMENTÁRIAS) (II)', dados.receitas_intra.total);
        
        // Receitas Correntes - Intra
        if (dados.receitas_intra.receitas_correntes.total.previsao_inicial > 0 ||
            dados.receitas_intra.receitas_correntes.total.realizado_ate_bimestre > 0) {
            
            adicionarLinhaCSV('RECEITAS CORRENTES - INTRA-ORÇAMENTÁRIAS', 
                dados.receitas_intra.receitas_correntes.total, 1);
            
            Object.values(dados.receitas_intra.receitas_correntes.detalhes).forEach(function(fonte) {
                adicionarLinhaCSV(fonte.nome, fonte.total, 2);
                
                Object.values(fonte.subfontes).forEach(function(subfonte) {
                    adicionarLinhaCSV(subfonte.nome, subfonte, 3);
                });
            });
        }
        
        // Receitas de Capital - Intra
        if (dados.receitas_intra.receitas_capital.total.previsao_inicial > 0 ||
            dados.receitas_intra.receitas_capital.total.realizado_ate_bimestre > 0) {
            
            adicionarLinhaCSV('RECEITAS DE CAPITAL - INTRA-ORÇAMENTÁRIAS', 
                dados.receitas_intra.receitas_capital.total, 1);
            
            Object.values(dados.receitas_intra.receitas_capital.detalhes).forEach(function(fonte) {
                adicionarLinhaCSV(fonte.nome, fonte.total, 2);
                
                Object.values(fonte.subfontes).forEach(function(subfonte) {
                    adicionarLinhaCSV(subfonte.nome, subfonte, 3);
                });
            });
        }
    }
    
    // Linha em branco antes dos totais
    csv.push(['']);
    
    // Totais
    adicionarLinhaCSV('TOTAL DAS RECEITAS (III) = (I + II)', dados.total_receitas);
    adicionarLinhaCSV('DÉFICIT (IV)', dados.deficit);
    adicionarLinhaCSV('TOTAL (V) = (III + IV)', dados.total_final);
    
    // Rodapé
    csv.push(['']);
    csv.push(['Fonte: SIGGO - Sistema Integrado de Gestão Governamental']);
    csv.push(['Dados extraídos do DuckDB Local']);
    csv.push([`Gerado em: ${dadosRelatorio.data_geracao}`]);
    
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