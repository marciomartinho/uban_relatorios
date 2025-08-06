// JavaScript para Balanço Orçamentário da Receita com suporte a UGs

console.log('Balanço Receita JS carregado');

// Variáveis globais
let dadosRelatorio = null;
let filtrosCarregados = false;
let dadosOriginais = null;
window.ultimoRelatorioGerado = null;

// Inicialização
$(document).ready(function() {
    console.log('Balanço Receita - Iniciando...');
    carregarFiltros();
    configurarEventos();
});

// Carregar filtros disponíveis
function carregarFiltros() {
    console.log('Carregando filtros...');
    
    $.ajax({
        url: '/balanco-receita/api/filtros',
        method: 'GET',
        success: function(data) {
            console.log('✅ Filtros carregados:', data);
            
            // Anos
            $('#selectAno').empty().append('<option value="">Selecione...</option>');
            if (data.anos && data.anos.length > 0) {
                data.anos.forEach(function(ano) {
                    $('#selectAno').append(`<option value="${ano}">${ano}</option>`);
                });
                
                if (data.ano_atual) {
                    $('#selectAno').val(data.ano_atual);
                }
            }
            
            // Carregar meses e selecionar o último mês com dados
            if (data.ano_atual) {
                carregarMeses(data.ano_atual);
                
                setTimeout(function() {
                    if (data.ultimo_mes) {
                        $('#selectMes').val(data.ultimo_mes);
                    }
                    
                    gerarRelatorioAutomatico();
                }, 100);
            }
            
            // UGs
            $('#selectUG').empty().append('<option value="">📊 Dados Consolidados</option>');
            if (data.ugs && data.ugs.length > 0) {
                data.ugs.forEach(function(ug) {
                    $('#selectUG').append(`<option value="${ug.codigo}">🏛️ ${ug.descricao}</option>`);
                });
            }
            
            filtrosCarregados = true;
        },
        error: function(xhr) {
            console.error('❌ Erro ao carregar filtros:', xhr);
            mostrarErro('Erro ao carregar filtros. Por favor, recarregue a página.');
        }
    });
}

// Gerar relatório automaticamente ao carregar a página
function gerarRelatorioAutomatico() {
    const ano = $('#selectAno').val();
    const mes = $('#selectMes').val();
    
    if (ano && mes) {
        console.log('🚀 Gerando relatório automático...');
        gerarRelatorio();
    }
}

// Configurar eventos
function configurarEventos() {
    // Mudança de ano - carregar meses disponíveis
    $('#selectAno').on('change', function() {
        const ano = $(this).val();
        carregarMeses(ano);
    });
    
    // Submit do formulário
    $('#formFiltros').on('submit', function(e) {
        e.preventDefault();
        gerarRelatorio();
    });
    
    // Botão limpar
    $('#btnLimpar').on('click', limparFiltros);
    
    // Botões de ação do relatório
    $(document).on('click', '#btnExportar', exportarExcel);
    $(document).on('click', '#btnDownloadImagem', downloadImagem);
    $(document).on('click', '#btnImprimir', function() {
        window.print();
    });
    $(document).on('click', '#btnExportarCompleto', exportarRelatorioCompleto);
    
    // Mudança no filtro de tipo de receita
    $(document).on('change', '#selectTipoReceita', function() {
        if (dadosRelatorio) {
            aplicarFiltroReceita($(this).val());
            
            if (window.ultimoRelatorioGerado) {
                if (typeof analiseVisual !== 'undefined') {
                    analiseVisual.atualizarGraficos(window.ultimoRelatorioGerado);
                }
                
                if (typeof comparativoMensal !== 'undefined') {
                    comparativoMensal.atualizar(window.ultimoRelatorioGerado);
                }
            }
        }
    });
    
    // Toggle de expansão/colapso - ATUALIZADO PARA SUPORTAR UGs
    $(document).on('click', '.toggle-btn', function() {
        const $btn = $(this);
        const nivel = parseInt($btn.data('nivel'));
        const id = $btn.data('id');
        const isExpanded = $btn.hasClass('expanded');
        
        if (nivel === 1) {
            // Expandir/colapsar subfontes de uma fonte
            const partes = id.split('-');
            const catId = partes[1];
            const fonteId = partes[2];
            
            if (isExpanded) {
                // Colapsar
                $btn.removeClass('expanded').text('+');
                $(`.filho-de-fonte-${catId}-${fonteId}`).hide();
                // Também colapsar as alíneas e UGs
                $(`.filho-de-fonte-${catId}-${fonteId}`).each(function() {
                    const $subfonte = $(this);
                    const subfonteId = $subfonte.data('id');
                    if (subfonteId) {
                        const subPartes = subfonteId.split('-');
                        if (subPartes.length >= 4) {
                            const subId = subPartes[3];
                            $(`.filho-de-subfonte-${catId}-${fonteId}-${subId}`).hide();
                            // Também ocultar UGs das alíneas
                            $(`.filho-de-subfonte-${catId}-${fonteId}-${subId}`).each(function() {
                                const $alinea = $(this);
                                const alineaId = $alinea.data('id');
                                if (alineaId) {
                                    const alineaPartes = alineaId.split('-');
                                    if (alineaPartes.length >= 5) {
                                        const aliId = alineaPartes[4];
                                        $(`.filho-de-alinea-${catId}-${fonteId}-${subId}-${aliId}`).hide();
                                    }
                                }
                            });
                            $subfonte.find('.toggle-btn').removeClass('expanded').text('+');
                        }
                    }
                });
            } else {
                // Expandir
                $btn.addClass('expanded').text('−');
                $(`.filho-de-fonte-${catId}-${fonteId}`).show();
            }
        } else if (nivel === 2) {
            // Expandir/colapsar alíneas de uma subfonte
            const partes = id.split('-');
            const catId = partes[1];
            const fonteId = partes[2];
            const subfonteId = partes[3];
            
            if (isExpanded) {
                // Colapsar
                $btn.removeClass('expanded').text('+');
                $(`.filho-de-subfonte-${catId}-${fonteId}-${subfonteId}`).hide();
                // Também colapsar UGs das alíneas
                $(`.filho-de-subfonte-${catId}-${fonteId}-${subfonteId}`).each(function() {
                    const $alinea = $(this);
                    const alineaId = $alinea.data('id');
                    if (alineaId) {
                        const alineaPartes = alineaId.split('-');
                        if (alineaPartes.length >= 5) {
                            const aliId = alineaPartes[4];
                            $(`.filho-de-alinea-${catId}-${fonteId}-${subfonteId}-${aliId}`).hide();
                            $alinea.find('.toggle-btn').removeClass('expanded').text('+');
                        }
                    }
                });
            } else {
                // Expandir
                $btn.addClass('expanded').text('−');
                $(`.filho-de-subfonte-${catId}-${fonteId}-${subfonteId}`).show();
            }
        } else if (nivel === 3) {
            // NOVO: Expandir/colapsar UGs de uma alínea
            const partes = id.split('-');
            const catId = partes[1];
            const fonteId = partes[2];
            const subfonteId = partes[3];
            const alineaId = partes[4];
            
            if (isExpanded) {
                // Colapsar
                $btn.removeClass('expanded').text('+');
                $(`.filho-de-alinea-${catId}-${fonteId}-${subfonteId}-${alineaId}`).hide();
            } else {
                // Expandir
                $btn.addClass('expanded').text('−');
                $(`.filho-de-alinea-${catId}-${fonteId}-${subfonteId}-${alineaId}`).show();
            }
        }
    });
}

