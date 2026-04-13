# Guia Rapida: levantar FastAPI con uv

Esta guia es corta y practica para ejecutar el backend `python_alzhecare_cnn` con `uv`.

## Requisitos

- Python 3.13+
- uv instalado

Instalar uv (si no lo tienes):

```powershell
pip install uv
```

## 1) Sincronizar dependencias

```powershell
uv sync
```

## 2) Configurar entorno

1. Copia `.env.example` a `.env`
2. Ajusta al menos estas variables:

- `SECRET_KEY` (minimo 24 caracteres)
- `DATABASE_URL`
- `CORS_ALLOW_ORIGINS` (por ejemplo `http://localhost:3000,http://localhost:5173`)

Si usaras analisis y fotos:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_S3_BUCKET`

Si usaras el modelo Torch:

- `TORCH_MODEL_PATH`
- `TORCH_LABEL_CLASSES_PATH`

## 3) Ejecutar la API

```powershell
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

## 4) Verificar que esta arriba

- Health: `GET http://localhost:8010/health`
- Docs Swagger: `http://localhost:8010/docs`

## Errores comunes

- `503 Base de datos no disponible`: revisar `DATABASE_URL`, red y credenciales.
- `503 Servicio de almacenamiento no disponible`: revisar variables AWS/S3.
- Error al arrancar por `SECRET_KEY`: definir una clave robusta en `.env`.
