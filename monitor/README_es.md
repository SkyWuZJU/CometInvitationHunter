# Comet Invitation Hunter – Servicio de monitoreo en segundo plano

Este directorio contiene el servicio de monitoreo que busca continuamente en X (Twitter) publicaciones relacionadas con invitaciones al navegador Comet y envía notificaciones por correo a los usuarios verificados.

## Descripción general

El servicio de monitoreo sigue este flujo de trabajo:

1. **Búsqueda**: Realiza búsquedas en X utilizando múltiples palabras clave relacionadas con Comet simultáneamente.
2. **Eliminación de duplicados**: Quita las publicaciones repetidas obtenidas mediante distintas búsquedas.
3. **Clasificación**: Identifica si una publicación es de “compartición libre” (contiene enlaces directos) o “condicional” (requiere ciertas acciones).
4. **Almacenamiento**: Guarda en la base de datos las nuevas publicaciones con invitaciones.
5. **Notificación**: Envía notificaciones por correo agrupadas a todos los usuarios verificados.

## Componentes

### PostClassifier
- Clasifica las publicaciones como de compartición libre o condicional.
- Extrae los enlaces de invitación de aquellas publicaciones de compartición libre.
- Determina qué acciones son necesarias para las publicaciones condicionales.

### EmailNotifier  
- Genera notificaciones por correo en formato HTML y texto.
- Implementa lógica de reintentos con retroceso exponencial.
- Registra todos los intentos de envío de correos.

### CometMonitor
- Coordina todo el flujo de trabajo de monitoreo.
- Garantiza el funcionamiento continuo del servicio incluso ante errores.
- Gestiona los límites de uso de la API y las conexiones a la base de datos.

## Configuración

El servicio utiliza las siguientes variables de entorno:

```bash
# Obligatorias
UTOOLS_API_KEY=su_clave_de_api_de_utools
RESEND_API_KEY=su_clave_de_api_de_resend
FROM_EMAIL=su_correo_verificado@su_dominio.com

# Opcionales
MONITORING_INTERVAL=300  # segundos entre ciclos (por defecto: 5 minutos)
LOG_LEVEL=INFO
```

## Ejecución del servicio

### Entorno de desarrollo
```bash
# Desde la raíz del proyecto
python start_monitor.py
```

### Entorno de producción
```bash
# Definir las variables de entorno para producción
export UTOOLS_API_KEY="su_clave_de_producción"
export RESEND_API_KEY="su_clave_de_resend"
export FROM_EMAIL="su_correo_verificado@su_dominio.com"

# Ejecutar el servicio
python start_monitor.py
```

## Palabras clave de búsqueda

El servicio busca publicaciones que contengan:
- `perplexity.ai/browser/claim` (enlaces directos)
- `comet invitation`
- `comet invite`
- `comet browser invite`
- `comet access`
- `perplexity browser invite`
- `ai browser invite`

## Clasificación de publicaciones

### Publicaciones de compartición libre
- Contienen enlaces directos a invitaciones de Comet: `https://www.perplexity.ai/browser/claim/[CODE]`
- Los usuarios pueden usar inmediatamente dichos enlaces.
- Se almacenan junto con el enlace extraído.

### Publicaciones de compartición condicional
- Incluyen frases como “escríbanme por DM”, “siganme y escríbanme”, “comenten abajo”.
- Deben mencionar también términos relacionados con Comet.
- Se guardan junto con las condiciones o requisitos identificados.

## Notificaciones por correo

- Se envían tras cada ciclo de monitoreo si se han encontrado nuevas publicaciones.
- Un único correo incluye tanto publicaciones libres como condicionales.
- El formato es HTML e incluye enlaces directos a las publicaciones y a los enlaces de invitación.
- La lógica de reintentos permite superar fallos temporales en el envío de correos.

## Manejo de errores

- Límites de uso de la API: Se gestionan de forma elegante mediante pausas entre solicitudes.
- Fallos en la base de datos: Se aplican reintentos con retroceso exponencial.
- Fallos al enviar correos: Hasta 3 intentos por lote.
- Funcionamiento continuo: El servicio sigue operativo aunque ocurran errores aislados.

## Registro de logs

Todas las operaciones se registran con niveles apropiados:
- INFO: Operaciones normales, publicaciones encontradas, notificaciones enviadas.
- WARNING: Límites de uso alcanzados, intentos de reintento, configuraciones faltantes.
- ERROR: Operaciones fallidas, errores de API, problemas en la base de datos.
- DEBUG: Detalles sobre la lógica de clasificación y respuestas de la API.

## Pruebas

Para ejecutar el conjunto de pruebas:
```bash
# Pruebas unitarias
python backend/test_monitor.py

# Pruebas de integración  
python test_monitor_integration.py
```

## Esquema de la base de datos

El servicio utiliza las siguientes tablas:

- `posts`: Almacena las publicaciones procesadas con invitaciones.
- `users`: Direcciones de correo de los usuarios verificados.
- `email_logs`: Registra los lotes de notificaciones y su estado de envío.

## Cumplimiento de requisitos

Esta implementación satisface los siguientes requisitos:

- **2.1**: Realiza búsquedas en X usando múltiples palabras clave simultáneamente.
- **2.2**: Elimina duplicados entre los resultados de distintas búsquedas.  
- **2.3**: Clasifica las publicaciones como de compartición libre o condicional.
- **2.7**: Registra errores y mantiene el funcionamiento del servicio.
- **5.2**: Gestiona adecuadamente los límites de uso de la API.
- **5.3**: Implementa manejo de errores y registro de logs correctos.
- **5.6**: Realiza verificaciones de salud y reinicios de componentes.