// Carregar meses disponíveis para o ano selecionado
function carregarMeses(ano) {
    if (!ano) {
        $('#selectMes').empty().append('<option value="">Selecione o ano primeiro</option>');
        return;
    }
    
    $('#selectMes').empty().append('<option value="">Selecione...</option>');
    for (let i = 1; i <= 12; i++) {
        const nomeMes = obterNomeMes(i);
        $('#selectMes').append(`<option value="${i}">${i} - ${nomeMes}</option>`);
    }
}

// Obter nome do mês
function obterNomeMes(mes) {
    const meses = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
    };
    return meses[mes] || mes;
}

// Gerar relatório
function gerarRelatorio() {
    const ano = $('#selectAno').val();
    const mes = $('#selectMes').val();
    const coug = $('#selectUG').val();
    const tipoReceita = $('#selectTipoReceita').val();
    
    if (!ano || !mes) {
        mostrarAlerta('Por favor, selecione ano e mês!', 'warning');
        return;
    }
    
    console.log('🦆 Gerando relatório:', {ano, mes, coug, tipoReceita});
    
    $('#mensagemInicial').hide();
    $('#relatorioContainer').html(`
        <div class="loading-container">
            <i class="bi bi-hourglass-split"></i>
            <h4 class="mt-3">Gerando relatório...</h4>
            <p class="text-muted">Consultando dados no DuckDB</p>
        </div>
    `).show();
    
    $.ajax({
        url: '/balanco-receita/api/gerar-relatorio',
        method: 'GET',
        data: {
            ano: ano,
            mes: mes,
            coug: coug,
            tipo_receita: tipoReceita
        },
        success: function(response) {
            console.log('✅ Relatório gerado:', response);
            
            dadosRelatorio = response;
            dadosOriginais = JSON.parse(JSON.stringify(response));
            window.ultimoRelatorioGerado = response;
            
            renderizarRelatorio(response);
            
            if (tipoReceita !== 'todas') {
                aplicarFiltroReceita(tipoReceita);
            }
            
            setTimeout(() => {
                integrarModulosAdicionais(response);
            }, 100);
        },
        error: function(xhr) {
            console.error('❌ Erro ao gerar relatório:', xhr);
            
            let mensagemErro = 'Erro ao gerar relatório';
            if (xhr.responseJSON && xhr.responseJSON.erro) {
                mensagemErro += ': ' + xhr.responseJSON.erro;
            }
            
            $('#relatorioContainer').html(`
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i> ${mensagemErro}
                </div>
            `);
        }
    });
}

