// Módulo de Inconsistências
// Arquivo: app/static/js/relatorio_receita_fonte/inconsistencias.js

window.Inconsistencias = {
    // ========================================
    // VERIFICAR TODAS
    // ========================================
    verificarTodas: function() {
        console.log('Verificando todas as inconsistências...');
        
        // Mostrar loading
        $('.loading-inconsistencias').show();
        
        // Verificar ambas as regras
        this.verificar('fonte-alinea');
        this.verificar('alinea-ug');
    },
    
    // ========================================
    // VERIFICAR POR TIPO
    // ========================================
    verificar: function(tipo) {
        console.log(`Verificando inconsistências ${tipo}...`);
        
        // Determinar endpoint
        const endpoint = tipo === 'fonte-alinea' 
            ? '/relatorio-receita-fonte/api/verificar-inconsistencias-fonte-alinea'
            : '/relatorio-receita-fonte/api/verificar-inconsistencias-alinea-ug';
        
        // Atualizar status
        $(`.status-verificacao[data-tipo="${tipo}"]`).html(
            '<span class="badge bg-info">Verificando...</span>'
        );
        
        $.ajax({
            url: endpoint,
            method: 'GET',
            data: { exportar: 'true' },
            success: function(response) {
                console.log(`✅ Inconsistências ${tipo} verificadas:`, response);
                
                // Salvar dados
                window.RelatorioReceitaFonte.dadosInconsistencias[tipo] = response.documentos;
                window.RelatorioReceitaFonte.ultimaVerificacao = new Date();
                
                // Atualizar interface
                Inconsistencias.atualizarInterface(tipo, response);
                
                // Construir tabela
                Inconsistencias.construirTabela(tipo, response.documentos);
                
                // Atualizar texto de última verificação
                $('#textoUltimaVerificacao').text(
                    'Última verificação: ' + window.RelatorioReceitaFonte.ultimaVerificacao.toLocaleString('pt-BR')
                );
                
                $('.loading-inconsistencias').hide();
            },
            error: function(xhr) {
                console.error(`❌ Erro ao verificar ${tipo}:`, xhr);
                
                $('.loading-inconsistencias').hide();
                $(`.status-verificacao[data-tipo="${tipo}"]`).html(
                    '<span class="badge bg-danger">Erro na verificação</span>'
                );
                
                Utilitarios.mostrarAlerta('danger', 
                    `Erro ao verificar inconsistências ${tipo}: ` + (xhr.responseJSON?.erro || 'Erro desconhecido')
                );
            }
        });
    },
    
    // ========================================
    // ATUALIZAR INTERFACE
    // ========================================
    atualizarInterface: function(tipo, response) {
        // Atualizar cards
        $(`.total-documentos[data-tipo="${tipo}"]`).text(
            response.totais.total_documentos.toLocaleString('pt-BR')
        );
        
        if (tipo === 'fonte-alinea') {
            $(`.total-combinacoes[data-tipo="${tipo}"]`).text(response.totais.total_combinacoes);
        } else {
            // Para alínea-ug, mostrar UGs divergentes
            $(`.total-combinacoes[data-tipo="${tipo}"]`).text(response.totais.total_combinacoes);
        }
        
        $(`.valor-total[data-tipo="${tipo}"]`).text(
            Utilitarios.formatarMoeda(response.totais.valor_total)
        );
        
        // Atualizar badge na tab
        const badge = tipo === 'fonte-alinea' ? '#badgeFonteAlinea' : '#badgeAlineaUG';
        $(badge).text(response.totais.total_documentos);
        
        // Atualizar status
        if (response.totais.total_documentos === 0) {
            $(`.status-verificacao[data-tipo="${tipo}"]`).html(
                '<span class="badge bg-success">✓ Nenhuma inconsistência</span>'
            );
        } else {
            $(`.status-verificacao[data-tipo="${tipo}"]`).html(
                '<span class="badge bg-danger">⚠ ' + response.totais.total_documentos + ' documentos</span>'
            );
        }
    },
    
    // ========================================
    // CONSTRUIR TABELA
    // ========================================
    construirTabela: function(tipo, dados) {
        const tbody = $(`.tabela-inconsistencias[data-tipo="${tipo}"] tbody`);
        tbody.empty();
        
        if (!dados || dados.length === 0) {
            tbody.html(`
                <tr>
                    <td colspan="10" class="text-center text-success">
                        <i class="bi bi-check-circle"></i> Nenhuma inconsistência encontrada
                    </td>
                </tr>
            `);
            return;
        }
        
        // Ordenar dados
        dados.sort(function(a, b) {
            if (a.coevento && b.coevento) {
                if (a.coevento < b.coevento) return -1;
                if (a.coevento > b.coevento) return 1;
            }
            if (a.nudocumento < b.nudocumento) return -1;
            if (a.nudocumento > b.nudocumento) return 1;
            return 0;
        });
        
        // Construir linhas
        dados.forEach(function(item, index) {
            const chaveDoc = `${item.nudocumento}_${item.cofonte}_${item.coalinea}`;
            const isResolvida = GerenciadorEstado.estaResolvida(tipo, chaveDoc);
            
            // Determinar cor baseado no valor
            let classeSeveridade = '';
            const valor = Math.abs(item.valancamento);
            if (valor > 100000) {
                classeSeveridade = 'table-warning';
            }
            
            const row = $('<tr>')
                .addClass(classeSeveridade)
                .addClass(isResolvida ? 'linha-resolvida' : '')
                .attr('data-documento', chaveDoc)
                .attr('data-resolvida', isResolvida);
            
            let html = '';
            
            // Colunas comuns
            html += `<td><strong>${item.nudocumento}</strong></td>`;
            html += `<td>${item.cougcontab}`;
            if (tipo === 'fonte-alinea' && item.noug) {
                html += `<br><small class="text-muted">${item.noug}</small>`;
            } else if (tipo === 'alinea-ug' && item.noug_contabil) {
                html += `<br><small class="text-muted">${item.noug_contabil}</small>`;
            }
            html += `</td>`;
            
            // Coluna específica para alínea-ug (UG Emitente)
            if (tipo === 'alinea-ug') {
                html += `<td>${item.coug}`;
                if (item.noug_emitente) {
                    html += `<br><small class="text-muted">${item.noug_emitente}</small>`;
                }
                html += `</td>`;
            }
            
            // Restante das colunas
            html += `<td>${item.coevento || ''}`;
            if (item.noevento) {
                html += `<br><small class="text-muted">${Utilitarios.truncarTexto(item.noevento, 20)}</small>`;
            }
            html += `</td>`;
            
            html += `<td>${item.cofonte}`;
            if (item.nofonte) {
                html += `<br><small class="text-muted">${Utilitarios.truncarTexto(item.nofonte, 20)}</small>`;
            }
            html += `</td>`;
            
            html += `<td>${item.coalinea}`;
            if (item.noalinea) {
                html += `<br><small class="text-muted">${Utilitarios.truncarTexto(item.noalinea, 20)}</small>`;
            }
            html += `</td>`;
            
            html += `<td>${item.dalancamento ? Utilitarios.formatarData(item.dalancamento) : ''}</td>`;
            
            html += `<td class="text-center">
                <span class="badge ${item.indebitocredito === 'D' ? 'bg-danger' : 'bg-success'}">
                    ${item.indebitocredito}
                </span>
            </td>`;
            
            html += `<td class="text-end">
                <strong class="${item.indebitocredito === 'D' ? 'text-danger' : 'text-success'}">
                    ${item.indebitocredito === 'D' ? '-' : '+'} ${Utilitarios.formatarMoeda(Math.abs(item.valancamento))}
                </strong>
            </td>`;
            
            // Ação - apenas para fonte-alinea
            if (tipo === 'fonte-alinea') {
                html += `<td class="text-center">
                    <button class="btn btn-sm btn-outline-primary" 
                            onclick="verDetalhesInconsistencia('${item.cofonte}', '${item.coalinea}', '${tipo}')"
                            title="Ver todos desta combinação">
                        <i class="bi bi-search"></i>
                    </button>
                </td>`;
            }
            
            // Checkbox
            html += `<td class="text-center">
                <input type="checkbox" 
                       class="checkbox-resolvido" 
                       data-documento="${chaveDoc}"
                       ${isResolvida ? 'checked' : ''}
                       title="${isResolvida ? 'Marcado como resolvido' : 'Marcar como resolvido'}">
            </td>`;
            
            row.html(html);
            tbody.append(row);
        });
        
        // Aplicar filtro e atualizar contagem
        this.aplicarFiltro(tipo);
        this.atualizarContagem(tipo);
    },
    
    // ========================================
    // APLICAR FILTRO
    // ========================================
    aplicarFiltro: function(tipo) {
        const filtro = $(`.filtro-status[data-tipo="${tipo}"]`).val();
        let visiveis = 0;
        
        $(`.tabela-inconsistencias[data-tipo="${tipo}"] tbody tr`).each(function() {
            const isResolvida = $(this).attr('data-resolvida') === 'true';
            
            if (filtro === 'todas') {
                $(this).show();
                visiveis++;
            } else if (filtro === 'resolvidas' && isResolvida) {
                $(this).show();
                visiveis++;
            } else if (filtro === 'nao_resolvidas' && !isResolvida) {
                $(this).show();
                visiveis++;
            } else {
                $(this).hide();
            }
        });
        
        $(`.contador-registros[data-tipo="${tipo}"]`).text(visiveis);
    },
    
    // ========================================
    // ATUALIZAR CONTAGEM
    // ========================================
    atualizarContagem: function(tipo) {
        const stats = GerenciadorEstado.obterEstatisticas(tipo);
        
        $(`.badge-resolvidas[data-tipo="${tipo}"]`).text(stats.resolvidas + ' resolvidas');
        $(`.badge-nao-resolvidas[data-tipo="${tipo}"]`).text(stats.naoResolvidas + ' não resolvidas');
    },
    
    // ========================================
    // MARCAR TODOS
    // ========================================
    marcarTodos: function(tipo, isChecked) {
        const filtroAtual = $(`.filtro-status[data-tipo="${tipo}"]`).val();
        
        $(`.tabela-inconsistencias[data-tipo="${tipo}"] tbody tr:visible`).each(function() {
            const checkbox = $(this).find('.checkbox-resolvido');
            const chaveDoc = checkbox.data('documento');
            
            if (filtroAtual === 'todas' || 
                (filtroAtual === 'resolvidas' && GerenciadorEstado.estaResolvida(tipo, chaveDoc)) ||
                (filtroAtual === 'nao_resolvidas' && !GerenciadorEstado.estaResolvida(tipo, chaveDoc))) {
                
                checkbox.prop('checked', isChecked);
                GerenciadorEstado.marcarResolvida(tipo, chaveDoc, isChecked);
                
                if (isChecked) {
                    $(this).addClass('linha-resolvida');
                } else {
                    $(this).removeClass('linha-resolvida');
                }
            }
        });
        
        this.atualizarContagem(tipo);
    }
};