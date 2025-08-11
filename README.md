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
4. (Opcional) Configurar o acesso ao Redis via variáveis de ambiente:
   ```bash
   export REDIS_HOST=localhost
   export REDIS_PORT=6379
   ```
5. Iniciar o servidor FastAPI:
   ```bash
   uvicorn backend.main:app --reload
   ```

### Testes
Para executar os testes do backend:
```bash
cd backend
pytest
```

Para executar os testes do frontend:
```bash
cd frontend
npm test
```

### Worker
1. Em outro terminal, iniciar o worker RQ:
   ```bash
   python -m backend.worker
   ```
   As variáveis `REDIS_HOST` e `REDIS_PORT` também são respeitadas aqui.

### Node
1. Instalar dependências do frontend:
   ```bash
   npm install
   ```

### Docker Compose
1. Subir backend, frontend, Redis e PostgreSQL:
   ```bash
   docker-compose up --build
   ```
   Backend em http://localhost:8000
   Frontend em http://localhost:5173

2. Parar e remover containers:
   ```bash
   docker-compose down
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

## Importar no SCI Visual
1. Gere o arquivo de lançamentos via rota `/transactions/export` informando `empresa_id`, `start_date` e `end_date`.
2. No **SCI Visual**, acesse o menu **Integrações > Importações layout padrão SCI**.
3. Identifique o número da empresa e a referência.
4. Em **Importar de**, selecione **TXT Visual Sucessor** e localize o arquivo gerado.
5. Confirme para concluir a importação dos lançamentos.

## Licença
Este projeto está licenciado sob os termos da [Licença MIT](LICENSE).
