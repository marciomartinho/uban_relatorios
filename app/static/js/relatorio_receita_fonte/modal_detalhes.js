// Módulo de Modal de Detalhes
// Arquivo: app/static/js/relatorio_receita_fonte/modal_detalhes.js

window.ModalDetalhes = {
    // ========================================
    // ABRIR MODAL
    // ========================================
    abrir: function(cofonte, coalinea, nomeFonte, nomeAlinea) {
        // Limpar e mostrar loading
        $('#tabelaDetalhes tbody').html(
            '<tr><td colspan="7" class="text-center">' +
            '<div class="spinner-border spinner-border-sm"></div> Carregando...</td></tr>'
        );
        $('#alertaLimite').hide();
        
        // Configurar título
        const titulo = `Detalhes dos Lançamentos<br>
                       <small class="text-muted">
                       Fonte: ${cofonte} - ${nomeFonte || 'Sem descrição'}<br>
                       Alínea: ${coalinea} - ${nomeAlinea || 'Sem descrição'}
                       </small>`;
        $('#modalDetalhesLabel').html(titulo);
        
        // Mostrar modal
        $('#modalDetalhes').modal('show');
        
        // Buscar dados
        this.carregarDados(cofonte, coalinea);
    },
    
    // ========================================
    // CARREGAR DADOS
    // ========================================
    carregarDados: function(cofonte, coalinea) {
        const ano = $('#anoAtual').text();
        const coug = $('#filtroUG').val();
        
        const params = {
            cofonte: cofonte,
            coalinea: coalinea,
            ano: ano
        };
        
        if (coug) {
            params.coug = coug;
        }
        
        $.ajax({
            url: '/relatorio-receita-fonte/api/detalhes-lancamentos',
            method: 'GET',
            data: params,
            success: function(response) {
                console.log('✅ Detalhes carregados:', response);
                
                // Salvar dados completos
                window.RelatorioReceitaFonte.dadosLancamentosCompletos = response;
                
                // Atualizar resumo
                ModalDetalhes.atualizarResumo(response);
                
                // Mostrar alerta se limitado
                if (response.limitado) {
                    $('#alertaLimite').show();
                    $('#textoLimite').html(`
                        <i class="bi bi-info-circle"></i> 
                        Exibindo apenas os primeiros 1.000 registros de um total de ${response.total_registros.toLocaleString('pt-BR')}.
                        <br>Para obter todos os registros, use o botão "Exportar Excel" abaixo.
                    `);
                }
                
                // Construir tabela
                ModalDetalhes.construirTabela(response.dados);
            },
            error: function(xhr) {
                console.error('❌ Erro ao carregar detalhes:', xhr);
                
                let erro = xhr.responseJSON ? xhr.responseJSON.erro : 'Erro desconhecido';
                $('#tabelaDetalhes tbody').html(
                    '<tr><td colspan="7" class="text-center text-danger">' +
                    '<i class="bi bi-exclamation-triangle"></i> Erro ao carregar dados: ' + erro +
                    '</td></tr>'
                );
            }
        });
    },
    
    // ========================================
    // ATUALIZAR RESUMO
    // ========================================
    atualizarResumo: function(dados) {
        $('#resumoTotalDebito').text(Utilitarios.formatarMoeda(dados.total_debito));
        $('#resumoTotalCredito').text(Utilitarios.formatarMoeda(dados.total_credito));
        $('#resumoSaldo').text(Utilitarios.formatarMoeda(dados.saldo));
        $('#resumoTotalRegistros').text(dados.total_registros.toLocaleString('pt-BR'));
    },
    
    // ========================================
    // CONSTRUIR TABELA
    // ========================================
    construirTabela: function(dados) {
        if (!dados || dados.length === 0) {
            $('#tabelaDetalhes tbody').html(
                '<tr><td colspan="7" class="text-center text-muted">Nenhum lançamento encontrado.</td></tr>'
            );
            return;
        }
        
        let html = '';
        
        dados.forEach(function(item, index) {
            html += '<tr>';
            
            // Conta contábil
            html += '<td class="text-nowrap">' + item.cocontacontabil;
            if (item.nocontacontabil) {
                html += '<br><small class="text-muted">' + item.nocontacontabil + '</small>';
            }
            html += '</td>';
            
            // UG
            html += '<td class="text-nowrap">' + item.coug;
            if (item.noug) {
                html += '<br><small class="text-muted">' + item.noug + '</small>';
            }
            html += '</td>';
            
            // Documento
            html += '<td>' + item.nudocumento + '</td>';
            
            // Evento
            html += '<td class="text-nowrap">' + item.coevento;
            if (item.noevento) {
                html += '<br><small class="text-muted">' + item.noevento + '</small>';
            }
            html += '</td>';
            
            // Grupo
            html += '<td class="text-center">' + (item.cogrupo || '-') + '</td>';
            
            // D/C
            html += '<td class="text-center">';
            if (item.indebitocredito === 'D') {
                html += '<span class="badge bg-danger">D</span>';
            } else {
                html += '<span class="badge bg-success">C</span>';
            }
            html += '</td>';
            
            // Valor
            html += '<td class="text-end">' + Utilitarios.formatarMoeda(item.valancamento) + '</td>';
            
            html += '</tr>';
        });
        
        $('#tabelaDetalhes tbody').html(html);
    },
    
    // ========================================
    // FECHAR MODAL
    // ========================================
    fechar: function() {
        $('#modalDetalhes').modal('hide');
        
        // Limpar dados
        window.RelatorioReceitaFonte.dadosLancamentosCompletos = [];
        $('#tabelaDetalhes tbody').empty();
        $('#resumoTotalDebito').text('R$ 0,00');
        $('#resumoTotalCredito').text('R$ 0,00');
        $('#resumoSaldo').text('R$ 0,00');
        $('#resumoTotalRegistros').text('0');
    }
};