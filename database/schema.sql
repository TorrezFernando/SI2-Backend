-- ============================================================================
-- SCRIPT DDL GENERADO AUTOMATICAMENTE
-- Proyecto: Inmobiliaria Raices (Multi-Tenant)
-- Generado: 2026-09-15 20:00:52
-- ============================================================================
-- Este archivo se genera a partir de los modelos SQLAlchemy del proyecto.
-- No editar manualmente: modificar los modelos en su lugar y volver a
-- generar este script con: python generar_ddl.py > esquema.sql
-- ============================================================================

-- 1. Eliminacion de tablas en orden inverso a sus dependencias
DROP TABLE IF EXISTS pago CASCADE;
DROP TABLE IF EXISTS visita CASCADE;
DROP TABLE IF EXISTS imagen CASCADE;
DROP TABLE IF EXISTS contrato CASCADE;
DROP TABLE IF EXISTS caracteristica CASCADE;
DROP TABLE IF EXISTS propiedad CASCADE;
DROP TABLE IF EXISTS propietario CASCADE;
DROP TABLE IF EXISTS cliente CASCADE;
DROP TABLE IF EXISTS bitacora CASCADE;
DROP TABLE IF EXISTS agente CASCADE;
DROP TABLE IF EXISTS usuario CASCADE;
DROP TABLE IF EXISTS zona CASCADE;
DROP TABLE IF EXISTS tipo_inmueble CASCADE;
DROP TABLE IF EXISTS tenant CASCADE;
DROP TABLE IF EXISTS rol CASCADE;

-- 2. Creacion de tablas

-- Tabla: rol
CREATE TABLE rol (
	id_rol SERIAL NOT NULL, 
	nombre VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id_rol)
);

-- Tabla: tenant
CREATE TABLE tenant (
	id_tenant SERIAL NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	slug VARCHAR(100) NOT NULL, 
	plan VARCHAR(50) NOT NULL, 
	max_propiedades INTEGER NOT NULL, 
	estado BOOLEAN, 
	fecha_vencimiento_pago DATE, 
	fecha_creacion TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id_tenant)
);

-- Tabla: tipo_inmueble
CREATE TABLE tipo_inmueble (
	id_tipo_inmueble SERIAL NOT NULL, 
	nombre VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id_tipo_inmueble), 
	UNIQUE (nombre)
);

-- Tabla: zona
CREATE TABLE zona (
	id_zona SERIAL NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id_zona), 
	UNIQUE (nombre)
);

-- Tabla: usuario
CREATE TABLE usuario (
	id SERIAL NOT NULL, 
	ci VARCHAR(20) NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	correo VARCHAR(100) NOT NULL, 
	telefono VARCHAR(20), 
	id_rol INTEGER, 
	password_hash VARCHAR(255) NOT NULL, 
	id_tenant INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_usuario_tenant_correo UNIQUE (id_tenant, correo), 
	CONSTRAINT uq_usuario_tenant_ci UNIQUE (id_tenant, ci), 
	FOREIGN KEY(id_rol) REFERENCES rol (id_rol), 
	FOREIGN KEY(id_tenant) REFERENCES tenant (id_tenant)
);

