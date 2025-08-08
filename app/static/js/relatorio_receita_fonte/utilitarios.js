// Módulo de Funções Utilitárias
// Arquivo: app/static/js/relatorio_receita_fonte/utilitarios.js

window.Utilitarios = {
    // ========================================
    // FORMATAÇÃO
    // ========================================
    formatarMoeda: function(valor) {
        if (valor === null || valor === undefined) return 'R$ 0,00';
        
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(valor);
    },
    
    formatarCodigoDescricao: function(codigo, descricao) {
        const tipo = $('#tipoExibicao').val();
        const maxLength = 50;
        
        let descricaoTruncada = descricao || 'Sem descrição';
        if (descricaoTruncada.length > maxLength) {
            descricaoTruncada = descricaoTruncada.substring(0, maxLength) + '...';
        }
        
        if (tipo === 'codigo') {
            return codigo;
        } else if (tipo === 'descricao') {
            return `<span title="${descricao || codigo}">${descricaoTruncada}</span>`;
        } else {
            return `<span title="${descricao || ''}">${codigo} - ${descricaoTruncada}</span>`;
        }
    },
    
    formatarParaExport: function(codigo, descricao, tipo) {
        if (tipo === 'codigo') {
            return codigo;
        } else if (tipo === 'descricao') {
            return descricao || codigo;
        } else {
            return codigo + ' - ' + (descricao || 'Sem descrição');
        }
    },
    
    formatarVariacaoPercentual: function(valor) {
        const sinal = valor > 0 ? '↑' : valor < 0 ? '↓' : '→';
        return sinal + ' ' + Math.abs(valor).toFixed(2) + '%';
    },
    
    // ========================================
    // CLASSES CSS
    // ========================================
    getClasseVariacao: function(valor) {
        if (valor > 0) return 'text-success';
        if (valor < 0) return 'text-danger';
        return 'text-muted';
    },
    
    // ========================================
    // ALERTAS
    // ========================================
    mostrarAlerta: function(tipo, mensagem, container) {
        const alertHtml = `
            <div class="alert alert-${tipo} alert-dismissible fade show" role="alert">
                ${mensagem}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        const target = container || '#modalInconsistencias .modal-body';
        $(target).prepend(alertHtml);
        
        setTimeout(() => {
            $('.alert').fadeOut(() => $('.alert').remove());
        }, 5000);
    },
    
    // ========================================
    // INDICADORES DE CARREGAMENTO
    // ========================================
    mostrarCarregando: function(elemento) {
        $(elemento).html(`
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Carregando...</span>
                </div>
            </div>
        `);
    },
    
    // ========================================
    // VALIDAÇÃO
    // ========================================
    validarDados: function(dados) {
        return dados && Array.isArray(dados) && dados.length > 0;
    },
    
    // ========================================
    // CONVERSÃO CSV
    // ========================================
    converterParaCSV: function(dados, headers) {
        let csv = [];
        
        // Adicionar headers
        if (headers) {
            csv.push(headers.join(';'));
        }
        
        // Adicionar dados
        dados.forEach(function(linha) {
            csv.push(linha.join(';'));
        });
        
        return '\ufeff' + csv.join('\n');
    },
    
    // ========================================
    // DOWNLOAD
    // ========================================
    baixarArquivo: function(conteudo, nomeArquivo, tipo = 'text/csv;charset=utf-8;') {
        const blob = new Blob([conteudo], { type: tipo });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        
        link.setAttribute('href', url);
        link.setAttribute('download', nomeArquivo);
        link.style.visibility = 'hidden';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        console.log('✅ Download concluído:', nomeArquivo);
    },
    
    // ========================================
    // DATAS
    // ========================================
    formatarData: function(data) {
        if (!data) return '';
        
        if (typeof data === 'string') {
            data = new Date(data);
        }
        
        return data.toLocaleDateString('pt-BR');
    },
    
    obterTimestamp: function() {
        return new Date().getTime();
    },
    
    // ========================================
    // NÚMEROS
    // ========================================
    formatarNumero: function(numero) {
        return numero.toLocaleString('pt-BR');
    },
    
    calcularPercentual: function(valor, total) {
        if (total === 0) return 0;
        return ((valor / total) * 100).toFixed(2);
    },
    
    // ========================================
    // STRINGS
    // ========================================
    truncarTexto: function(texto, tamanho = 50) {
        if (!texto) return '';
        if (texto.length <= tamanho) return texto;
        return texto.substring(0, tamanho) + '...';
    },
    
    limparTexto: function(texto) {
        if (!texto) return '';
        return texto.trim().replace(/\s+/g, ' ');
    },
    
    // ========================================
    // OBJETOS
    // ========================================
    clonarObjeto: function(obj) {
        return JSON.parse(JSON.stringify(obj));
    },
    
    mesclarObjetos: function(obj1, obj2) {
        return Object.assign({}, obj1, obj2);
    },
    
    // ========================================
    // ARRAYS
    // ========================================
    ordenarPor: function(array, campo, descendente = false) {
        return array.sort(function(a, b) {
            if (descendente) {
                return b[campo] - a[campo];
            }
            return a[campo] - b[campo];
        });
    },
    
    agruparPor: function(array, campo) {
        return array.reduce(function(grupos, item) {
            const chave = item[campo];
            if (!grupos[chave]) {
                grupos[chave] = [];
            }
            grupos[chave].push(item);
            return grupos;
        }, {});
    },
    
    // ========================================
    // FILTROS
    // ========================================
    aplicarFiltros: function(dados, filtros) {
        let resultado = dados;
        
        Object.keys(filtros).forEach(function(campo) {
            const valor = filtros[campo];
            if (valor) {
                resultado = resultado.filter(function(item) {
                    return item[campo] === valor;
                });
            }
        });
        
        return resultado;
    },
    
    // ========================================
    // VALIDAÇÃO DE FORMULÁRIOS
    // ========================================
    validarCampo: function(campo, tipo) {
        const valor = $(campo).val();
        
        switch (tipo) {
            case 'obrigatorio':
                return valor && valor.trim() !== '';
            case 'numero':
                return !isNaN(valor) && valor !== '';
            case 'email':
                return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valor);
            default:
                return true;
        }
    },
    
    // ========================================
    // DEBOUNCE
    // ========================================
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};