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
2. Instalar dependências do backend:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Definir a variável de ambiente `DATABASE_URL` apontando para seu PostgreSQL:
   ```bash
   export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
   ```
4. Iniciar o servidor FastAPI:
   ```bash
   uvicorn backend.main:app --reload
   ```

### Worker
1. Em outro terminal, iniciar o worker RQ:
   ```bash
   python backend/worker.py
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

## Licença
Este projeto está licenciado sob os termos da [Licença MIT](LICENSE).
