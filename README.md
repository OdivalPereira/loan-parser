# loan-parser

## Propósito
Plataforma para processamento e análise de contratos de empréstimo.

## Arquitetura Macro
- **FastAPI** para a API backend.
- **RQ** para filas de processamento assíncrono.
- **React** para a interface web.
- **PostgreSQL** para persistência de dados.
- **Amazon S3** para armazenamento de arquivos.

## Setup Local
### Python
1. Criar e ativar o ambiente virtual:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Instalar dependências:
   ```bash
   pip install -r requirements.txt
   ```

### Node
1. Instalar dependências do frontend:
   ```bash
   npm install
   ```

### Redis e PostgreSQL via Docker
1. Subir serviços com Docker:
   ```bash
   docker run --name redis -p 6379:6379 -d redis
   docker run --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres
   ```

## Padrões de Commit
Adote [Conventional Commits](https://www.conventionalcommits.org/), por exemplo `feat: adicionar parser Sicoob`.

## Próximos Passos do MVP
- Upload e parser de arquivos do Sicoob.
- Tela de listagem de contratos.
- Exportação de juros.

## Roadmap
Verificar o roadmap para detalhes de:
- Upload/parser Sicoob.
- Tela de contratos.
- Exportação de juros.

