/**
 * JavaScript específico para Receita Estimada Líquida por Tipo de Administração
 * Parte do Balanço Geral GDF
 * Arquivo: app/static/js/balanco_geral/receita_tipo_administracao.js
 */

// NÃO declarar variáveis aqui - elas já estão em balanco_geral.js
// let dadosReceitaTipoAdm = null; // REMOVIDO

/**
 * Gera o quadro de receita por tipo de administração
 */
async function gerarReceitaTipoAdministracao() {
    // Mostrar loading (função do balanco_geral.js)
    mostrarLoading();
    
    try {
        // Buscar dados da API
        const response = await fetch('/balanco-geral/api/dados-receita-tipo-administracao');
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.erro || 'Erro ao buscar dados');
        }
        
        // Armazenar dados
        dadosReceitaTipoAdm = data;
        
        // Gerar HTML do quadro
        const quadroHTML = gerarHTMLReceitaTipoAdm(data);
        
        // Mostrar preview (função do balanco_geral.js)
        mostrarPreview(quadroHTML);
        
        // Atualizar variável global do quadro atual
        quadroAtual = 'receita_tipo_administracao';
        
    } catch (error) {
        console.error('Erro ao gerar quadro de receita por tipo de administração:', error);
        mostrarErro('Erro ao gerar quadro: ' + error.message);
    }
}

/**
 * Gera o HTML do quadro de Receita por Tipo de Administração
 */
function gerarHTMLReceitaTipoAdm(dados) {
    const { ano, colunas, dados: linhas } = dados;
    
    let html = `
        <table class="tabela-receita-tipo-adm">
            <thead>
                <tr class="header-principal">
                    <th colspan="${colunas.length + 1}" class="titulo-principal">
                        RECEITA ESTIMADA LÍQUIDA
                    </th>
                </tr>
                <tr class="header-colunas">
                    <th class="col-especificacao">ESPECIFICAÇÃO</th>
    `;
    
    // Adicionar colunas de tipo de administração
    colunas.forEach(col => {
        html += `<th class="col-tipo-adm">${col.nome}</th>`;
    });
    
    html += `
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
            `;
            
            // Adicionar valores por tipo de administração
            colunas.forEach(col => {
                const valor = linha.valores_tipo_adm[col.codigo] || 0;
                html += `<td class="col-valor">${formatarMoeda(valor)}</td>`;
            });
            
            html += `</tr>`;
            
            // Adicionar fontes
            if (linha.fontes) {
                linha.fontes.forEach(fonte => {
                    html += `
                        <tr class="linha-fonte">
                            <td class="col-especificacao">${fonte.nome}</td>
                    `;
                    
                    // Valores da fonte por tipo de administração
                    colunas.forEach(col => {
                        const valor = fonte.valores_tipo_adm[col.codigo] || 0;
                        html += `<td class="col-valor">${formatarMoeda(valor)}</td>`;
                    });
                    
                    html += `</tr>`;
                });
            }
        } else if (linha.tipo === 'total') {
            html += `
                <tr class="linha-total">
                    <td class="col-especificacao">${linha.nome}</td>
            `;
            
            // Valores totais por tipo de administração
            colunas.forEach(col => {
                const valor = linha.valores_tipo_adm[col.codigo] || 0;
                html += `<td class="col-valor">${formatarMoeda(valor)}</td>`;
            });
            
            html += `</tr>`;
        }
    });
    
    html += `
            </tbody>
        </table>
        <div class="rodape-tabela">
            <p>Tabela 2 – Receita Líquida Estimada ${ano} – Por Tipo de Administração</p>
            <p>Dados em: R$ 1,00</p>
            <p>Fonte: SIAC/SIGGO WEB</p>
        </div>
    `;
    
    return html;
}

/**
 * Baixa a imagem de receita por tipo de administração
 */
async function baixarImagemTipoAdm() {
    // Verifica qual quadro está ativo
    if (quadroAtual !== 'receita_tipo_administracao' || !dadosReceitaTipoAdm) {
        mostrarErro('Nenhum quadro de receita por tipo de administração para download');
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
    divCaptura.innerHTML = gerarHTMLTipoAdmParaImagem(dadosReceitaTipoAdm);
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
            link.download = `receita_estimada_tipo_administracao_${dadosReceitaTipoAdm.ano}.png`;
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
function gerarHTMLTipoAdmParaImagem(dados) {
    const { ano, colunas, dados: linhas } = dados;
    
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
                width: 30%;
            }
            .col-tipo-adm {
                width: auto;
                text-align: center !important;
            }
            .linha-categoria td {
                font-weight: bold;
                background-color: #e8f0ff;
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
                    <th colspan="${colunas.length + 1}" class="titulo-principal">
                        RECEITA ESTIMADA LÍQUIDA
                    </th>
                </tr>
                <tr class="header-colunas">
                    <th class="col-especificacao">ESPECIFICAÇÃO</th>
    `;
    
    // Adicionar colunas
    colunas.forEach(col => {
        html += `<th class="col-tipo-adm">${col.nome}</th>`;
    });
    
    html += `
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
            `;
            
            colunas.forEach(col => {
                const valor = linha.valores_tipo_adm[col.codigo] || 0;
                html += `<td>${formatarMoeda(valor)}</td>`;
            });
            
            html += `</tr>`;
            
            if (linha.fontes) {
                linha.fontes.forEach(fonte => {
                    html += `
                        <tr class="linha-fonte">
                            <td class="col-especificacao">${fonte.nome}</td>
                    `;
                    
                    colunas.forEach(col => {
                        const valor = fonte.valores_tipo_adm[col.codigo] || 0;
                        html += `<td>${formatarMoeda(valor)}</td>`;
                    });
                    
                    html += `</tr>`;
                });
            }
        } else if (linha.tipo === 'total') {
            html += `
                <tr class="linha-total">
                    <td class="col-especificacao">${linha.nome}</td>
            `;
            
            colunas.forEach(col => {
                const valor = linha.valores_tipo_adm[col.codigo] || 0;
                html += `<td>${formatarMoeda(valor)}</td>`;
            });
            
            html += `</tr>`;
        }
    });
    
    html += `
            </tbody>
        </table>
        <div class="rodape-tabela">
            <p>Tabela 2 – Receita Líquida Estimada ${ano} – Por Tipo de Administração</p>
            <p>Dados em: R$ 1,00</p>
            <p>Fonte: SIAC/SIGGO WEB</p>
        </div>
    `;
    
    return html;
}