// Renderizar relatório completo - ATUALIZADO PARA UGs
function renderizarRelatorio(dados) {
    let html = `
        <div class="card">
            <div class="card-header bg-light">
                <div class="row align-items-center">
                    <div class="col-md-8">
                        <h5 class="mb-0">
                            <i class="bi bi-file-earmark-bar-graph"></i> 
                            Balanço Orçamentário - ${dados.periodo.nome_mes}/${dados.periodo.ano}
                        </h5>
                        <small class="text-muted">UG: ${dados.filtros.nome_coug}</small>
                    </div>
                    <div class="col-md-4 text-end">
                        <button id="btnExportar" class="btn btn-success btn-sm">
                            <i class="bi bi-file-earmark-excel"></i> Excel
                        </button>
                        <button id="btnExportarCompleto" class="btn btn-primary btn-sm">
                            <i class="bi bi-file-earmark-spreadsheet"></i> Completo
                        </button>
                        <button id="btnDownloadImagem" class="btn btn-warning btn-sm">
                            <i class="bi bi-image"></i> Imagem HD
                        </button>
                        <button id="btnImprimir" class="btn btn-secondary btn-sm">
                            <i class="bi bi-printer"></i> Imprimir
                        </button>
                    </div>
                </div>
            </div>
            <div class="card-body">
    `;
    
    if (!dados.dados || dados.dados.length === 0) {
        html += `
            <div class="alert alert-warning">
                <i class="bi bi-exclamation-triangle"></i> 
                Nenhum dado encontrado para os filtros selecionados.
            </div>
        `;
    } else {
        html += `
            <div class="table-responsive">
                <table class="table table-bordered table-hover" id="tabelaBalanco">
                    <thead class="table-primary">
                        <tr>
                            <th class="text-center align-middle" style="min-width: 400px;">RECEITAS</th>
                            <th class="text-center">PREVISÃO INICIAL<br>${dados.periodo.ano}</th>
                            <th class="text-center">PREVISÃO ATUALIZADA<br>${dados.periodo.ano}</th>
                            <th class="text-center">REALIZADA<br>${dados.periodo.mes}/${dados.periodo.ano}</th>
                            <th class="text-center">REALIZADA<br>${dados.periodo.mes}/${dados.periodo.ano_anterior}</th>
                            <th class="text-center">VARIAÇÃO<br>ABSOLUTA</th>
                            <th class="text-center">VARIAÇÃO<br>%</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        // Adicionar linhas de dados
        dados.dados.forEach(function(item) {
            const classeNivel = `nivel-${item.nivel}`;
            let classeLinha = '';
            let paddingLeft = item.nivel * 30;
            
            // Estilos especiais por nível
            if (item.nivel === 0) {
                classeLinha = 'table-light fw-bold';
            } else if (item.nivel === 4) {
                // UGs com estilo diferenciado
                classeLinha = 'table-info';
                paddingLeft += 10; // Padding extra para UGs
            }
            
            // Definir visibilidade inicial
            let estiloLinha = '';
            if (item.nivel === 1) {
                // Fontes visíveis
                estiloLinha = '';
            } else if (item.nivel === 2) {
                // Subfontes ocultas
                estiloLinha = 'style="display: none;"';
            } else if (item.nivel === 3) {
                // Alíneas ocultas
                estiloLinha = 'style="display: none;"';
            } else if (item.nivel === 4) {
                // UGs ocultas
                estiloLinha = 'style="display: none;"';
            }
            
            // Montar classes de identificação hierárquica
            let classesHierarquia = `${classeNivel}`;
            if (item.nivel === 1) {
                classesHierarquia += ` filho-de-cat-${item.categoria_pai}`;
            } else if (item.nivel === 2) {
                classesHierarquia += ` filho-de-fonte-${item.categoria_pai}-${item.fonte_pai}`;
            } else if (item.nivel === 3) {
                classesHierarquia += ` filho-de-subfonte-${item.categoria_pai}-${item.fonte_pai}-${item.subfonte_pai}`;
            } else if (item.nivel === 4) {
                // NOVO: Classes para UGs
                classesHierarquia += ` filho-de-alinea-${item.categoria_pai}-${item.fonte_pai}-${item.subfonte_pai}-${item.alinea_pai}`;
            }
            
            html += `
                <tr class="${classeLinha} ${classesHierarquia}" 
                    data-id="${item.id}" 
                    data-nivel="${item.nivel}"
                    ${estiloLinha}>
                    <td style="padding-left: ${paddingLeft}px;">
            `;
            
            // Adicionar botão de expansão (níveis 1, 2 e 3 agora)
            if ((item.nivel === 1 || item.nivel === 2 || item.nivel === 3) && item.tem_filhos) {
                const btnTexto = item.expandido ? '−' : '+';
                const btnClasse = item.expandido ? 'expanded' : '';
                html += `<button class="btn btn-sm btn-link toggle-btn ${btnClasse}" data-nivel="${item.nivel}" data-id="${item.id}">+</button> `;
            } else if (item.nivel > 0) {
                html += `<span style="display: inline-block; width: 30px;"></span>`;
            }
            
            // Ícone especial para UGs
            if (item.nivel === 4) {
                html += `<i class="bi bi-building text-primary me-2"></i>`;
            }
            
            html += `
                        <span>${item.descricao}</span>
                    </td>
                    <td class="text-end">${formatarValor(item.previsao_inicial)}</td>
                    <td class="text-end">${formatarValor(item.previsao_atualizada)}</td>
                    <td class="text-end">${formatarValor(item.receita_atual)}</td>
                    <td class="text-end">${formatarValor(item.receita_anterior)}</td>
                    <td class="text-end ${item.variacao_absoluta >= 0 ? 'text-success' : 'text-danger'}">
                        ${formatarValor(item.variacao_absoluta)}
                    </td>
                    <td class="text-center ${item.variacao_percentual >= 0 ? 'text-success' : 'text-danger'}">
                        ${formatarPercentual(item.variacao_percentual)}
                    </td>
                </tr>
            `;
        });
        
        // Adicionar linha de total
        html += `
                        <tr class="table-dark fw-bold">
                            <td>TOTAL GERAL</td>
                            <td class="text-end">${formatarValor(dados.totais.previsao_inicial)}</td>
                            <td class="text-end">${formatarValor(dados.totais.previsao_atualizada)}</td>
                            <td class="text-end">${formatarValor(dados.totais.receita_atual)}</td>
                            <td class="text-end">${formatarValor(dados.totais.receita_anterior)}</td>
                            <td class="text-end ${dados.totais.variacao_absoluta >= 0 ? 'text-success' : 'text-danger'}">
                                ${formatarValor(dados.totais.variacao_absoluta)}
                            </td>
                            <td class="text-center ${dados.totais.variacao_percentual >= 0 ? 'text-success' : 'text-danger'}">
                                ${formatarPercentual(dados.totais.variacao_percentual)}
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
    }
    
    html += `
            </div>
            <div class="card-footer text-muted text-center">
                <small>Gerado em: ${dados.data_geracao}</small>
            </div>
        </div>
    `;
    
    $('#relatorioContainer').html(html);
}

// Integração com módulos adicionais
function integrarModulosAdicionais(dadosRelatorio) {
    if (typeof analiseVisual !== 'undefined') {
        console.log('🎨 Integrando módulo de Análise Visual');
        analiseVisual.inicializar(dadosRelatorio);
    }
    
    if (typeof comparativoMensal !== 'undefined') {
        console.log('📊 Integrando módulo de Comparativo Mensal');
        comparativoMensal.inicializar(dadosRelatorio);
    }
}

