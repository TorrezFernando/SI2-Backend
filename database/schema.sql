-- ============================================================================
-- SCRIPT DE SEMILLA (SEED) MULTITENANT
-- ============================================================================

-- INSERCIÓN DE EMPRESAS
INSERT INTO empresa (id_empresa, nombre, dominio) VALUES 
(1, 'Raíces Inmobiliaria', 'raices.com'),
(2, 'Horizonte Bienes Raíces', 'horizonte.com'),
(3, 'Cúspide Propiedades', 'cuspide.com');

-- ROLES
INSERT INTO rol (id_rol, id_empresa, nombre) VALUES 
(1, NULL, 'Super Administrador'),
(2, NULL, 'Administrador de Empresa'),
(3, 1, 'Agente Raíces'),
(4, 1, 'Cliente Raíces'),
(5, 2, 'Agente Horizonte'),
(6, 2, 'Cliente Horizonte'),
(7, 3, 'Agente Cúspide'),
(8, 3, 'Cliente Cúspide');

-- PERMISOS
INSERT INTO permiso (id_permiso, codigo, descripcion, tipo) VALUES 
(1, 'UI:MENU_CATALOGO', 'Ver menú de catálogo de propiedades', 'UI_Menu'),
(2, 'UI:BTN_CREAR_PROP', 'Botón para crear una nueva propiedad', 'UI_Boton'),
(3, 'UI:BTN_ELIMINAR_PROP', 'Botón para eliminar propiedad', 'UI_Boton'),
(4, 'API:USUARIOS_CREAR', 'Permiso para crear usuarios', 'Endpoint');

-- ROL_PERMISO
-- Super Admin lo ve todo
INSERT INTO rol_permiso (id_rol, id_permiso) VALUES (1, 1), (1, 2), (1, 3), (1, 4);
-- Admin de Empresa
INSERT INTO rol_permiso (id_rol, id_permiso) VALUES (2, 1), (2, 2), (2, 3), (2, 4);
-- Agentes (Solo crean y ven catálogo)
INSERT INTO rol_permiso (id_rol, id_permiso) VALUES (3, 1), (3, 2), (5, 1), (5, 2), (7, 1), (7, 2);

-- USUARIOS
-- Super Admin
INSERT INTO usuario (ci, id_empresa, nombre, correo, telefono, id_rol, password_hash) 
VALUES ('0000000', NULL, 'Super Admin', 'super@saas.com', '70000000', 1, '$2b$12$7jO3MSeR/WQ.QwZBqjICBegD.WQpCS3D5yq23NQYj6BVS5zyAk5pG');

-- Empresa 1: Raíces
INSERT INTO usuario (ci, id_empresa, nombre, correo, telefono, id_rol, password_hash) 
VALUES 
('1000001', 1, 'Admin Raices', 'admin@raices.com', '77712345', 2, '$2b$12$7jO3MSeR/WQ.QwZBqjICBegD.WQpCS3D5yq23NQYj6BVS5zyAk5pG'),
('1000002', 1, 'Ana Agente', 'agente@raices.com', '70000001', 3, '$2b$12$7jO3MSeR/WQ.QwZBqjICBegD.WQpCS3D5yq23NQYj6BVS5zyAk5pG'),
('1000003', 1, 'Pablo Propietario', 'propietario@raices.com', '70000002', 4, '$2b$12$7jO3MSeR/WQ.QwZBqjICBegD.WQpCS3D5yq23NQYj6BVS5zyAk5pG'),
('1000004', 1, 'Carlos Cliente', 'cliente@raices.com', '70000003', 4, '$2b$12$7jO3MSeR/WQ.QwZBqjICBegD.WQpCS3D5yq23NQYj6BVS5zyAk5pG');

