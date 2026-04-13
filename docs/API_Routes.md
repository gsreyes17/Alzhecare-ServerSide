# Documentacion de API (Routers) para Frontend Web y App Movil

Este documento describe los endpoints expuestos en los routers de FastAPI, sus JSON de entrada/salida, autenticacion, estados y recomendaciones de integracion para frontend.

## 1. Base de API y convenciones

- Base URL local sugerida: `http://localhost:8010`
- Healthcheck: `GET /health`
- Formato de fecha/hora: ISO 8601 (ejemplo: `2026-04-13T15:30:00+00:00`)
- Error estandar FastAPI (general):

```json
{
  "detail": "Mensaje de error"
}
```

- Errores de infraestructura estandarizados:
  - `503` cuando la base de datos no esta disponible
  - `500` para errores internos no controlados

## 2. Autenticacion y autorizacion

### 2.1 Login y token

El backend usa JWT Bearer.

- Endpoint login JSON: `POST /api/auth/login`
- Endpoint login formulario OAuth2: `POST /api/auth/login/form`
- Respuesta en ambos:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

### 2.2 Header requerido para endpoints protegidos

```http
Authorization: Bearer <access_token>
```

### 2.3 Roles disponibles

- `paciente`
- `doctor`
- `admin`

El backend valida permisos por rol en endpoints de doctor, paciente y admin.

## 3. Router de autenticacion (`/api/auth`)

## 3.1 Registrar paciente

- `POST /api/auth/register`
- Auth: no
- Request JSON:

```json
{
  "username": "paciente01",
  "password": "secreto123",
  "name": "Ana",
  "lastname": "Perez",
  "email": "ana@mail.com"
}
```

- Response `201` (`UserResponse`):

```json
{
  "id": "6612abc...",
  "username": "paciente01",
  "name": "Ana",
  "lastname": "Perez",
  "email": "ana@mail.com",
  "role": "paciente",
  "status": true,
  "profile_image_url": null,
  "created_at": "2026-04-13T10:00:00+00:00",
  "updated_at": "2026-04-13T10:00:00+00:00"
}
```

- Errores comunes:
  - `400` usuario ya registrado
  - `400` email ya registrado

## 3.2 Login JSON

- `POST /api/auth/login`
- Auth: no
- Request JSON:

```json
{
  "username": "paciente01",
  "password": "secreto123"
}
```

- Response `200`: `Token`
- Errores comunes:
  - `401` credenciales invalidas
  - `403` usuario inactivo

## 3.3 Login form (OAuth2PasswordRequestForm)

- `POST /api/auth/login/form`
- Content-Type: `application/x-www-form-urlencoded`
- Auth: no
- Campos:
  - `username`
  - `password`

- Response `200`: `Token`

## 3.4 Ver perfil actual

- `GET /api/auth/me`
- Auth: si
- Response `200`: `UserResponse`

## 3.5 Actualizar perfil actual

- `PATCH /api/auth/me`
- Auth: si
- Request JSON (todos opcionales):

```json
{
  "name": "Ana Maria",
  "lastname": "Perez",
  "email": "ana.nueva@mail.com",
  "password": "nuevaClave123"
}
```

- Response `200`: `UserResponse`
- Errores comunes:
  - `400` email en uso

## 3.6 Subir foto de perfil

- `POST /api/auth/me/photo`
- Auth: si
- Content-Type: `multipart/form-data`
- Campo archivo: `file`
- Response `200`:

```json
{
  "profile_image_url": "https://..."
}
```

- Errores comunes:
  - `400` archivo vacio
  - `503` servicio de almacenamiento no disponible

## 4. Router de diagnosticos (`/api/diagnoses`)

## 4.1 Analizar imagen propia

- `POST /api/diagnoses/analyze`
- Auth: si
- Content-Type: `multipart/form-data`
- Campo archivo: `file`
- Response `200` (`AnalysisResponse`):

