
.\run.ps1

# Roboflow Simple App

Proyecto simple con mejor arquitectura por capas para:

- Analizar imagenes con un workflow de Roboflow
- Guardar imagenes en AWS S3
- Generar URLs firmadas (presigned URLs)
- Guardar resultados en MongoDB
- Registrar y autenticar usuarios con JWT
- Gestion avanzada de usuarios por roles
- El analisis solo persiste la imagen original; no se genera imagen procesada

## 1) Estructura

```
roboflow_simple_app/
  app/
    core/
      config.py
      security.py
    db/
      mongo.py
    repositories/
      user_repository.py
      diagnostico_repository.py
    routers/
      auth.py
      diagnostico.py
      admin_users.py
    schemas/
      auth.py
      diagnostico.py
    services/
      auth_service.py
      diagnostico_service.py
      roboflow_service.py
      s3_service.py
    dependencies.py
    main.py
  .env.example
  requirements.txt
```

## 2) Instalacion

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 3) Configuracion

1. Copia `.env.example` a `.env`
2. Completa tus credenciales y valores:

- `ROBOFLOW_API_KEY`
- `ROBOFLOW_WORKSPACE`
- `ROBOFLOW_WORKFLOW_ID`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_S3_BUCKET`
- `MONGODB_URI`
- `SECRET_KEY`
- `INITIAL_ADMIN_USERNAME`
- `INITIAL_ADMIN_PASSWORD`
- `INITIAL_ADMIN_NOMBRE`
- `INITIAL_ADMIN_APELLIDO`
- `INITIAL_ADMIN_EMAIL`

## 4) Ejecutar

```bash
uvicorn app.main:app --reload --port 8010
```

## 5) Endpoints

- `GET /health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/login/form`
- `GET /api/auth/me`
- `GET /api/admin/users`
- `POST /api/admin/users`
- `PATCH /api/admin/users/{user_id}`
- `POST /api/diagnosticos/analizar` (form-data con campo `file`)
- `GET /api/diagnosticos/historial`
- `GET /api/diagnosticos/mis-diagnosticos`
- `GET /api/diagnosticos/detalle/{diagnostico_id}`
- `GET /api/diagnosticos/{diagnostico_id}`

## 6) Flujo de `POST /api/diagnosticos/analizar`

1. Recibe imagen
2. Valida formato
3. Ejecuta workflow de Roboflow
4. Sube imagen original (y procesada si existe) a S3
5. Genera URLs firmadas
6. Guarda metadata en MongoDB
7. Retorna resultado de analisis

## 7) Notas de autenticacion

- Usa el token retornado por login en `Authorization: Bearer <token>`
- Los endpoints de diagnostico requieren autenticacion
- El registro publico crea pacientes
- La cuenta admin inicial se crea al arrancar la app si se configuran las variables `INITIAL_ADMIN_*`
- Solo un usuario con rol `admin` puede gestionar usuarios y crear doctores o nuevos administradores
- Para desarrollo en Windows usa `run.ps1` para guardar el bytecode fuera de `app`
