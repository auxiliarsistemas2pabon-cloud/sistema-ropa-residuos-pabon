from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

OUT=Path(__file__).resolve().parent
AUTHOR='Eval Samuel Molina Fuertes'
TITLE='Sistema de Ropa Hospitalaria y Residuos'
INK='#1F2937'; MUTED='#6B7280'; BLUE='#2563EB'; DARK='#111827'
for family,normal,bold,italic in [('Calibri','calibri.ttf','calibrib.ttf','calibrii.ttf'),('Georgia','georgia.ttf','georgiab.ttf','georgiai.ttf')]:
    for suffix,file in [('',normal),('-Bold',bold),('-Italic',italic)]:
        pdfmetrics.registerFont(TTFont(family+suffix,str(Path('C:/Windows/Fonts')/file)))
    pdfmetrics.registerFontFamily(family,normal=family,bold=family+'-Bold',italic=family+'-Italic',boldItalic=family+'-Bold')

def txt(c,text,x,top,width,size=14,font='Calibri',color=INK,align=0,leading=None):
    p=Paragraph(text,ParagraphStyle('p',fontName=font,fontSize=size,leading=leading or size*1.32,textColor=colors.HexColor(color),alignment=align))
    _,h=p.wrap(width,2000);p.drawOn(c,x,c._pagesize[1]-top-h)
    return top+h

def rect(c,x,top,w,h,fill,stroke=None,r=0):
    c.setFillColor(colors.HexColor(fill));c.setStrokeColor(colors.HexColor(stroke or fill))
    if r:c.roundRect(x,c._pagesize[1]-top-h,w,h,r,fill=1,stroke=bool(stroke))
    else:c.rect(x,c._pagesize[1]-top-h,w,h,fill=1,stroke=bool(stroke))

def line(c,x1,t1,x2,t2,color='#CBD5E1',width=1):
    c.setStrokeColor(colors.HexColor(color));c.setLineWidth(width);H=c._pagesize[1];c.line(x1,H-t1,x2,H-t2)

def icon(c,x,t,kind,color=BLUE,r=24):
    H=c._pagesize[1];cy=H-t
    c.setFillColor(colors.HexColor(color));c.circle(x,cy,r,fill=1,stroke=0)
    c.setStrokeColor(colors.white);c.setLineWidth(1.8)
    if kind=='check':
        c.line(x-9,cy,x-2,cy-7);c.line(x-2,cy-7,x+11,cy+8)
    elif kind=='clock':
        c.circle(x,cy,11,fill=0,stroke=1);c.line(x,cy,x,cy+7);c.line(x,cy,x+5,cy-4)
    elif kind=='lock':
        c.roundRect(x-10,cy-10,20,15,2,fill=0,stroke=1);c.arc(x-6,cy, x+6,cy+16,0,180)
    elif kind=='doc':
        c.rect(x-8,cy-11,16,22,fill=0,stroke=1)
        for yy in [-4,1,6]:c.line(x-4,cy+yy,x+4,cy+yy)
    else:
        c.circle(x,cy+5,5,fill=0,stroke=1);c.arc(x-11,cy-14,x+11,cy+3,0,180)

def pictogram(c,x,t,size=32):
    # A simple symbol of the two processes, drawn as vectors.
    rect(c,x-size*.45,t,size*.9,size*.8,BLUE,r=4)
    line(c,x-size*.22,t+size*.2,x+size*.22,t+size*.2,'#FFFFFF',2)
    line(c,x,t+size*.1,x,t+size*.48,'#FFFFFF',2)
    rect(c,x-size*.6,t+size*.8,size*1.2,size*.12,'#93C5FD',r=2)

def slide_title(c,title,sub=''):
    txt(c,title,50,36,860,28,'Calibri-Bold')
    if sub:txt(c,sub,50,79,860,13,color=MUTED)

