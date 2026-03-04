FROM python:3.12-slim

# USUÁRIO NÃO-ROOT
RUN useradd -m -u 1001 runner

# DEPENDÊNCIAS
WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --only main

# CÓDIGO
COPY wanda_runner/ ./wanda_runner/

# PERMISSÕES
RUN chown -R runner:runner /app

USER runner

# INICIALIZAÇÃO
EXPOSE 8001

CMD ["uvicorn", "wanda_runner.app:app", "--host", "0.0.0.0", "--port", "8001"]