from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
AUTHOR = 'Eval Samuel Molina Fuertes'
SYSTEM = 'Sistema de Registro y Control de Ropa Hospitalaria y Residuos'
DATE = '11 de noviembre de 2026'
NAVY = colors.HexColor('#123047')
TEAL = colors.HexColor('#00877D')
INK = colors.HexColor('#243B4B')
GRAY = colors.HexColor('#607585')
LIGHT = colors.HexColor('#EDF5F6')
for name, file in [('Arial','arial.ttf'), ('Arial-Bold','arialbd.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(Path('C:/Windows/Fonts') / file)))
pdfmetrics.registerFontFamily('Arial', normal='Arial', bold='Arial-Bold', italic='Arial', boldItalic='Arial-Bold')


def para(c, text, x, y, width, size=11, color=INK, bold=False, leading=None):
    style = ParagraphStyle('p', fontName='Arial-Bold' if bold else 'Arial', fontSize=size,
                           leading=leading or size * 1.45, textColor=color)
    p = Paragraph(text, style)
    _, h = p.wrap(width, 2000)
    p.drawOn(c, x, y-h)
    return y-h


def logos(c, x, y, height=37):
    for name in ['logo-clinica-pabon.jpg', 'logo-centro-cuidados.png']:
        path = ROOT / 'frontend/public/img' / name
        im = ImageReader(str(path))
        w, h = im.getSize()
        width = min(height*w/h, 155)
        hh = width*h/w
        c.drawImage(im, x, y-hh, width=width, height=hh, mask='auto')
        x += width + 24


def base(c, size, label, number, total):
    w,h = size
    c.setFillColor(colors.white)
    c.rect(0,0,w,h,fill=1,stroke=0)
    c.setFillColor(TEAL)
    c.rect(0,h-8,w,8,fill=1,stroke=0)
    para(c,'CLÍNICA CARDIONEUROVASCULAR PABÓN S.A.S.',40,h-30,w-80,8,GRAY,bold=True)
    c.setStrokeColor(colors.HexColor('#D9E5E9'))
    c.line(40,43,w-40,43)
    para(c,AUTHOR,40,32,w-150,8,GRAY)
    c.setFont('Arial',8)
    c.setFillColor(GRAY)
    c.drawRightString(w-40,23,f'{label}  |  {number:02d} / {total:02d}')


def cover(c, size, kind, subtitle, label, total):
    w,h=size
    base(c,size,label,1,total)
    logos(c,44,h-65,44)
    top = h-170 if w>h else h-225
    para(c,kind.upper(),44,top,w-88,12,TEAL,bold=True)
    y=para(c,'Ropa hospitalaria<br/>y residuos',44,top-36,w-88,36 if w>h else 35,NAVY,bold=True,leading=44)
    y=para(c,subtitle,46,y-18,w-100,16,GRAY)
    y=para(c,SYSTEM,46,y-25,w-100,11,INK)
    para(c,'Elaborado por<br/><b>'+AUTHOR+'</b>',46,155,w-100,12)
    para(c,'Pasto, Nariño · '+DATE+' · Versión documental 1.0',46,92,w-100,9,GRAY)
    c.showPage()


SLIDES = [
('01 · Conoce la aplicación','Un registro común para dos procesos',[
('Ropa hospitalaria','Registra la entrega de ropa sucia, la recepción desde lavandería y la distribución de ropa limpia a los servicios.'),
('Gestión de residuos','Registra generación y recolección, clasifica los residuos y conserva los pesos que alimentan los reportes.'),
('Seguimiento','Relaciona sedes, servicios, responsables, firmas, novedades y fechas. La Administradora consulta consolidados y facturación.')],
'Ruta de lectura: acceso y perfiles → ropa → residuos → reportes y cierre.'),
('02 · Acceso','Ingresa con tu cuenta asignada',[
('1. Abre la dirección de la app','Usa la dirección que te entregue Sistemas. En la pantalla de acceso escribe tu Usuario y tu Contraseña.'),
('2. Pulsa «Entrar»','El panel y las opciones disponibles dependen de tu perfil. Si hay un error de acceso, revisa el mensaje antes de reintentar.'),
('3. Protege tu sesión','La sesión vence tras 30 minutos de inactividad. Cinco intentos fallidos bloquean la cuenta durante 15 minutos; solicita apoyo si necesitas recuperar el acceso.')],
'Las contraseñas las administra la Administradora. Cierra sesión al terminar en equipos compartidos.'),
('03 · Perfiles','Cada persona tiene una función',[
('Personal de servicio','Cuenta prendas y marca los tipos de residuos que entrega. Selecciona al operario que recibe; el peso se registra después.'),
('Usuario · operario','Captura pesajes, recibe entregas asignadas y opera recepción de ropa limpia, rótulos, validación y consolidado de peligrosos.'),
('Administradora','Gestiona catálogos y cuentas, consulta reportes, novedades, RH1 y facturación. Puede corregir registros sin la ventana de tiempo del usuario.')],
'El perfil Administradora se concentra en gestión y control; las pantallas de captura diaria corresponden al personal operativo.'),
('04 · Ropa sucia','Entrega desde el servicio',[
('1. Origen','Abre «Entregar ropa sucia». Selecciona sede y servicio de origen. El servicio debe elegirse de forma explícita.'),
('2. Prendas o pesaje','Personal de servicio: marca al menos una prenda e indica su cantidad. Operario: registra peso total, tara y, si corresponde, bolsas y detalle de prendas.'),
('3. Cierre','Selecciona quién recibe, diligencia la firma cuando corresponda y agrega observaciones. Pulsa «Guardar entrega» y revisa el detalle del movimiento.')],
'Peso neto = peso total − tara. Ejemplo ilustrativo: 12,50 kg − 0,50 kg = 12,00 kg.'),
('05 · Recepción asignada','Completa los pesos pendientes',[
('1. Consulta tus entregas','En «Ropa sucia que me entregaron» y «Residuos que me entregaron», ubica los movimientos asignados a tu cuenta.'),
('2. Registra el peso real','El operario seleccionado como receptor pesa la ropa o cada tipo de residuo de la entrega. Revisa total y tara antes de guardar.'),
('3. Verifica el resultado','Confirma que el detalle ya muestra el peso registrado. Si una entrega ya está pesada, usa la corrección autorizada para resolver errores.')],
'Un registro sin pesaje conserva información pendiente: no equivale a un peso de cero.'),
('06 · Ropa limpia','Recibe el retorno de lavandería',[
('1. Selecciona la sede','En «Recibir ropa limpia», identifica dónde se recibe la ropa. Esta operación corresponde al operario.'),
('2. Diligencia el pesaje','Registra peso total y tara. El sistema calcula el peso neto; puedes incluir el detalle de prendas cuando lo controles por unidades.'),
('3. Revisa el cierre','Selecciona quién entrega, registra la firma cuando corresponda y las observaciones. Documenta la diferencia si el formulario lo requiere y guarda la recepción.')],
'El sistema dispone de seguimiento del ciclo de retorno entre ropa sucia entregada y ropa limpia recibida.'),
('07 · Distribución','Entrega ropa limpia a cada servicio',[
('1. Destino','Abre «Distribuir ropa limpia». Selecciona sede y área o servicio receptor.'),
('2. Prenda y cantidad','Elige la prenda e indica la cantidad de unidades. Este flujo trabaja por conteo de prendas.'),
('3. Responsable','Selecciona quién recibe, agrega la firma y observaciones cuando corresponda. Guarda y comprueba el movimiento.')],
'Verifica la unidad: las prendas se cuentan en unidades; los pesajes se registran en kilogramos.'),
('08 · Identificación y control','Rótulos, validación y corte',[
('Rótulos','Selecciona sede y entrega de ropa sucia; registra código y contenido. Si llegó sin rotular, marca la opción correspondiente.'),
('Validación de entrega a lavandería','Filtra por sede, fecha y jornada. Revisa el desglose y compara el total del sistema con el peso declarado; registra observaciones y guarda.'),
('Corte de ropa sucia','Consulta el corte de la entrega de las 18:00 de ayer más la de las 10:00 de hoy. Es una vista de seguimiento; no se añade otra vez al consolidado.')],
'El bloqueo por diferencias está desactivado por defecto. Sistemas puede configurar umbrales y activar el bloqueo.'),
('09 · Residuos','Registra la generación',[
('1. Identifica el origen','Abre «Generación de residuos» y selecciona sede y servicio. Revisa que correspondan al lugar de generación.'),
('2. Clasifica','Personal de servicio: marca al menos un tipo de residuo. Operario: elige grupo, categoría y tipo específico si aplica, y registra el pesaje.'),
('3. Entrega y guarda','Selecciona al receptor, incluye firma y observaciones cuando corresponda y guarda. Las entregas sin peso las completa el operario asignado.')],
'Grupos disponibles: No peligroso · Riesgo biológico · Otro peligroso · Otros. Usa el catálogo institucional vigente.'),
('10 · Residuos','Registra la recolección',[
('1. Origen y clasificación','Abre «Recolección de residuos». Selecciona sede y servicio; completa tipos o categorías según tu perfil.'),
('2. Pesaje o tipos','El operario registra peso total, tara y bolsas cuando corresponda. El Personal de servicio marca los tipos y asigna quién recibe para pesarlos después.'),
('3. Cierre y consulta','Revisa al receptor y las observaciones; guarda y verifica el detalle. El operario también dispone del «Consolidado de peligrosos».')],
'Generación y recolección son etapas distintas. Selecciona la pantalla que corresponda a la operación real.'),
('11 · Gestor externo','Registra la factura y concilia',[
('1. Selecciona la recolección','Como Administradora, abre «Entrega al gestor externo» y elige una recolección que aún no tenga factura registrada.'),
('2. Datos de la entrega','Selecciona el gestor activo e ingresa kg facturados y valor facturado. El número de factura es opcional en el formulario.'),
('3. Revisa la conciliación','Guarda y consulta «RH1 y facturación» para comparar los kg pesados internamente con los kg facturados y revisar los valores del periodo.')],
'La facturación se asocia a una recolección guardada. Revisa el periodo aplicado antes de interpretar los totales.'),
('12 · Reportes','Consulta y exporta información',[
('Consolidados','La Administradora filtra el periodo y consulta ropa por servicio o sede, residuos por categoría o servicio, por jornada y corte de peligrosos.'),
('RH1 y facturación','Selecciona el mes y revisa el RH1, el resumen de facturación y la conciliación con el gestor. El RH1 depende de las columnas configuradas.'),
('Excel','Usa las opciones de exportación de la pantalla. Verifica periodo y filtros antes de compartir el archivo; el Excel mensual RH1 incluye el mes completo.')],
'Antes de usar el RH1 como entrega institucional, confirma sus columnas con el área responsable.'),
('13 · Correcciones y novedades','Deja evidencia de lo ocurrido',[
('Corregir un registro','Abre el detalle y usa la corrección si está habilitada. Para cuentas operativas aplica autoría y ventana configurable: 60 minutos por defecto.'),
('Reportar una novedad','Quien entrega o recibe puede reportar una novedad del movimiento. Describe faltantes, daños, diferencias de peso u otra situación concreta.'),
('Revisar el día anterior','Consulta los movimientos y novedades del día previo. En perfiles operativos se muestran los movimientos en los que participaste.')],
'La Administradora puede corregir sin límite de ventana. La visibilidad de las firmas se limita a participantes y administración.'),
('14 · Cierre de jornada','Una revisión breve antes de salir',[
('Comprueba','Revisa sede, servicio, prendas o categorías, pesos, tara, receptor y observaciones. Confirma que aparezca el movimiento guardado.'),
('Resuelve pendientes','Completa los pesajes que te asignaron. Si detectas diferencias, corrige con tu permiso o reporta una novedad con el contexto necesario.'),
('Cierra sesión','Sal de tu cuenta al terminar. Para problemas de acceso o permisos, contacta a la Administradora o al equipo de Sistemas.')],
'Manual elaborado por Eval Samuel Molina Fuertes · Basado en los archivos de la aplicación revisados el 11 de noviembre de 2026.'),
]


def tutorial():
    size=landscape(A4); w,h=size
    path=OUT/'Tutorial_Sistema_Ropa_Hospitalaria_y_Residuos.pdf'
    c=canvas.Canvas(str(path),pagesize=size)
    c.setTitle('Tutorial de uso - '+SYSTEM); c.setAuthor(AUTHOR)
    cover(c,size,'Capacitación y manual de uso','Guía práctica para el personal de servicio, operarios y administración','Tutorial',len(SLIDES)+1)
    for i,(tag,title,cards,note) in enumerate(SLIDES,2):
        base(c,size,'Tutorial',i,len(SLIDES)+1)
        para(c,tag.upper(),42,h-63,w-84,10,TEAL,bold=True)
        para(c,title,42,h-93,w-84,27,NAVY,bold=True)
        gap=17; cw=(w-84-2*gap)/3; top=h-158; bottom=148
        for j,(heading,body) in enumerate(cards):
            x=42+j*(cw+gap)
            c.setFillColor(LIGHT); c.roundRect(x,bottom,cw,top-bottom,10,fill=1,stroke=0)
            c.setFillColor(TEAL); c.circle(x+25,top-27,11,fill=1,stroke=0)
            c.setFillColor(colors.white); c.setFont('Arial-Bold',10); c.drawCentredString(x+25,top-30,str(j+1))
            y=para(c,heading,x+17,top-57,cw-34,15,NAVY,bold=True)
            y=para(c,body,x+17,y-15,cw-34,12,INK)
            if y<bottom+13: raise RuntimeError(('slide overflow',i,j,y))
        para(c,note,45,119,w-90,11,TEAL)
        c.showPage()
    c.save()
    return path


PAGES = [
('Contenido y alcance',[
('Contenido','3. Visión general y alcance funcional<br/>4. Módulos y operación<br/>5. Trazabilidad y reglas de negocio<br/>6. Arquitectura y componentes<br/>7. Modelo de datos<br/>8. Roles y permisos<br/>9. Seguridad implementada<br/>10. API e integración<br/>11. Instalación y despliegue<br/>12. Respaldos y continuidad<br/>13. Verificación, límites y fuentes'),
('Identificación documental','Autor: <b>'+AUTHOR+'</b><br/>Fecha: '+DATE+'<br/>Versión documental: 1.0<br/>Aplicación: '+SYSTEM+'<br/>Institución indicada en el proyecto: Clínica Cardioneurovascular Pabón S.A.S., Pasto, Nariño.'),
('Criterio de elaboración','Se describe la implementación disponible en el repositorio local. Las afirmaciones sobre configuración corresponden al código y a los valores predeterminados revisados; no certifican la configuración de un servidor en producción.'),
('Documentos de referencia','Los PDF de Equipos de Emergencia aportan la separación entre tutorial y documentación técnica. Sus módulos, tecnologías, autores y estados de despliegue pertenecen a otra aplicación y no se trasladan a este sistema.')]),
('Visión general y alcance funcional',[
('Propósito','Centralizar el registro y control de ropa hospitalaria y residuos, vinculando las operaciones con sede, servicio, fecha, jornada y responsables. Facilita revisar los movimientos, documentar novedades y producir información para seguimiento y facturación.'),
('Ropa hospitalaria','El proceso incluye entrega de ropa sucia, recepción de ropa limpia desde lavandería y distribución a los servicios. Incorpora detalle por prenda, rótulos, seguimiento del ciclo de retorno, validación de entrega a lavandería y corte de control.'),
('Residuos','El proceso comprende generación y recolección, categorías y tipos de residuo, pesos por tipo cuando corresponde, consolidado de peligrosos y asociación de entregas con gestores externos para facturación y conciliación.'),
('Administración y seguimiento','Dispone de catálogos, cuentas y perfiles, parámetros de jornadas y umbrales, novedades, revisión del día anterior, consolidados y exportaciones a Excel. El RH1 se construye con columnas configurables.'),
('Límite del alcance','La revisión es documental y de código. No se verificaron disponibilidad del servidor, datos productivos, configuración institucional definitiva del RH1 ni la ejecución de respaldos en infraestructura real.')]),
('Módulos y operación',[
('Acceso y panel','La interfaz solicita usuario y contraseña. Tras autenticarse, muestra opciones según el perfil. El panel y la revisión del día anterior limitan las listas operativas a movimientos en los que participó la persona; administración tiene alcance institucional.'),
('Captura de ropa','La entrega de ropa sucia identifica sede y servicio. Personal de servicio captura prendas y cantidades sin peso; el operario captura el pesaje o completa la entrega que le asignaron. La recepción limpia registra peso total, tara y datos del retorno; la distribución registra prenda y cantidad de unidades por servicio receptor.'),
('Captura de residuos','Personal de servicio marca tipos y asigna un receptor sin pesar. El operario puede registrar grupo, categoría, tipo específico y pesaje; también completa los pesos de entregas asignadas. Los grupos definidos son No peligroso, Riesgo biológico, Otro peligroso y Otros.'),
('Control y reportes','Rótulos conserva identificación y señala entregas sin rotular. Validación compara peso declarado y calculado. Consolidados agrupa por sede, servicio, categoría y jornada. RH1 y facturación reúne el formato ambiental, valores facturados y conciliación con el gestor.'),
('Gestores y novedades','Una entrega al gestor enlaza una recolección con un gestor, kg facturados, valor y número de factura opcional. Las novedades describen situaciones como faltantes, deterioro, derrames o diferencias de peso y conservan su relación con el movimiento.')]),
('Trazabilidad y reglas de negocio',[
('Identidad de la operación','Movimiento conserva tipo, fecha, hora, jornada, sede, servicio cuando aplica, quién entrega, quién recibe, creador, fecha de creación, estado y periodo de facturación. Los modelos principales usan historial de cambios mediante django-simple-history.'),
('Pesaje','Peso neto = peso total − tara. El modelo de pesaje y los formularios validan los datos; la tara no puede superar el total. Una entrega pendiente de pesaje no se interpreta como cero. El operario asignado como receptor puede registrar su peso una vez; los errores posteriores se tramitan como corrección.'),
('Correcciones y novedades','Para cuentas operativas, la corrección exige que el registro sea propio y esté dentro de la ventana configurada, de 60 minutos por defecto. La Administradora y la cuenta técnica superusuario no tienen ese límite. Quien entrega o recibe puede reportar una novedad; administración también puede hacerlo.'),
('Ciclo y cortes','La recepción de ropa limpia puede enlazarse con la entrega de ropa sucia mediante mov_origen. El corte de control combina la entrega de las 18:00 del día anterior con la de las 10:00 del día actual. Es una consulta de seguimiento y no se suma otra vez al consolidado del periodo.'),
('Conformidad y conservación','La evaluación compara peso declarado y peso del sistema, con umbrales en kg y porcentaje. Ambos umbrales parten de cero y el bloqueo está desactivado por defecto. La aplicación incorpora controles para impedir eliminación de registros; las correcciones deben conservar trazabilidad.')]),
('Arquitectura y componentes',[
('Vista de componentes','Interfaz React → API REST Django → PostgreSQL.<br/>La configuración de producción incluida usa Caddy → Gunicorn/Django → PostgreSQL. Un servicio independiente ejecuta respaldos. El proyecto también conserva vistas y plantillas Django.'),
('Frontend','React 19, TypeScript y Vite 8. React Router administra rutas; TanStack Query consulta y actualiza datos; React Hook Form gestiona formularios y Axios realiza peticiones HTTP. El código organiza pantallas por dominio: ropa, residuos, movimientos, reportes y catálogos.'),
('Backend','Python 3.12 en la imagen Docker, Django 5.2 y Django REST Framework 3.16. La API se publica bajo /api/. Las áreas principales son core, ropa, residuos, movimientos y reportes. Las operaciones reutilizan validaciones de formularios y servicios del backend.'),
('Persistencia y exportación','PostgreSQL 16 según Docker Compose. psycopg conecta la aplicación con la base. openpyxl genera exportaciones Excel; django-simple-history conserva cambios. django-constance almacena parámetros editables en la base de datos.'),
('Producción definida','Docker Compose declara db, web, caddy y respaldo, con volúmenes persistentes. Caddy publica 80/443 y sirve /static/. La configuración actual redirige el resto de solicitudes a Django; no incluye la publicación del build de React. Integrar ese build requiere configurar su servicio estático y el fallback de rutas.')]),
('Modelo de datos',[
('Estructura institucional','Sede tiene varias AreaServicio. El servicio indica si genera ropa y/o residuos. Color y AreaColor describen asociaciones informativas; el color no identifica de forma única al servicio. Usuario extiende AbstractUser y añade documento, rol y estado activo.'),
('Núcleo transaccional','Movimiento es la entidad central. Se relaciona con sede, servicio de origen, usuarios de entrega y recepción, y uno o varios Pesaje. También contiene firmas dibujadas y una referencia opcional a otro movimiento para el ciclo de ropa. Novedad pertenece a un movimiento.'),
('Ropa','Prenda define el catálogo. DetalleRopa asocia prendas y cantidades con el movimiento. Rotulo registra identificación y contenido de una entrega. ValidacionEntrega conserva la comparación de peso para sede, fecha y jornada.'),
('Residuos y facturación','CategoriaResiduo organiza grupos y jerarquía de categorías. DetalleResiduo relaciona el movimiento con categorías y peso cuando aplica. EntregaGestor tiene relación uno a uno con Movimiento y referencia a GestorExterno. ColumnaRH1 define el orden, nombre y categorías o grupo que alimentan el reporte.'),
('Configuración y protección','ConfiguracionJornada define horarios por sede y proceso. Los parámetros generales se almacenan mediante Constance. Las relaciones sensibles utilizan protección referencial y existen restricciones de unicidad en entidades como categorías por movimiento y servicios por sede.')]),
('Roles y permisos',[
('Personal de servicio · SERVICIO','Registra entregas de ropa por conteo y tipos de residuos sin pesar. Puede distribuir ropa limpia por unidades. Asigna al operario que recibe y completa el pesaje. Consulta movimientos en los que participa y reporta novedades cuando entrega o recibe.'),
('Usuario · USUARIO','Es el perfil de operación y pesaje. Dispone de recepción de ropa limpia, rótulos, validación y consolidado de peligrosos, además de los flujos de captura habilitados. Solo el receptor operativo asignado puede pesar una entrega pendiente.'),
('Administradora · ADMIN','Gestiona cuentas, catálogos, configuración, novedades y reportes; registra entrega al gestor y consulta RH1/facturación. Corrige registros sin límite de ventana. La navegación separa sus tareas de gestión de la captura operativa.'),
('Cuenta técnica','El superusuario tiene excepciones explícitas en permisos del backend para soporte y administración. No constituye un cuarto perfil operativo del catálogo. Su contraseña solo la modifica otro superusuario según la documentación de despliegue.'),
('Aplicación de permisos','El frontend usa rutas protegidas y el backend comprueba autenticación y permisos por endpoint mediante IsAdministradora, IsOperario e IsUsuario y controles equivalentes. Las firmas dibujadas solo se muestran a participantes del movimiento y administración. Los cortes y consolidados tienen alcance institucional por diseño.')]),
('Seguridad implementada',[
('Autenticación y sesión','La API usa sesión Django mediante cookies y protección CSRF. El flujo obtiene primero la cookie CSRF y luego inicia sesión. La configuración establece 1.800 segundos de sesión y renovación por actividad; la sesión expira al cerrar el navegador según la cookie configurada.'),
('Credenciales y bloqueo','Django valida contraseñas con mínimo de 10 caracteres, control de similitud, claves comunes y claves solo numéricas. django-axes bloquea una cuenta después de cinco fallos durante 15 minutos y registra intentos con IP. La Administradora asigna y cambia las contraseñas.'),
('Transporte y exposición','La configuración de producción activa cookies seguras y cabeceras de seguridad. Caddy obtiene HTTPS al configurar un dominio real y restringe /admin/ a redes permitidas. PostgreSQL no publica un puerto del host en el compose de producción. Estos controles dependen del despliegue efectivo.'),
('Datos y auditoría','El historial de modelos permite revisar cambios. Los permisos limitan captura, corrección y acceso a firmas. Las cuentas operativas ven sus participaciones en panel y revisión del día anterior. Los secretos se cargan desde variables de entorno, que no deben incluirse en documentación ni repositorios.'),
('Comprobación operativa','Ejecutar python manage.py check --deploy en el entorno objetivo. Revisar CORS y CSRF para los orígenes reales, redes de administración, HTTPS y advertencias de respaldos. Si existe un proxy adicional, configurar adecuadamente la confianza y la IP del cliente antes de depender de las restricciones de red.')]),
('API e integración',[
('Base y autenticación','Prefijo: /api/.<br/>GET auth/csrf/ obtiene la cookie CSRF.<br/>POST auth/login/ inicia sesión con X-CSRFToken.<br/>GET auth/me/ consulta el usuario autenticado.<br/>POST auth/logout/ cierra sesión.<br/>auth/cambiar-clave/ atiende el cambio autorizado.'),
('Operaciones principales','movimientos/entrega-ropa-sucia/<br/>movimientos/recepcion-ropa-limpia/<br/>movimientos/distribucion-ropa-limpia/<br/>movimientos/generacion-residuo/<br/>movimientos/recoleccion-residuo/<br/>Los endpoints de creación usan validaciones específicas para cada proceso.'),
('Catálogos y control','catalogos/sedes/, catalogos/servicios/, catalogos/prendas/, catalogos/categorias-residuo/, catalogos/gestores-externos/ y catalogos/columnas-rh1/. El router también publica usuarios/, movimientos/, novedades/, rotulos/ y validacion-entrega/, según los permisos y acciones definidos.'),
('Consultas y exportaciones','ropa/ciclo-retorno/, ropa/corte-control/ y residuos/corte-peligrosos/. Reportes en consolidados/&lt;clave&gt;/, rh1/, facturacion/resumen/ y facturacion/conciliacion/. Hay rutas .xlsx para consolidados, novedades, RH1 y facturación.'),
('Configuración del cliente','VITE_API_URL usa http://localhost:8000/api como valor de desarrollo. Si frontend y API tienen distinto origen, configurar CORS_ALLOWED_ORIGINS y CSRF_TRUSTED_ORIGINS. Las solicitudes deben enviar credenciales de sesión y, en escrituras, el token CSRF. Consultar serializers y vistas para el contrato exacto de cada operación.')]),
('Instalación y despliegue',[
('Desarrollo local','Backend: crear un entorno Python, instalar backend/requirements.txt, configurar PostgreSQL y variables del entorno local, aplicar migraciones y ejecutar python manage.py runserver desde backend/.<br/>Frontend: instalar dependencias en frontend/ con npm install, configurar VITE_API_URL y ejecutar npm run dev. Puertos de referencia: API 8000 e interfaz 5173.'),
('Preparación de producción','Usar Linux con Docker y Docker Compose. Copiar backend/.env.example como .env y definir valores reales de clave de Django, hosts y acceso a PostgreSQL. Configurar el dominio en Caddyfile, las redes de administración y los parámetros de respaldo. No usar los valores de ejemplo como credenciales productivas.'),
('Arranque documentado','Desde backend/:<br/><font name="Arial-Bold">docker compose -f docker-compose.prod.yml up -d --build</font><br/>El entrypoint del contenedor aplica la preparación de Django. Crear la cuenta técnica mediante el comando de administración correspondiente y revisar los registros de los servicios.'),
('Publicación de React','npm run build en frontend/ produce los archivos de distribución. El compose y Caddyfile revisados publican Django y sus archivos estáticos. Para exponer la interfaz React debe definirse dónde servir su build, mantener /api/ hacia Django y resolver las rutas de la SPA.'),
('Verificación posterior','Ejecutar check --deploy, confirmar HTTPS, acceso por rol, cookies y CSRF, creación y consulta de un movimiento de prueba y generación de un Excel. Verificar persistencia de datos y respaldos. La documentación del repositorio contiene el detalle operativo; aquí no se certifica un despliegue ejecutado.')]),
('Respaldos y continuidad',[
('Programación y retención','El servicio respaldo está definido para ejecutar respaldo_diario al arrancar y cada 24 horas. El manual establece retención de 35 copias locales en backups_data. Como alternativa, puede programarse el comando con cron para una hora fija.'),
('Protección y copia externa','La implementación admite cifrado GPG con llave pública, copia a un almacenamiento externo montado y correo ante fallos. La llave privada debe mantenerse en custodia fuera del servidor. La configuración de copia externa conserva las últimas 35 copias y la última de cada uno de los 12 meses previos, según el manual.'),
('Control periódico','Comprobar el resultado del servicio, consultar listbackups y confirmar existencia de copias externas. check --deploy advierte con core.W001, core.W002 y core.W003 si faltan componentes de protección del respaldo. La configuración por sí sola no demuestra que las copias sean recuperables.'),
('Restauración','Procedimiento documentado: identificar la copia, detener web y caddy, restaurar con dbrestore y volver a levantar los servicios. dbrestore -i &lt;archivo&gt; permite seleccionar una copia. Los respaldos cifrados requieren la llave privada y la opción --decrypt, con custodia temporal controlada.'),
('Prueba de recuperación','Realizar una restauración trimestral en una base separada y registrar archivo, fecha, duración y conteos verificados. El manual del repositorio refiere una prueba previa; esta elaboración documental no ejecutó una restauración ni validó los respaldos de un servidor real.')]),
('Verificación, límites y fuentes',[
('Estado comprobado','Se identificaron implementaciones de pantallas y API para ropa, residuos, movimientos, reportes y catálogos. El README del frontend aún describe varias pantallas como placeholders; esa nota está desactualizada frente a los archivos revisados. La existencia del código no sustituye una prueba funcional de todas las rutas.'),
('Validación recomendada para aceptación','Probar acceso de los tres perfiles; conteo sin peso y pesaje posterior por el receptor; ropa limpia y distribución; clasificación de residuos; permisos y ventana de corrección; novedades; reportes y Excel; conciliación con el gestor; bloqueo de acceso y recuperación de respaldos. Usar datos de prueba controlados.'),
('Pendientes de confirmación institucional','Confirmar columnas y presentación definitiva del RH1, sedes y servicios activos, jornadas, umbrales, gestores y tarifas, responsables de administración, dominio, integración del build React y evidencias de operación y continuidad en el servidor objetivo.'),
('Fuentes del proyecto','README.md; backend/DESPLIEGUE.md; backend/requirements.txt; backend/config/settings/; backend/config/api_urls.py; backend/docker-compose.prod.yml; backend/Caddyfile; modelos, permisos y servicios de core, movimientos, ropa y residuos; frontend/package.json; frontend/src/App.tsx y pantallas de frontend/src/features/.'),
('Referencias de presentación','Tutorial_Sistema_Equipos_Emergencia.pdf y Documentacion_Sistema_Equipos_Emergencia.pdf, aportados por el usuario, se usaron como referencias de estructura documental.<br/><br/><b>Elaborado por: '+AUTHOR+'</b><br/>'+DATE+' · Versión documental 1.0')]),
]


def technical():
    size=A4; w,h=size
    path=OUT/'Documentacion_Tecnica_y_Funcional_Ropa_y_Residuos.pdf'
    c=canvas.Canvas(str(path),pagesize=size)
    c.setTitle('Documentación técnica y funcional - '+SYSTEM); c.setAuthor(AUTHOR)
    total=len(PAGES)+1
    cover(c,size,'Documentación técnica y funcional','Arquitectura, procesos, permisos y operación del sistema','Documentación',total)
    for n,(title,sections) in enumerate(PAGES,2):
        base(c,size,'Documentación',n,total)
        c.bookmarkPage('page'+str(n)); c.addOutlineEntry(title,'page'+str(n),0)
        y=para(c,title,43,h-69,w-86,23,NAVY,bold=True,leading=29)-24
        for heading,body in sections:
            y=para(c,heading,43,y,w-86,12,TEAL,bold=True)-7
            y=para(c,body,43,y,w-86,10.5,INK,leading=15.1)-18
        if y<51: raise RuntimeError(('technical overflow',n,y))
        c.showPage()
    c.save()
    return path


if __name__=='__main__':
    for path in [tutorial(),technical()]:
        print(path)