-- Tabla: agente
CREATE TABLE agente (
	id_agente SERIAL NOT NULL, 
	id_usuario INTEGER NOT NULL, 
	PRIMARY KEY (id_agente), 
	UNIQUE (id_usuario), 
	FOREIGN KEY(id_usuario) REFERENCES usuario (id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Tabla: bitacora
CREATE TABLE bitacora (
	id_bitacora SERIAL NOT NULL, 
	id_usuario INTEGER NOT NULL, 
	id_tenant INTEGER NOT NULL, 
	accion VARCHAR(255) NOT NULL, 
	fecha_hora TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id_bitacora), 
	FOREIGN KEY(id_usuario) REFERENCES usuario (id) ON DELETE Restrict ON UPDATE CASCADE, 
	FOREIGN KEY(id_tenant) REFERENCES tenant (id_tenant) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Tabla: cliente
CREATE TABLE cliente (
	id_cliente SERIAL NOT NULL, 
	id_usuario INTEGER NOT NULL, 
	PRIMARY KEY (id_cliente), 
	UNIQUE (id_usuario), 
	FOREIGN KEY(id_usuario) REFERENCES usuario (id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Tabla: propietario
CREATE TABLE propietario (
	id_propietario SERIAL NOT NULL, 
	id_usuario INTEGER NOT NULL, 
	PRIMARY KEY (id_propietario), 
	UNIQUE (id_usuario), 
	FOREIGN KEY(id_usuario) REFERENCES usuario (id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Tabla: propiedad
CREATE TABLE propiedad (
	id_propiedad SERIAL NOT NULL, 
	id_propietario INTEGER NOT NULL, 
	id_agente INTEGER NOT NULL, 
	id_tipo_inmueble INTEGER NOT NULL, 
	id_zona INTEGER NOT NULL, 
	titulo VARCHAR(150) NOT NULL, 
	direccion VARCHAR(255) NOT NULL, 
	precio NUMERIC(12, 2) NOT NULL, 
	tipo_operacion VARCHAR(20) NOT NULL, 
	estado VARCHAR(20), 
	habitaciones INTEGER, 
	banos INTEGER, 
	superficie_m2 NUMERIC(10, 2), 
	garaje BOOLEAN, 
	antiguedad_anios INTEGER, 
	id_tenant INTEGER NOT NULL, 
	PRIMARY KEY (id_propiedad), 
	FOREIGN KEY(id_propietario) REFERENCES propietario (id_propietario) ON DELETE RESTRICT, 
	FOREIGN KEY(id_agente) REFERENCES agente (id_agente) ON DELETE RESTRICT, 
	FOREIGN KEY(id_tipo_inmueble) REFERENCES tipo_inmueble (id_tipo_inmueble) ON DELETE RESTRICT, 
	FOREIGN KEY(id_zona) REFERENCES zona (id_zona) ON DELETE RESTRICT, 
	FOREIGN KEY(id_tenant) REFERENCES tenant (id_tenant) ON DELETE RESTRICT
);

-- Tabla: caracteristica
CREATE TABLE caracteristica (
	id_caracteristica SERIAL NOT NULL, 
	id_propiedad INTEGER NOT NULL, 
	nombre VARCHAR(100) NOT NULL, 
	valor VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id_caracteristica), 
	FOREIGN KEY(id_propiedad) REFERENCES propiedad (id_propiedad) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Tabla: contrato
CREATE TABLE contrato (
	id_contrato SERIAL NOT NULL, 
	id_tenant INTEGER NOT NULL, 
	id_cliente INTEGER NOT NULL, 
	id_propiedad INTEGER NOT NULL, 
	id_agente INTEGER NOT NULL, 
	tipo_contrato VARCHAR(50) NOT NULL, 
	monto_total NUMERIC(12, 2) NOT NULL, 
	fecha_inicio DATE NOT NULL, 
	fecha_fin DATE, 
	PRIMARY KEY (id_contrato), 
	FOREIGN KEY(id_tenant) REFERENCES tenant (id_tenant) ON DELETE RESTRICT ON UPDATE CASCADE, 
	FOREIGN KEY(id_cliente) REFERENCES cliente (id_cliente) ON DELETE RESTRICT ON UPDATE CASCADE, 
	FOREIGN KEY(id_propiedad) REFERENCES propiedad (id_propiedad) ON DELETE RESTRICT ON UPDATE CASCADE, 
	FOREIGN KEY(id_agente) REFERENCES agente (id_agente) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Tabla: imagen
CREATE TABLE imagen (
	id_imagen SERIAL NOT NULL, 
	id_propiedad INTEGER NOT NULL, 
	url VARCHAR(255) NOT NULL, 
	PRIMARY KEY (id_imagen), 
	FOREIGN KEY(id_propiedad) REFERENCES propiedad (id_propiedad) ON DELETE CASCADE ON UPDATE CASCADE
);

-- Tabla: visita
CREATE TABLE visita (
	id_visita SERIAL NOT NULL, 
	id_tenant INTEGER NOT NULL, 
	id_cliente INTEGER NOT NULL, 
	id_propiedad INTEGER NOT NULL, 
	id_agente INTEGER NOT NULL, 
	fecha_hora TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	comentario TEXT, 
	estado VARCHAR(20), 
	PRIMARY KEY (id_visita), 
	FOREIGN KEY(id_tenant) REFERENCES tenant (id_tenant) ON DELETE RESTRICT ON UPDATE CASCADE, 
	FOREIGN KEY(id_cliente) REFERENCES cliente (id_cliente) ON DELETE RESTRICT ON UPDATE CASCADE, 
	FOREIGN KEY(id_propiedad) REFERENCES propiedad (id_propiedad) ON DELETE RESTRICT ON UPDATE CASCADE, 
	FOREIGN KEY(id_agente) REFERENCES agente (id_agente) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Tabla: pago
CREATE TABLE pago (
	id_pago SERIAL NOT NULL, 
	id_contrato INTEGER NOT NULL, 
	monto NUMERIC(12, 2) NOT NULL, 
	fecha_pago TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
	metodo_pago VARCHAR(50) NOT NULL, 
	numero_recibo VARCHAR(50), 
	PRIMARY KEY (id_pago), 
	FOREIGN KEY(id_contrato) REFERENCES contrato (id_contrato) ON DELETE RESTRICT ON UPDATE CASCADE
);