```json
{
  "id": "6622def...",
  "result": "No Demented",
  "confidence": 0.947,
  "image_url": "https://...",
  "created_at": "2026-04-13T12:00:00+00:00"
}
```

- Errores comunes:
  - `400` archivo vacio
  - `400` archivo no es imagen valida
  - `503` servicio de almacenamiento no disponible

## 4.2 Historial resumido

- `GET /api/diagnoses/history?limit=50`
- Auth: si
- Restricciones de `limit`: `1..200`
- Response `200`:

```json
{
  "diagnoses": [
    {
      "id": "6622def...",
      "user_id": "6612abc...",
      "result": "No Demented",
      "confidence": 0.947,
      "status": "completado",
      "image_url": "https://...",
      "created_at": "2026-04-13T12:00:00+00:00",
      "updated_at": "2026-04-13T12:00:00+00:00",
      "model_output": {}
    }
  ],
  "total": 1
}
```

## 4.3 Mis diagnosticos

- `GET /api/diagnoses/my-diagnoses`
- Auth: si
- Response `200`: lista de `DiagnosisResponse`

## 4.4 Detalle de diagnostico

- `GET /api/diagnoses/detail/{diagnosis_id}`
- Auth: si
- Response `200`: objeto diagnostico completo
- Error:
  - `404` diagnostico no encontrado

## 4.5 Diagnostico por ID (tipado)

- `GET /api/diagnoses/{diagnosis_id}`
- Auth: si
- Response `200`: `DiagnosisResponse`
- Error:
  - `404` diagnostico no encontrado

## 5. Router doctor (`/api/doctor`)

Todos requieren rol `doctor`.

## 5.1 Buscar pacientes

- `GET /api/doctor/patients/search?q=ana`
- Response `200`: lista de `BasicUserResponse`

## 5.2 Crear solicitud de vinculacion

- `POST /api/doctor/requests`
- Request JSON:

```json
{
  "patient_user_id": "6612abc..."
}
```

- Response `200`: `BindingResponse`
- Errores comunes:
  - `404` paciente no encontrado
  - `400` ya vinculado
  - `400` ya existe solicitud pendiente

## 5.3 Listar solicitudes del doctor

- `GET /api/doctor/requests`
- Response `200`: lista `BindingResponse`

## 5.4 Listar pacientes asignados

- `GET /api/doctor/patients`
- Response `200`: lista `BasicUserResponse`

## 5.5 Historial de un paciente vinculado

- `GET /api/doctor/patients/{patient_user_id}/history?limit=100`
- Restricciones de `limit`: `1..500`
- Response `200`:

```json
{
  "diagnoses": [
    {
      "id": "...",
      "result": "...",
      "confidence": 0.91,
      "status": "completado",
      "image_url": "https://...",
      "created_at": "2026-04-13T12:00:00+00:00"
    }
  ]
}
```

- Error:
  - `403` sin vinculo activo con paciente

## 5.6 Analizar para paciente vinculado

- `POST /api/doctor/patients/{patient_user_id}/analyze`
- Content-Type: `multipart/form-data`
- Campo archivo: `file`
- Response `200`: `AnalysisResponse`
- Errores comunes:
  - `403` sin vinculo activo
  - `400` archivo vacio o invalido
  - `503` servicio de almacenamiento no disponible

## 5.7 Crear cita

- `POST /api/doctor/appointments`
- Request JSON:

```json
{
  "patient_user_id": "6612abc...",
  "title": "Control mensual",
  "date_time": "2026-05-02T14:30:00+00:00",
  "description": "Revision general"
}
```

- Response `200`: `AppointmentResponse` (status inicial `programada`)
- Error:
  - `403` sin vinculo activo

## 5.8 Listar citas del doctor

- `GET /api/doctor/appointments?status=programada`
- Valores permitidos de `status`:
  - `programada`
  - `realizada`
  - `cancelada`
