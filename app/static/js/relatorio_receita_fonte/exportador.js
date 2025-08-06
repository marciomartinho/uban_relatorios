/**
 * Módulo de Exportação
 * Gerencia exportação para Excel e outros formatos
 * app/static/js/relatorio_receita_fonte/exportador.js
 */

class ExportadorRelatorioReceitaFonte {
    constructor() {
        this.config = window.ConfigRelatorioReceitaFonte;
        this.dadosAtuais = null;
    }
    
    /**
     * Define os dados atuais do relatório
     * @param {Object} dados - Dados do relatório
     */
    setDadosAtuais(dados) {
        this.dadosAtuais = dados;
    }
    
    /**
     * Exporta relatório para Excel
     * @param {Object} dados - Dados do relatório (opcional, usa dadosAtuais se não fornecido)
     */
    async exportarExcel(dados = null) {
        const dadosExportar = dados || this.dadosAtuais;
        
        if (!dadosExportar || !dadosExportar.dados) {
            window.RenderizadorRelatorioReceitaFonte.mostrarErro('Nenhum dado para exportar');
            return;
        }
        
        console.log('Exportando para Excel:', dadosExportar);
        
        try {
            // Criar workbook
            const wb = XLSX.utils.book_new();
            
            // Preparar dados para a planilha
            const dadosPlanilha = this._prepararDadosExcel(dadosExportar);
            
            // Criar worksheet
            const ws = XLSX.utils.aoa_to_sheet(dadosPlanilha);
            
            // Configurar larguras das colunas
            ws['!cols'] = this.config.EXPORTACAO.EXCEL.LARGURAS_COLUNAS.map(w => ({ wch: w }));
            
            // Adicionar worksheet ao workbook
            XLSX.utils.book_append_sheet(wb, ws, this.config.EXPORTACAO.EXCEL.NOME_ABA);
            
            // Gerar nome do arquivo
            const tipo = dadosExportar.tipo || 'fonte';
            const periodo = dadosExportar.periodo;
            const nomeArquivo = this.config.EXPORTACAO.EXCEL.NOME_ARQUIVO
                .replace('{tipo}', tipo)
                .replace('{periodo}', `${periodo.ano}_${String(periodo.mes).padStart(2, '0')}`);
            
            // Baixar arquivo
            XLSX.writeFile(wb, nomeArquivo);
            
            window.RenderizadorRelatorioReceitaFonte.mostrarSucesso('Arquivo Excel gerado com sucesso!');
            
        } catch (erro) {
            console.error('Erro ao exportar Excel:', erro);
            window.RenderizadorRelatorioReceitaFonte.mostrarErro('Erro ao gerar arquivo Excel');
        }
    }
    
    /**
     * Prepara dados para exportação Excel
     * @private
     */
    _prepararDadosExcel(dados) {
        const resultado = [];
        const periodo = dados.periodo;
        const tipo = dados.tipo === 'receita' ? 'CÓDIGO DE RECEITA' : 'FONTE DE RECEITA';
        
        // Cabeçalho do relatório
        resultado.push([`RELATÓRIO DETALHADO POR ${tipo}`]);
        resultado.push([`Período: ${String(periodo.mes).padStart(2, '0')}/${periodo.ano}`]);
        resultado.push([`Unidade Gestora: ${dados.nome_ug || 'Consolidado'}`]);
        resultado.push([`Data de Geração: ${dados.data_geracao || new Date().toLocaleString('pt-BR')}`]);
        resultado.push([]); // Linha em branco
        
        // Cabeçalhos da tabela
        resultado.push([
            'CÓDIGO',
            'DESCRIÇÃO',
            'PREVISÃO INICIAL',
            'PREVISÃO ATUALIZADA',
            `REALIZADA ${periodo.ano}`,
            `REALIZADA ${periodo.ano - 1}`,
            'VARIAÇÃO ABSOLUTA',
            'VARIAÇÃO %'
        ]);
        
        // Dados do relatório
        if (dados.dados && dados.dados.length > 0) {
            dados.dados.forEach(item => {
                // Adicionar indentação para itens de nível 1
                const descricao = item.nivel === 0 ? 
                    item.descricao : 
                    `    ${item.descricao}`;
                
                resultado.push([
                    item.codigo,
                    descricao,
                    item.previsao_inicial,
                    item.previsao_atualizada,
                    item.receita_atual,
                    item.receita_anterior,
                    item.variacao_absoluta,
                    item.variacao_percentual
                ]);
            });
        }
        
        // Linha em branco antes do total
        resultado.push([]);
        
        // Total geral
        if (dados.totais) {
            resultado.push([
                '',
                'TOTAL GERAL',
                dados.totais.previsao_inicial,
                dados.totais.previsao_atualizada,
                dados.totais.receita_atual,
                dados.totais.receita_anterior,
                dados.totais.variacao_absoluta,
                dados.totais.variacao_percentual
            ]);
        }
        
        return resultado;
    }
    