def screenshot(c,name,x=58,top=126,w=552,h=355):
    im=ImageReader(str(OUT/'capturas'/f'{name}.png'));iw,ih=im.getSize()
    ratio=min(w/iw,h/ih);dw,dh=iw*ratio,ih*ratio
    rect(c,x+2,top+3,dw,dh,'#E5E7EB',r=2)
    c.drawImage(im,x,c._pagesize[1]-top-dh,width=dw,height=dh,mask='auto')
    rect(c,x,top,dw,dh,'#FFFFFF',stroke='#D1D5DB') if False else None
    txt(c,'Captura de la interfaz · datos de demostración',x,top+dh+7,w,9,color=MUTED)

def steps(c,items,x=642,top=125,width=265):
    for i,item in enumerate(items,1):
        c.setFillColor(colors.HexColor(BLUE));c.circle(x-13,540-top-8,13,fill=1,stroke=0)
        txt(c,str(i),x-25,top-1,24,13,'Calibri-Bold','#FFFFFF',align=1)
        end=txt(c,item,x+17,top,width-17,14)
        top=max(top+52,end+21)
    return top

def note(c,text,x,top,w,color='#FEF3C7'):
    p=Paragraph(text,ParagraphStyle('n',fontName='Calibri-Italic',fontSize=12,leading=16,textColor=colors.HexColor('#78350F')))
    _,h=p.wrap(w-28,1000);rect(c,x,top,w,h+28,color,r=3);p.drawOn(c,x+14,540-top-14-h)

