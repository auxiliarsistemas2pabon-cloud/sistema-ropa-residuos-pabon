# Sistema de Registro y Control de Ropa Hospitalaria y Residuos

Clínica Cardioneurovascular Pabón S.A.S. (Pasto, Nariño).

## Estructura del repositorio

```
backend/    Django 5 + API REST (DRF) bajo /api/. Ver backend/DESPLIEGUE.md
            para instalación, respaldos y restauración en producción.
frontend/   React + Vite + TypeScript, consume la API del backend.
            Ver frontend/README.md para correrlo en local.
```

Cada carpeta es independiente: instala y corre sus dependencias por su
cuenta (`backend/requirements.txt` con pip/venv, `frontend/package.json`
con npm) y tiene su propio `.gitignore`.

## Correr todo en local

1. **Backend**: seguir `backend/DESPLIEGUE.md` (o, para desarrollo sin
   Docker, crear un entorno virtual en `backend/`, instalar
   `requirements.txt`, levantar PostgreSQL — hay un `docker-compose.yml`
   solo para la base de datos — y correr `python manage.py runserver`).
2. **Frontend**: seguir `frontend/README.md` (`npm install && npm run dev`).

El frontend espera la API en `http://localhost:8000/api` por defecto
(`frontend/.env.example`), y el backend ya acepta el origen del dev server
de Vite (`http://localhost:5173`) por defecto en desarrollo.
