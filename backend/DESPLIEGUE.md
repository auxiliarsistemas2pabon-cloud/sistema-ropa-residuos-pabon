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
cd sistema-ropa-residuos-pabon/backend

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

Las contraseñas solo las cambia la Administradora: la de cada persona en
Catálogos → Usuarios (botón "Clave") y la suya en "Contraseña", arriba a la
derecha. Usuario y Personal de servicio no pueden cambiar la propia.

## 3. Actualizaciones

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

Antes de cada actualización, un respaldo manual (las migraciones cambian la
base): `docker compose -f docker-compose.prod.yml run --rm respaldo python manage.py respaldo_diario`.

## 4. Respaldos (RNF-15)

El servicio `respaldo` del compose hace un respaldo al arrancar y luego cada
24 horas, con retención de 35 copias (`DBBACKUP_CLEANUP_KEEP`). Las copias
quedan en el volumen `backups_data` (`/app/backups` dentro del contenedor).

### Alternativa: hora fija con cron del host

Quitar el servicio `respaldo` del compose y agregar al cron del servidor:

```cron
5 20 * * 1-5  cd /ruta/al/proyecto && docker compose -f docker-compose.prod.yml run --rm respaldo python manage.py respaldo_diario
```

### Cifrado, copia fuera del servidor y avisos (protocolo de seguridad, A5)

Mientras falte alguno de estos tres puntos, `check --deploy` lo advierte
(`core.W001`, `core.W002`, `core.W003`).

**1. Cifrado con GPG.** El par de llaves se genera en un equipo de Sistemas,
nunca en el servidor:

```bash
gpg --quick-generate-key "Respaldos Clínica Pabón <respaldos@clinica-pabon.tudominio.com>" rsa4096 encrypt never
gpg --armor --export respaldos@clinica-pabon.tudominio.com > respaldo.asc
```

Al servidor solo va la llave **pública**, en `backend/llaves/respaldo.asc`, y en `.env`:

```bash
RESPALDO_GPG_DESTINATARIO=respaldos@clinica-pabon.tudominio.com
RESPALDO_GPG_LLAVE_PUBLICA=/run/llaves/respaldo.asc
```

La llave **privada** y su frase se guardan en custodia de Sistemas (gestor de
contraseñas y una copia fuera de línea). Sin ella las copias no se pueden
restaurar; junto al servidor, el cifrado no protegería nada.

**2. Copia fuera del servidor.** Montar en el servidor un disco o carpeta de
red de otra sede (NAS por SMB/NFS, o una carpeta sincronizada con la nube) y
declararla en `.env`:

```bash
RESPALDO_COPIA_EXTERNA_HOST=/mnt/respaldos-externos   # ruta en el servidor
RESPALDO_COPIA_EXTERNA_DIR=/respaldo-externo          # ruta dentro del contenedor (no cambiar)
```

Cada respaldo se copia ahí y se verifica su tamaño. En esa carpeta se
conservan las últimas 35 copias y la última de cada uno de los 12 meses
previos. Si la carpeta no está montada, el respaldo se da por fallido: nunca
se escribe la "copia externa" dentro del mismo servidor.

**3. Aviso si falla.** Con los datos del correo saliente (`EMAIL_HOST`,
`EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`)
y `RESPALDO_AVISO_CORREOS=sistemas@...,otra@...`, cada fallo envía un correo.

**Cada semana**, Sistemas confirma que hay un respaldo por día:
`docker compose -f docker-compose.prod.yml run --rm web python manage.py listbackups`.

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

**Copias cifradas (`.gpg`).** La llave privada entra solo durante la
restauración y el contenedor se descarta al terminar (`--rm`); la frase se
pide en pantalla:

```bash
docker compose -f docker-compose.prod.yml run --rm -v /ruta/segura/respaldo-privada.asc:/tmp/privada.asc:ro web \
  sh -c "gpg --batch --import /tmp/privada.asc && python manage.py dbrestore --decrypt -i <archivo>.gpg"
```

**Prueba trimestral (protocolo 4).** Restaurar el último respaldo en una base
aparte, nunca sobre la de producción, y anotar fecha, archivo, tiempo y conteos
verificados:

```bash
docker compose -f docker-compose.prod.yml exec db createdb -U clinica_pabon clinica_pabon_prueba
docker compose -f docker-compose.prod.yml run --rm -e POSTGRES_DB=clinica_pabon_prueba web python manage.py dbrestore -i <archivo>
docker compose -f docker-compose.prod.yml exec db dropdb -U clinica_pabon clinica_pabon_prueba
```

## 6. Verificación post-despliegue

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py check --deploy
```

- La sesión expira a los 30 minutos de inactividad (RNF-10).
- Todo el tráfico va por HTTPS; HTTP redirige a HTTPS.
- Ningún registro se puede eliminar, ni desde el admin ni por un superusuario.
- `/admin/` responde 403 desde fuera de la red interna (ver sección 9).
- `check --deploy` sin advertencias `core.W00x` (respaldos protegidos).

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

## 9. Seguridad de acceso (protocolos de seguridad)

**Bloqueo por intentos fallidos (A2).** Cinco contraseñas equivocadas seguidas
bloquean esa cuenta 15 minutos, en la pantalla de ingreso y en la API. Cada
intento fallido queda registrado con su IP (en `/admin/`, sección *Axes*).
Para desbloquear antes de tiempo a quien ya se identificó con Sistemas:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py axes_reset_username <usuario>
```

**Contraseñas (A3, A4).** Mínimo 10 caracteres, no comunes, no solo números,
no parecidas a los datos de la persona. Solo la Administradora las asigna y
las cambia (Catálogos → Usuarios → "Clave"); Usuario y Personal de servicio no
pueden cambiar la propia. La cuenta técnica (superusuario) solo la modifica
otro superusuario.

**`/admin/` solo desde la red interna (A6).** Caddy responde 403 a `/admin/`
desde cualquier IP fuera de `ADMIN_REDES_PERMITIDAS` (por defecto, las redes
privadas). Para fijar las redes reales de las sedes, en `.env`:

```bash
ADMIN_REDES_PERMITIDAS=192.168.10.0/24 10.20.0.0/16
```

Después de cambiar el `Caddyfile` o esa variable, validar y recargar:

```bash
docker compose -f docker-compose.prod.yml exec caddy caddy validate --config /etc/caddy/Caddyfile
docker compose -f docker-compose.prod.yml up -d caddy
```

Si delante del servidor hay otro proxy o balanceador, Caddy verá su IP y no
la del usuario: en ese caso hay que declarar ese proxy en `trusted_proxies`
del Caddyfile antes de confiar en esta regla.