    /**
     * Exporta dados brutos em JSON
     * @param {Object} dados - Dados do relatório
     */
    exportarJSON(dados = null) {
        const dadosExportar = dados || this.dadosAtuais;
        
        if (!dadosExportar) {
            window.RenderizadorRelatorioReceitaFonte.mostrarErro('Nenhum dado para exportar');
            return;
        }
        
        try {
            const json = JSON.stringify(dadosExportar, null, 2);
            const blob = new Blob([json], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            
            const link = document.createElement('a');
            link.href = url;
            link.download = `relatorio_receita_fonte_${Date.now()}.json`;
            link.click();
            
            URL.revokeObjectURL(url);
            
            window.RenderizadorRelatorioReceitaFonte.mostrarSucesso('Arquivo JSON exportado com sucesso!');
            
        } catch (erro) {
            console.error('Erro ao exportar JSON:', erro);
            window.RenderizadorRelatorioReceitaFonte.mostrarErro('Erro ao exportar JSON');
        }
    }
    
    /**
     * Copia dados da tabela para clipboard
     */
    copiarTabela() {
        if (!this.dadosAtuais || !this.dadosAtuais.dados) {
            window.RenderizadorRelatorioReceitaFonte.mostrarErro('Nenhum dado para copiar');
            return;
        }
        
        try {
            let texto = '';
            const periodo = this.dadosAtuais.periodo;
            
            // Cabeçalho
            texto += `CÓDIGO\tDESCRIÇÃO\tPREVISÃO INICIAL\tPREVISÃO ATUALIZADA\t`;
            texto += `REALIZADA ${periodo.ano}\tREALIZADA ${periodo.ano - 1}\t`;
            texto += `VARIAÇÃO ABSOLUTA\tVARIAÇÃO %\n`;
            
            // Dados
            this.dadosAtuais.dados.forEach(item => {
                const descricao = item.nivel === 0 ? item.descricao : `  ${item.descricao}`;
                texto += `${item.codigo}\t${descricao}\t`;
                texto += `${this._formatarNumero(item.previsao_inicial)}\t`;
                texto += `${this._formatarNumero(item.previsao_atualizada)}\t`;
                texto += `${this._formatarNumero(item.receita_atual)}\t`;
                texto += `${this._formatarNumero(item.receita_anterior)}\t`;
                texto += `${this._formatarNumero(item.variacao_absoluta)}\t`;
                texto += `${this._formatarNumero(item.variacao_percentual, true)}\n`;
            });
            
            // Total
            if (this.dadosAtuais.totais) {
                texto += `\nTOTAL GERAL\t\t`;
                texto += `${this._formatarNumero(this.dadosAtuais.totais.previsao_inicial)}\t`;
                texto += `${this._formatarNumero(this.dadosAtuais.totais.previsao_atualizada)}\t`;
                texto += `${this._formatarNumero(this.dadosAtuais.totais.receita_atual)}\t`;
                texto += `${this._formatarNumero(this.dadosAtuais.totais.receita_anterior)}\t`;
                texto += `${this._formatarNumero(this.dadosAtuais.totais.variacao_absoluta)}\t`;
                texto += `${this._formatarNumero(this.dadosAtuais.totais.variacao_percentual, true)}`;
            }
            
            // Copiar para clipboard
            navigator.clipboard.writeText(texto).then(() => {
                window.RenderizadorRelatorioReceitaFonte.mostrarSucesso('Dados copiados para a área de transferência!');
            }).catch(erro => {
                console.error('Erro ao copiar:', erro);
                window.RenderizadorRelatorioReceitaFonte.mostrarErro('Erro ao copiar dados');
            });
            
        } catch (erro) {
            console.error('Erro ao copiar tabela:', erro);
            window.RenderizadorRelatorioReceitaFonte.mostrarErro('Erro ao copiar dados');
        }
    }
    
    /**
     * Formata número para exportação
     * @private
     */
    _formatarNumero(valor, isPercentual = false) {
        if (valor === null || valor === undefined) {
            return '0,00';
        }
        
        if (isPercentual) {
            return valor.toFixed(2).replace('.', ',') + '%';
        }
        
        return valor.toFixed(2).replace('.', ',');
    }
    
    /**
     * Prepara dados para impressão
     */
    prepararImpressao() {
        // Adicionar classe para impressão
        document.body.classList.add('printing');
        
        // Expandir todos os itens antes de imprimir
        window.RenderizadorRelatorioReceitaFonte.expandirTodos();
        
        // Remover classe após impressão
        window.addEventListener('afterprint', () => {
            document.body.classList.remove('printing');
        }, { once: true });
    }
}

// Exportar instância única
window.ExportadorRelatorioReceitaFonte = new ExportadorRelatorioReceitaFonte();