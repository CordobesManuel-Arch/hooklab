# HookLab

Inspector local de webhooks hecho con FastAPI. Recibe requests HTTP, las guarda en SQLite y permite revisarlas desde una interfaz web simple.

## Uso

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Abrir `http://127.0.0.1:8000` y enviar webhooks a `/hooks/<nombre>`.
