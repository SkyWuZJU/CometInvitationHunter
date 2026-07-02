# Comet Invitation Hunter

Un sistema que monitorea Twitter en busca de códigos de invitación y responde a ellos automáticamente.

## Estructura del proyecto

```
├── backend/          # Servicio backend desarrollado con FastAPI
├── frontend/         # Interfaz frontend desarrollada en TypeScript/Vite
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
- Dockerfile – Configuración de un contenedor ligero
- docker-compose.yml – Orquestación de servicios
- nginx.conf – Configuración del proxy inverso
- deploy.sh – Script para despliegue con un solo comando
- deploy/production-setup.md – Guía completa de configuración

Características principales:
- Utiliza SQLite por su simplicidad (no se requiere base de datos externa)
- Un único contenedor Docker para el backend
- Nginx sirve la interfaz frontend y redirige las solicitudes a la API
- Las actualizaciones se realizan manualmente mediante el script ./deploy.sh
- Está configurado para funcionar en comethunter.skywu.me

Pasos para el despliegue:
1. Suba los archivos al servidor Linux.
2. Ejecute el script ./deploy.sh.
3. Configure el certificado SSL mediante el comando:  
   `certbot --nginx -d comethunter.skywu.me`
