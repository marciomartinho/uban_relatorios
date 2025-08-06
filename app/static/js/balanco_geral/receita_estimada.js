/**
 * JavaScript específico para Receita Estimada Líquida
 * Parte do Balanço Geral GDF
 */

// NÃO declarar variáveis aqui - elas já estão em balanco_geral.js
// let dadosReceitaEstimada = null; // REMOVIDO

/**
 * Gera o quadro de receita estimada
 */
async function gerarReceitaEstimada() {
    // Mostrar loading (função do balanco_geral.js)
    mostrarLoading();
    
    try {
        // Buscar dados da API
        const response = await fetch('/balanco-geral/api/dados-receita-estimada');
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.erro || 'Erro ao buscar dados');
        }
        
        // Armazenar dados na variável global (definida em balanco_geral.js)
        dadosReceitaEstimada = data;
        
        // Gerar HTML do quadro
        const quadroHTML = gerarHTMLReceitaEstimada(data);
        
        // Mostrar preview (função do balanco_geral.js)
        mostrarPreview(quadroHTML);
        
        // Atualizar variável global
        quadroAtual = 'receita_estimada';
        
    } catch (error) {
        console.error('Erro ao gerar quadro de receita estimada:', error);
        mostrarErro('Erro ao gerar quadro: ' + error.message);
    }
}

/**
 * Gera o HTML do quadro de Receita Estimada
 */
