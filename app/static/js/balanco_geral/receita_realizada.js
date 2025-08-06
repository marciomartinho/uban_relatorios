/**
 * JavaScript específico para Receita Líquida Realizada
 * Parte do Balanço Geral GDF
 */

// Variável global já definida em balanco_geral.js
// let dadosReceitaRealizada = null;

/**
 * Gera o quadro de receita realizada
 */
async function gerarReceitaRealizada() {
    // Mostrar loading (função do balanco_geral.js)
    mostrarLoading();
    
    try {
        // Buscar dados da API
        const response = await fetch('/balanco-geral/api/dados-receita-realizada');
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.erro || 'Erro ao buscar dados');
        }
        
        // Armazenar dados na variável global
        dadosReceitaRealizada = data;
        
        // Gerar HTML do quadro
        const quadroHTML = gerarHTMLReceitaRealizada(data);
        
        // Mostrar preview (função do balanco_geral.js)
        mostrarPreview(quadroHTML);
        
        // Atualizar variável global
        quadroAtual = 'receita_realizada';
        
    } catch (error) {
        console.error('Erro ao gerar quadro de receita realizada:', error);
        mostrarErro('Erro ao gerar quadro: ' + error.message);
    }
}

/**
 * Gera o HTML do quadro de Receita Realizada
 */
function gerarHTMLReceitaRealizada(dados) {
    const { ano_atual, ano_anterior, dados: linhas } = dados;
    
    let html = `
        <table class="tabela-receita-realizada">
            <thead>
                <tr class="header-principal">
                    <th colspan="7" class="titulo-principal">RECEITA LÍQUIDA REALIZADA</th>
                </tr>
                <tr class="header-anos">
                    <th rowspan="2" class="col-especificacao">ESPECIFICAÇÃO</th>
                    <th colspan="3" class="ano-header">${ano_atual}</th>
                    <th colspan="2" class="ano-header">${ano_anterior}</th>
                </tr>
                <tr class="header-colunas">
                    <th class="col-valor">PREVISÃO<br>ATUALIZADA</th>
                    <th class="col-valor">RECEITA<br>REALIZADA</th>
                    <th class="col-variacao">Δ%</th>
                    <th class="col-valor">RECEITA<br>REALIZADA</th>
                    <th class="col-variacao">Δ%</th>
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
                    <td class="col-valor">${formatarMoeda(linha.previsao_atual)}</td>
                    <td class="col-valor">${formatarMoeda(linha.realizada_atual)}</td>
                    <td class="col-variacao ${linha.variacao_previsto >= 0 ? 'positiva' : 'negativa'}">
                        ${formatarPercentual(linha.variacao_previsto)}
                    </td>
                    <td class="col-valor">${formatarMoeda(linha.realizada_anterior)}</td>
                    <td class="col-variacao ${linha.variacao_anual >= 0 ? 'positiva' : 'negativa'}">
                        ${formatarPercentual(linha.variacao_anual)}
                    </td>
                </tr>
            `;
            
            // Adicionar fontes
            if (linha.fontes && linha.fontes.length > 0) {
                linha.fontes.forEach(fonte => {
                    html += `
                        <tr class="linha-fonte">
                            <td class="col-especificacao">${fonte.nome}</td>
                            <td class="col-valor">${formatarMoeda(fonte.previsao_atual)}</td>
                            <td class="col-valor">${formatarMoeda(fonte.realizada_atual)}</td>
                            <td class="col-variacao ${fonte.variacao_previsto >= 0 ? 'positiva' : 'negativa'}">
                                ${formatarPercentual(fonte.variacao_previsto)}
                            </td>
                            <td class="col-valor">${formatarMoeda(fonte.realizada_anterior)}</td>
                            <td class="col-variacao ${fonte.variacao_anual >= 0 ? 'positiva' : 'negativa'}">
                                ${formatarPercentual(fonte.variacao_anual)}
                            </td>
                        </tr>
                    `;
                });
            }
        } else if (linha.tipo === 'total') {
            html += `
                <tr class="linha-total">
                    <td class="col-especificacao">${linha.nome}</td>
                    <td class="col-valor">${formatarMoeda(linha.previsao_atual)}</td>
                    <td class="col-valor">${formatarMoeda(linha.realizada_atual)}</td>
                    <td class="col-variacao ${linha.variacao_previsto >= 0 ? 'positiva' : 'negativa'}">
                        ${formatarPercentual(linha.variacao_previsto)}
                    </td>
                    <td class="col-valor">${formatarMoeda(linha.realizada_anterior)}</td>
                    <td class="col-variacao ${linha.variacao_anual >= 0 ? 'positiva' : 'negativa'}">
                        ${formatarPercentual(linha.variacao_anual)}
                    </td>
                </tr>
            `;
        }
    });
    
    html += `
            </tbody>
        </table>
        <div class="rodape-tabela">
            <p>Tabela 4 – Receita Líquida Realizada ${ano_atual} – Comparada com ${ano_anterior}</p>
            <p>Dados em: R$ 1,00</p>
            <p>Fonte: SIAC/SIGGO WEB</p>
            <p class="nota-explicativa">
                <strong>Nota:</strong> A primeira coluna Δ% representa a variação entre a Previsão Atualizada e a Receita Realizada de ${ano_atual}. 
                A segunda coluna Δ% representa a variação entre a Receita Realizada de ${ano_atual} e a Receita Realizada de ${ano_anterior}.
            </p>
        </div>
    `;
    
    return html;
}