- Response `200`: lista `AppointmentResponse`

## 5.9 Cambiar estado de cita

- `PATCH /api/doctor/appointments/{appointment_id}/status`
- Request JSON:

```json
{
  "status": "realizada"
}
```

- Valores permitidos de `status`:
  - `programada`
  - `realizada`
  - `cancelada`

- Response `200`: `AppointmentResponse`
- Error:
  - `404` cita no encontrada

## 6. Router paciente (`/api/patient`)

Todos requieren rol `paciente`.

## 6.1 Listar solicitudes pendientes

- `GET /api/patient/requests`
- Response `200`: lista `BindingResponse`

## 6.2 Responder solicitud

- `PATCH /api/patient/requests/{request_id}`
- Request JSON:

```json
{
  "action": "aceptar"
}
```

- Valores permitidos:
  - `aceptar`
  - `denegar`

- Response `200`: `BindingResponse`
- Errores comunes:
  - `400` accion invalida
  - `400` solicitud ya procesada
  - `404` solicitud no encontrada

## 6.3 Listar notificaciones

- `GET /api/patient/notifications?unread_only=true`
- Response `200`: lista `NotificationResponse`
- Tipos de notificacion:
  - `solicitud_medico`
  - `respuesta_solicitud`
  - `cita_programada`
  - `cita_actualizada`

## 6.4 Marcar notificacion como leida

- `PATCH /api/patient/notifications/{notification_id}/read`
- Response `200`:

```json
{
  "ok": true
}
```

- Error:
  - `404` notificacion no encontrada

## 6.5 Listar citas del paciente

- `GET /api/patient/appointments?status=programada`
- Valores permitidos de `status`:
  - `programada`
  - `realizada`
  - `cancelada`
- Response `200`: lista `AppointmentResponse`

## 7. Router admin usuarios (`/api/admin/users`)

Todos requieren rol `admin`.

## 7.1 Listar usuarios

- `GET /api/admin/users?role=doctor&status=true&skip=0&limit=50`
- Query params:
  - `role`: `paciente|doctor|admin`
  - `status`: `true|false`
  - `skip`: >= 0
  - `limit`: 1..200

- Response `200`:

```json
{
  "users": [
    {
      "id": "...",
      "username": "doctor1",
      "name": "Luis",
      "lastname": "Gomez",
      "email": "luis@mail.com",
      "role": "doctor",
      "status": true,
      "profile_image_url": "https://...",
      "created_at": "2026-04-13T10:00:00+00:00",
      "updated_at": "2026-04-13T10:00:00+00:00"
    }
  ],
  "total": 1
}
```

## 7.2 Crear usuario (solo doctor o admin)

- `POST /api/admin/users`
- Request JSON:

```json
{
  "username": "doctor2",
  "password": "claveSegura123",
  "name": "Maria",
  "lastname": "Lopez",
  "email": "maria@mail.com",
  "role": "doctor"
}
```

- Restriccion: no se permite crear `paciente` desde este endpoint.
- Response `201`: `UserResponse`

## 7.3 Obtener usuario por ID

- `GET /api/admin/users/{user_id}`
- Response `200`: `UserResponse`
- Error:
  - `404` usuario no encontrado

## 7.4 Actualizar usuario por ID

- `PATCH /api/admin/users/{user_id}`
- Request JSON (campos opcionales):

```json
{
  "name": "Maria Elena",
  "lastname": "Lopez",
  "password": "NuevaClave123",
  "status": true,
  "role": "admin"
}
```

- Restriccion: no permite dejar rol en `paciente`.
- Response `200`: `UserResponse`
- Error:
  - `404` usuario no encontrado
  - `400` rol invalido para gestion administrativa

## 8. Router admin citas (`/api/admin/citas`)

Todos requieren rol `admin`.

## 8.1 Listar citas globales

