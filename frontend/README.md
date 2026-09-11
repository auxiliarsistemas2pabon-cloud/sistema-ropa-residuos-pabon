# Frontend — Sistema de Registro y Control de Ropa Hospitalaria y Residuos

React + Vite + TypeScript, consumiendo la API REST de Django bajo `/api/`.

## Requisitos

- Node 18+ (probado con Node 24).
- El backend Django corriendo por separado (ver el `README`/`DESPLIEGUE.md` de la raíz del repo) — este frontend no sirve nada por sí solo, necesita la API real.

## Correr en local

```bash
cd frontend
npm install
cp .env.example .env   # ajustar VITE_API_URL si la API no está en localhost:8000/api
npm run dev
```

Abre `http://localhost:5173`.

**El backend debe correr con `python manage.py runserver` (puerto 8000 por defecto)** y con `CORS_ALLOWED_ORIGINS`/`CSRF_TRUSTED_ORIGINS` incluyendo `http://localhost:5173` — `config/settings/local.py` ya trae ese valor por defecto, no hace falta tocar nada si usas los puertos estándar.

## Variables de entorno

| Variable | Default | Qué es |
|---|---|---|
| `VITE_API_URL` | `http://localhost:8000/api` | Base URL de la API Django |

## Autenticación

Sesión Django (cookies), no JWT — igual que el resto del sistema. El arranque de cualquier flujo de escritura sigue esta secuencia (ya implementada en `src/api/client.ts` y `src/auth/AuthContext.tsx`):

1. `GET /auth/csrf/` fija la cookie `csrftoken`.
2. `POST /auth/login/` con `X-CSRFToken` desde esa cookie.
3. Las siguientes peticiones ya van autenticadas por cookie de sesión (mismo cierre por inactividad de 30 min del resto del sistema).

## Estructura

```
src/
  api/          cliente HTTP (axios + manejo de CSRF) y funciones por entidad
  auth/         AuthContext (sesión) y RutaProtegida (bloqueo por rol)
  components/   UI compartida: Layout, Stepper, Aviso
  features/     una carpeta por dominio (ropa, residuos, movimientos, ...)
  pages/        páginas que componen las rutas (Login, Panel)
  styles/       tokens.css + base.css — el mismo sistema de diseño que
                static/css/tokens.css y app.css del sitio Django, portado
                tal cual (mismos nombres de variables y clases)
```

## Estado actual

Construido y verificado extremo a extremo contra la API real: **Login → Panel (por rol) → Entregar ropa sucia (wizard de 3 pasos) → Detalle del movimiento**. El resto de las pantallas del prompt original (ropa limpia, residuos, rótulos, validación, novedades, día anterior, consolidados, RH1/facturación, catálogos) están enrutadas como placeholders ("Próximamente") — el patrón para construirlas ya está establecido en `features/ropa/EntregaSucia.tsx` (wizard) y `features/movimientos/Detalle.tsx` (vista de detalle): reutilizar `src/api/*`, los mismos componentes de `components/` y las clases de `styles/base.css`.