def tutorial():
    path=OUT/'Tutorial_Ropa_y_Residuos_Estilo_Ejemplo.pdf'
    c=canvas.Canvas(str(path),pagesize=(960,540));c.setTitle(TITLE+' · Capacitación y manual de uso');c.setAuthor(AUTHOR)
    rect(c,0,0,960,540,DARK);pictogram(c,480,99,38)
    txt(c,TITLE,50,205,860,35,'Calibri-Bold','#FFFFFF',1)
    txt(c,'Capacitación y manual de uso',100,274,760,19,color='#93C5FD',align=1)
    line(c,430,324,530,324,'#374151')
    txt(c,AUTHOR+'<br/>Clínica Cardioneurovascular Pabón',100,343,760,14,color='#CBD5E1',align=1)
    txt(c,'Centro de Cuidados Cardioneurovasculares Pabón S.A.S.',80,381,800,12,color='#9CA3AF',align=1)
    txt(c,'Noviembre de 2026',100,480,760,11,color=MUTED,align=1);c.showPage()
    slide_title(c,'¿Qué es el sistema?','Digitaliza el registro y control de ropa hospitalaria y residuos, con responsables y trazabilidad.')
    for x,col,kind,head,body in [(50,'#059669','check','Trazabilidad completa','Cada entrega, recepción y recolección conserva fecha, sede, servicio y responsables. Las novedades quedan asociadas al movimiento.'),(354,'#D97706','clock','Control de la operación','Separa el conteo de prendas y tipos de residuos del pesaje que realiza el operario receptor.'),(657,BLUE,'doc','Reportes y consolidación','Permite consultar consolidados, generar RH1 y comparar pesos internos con facturación del gestor. Exporta información a Excel.')]:
        icon(c,x+24,183,kind,col,32);txt(c,head,x,245,250,17,'Calibri-Bold');txt(c,body,x,327,250,13,color=MUTED)
    c.showPage()
    slide_title(c,'Cómo ingresar al sistema')
    screenshot(c,'acceso',58,135,365,285)
    steps(c,['Ingresa tu usuario asignado','Escribe tu contraseña','Clic en «Entrar»'],x=470,top=125,width=390)
    note(c,'<b>Por seguridad</b><br/><br/>• La sesión vence tras 30 minutos de inactividad.<br/>• Cinco intentos fallidos bloquean la cuenta 15 minutos.<br/>• Cierra sesión al terminar en equipos compartidos.',455,302,425,'#FEF2F2');c.showPage()
    slide_title(c,'Roles del sistema','Cada persona ve y puede hacer lo que su función requiere')
    roles=[('Administradora','Gestiona catálogos y usuarios. Consulta reportes, RH1, facturación y novedades. Corrige sin límite de ventana.','lock',DARK),('Usuario · operario','Registra pesos y completa entregas asignadas. Opera recepción limpia, rótulos, validación y consolidado de peligrosos.','doc','#059669'),('Personal de servicio','Cuenta prendas y marca tipos de residuos. Selecciona al operario receptor que registrará los pesos.','user',BLUE)]
    for i,(head,body,kind,col) in enumerate(roles):
        x=50+i*303;rect(c,x,126,275,312,'#F3F4F6',r=4);icon(c,x+137,180,kind,col,26);txt(c,head,x+15,239,245,16,'Calibri-Bold',align=1);txt(c,body,x+25,318,225,13,color=MUTED,align=1)
    c.showPage()
    slides=[
        ('Panel principal','Accesos rápidos y movimientos de la jornada','panel',['El panel muestra las opciones de tu perfil','Consulta movimientos, pesos y pendientes del día','Abre el detalle para revisar cada registro'],None),
        ('Entrega de ropa sucia','Identifica el origen y registra la entrega del servicio','sucia',['Selecciona la sede y el servicio de origen','Personal de servicio: cuenta prendas y cantidades','Operario: registra peso total y tara','Selecciona quién recibe y guarda la entrega'],'El operario asignado como receptor completa el pesaje de las entregas registradas sin peso.'),
        ('Pesaje de las entregas','Registra los kilogramos medidos y el peso del recipiente','pesaje',['Ingresa el peso total en kg','Registra la tara del recipiente','Comprueba el peso neto calculado','Continúa al cierre y revisa el detalle'],'Peso neto = peso total − tara. Ejemplo: 12,50 − 0,50 = 12,00 kg.'),
        ('Recepción de ropa limpia','Registra el retorno de la ropa desde lavandería','recepcion',['Selecciona la sede receptora','Ingresa peso total y tara','Incluye prendas si se controlan por unidades','Selecciona quién entrega y guarda'],'Registra las observaciones de diferencia cuando correspondan. Revisa el ciclo de retorno.'),
        ('Distribución de ropa limpia','Entrega prendas a los servicios por cantidad de unidades','distribucion',['Selecciona sede y servicio receptor','Elige la prenda y su cantidad','Selecciona a la persona que recibe','Diligencia observaciones y guarda'],None),
        ('Rótulos y validación','Identificación de las entregas y comparación de totales','rotulos',['Selecciona sede y entrega de ropa sucia','Ingresa el código y contenido del rótulo','Marca si la entrega llegó sin rotular','En Validación, compara el total declarado y el del sistema'],'La validación se consulta por sede, fecha y jornada. Los umbrales y el bloqueo son configurables.'),
        ('Generación de residuos','Registra qué residuos se producen y dónde se originan','generacion',['Selecciona sede y servicio','Personal de servicio: marca los tipos','Operario: clasifica y registra el pesaje','Selecciona quién recibe y guarda'],'Grupos: No peligroso, Riesgo biológico, Otro peligroso y Otros. Usa el catálogo institucional.'),
        ('Recolección de residuos','Registra el paso de los residuos hacia el almacenamiento','recoleccion',['Identifica sede y servicio de origen','Selecciona categorías o marca tipos, según tu perfil','Registra el peso o asígnalo al receptor','Revisa observaciones y guarda'],'Una entrega sin peso debe completarla el operario receptor. No se interpreta como un peso de cero.'),
        ('Entrega al gestor externo','Asocia la recolección con su factura y proveedor','gestor',['Selecciona una recolección sin factura registrada','Elige el gestor externo activo','Ingresa kg facturados y valor facturado','Guarda y revisa RH1 y facturación'],'Operación de la Administradora. El número de factura es opcional en el formulario.'),
        ('Reportes','Consolidados por periodo y exportación a Excel','reportes',['Selecciona periodo y filtros de consulta','Revisa ropa por sede o servicio y residuos por categoría','Consulta el resumen por jornada y los cortes','Exporta a Excel el reporte que necesitas'],None),
        ('RH1, facturación y novedades','Consulta ambiental y seguimiento de diferencias','rh1',['Selecciona el mes de consulta','Revisa el RH1 y sus columnas configuradas','Compara kg internos y kg facturados','Reporta novedades desde el movimiento cuando corresponda'],'La Administradora revisa el conjunto de novedades. La ventana de corrección operativa es de 60 minutos por defecto.'),
    ]
    for title,sub,image,items,callout in slides:
        slide_title(c,title,sub);screenshot(c,image);end=steps(c,items)
        if callout:note(c,callout,630,max(end+5,340),280)
        c.showPage()
    rect(c,0,0,960,540,DARK);txt(c,'Seguridad de la información',50,39,850,28,'Calibri-Bold','#FFFFFF');txt(c,'Protección de las cuentas, los registros y las firmas',50,82,850,13,color='#9CA3AF')
    for x,col,kind,head,body in [(50,'#DC2626','clock','Cierre por inactividad','La sesión vence tras 30 minutos sin actividad. Cierra sesión al finalizar tu trabajo.'),(354,BLUE,'lock','Acceso por perfil','Las acciones están limitadas por rol. Cinco accesos fallidos bloquean la cuenta durante 15 minutos.'),(657,'#7C3AED','doc','Historial y firmas','El sistema conserva historial de cambios. Las firmas son visibles para participantes y administración.')]:
        icon(c,x+24,183,kind,col,32);txt(c,head,x,245,250,16,'Calibri-Bold','#FFFFFF');txt(c,body,x,327,250,13,color='#9CA3AF')
    c.showPage();rect(c,0,0,960,540,DARK)
    txt(c,'G R A C I A S',70,193,820,12,'Calibri-Bold','#93C5FD');txt(c,'¿Preguntas o dudas de uso?',70,239,820,35,'Calibri-Bold','#FFFFFF');txt(c,AUTHOR,70,309,820,17,color='#CBD5E1');txt(c,'Clínica Cardioneurovascular Pabón · Centro de Cuidados Cardioneurovasculares Pabón S.A.S.',70,459,820,11,color='#9CA3AF');c.showPage();c.save()
    print(path)