/**
 * Baixa a imagem de receita realizada
 */
async function baixarImagemReceitaRealizada() {
    if (quadroAtual !== 'receita_realizada' || !dadosReceitaRealizada) {
        mostrarErro('Nenhum quadro de receita realizada para download');
        return;
    }
    
    mostrarAlerta('Gerando imagem em alta resolução...', 'info');
    
    // Criar container temporário
    const containerTemp = document.getElementById('imagemContainer');
    containerTemp.innerHTML = '';
    
    // Criar div com estilo específico para captura
    const divCaptura = document.createElement('div');
    divCaptura.style.width = '1400px'; // Mais largo para acomodar mais colunas
    divCaptura.style.padding = '40px';
    divCaptura.style.backgroundColor = 'white';
    divCaptura.style.fontFamily = 'Arial, sans-serif';
    
    // Adicionar o quadro com estilos inline
    divCaptura.innerHTML = gerarHTMLReceitaRealizadaParaImagem(dadosReceitaRealizada);
    containerTemp.appendChild(divCaptura);
    
    try {
        // Capturar com html2canvas
        const canvas = await html2canvas(divCaptura, {
            scale: 3, // Alta resolução
            useCORS: true,
            logging: false,
            backgroundColor: '#ffffff'
        });
        
        // Converter para blob e download
        canvas.toBlob(function(blob) {
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.download = `receita_liquida_realizada_${dadosReceitaRealizada.ano_atual}_${dadosReceitaRealizada.ano_anterior}.png`;
            link.href = url;
            link.click();
            URL.revokeObjectURL(url);
            
            mostrarAlerta('Imagem gerada com sucesso!', 'success');
        }, 'image/png', 1.0);
        
    } catch (error) {
        console.error('Erro ao gerar imagem:', error);
        mostrarErro('Erro ao gerar imagem: ' + error.message);
    } finally {
        // Limpar container
        containerTemp.innerHTML = '';
    }
}

/**
 * Gera HTML com estilos inline para captura de imagem
 */
