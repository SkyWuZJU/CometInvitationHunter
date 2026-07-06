# Comet Invitation Hunter

Un sistema para monitorear Twitter en busca de códigos de invitación de Comet y responder a ellos automáticamente.

**Comet** es un navegador web nativo de IA desarrollado por **Perplexity**, que redefine la forma en que las personas navegan por Internet. En lugar de tratar a la IA como un chatbot independiente, Comet integra la asistencia de IA directamente en la experiencia de navegación, permitiendo a los usuarios buscar, resumir páginas, responder preguntas y completar tareas complejas sin tener que cambiar constantemente entre pestañas o aplicaciones. Al combinar el acceso en tiempo real a la web con el razonamiento inteligente, Comet tiene como objetivo hacer que la investigación, el descubrimiento de información y los flujos de trabajo diarios en Internet sean significativamente más rápidos y eficientes.


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

## Configuraciones

- Para desarrollo: `config/development.env`
- Para producción: `config/production.env`

## Despliegue en producción
Archivos relacionados:
- Dockerfile - Configuración de contenedor ligero
- docker-compose.yml - Orquestación de servicios
- nginx.conf - Configuración del proxy inverso
- deploy.sh - Script de despliegue con una sola orden
- deploy/production-setup.md - Guía completa de configuración

Características principales:
- Utiliza SQLite por su simplicidad (no se necesita base de datos externa)
- Un único contenedor Docker para el backend
- Nginx sirve al frontend y también hace de proxy para las APIs
- Actualizaciones manuales mediante./deploy.sh
- Configurado específicamente para comethunter.skywu.me

Para desplegar:
1. Suba los archivos a su servidor Linux
2. Ejecute./deploy.sh
3. Añada el certificado SSL con certbot --nginx -d comethunter.skywu.me
