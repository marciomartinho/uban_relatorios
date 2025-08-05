// JavaScript para RREO - Demonstrativo de Despesas

console.log('Arquivo rreo_despesa.js carregado');

// Variáveis globais
let dadosRelatorio = null;

// Inicialização
$(document).ready(function() {
    console.log('Document ready - iniciando RREO Despesa');
    carregarFiltros();
    configurarEventos();
});

// Carregar opções dos filtros
function carregarFiltros() {
    console.log('Carregando filtros...');
    
    $.ajax({
        url: '/rreo-despesa/api/filtros',
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
    
    console.log('💰 Gerando relatório RREO Despesa:', {ano, bimestre});
    
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
        url: '/rreo-despesa/api/gerar-relatorio',
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
    
    // Linha 1: DESPESAS (EXCETO INTRA-ORÇAMENTÁRIAS) (VI)
    tbody.append(criarLinhaTituloPrincipal(
        'DESPESAS (EXCETO INTRA-ORÇAMENTÁRIAS) (VI)',
        dados.despesas_exceto_intra.total
    ));
    
    // DESPESAS CORRENTES
    if (Object.keys(dados.despesas_exceto_intra.despesas_correntes.detalhes).length > 0) {
        tbody.append(criarLinhaGrupo(
            'DESPESAS CORRENTES',
            dados.despesas_exceto_intra.despesas_correntes.total
        ));
        
        // Detalhes das despesas correntes
        construirDetalhesCategorias(
            tbody,
            dados.despesas_exceto_intra.despesas_correntes.detalhes
        );
    }
    
    // DESPESAS DE CAPITAL
    if (Object.keys(dados.despesas_exceto_intra.despesas_capital.detalhes).length > 0) {
        tbody.append(criarLinhaGrupo(
            'DESPESAS DE CAPITAL',
            dados.despesas_exceto_intra.despesas_capital.total
        ));
        
        // Detalhes das despesas de capital
        construirDetalhesCategorias(
            tbody,
            dados.despesas_exceto_intra.despesas_capital.detalhes
        );
    }
    
    // RESERVA DE CONTINGÊNCIA
    if (dados.reserva_contingencia && (dados.reserva_contingencia.dotacao_inicial > 0 ||
        dados.reserva_contingencia.dotacao_autorizada > 0)) {
        tbody.append(criarLinhaGrupo(
            'RESERVA DE CONTINGÊNCIA',
            dados.reserva_contingencia
        ));
    }
    
    // Linha 2: DESPESAS (INTRA-ORÇAMENTÁRIAS) (VII)
    if (dados.despesas_intra.total.dotacao_inicial > 0 ||
        dados.despesas_intra.total.dotacao_autorizada > 0 ||
        dados.despesas_intra.total.empenhado_ate_bimestre > 0) {
        
        tbody.append(criarLinhaTituloPrincipal(
            'DESPESAS (INTRA-ORÇAMENTÁRIAS) (VII)',
            dados.despesas_intra.total
        ));
        
        // DESPESAS CORRENTES - INTRA
        if (Object.keys(dados.despesas_intra.despesas_correntes.detalhes).length > 0) {
            tbody.append(criarLinhaGrupo(
                'DESPESAS CORRENTES',
                dados.despesas_intra.despesas_correntes.total
            ));
            
            construirDetalhesCategorias(
                tbody,
                dados.despesas_intra.despesas_correntes.detalhes
            );
        }
        
        // DESPESAS DE CAPITAL - INTRA
        if (Object.keys(dados.despesas_intra.despesas_capital.detalhes).length > 0) {
            tbody.append(criarLinhaGrupo(
                'DESPESAS DE CAPITAL',
                dados.despesas_intra.despesas_capital.total
            ));
            
            construirDetalhesCategorias(
                tbody,
                dados.despesas_intra.despesas_capital.detalhes
            );
        }
    }
    
    // Linha 3: TOTAL DAS DESPESAS (VIII) = (VI + VII)
    tbody.append(criarLinhaTotal(
        'TOTAL DAS DESPESAS (VIII) = (VI + VII)',
        dados.total_despesas
    ));
    
    // Linha 4: SUPERÁVIT (IX)
    tbody.append(criarLinhaTotal(
        'SUPERÁVIT (IX)',
        dados.superavit
    ));
    
    // Linha 5: TOTAL (X) = (VIII + IX)
    tbody.append(criarLinhaTotalGeral(
        'TOTAL (X) = (VIII + IX)',
        dados.total_final
    ));
}

// Construir detalhes das categorias
function construirDetalhesCategorias(tbody, detalhes) {
    // Ordenar as categorias por código
    const categoriasOrdenadas = Object.keys(detalhes).sort();
    
    categoriasOrdenadas.forEach(function(codigo) {
        const categoria = detalhes[codigo];
        tbody.append(criarLinhaCategoria(categoria.nome, categoria));
    });
}

// Criar linha de título principal
function criarLinhaTituloPrincipal(titulo, valores) {
    return criarLinha(titulo, valores, 'linha-titulo-principal');
}

// Criar linha de grupo
function criarLinhaGrupo(titulo, valores) {
    return criarLinha(titulo, valores, 'linha-grupo');
}

// Criar linha de categoria
function criarLinhaCategoria(titulo, valores) {
    return criarLinha(titulo, valores, 'linha-categoria');
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
    // Calcular saldos
    const saldoEmpenho = valores.dotacao_autorizada - valores.empenhado_ate_bimestre;
    const saldoLiquidacao = valores.dotacao_autorizada - valores.liquidado_ate_bimestre;
    
    const tr = $('<tr>').addClass(classe);
    
    // Coluna de despesas
    tr.append($('<td>').text(titulo));
    
    // Dotação Inicial
    tr.append($('<td>').addClass('valor-numerico').html(formatarValor(valores.dotacao_inicial)));
    
    // Dotação Autorizada
    tr.append($('<td>').addClass('valor-numerico').html(formatarValor(valores.dotacao_autorizada)));
    
    // Empenhado no Bimestre
    tr.append($('<td>').addClass('valor-numerico').html(formatarValor(valores.empenhado_bimestre)));
    
    // Empenhado até o Bimestre
    tr.append($('<td>').addClass('valor-numerico').html(formatarValor(valores.empenhado_ate_bimestre)));
    
    // Saldo após empenho
    tr.append($('<td>').addClass('valor-numerico').html(formatarValor(saldoEmpenho)));
    
    // Liquidado no Bimestre
    tr.append($('<td>').addClass('valor-numerico').html(formatarValor(valores.liquidado_bimestre)));
    
    // Liquidado até o Bimestre
    tr.append($('<td>').addClass('valor-numerico').html(formatarValor(valores.liquidado_ate_bimestre)));
    
    // Saldo após liquidação
    tr.append($('<td>').addClass('valor-numerico').html(formatarValor(saldoLiquidacao)));
    
    // Pago até o Bimestre
    tr.append($('<td>').addClass('valor-numerico').html(formatarValor(valores.pago_ate_bimestre)));
    
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

// Limpar filtros
function limparFiltros() {
    $('#selectAno').val('');
    $('#selectBimestre').val('');
    
    $('#areaRelatorio').hide();
    $('#mensagemInicial').removeClass('alert-danger').addClass('alert-info');
    $('#mensagemInicial').html(
        '<i class="bi bi-info-circle"></i> Selecione os filtros acima para gerar o relatório RREO de Despesas'
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
        'DESPESAS',
        'DOTAÇÃO INICIAL',
        'DOTAÇÃO AUTORIZADA',
        'EMPENHADO NO BIMESTRE',
        'EMPENHADO ATÉ O BIMESTRE',
        'SALDO (APÓS EMPENHO)',
        'LIQUIDADO NO BIMESTRE',
        'LIQUIDADO ATÉ O BIMESTRE',
        'SALDO (APÓS LIQUIDAÇÃO)',
        'PAGO ATÉ O BIMESTRE'
    ]);
    
    // Função para adicionar linha ao CSV
    function adicionarLinhaCSV(titulo, valores, nivel = 0) {
        const saldoEmpenho = valores.dotacao_autorizada - valores.empenhado_ate_bimestre;
        const saldoLiquidacao = valores.dotacao_autorizada - valores.liquidado_ate_bimestre;
        
        // Adicionar indentação baseada no nível
        const tituloIndentado = '  '.repeat(nivel) + titulo;
        
        csv.push([
            tituloIndentado,
            valores.dotacao_inicial.toFixed(2).replace('.', ','),
            valores.dotacao_autorizada.toFixed(2).replace('.', ','),
            valores.empenhado_bimestre.toFixed(2).replace('.', ','),
            valores.empenhado_ate_bimestre.toFixed(2).replace('.', ','),
            saldoEmpenho.toFixed(2).replace('.', ','),
            valores.liquidado_bimestre.toFixed(2).replace('.', ','),
            valores.liquidado_ate_bimestre.toFixed(2).replace('.', ','),
            saldoLiquidacao.toFixed(2).replace('.', ','),
            valores.pago_ate_bimestre.toFixed(2).replace('.', ',')
        ]);
    }
    
    // Adicionar dados
    const dados = dadosRelatorio.dados;
    
    // DESPESAS (EXCETO INTRA-ORÇAMENTÁRIAS)
    adicionarLinhaCSV('DESPESAS (EXCETO INTRA-ORÇAMENTÁRIAS) (VI)', dados.despesas_exceto_intra.total);
    
    // Despesas Correntes
    if (Object.keys(dados.despesas_exceto_intra.despesas_correntes.detalhes).length > 0) {
        adicionarLinhaCSV('DESPESAS CORRENTES', dados.despesas_exceto_intra.despesas_correntes.total, 1);
        
        Object.values(dados.despesas_exceto_intra.despesas_correntes.detalhes).forEach(function(categoria) {
            adicionarLinhaCSV(categoria.nome, categoria, 2);
        });
    }
    
    // Despesas de Capital
    if (Object.keys(dados.despesas_exceto_intra.despesas_capital.detalhes).length > 0) {
        adicionarLinhaCSV('DESPESAS DE CAPITAL', dados.despesas_exceto_intra.despesas_capital.total, 1);
        
        Object.values(dados.despesas_exceto_intra.despesas_capital.detalhes).forEach(function(categoria) {
            adicionarLinhaCSV(categoria.nome, categoria, 2);
        });
    }
    
    // Reserva de Contingência
    if (dados.reserva_contingencia && (dados.reserva_contingencia.dotacao_inicial > 0 ||
        dados.reserva_contingencia.dotacao_autorizada > 0)) {
        adicionarLinhaCSV('RESERVA DE CONTINGÊNCIA', dados.reserva_contingencia, 1);
    }
    
    // Despesas Intra
    if (dados.despesas_intra.total.dotacao_inicial > 0 ||
        dados.despesas_intra.total.dotacao_autorizada > 0 ||
        dados.despesas_intra.total.empenhado_ate_bimestre > 0) {
        
        csv.push(['']); // Linha em branco
        adicionarLinhaCSV('DESPESAS (INTRA-ORÇAMENTÁRIAS) (VII)', dados.despesas_intra.total);
        
        // Despesas Correntes - Intra
        if (Object.keys(dados.despesas_intra.despesas_correntes.detalhes).length > 0) {
            adicionarLinhaCSV('DESPESAS CORRENTES', dados.despesas_intra.despesas_correntes.total, 1);
            
            Object.values(dados.despesas_intra.despesas_correntes.detalhes).forEach(function(categoria) {
                adicionarLinhaCSV(categoria.nome, categoria, 2);
            });
        }
        
        // Despesas de Capital - Intra
        if (Object.keys(dados.despesas_intra.despesas_capital.detalhes).length > 0) {
            adicionarLinhaCSV('DESPESAS DE CAPITAL', dados.despesas_intra.despesas_capital.total, 1);
            
            Object.values(dados.despesas_intra.despesas_capital.detalhes).forEach(function(categoria) {
                adicionarLinhaCSV(categoria.nome, categoria, 2);
            });
        }
    }
    
    // Linha em branco antes dos totais
    csv.push(['']);
    
    // Totais
    adicionarLinhaCSV('TOTAL DAS DESPESAS (VIII) = (VI + VII)', dados.total_despesas);
    adicionarLinhaCSV('SUPERÁVIT (IX)', dados.superavit);
    adicionarLinhaCSV('TOTAL (X) = (VIII + IX)', dados.total_final);
    
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
    
    let filename = `RREO_Despesa_${dadosRelatorio.ano}_Bim${dadosRelatorio.bimestre}.csv`;
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    console.log('✅ Exportação concluída:', filename);
}