function gerarHTMLReceitaEstimada(dados) {
    const { ano_atual, ano_anterior, dados: linhas } = dados;
    
    let html = `
        <table class="tabela-receita-estimada">
            <thead>
                <tr class="header-principal">
                    <th colspan="7" class="titulo-principal">RECEITA ESTIMADA LÍQUIDA</th>
                </tr>
                <tr class="header-anos">
                    <th rowspan="2" class="col-especificacao">ESPECIFICAÇÃO</th>
                    <th colspan="2" class="ano-header">${ano_atual}</th>
                    <th colspan="2" class="ano-header">${ano_anterior}</th>
                    <th rowspan="2" class="col-variacao">Δ%</th>
                </tr>
                <tr class="header-colunas">
                    <th class="col-valor">RECEITA<br>PREVISTA</th>
                    <th class="col-percentual">%</th>
                    <th class="col-valor">RECEITA<br>PREVISTA</th>
                    <th class="col-percentual">%</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    // Adicionar linhas de dados
    linhas.forEach(linha => {
        if (linha.tipo === 'categoria') {
            html += `
                <tr class="linha-categoria">
                    <td class="col-especificacao">${linha.nome}</td>
                    <td class="col-valor">${formatarMoeda(linha.valor_atual)}</td>
                    <td class="col-percentual">${formatarPercentual(linha.percentual_atual)}</td>
                    <td class="col-valor">${formatarMoeda(linha.valor_anterior)}</td>
                    <td class="col-percentual">${formatarPercentual(linha.percentual_anterior)}</td>
                    <td class="col-variacao ${linha.variacao >= 0 ? 'positiva' : 'negativa'}">
                        ${formatarPercentual(linha.variacao)}
                    </td>
                </tr>
            `;
            
            // Adicionar fontes
            if (linha.fontes) {
                linha.fontes.forEach(fonte => {
                    html += `
                        <tr class="linha-fonte">
                            <td class="col-especificacao">${fonte.nome}</td>
                            <td class="col-valor">${formatarMoeda(fonte.valor_atual)}</td>
                            <td class="col-percentual">${formatarPercentual(fonte.percentual_atual)}</td>
                            <td class="col-valor">${formatarMoeda(fonte.valor_anterior)}</td>
                            <td class="col-percentual">${formatarPercentual(fonte.percentual_anterior)}</td>
                            <td class="col-variacao ${fonte.variacao >= 0 ? 'positiva' : 'negativa'}">
                                ${formatarPercentual(fonte.variacao)}
                            </td>
                        </tr>
                    `;
                });
            }
        } else if (linha.tipo === 'total') {
            html += `
                <tr class="linha-total">
                    <td class="col-especificacao">${linha.nome}</td>
                    <td class="col-valor">${formatarMoeda(linha.valor_atual)}</td>
                    <td class="col-percentual">${formatarPercentual(linha.percentual_atual)}</td>
                    <td class="col-valor">${formatarMoeda(linha.valor_anterior)}</td>
                    <td class="col-percentual">${formatarPercentual(linha.percentual_anterior)}</td>
                    <td class="col-variacao ${linha.variacao >= 0 ? 'positiva' : 'negativa'}">
                        ${formatarPercentual(linha.variacao)}
                    </td>
                </tr>
            `;
        }
    });
    
    html += `
            </tbody>
        </table>
        <div class="rodape-tabela">
            <p>Tabela 1 – Receita Líquida Estimada ${ano_atual} – Comparada com ${ano_anterior}</p>
            <p>Dados em: R$ 1,00</p>
            <p>Fonte: SIAC/SIGGO WEB</p>
        </div>
    `;
    
    return html;
}

/**
 * Gera HTML com estilos inline para captura de imagem
 */
function gerarHTMLReceitaEstimadaParaImagem(dados) {
    const { ano_atual, ano_anterior, dados: linhas } = dados;
    
    let html = `
        <style>
            table { 
                width: 100%; 
                border-collapse: collapse; 
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            th, td { 
                border: 1px solid #000; 
                padding: 8px; 
                text-align: right;
            }
            .titulo-principal {
                background-color: #1e3c72;
                color: white;
                font-size: 18px;
                font-weight: bold;
                text-align: center;
                padding: 12px;
            }
            .header-anos th {
                background-color: #2a5298;
                color: white;
                font-weight: bold;
                text-align: center;
            }
            .header-colunas th {
                background-color: #3468c0;
                color: white;
                font-weight: bold;
                text-align: center;
                font-size: 12px;
            }
            .col-especificacao {
                text-align: left !important;
                width: 40%;
            }
            .linha-categoria td {
                font-weight: bold;
                background-color: #e8f0ff;
            }
            .linha-fonte td {
                padding-left: 30px;
            }
            .linha-fonte .col-especificacao {
                padding-left: 30px;
            }
            .linha-total td {
                font-weight: bold;
                background-color: #1e3c72;
                color: white;
            }
            .positiva { color: #28a745; }
            .negativa { color: #dc3545; }
            .rodape-tabela {
                margin-top: 20px;
                font-size: 11px;
                color: #666;
                line-height: 1.4;
            }
        </style>
        
        <table>
            <thead>
                <tr>
                    <th colspan="6" class="titulo-principal">RECEITA ESTIMADA LÍQUIDA</th>
                </tr>
                <tr class="header-anos">
                    <th rowspan="2" class="col-especificacao">ESPECIFICAÇÃO</th>
                    <th colspan="2">${ano_atual}</th>
                    <th colspan="2">${ano_anterior}</th>
                    <th rowspan="2">Δ%</th>
                </tr>
                <tr class="header-colunas">
                    <th>RECEITA<br>PREVISTA</th>
                    <th>%</th>
                    <th>RECEITA<br>PREVISTA</th>
                    <th>%</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    // Adicionar linhas
    linhas.forEach(linha => {
        if (linha.tipo === 'categoria') {
            html += `
                <tr class="linha-categoria">
                    <td class="col-especificacao">${linha.nome}</td>
                    <td>${formatarMoeda(linha.valor_atual)}</td>
                    <td>${formatarPercentual(linha.percentual_atual)}</td>
                    <td>${formatarMoeda(linha.valor_anterior)}</td>
                    <td>${formatarPercentual(linha.percentual_anterior)}</td>
                    <td class="${linha.variacao >= 0 ? 'positiva' : 'negativa'}">
                        ${formatarPercentual(linha.variacao)}
                    </td>
                </tr>
            `;
            
            if (linha.fontes) {
                linha.fontes.forEach(fonte => {
                    html += `
                        <tr class="linha-fonte">
                            <td class="col-especificacao">${fonte.nome}</td>
                            <td>${formatarMoeda(fonte.valor_atual)}</td>
                            <td>${formatarPercentual(fonte.percentual_atual)}</td>
                            <td>${formatarMoeda(fonte.valor_anterior)}</td>
                            <td>${formatarPercentual(fonte.percentual_anterior)}</td>
                            <td class="${fonte.variacao >= 0 ? 'positiva' : 'negativa'}">
                                ${formatarPercentual(fonte.variacao)}
                            </td>
                        </tr>
                    `;
                });
            }
        } else if (linha.tipo === 'total') {
            html += `
                <tr class="linha-total">
                    <td class="col-especificacao">${linha.nome}</td>
                    <td>${formatarMoeda(linha.valor_atual)}</td>
                    <td>${formatarPercentual(linha.percentual_atual)}</td>
                    <td>${formatarMoeda(linha.valor_anterior)}</td>
                    <td>${formatarPercentual(linha.percentual_anterior)}</td>
                    <td>${linha.variacao >= 0 ? '+' : ''}${formatarPercentual(linha.variacao)}</td>
                </tr>
            `;
        }
    });
    
    html += `
            </tbody>
        </table>
        <div class="rodape-tabela">
            <p>Tabela 1 – Receita Líquida Estimada ${ano_atual} – Comparada com ${ano_anterior}</p>
            <p>Dados em: R$ 1,00</p>
            <p>Fonte: SIAC/SIGGO WEB</p>
        </div>
    `;
    
    return html;
}