# Contexto do Projeto - Sistema de Relatórios Orçamentários, Financeiros e Patrimoniais

## Visão Geral
Sistema web desenvolvido em Python/Flask para gerenciamento e geração de relatórios orçamentários, financeiros e patrimoniais. O sistema importa dados de planilhas Excel para um banco PostgreSQL e disponibiliza relatórios via interface web.

## Stack Tecnológica
- **Backend**: Python 3.x, Flask (com Blueprints)
- **Banco de Dados**: PostgreSQL 
- **ORM**: SQLAlchemy
- **Frontend**: HTML, CSS (separado), JavaScript (separado)
- **ETL**: Pandas para leitura de Excel e carga no banco
- **Deploy**: Desenvolvimento local, futura implantação no Railway

## Arquitetura do Sistema

### 1. Camada de Dados
- **Fonte**: Planilhas Excel em `dados_brutos/` (subpastas: dimensao/ e fato/)
- **Destino**: PostgreSQL hospedado em VPS
- **Processo ETL**: Scripts Python para ler Excel e popular banco de dados
- **Atualização**: Sistema deve permitir recarregar dados quando planilhas forem alteradas

### 2. Estrutura de Diretórios
```
relatorios_uban/
├── venv/                    # Ambiente virtual Python
├── dados_brutos/           # Planilhas Excel fonte
│   ├── dimensao/          # Dados dimensionais
│   └── fato/              # Dados de fatos
├── app/                    # Aplicação Flask
│   ├── __init__.py        # Inicialização e configuração Flask
│   ├── routes/            # Blueprints de rotas
│   │   ├── main.py        # Rotas principais
│   │   ├── relatorios.py  # Blueprint de relatórios
│   │   └── api.py         # Blueprint da API REST
│   ├── static/            # Assets estáticos
│   │   ├── css/          # Arquivos CSS
│   │   └── js/           # Arquivos JavaScript
│   ├── templates/         # Templates HTML (Jinja2)
│   │   ├── base.html     # Template base
│   │   └── relatorios/   # Templates específicos
│   └── modules/           # Módulos reutilizáveis
│       ├── database.py    # Conexão e helpers do banco
│       └── etl.py        # Lógica de importação Excel→DB
├── models/                # Modelos SQLAlchemy (ORM)
├── config.py             # Configurações da aplicação
├── .env                  # Variáveis de ambiente (credenciais)
├── run.py                # Entry point da aplicação
└── requirements.txt      # Dependências Python
```

### 3. Configuração do Banco de Dados
- **Host**: 31.97.128.109:5432
- **Banco atual**: meu_banco (será criado novo banco exclusivo)
- **Novo banco sugerido**: relatorios_uban
- **Conexão**: Usando SQLAlchemy com psycopg2

### 4. Funcionalidades Planejadas

#### Fase 1 - ETL e Banco
1. Criação automática de tabelas baseada nas planilhas Excel
2. Importação inicial de dados
3. Sistema de atualização (reimportação) de dados
4. Validação e tratamento de erros

#### Fase 2 - API e Relatórios
1. API REST para consulta de dados
2. Interface web para visualização de relatórios
3. Filtros dinâmicos (período, categoria, etc.)
4. Exportação de relatórios (PDF, Excel)

#### Fase 3 - Recursos Avançados
1. Dashboard com gráficos interativos
2. Sistema de permissões/usuários
3. Agendamento de atualizações automáticas
4. Notificações e alertas

## Padrões e Boas Práticas

### Segurança
- Credenciais em arquivo `.env` (nunca commitar)
- Validação de inputs
- Prepared statements para queries SQL

### Código
- Blueprints Flask para modularização
- Separação de responsabilidades (MVC)
- Docstrings e comentários em português
- Tratamento de exceções

### Frontend
- CSS e JS em arquivos separados
- Mobile-responsive
- Acessibilidade (ARIA labels)

## Dependências Principais
```
flask              # Framework web
psycopg2-binary   # Driver PostgreSQL
pandas            # Manipulação de dados
openpyxl          # Leitura de Excel
sqlalchemy        # ORM
python-dotenv     # Variáveis de ambiente
```

## Próximos Passos Imediatos
1. ✅ Estrutura de pastas criada
2. ⏳ Configurar conexão segura com PostgreSQL
3. ⏳ Criar novo banco de dados
4. ⏳ Analisar estrutura das planilhas Excel
5. ⏳ Implementar ETL básico
6. ⏳ Criar primeira rota Flask

## Comandos Úteis

### Ativar ambiente virtual
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Executar aplicação
```bash
python run.py
```

### Atualizar dados do banco
```bash
python -m app.modules.etl update
```

## Observações Importantes
- O desenvolvedor é iniciante, então o código deve ser claro e bem comentado
- Preferência por explicações passo a passo
- Sistema inicialmente local, depois será deployado no Railway
- Dados sensíveis (financeiros/patrimoniais) - atenção à segurança

## Contexto de Negócio
Sistema para gestão de relatórios organizacionais com foco em:
- Relatórios orçamentários
- Relatórios financeiros  
- Relatórios patrimoniais

Os dados fonte estão em planilhas Excel que precisam ser consolidadas em um banco de dados para permitir análises mais complexas e geração de relatórios padronizados.