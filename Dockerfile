FROM python:3.12-slim

COPY . /app
WORKDIR /app

ENV PYTHONPATH=/app
ENV PUBLIC_OR_LOCAL=PROD


COPY pyproject.toml .
COPY pdm.lock .

RUN pip install -U pip setuptools wheel
RUN pip install pdm
RUN pdm install --prod --no-lock --no-editable
RUN apt-get update && apt-get install -y chromium-browser
ENV PLOTLY_BROWSER_EXECUTABLE=/usr/bin/chromium-browser
EXPOSE 7070
ENTRYPOINT ["pdm", "run", "src/server.py"]