function gerarHTMLReceitaRealizadaParaImagem(dados) {
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
                width: 35%;
            }
            .linha-categoria td {
                font-weight: bold;
                background-color: #e8f0ff;
            }
            .linha-categoria .col-especificacao {
                text-transform: uppercase;
            }
            .linha-fonte td {
                background-color: white;
            }
            .linha-fonte .col-especificacao {
                padding-left: 30px;
                font-size: 13px;
            }
            .linha-total td {
                font-weight: bold;
                background-color: #1e3c72;
                color: white;
            }
            .positiva { color: #28a745; }
            .negativa { color: #dc3545; }
            .linha-total .positiva,
            .linha-total .negativa {
                color: white;
            }
            .rodape-tabela {
                margin-top: 20px;
                font-size: 11px;
                color: #666;
                line-height: 1.4;
            }
            .nota-explicativa {
                margin-top: 10px;
                font-style: italic;
                border-top: 1px solid #ddd;
                padding-top: 5px;
            }
        </style>
        
        <table>
            <thead>
                <tr>
                    <th colspan="7" class="titulo-principal">RECEITA LÍQUIDA REALIZADA</th>
                </tr>
                <tr class="header-anos">
                    <th rowspan="2" class="col-especificacao">ESPECIFICAÇÃO</th>
                    <th colspan="3">${ano_atual}</th>
                    <th colspan="2">${ano_anterior}</th>
                </tr>
                <tr class="header-colunas">
                    <th>PREVISÃO<br>ATUALIZADA</th>
                    <th>RECEITA<br>REALIZADA</th>
                    <th>Δ%</th>
                    <th>RECEITA<br>REALIZADA</th>
                    <th>Δ%</th>
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
                    <td>${formatarMoeda(linha.previsao_atual)}</td>
                    <td>${formatarMoeda(linha.realizada_atual)}</td>
                    <td class="${linha.variacao_previsto >= 0 ? 'positiva' : 'negativa'}">
                        ${formatarPercentual(linha.variacao_previsto)}
                    </td>
                    <td>${formatarMoeda(linha.realizada_anterior)}</td>
                    <td class="${linha.variacao_anual >= 0 ? 'positiva' : 'negativa'}">
                        ${formatarPercentual(linha.variacao_anual)}
                    </td>
                </tr>
            `;
            
            if (linha.fontes) {
                linha.fontes.forEach(fonte => {
                    html += `
                        <tr class="linha-fonte">
                            <td class="col-especificacao">${fonte.nome}</td>
                            <td>${formatarMoeda(fonte.previsao_atual)}</td>
                            <td>${formatarMoeda(fonte.realizada_atual)}</td>
                            <td class="${fonte.variacao_previsto >= 0 ? 'positiva' : 'negativa'}">
                                ${formatarPercentual(fonte.variacao_previsto)}
                            </td>
                            <td>${formatarMoeda(fonte.realizada_anterior)}</td>
                            <td class="${fonte.variacao_anual >= 0 ? 'positiva' : 'negativa'}">
                                ${formatarPercentual(fonte.variacao_anual)}
                            </td>
                        </tr>
                    `;
                });
            }
        } else if (linha.tipo === 'total') {
            html += `
                <tr class="linha-total">
                    <td class="col-especificacao">${linha.nome}</td>
                    <td>${formatarMoeda(linha.previsao_atual)}</td>
                    <td>${formatarMoeda(linha.realizada_atual)}</td>
                    <td>${linha.variacao_previsto >= 0 ? '+' : ''}${formatarPercentual(linha.variacao_previsto)}</td>
                    <td>${formatarMoeda(linha.realizada_anterior)}</td>
                    <td>${linha.variacao_anual >= 0 ? '+' : ''}${formatarPercentual(linha.variacao_anual)}</td>
                </tr>
            `;
        }
    });
    
    html += `
            </tbody>
        </table>
        <div class="rodape-tabela">
            <p>Tabela 4 – Receita Líquida Realizada ${ano_atual} – Comparada com ${ano_anterior}</p>
            <p>Dados em: R$ 1,00</p>
            <p>Fonte: SIAC/SIGGO WEB</p>
            <p class="nota-explicativa">
                <strong>Nota:</strong> A primeira coluna Δ% representa a variação entre a Previsão Atualizada e a Receita Realizada de ${ano_atual}. 
                A segunda coluna Δ% representa a variação entre a Receita Realizada de ${ano_atual} e a Receita Realizada de ${ano_anterior}.
            </p>
        </div>
    `;
    
    return html;
}