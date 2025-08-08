// Módulo de Gerenciamento de Estado
// Arquivo: app/static/js/relatorio_receita_fonte/gerenciador_estado.js

window.GerenciadorEstado = {
    // ========================================
    // CHAVES DO LOCALSTORAGE
    // ========================================
    CHAVES: {
        FONTE_ALINEA: 'inconsistencias_fonte_alinea_resolvidas',
        ALINEA_UG: 'inconsistencias_alinea_ug_resolvidas'
    },
    
    // ========================================
    // CARREGAR ESTADO
    // ========================================
    carregar: function() {
        try {
            // Carregar estado das inconsistências Fonte/Alínea
            const estadoFonteAlinea = localStorage.getItem(this.CHAVES.FONTE_ALINEA);
            if (estadoFonteAlinea) {
                window.RelatorioReceitaFonte.inconsistenciasResolvidas['fonte-alinea'] = JSON.parse(estadoFonteAlinea);
                console.log('Estado Fonte/Alínea carregado:', 
                    Object.keys(window.RelatorioReceitaFonte.inconsistenciasResolvidas['fonte-alinea']).length, 
                    'itens marcados');
            }
            
            // Carregar estado das inconsistências Alínea/UG
            const estadoAlineaUG = localStorage.getItem(this.CHAVES.ALINEA_UG);
            if (estadoAlineaUG) {
                window.RelatorioReceitaFonte.inconsistenciasResolvidas['alinea-ug'] = JSON.parse(estadoAlineaUG);
                console.log('Estado Alínea/UG carregado:', 
                    Object.keys(window.RelatorioReceitaFonte.inconsistenciasResolvidas['alinea-ug']).length, 
                    'itens marcados');
            }
        } catch (e) {
            console.error('Erro ao carregar estado:', e);
            this.limpar();
        }
    },
    
    // ========================================
    // SALVAR ESTADO
    // ========================================
    salvar: function(tipo) {
        try {
            const chave = tipo === 'fonte-alinea' ? this.CHAVES.FONTE_ALINEA : this.CHAVES.ALINEA_UG;
            const dados = window.RelatorioReceitaFonte.inconsistenciasResolvidas[tipo];
            
            localStorage.setItem(chave, JSON.stringify(dados));
            console.log(`Estado ${tipo} salvo:`, Object.keys(dados).length, 'itens marcados');
        } catch (e) {
            console.error('Erro ao salvar estado:', e);
        }
    },
    
    // ========================================
    // MARCAR COMO RESOLVIDA
    // ========================================
    marcarResolvida: function(tipo, chaveDocumento, resolvida) {
        if (!window.RelatorioReceitaFonte.inconsistenciasResolvidas[tipo]) {
            window.RelatorioReceitaFonte.inconsistenciasResolvidas[tipo] = {};
        }
        
        if (resolvida) {
            window.RelatorioReceitaFonte.inconsistenciasResolvidas[tipo][chaveDocumento] = {
                dataResolucao: new Date().toISOString(),
                resolvida: true
            };
        } else {
            delete window.RelatorioReceitaFonte.inconsistenciasResolvidas[tipo][chaveDocumento];
        }
        
        this.salvar(tipo);
    },
    
    // ========================================
    // VERIFICAR SE ESTÁ RESOLVIDA
    // ========================================
    estaResolvida: function(tipo, chaveDocumento) {
        return window.RelatorioReceitaFonte.inconsistenciasResolvidas[tipo] &&
               window.RelatorioReceitaFonte.inconsistenciasResolvidas[tipo][chaveDocumento] ? true : false;
    },
    
    // ========================================
    // EXPORTAR ESTADO
    // ========================================
    exportar: function(tipo) {
        const estado = {
            tipo: tipo,
            inconsistenciasResolvidas: window.RelatorioReceitaFonte.inconsistenciasResolvidas[tipo],
            dataExportacao: new Date().toISOString(),
            totalMarcadas: Object.keys(window.RelatorioReceitaFonte.inconsistenciasResolvidas[tipo] || {}).length
        };
        
        const nomeArquivo = `estado_${tipo}_${Utilitarios.obterTimestamp()}.json`;
        const conteudo = JSON.stringify(estado, null, 2);
        
        Utilitarios.baixarArquivo(conteudo, nomeArquivo, 'application/json');
    },
    
    // ========================================
    // IMPORTAR ESTADO
    // ========================================
    importar: function(event, tipo) {
        const file = event.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const estado = JSON.parse(e.target.result);
                
                // Validar se o tipo corresponde
                if (estado.tipo && estado.tipo !== tipo) {
                    alert(`Arquivo incompatível! Este arquivo é do tipo "${estado.tipo}" mas você está tentando importar para "${tipo}".`);
                    return;
                }
                
                window.RelatorioReceitaFonte.inconsistenciasResolvidas[tipo] = estado.inconsistenciasResolvidas || {};
                GerenciadorEstado.salvar(tipo);
                
                alert(`Estado importado com sucesso! ${Object.keys(window.RelatorioReceitaFonte.inconsistenciasResolvidas[tipo]).length} itens marcados.`);
                
                // Recarregar a tabela se estiver aberta
                if ($('#modalInconsistencias').hasClass('show')) {
                    const tabAtiva = $('.tab-pane.active').attr('id');
                    if ((tipo === 'fonte-alinea' && tabAtiva === 'conteudo-fonte-alinea') ||
                        (tipo === 'alinea-ug' && tabAtiva === 'conteudo-alinea-ug')) {
                        Inconsistencias.construirTabela(tipo, window.RelatorioReceitaFonte.dadosInconsistencias[tipo]);
                    }
                }
            } catch (error) {
                alert('Erro ao importar arquivo: ' + error.message);
            }
        };
        reader.readAsText(file);
        
        // Limpar o input para permitir reimportar o mesmo arquivo
        event.target.value = '';
    },
    
    // ========================================
    // OBTER ESTATÍSTICAS
    // ========================================
    obterEstatisticas: function(tipo) {
        const resolvidas = window.RelatorioReceitaFonte.inconsistenciasResolvidas[tipo] || {};
        const total = window.RelatorioReceitaFonte.dadosInconsistencias[tipo].length;
        const totalResolvidas = Object.keys(resolvidas).length;
        
        return {
            total: total,
            resolvidas: totalResolvidas,
            naoResolvidas: total - totalResolvidas,
            percentualResolvido: total > 0 ? ((totalResolvidas / total) * 100).toFixed(1) : 0
        };
    },
    
    // ========================================
    // LIMPAR ESTADO
    // ========================================
    limpar: function(tipo) {
        if (tipo) {
            window.RelatorioReceitaFonte.inconsistenciasResolvidas[tipo] = {};
            const chave = tipo === 'fonte-alinea' ? this.CHAVES.FONTE_ALINEA : this.CHAVES.ALINEA_UG;
            localStorage.removeItem(chave);
        } else {
            // Limpar tudo
            window.RelatorioReceitaFonte.inconsistenciasResolvidas = {
                'fonte-alinea': {},
                'alinea-ug': {}
            };
            localStorage.removeItem(this.CHAVES.FONTE_ALINEA);
            localStorage.removeItem(this.CHAVES.ALINEA_UG);
        }
    },
    
    // ========================================
    // BACKUP COMPLETO
    // ========================================
    backupCompleto: function() {
        const backup = {
            versao: '1.0',
            dataBackup: new Date().toISOString(),
            inconsistencias: {
                'fonte-alinea': {
                    resolvidas: window.RelatorioReceitaFonte.inconsistenciasResolvidas['fonte-alinea'],
                    total: Object.keys(window.RelatorioReceitaFonte.inconsistenciasResolvidas['fonte-alinea'] || {}).length
                },
                'alinea-ug': {
                    resolvidas: window.RelatorioReceitaFonte.inconsistenciasResolvidas['alinea-ug'],
                    total: Object.keys(window.RelatorioReceitaFonte.inconsistenciasResolvidas['alinea-ug'] || {}).length
                }
            }
        };
        
        const nomeArquivo = `backup_completo_${Utilitarios.obterTimestamp()}.json`;
        const conteudo = JSON.stringify(backup, null, 2);
        
        Utilitarios.baixarArquivo(conteudo, nomeArquivo, 'application/json');
    },
    
    // ========================================
    // RESTAURAR BACKUP
    // ========================================
    restaurarBackup: function(arquivo) {
        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const backup = JSON.parse(e.target.result);
                
                if (!backup.versao || !backup.inconsistencias) {
                    throw new Error('Arquivo de backup inválido');
                }
                
                // Restaurar dados
                window.RelatorioReceitaFonte.inconsistenciasResolvidas['fonte-alinea'] = 
                    backup.inconsistencias['fonte-alinea'].resolvidas || {};
                window.RelatorioReceitaFonte.inconsistenciasResolvidas['alinea-ug'] = 
                    backup.inconsistencias['alinea-ug'].resolvidas || {};
                
                // Salvar no localStorage
                GerenciadorEstado.salvar('fonte-alinea');
                GerenciadorEstado.salvar('alinea-ug');
                
                alert('Backup restaurado com sucesso!');
                
                // Recarregar interface se necessário
                if ($('#modalInconsistencias').hasClass('show')) {
                    Inconsistencias.verificarTodas();
                }
            } catch (error) {
                alert('Erro ao restaurar backup: ' + error.message);
            }
        };
        reader.readAsText(arquivo);
    }
};