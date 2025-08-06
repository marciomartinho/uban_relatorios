/**
 * Módulo de Exportação
 * Gerencia exportação para Excel, imagem e outros formatos
 */

class ExportadorBalancoReceita {
    constructor() {
        this.config = window.ConfiguracoesBalancoReceita;
        this.formatadores = window.FormatadoresBalancoReceita;
        this.renderizador = window.RenderizadorBalancoReceita;
    }
    
    /**
     * Exporta relatório para Excel
     * @param {Object} dadosRelatorio - Dados do relatório
     */
    exportarExcel(dadosRelatorio) {
        if (!dadosRelatorio) {
            this.renderizador.mostrarAlerta('Nenhum relatório para exportar!', 'warning');
            return;
        }
        
        console.log('📊 Exportando para Excel...');
        
        const workbook = XLSX.utils.book_new();
        const wsData = this._prepararDadosExcel(dadosRelatorio);
        const worksheet = XLSX.utils.aoa_to_sheet(wsData);
        
        // Configurar larguras das colunas
        worksheet['!cols'] = this.config.EXPORTACAO.EXCEL.LARGURAS_COLUNAS.map(w => ({ wch: w }));
        
        // Adicionar worksheet ao workbook
        XLSX.utils.book_append_sheet(workbook, worksheet, this.config.EXPORTACAO.EXCEL.NOME_ABA);
        
        // Gerar arquivo
        const filename = `balanco_receita_${dadosRelatorio.periodo.ano}_${dadosRelatorio.periodo.mes}.xlsx`;
        XLSX.writeFile(workbook, filename);
        
        this.renderizador.mostrarAlerta('Arquivo Excel gerado com sucesso!', 'success');
    }
    
    /**
     * Prepara dados para exportação Excel
     * @private
     */
    _prepararDadosExcel(dadosRelatorio) {
        const wsData = [
            // Cabeçalho
            ['BALANÇO ORÇAMENTÁRIO DA RECEITA'],
            [`${dadosRelatorio.periodo.nome_mes}/${dadosRelatorio.periodo.ano}`],
            [`UG: ${dadosRelatorio.filtros.nome_coug}`],
            [],
            // Cabeçalhos da tabela
            [
                'RECEITAS',
                `PREVISÃO INICIAL ${dadosRelatorio.periodo.ano}`,
                `PREVISÃO ATUALIZADA ${dadosRelatorio.periodo.ano}`,
                `REALIZADA ${dadosRelatorio.periodo.mes}/${dadosRelatorio.periodo.ano}`,
                `REALIZADA ${dadosRelatorio.periodo.mes}/${dadosRelatorio.periodo.ano_anterior}`,
                'VARIAÇÃO ABSOLUTA',
                'VARIAÇÃO %'
            ]
        ];
        
        // Dados do relatório
        dadosRelatorio.dados.forEach(item => {
            const descricao = this.formatadores.formatarDescricaoHierarquica(item);
            
            wsData.push([
                descricao,
                item.previsao_inicial,
                item.previsao_atualizada,
                item.receita_atual,
                item.receita_anterior,
                item.variacao_absoluta,
                item.variacao_percentual / 100
            ]);
        });
        
        // Total
        wsData.push([
            'TOTAL GERAL',
            dadosRelatorio.totais.previsao_inicial,
            dadosRelatorio.totais.previsao_atualizada,
            dadosRelatorio.totais.receita_atual,
            dadosRelatorio.totais.receita_anterior,
            dadosRelatorio.totais.variacao_absoluta,
            dadosRelatorio.totais.variacao_percentual / 100
        ]);
        
        return wsData;
    }
    