- `GET /api/admin/citas?status=programada&skip=0&limit=100`
- Query params:
  - `status`: `programada|realizada|cancelada`
  - `skip`: >= 0
  - `limit`: 1..200
- Response `200`:

```json
{
  "appointments": [
    {
      "id": "...",
      "doctor_user_id": "...",
      "patient_user_id": "...",
      "title": "Control mensual",
      "date_time": "2026-05-02T14:30:00+00:00",
      "description": "Revision general",
      "status": "programada",
      "created_at": "2026-04-13T10:00:00+00:00",
      "updated_at": "2026-04-13T10:00:00+00:00",
      "doctor_name": "Luis Gomez",
      "patient_name": "Ana Perez"
    }
  ],
  "total": 1
}
```

## 8.2 Cambiar estado de cita como admin

- `PATCH /api/admin/citas/{appointment_id}/status`
- Request JSON:

```json
{
  "status": "cancelada"
}
```

- Valores permitidos de `status`:
  - `programada`
  - `realizada`
  - `cancelada`

- Response `200`: `AppointmentResponse`
- Error:
  - `404` cita no encontrada

## 9. Integracion frontend web y movil

## 9.1 Cliente HTTP recomendado

1. Crear un cliente base con:
   - `baseURL`
   - timeout
   - interceptor para agregar `Authorization`
2. Guardar `access_token` de forma segura:
   - Web: almacenamiento seguro segun politica del proyecto (idealmente no exponer en localStorage si hay alternativa)
   - Movil: almacenamiento seguro del sistema (Keychain/Keystore)
3. Renovar sesion redirigiendo a login cuando llegue `401`.

## 9.2 Manejo de `multipart/form-data`

Endpoints con archivo:
- `/api/auth/me/photo`
- `/api/diagnoses/analyze`
- `/api/doctor/patients/{patient_user_id}/analyze`

En estos endpoints, enviar el archivo con nombre de campo exacto: `file`.

## 9.3 Flujos sugeridos por rol

### Paciente

1. Registro/Login
2. Ver y editar perfil
3. Analizar imagen propia
4. Consultar historial y detalle
5. Responder solicitudes de doctor
6. Revisar citas y notificaciones

### Doctor

1. Login
2. Buscar pacientes
3. Enviar solicitud de vinculacion
4. Ver pacientes asignados
5. Analizar para paciente vinculado
6. Crear/actualizar citas

### Admin

1. Login
2. Gestionar usuarios doctor/admin
3. Supervisar y actualizar estado de citas globales

## 9.4 CORS y entornos

El backend usa la variable de entorno `CORS_ALLOW_ORIGINS`.

- Ejemplo desarrollo:
  - `CORS_ALLOW_ORIGINS=http://localhost:3000,http://localhost:5173`
- Ejemplo abierto (no recomendado en produccion):
  - `CORS_ALLOW_ORIGINS=*`

Para produccion web, configura solo dominios permitidos.

## 10. Tipos y enums para frontend (TypeScript sugerido)

```ts
export type UserRole = "paciente" | "doctor" | "admin";

export type RequestStatus = "pendiente" | "aceptada" | "denegada";

export type AppointmentStatus = "programada" | "realizada" | "cancelada";

export type NotificationType =
  | "solicitud_medico"
  | "respuesta_solicitud"
  | "cita_programada"
  | "cita_actualizada";
```

## 11. Endpoints publicos auxiliares

- `GET /` retorna mensaje de bienvenida
- `GET /health` retorna `{ "status": "ok" }`

Estos endpoints no requieren token.

## 12. Notas de estabilidad para frontend

- Reintentos: para errores `503`, reintentar con backoff exponencial (p. ej. 3 intentos).
- Errores internos `500`: mostrar mensaje generico al usuario y registrar detalle en logging/observabilidad del frontend.
- Login: aun no hay rate-limiting en backend; se recomienda controlar intentos en frontend (UX) mientras se implementa del lado servidor.
