# Manual técnico — instalación, respaldos y restauración

Sistema de Registro y Control de Ropa Hospitalaria y Residuos
Clínica Cardioneurovascular Pabón S.A.S.

## 1. Requisitos del servidor

- Linux con Docker y Docker Compose.
- Un dominio apuntando al servidor (para el certificado HTTPS automático).
- Puertos 80 y 443 abiertos.

## 2. Primer despliegue

```bash
git clone https://github.com/auxiliarsistemas2pabon-cloud/sistema-ropa-residuos-pabon.git
cd sistema-ropa-residuos-pabon

cp .env.example .env
# Editar .env:
#   DJANGO_SECRET_KEY=<clave larga y aleatoria>
#   DJANGO_ALLOWED_HOSTS=clinica-pabon.tudominio.com
#   POSTGRES_PASSWORD=<contraseña fuerte>

# Poner el dominio real en el Caddyfile (línea 1).

docker compose -f docker-compose.prod.yml up -d --build
```

El contenedor `web` aplica migraciones y recolecta estáticos solo al arrancar.
Caddy obtiene el certificado TLS la primera vez que alguien entra por HTTPS.

### Crear la primera usuaria administradora

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

Luego, en `/admin/` → Usuarios, asignarle rol **Administradora**.

## 3. Actualizaciones

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

## 4. Respaldos (RNF-15)

El servicio `respaldo` del compose hace un respaldo al arrancar y luego cada
24 horas, con retención de 35 copias (`DBBACKUP_CLEANUP_KEEP`). Las copias
quedan en el volumen `backups_data` (`/app/backups` dentro del contenedor).

### Alternativa: hora fija con cron del host

Quitar el servicio `respaldo` del compose y agregar al cron del servidor:

```cron
5 20 * * 1-5  cd /ruta/al/proyecto && docker compose -f docker-compose.prod.yml run --rm respaldo python manage.py respaldo_diario
```

### Copiar los respaldos fuera del servidor

Se recomienda sincronizar el volumen a otro disco o a la nube a diario, por
ejemplo con `rsync` o `rclone` sobre el directorio del volumen.

## 5. Restauración (RNF-16 — procedimiento probado)

Este procedimiento se probó restaurando un respaldo en una base de datos
aparte: las 2 sedes, 38 prendas y 23 categorías del catálogo se recuperaron
íntegras.

```bash
# 1. Ver los respaldos disponibles
docker compose -f docker-compose.prod.yml run --rm web python manage.py listbackups

# 2. Detener la aplicación (no la base)
docker compose -f docker-compose.prod.yml stop web caddy

# 3. Restaurar (pide confirmación)
docker compose -f docker-compose.prod.yml run --rm web python manage.py dbrestore

# 4. Volver a levantar
docker compose -f docker-compose.prod.yml up -d
```

Para restaurar una copia concreta: `dbrestore -i <nombre-del-archivo>`.

## 6. Verificación post-despliegue

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py check --deploy
```

- La sesión expira a los 30 minutos de inactividad (RNF-10).
- Todo el tráfico va por HTTPS; HTTP redirige a HTTPS.
- Ningún registro se puede eliminar, ni desde el admin ni por un superusuario.

## 7. Zona horaria y datos

- El servidor y la base operan en `America/Bogota`, horarios en formato 24 h.
- Los catálogos (sedes, servicios, prendas, categorías, columnas del RH1,
  parámetros de jornada y umbrales) se editan desde `/admin/` sin desplegar.

## 8. API REST (para el frontend React)

Bajo `/api/` corre una API DRF con autenticación por sesión (no JWT) sobre el
mismo login/logout de siempre. Si el frontend se sirve desde un origen
distinto (p. ej. el dev server de Vite), hay que declarar ese origen en dos
variables de entorno nuevas en `.env`:

```bash
CORS_ALLOWED_ORIGINS=https://app.clinica-pabon.tudominio.com
CSRF_TRUSTED_ORIGINS=https://app.clinica-pabon.tudominio.com
```

Si en cambio el build del frontend se sirve desde el mismo dominio que la
API (recomendado en producción: menos superficie de CORS, cookies sin
complicaciones), estas variables pueden dejarse vacías.

El flujo de arranque que debe seguir el cliente JS es: `GET /api/auth/csrf/`
(fija la cookie `csrftoken`) → `POST /api/auth/login/` con el encabezado
`X-CSRFToken` → las peticiones siguientes ya quedan autenticadas por cookie
de sesión, con el mismo cierre por inactividad de 30 minutos de siempre.
