// JavaScript para Balanço Orçamentário da Receita

console.log('Balanço Receita JS carregado');

// Variáveis globais
let dadosRelatorio = null;
let filtrosCarregados = false;

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
            }
            
            // UGs
            $('#selectUG').empty().append('<option value="">📊 Dados Consolidados</option>');
            if (data.ugs && data.ugs.length > 0) {
                data.ugs.forEach(function(ug) {
                    $('#selectUG').append(`<option value="${ug.codigo}">🏛️ ${ug.descricao}</option>`);
                });
            }
            
            // Filtros de receita
            $('#filtrosReceita').empty();
            if (data.filtros_receita && data.filtros_receita.length > 0) {
                data.filtros_receita.forEach(function(filtro) {
                    $('#filtrosReceita').append(`
                        <button type="button" class="btn btn-outline-primary filtro-receita ${filtro.valor === 'todas' ? 'active' : ''}" 
                                data-filtro="${filtro.valor}">
                            ${filtro.nome}
                        </button>
                    `);
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

// Configurar eventos
function configurarEventos() {
    // Mudança de ano - carregar meses disponíveis
    $('#selectAno').on('change', function() {
        const ano = $(this).val();
        carregarMeses(ano);
    });
    
    // Clique nos filtros de receita
    $(document).on('click', '.filtro-receita', function() {
        $('.filtro-receita').removeClass('active');
        $(this).addClass('active');
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
    
    // Toggle de expansão/colapso
    $(document).on('click', '.toggle-btn', function() {
        const $btn = $(this);
        const nivel = parseInt($btn.data('nivel'));
        const id = $btn.data('id');
        const isExpanded = $btn.hasClass('expanded');
        
        if (isExpanded) {
            // Colapsar
            $btn.removeClass('expanded').text('+');
            $(`.filho-de-${id}`).hide();
        } else {
            // Expandir
            $btn.addClass('expanded').text('−');
            $(`.filho-de-${id}`).show();
        }
    });
}

// Carregar meses disponíveis para o ano selecionado
function carregarMeses(ano) {
    if (!ano) {
        $('#selectMes').empty().append('<option value="">Selecione o ano primeiro</option>');
        return;
    }
    
    // Por enquanto, vamos usar todos os meses
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
    const filtro = $('.filtro-receita.active').data('filtro') || 'todas';
    
    // Validação
    if (!ano || !mes) {
        mostrarAlerta('Por favor, selecione ano e mês!', 'warning');
        return;
    }
    
    console.log('🦆 Gerando relatório:', {ano, mes, coug, filtro});
    
    // Esconder mensagem inicial e mostrar loading
    $('#mensagemInicial').hide();
    $('#relatorioContainer').html(`
        <div class="loading-container">
            <i class="bi bi-hourglass-split"></i>
            <h4 class="mt-3">Gerando relatório...</h4>
            <p class="text-muted">Consultando dados no DuckDB</p>
        </div>
    `).show();
    
    // Fazer requisição
    $.ajax({
        url: '/balanco-receita/api/gerar-relatorio',
        method: 'GET',
        data: {
            ano: ano,
            mes: mes,
            coug: coug,
            filtro: filtro
        },
        success: function(response) {
            console.log('✅ Relatório gerado:', response);
            
            // Armazenar dados globalmente
            dadosRelatorio = response;
            
            // Renderizar relatório completo
            renderizarRelatorio(response);
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

// Renderizar relatório completo
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
                        <small class="text-muted">UG: ${dados.filtros.nome_coug} | Filtro: ${dados.filtros.filtro_descricao}</small>
                    </div>
                    <div class="col-md-4 text-end">
                        <button id="btnExportar" class="btn btn-success btn-sm">
                            <i class="bi bi-file-earmark-excel"></i> Excel
                        </button>
                        <button id="btnDownloadImagem" class="btn btn-warning btn-sm">
                            <i class="bi bi-image"></i> Imagem HD
                        </button>
                        <button id="btnImprimir" class="btn btn-primary btn-sm">
                            <i class="bi bi-printer"></i> Imprimir
                        </button>
                    </div>
                </div>
            </div>
            <div class="card-body">
    `;
    
    // Verificar se há dados
    if (!dados.dados || dados.dados.length === 0) {
        html += `
            <div class="alert alert-warning">
                <i class="bi bi-exclamation-triangle"></i> 
                Nenhum dado encontrado para os filtros selecionados.
            </div>
        `;
    } else {
        // Criar tabela
        html += `
            <div class="table-responsive">
                <table class="table table-bordered table-hover" id="tabelaBalanco">
                    <thead class="table-primary">
                        <tr>
                            <th style="min-width: 350px;">RECEITAS</th>
                            <th class="text-end">PREVISÃO INICIAL<br>${dados.periodo.ano}</th>
                            <th class="text-end">PREVISÃO ATUALIZADA<br>${dados.periodo.ano}</th>
                            <th class="text-end">REALIZADA<br>${dados.periodo.mes}/${dados.periodo.ano}</th>
                            <th class="text-end">REALIZADA<br>${dados.periodo.mes}/${dados.periodo.ano_anterior}</th>
                            <th class="text-center">VARIAÇÃO<br>ABSOLUTA</th>
                            <th class="text-center">VARIAÇÃO<br>%</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        // Adicionar linhas de dados
        dados.dados.forEach(function(item) {
            const classeNivel = `nivel-${item.nivel}`;
            const classeLinha = item.nivel === 0 ? 'table-light fw-bold' : '';
            const paddingLeft = item.nivel * 30;
            
            html += `
                <tr class="${classeLinha} ${classeNivel}" data-id="${item.id}" data-nivel="${item.nivel}">
                    <td style="padding-left: ${paddingLeft}px;">
            `;
            
            // Adicionar botão de expansão se tiver filhos
            if (item.tem_filhos) {
                html += `<button class="btn btn-sm btn-link toggle-btn" data-nivel="${item.nivel}" data-id="${item.id}">+</button> `;
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
            
            // Se for nível 1, adicionar classe para esconder inicialmente
            if (item.nivel === 1) {
                // Adicionar classe para identificar como filho
                const paiId = item.id.split('-')[1]; // Extrair ID da categoria pai
                html = html.replace(`<tr class="${classeLinha} ${classeNivel}"`, 
                                  `<tr class="${classeLinha} ${classeNivel} filho-de-cat-${paiId}" style="display: none;"`);
            }
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

// Limpar filtros
function limparFiltros() {
    $('#formFiltros')[0].reset();
    $('#selectMes').empty().append('<option value="">Selecione o ano primeiro</option>');
    $('.filtro-receita').removeClass('active');
    $('.filtro-receita[data-filtro="todas"]').addClass('active');
    $('#relatorioContainer').hide();
    $('#mensagemInicial').show();
    dadosRelatorio = null;
}

// Exportar para Excel (placeholder)
function exportarExcel() {
    if (!dadosRelatorio) {
        mostrarAlerta('Nenhum relatório para exportar!', 'warning');
        return;
    }
    
    console.log('📊 Exportando para Excel...');
    mostrarAlerta('Exportação para Excel será implementada em breve!', 'info');
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
    containerTemp.style.width = '190mm'; // Largura A4 retrato com margem
    containerTemp.style.fontFamily = 'Arial, sans-serif';
    
    // Adicionar título e informações do cabeçalho
    const cabecalho = document.createElement('div');
    cabecalho.style.textAlign = 'center';
    cabecalho.style.marginBottom = '20px';
    cabecalho.innerHTML = `
        <h2 style="color: #1e3c72; margin-bottom: 10px; font-size: 24px;">BALANÇO ORÇAMENTÁRIO DA RECEITA</h2>
        <h3 style="color: #333; margin-bottom: 8px; font-size: 18px;">${dadosRelatorio.periodo.nome_mes}/${dadosRelatorio.periodo.ano}</h3>
        <p style="color: #666; margin: 5px 0; font-size: 14px;">UG: ${dadosRelatorio.filtros.nome_coug}</p>
        <p style="color: #666; margin: 5px 0; font-size: 14px;">Filtro: ${dadosRelatorio.filtros.filtro_descricao}</p>
    `;
    
    // Criar tabela reformatada para caber em retrato
    const tabelaContainer = document.createElement('div');
    
    // Criar a tabela reorganizada
    let tabelaHTML = `
        <table style="width: 100%; border-collapse: collapse; font-size: 11px; margin-top: 20px;">
            <thead>
                <tr style="background-color: #1e3c72; color: white;">
                    <th rowspan="2" style="border: 1px solid #ddd; padding: 8px; text-align: left; width: 40%;">RECEITAS</th>
                    <th colspan="3" style="border: 1px solid #ddd; padding: 8px; text-align: center;">VALORES (R$)</th>
                </tr>
                <tr style="background-color: #1e3c72; color: white;">
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right; width: 20%;">PREVISÃO INICIAL<br>${dadosRelatorio.periodo.ano}</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right; width: 20%;">PREVISÃO ATUALIZADA<br>${dadosRelatorio.periodo.ano}</th>
                    <th style="border: 1px solid #ddd; padding: 8px; text-align: right; width: 20%;">REALIZADA<br>${dadosRelatorio.periodo.mes}/${dadosRelatorio.periodo.ano}</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    // Adicionar linhas de dados com apenas as colunas essenciais
    dadosRelatorio.dados.forEach(function(item) {
        const paddingLeft = 10 + (item.nivel * 20);
        const fontWeight = item.nivel === 0 ? 'bold' : 'normal';
        const backgroundColor = item.nivel === 0 ? '#f5f5f5' : 'white';
        
        let descricao = item.descricao;
        if (item.tem_filhos) {
            descricao = `+ ${descricao}`;
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
            </tr>
        `;
    });
    
    // Adicionar linha de total
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
            </tr>
            </tbody>
        </table>
    `;
    
    tabelaContainer.innerHTML = tabelaHTML;
    
    // Adicionar tabela de variações separada (opcional - se couber)
    const variacoesHTML = `
        <div style="margin-top: 20px; page-break-inside: avoid;">
            <h4 style="color: #1e3c72; margin-bottom: 10px; font-size: 14px;">ANÁLISE DE VARIAÇÕES</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 10px;">
                <thead>
                    <tr style="background-color: #495057; color: white;">
                        <th style="border: 1px solid #ddd; padding: 6px; text-align: left;">CATEGORIA</th>
                        <th style="border: 1px solid #ddd; padding: 6px; text-align: right;">REALIZADA ${dadosRelatorio.periodo.mes}/${dadosRelatorio.periodo.ano_anterior}</th>
                        <th style="border: 1px solid #ddd; padding: 6px; text-align: right;">VARIAÇÃO ABSOLUTA</th>
                        <th style="border: 1px solid #ddd; padding: 6px; text-align: center;">VARIAÇÃO %</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    let variacoesBody = '';
    // Adicionar apenas categorias principais (nível 0) na tabela de variações
    dadosRelatorio.dados.filter(item => item.nivel === 0).forEach(function(item) {
        const corVariacao = item.variacao_absoluta >= 0 ? '#28a745' : '#dc3545';
        variacoesBody += `
            <tr>
                <td style="border: 1px solid #ddd; padding: 4px 6px; font-weight: bold;">${item.descricao}</td>
                <td style="border: 1px solid #ddd; padding: 4px 6px; text-align: right;">
                    ${formatarValor(item.receita_anterior)}
                </td>
                <td style="border: 1px solid #ddd; padding: 4px 6px; text-align: right; color: ${corVariacao};">
                    ${formatarValor(item.variacao_absoluta)}
                </td>
                <td style="border: 1px solid #ddd; padding: 4px 6px; text-align: center; color: ${corVariacao};">
                    ${formatarPercentual(item.variacao_percentual)}
                </td>
            </tr>
        `;
    });
    
    // Total das variações
    const corTotalVariacao = dadosRelatorio.totais.variacao_absoluta >= 0 ? '#28a745' : '#dc3545';
    variacoesBody += `
        <tr style="background-color: #f5f5f5; font-weight: bold;">
            <td style="border: 1px solid #ddd; padding: 6px;">TOTAL</td>
            <td style="border: 1px solid #ddd; padding: 6px; text-align: right;">
                ${formatarValor(dadosRelatorio.totais.receita_anterior)}
            </td>
            <td style="border: 1px solid #ddd; padding: 6px; text-align: right; color: ${corTotalVariacao};">
                ${formatarValor(dadosRelatorio.totais.variacao_absoluta)}
            </td>
            <td style="border: 1px solid #ddd; padding: 6px; text-align: center; color: ${corTotalVariacao};">
                ${formatarPercentual(dadosRelatorio.totais.variacao_percentual)}
            </td>
        </tr>
    `;
    
    const tabelaVariacoes = document.createElement('div');
    tabelaVariacoes.innerHTML = variacoesHTML + variacoesBody + '</tbody></table></div>';
    
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
    containerTemp.appendChild(tabelaVariacoes);
    containerTemp.appendChild(rodape);
    document.body.appendChild(containerTemp);
    
    // Configurações do html2canvas para alta resolução
    html2canvas(containerTemp, {
        scale: 3, // Aumentar escala para alta resolução
        useCORS: true,
        logging: false,
        backgroundColor: '#ffffff',
        windowWidth: containerTemp.scrollWidth,
        windowHeight: containerTemp.scrollHeight,
        onclone: function(clonedDoc) {
            // Garantir que todos os estilos sejam aplicados no clone
            const clonedContainer = clonedDoc.querySelector('[style*="position: absolute"]');
            if (clonedContainer) {
                clonedContainer.style.position = 'relative';
                clonedContainer.style.left = '0';
            }
        }
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