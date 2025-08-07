Documentação do Banco de Dados Híbrido - Sistema UBAN
Este documento detalha a arquitetura de banco de dados do Sistema de Relatórios UBAN, explicando o funcionamento da conexão híbrida (DuckDB e PostgreSQL) e os procedimentos para realizar cargas de dados incrementais.

1. Arquitetura de Banco de Dados Híbrida
O sistema foi projetado para operar em dois ambientes distintos, utilizando um banco de dados otimizado para cada cenário, o que proporciona flexibilidade, performance e economia de recursos.

Ambiente de Desenvolvimento (Local): Utiliza o DuckDB.

Motivo: DuckDB é um banco de dados analítico de alta performance que opera a partir de um único arquivo (uban.duckdb). É extremamente rápido para consultas complexas e agregações, ideal para desenvolvimento, testes e análises locais sem a necessidade de um servidor.

Ativação: Este ambiente é ativado quando a variável de ambiente FLASK_ENV está definida como development ou não está definida (padrão).

Ambiente de Produção (Servidor/VPS): Utiliza o PostgreSQL.

Motivo: PostgreSQL é um sistema de gerenciamento de banco de dados relacional robusto, confiável e ideal para ambientes de produção que exigem concorrência, segurança e escalabilidade.

Ativação: Este ambiente é ativado quando a variável de ambiente FLASK_ENV está definida como production.

Como o Sistema Escolhe o Banco de Dados?
A "inteligência" para a escolha do banco de dados reside no módulo app/db_manager.py.

Inicialização: Ao iniciar a aplicação (run.py), o create_app é chamado.

Leitura do Ambiente: Dentro de create_app, a função db_manager.init_app(app) é executada.

Seleção da Conexão: O db_manager verifica o valor de app.config['FLASK_ENV']:

Se for development, ele se configura para usar o DuckDB.

Se for production, ele se configura para usar o PostgreSQL, cujas credenciais são lidas do arquivo .env através do config.py.

Execução de Consultas: Todas as consultas no sistema (rotas da API, relatórios, etc.) utilizam o db_manager.execute_query(). Este método abstrai a lógica, direcionando a consulta para o banco de dados correto (DuckDB ou PostgreSQL) sem que o resto do código precise se preocupar com qual banco está ativo.