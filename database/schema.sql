-- ============================================================================
-- SCRIPT DE SEMILLA (SEED)
-- ============================================================================

-- INSERCIÓN DE DATOS DE PRUEBA (SEED)
INSERT INTO empresa (id_empresa, nombre, dominio) VALUES (1, 'Raíces Inmobiliaria', 'raices.com');
INSERT INTO empresa (id_empresa, nombre, dominio) VALUES (2, 'Horizonte Bienes Raíces', 'horizonte.com');

-- Roles Base (Globales) e Inyectados
INSERT INTO rol (id_rol, id_empresa, nombre) VALUES (1, NULL, 'Super Administrador');
INSERT INTO rol (id_rol, id_empresa, nombre) VALUES (2, NULL, 'Administrador de Empresa');
INSERT INTO rol (id_rol, id_empresa, nombre) VALUES (3, 1, 'Agente Raíces');
INSERT INTO rol (id_rol, id_empresa, nombre) VALUES (4, 1, 'Cliente Raíces');

-- Permisos (Componentes del Sistema)
INSERT INTO permiso (id_permiso, codigo, descripcion, tipo) VALUES (1, 'UI:MENU_CATALOGO', 'Ver menú de catálogo de propiedades', 'UI_Menu');
INSERT INTO permiso (id_permiso, codigo, descripcion, tipo) VALUES (2, 'UI:BTN_CREAR_PROP', 'Botón para crear una nueva propiedad', 'UI_Boton');
INSERT INTO permiso (id_permiso, codigo, descripcion, tipo) VALUES (3, 'UI:BTN_ELIMINAR_PROP', 'Botón para eliminar propiedad', 'UI_Boton');
INSERT INTO permiso (id_permiso, codigo, descripcion, tipo) VALUES (4, 'API:USUARIOS_CREAR', 'Permiso para crear usuarios', 'Endpoint');

-- Asignación de Permisos a Roles
-- Super Admin lo ve todo
INSERT INTO rol_permiso (id_rol, id_permiso) VALUES (1, 1), (1, 2), (1, 3), (1, 4);
-- Admin de Empresa
INSERT INTO rol_permiso (id_rol, id_permiso) VALUES (2, 1), (2, 2), (2, 3), (2, 4);
-- Agente (Solo crea y ve catálogo, no elimina)
INSERT INTO rol_permiso (id_rol, id_permiso) VALUES (3, 1), (3, 2);

-- Usuarios
-- Super Admin Global (Sin empresa)
INSERT INTO usuario (ci, id_empresa, nombre, correo, telefono, id_rol, password_hash) 
VALUES ('0000000', NULL, 'Super Admin', 'super@saas.com', '70000000', 1, '$2b$12$7jO3MSeR/WQ.QwZBqjICBegD.WQpCS3D5yq23NQYj6BVS5zyAk5pG');

-- Admin Empresa 1
INSERT INTO usuario (ci, id_empresa, nombre, correo, telefono, id_rol, password_hash) 
VALUES ('1234567', 1, 'Admin Raices', 'admin@raices.com', '77712345', 2, '$2b$12$7jO3MSeR/WQ.QwZBqjICBegD.WQpCS3D5yq23NQYj6BVS5zyAk5pG');

-- Agente Empresa 1
INSERT INTO usuario (ci, id_empresa, nombre, correo, telefono, id_rol, password_hash) 
VALUES ('2000000', 1, 'Ana Agente', 'agente@raices.com', '70000001', 3, '$2b$12$7jO3MSeR/WQ.QwZBqjICBegD.WQpCS3D5yq23NQYj6BVS5zyAk5pG');
