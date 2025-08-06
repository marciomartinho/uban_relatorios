/**
 * JavaScript principal para Balanço Geral GDF
 * Gerencia a página principal e coordena os módulos
 */

// Variáveis globais
let quadroAtual = null;
let dadosReceitaEstimada = null;
let dadosReceitaTipoAdm = null;

/**
 * Função para chamar o gerador de cada quadro
 */
function gerarQuadroReceita() {
    // Chama a função do arquivo receita_estimada.js
    if (typeof gerarReceitaEstimada === 'function') {
        quadroAtual = 'receita_estimada';
        gerarReceitaEstimada();
    } else {
        mostrarErro('Módulo de Receita Estimada não carregado');
    }
}

function gerarQuadroReceitaTipoAdm() {
    // Chama a função do arquivo receita_tipo_administracao.js
    if (typeof gerarReceitaTipoAdministracao === 'function') {
        quadroAtual = 'receita_tipo_administracao';
        gerarReceitaTipoAdministracao();
    } else {
        mostrarErro('Módulo de Receita por Tipo de Administração não carregado');
    }
}

// Futuros quadros serão adicionados aqui:
// function gerarQuadroDespesa() { ... }
// function gerarQuadroResultado() { ... }

/**
 * Fecha o preview (usado por todos os quadros)
 */
function fecharPreview() {
    $('#previewContainer').hide();
    quadroAtual = null;
}

/**
 * Mostra container de preview
 */
function mostrarPreview(html) {
    $('#quadroPreview').html(html);
    $('#loadingContainer').hide();
    $('#previewContainer').show();
    
    // Scroll suave até o preview
    $('html, body').animate({
        scrollTop: $('#previewContainer').offset().top - 100
    }, 500);
}

/**
 * Mostra loading
 */
function mostrarLoading() {
    $('#loadingContainer').show();
    $('#previewContainer').hide();
}

/**
 * Esconde loading
 */
function esconderLoading() {
    $('#loadingContainer').hide();
}

/**
 * Mostra mensagem de erro
 */
function mostrarErro(mensagem) {
    const alertHtml = `
        <div class="alert alert-danger alert-dismissible fade show" role="alert">
            <i class="bi bi-exclamation-triangle"></i> ${mensagem}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    $('.container-fluid').prepend(alertHtml);
    esconderLoading();
}

/**
 * Mostra mensagem de alerta
 */
function mostrarAlerta(mensagem, tipo = 'info') {
    const alertHtml = `
        <div class="alert alert-${tipo} alert-dismissible fade show" role="alert">
            ${mensagem}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    $('.container-fluid').prepend(alertHtml);
    
    // Auto-remover após 3 segundos
    setTimeout(() => {
        $('.alert').fadeOut(() => {
            $('.alert').remove();
        });
    }, 3000);
}

/**
 * Formata valor monetário (usado por todos os quadros)
 */
function formatarMoeda(valor) {
    return new Intl.NumberFormat('pt-BR', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(valor || 0);
}

/**
 * Formata percentual (usado por todos os quadros)
 */
function formatarPercentual(valor) {
    return (valor || 0).toFixed(2).replace('.', ',') + '%';
}

/**
 * Baixa a imagem do quadro ativo
 */
async function baixarImagem() {
    // Verifica qual quadro está ativo e chama a função apropriada
    if (quadroAtual === 'receita_estimada' && dadosReceitaEstimada) {
        await baixarImagemReceitaEstimada();
    } else if (quadroAtual === 'receita_tipo_administracao' && dadosReceitaTipoAdm) {
        await baixarImagemTipoAdm();
    } else {
        mostrarErro('Nenhum quadro disponível para download');
    }
}

/**
 * Função específica para baixar receita estimada
 */
async function baixarImagemReceitaEstimada() {
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
    divCaptura.innerHTML = gerarHTMLReceitaEstimadaParaImagem(dadosReceitaEstimada);
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
            link.download = `receita_estimada_liquida_${dadosReceitaEstimada.ano_atual}_${dadosReceitaEstimada.ano_anterior}.png`;
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