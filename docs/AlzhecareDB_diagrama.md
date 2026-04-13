// AlzheCare Database Schema
// Diseño visual de la base de datos para dbdiagram.io

Table user_roles {
  id SMALLSERIAL [pk, increment]
  code VARCHAR(20) [unique, not null]
}

Table users {
  id CHAR(36) [pk]
  username VARCHAR(40) [unique, not null]
  password_hash VARCHAR(255) [not null]
  name VARCHAR(80) [not null]
  lastname VARCHAR(80) [not null]
  email VARCHAR(255) [unique, not null]
  role_id SMALLINT [not null, ref: > user_roles.id]
  status BOOLEAN [not null, default: true]
  profile_image_key TEXT
  created_at TIMESTAMPTZ [not null]
  updated_at TIMESTAMPTZ [not null]
}

Table diagnosis_statuses {
  code VARCHAR(20) [pk]
}

Table diagnoses {
  id CHAR(36) [pk]
  user_id CHAR(36) [not null, ref: > users.id]
  result VARCHAR(120) [not null]
  confidence DOUBLE  [not null]
  status VARCHAR(20) [not null, ref: > diagnosis_statuses.code]
  image_s3_key TEXT [not null]
  image_url TEXT [not null]
  model_output TEXT [not null, default: "{}"]
  created_at TIMESTAMPTZ [not null]
  updated_at TIMESTAMPTZ [not null]
  
  Indexes {
    (user_id, created_at) []
  }
}

Table doctor_patient_link_statuses {
  code VARCHAR(20) [pk]
}

Table doctor_patient_links {
  id CHAR(36) [pk]
  doctor_user_id CHAR(36) [not null, ref: > users.id]
  patient_user_id CHAR(36) [not null, ref: > users.id]
  status VARCHAR(20) [not null, ref: > doctor_patient_link_statuses.code]
  created_at TIMESTAMPTZ [not null]
  updated_at TIMESTAMPTZ [not null]
  
  Indexes {
    (doctor_user_id, patient_user_id) [unique]
    doctor_user_id
    patient_user_id
  }
}

Table doctor_request_statuses {
  code VARCHAR(20) [pk]
}

Table doctor_requests {
  id CHAR(36) [pk]
  doctor_user_id CHAR(36) [not null, ref: > users.id]
  patient_user_id CHAR(36) [not null, ref: > users.id]
  status VARCHAR(20) [not null, ref: > doctor_request_statuses.code]
  created_at TIMESTAMPTZ [not null]
  updated_at TIMESTAMPTZ [not null]
  
  Indexes {
    (doctor_user_id, created_at) []
    (patient_user_id, status, created_at) []
  }
}

Table appointment_statuses {
  code VARCHAR(20) [pk]
}

Table appointments {
  id CHAR(36) [pk]
  doctor_user_id CHAR(36) [not null, ref: > users.id]
  patient_user_id CHAR(36) [not null, ref: > users.id]
  title VARCHAR(120) [not null]
  date_time TIMESTAMPTZ [not null]
  description VARCHAR(500) [not null]
  status VARCHAR(20) [not null, ref: > appointment_statuses.code]
  created_at TIMESTAMPTZ [not null]
  updated_at TIMESTAMPTZ [not null]
  
  Indexes {
    (doctor_user_id, date_time) []
    (patient_user_id, date_time) []
    (status, created_at) []
  }
}

Table notification_types {
  code VARCHAR(40) [pk]
}

Table notifications {
  id CHAR(36) [pk]
  user_id CHAR(36) [not null, ref: > users.id]
  type VARCHAR(40) [not null, ref: > notification_types.code]
  title VARCHAR(180) [not null]
  message TEXT [not null]
  data TEXT [not null, default: "{}"]
  read BOOLEAN [not null, default: false]
  created_at TIMESTAMPTZ [not null]
  
  Indexes {
    (user_id, created_at) []
    (user_id, read)
  }
}

// Valores que solo ingresan manualmente:
// 
// user_roles: ('paciente'), ('doctor'), ('admin')
// diagnosis_statuses: ('completado'), ('pendiente')
// doctor_patient_link_statuses: ('activo')
// doctor_request_statuses: ('pendiente'), ('aceptada'), ('denegada')
// appointment_statuses: ('programada'), ('realizada'), ('cancelada')
// notification_types: ('solicitud_medico'), ('respuesta_solicitud'), ('cita_programada'), ('cita_actualizada')

Ref: "users"."id" < "users"."name"