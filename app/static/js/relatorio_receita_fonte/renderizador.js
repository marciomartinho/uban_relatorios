/**
 * Módulo de Renderização
 * Responsável por toda a renderização de UI e tabelas
 * app/static/js/relatorio_receita_fonte/renderizador.js
 */

class RenderizadorRelatorioReceitaFonte {
    constructor() {
        this.config = window.ConfigRelatorioReceitaFonte;
        this.seletores = this.config.SELETORES;
    }
    
    /**
     * Renderiza tela de loading
     */
    mostrarLoading() {
        document.querySelector(this.seletores.MENSAGEM_INICIAL).style.display = 'none';
        document.querySelector(this.seletores.CONTAINER_RELATORIO).style.display = 'none';
        document.querySelector(this.seletores.CONTAINER_LOADING).style.display = 'block';
    }
    
    /**
     * Oculta tela de loading
     */
    ocultarLoading() {
        document.querySelector(this.seletores.CONTAINER_LOADING).style.display = 'none';
    }
    
    /**
     * Renderiza o relatório completo
     * @param {Object} dados - Dados do relatório
     */
    renderizarRelatorio(dados) {
        console.log('Renderizando relatório:', dados);
        
        // Ocultar loading e mensagem inicial
        this.ocultarLoading();
        document.querySelector(this.seletores.MENSAGEM_INICIAL).style.display = 'none';
        
        // Atualizar informações do cabeçalho
        this._atualizarCabecalho(dados);
        
        // Verificar se há dados
        if (!dados.dados || dados.dados.length === 0) {
            this._mostrarEstadoVazio();
            return;
        }
        
        // Renderizar tabela
        this._renderizarTabela(dados);
        
        // Renderizar totais
        this._renderizarTotais(dados.totais);
        
        // Mostrar container do relatório
        document.querySelector(this.seletores.CONTAINER_RELATORIO).style.display = 'block';
        document.querySelector(this.seletores.EMPTY_STATE).style.display = 'none';
    }
    
    /**
     * Atualiza o cabeçalho do relatório
     * @private
     */
    _atualizarCabecalho(dados) {
        const tipo = dados.tipo || 'fonte';
        const configTipo = this.config.TIPOS_RELATORIO[tipo];
        
        // Título do relatório
        document.querySelector(this.seletores.TITULO_RELATORIO).textContent = configTipo.titulo;
        
        // Header da tabela
        document.querySelector(this.seletores.HEADER_TIPO).textContent = configTipo.header;
        
        // Período
        const periodo = dados.periodo;
        const periodoTexto = `${periodo.mes.toString().padStart(2, '0')}/${periodo.ano}`;
        document.querySelector(this.seletores.PERIODO_RELATORIO).textContent = periodoTexto;
        
        // Anos nos headers
        document.querySelector(this.seletores.HEADER_ANO_ATUAL).textContent = periodo.ano;
        document.querySelector(this.seletores.HEADER_ANO_ANTERIOR).textContent = periodo.ano - 1;
        
        // UG
        document.querySelector(this.seletores.UG_RELATORIO).textContent = dados.nome_ug || 'Consolidado';
        
        // Data de geração
        document.querySelector(this.seletores.DATA_GERACAO).textContent = dados.data_geracao || '-';
    }
    
    /**
     * Renderiza a tabela de dados
     * @private
     */
    _renderizarTabela(dados) {
        const tbody = document.querySelector(this.seletores.TBODY_RELATORIO);
        tbody.innerHTML = '';
        
        // Renderizar cada item
        dados.dados.forEach(item => {
            const tr = this._criarLinhaTabela(item);
            tbody.appendChild(tr);
        });
    }
    
    /**
     * Cria uma linha da tabela
     * @private
     */
    _criarLinhaTabela(item) {
        const tr = document.createElement('tr');
        
        // Adicionar classes e atributos
        tr.className = this.config.CLASSES.NIVEIS[item.nivel] || '';
        tr.dataset.id = item.id;
        tr.dataset.nivel = item.nivel;
        
        if (item.pai_id) {
            tr.dataset.paiId = item.pai_id;
        }
        
        // Ocultar itens de nível 1 inicialmente
        if (item.nivel === 1) {
            tr.style.display = 'none';
        }
        
        // Célula de descrição
        const tdDescricao = document.createElement('td');
        tdDescricao.style.paddingLeft = `${item.nivel * this.config.RENDERIZACAO.PADDING_POR_NIVEL}px`;
        
        // Botão de expansão para itens com filhos
        if (item.tem_filhos) {
            const btnExpandir = document.createElement('button');
            btnExpandir.className = 'btn btn-sm btn-link toggle-btn p-0 me-2';
            btnExpandir.dataset.id = item.id;
            btnExpandir.innerHTML = this.config.ICONES.EXPANDIR;
            btnExpandir.style.width = '20px';
            tdDescricao.appendChild(btnExpandir);
        }
        
        // Texto da descrição
        const spanDescricao = document.createElement('span');
        spanDescricao.textContent = `${item.codigo} - ${item.descricao}`;
        if (item.nivel === 0) {
            spanDescricao.className = 'fw-bold';
        }
        tdDescricao.appendChild(spanDescricao);
        tr.appendChild(tdDescricao);
        
        // Células de valores
        const valores = [
            item.previsao_inicial,
            item.previsao_atualizada,
            item.receita_atual,
            item.receita_anterior,
            item.variacao_absoluta
        ];
        
        valores.forEach(valor => {
            const td = document.createElement('td');
            td.className = 'text-end';
            td.textContent = this._formatarMoeda(valor);
            tr.appendChild(td);
        });
        
        // Célula de variação percentual
        const tdVariacao = document.createElement('td');
        tdVariacao.className = 'text-center';
        tdVariacao.textContent = this._formatarPercentual(item.variacao_percentual);
        
        // Adicionar classe de cor para variação
        if (item.variacao_percentual > 0) {
            tdVariacao.classList.add(this.config.CLASSES.VARIACAO.POSITIVA);
        } else if (item.variacao_percentual < 0) {
            tdVariacao.classList.add(this.config.CLASSES.VARIACAO.NEGATIVA);
        }
        
        tr.appendChild(tdVariacao);
        
        return tr;
    }
    
