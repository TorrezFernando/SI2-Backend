-- ============================================================================
-- SCRIPT DDL: BASE DE DATOS INMOBILIARIA RAICES
-- ============================================================================

-- 1. Eliminación de tablas en orden inverso a sus dependencias
DROP TABLE IF EXISTS pago CASCADE;
DROP TABLE IF EXISTS contrato CASCADE;
DROP TABLE IF EXISTS visita CASCADE;
DROP TABLE IF EXISTS caracteristica CASCADE;
DROP TABLE IF EXISTS imagen CASCADE;
DROP TABLE IF EXISTS propiedad CASCADE;
DROP TABLE IF EXISTS cliente CASCADE;
DROP TABLE IF EXISTS agente CASCADE;
DROP TABLE IF EXISTS propietario CASCADE;
DROP TABLE IF EXISTS bitacora CASCADE;
DROP TABLE IF EXISTS usuario CASCADE;
DROP TABLE IF EXISTS rol CASCADE;

-- 2. Tabla: Rol
CREATE TABLE rol (
    id_rol SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE
);

-- 3. Tabla: Usuario
CREATE TABLE usuario (
    ci VARCHAR(20) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    correo VARCHAR(100) UNIQUE NOT NULL,
    telefono VARCHAR(20),
    id_rol INT NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    CONSTRAINT fk_usuario_rol FOREIGN KEY (id_rol) 
        REFERENCES rol(id_rol) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- 4. Tabla: Bitacora
CREATE TABLE bitacora (
    id_bitacora SERIAL PRIMARY KEY,
    ci_usuario VARCHAR(20) NOT NULL,
    accion VARCHAR(255) NOT NULL,
    fecha_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_bitacora_usuario FOREIGN KEY (ci_usuario) 
        REFERENCES usuario(ci) ON UPDATE CASCADE ON DELETE CASCADE
);

-- 5. Tablas de Perfiles / Especialización
CREATE TABLE propietario (
    id_propietario SERIAL PRIMARY KEY,
    ci_usuario VARCHAR(20) UNIQUE NOT NULL,
    CONSTRAINT fk_propietario_usuario FOREIGN KEY (ci_usuario) 
        REFERENCES usuario(ci) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE agente (
    id_agente SERIAL PRIMARY KEY,
    ci_usuario VARCHAR(20) UNIQUE NOT NULL,
    CONSTRAINT fk_agente_usuario FOREIGN KEY (ci_usuario) 
        REFERENCES usuario(ci) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE cliente (
    id_cliente SERIAL PRIMARY KEY,
    ci_usuario VARCHAR(20) UNIQUE NOT NULL,
    CONSTRAINT fk_cliente_usuario FOREIGN KEY (ci_usuario) 
        REFERENCES usuario(ci) ON UPDATE CASCADE ON DELETE CASCADE
);

-- 6. Tabla: Propiedad
CREATE TABLE propiedad (
    id_propiedad SERIAL PRIMARY KEY,
    id_propietario INT NOT NULL,
    id_agente INT NOT NULL,
    titulo VARCHAR(150) NOT NULL,
    direccion VARCHAR(255) NOT NULL,
    precio NUMERIC(12, 2) NOT NULL,
    tipo_operacion VARCHAR(20) NOT NULL,
    estado VARCHAR(20) DEFAULT 'Disponible',
    CONSTRAINT fk_propiedad_propietario FOREIGN KEY (id_propietario) 
        REFERENCES propietario(id_propietario) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_propiedad_agente FOREIGN KEY (id_agente) 
        REFERENCES agente(id_agente) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- 7. Tabla: Imagen
CREATE TABLE imagen (
    id_imagen SERIAL PRIMARY KEY,
    id_propiedad INT NOT NULL,
    url VARCHAR(255) NOT NULL,
    CONSTRAINT fk_imagen_propiedad FOREIGN KEY (id_propiedad) 
        REFERENCES propiedad(id_propiedad) ON UPDATE CASCADE ON DELETE CASCADE
);

-- 8. Tabla: Caracteristica
CREATE TABLE caracteristica (
    id_caracteristica SERIAL PRIMARY KEY,
    id_propiedad INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    valor VARCHAR(100) NOT NULL,
    CONSTRAINT fk_caracteristica_propiedad FOREIGN KEY (id_propiedad) 
        REFERENCES propiedad(id_propiedad) ON UPDATE CASCADE ON DELETE CASCADE
);

-- 9. Tabla: Visita
CREATE TABLE visita (
    id_visita SERIAL PRIMARY KEY,
    id_cliente INT NOT NULL,
    id_propiedad INT NOT NULL,
    id_agente INT NOT NULL,
    fecha_hora TIMESTAMP NOT NULL,
    comentario TEXT,
    estado VARCHAR(20) DEFAULT 'Programada',
    CONSTRAINT fk_visita_cliente FOREIGN KEY (id_cliente) 
        REFERENCES cliente(id_cliente) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_visita_propiedad FOREIGN KEY (id_propiedad) 
        REFERENCES propiedad(id_propiedad) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_visita_agente FOREIGN KEY (id_agente) 
        REFERENCES agente(id_agente) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- 10. Tabla: Contrato
CREATE TABLE contrato (
    id_contrato SERIAL PRIMARY KEY,
    id_cliente INT NOT NULL,
    id_propiedad INT NOT NULL,
    id_agente INT NOT NULL,
    tipo_contrato VARCHAR(50) NOT NULL,
    monto_total NUMERIC(12, 2) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE,
    CONSTRAINT fk_contrato_cliente FOREIGN KEY (id_cliente) 
        REFERENCES cliente(id_cliente) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_contrato_propiedad FOREIGN KEY (id_propiedad) 
        REFERENCES propiedad(id_propiedad) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_contrato_agente FOREIGN KEY (id_agente) 
        REFERENCES agente(id_agente) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- 11. Tabla: Pago
CREATE TABLE pago (
    id_pago SERIAL PRIMARY KEY,
    id_contrato INT NOT NULL,
    monto NUMERIC(12, 2) NOT NULL,
    fecha_pago TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metodo_pago VARCHAR(50) NOT NULL,
    numero_recibo VARCHAR(50),
    CONSTRAINT fk_pago_contrato FOREIGN KEY (id_contrato) 
        REFERENCES contrato(id_contrato) ON UPDATE CASCADE ON DELETE RESTRICT
);

-- INSERCIÓN DE DATOS DE PRUEBA SPRINT 0
INSERT INTO rol (id_rol, nombre) VALUES (1, 'Administrador');
INSERT INTO rol (id_rol, nombre) VALUES (2, 'Agente Inmobiliario');
INSERT INTO rol (id_rol, nombre) VALUES (3, 'Propietario');
INSERT INTO rol (id_rol, nombre) VALUES (4, 'Cliente');

INSERT INTO usuario (ci, nombre, correo, telefono, id_rol, password_hash) 
VALUES ('1234567', 'Admin Raices', 'admin@raices.com', '77712345', 1, '$2b$12$/0NUEZXBsLWPtbyxs2.qp.HxhXGL4SOhkXwTSiwWHILk0BsVuJSta');
INSERT INTO usuario (ci, nombre, correo, telefono, id_rol, password_hash) 
VALUES ('2000000', 'Ana Agente', 'agente@raices.com', '70000001', 2, '$2b$12$fUZI/A/X3Tm.W74DIXi0n.OITkX8UOREpWBpF98oIJN05Bnvtmmde');
INSERT INTO usuario (ci, nombre, correo, telefono, id_rol, password_hash) 
VALUES ('3000000', 'Pablo Propietario', 'propietario@raices.com', '70000002', 3, '$2b$12$lt1xPF1n78s.whh6ZlvLa.rMhKO/Gxi5a98CEtoQOZCM0XWP7cJeq');
INSERT INTO usuario (ci, nombre, correo, telefono, id_rol, password_hash) 
VALUES ('4000000', 'Carlos Cliente', 'cliente@raices.com', '70000003', 4, '$2b$12$g71uaGPG1r.OfpdHi3MHi.NS6JW2ZoS7LnrhIw6Jl3NRzq146onnK');
