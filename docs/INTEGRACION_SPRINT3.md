# APIs Sprint 3 para web y móvil

Backend actualizado en `sprint-3`. OpenAPI exportado en `docs/openapi.json`. Con el backend iniciado: `/openapi.json` y `/docs`. Autenticación Bearer JWT. Todos los recursos se restringen a la empresa del usuario autenticado; los clientes solo consultan sus propios contratos y recibos. No se modificó Flutter.

## Instalación

Instalar `requirements.txt` y reiniciar `uvicorn main:app`. La inicialización crea tablas adicionales sin borrar datos existentes. Variables en `.env.example`: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD (contraseña de aplicación para Gmail), GOOGLE_APPLICATION_CREDENTIALS (ruta al JSON privado de Firebase). No guardar credenciales en el repositorio. Se necesita una JWT_SECRET_KEY válida para iniciar.

## Endpoints

| Método | Ruta | Acceso / comportamiento |
|---|---|---|
| POST | /api/ia/tasaciones | Usuario Premium; body id_propiedad; responde minimo, estimado, maximo, explicacion |
| POST | /api/contratos | Administrador; crea contrato y cuotas mensuales |
| GET | /api/contratos | Administrador; cuentas de su empresa |
| GET | /api/mi-cuenta | Contratos, saldos, cuotas y pagos del cliente autenticado |
| GET | /api/contratos/{cid}/cuotas | Administrador de empresa o titular del contrato |
| POST | /api/cuotas/{qid}/pagos | Administrador; abono simulado, idempotente |
| GET | /api/pagos/{pid}/recibo.pdf | PDF descargable por administrador o titular |
| POST | /api/pagos/{pid}/enviar-recibo | Envía PDF únicamente al correo registrado del cliente |
| PUT | /api/notificaciones/tokens | Alta o rotación del token de un dispositivo del usuario |
| GET | /api/notificaciones/tokens | Dispositivos propios sin revelar sus tokens |
| DELETE | /api/notificaciones/tokens/{ident} | Baja del dispositivo propio |
| POST | /api/notificaciones/procesar | Administrador: procesa recordatorios de cuotas de su empresa |

Ejemplo de alta de contrato (monto_total es el total acordado de todo el contrato, no una renta mensual):

```json
{"id_cliente":1,"id_propiedad":1,"id_agente":1,"tipo_contrato":"Alquiler","monto_total":"12000.00","fecha_inicio":"2026-11-01","cuotas":12,"primer_vencimiento":"2026-11-01"}
```

Abono:

```json
{"monto":"1000.00","clave_idempotencia":"identificador-unico-operacion","confirma_simulacion":true}
```

Reutilizar la misma clave con idénticos datos permite reintentar sin duplicar el pago; cambiar los datos con la misma clave devuelve 409. Los importes se manejan como decimales; los clientes deben admitir cadenas decimales en las respuestas. Todas las operaciones mantienen la unidad monetaria de los importes registrados; no hay conversión de moneda. Se impide abonar por encima del saldo de la cuota o del contrato. Los pagos anteriores sin vínculo a cuota se incluyen en el saldo total, pero no se asignan automáticamente a cuotas. Los contratos anteriores sin cronograma indican cronograma_disponible=false; no se inventan fechas ni cuotas históricas.

Token FCM (el cliente obtiene su token del SDK Firebase con consentimiento de notificaciones):

```json
{"dispositivo":"identificador-estable-del-dispositivo","token":"TOKEN_FCM_REAL","plataforma":"android"}
```

PUT devuelve id, dispositivo y plataforma. Guardar el id para DELETE al cerrar sesión o desactivar notificaciones. La rotación usa el mismo dispositivo. Un token vinculado a otra cuenta/dispositivo requiere baja previa y devuelve 409. El frontend web de esta entrega permite procesar recordatorios; la obtención del token mediante SDK/service worker y el permiso del navegador quedan para la integración del cliente, igual que en móvil.

## IA y notificaciones

La tasación usa al menos tres anuncios internos de igual zona, tipo y operación. No es una tasación certificada ni utiliza ventas verificadas o fuentes de mercado externas. Normal y Pro reciben 403; Premium accede sujeto a disponibilidad y cuota de Gemini. Faltan comparables: 422; Gemini no configurado: 503; respuesta inválida/proveedor fallido: 502. El modelo se configura en GEMINI_MODEL.

ENABLE_FCM_SCHEDULER=true habilita revisión horaria de cuotas con vencimiento hasta dentro de siete días, incluidas vencidas, y saldo pendiente. Activar en un solo worker. Cada dispositivo recibe como máximo un aviso por cuota y día cuando el proveedor confirma el envío. Los fallos permanecen pendientes de reintento. Hay una pequeña ventana de duplicación si el proceso termina después del envío antes de guardar su confirmación. El planificador necesita backend en ejecución. La respuesta manual informa enviados/fallidos; sin Firebase configurado responde 503. No hay confirmación de lectura ni garantía de entrega al dispositivo. Los tokens inválidos deben actualizarse o darse de baja desde el cliente.

SMTP exige STARTTLS. La respuesta aceptado_por_smtp confirma aceptación del servidor, no llegada a la bandeja. Sin configuración: 503; fallo SMTP: 502. No hay envío automático al registrar el abono; se solicita explícitamente con el endpoint de envío. Todos los abonos y recibos nuevos son simulados, sin cobro bancario ni validez fiscal.

## Verificación

`venv/Scripts/python.exe tests/test_operaciones.py`: siete pruebas con SQLite en memoria y servicios externos simulados. Incluyen aislamiento, cuotas en meses cortos, importes pequeños, idempotencia, sobrepago, PDF, correo, rotación/baja de tokens y recordatorios deduplicados. La web compila en producción. No se efectuaron envíos reales ni una tasación contra Gemini. Promociones CU-25 y comisiones CU-29 siguen pendientes para la siguiente entrega.

Para actualizar el archivo OpenAPI: `venv/Scripts/python.exe scripts/export_openapi.py`. El exportador usa una base en memoria y no modifica la base de desarrollo.