    /**
     * Exporta relatório completo com todos os módulos
     */
    async exportarRelatorioCompleto() {
        try {
            this.renderizador.mostrarAlerta('Preparando exportação completa...', 'info');
            
            const wb = XLSX.utils.book_new();
            
            // 1. Adicionar dados do relatório principal
            if (window.ultimoRelatorioGerado) {
                const dadosPrincipais = this._prepararDadosExportacaoCompleta(window.ultimoRelatorioGerado);
                const wsPrincipal = XLSX.utils.json_to_sheet(dadosPrincipais);
                XLSX.utils.book_append_sheet(wb, wsPrincipal, 'Balanço Orçamentário');
            }
            
            // 2. Adicionar dados do comparativo mensal se disponível
            if (typeof comparativoMensal !== 'undefined' && comparativoMensal.dadosOriginais) {
                const dadosComparativo = comparativoMensal.dadosOriginais.dados_brutos.map(item => ({
                    'Mês': item.nome_mes,
                    [`Receita ${item.ano_anterior}`]: item.receita_anterior,
                    [`Receita ${item.ano_atual}`]: item.receita_atual,
                    'Variação R: item.variacao_absoluta,
                    'Variação %': item.variacao_percentual.toFixed(2) + '%'
                }));
                const wsComparativo = XLSX.utils.json_to_sheet(dadosComparativo);
                XLSX.utils.book_append_sheet(wb, wsComparativo, 'Comparativo Mensal');
            }
            
            // 3. Gerar nome do arquivo
            const timestamp = this.formatadores.obterTimestamp();
            const nomeArquivo = `relatorio_completo_receitas_${timestamp}.xlsx`;
            
            // 4. Baixar arquivo
            XLSX.writeFile(wb, nomeArquivo);
            
            this.renderizador.mostrarAlerta('Relatório completo exportado com sucesso!', 'success');
            
        } catch (error) {
            console.error('Erro ao exportar relatório completo:', error);
            this.renderizador.mostrarAlerta('Erro ao exportar relatório completo', 'danger');
        }
    }
    
    /**
     * Prepara dados para exportação completa
     * @private
     */
    _prepararDadosExportacaoCompleta(relatorio) {
        const dados = [];
        
        relatorio.dados.forEach(item => {
            const descricao = this.formatadores.formatarDescricaoHierarquica(item);
            
            dados.push({
                'Código': item.codigo,
                'Especificação': descricao,
                'Previsão Inicial': item.previsao_inicial,
                'Previsão Atualizada': item.previsao_atualizada,
                [`Realizado ${relatorio.periodo.ano_anterior}`]: item.receita_anterior,
                [`Realizado ${relatorio.periodo.ano}`]: item.receita_atual,
                'Variação %': item.variacao_percentual.toFixed(2)
            });
        });
        
        // Adicionar total
        dados.push({
            'Código': '',
            'Especificação': 'TOTAL GERAL',
            'Previsão Inicial': relatorio.totais.previsao_inicial,
            'Previsão Atualizada': relatorio.totais.previsao_atualizada,
            [`Realizado ${relatorio.periodo.ano_anterior}`]: relatorio.totais.receita_anterior,
            [`Realizado ${relatorio.periodo.ano}`]: relatorio.totais.receita_atual,
            'Variação %': relatorio.totais.variacao_percentual.toFixed(2)
        });
        
        return dados;
    }
    