-- Empresa 2: Horizonte
INSERT INTO usuario (ci, id_empresa, nombre, correo, telefono, id_rol, password_hash) 
VALUES 
('2000001', 2, 'Admin Horizonte', 'admin@horizonte.com', '77720001', 2, '$2b$12$7jO3MSeR/WQ.QwZBqjICBegD.WQpCS3D5yq23NQYj6BVS5zyAk5pG'),
('2000002', 2, 'Luis Agente', 'agente@horizonte.com', '70000011', 5, '$2b$12$7jO3MSeR/WQ.QwZBqjICBegD.WQpCS3D5yq23NQYj6BVS5zyAk5pG'),
('2000003', 2, 'Maria Propietario', 'propietario@horizonte.com', '70000012', 6, '$2b$12$7jO3MSeR/WQ.QwZBqjICBegD.WQpCS3D5yq23NQYj6BVS5zyAk5pG'),
('2000004', 2, 'Jose Cliente', 'cliente@horizonte.com', '70000013', 6, '$2b$12$7jO3MSeR/WQ.QwZBqjICBegD.WQpCS3D5yq23NQYj6BVS5zyAk5pG');

-- Empresa 3: Cúspide
INSERT INTO usuario (ci, id_empresa, nombre, correo, telefono, id_rol, password_hash) 
VALUES 
('3000001', 3, 'Admin Cuspide', 'admin@cuspide.com', '77730001', 2, '$2b$12$7jO3MSeR/WQ.QwZBqjICBegD.WQpCS3D5yq23NQYj6BVS5zyAk5pG'),
('3000002', 3, 'Marta Agente', 'agente@cuspide.com', '70000021', 7, '$2b$12$7jO3MSeR/WQ.QwZBqjICBegD.WQpCS3D5yq23NQYj6BVS5zyAk5pG'),
('3000003', 3, 'Jorge Propietario', 'propietario@cuspide.com', '70000022', 8, '$2b$12$7jO3MSeR/WQ.QwZBqjICBegD.WQpCS3D5yq23NQYj6BVS5zyAk5pG'),
('3000004', 3, 'Sofia Cliente', 'cliente@cuspide.com', '70000023', 8, '$2b$12$7jO3MSeR/WQ.QwZBqjICBegD.WQpCS3D5yq23NQYj6BVS5zyAk5pG');

-- PROPIETARIOS, AGENTES, CLIENTES
-- Empresa 1
INSERT INTO propietario (id_propietario, ci_usuario, id_empresa) VALUES (1, '1000003', 1);
INSERT INTO agente (id_agente, ci_usuario, id_empresa) VALUES (1, '1000002', 1);
INSERT INTO cliente (id_cliente, ci_usuario, id_empresa) VALUES (1, '1000004', 1);

-- Empresa 2
INSERT INTO propietario (id_propietario, ci_usuario, id_empresa) VALUES (2, '2000003', 2);
INSERT INTO agente (id_agente, ci_usuario, id_empresa) VALUES (2, '2000002', 2);
INSERT INTO cliente (id_cliente, ci_usuario, id_empresa) VALUES (2, '2000004', 2);

-- Empresa 3
INSERT INTO propietario (id_propietario, ci_usuario, id_empresa) VALUES (3, '3000003', 3);
INSERT INTO agente (id_agente, ci_usuario, id_empresa) VALUES (3, '3000002', 3);
INSERT INTO cliente (id_cliente, ci_usuario, id_empresa) VALUES (3, '3000004', 3);

-- PROPIEDADES
INSERT INTO propiedad (id_propiedad, id_empresa, id_propietario, id_agente, titulo, direccion, precio, tipo_operacion, estado) VALUES 
(1, 1, 1, 1, 'Hermosa Casa en Equipetrol', 'Av. San Martin, 3er Anillo Interno', 250000.00, 'Venta', 'Disponible'),
(2, 1, 1, 1, 'Departamento de Lujo en Urubo', 'Condominio Urubo Golf', 1200.00, 'Alquiler', 'Disponible'),
(3, 1, 1, 1, 'Local Comercial Centro', 'Calle 24 de Septiembre', 30000.00, 'Anticretico', 'Disponible'),