// Formatar valor monetário
function formatarValor(valor) {
    if (valor === null || valor === undefined || valor === 0) {
        return '0,00';
    }
    
    return new Intl.NumberFormat('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(valor);
}

// Formatar percentual
function formatarPercentual(valor) {
    if (valor === null || valor === undefined || valor === 0) {
        return '0,00%';
    }
    
    return new Intl.NumberFormat('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(valor) + '%';
}

// Aplicar filtro de receita - ATUALIZADO PARA CONSIDERAR UGs
function aplicarFiltroReceita(tipoFiltro) {
    const filtroAtivo = tipoFiltro || $('#selectTipoReceita').val();
    console.log('Aplicando filtro:', filtroAtivo);
    
    // Resetar todas as linhas
    $('tr[data-nivel]').hide();
    
    if (filtroAtivo === 'todas') {
        // Mostrar todas as categorias e fontes
        $('tr[data-nivel="0"]').show();
        $('tr[data-nivel="1"]').show();
        
        // Restaurar valores originais
        if (dadosOriginais) {
            dadosOriginais.dados.forEach(function(item) {
                if (item.nivel === 0) {
                    const $row = $(`tr[data-id="${item.id}"]`);
                    if ($row.length) {
                        $row.find('td:eq(1)').text(formatarValor(item.previsao_inicial));
                        $row.find('td:eq(2)').text(formatarValor(item.previsao_atualizada));
                        $row.find('td:eq(3)').text(formatarValor(item.receita_atual));
                        $row.find('td:eq(4)').text(formatarValor(item.receita_anterior));
                        
                        const $varAbsoluta = $row.find('td:eq(5)');
                        $varAbsoluta.text(formatarValor(item.variacao_absoluta));
                        $varAbsoluta.removeClass('text-success text-danger');
                        if (item.variacao_absoluta >= 0) {
                            $varAbsoluta.addClass('text-success');
                        } else {
                            $varAbsoluta.addClass('text-danger');
                        }
                        
                        const $varPercentual = $row.find('td:eq(6)');
                        $varPercentual.text(formatarPercentual(item.variacao_percentual));
                        $varPercentual.removeClass('text-success text-danger');
                        if (item.variacao_percentual >= 0) {
                            $varPercentual.addClass('text-success');
                        } else {
                            $varPercentual.addClass('text-danger');
                        }
                    }
                }
            });
        }
        
        // Respeitar estado de expansão para subfontes, alíneas e UGs
        $('tr[data-nivel="2"], tr[data-nivel="3"], tr[data-nivel="4"]').each(function() {
            const $row = $(this);
            const nivel = parseInt($row.data('nivel'));
            
            if (nivel === 2) {
                // Verificar se fonte pai está expandida
                const $tr = $row.closest('tr');
                const classes = $tr.attr('class') || '';
                const match = classes.match(/filho-de-fonte-(\d+)-(\d+)/);
                
                if (match) {
                    const catId = match[1];
                    const fonteId = match[2];
                    const fonteBtn = $(`.toggle-btn[data-id="fonte-${catId}-${fonteId}"]`);
                    if (fonteBtn.hasClass('expanded')) {
                        $row.show();
                    }
                }
            } else if (nivel === 3) {
                // Verificar se subfonte pai está expandida
                const $tr = $row.closest('tr');
                const classes = $tr.attr('class') || '';
                const match = classes.match(/filho-de-subfonte-(\d+)-(\d+)-(\d+)/);
                
                if (match) {
                    const catId = match[1];
                    const fonteId = match[2];
                    const subfonteId = match[3];
                    const subfonteBtn = $(`.toggle-btn[data-id="subfonte-${catId}-${fonteId}-${subfonteId}"]`);
                    if (subfonteBtn.hasClass('expanded')) {
                        const fonteBtn = $(`.toggle-btn[data-id="fonte-${catId}-${fonteId}"]`);
                        if (fonteBtn.hasClass('expanded')) {
                            $row.show();
                        }
                    }
                }
            } else if (nivel === 4) {
                // NOVO: Verificar se alínea pai está expandida
                const $tr = $row.closest('tr');
                const classes = $tr.attr('class') || '';
                const match = classes.match(/filho-de-alinea-(\d+)-(\d+)-(\d+)-(\d+)/);
                
                if (match) {
                    const catId = match[1];
                    const fonteId = match[2];
                    const subfonteId = match[3];
                    const alineaId = match[4];
                    const alineaBtn = $(`.toggle-btn[data-id="alinea-${catId}-${fonteId}-${subfonteId}-${alineaId}"]`);
                    if (alineaBtn.hasClass('expanded')) {
                        const subfonteBtn = $(`.toggle-btn[data-id="subfonte-${catId}-${fonteId}-${subfonteId}"]`);
                        const fonteBtn = $(`.toggle-btn[data-id="fonte-${catId}-${fonteId}"]`);
                        if (fonteBtn.hasClass('expanded') && subfonteBtn.hasClass('expanded')) {
                            $row.show();
                        }
                    }
                }
            }
        });
    } else {
        // Aplicar filtro específico
        let fontesParaMostrar = [];
        let categoriasComDados = new Set();
        let totaisPorCategoria = {};
        
        // Determinar fontes baseado no filtro
        switch(filtroAtivo) {
            case '11': fontesParaMostrar = ['11', '71']; break;
            case '12': fontesParaMostrar = ['12', '72']; break;
            case '13': fontesParaMostrar = ['13', '73']; break;
            case '14': fontesParaMostrar = ['14', '74']; break;
            case '15': fontesParaMostrar = ['15', '75']; break;
            case '16': fontesParaMostrar = ['16', '76']; break;
            case '17': fontesParaMostrar = ['17', '77']; break;
            case '19': fontesParaMostrar = ['19', '79']; break;
            case '21': fontesParaMostrar = ['21']; break;
            case '22': fontesParaMostrar = ['22']; break;
            case '23': fontesParaMostrar = ['23']; break;
            case '24': fontesParaMostrar = ['24']; break;
        }
        
        console.log('Fontes para mostrar:', fontesParaMostrar);
        
        // Calcular totais por categoria considerando o filtro
        dadosOriginais.dados.forEach(function(item) {
            if (item.nivel === 1 && item.id) {
                const match = item.id.match(/fonte-(\d+)-(\d+)/);
                if (match) {
                    const catId = match[1];
                    const fonteId = match[2];
                    
                    if (fontesParaMostrar.includes(fonteId)) {
                        categoriasComDados.add(catId);
                        
                        if (!totaisPorCategoria[catId]) {
                            totaisPorCategoria[catId] = {
                                previsao_inicial: 0,
                                previsao_atualizada: 0,
                                receita_atual: 0,
                                receita_anterior: 0,
                                variacao_absoluta: 0,
                                variacao_percentual: 0
                            };
                        }
                        
                        totaisPorCategoria[catId].previsao_inicial += item.previsao_inicial;
                        totaisPorCategoria[catId].previsao_atualizada += item.previsao_atualizada;
                        totaisPorCategoria[catId].receita_atual += item.receita_atual;
                        totaisPorCategoria[catId].receita_anterior += item.receita_anterior;
                    }
                }
            }
        });
        
        // Calcular variações
        Object.keys(totaisPorCategoria).forEach(function(catId) {
            const totais = totaisPorCategoria[catId];
            totais.variacao_absoluta = totais.receita_atual - totais.receita_anterior;
            if (totais.receita_anterior !== 0) {
                totais.variacao_percentual = (totais.variacao_absoluta / Math.abs(totais.receita_anterior)) * 100;
            } else {
                totais.variacao_percentual = totais.receita_atual !== 0 ? 100 : 0;
            }
        });
        
        // Mostrar categorias com dados
        $('tr[data-nivel="0"]').each(function() {
            const $row = $(this);
            const id = $row.data('id');
            
            const match = id.match(/cat-(\d+)/);
            if (match) {
                const catId = match[1];
                if (categoriasComDados.has(catId)) {
                    $row.show();
                    
                    // Atualizar valores
                    if (totaisPorCategoria[catId]) {
                        const totais = totaisPorCategoria[catId];
                        $row.find('td:eq(1)').text(formatarValor(totais.previsao_inicial));
                        $row.find('td:eq(2)').text(formatarValor(totais.previsao_atualizada));
                        $row.find('td:eq(3)').text(formatarValor(totais.receita_atual));
                        $row.find('td:eq(4)').text(formatarValor(totais.receita_anterior));
                        
                        const $varAbsoluta = $row.find('td:eq(5)');
                        $varAbsoluta.text(formatarValor(totais.variacao_absoluta));
                        $varAbsoluta.removeClass('text-success text-danger');
                        if (totais.variacao_absoluta >= 0) {
                            $varAbsoluta.addClass('text-success');
                        } else {
                            $varAbsoluta.addClass('text-danger');
                        }
                        
                        const $varPercentual = $row.find('td:eq(6)');
                        $varPercentual.text(formatarPercentual(totais.variacao_percentual));
                        $varPercentual.removeClass('text-success text-danger');
                        if (totais.variacao_percentual >= 0) {
                            $varPercentual.addClass('text-success');
                        } else {
                            $varPercentual.addClass('text-danger');
                        }
                    }
                }
            }
        });
        
        // Mostrar fontes filtradas e seus filhos (incluindo UGs)
        $('tr[data-nivel]').each(function() {
            const $row = $(this);
            const nivel = parseInt($row.data('nivel'));
            const id = $row.data('id') || '';
            
            if (nivel === 1) {
                // Fontes
                const match = id.match(/fonte-(\d+)-(\d+)/);
                if (match) {
                    const catId = match[1];
                    const fonteId = match[2];
                    if (fontesParaMostrar.includes(fonteId) && categoriasComDados.has(catId)) {
                        $row.show();
                    }
                }
            } else if (nivel === 2) {
                // Subfontes
                const $tr = $row.closest('tr');
                const classes = $tr.attr('class') || '';
                const match = classes.match(/filho-de-fonte-(\d+)-(\d+)/);
                
                if (match) {
                    const catId = match[1];
                    const fonteId = match[2];
                    if (fontesParaMostrar.includes(fonteId) && categoriasComDados.has(catId)) {
                        const fonteBtn = $(`.toggle-btn[data-id="fonte-${catId}-${fonteId}"]`);
                        if (fonteBtn.hasClass('expanded')) {
                            $row.show();
                        }
                    }
                }
            } else if (nivel === 3) {
                // Alíneas
                const $tr = $row.closest('tr');
                const classes = $tr.attr('class') || '';
                const match = classes.match(/filho-de-subfonte-(\d+)-(\d+)-(\d+)/);
                
                if (match) {
                    const catId = match[1];
                    const fonteId = match[2];
                    const subfonteId = match[3];
                    if (fontesParaMostrar.includes(fonteId) && categoriasComDados.has(catId)) {
                        const fonteBtn = $(`.toggle-btn[data-id="fonte-${catId}-${fonteId}"]`);
                        const subfonteBtn = $(`.toggle-btn[data-id="subfonte-${catId}-${fonteId}-${subfonteId}"]`);
                        
                        if (fonteBtn.hasClass('expanded') && subfonteBtn.hasClass('expanded')) {
                            $row.show();
                        }
                    }
                }
            } else if (nivel === 4) {
                // UGs
                const $tr = $row.closest('tr');
                const classes = $tr.attr('class') || '';
                const match = classes.match(/filho-de-alinea-(\d+)-(\d+)-(\d+)-(\d+)/);
                
                if (match) {
                    const catId = match[1];
                    const fonteId = match[2];
                    const subfonteId = match[3];
                    const alineaId = match[4];
                    if (fontesParaMostrar.includes(fonteId) && categoriasComDados.has(catId)) {
                        const fonteBtn = $(`.toggle-btn[data-id="fonte-${catId}-${fonteId}"]`);
                        const subfonteBtn = $(`.toggle-btn[data-id="subfonte-${catId}-${fonteId}-${subfonteId}"]`);
                        const alineaBtn = $(`.toggle-btn[data-id="alinea-${catId}-${fonteId}-${subfonteId}-${alineaId}"]`);
                        
                        if (fonteBtn.hasClass('expanded') && subfonteBtn.hasClass('expanded') && alineaBtn.hasClass('expanded')) {
                            $row.show();
                        }
                    }
                }
            }
        });
    }
    
    // Recalcular totais baseado nas linhas visíveis
    recalcularTotais();
}

// Recalcular totais baseado no filtro selecionado
function recalcularTotais() {
    if (!dadosRelatorio || !dadosOriginais) {
        console.log('Dados não disponíveis para recalcular totais');
        return;
    }
    
    const filtroAtivo = $('#selectTipoReceita').val();
    console.log('Recalculando totais para filtro:', filtroAtivo);
    
    let totais = {
        previsao_inicial: 0,
        previsao_atualizada: 0,
        receita_atual: 0,
        receita_anterior: 0,
        variacao_absoluta: 0,
        variacao_percentual: 0
    };
    
    if (filtroAtivo === 'todas') {
        // Usar totais originais
        totais = dadosRelatorio.totais;
    } else {
        // Definir quais fontes somar baseado no filtro
        let fontesParaSomar = [];
        
        switch(filtroAtivo) {
            case '11': fontesParaSomar = ['11', '71']; break;
            case '12': fontesParaSomar = ['12', '72']; break;
            case '13': fontesParaSomar = ['13', '73']; break;
            case '14': fontesParaSomar = ['14', '74']; break;
            case '15': fontesParaSomar = ['15', '75']; break;
            case '16': fontesParaSomar = ['16', '76']; break;
            case '17': fontesParaSomar = ['17', '77']; break;
            case '19': fontesParaSomar = ['19', '79']; break;
            case '21': fontesParaSomar = ['21']; break;
            case '22': fontesParaSomar = ['22']; break;
            case '23': fontesParaSomar = ['23']; break;
            case '24': fontesParaSomar = ['24']; break;
        }
        
        console.log('Fontes para somar:', fontesParaSomar);
        
        // Calcular totais apenas para as fontes filtradas
        dadosOriginais.dados.forEach(function(item) {
            if (item.nivel === 1 && item.id) {
                const match = item.id.match(/fonte-\d+-(\d+)/);
                if (match) {
                    const fonteId = match[1];
                    if (fontesParaSomar.includes(fonteId)) {
                        console.log('Somando fonte:', fonteId, item);
                        totais.previsao_inicial += item.previsao_inicial;
                        totais.previsao_atualizada += item.previsao_atualizada;
                        totais.receita_atual += item.receita_atual;
                        totais.receita_anterior += item.receita_anterior;
                    }
                }
            }
        });
        
        // Calcular variações
        totais.variacao_absoluta = totais.receita_atual - totais.receita_anterior;
        if (totais.receita_anterior !== 0) {
            totais.variacao_percentual = (totais.variacao_absoluta / Math.abs(totais.receita_anterior)) * 100;
        } else {
            totais.variacao_percentual = totais.receita_atual !== 0 ? 100 : 0;
        }
    }
    
    console.log('Totais calculados:', totais);
    
    // Atualizar linha de total na tabela
    const $totalRow = $('tr.table-dark');
    if ($totalRow.length) {
        $totalRow.find('td:eq(1)').text(formatarValor(totais.previsao_inicial));
        $totalRow.find('td:eq(2)').text(formatarValor(totais.previsao_atualizada));
        $totalRow.find('td:eq(3)').text(formatarValor(totais.receita_atual));
        $totalRow.find('td:eq(4)').text(formatarValor(totais.receita_anterior));
        
        const $varAbsoluta = $totalRow.find('td:eq(5)');
        $varAbsoluta.text(formatarValor(totais.variacao_absoluta));
        $varAbsoluta.removeClass('text-success text-danger');
        if (totais.variacao_absoluta >= 0) {
            $varAbsoluta.addClass('text-success');
        } else {
            $varAbsoluta.addClass('text-danger');
        }
        
        const $varPercentual = $totalRow.find('td:eq(6)');
        $varPercentual.text(formatarPercentual(totais.variacao_percentual));
        $varPercentual.removeClass('text-success text-danger');
        if (totais.variacao_percentual >= 0) {
            $varPercentual.addClass('text-success');
        } else {
            $varPercentual.addClass('text-danger');
        }
    }
}

// Limpar filtros
function limparFiltros() {
    // Destruir módulos se existirem
    if (typeof analiseVisual !== 'undefined') {
        analiseVisual.destruir();
        $('#analiseVisualContainer').remove();
    }
    
    if (typeof comparativoMensal !== 'undefined') {
        comparativoMensal.destruir();
        $('#comparativoMensalContainer').remove();
    }
    
    $('#formFiltros')[0].reset();
    $('#selectMes').empty().append('<option value="">Selecione o ano primeiro</option>');
    $('#selectTipoReceita').val('todas');
    $('#relatorioContainer').hide();
    $('#mensagemInicial').show();
    dadosRelatorio = null;
    dadosOriginais = null;
    window.ultimoRelatorioGerado = null;
}

// Exportar relatório completo com todos os módulos
async function exportarRelatorioCompleto() {
    try {
        mostrarAlerta('Preparando exportação completa...', 'info');
        
        // Criar workbook
        const wb = XLSX.utils.book_new();
        
        // 1. Adicionar dados do relatório principal
        if (window.ultimoRelatorioGerado) {
            const dadosPrincipais = prepararDadosExportacao(window.ultimoRelatorioGerado);
            const wsPrincipal = XLSX.utils.json_to_sheet(dadosPrincipais);
            XLSX.utils.book_append_sheet(wb, wsPrincipal, 'Balanço Orçamentário');
        }
        
        // 2. Adicionar dados do comparativo mensal se disponível
        if (typeof comparativoMensal !== 'undefined' && comparativoMensal.dadosOriginais) {
            const dadosComparativo = comparativoMensal.dadosOriginais.dados_brutos.map(item => ({
                'Mês': item.nome_mes,
                [`Receita ${item.ano_anterior}`]: item.receita_anterior,
                [`Receita ${item.ano_atual}`]: item.receita_atual,
                'Variação R$': item.variacao_absoluta,
                'Variação %': item.variacao_percentual.toFixed(2) + '%'
            }));
            const wsComparativo = XLSX.utils.json_to_sheet(dadosComparativo);
            XLSX.utils.book_append_sheet(wb, wsComparativo, 'Comparativo Mensal');
        }
        
        // 3. Gerar nome do arquivo
        const timestamp = new Date().getTime();
        const nomeArquivo = `relatorio_completo_receitas_${timestamp}.xlsx`;
        
        // 4. Baixar arquivo
        XLSX.writeFile(wb, nomeArquivo);
        
        mostrarAlerta('Relatório completo exportado com sucesso!', 'success');
        
    } catch (error) {
        console.error('Erro ao exportar relatório completo:', error);
        mostrarAlerta('Erro ao exportar relatório completo', 'danger');
    }
}

// Preparar dados para exportação
function prepararDadosExportacao(relatorio) {
    const dados = [];
    
    relatorio.dados.forEach(item => {
        let prefixo = '  '.repeat(item.nivel);
        let descricao = item.descricao;
        
        // Adicionar indicador para UGs
        if (item.nivel === 4) {
            prefixo += '► ';
            descricao = `UG ${descricao}`;
        }
        
        dados.push({
            'Código': item.codigo,
            'Especificação': prefixo + descricao,
            'Previsão Inicial': item.previsao_inicial,
            'Previsão Atualizada': item.previsao_atualizada,
            [`Realizado ${relatorio.periodo.ano_anterior}`]: item.receita_anterior,
            [`Realizado ${relatorio.periodo.ano}`]: item.receita_atual,
            'Variação %': item.variacao_percentual.toFixed(2)
        });
    });
    
    // Adicionar total
    dados.push({
        'Código': '',
        'Especificação': 'TOTAL GERAL',
        'Previsão Inicial': relatorio.totais.previsao_inicial,
        'Previsão Atualizada': relatorio.totais.previsao_atualizada,
        [`Realizado ${relatorio.periodo.ano_anterior}`]: relatorio.totais.receita_anterior,
        [`Realizado ${relatorio.periodo.ano}`]: relatorio.totais.receita_atual,
        'Variação %': relatorio.totais.variacao_percentual.toFixed(2)
    });
    
    return dados;
}

// Exportar para Excel - ATUALIZADO com UGs
function exportarExcel() {
    if (!dadosRelatorio) {
        mostrarAlerta('Nenhum relatório para exportar!', 'warning');
        return;
    }
    
    console.log('📊 Exportando para Excel...');
    
    // Criar dados para o Excel
    const workbook = XLSX.utils.book_new();
    
    // Dados para a planilha
    const wsData = [
        // Cabeçalho
        ['BALANÇO ORÇAMENTÁRIO DA RECEITA'],
        [`${dadosRelatorio.periodo.nome_mes}/${dadosRelatorio.periodo.ano}`],
        [`UG: ${dadosRelatorio.filtros.nome_coug}`],
        [],
        // Cabeçalhos da tabela
        [
            'RECEITAS',
            `PREVISÃO INICIAL ${dadosRelatorio.periodo.ano}`,
            `PREVISÃO ATUALIZADA ${dadosRelatorio.periodo.ano}`,
            `REALIZADA ${dadosRelatorio.periodo.mes}/${dadosRelatorio.periodo.ano}`,
            `REALIZADA ${dadosRelatorio.periodo.mes}/${dadosRelatorio.periodo.ano_anterior}`,
            'VARIAÇÃO ABSOLUTA',
            'VARIAÇÃO %'
        ]
    ];
    
    // Dados do relatório com indicação especial para UGs
    dadosRelatorio.dados.forEach(function(item) {
        let prefixo = item.nivel > 0 ? '  '.repeat(item.nivel) : '';
        let descricao = item.descricao;
        
        // Adicionar indicador para UGs
        if (item.nivel === 4) {
            prefixo += '► ';
            descricao = `UG ${descricao}`;
        }
        
        wsData.push([
            prefixo + descricao,
            item.previsao_inicial,
            item.previsao_atualizada,
            item.receita_atual,
            item.receita_anterior,
            item.variacao_absoluta,
            item.variacao_percentual / 100 // Para formato de percentual no Excel
        ]);
    });
    
    // Total
    wsData.push([
        'TOTAL GERAL',
        dadosRelatorio.totais.previsao_inicial,
        dadosRelatorio.totais.previsao_atualizada,
        dadosRelatorio.totais.receita_atual,
        dadosRelatorio.totais.receita_anterior,
        dadosRelatorio.totais.variacao_absoluta,
        dadosRelatorio.totais.variacao_percentual / 100
    ]);
    
    // Criar worksheet
    const worksheet = XLSX.utils.aoa_to_sheet(wsData);
    
    // Adicionar formatação de largura de coluna
    worksheet['!cols'] = [
        { wch: 60 }, // Receitas (maior para acomodar UGs)
        { wch: 20 }, // Previsão Inicial
        { wch: 20 }, // Previsão Atualizada
        { wch: 20 }, // Realizada Atual
        { wch: 20 }, // Realizada Anterior
        { wch: 20 }, // Variação Absoluta
        { wch: 15 }  // Variação %
    ];
    
    // Adicionar worksheet ao workbook
    XLSX.utils.book_append_sheet(workbook, worksheet, 'Balanço Receita');
    
    // Gerar arquivo e download
    const filename = `balanco_receita_${dadosRelatorio.periodo.ano}_${dadosRelatorio.periodo.mes}.xlsx`;
    XLSX.writeFile(workbook, filename);
    
    mostrarAlerta('Arquivo Excel gerado com sucesso!', 'success');
}

// Download como imagem em alta resolução
function downloadImagem() {
    if (!dadosRelatorio) {
        mostrarAlerta('Nenhum relatório para exportar!', 'warning');
        return;
    }
    
    // Mostrar loading
    mostrarAlerta('Gerando imagem em alta resolução...', 'info');
    
    // Desabilitar botão temporariamente
    $('#btnDownloadImagem').prop('disabled', true).html('<i class="bi bi-hourglass-split"></i> Gerando...');
    
    // Criar container temporário com fundo branco
    const containerTemp = document.createElement('div');
    containerTemp.style.position = 'absolute';
    containerTemp.style.left = '-9999px';
    containerTemp.style.background = 'white';
    containerTemp.style.padding = '30px';
    containerTemp.style.width = '297mm'; // Largura A4 paisagem
    containerTemp.style.fontFamily = 'Arial, sans-serif';
    
    // Adicionar título e informações do cabeçalho
    const cabecalho = document.createElement('div');
    cabecalho.style.textAlign = 'center';
    cabecalho.style.marginBottom = '20px';
    cabecalho.innerHTML = `
        <h2 style="color: #1e3c72; margin-bottom: 10px; font-size: 24px;">BALANÇO ORÇAMENTÁRIO DA RECEITA</h2>
        <h3 style="color: #333; margin-bottom: 8px; font-size: 18px;">${dadosRelatorio.periodo.nome_mes}/${dadosRelatorio.periodo.ano}</h3>
        <p style="color: #666; margin: 5px 0; font-size: 14px;">UG: ${dadosRelatorio.filtros.nome_coug}</p>
    `;
    
    // Criar tabela
    const tabelaContainer = document.createElement('div');
    
    let tabelaHTML = `
        <table style="width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 20px;">
            <thead>
                <tr style="background-color: #1e3c72; color: white;">
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: left; width: 35%;">RECEITAS</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">PREVISÃO INICIAL<br>${dadosRelatorio.periodo.ano}</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">PREVISÃO ATUALIZADA<br>${dadosRelatorio.periodo.ano}</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">REALIZADA<br>${dadosRelatorio.periodo.mes}/${dadosRelatorio.periodo.ano}</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">REALIZADA<br>${dadosRelatorio.periodo.mes}/${dadosRelatorio.periodo.ano_anterior}</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">VARIAÇÃO<br>ABSOLUTA</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">VARIAÇÃO<br>%</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    // Adicionar linhas de dados
    dadosRelatorio.dados.forEach(function(item) {
        const paddingLeft = 10 + (item.nivel * 20);
        const fontWeight = item.nivel === 0 ? 'bold' : 'normal';
        let backgroundColor = 'white';
        
        if (item.nivel === 0) {
            backgroundColor = '#f5f5f5';
        } else if (item.nivel === 4) {
            backgroundColor = '#e3f2fd';
        }
        
        const corVariacao = item.variacao_absoluta >= 0 ? '#28a745' : '#dc3545';
        
        let descricao = item.descricao;
        if (item.nivel === 4) {
            descricao = `► UG ${descricao}`;
        }
        
        tabelaHTML += `
            <tr style="background-color: ${backgroundColor};">
                <td style="border: 1px solid #ddd; padding: 6px 8px; padding-left: ${paddingLeft}px; font-weight: ${fontWeight};">
                    ${descricao}
                </td>
                <td style="border: 1px solid #ddd; padding: 6px 8px; text-align: right; font-weight: ${fontWeight};">
                    ${formatarValor(item.previsao_inicial)}
                </td>
                <td style="border: 1px solid #ddd; padding: 6px 8px; text-align: right; font-weight: ${fontWeight};">
                    ${formatarValor(item.previsao_atualizada)}
                </td>
                <td style="border: 1px solid #ddd; padding: 6px 8px; text-align: right; font-weight: ${fontWeight};">
                    ${formatarValor(item.receita_atual)}
                </td>
                <td style="border: 1px solid #ddd; padding: 6px 8px; text-align: right; font-weight: ${fontWeight};">
                    ${formatarValor(item.receita_anterior)}
                </td>
                <td style="border: 1px solid #ddd; padding: 6px 8px; text-align: right; font-weight: ${fontWeight}; color: ${corVariacao};">
                    ${formatarValor(item.variacao_absoluta)}
                </td>
                <td style="border: 1px solid #ddd; padding: 6px 8px; text-align: center; font-weight: ${fontWeight}; color: ${corVariacao};">
                    ${formatarPercentual(item.variacao_percentual)}
                </td>
            </tr>
        `;
    });
    
    // Adicionar linha de total
    const corTotalVariacao = dadosRelatorio.totais.variacao_absoluta >= 0 ? '#28a745' : '#dc3545';
    tabelaHTML += `
            <tr style="background-color: #2c3e50; color: white; font-weight: bold;">
                <td style="border: 1px solid #ddd; padding: 8px;">TOTAL GERAL</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">
                    ${formatarValor(dadosRelatorio.totais.previsao_inicial)}
                </td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">
                    ${formatarValor(dadosRelatorio.totais.previsao_atualizada)}
                </td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">
                    ${formatarValor(dadosRelatorio.totais.receita_atual)}
                </td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">
                    ${formatarValor(dadosRelatorio.totais.receita_anterior)}
                </td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right; color: ${corTotalVariacao};">
                    ${formatarValor(dadosRelatorio.totais.variacao_absoluta)}
                </td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: center; color: ${corTotalVariacao};">
                    ${formatarPercentual(dadosRelatorio.totais.variacao_percentual)}
                </td>
            </tr>
            </tbody>
        </table>
    `;
    
    tabelaContainer.innerHTML = tabelaHTML;
    
    // Adicionar rodapé
    const rodape = document.createElement('div');
    rodape.style.textAlign = 'center';
    rodape.style.marginTop = '30px';
    rodape.style.fontSize = '10px';
    rodape.style.color = '#666';
    rodape.style.borderTop = '1px solid #ddd';
    rodape.style.paddingTop = '10px';
    rodape.innerHTML = `
        <p style="margin: 0;">Gerado em: ${dadosRelatorio.data_geracao}</p>
    `;
    
    // Montar container
    containerTemp.appendChild(cabecalho);
    containerTemp.appendChild(tabelaContainer);
    containerTemp.appendChild(rodape);
    document.body.appendChild(containerTemp);
    
    // Configurações do html2canvas para alta resolução
    html2canvas(containerTemp, {
        scale: 3, // Aumentar escala para alta resolução
        useCORS: true,
        logging: false,
        backgroundColor: '#ffffff',
        windowWidth: containerTemp.scrollWidth,
        windowHeight: containerTemp.scrollHeight
    }).then(canvas => {
        // Remover container temporário
        document.body.removeChild(containerTemp);
        
        // Converter para blob e fazer download
        canvas.toBlob(function(blob) {
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            
            // Nome do arquivo
            const nomeArquivo = `balanco_receita_${dadosRelatorio.periodo.ano}_${dadosRelatorio.periodo.mes}_${new Date().getTime()}.png`;
            
            link.download = nomeArquivo;
            link.href = url;
            link.click();
            
            // Limpar URL
            URL.revokeObjectURL(url);
            
            // Restaurar botão
            $('#btnDownloadImagem').prop('disabled', false).html('<i class="bi bi-image"></i> Imagem HD');
            
            mostrarAlerta('Imagem gerada com sucesso!', 'success');
        }, 'image/png', 1.0); // Qualidade máxima
    }).catch(error => {
        console.error('Erro ao gerar imagem:', error);
        
        // Remover container se ainda existir
        if (containerTemp.parentNode) {
            document.body.removeChild(containerTemp);
        }
        
        // Restaurar botão
        $('#btnDownloadImagem').prop('disabled', false).html('<i class="bi bi-image"></i> Imagem HD');
        
        mostrarAlerta('Erro ao gerar imagem. Por favor, tente novamente.', 'danger');
    });
}

// Funções auxiliares
function mostrarAlerta(mensagem, tipo = 'info') {
    const alertHtml = `
        <div class="alert alert-${tipo} alert-dismissible fade show" role="alert">
            ${mensagem}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Inserir alerta no topo do container principal
    $('.container-fluid').prepend(alertHtml);
    
    // Auto-remover após 5 segundos
    setTimeout(function() {
        $('.alert').fadeOut('slow', function() {
            $(this).remove();
        });
    }, 5000);
}

function mostrarErro(mensagem) {
    $('#mensagemInicial')
        .removeClass('alert-info')
        .addClass('alert-danger')
        .html(`<i class="bi bi-exclamation-triangle"></i> ${mensagem}`)
        .show();
}