class Doc:
    def __init__(self):
        self.path=OUT/'Documentacion_Ropa_y_Residuos_Estilo_Ejemplo.pdf';self.c=canvas.Canvas(str(self.path),pagesize=(612,792));self.c.setTitle(TITLE+' · Documentación técnica y funcional');self.c.setAuthor(AUTHOR);self.y=58
    def page(self):self.c.showPage();self.y=58
    def p(self,text,size=13.5,color=INK,font='Georgia',gap=12):
        self.y=txt(self.c,text,58,self.y,496,size,font,color,leading=size*1.32)+gap
        if self.y>750:raise RuntimeError(('document overflow',self.c.getPageNumber(),self.y))
    def h(self,text):
        self.y+=7;self.p(text,14,font='Georgia-Bold',gap=4);line(self.c,58,self.y,554,self.y,'#93B4FF',.7);self.y+=10
    def sub(self,text):self.p(text,14,'#1E40AF','Georgia-Bold',7)
    def bullet(self,text):
        self.y=txt(self.c,'•',63,self.y,15,13,'Georgia') or self.y
        # Bullet text shares the line above.
        self.y-=17.16
        self.y=txt(self.c,text,79,self.y,475,13,'Georgia',leading=17.1)+7
        if self.y>750:raise RuntimeError(('bullet overflow',self.c.getPageNumber(),self.y))
    def caption(self,text):self.p(text,12.5,'#4B5563','Georgia-Italic',14)
    def table(self,headers,rows,widths):
        style=lambda s,b=False:Paragraph(s,ParagraphStyle('cell',fontName='Georgia-Bold' if b else 'Georgia',fontSize=11.5,leading=14.5,textColor=colors.white if b else colors.HexColor(INK)))
        t=Table([[style(x,True) for x in headers]]+[[style(x) for x in row] for row in rows],colWidths=widths)
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor(INK)),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#E5E7EB')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        _,h=t.wrap(496,1000);t.drawOn(self.c,58,792-self.y-h);self.y+=h+17
        if self.y>750:raise RuntimeError(('table overflow',self.c.getPageNumber(),self.y))
    def box(self,x,top,w,h,text,fill='#DBEAFE',stroke='#60A5FA'):
        rect(self.c,x,top,w,h,fill,stroke,5);txt(self.c,text,x+5,top+8,w-10,10.5,'Calibri',align=1)