(4, 2, 2, 2, 'Casa Quinta en La Guardia', 'Km 20 Carretera Antigua', 180000.00, 'Venta', 'Disponible'),
(5, 2, 2, 2, 'Monoambiente en Sirari', 'Calle Las Begonias', 400.00, 'Alquiler', 'Reservada'),
(6, 2, 2, 2, 'Oficina Equipetrol Norte', 'Av. Canal Isuto', 800.00, 'Alquiler', 'Disponible'),

(7, 3, 3, 3, 'Casa Minimalista en Las Palmas', 'Calle Los Sauces', 320000.00, 'Venta', 'Disponible'),
(8, 3, 3, 3, 'Duplex Zona Sur', 'Santos Dumont 4to Anillo', 600.00, 'Alquiler', 'Disponible'),
(9, 3, 3, 3, 'Terreno en el Urubo', 'Urubo Village', 85000.00, 'Venta', 'Vendida');

-- CARACTERISTICAS
INSERT INTO caracteristica (id_caracteristica, id_propiedad, nombre, valor) VALUES 
(1, 1, 'Cuartos', '4'), (2, 1, 'Baños', '3'), (3, 1, 'Metros Cuadrados', '350'), (4, 1, 'Amoblado', 'No'), (5, 1, 'Agua', 'Sí'), (6, 1, 'Luz', 'Sí'),
(7, 2, 'Cuartos', '2'), (8, 2, 'Baños', '2'), (9, 2, 'Metros Cuadrados', '120'), (10, 2, 'Amoblado', 'Sí'), (11, 2, 'Agua', 'Sí'), (12, 2, 'Luz', 'Sí'),
(13, 3, 'Cuartos', '1'), (14, 3, 'Baños', '1'), (15, 3, 'Metros Cuadrados', '50'), (16, 3, 'Amoblado', 'No'), (17, 3, 'Agua', 'Sí'), (18, 3, 'Luz', 'Sí'),

(19, 4, 'Cuartos', '5'), (20, 4, 'Baños', '4'), (21, 4, 'Metros Cuadrados', '1200'), (22, 4, 'Amoblado', 'No'), (23, 4, 'Agua', 'Sí'), (24, 4, 'Luz', 'Sí'),
(25, 5, 'Cuartos', '1'), (26, 5, 'Baños', '1'), (27, 5, 'Metros Cuadrados', '45'), (28, 5, 'Amoblado', 'Sí'), (29, 5, 'Agua', 'Sí'), (30, 5, 'Luz', 'Sí'),

(31, 7, 'Cuartos', '3'), (32, 7, 'Baños', '3'), (33, 7, 'Metros Cuadrados', '400'), (34, 7, 'Amoblado', 'Sí'), (35, 7, 'Agua', 'Sí'), (36, 7, 'Luz', 'Sí'),
(37, 8, 'Cuartos', '2'), (38, 8, 'Baños', '2'), (39, 8, 'Metros Cuadrados', '150'), (40, 8, 'Amoblado', 'No'), (41, 8, 'Agua', 'Sí'), (42, 8, 'Luz', 'Sí');

-- IMAGENES (Plaseholders reales)
INSERT INTO imagen (id_imagen, id_propiedad, url) VALUES 
(1, 1, 'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=800'),
(2, 1, 'https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?w=800'),
(3, 2, 'https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?w=800'),
(4, 3, 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=800'),
(5, 4, 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800'),
(6, 5, 'https://images.unsplash.com/photo-1536376072261-38c75010e6c9?w=800'),
(7, 6, 'https://images.unsplash.com/photo-1497366811353-6870744d04b2?w=800'),
(8, 7, 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800'),
(9, 8, 'https://images.unsplash.com/photo-1502672260266-1c1de24244e3?w=800'),
(10, 9, 'https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800');

