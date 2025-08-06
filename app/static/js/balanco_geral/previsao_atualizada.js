/**
 * JavaScript específico para Previsão Atualizada
 * Parte do Balanço Geral GDF
 */

// Variável global já definida em balanco_geral.js
// let dadosPrevisaoAtualizada = null;

/**
 * Gera o quadro de previsão atualizada
 */
async function gerarPrevisaoAtualizada() {
    // Mostrar loading (função do balanco_geral.js)
    mostrarLoading();
    
    try {
        // Buscar dados da API
        const response = await fetch('/balanco-geral/api/dados-previsao-atualizada');
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.erro || 'Erro ao buscar dados');
        }
        
        // Armazenar dados na variável global
        dadosPrevisaoAtualizada = data;
        
        // Gerar HTML do quadro
        const quadroHTML = gerarHTMLPrevisaoAtualizada(data);
        
        // Mostrar preview (função do balanco_geral.js)
        mostrarPreview(quadroHTML);
        
        // Atualizar variável global
        quadroAtual = 'previsao_atualizada';
        
    } catch (error) {
        console.error('Erro ao gerar quadro de previsão atualizada:', error);
        mostrarErro('Erro ao gerar quadro: ' + error.message);
    }
}

/**
 * Gera o HTML do quadro de Previsão Atualizada
 */
function gerarHTMLPrevisaoAtualizada(dados) {
    const { ano, dados: linhas } = dados;
    
    let html = `
        <table class="tabela-previsao-atualizada">
            <thead>
                <tr class="header-principal">
                    <th colspan="4" class="titulo-principal">PREVISÃO ATUALIZADA</th>
                </tr>
                <tr class="header-colunas">
                    <th class="col-especificacao">ESPECIFICAÇÃO</th>
                    <th class="col-valor">PREVISÃO<br>INICIAL</th>
                    <th class="col-valor">PREVISÃO<br>ATUALIZADA</th>
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
                    <td class="col-valor">${formatarMoeda(linha.previsao_inicial)}</td>
                    <td class="col-valor">${formatarMoeda(linha.previsao_atualizada)}</td>
                    <td class="col-variacao ${linha.variacao >= 0 ? 'positiva' : 'negativa'}">
                        ${formatarPercentual(linha.variacao)}
                    </td>
                </tr>
            `;
            
            // Adicionar fontes
            if (linha.fontes && linha.fontes.length > 0) {
                linha.fontes.forEach(fonte => {
                    html += `
                        <tr class="linha-fonte">
                            <td class="col-especificacao">${fonte.nome}</td>
                            <td class="col-valor">${formatarMoeda(fonte.previsao_inicial)}</td>
                            <td class="col-valor">${formatarMoeda(fonte.previsao_atualizada)}</td>
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
                    <td class="col-valor">${formatarMoeda(linha.previsao_inicial)}</td>
                    <td class="col-valor">${formatarMoeda(linha.previsao_atualizada)}</td>
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
            <p>Tabela 3 – Previsão da Receita Atualizada ${ano}</p>
            <p>Dados em: R$ 1,00</p>
            <p>Fonte: SIAC/SIGGO WEB</p>
        </div>
    `;
    
    return html;
}

/**
 * Baixa a imagem de previsão atualizada
 */
async function baixarImagemPrevisaoAtualizada() {
    if (quadroAtual !== 'previsao_atualizada' || !dadosPrevisaoAtualizada) {
        mostrarErro('Nenhum quadro de previsão atualizada para download');
        return;
    }
    
    mostrarAlerta('Gerando imagem em alta resolução...', 'info');
    
    // Criar container temporário
    const containerTemp = document.getElementById('imagemContainer');
    containerTemp.innerHTML = '';
    
    // Criar div com estilo específico para captura
    const divCaptura = document.createElement('div');
    divCaptura.style.width = '1200px';
    divCaptura.style.padding = '40px';
    divCaptura.style.backgroundColor = 'white';
    divCaptura.style.fontFamily = 'Arial, sans-serif';
    
    // Adicionar o quadro com estilos inline
    divCaptura.innerHTML = gerarHTMLPrevisaoAtualizadaParaImagem(dadosPrevisaoAtualizada);
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
            link.download = `previsao_atualizada_${dadosPrevisaoAtualizada.ano}.png`;
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
function gerarHTMLPrevisaoAtualizadaParaImagem(dados) {
    const { ano, dados: linhas } = dados;
    
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
        </style>
        
        <table>
            <thead>
                <tr>
                    <th colspan="4" class="titulo-principal">PREVISÃO ATUALIZADA</th>
                </tr>
                <tr class="header-colunas">
                    <th class="col-especificacao">ESPECIFICAÇÃO</th>
                    <th>PREVISÃO<br>INICIAL</th>
                    <th>PREVISÃO<br>ATUALIZADA</th>
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
                    <td>${formatarMoeda(linha.previsao_inicial)}</td>
                    <td>${formatarMoeda(linha.previsao_atualizada)}</td>
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
                            <td>${formatarMoeda(fonte.previsao_inicial)}</td>
                            <td>${formatarMoeda(fonte.previsao_atualizada)}</td>
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
                    <td>${formatarMoeda(linha.previsao_inicial)}</td>
                    <td>${formatarMoeda(linha.previsao_atualizada)}</td>
                    <td>${linha.variacao >= 0 ? '+' : ''}${formatarPercentual(linha.variacao)}</td>
                </tr>
            `;
        }
    });
    
    html += `
            </tbody>
        </table>
        <div class="rodape-tabela">
            <p>Tabela 3 – Previsão da Receita Atualizada ${ano}</p>
            <p>Dados em: R$ 1,00</p>
            <p>Fonte: SIAC/SIGGO WEB</p>
        </div>
    `;
    
    return html;
}