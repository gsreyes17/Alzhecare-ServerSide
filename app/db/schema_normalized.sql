-- Normalized relational schema for AlzheCare backend
-- Keeps business status values in Spanish as requested.

CREATE TABLE user_roles (
    id SMALLSERIAL PRIMARY KEY,
    code VARCHAR(20) NOT NULL UNIQUE
);

INSERT INTO user_roles (code) VALUES ('paciente');
INSERT INTO user_roles (code) VALUES ('doctor');
INSERT INTO user_roles (code) VALUES ('admin');

CREATE TABLE users (
    id CHAR(36) PRIMARY KEY,
    username VARCHAR(40) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(80) NOT NULL,
    lastname VARCHAR(80) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    role_id SMALLINT NOT NULL REFERENCES user_roles(id),
    status BOOLEAN NOT NULL DEFAULT TRUE,
    profile_image_key TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE diagnosis_statuses (
    code VARCHAR(20) PRIMARY KEY
);

INSERT INTO diagnosis_statuses (code) VALUES ('completado');
INSERT INTO diagnosis_statuses (code) VALUES ('pendiente');

CREATE TABLE diagnoses (
    id CHAR(36) PRIMARY KEY,
    user_id CHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    result VARCHAR(120) NOT NULL,
    confidence DOUBLE PRECISION NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    status VARCHAR(20) NOT NULL REFERENCES diagnosis_statuses(code),
    image_s3_key TEXT NOT NULL,
    image_url TEXT NOT NULL,
    model_output TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_diagnoses_user_created_at ON diagnoses(user_id, created_at DESC);

CREATE TABLE doctor_patient_link_statuses (
    code VARCHAR(20) PRIMARY KEY
);

INSERT INTO doctor_patient_link_statuses (code) VALUES ('activo');

CREATE TABLE doctor_patient_links (
    id CHAR(36) PRIMARY KEY,
    doctor_user_id CHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    patient_user_id CHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL REFERENCES doctor_patient_link_statuses(code),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE (doctor_user_id, patient_user_id)
);

CREATE INDEX idx_doctor_patient_links_doctor ON doctor_patient_links(doctor_user_id);
CREATE INDEX idx_doctor_patient_links_patient ON doctor_patient_links(patient_user_id);

CREATE TABLE doctor_request_statuses (
    code VARCHAR(20) PRIMARY KEY
);

INSERT INTO doctor_request_statuses (code) VALUES ('pendiente');
INSERT INTO doctor_request_statuses (code) VALUES ('aceptada');
INSERT INTO doctor_request_statuses (code) VALUES ('denegada');

CREATE TABLE doctor_requests (
    id CHAR(36) PRIMARY KEY,
    doctor_user_id CHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    patient_user_id CHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL REFERENCES doctor_request_statuses(code),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_doctor_requests_doctor_created ON doctor_requests(doctor_user_id, created_at DESC);
CREATE INDEX idx_doctor_requests_patient_status_created ON doctor_requests(patient_user_id, status, created_at DESC);

CREATE TABLE appointment_statuses (
    code VARCHAR(20) PRIMARY KEY
);

INSERT INTO appointment_statuses (code) VALUES ('programada');
INSERT INTO appointment_statuses (code) VALUES ('realizada');
INSERT INTO appointment_statuses (code) VALUES ('cancelada');

CREATE TABLE appointments (
    id CHAR(36) PRIMARY KEY,
    doctor_user_id CHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    patient_user_id CHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(120) NOT NULL,
    date_time TIMESTAMPTZ NOT NULL,
    description VARCHAR(500) NOT NULL,
    status VARCHAR(20) NOT NULL REFERENCES appointment_statuses(code),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_appointments_doctor_date ON appointments(doctor_user_id, date_time DESC);
CREATE INDEX idx_appointments_patient_date ON appointments(patient_user_id, date_time DESC);
CREATE INDEX idx_appointments_status_created ON appointments(status, created_at DESC);

CREATE TABLE notification_types (
    code VARCHAR(40) PRIMARY KEY
);

INSERT INTO notification_types (code) VALUES ('solicitud_medico');
INSERT INTO notification_types (code) VALUES ('respuesta_solicitud');
INSERT INTO notification_types (code) VALUES ('cita_programada');
INSERT INTO notification_types (code) VALUES ('cita_actualizada');

CREATE TABLE notifications (
    id CHAR(36) PRIMARY KEY,
    user_id CHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(40) NOT NULL REFERENCES notification_types(code),
    title VARCHAR(180) NOT NULL,
    message TEXT NOT NULL,
    data TEXT NOT NULL DEFAULT '{}',
    read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_notifications_user_created ON notifications(user_id, created_at DESC);
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, read);