    /**
     * Gera download de imagem em alta resolução
     * @param {Object} dadosRelatorio - Dados do relatório
     */
    downloadImagem(dadosRelatorio) {
        if (!dadosRelatorio) {
            this.renderizador.mostrarAlerta('Nenhum relatório para exportar!', 'warning');
            return;
        }
        
        this.renderizador.mostrarAlerta('Gerando imagem em alta resolução...', 'info');
        
        // Desabilitar botão temporariamente
        const $btn = $('#btnDownloadImagem');
        $btn.prop('disabled', true).html('<i class="bi bi-hourglass-split"></i> Gerando...');
        
        // Criar container temporário
        const containerTemp = this._criarContainerImagem(dadosRelatorio);
        document.body.appendChild(containerTemp);
        
        // Configurações do html2canvas
        const configCanvas = {
            scale: this.config.EXPORTACAO.IMAGEM.ESCALA,
            useCORS: true,
            logging: false,
            backgroundColor: this.config.EXPORTACAO.IMAGEM.COR_FUNDO,
            windowWidth: containerTemp.scrollWidth,
            windowHeight: containerTemp.scrollHeight
        };
        
        // Gerar canvas e download
        html2canvas(containerTemp, configCanvas)
            .then(canvas => {
                document.body.removeChild(containerTemp);
                
                canvas.toBlob(blob => {
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    const nomeArquivo = `balanco_receita_${dadosRelatorio.periodo.ano}_${dadosRelatorio.periodo.mes}_${this.formatadores.obterTimestamp()}.png`;
                    
                    link.download = nomeArquivo;
                    link.href = url;
                    link.click();
                    
                    URL.revokeObjectURL(url);
                    
                    // Restaurar botão
                    $btn.prop('disabled', false).html('<i class="bi bi-image"></i> Imagem HD');
                    this.renderizador.mostrarAlerta('Imagem gerada com sucesso!', 'success');
                    
                }, this.config.EXPORTACAO.IMAGEM.FORMATO, this.config.EXPORTACAO.IMAGEM.QUALIDADE);
            })
            .catch(error => {
                console.error('Erro ao gerar imagem:', error);
                
                if (containerTemp.parentNode) {
                    document.body.removeChild(containerTemp);
                }
                
                $btn.prop('disabled', false).html('<i class="bi bi-image"></i> Imagem HD');
                this.renderizador.mostrarAlerta('Erro ao gerar imagem. Por favor, tente novamente.', 'danger');
            });
    }
    
    /**
     * Cria container temporário para geração de imagem
     * @private
     */
    _criarContainerImagem(dadosRelatorio) {
        const containerTemp = document.createElement('div');
        containerTemp.style.position = 'absolute';
        containerTemp.style.left = '-9999px';
        containerTemp.style.background = 'white';
        containerTemp.style.padding = '30px';
        containerTemp.style.width = this.config.EXPORTACAO.IMAGEM.LARGURA;
        containerTemp.style.fontFamily = 'Arial, sans-serif';
        
        // Cabeçalho
        const cabecalho = document.createElement('div');
        cabecalho.style.textAlign = 'center';
        cabecalho.style.marginBottom = '20px';
        cabecalho.innerHTML = `
            <h2 style="color: #1e3c72; margin-bottom: 10px; font-size: 24px;">BALANÇO ORÇAMENTÁRIO DA RECEITA</h2>
            <h3 style="color: #333; margin-bottom: 8px; font-size: 18px;">${dadosRelatorio.periodo.nome_mes}/${dadosRelatorio.periodo.ano}</h3>
            <p style="color: #666; margin: 5px 0; font-size: 14px;">UG: ${dadosRelatorio.filtros.nome_coug}</p>
        `;
        
        // Tabela
        const tabelaContainer = document.createElement('div');
        tabelaContainer.innerHTML = this._criarTabelaImagem(dadosRelatorio);
        
        // Rodapé
        const rodape = document.createElement('div');
        rodape.style.textAlign = 'center';
        rodape.style.marginTop = '30px';
        rodape.style.fontSize = '10px';
        rodape.style.color = '#666';
        rodape.style.borderTop = '1px solid #ddd';
        rodape.style.paddingTop = '10px';
        rodape.innerHTML = `<p style="margin: 0;">Gerado em: ${dadosRelatorio.data_geracao}</p>`;
        
        containerTemp.appendChild(cabecalho);
        containerTemp.appendChild(tabelaContainer);
        containerTemp.appendChild(rodape);
        
        return containerTemp;
    }
    