def technical():
    d=Doc();c=d.c
    pictogram(c,306,157,23)
    txt(c,TITLE,65,204,482,21,'Georgia-Bold',align=1)
    txt(c,'Documentación técnica y funcional',58,263,496,22,'Georgia','#1E40AF',1)
    txt(c,'Centro de Cuidados Cardioneurovasculares<br/>Pabón S.A.S.<br/>Clínica Cardioneurovascular Pabón',58,318,496,20,'Georgia','#4B5563',1)
    line(c,58,437,554,437,'#E5E7EB',.7)
    txt(c,'Elaborado por:<br/>'+AUTHOR,58,483,496,21,'Georgia',align=1)
    txt(c,'Noviembre de 2026 · Versión 1.0',58,568,496,19,'Georgia','#4B5563',1);d.page()
    d.h('Índice')
    sections=['Resumen ejecutivo','Objetivo del sistema','Módulos y funcionalidades','Trazabilidad: entregas, pesajes y retorno','Arquitectura técnica','Modelo de datos','Roles y permisos','Seguridad implementada','Formatos y reportes soportados','Estado del despliegue','Próximos pasos']
    for i,s in enumerate(sections,1):d.p(f'{i}. {s}',14,gap=5)
    d.page()
    d.h('1. Resumen ejecutivo')
    d.p('Este documento describe el Sistema de Registro y Control de Ropa Hospitalaria y Residuos de la Clínica Cardioneurovascular Pabón S.A.S. La aplicación centraliza la información de las entregas de ropa, su retorno desde lavandería y la generación y recolección de residuos, conservando sede, servicio, fechas y responsables.')
    d.p('El sistema diferencia el conteo que realiza el Personal de servicio del pesaje que completa el operario receptor. Relaciona los movimientos con prendas, categorías de residuos, firmas y novedades, y permite consultar consolidados y exportaciones para seguimiento institucional.')
    d.p('La Administradora dispone de reportes, RH1, facturación y conciliación con gestores externos. El historial de cambios y las restricciones de corrección ayudan a mantener la trazabilidad de los registros.')
    d.h('2. Objetivo del sistema')
    d.p('Organizar la captura y revisión de los procesos de ropa hospitalaria y residuos mediante un registro digital común, con responsabilidades identificadas y datos consistentes para la gestión.')
    for t in ['Registrar entregas, recepciones y recolecciones por sede, servicio y jornada.','Relacionar prendas y categorías con cantidades y pesos medidos.','Identificar pesajes pendientes y asignar quién debe completarlos.','Documentar diferencias, faltantes, daños y otras novedades.','Facilitar reportes, RH1 y conciliación de pesos y facturación.']:d.bullet(t)
    d.page()
    d.h('3. Módulos y funcionalidades')
    d.p('Las funciones se agrupan en operación diaria, reportes y administración. Los accesos disponibles dependen del perfil de la persona autenticada.')
    y=d.y
    groups=[('OPERACIÓN DIARIA',['Ropa sucia','Ropa limpia','Residuos','Pesajes y novedades'],'#DBEAFE','#60A5FA'),('REPORTES Y CONTROL',['Consolidados','RH1 y facturación','Validación y cortes','Exportación Excel'],'#FEF3C7','#FBBF24'),('ADMINISTRACIÓN',['Usuarios y perfiles','Catálogos','Jornadas y umbrales','Historial de cambios'],'#EDE9FE','#A78BFA')]
    for i,(head,items,fill,stroke) in enumerate(groups):
        x=67+i*166;rect(c,x,y,154,205,'#F8FAFC',r=6);txt(c,head,x+4,y+9,146,9,'Calibri-Bold',align=1)
        for j,t in enumerate(items):d.box(x+9,y+34+j*40,136,28,t,fill,stroke)
    d.y=y+219;d.caption('Mapa de módulos del sistema')
    d.sub('Operación diaria')
    for t in ['Ropa sucia: entrega desde el servicio, conteo, pesaje y rótulos.','Ropa limpia: recepción desde lavandería y distribución por unidades.','Residuos: generación, recolección, clasificación y consolidado de peligrosos.']:d.bullet(t)
    d.sub('Reportes y administración')
    for t in ['Consolidados por sede, servicio, categoría y jornada; RH1 y facturación, con exportación a Excel.','Catálogos de sedes, servicios, prendas, residuos y gestores; cuentas, perfiles, jornadas y parámetros de diferencias.']:d.bullet(t)
    d.page()
    d.h('4. Trazabilidad: entregas, pesajes y retorno')
    d.p('Cada movimiento conserva su origen, fecha, hora, jornada y responsables. Una entrega registrada sin peso mantiene la información de prendas o tipos de residuos hasta que el operario asignado la pesa. La ausencia de pesaje no equivale a un peso de cero.')
    y=d.y+5
    for x,tt,ww,hh,s,fill,stroke in [(65,y,128,60,'Entrega del servicio<br/>Prendas o tipos','#FEF3C7','#FBBF24'),(237,y,128,60,'Operario receptor<br/>Pesaje real','#DBEAFE','#60A5FA'),(409,y,128,60,'Movimiento<br/>con peso registrado','#D1FAE5','#34D399')]:d.box(x,tt,ww,hh,s,fill,stroke)
    for x in [194,366]:line(c,x,y+30,x+40,y+30,'#94A3B8');txt(c,'→',x+10,y+18,25,18)
    d.y=y+80;d.caption('Del conteo o clasificación inicial al pesaje del receptor')
    d.sub('Reglas de registro y corrección')
    for t in ['Peso neto = peso total − tara. La tara no puede superar el peso total.','El receptor operativo asignado completa el peso pendiente; un pesaje existente se corrige mediante el permiso correspondiente.','Las cuentas operativas corrigen registros propios dentro de una ventana configurable de 60 minutos por defecto. La Administradora puede corregir sin ese límite.','Quien entrega o recibe puede reportar una novedad; la Administradora también puede hacerlo.']:d.bullet(t)
    d.sub('Retorno y comparación de totales')
    d.p('La recepción de ropa limpia puede vincularse con el movimiento de ropa sucia de origen. La validación compara el peso declarado con el calculado por el sistema. Los umbrales en kg y porcentaje, y el bloqueo por diferencia, son configurables; el bloqueo está desactivado por defecto.')
    d.p('El corte de control combina la entrega de las 18:00 de ayer con la de las 10:00 de hoy. Se consulta como seguimiento y no se suma otra vez al consolidado del periodo.')
    d.page()
    d.h('5. Arquitectura técnica')
    d.p('La aplicación combina una interfaz React y una API REST Django con PostgreSQL. El repositorio también conserva vistas y plantillas Django. La configuración de producción incluida usa Caddy como entrada y Gunicorn para ejecutar el backend.')
    y=d.y
    d.box(223,y,166,34,'Usuario · navegador web')
    d.box(223,y+59,166,37,'Caddy · HTTPS y proxy','#F1F5F9','#94A3B8')
    d.box(78,y+126,190,46,'Frontend React + Vite<br/>Build por integrar al despliegue')
    d.box(345,y+126,190,46,'Backend Django + DRF<br/>Gunicorn · API /api/','#D1FAE5','#34D399')
    d.box(345,y+207,190,40,'PostgreSQL 16<br/>Persistencia e historial','#FEF3C7','#FBBF24')
    line(c,306,y+34,306,y+59);line(c,306,y+96,440,y+126);line(c,440,y+172,440,y+207);line(c,268,y+149,345,y+149)
    line(c,306,y+96,173,y+126,'#CBD5E1')
    d.y=y+262;d.caption('Arquitectura del proyecto y configuración de producción incluida')
    d.sub('Componentes')
    d.table(['Componente','Tecnología','Función'],[
        ['Frontend','React 19 + Vite 8 + TypeScript','Interfaz, navegación y formularios.'],['Backend','Python 3.12 + Django 5.2 + DRF 3.16','API, autenticación y reglas del proceso.'],['Base de datos','PostgreSQL 16','Persistencia de registros y catálogos.'],['Servidor web','Caddy 2 + Gunicorn','HTTPS y ejecución de Django.'],['Operación','Docker Compose','Servicios y volúmenes persistentes.']], [103,168,225])
    d.page()
    d.h('6. Modelo de datos')
    d.p('Movimiento es la entidad central de las operaciones. Se relaciona con la sede, el servicio y los usuarios que crean, entregan o reciben. Los detalles especializados describen prendas, residuos, pesajes y novedades.')
    y=d.y+8
    boxes=[(65,y+55,112,45,'Sede<br/>Área o servicio','#DBEAFE','#60A5FA'),(242,y+55,128,45,'Movimiento<br/>Fecha · tipo · jornada','#FEF3C7','#FBBF24'),(242,y-5,128,36,'Usuario<br/>Crea · entrega · recibe','#EDE9FE','#A78BFA'),(426,y+2,112,38,'Pesaje<br/>Total · tara · neto','#D1FAE5','#34D399'),(426,y+57,112,38,'Detalle de ropa<br/>Prenda · cantidad','#D1FAE5','#34D399'),(426,y+112,112,38,'Detalle de residuo<br/>Categoría · peso','#D1FAE5','#34D399'),(242,y+140,128,38,'Novedad · Rótulo<br/>Validación','#FEE2E2','#F87171')]
    for b in boxes:d.box(*b)
    line(c,177,y+77,242,y+77);line(c,306,y+31,306,y+55);line(c,306,y+100,306,y+140)
    for t in [y+21,y+76,y+131]:line(c,370,y+77,426,t)
    d.y=y+198;d.caption('Entidades principales y sus relaciones')
    d.sub('Entidades complementarias')
    for t in ['Prenda y DetalleRopa: catálogo de prendas, unidades y pesos cuando corresponden.','CategoriaResiduo y DetalleResiduo: clasificación jerárquica y detalle por movimiento.','GestorExterno y EntregaGestor: proveedor, kg y valor facturados; una entrega al gestor por movimiento.','ColumnaRH1: nombre, orden y grupos o categorías que alimentan el formato.','ConfiguracionJornada y parámetros Constance: horarios y reglas editables.']:d.bullet(t)
    d.p('Los modelos principales incorporan historial de cambios. Las relaciones sensibles usan protección referencial y restricciones de unicidad. Las firmas dibujadas se guardan asociadas al movimiento y su visualización se limita por participación o perfil.')
    d.page()
    d.h('7. Roles y permisos')
    d.table(['Rol','Puede hacer'],[
        ['Administradora','Gestionar cuentas, catálogos y parámetros; consultar reportes y novedades; registrar entregas al gestor; corregir sin límite de ventana.'],['Usuario · operario','Capturar pesajes y recibir entregas asignadas; operar ropa limpia, rótulos, validación y consolidado de peligrosos.'],['Personal de servicio','Contar prendas, marcar tipos de residuos y asignar el receptor operativo. Distribuir ropa limpia por unidades.']], [125,371])
    d.p('La cuenta técnica superusuario tiene excepciones explícitas de soporte en el backend. No constituye un cuarto perfil operativo. Los permisos se verifican en la API y también se reflejan en las rutas protegidas del frontend.')
    d.h('8. Seguridad implementada')
    for t in ['Autenticación por sesión Django mediante cookies y protección CSRF.','Cierre de sesión tras 30 minutos de inactividad, según la configuración incluida.','Cinco intentos fallidos bloquean la cuenta durante 15 minutos mediante django-axes.','Contraseñas de mínimo 10 caracteres, con validación de similitud, claves comunes y valores solo numéricos.','La Administradora asigna y cambia contraseñas; las firmas se muestran a participantes y administración.','Producción define cookies seguras, HTTPS mediante Caddy y acceso a /admin/ restringido por redes permitidas.','Las cuentas operativas ven sus participaciones en panel y revisión del día anterior. Los cortes y consolidados tienen alcance institucional.']:d.bullet(t)
    d.page()
    d.h('9. Formatos y reportes soportados')
    d.sub('Consolidados operativos')
    d.p('Consultas de ropa por sede o servicio, residuos por categoría o servicio, resumen por jornada y corte de peligrosos. La Administradora puede aplicar filtros y exportar a Excel. El corte de ropa sucia se conserva como vista independiente de control para evitar doble conteo.')
    d.sub('RH1 y facturación')
    d.p('El RH1 usa columnas configurables por grupo o categorías. La interfaz presenta la información del mes y permite exportar el mes completo o un día. La estructura definitiva debe validarse con el área institucional responsable antes de su entrega formal.')
    d.p('La facturación reúne kg y valores registrados frente a las recolecciones y permite conciliar los pesos internos con los facturados. El registro al gestor parte de una recolección existente y usa el gestor externo seleccionado.')
    d.sub('Novedades y trazabilidad')
    d.p('Las novedades documentan faltantes, deterioro, diferencias de peso, problemas de bolsas o recipientes, derrames y otros eventos. Se consultan asociadas al movimiento y pueden exportarse a Excel desde administración.')
    d.h('10. Estado del despliegue')
    d.p('La revisión confirma código de interfaz, API, modelos y archivos para desplegar. No se ha comprobado el estado de un servidor productivo como parte de esta documentación.')
    d.table(['Elemento','Estado observado'],[
        ['Interfaz y API','Implementaciones presentes en el repositorio.'],['Producción Docker','Compose, Dockerfile y Caddyfile disponibles.'],['Publicación de React','El build requiere integración al despliegue incluido.'],['Operación institucional','Servidor, datos y aceptación pendientes de verificar.']], [185,311])
    d.page()
    d.h('11. Próximos pasos')
    for t in ['Confirmar catálogos, jornadas, responsables, gestores y columnas del RH1.','Validar con los tres perfiles el conteo, pesaje posterior, ropa limpia, residuos, correcciones, novedades y reportes.','Publicar el build de React, definir el dominio y comprobar HTTPS, permisos y CSRF en el entorno final.','Capacitar al personal y documentar la aceptación del sistema.']:d.bullet(t)
    d.sub('Respaldos y continuidad operativa')
    d.p('El servicio de respaldo está definido para ejecutarse al arrancar y cada 24 horas, con retención de 35 copias locales. Admite cifrado GPG, copia externa y correo ante fallos. Estas protecciones requieren configuración y verificación en el servidor.')
    d.p('La restauración se realiza con las herramientas de django-dbbackup. Debe probarse en una base separada, registrando fecha, archivo y resultados; el manual propone una prueba trimestral. Los procedimientos detallados están en backend/DESPLIEGUE.md.')
    d.sub('Base de esta documentación')
    d.p('El contenido se elaboró a partir del código y documentación local: README, DESPLIEGUE, modelos, servicios, permisos, rutas de API, configuración de seguridad y pantallas React. Las capturas del tutorial muestran la interfaz con datos de demostración; no corresponden a información productiva.',12)
    d.p('Los dos PDF de Equipos de Emergencia se tomaron como referencia de presentación. La información funcional y técnica de este documento corresponde al sistema de ropa hospitalaria y residuos.',12)
    d.y+=18;d.p('Atentamente,',13);d.y+=20;d.p(AUTHOR,14,font='Georgia-Bold');d.p('Elaboración de la documentación<br/>11 de noviembre de 2026',12,color='#4B5563')
    c.showPage();c.save();print(d.path)

if __name__=='__main__':tutorial();technical()