    /**
     * Renderiza os totais
     * @private
     */
    _renderizarTotais(totais) {
        if (!totais) return;
        
        document.querySelector(this.seletores.TOTAL_PREVISAO_INICIAL).textContent = 
            this._formatarMoeda(totais.previsao_inicial);
        
        document.querySelector(this.seletores.TOTAL_PREVISAO_ATUALIZADA).textContent = 
            this._formatarMoeda(totais.previsao_atualizada);
        
        document.querySelector(this.seletores.TOTAL_RECEITA_ATUAL).textContent = 
            this._formatarMoeda(totais.receita_atual);
        
        document.querySelector(this.seletores.TOTAL_RECEITA_ANTERIOR).textContent = 
            this._formatarMoeda(totais.receita_anterior);
        
        const elementoVariacaoAbs = document.querySelector(this.seletores.TOTAL_VARIACAO_ABSOLUTA);
        elementoVariacaoAbs.textContent = this._formatarMoeda(totais.variacao_absoluta);
        
        const elementoVariacaoPct = document.querySelector(this.seletores.TOTAL_VARIACAO_PERCENTUAL);
        elementoVariacaoPct.textContent = this._formatarPercentual(totais.variacao_percentual);
        
        // Adicionar classes de cor
        const classeVariacao = totais.variacao_absoluta >= 0 ? 
            this.config.CLASSES.VARIACAO.POSITIVA : 
            this.config.CLASSES.VARIACAO.NEGATIVA;
        
        elementoVariacaoAbs.className = `text-end ${classeVariacao}`;
        elementoVariacaoPct.className = `text-center ${classeVariacao}`;
    }
    
    /**
     * Mostra estado vazio
     * @private
     */
    _mostrarEstadoVazio() {
        document.querySelector(this.seletores.CONTAINER_RELATORIO).style.display = 'block';
        document.querySelector(this.seletores.EMPTY_STATE).style.display = 'block';
        document.querySelector(this.seletores.TABELA_RELATORIO).style.display = 'none';
    }
    
    /**
     * Mostra mensagem de erro
     * @param {string} mensagem - Mensagem de erro
     */
    mostrarErro(mensagem) {
        this.ocultarLoading();
        
        const alertHtml = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                ${this.config.ICONES.ERRO} ${mensagem}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        const container = document.querySelector('.container-fluid');
        container.insertAdjacentHTML('afterbegin', alertHtml);
        
        // Auto-remover após 5 segundos
        setTimeout(() => {
            const alert = container.querySelector('.alert');
            if (alert) {
                alert.remove();
            }
        }, this.config.RENDERIZACAO.TEMPO_ALERTA);
    }
    
    /**
     * Mostra mensagem de sucesso
     * @param {string} mensagem - Mensagem de sucesso
     */
    mostrarSucesso(mensagem) {
        const alertHtml = `
            <div class="alert alert-success alert-dismissible fade show" role="alert">
                ${this.config.ICONES.SUCESSO} ${mensagem}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        const container = document.querySelector('.container-fluid');
        container.insertAdjacentHTML('afterbegin', alertHtml);
        
        // Auto-remover após 3 segundos
        setTimeout(() => {
            const alert = container.querySelector('.alert-success');
            if (alert) {
                alert.remove();
            }
        }, 3000);
    }
    
    /**
     * Formata valor para moeda
     * @private
     */
    _formatarMoeda(valor) {
        if (valor === null || valor === undefined) {
            return '0,00';
        }
        return new Intl.NumberFormat(
            this.config.FORMATACAO.LOCALE,
            this.config.FORMATACAO.NUMERO
        ).format(valor);
    }
    
    /**
     * Formata percentual
     * @private
     */
    _formatarPercentual(valor) {
        if (valor === null || valor === undefined) {
            return '0,00%';
        }
        return new Intl.NumberFormat(
            this.config.FORMATACAO.LOCALE,
            this.config.FORMATACAO.PERCENTUAL
        ).format(valor) + '%';
    }
    
    /**
     * Expande todos os itens
     */
    expandirTodos() {
        const botoes = document.querySelectorAll('.toggle-btn');
        botoes.forEach(btn => {
            btn.innerHTML = this.config.ICONES.RECOLHER;
            btn.classList.add(this.config.CLASSES.EXPANDIDO);
        });
        
        // Mostrar todos os itens de nível 1
        const itensNivel1 = document.querySelectorAll('tr[data-nivel="1"]');
        itensNivel1.forEach(item => {
            item.style.display = 'table-row';
        });
    }
    
    /**
     * Recolhe todos os itens
     */
    recolherTodos() {
        const botoes = document.querySelectorAll('.toggle-btn');
        botoes.forEach(btn => {
            btn.innerHTML = this.config.ICONES.EXPANDIR;
            btn.classList.remove(this.config.CLASSES.EXPANDIDO);
        });
        
        // Ocultar todos os itens de nível 1
        const itensNivel1 = document.querySelectorAll('tr[data-nivel="1"]');
        itensNivel1.forEach(item => {
            item.style.display = 'none';
        });
    }
}

// Exportar instância única
window.RenderizadorRelatorioReceitaFonte = new RenderizadorRelatorioReceitaFonte();