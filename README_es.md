# Comet Invitation Hunter

Un sistema para monitorear Twitter en busca de códigos de invitación y responder a ellos automáticamente.

## Estructura del proyecto

```
├── backend/          # Servicio backend basado en FastAPI
├── frontend/         # Interfaz web desarrollada con TypeScript/Vite
├── monitor/          # Servicio de monitoreo en segundo plano
├── config/           # Archivos de configuración del entorno
└── setup_env.sh      # Script para configurar el entorno
```

## Configuración inicial

1. Ejecute el script de configuración para crear el entorno virtual de Python:
   ```bash
   ./setup_env.sh
   ```

2. Instale las dependencias del frontend:
   ```bash
   cd frontend
   npm install
   ```

## Desarrollo

1. Active el entorno virtual de Python:
   ```bash
   source venv/bin/activate
   ```

2. Inicie el servidor backend:
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```

3. Inicie el servidor de desarrollo del frontend:
   ```bash
   cd frontend
   npm run dev
   ```

## Configuración

- Entorno de desarrollo: `config/development.env`
- Entorno de producción: `config/production.env`

## Despliegue en producción

Archivos relevantes:
- Dockerfile: Configuración de un contenedor ligero.
- docker-compose.yml: Orquestación de los servicios.
- nginx.conf: Configuración del proxy inverso.
- deploy.sh: Script que permite desplegar el sistema con un solo comando.
- deploy/production-setup.md: Guía completa para la configuración en producción.

Características principales:
- Utiliza SQLite por su simplicidad (no se requiere base de datos externa).
- Un único contenedor Docker para el backend.
- Nginx sirve la interfaz web y redirige las solicitudes a la API.
- Las actualizaciones se realizan manualmente mediante `./deploy.sh`.
- El sistema está configurado para operar en `comethunter.skywu.me`.

Pasos para el despliegue:
1. Suba los archivos al servidor Linux.
2. Ejecute `./deploy.sh`.
3. Configure el certificado SSL usando `certbot --nginx -d comethunter.skywu.me`.
