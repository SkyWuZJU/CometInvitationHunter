# Comet Invitation Hunter

Un sistema para monitorear Twitter en busca de códigos de invitación de Comet y responder a ellos automáticamente.

**Comet** es un navegador web nativo de IA desarrollado por **Perplexity**, que integra la inteligencia artificial directamente en la experiencia de navegación, lo que hace que las búsquedas, las investigaciones y las tareas cotidianas en la web sean más rápidas y eficientes.


## Estructura del proyecto

```
├── backend/          # Servicio backend de FastAPI
├── frontend/         # Frontend en TypeScript/Vite
├── monitor/          # Servicio de monitoreo en segundo plano
├── config/           # Archivos de configuración del entorno
└── setup_env.sh      # Script de configuración del entorno
```

## Configuración inicial

1. Ejecute el script de configuración para crear un entorno virtual de Python:
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

- Desarrollo: `config/development.env`
- Producción: `config/production.env`

## Despliegue en producción
Archivos relacionados:
- Dockerfile - Configuración de contenedor ligero
- docker-compose.yml - Orquestación de servicios
- nginx.conf - Configuración del proxy inverso
- deploy.sh - Script de despliegue con una sola orden
- deploy/production-setup.md - Guía completa de configuración

Características principales:
- Utiliza SQLite por su simplicidad (no se necesita una base de datos externa)
- Un único contenedor Docker para el backend
- Nginx sirve al frontend y proxyea las API
- Actualizaciones manuales mediante./deploy.sh
- Configurado para comethunter.skywu.me

Para desplegar:
1. Suba los archivos a su servidor Linux
2. Ejecute./deploy.sh
3. Agregue SSL con certbot --nginx -d comethunter.skywu.me