    /**
     * Cria HTML da tabela para imagem
     * @private
     */
    _criarTabelaImagem(dadosRelatorio) {
        let html = `
            <table style="width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 20px;">
                <thead>
                    <tr style="background-color: #1e3c72; color: white;">
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: left; width: 35%;">RECEITAS</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">PREVISÃO INICIAL<br>${dadosRelatorio.periodo.ano}</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">PREVISÃO ATUALIZADA<br>${dadosRelatorio.periodo.ano}</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">REALIZADA<br>${dadosRelatorio.periodo.mes}/${dadosRelatorio.periodo.ano}</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">REALIZADA<br>${dadosRelatorio.periodo.mes}/${dadosRelatorio.periodo.ano_anterior}</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: right;">VARIAÇÃO<br>ABSOLUTA</th>
                        <th style="border: 1px solid #ddd; padding: 8px; text-align: center;">VARIAÇÃO<br>%</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        // Adicionar linhas de dados
        dadosRelatorio.dados.forEach(item => {
            const paddingLeft = 10 + (item.nivel * 20);
            const fontWeight = item.nivel === 0 ? 'bold' : 'normal';
            let backgroundColor = 'white';
            
            if (item.nivel === 0) {
                backgroundColor = '#f5f5f5';
            } else if (item.nivel === 4) {
                backgroundColor = '#e3f2fd';
            }
            
            const corVariacao = item.variacao_absoluta >= 0 ? '#28a745' : '#dc3545';
            const descricao = this.formatadores.formatarDescricaoHierarquica(item);
            
            html += `
                <tr style="background-color: ${backgroundColor};">
                    <td style="border: 1px solid #ddd; padding: 6px 8px; padding-left: ${paddingLeft}px; font-weight: ${fontWeight};">
                        ${descricao}
                    </td>
                    <td style="border: 1px solid #ddd; padding: 6px 8px; text-align: right; font-weight: ${fontWeight};">
                        ${this.formatadores.formatarValor(item.previsao_inicial)}
                    </td>
                    <td style="border: 1px solid #ddd; padding: 6px 8px; text-align: right; font-weight: ${fontWeight};">
                        ${this.formatadores.formatarValor(item.previsao_atualizada)}
                    </td>
                    <td style="border: 1px solid #ddd; padding: 6px 8px; text-align: right; font-weight: ${fontWeight};">
                        ${this.formatadores.formatarValor(item.receita_atual)}
                    </td>
                    <td style="border: 1px solid #ddd; padding: 6px 8px; text-align: right; font-weight: ${fontWeight};">
                        ${this.formatadores.formatarValor(item.receita_anterior)}
                    </td>
                    <td style="border: 1px solid #ddd; padding: 6px 8px; text-align: right; font-weight: ${fontWeight}; color: ${corVariacao};">
                        ${this.formatadores.formatarValor(item.variacao_absoluta)}
                    </td>
                    <td style="border: 1px solid #ddd; padding: 6px 8px; text-align: center; font-weight: ${fontWeight}; color: ${corVariacao};">
                        ${this.formatadores.formatarPercentual(item.variacao_percentual)}
                    </td>
                </tr>
            `;
        });
        
        // Adicionar linha de total
        const corTotalVariacao = dadosRelatorio.totais.variacao_absoluta >= 0 ? '#28a745' : '#dc3545';
        html += `
                <tr style="background-color: #2c3e50; color: white; font-weight: bold;">
                    <td style="border: 1px solid #ddd; padding: 8px;">TOTAL GERAL</td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">
                        ${this.formatadores.formatarValor(dadosRelatorio.totais.previsao_inicial)}
                    </td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">
                        ${this.formatadores.formatarValor(dadosRelatorio.totais.previsao_atualizada)}
                    </td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">
                        ${this.formatadores.formatarValor(dadosRelatorio.totais.receita_atual)}
                    </td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">
                        ${this.formatadores.formatarValor(dadosRelatorio.totais.receita_anterior)}
                    </td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: right; color: ${corTotalVariacao};">
                        ${this.formatadores.formatarValor(dadosRelatorio.totais.variacao_absoluta)}
                    </td>
                    <td style="border: 1px solid #ddd; padding: 8px; text-align: center; color: ${corTotalVariacao};">
                        ${this.formatadores.formatarPercentual(dadosRelatorio.totais.variacao_percentual)}
                    </td>
                </tr>
            </tbody>
        </table>
        `;
        
        return html;
    }
}

// Exportar instância única
window.ExportadorBalancoReceita = new ExportadorBalancoReceita();