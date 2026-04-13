# SQL Migration Mapping

## Main entities extracted from schemas

- users
- diagnoses
- doctor_requests
- doctor_patient_links
- appointments
- notifications

## Field naming migration (Spanish -> English)

- users.nombre -> users.name
- users.apellido -> users.lastname
- users.estado -> users.status
- doctor_requests.estado -> doctor_requests.status
- doctor_patient_links.estado -> doctor_patient_links.status
- appointments.titulo -> appointments.title
- appointments.fecha_hora -> appointments.date_time
- appointments.descripcion -> appointments.description
- appointments.estado -> appointments.status
- notifications.tipo -> notifications.type
- notifications.titulo -> notifications.title
- notifications.mensaje -> notifications.message
- notifications.leida -> notifications.read

## Allowed status values to preserve

- diagnosis status: completado, pendiente
- doctor request status: pendiente, aceptada, denegada
- doctor-patient link status: activo
- appointment status: programada, realizada, cancelada

## Notes

- The normalized SQL schema is in app/db/schema_normalized.sql.
- Status values remain in Spanish by design.
- Identifier names for code, models, and columns are standardized to English.
