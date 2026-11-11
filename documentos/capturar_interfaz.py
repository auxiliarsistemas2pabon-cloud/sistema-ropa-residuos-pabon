import json
import os
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

OUT=Path(__file__).resolve().parent/'capturas'
OUT.mkdir(exist_ok=True)
role='USUARIO'
logged=True
user={'id':1,'username':'demostracion','first_name':'Eval Samuel','last_name':'Molina Fuertes','documento':None,'rol':'USUARIO','es_administradora':False,'is_superuser':False,'puede_cambiar_su_clave':False}
sedes=[{'id':1,'nombre':'Clínica Pabón','activo':True}]
servicios=[{'id':1,'sede':1,'nombre':'Hospitalización','genera_ropa':True,'genera_residuos':True,'activo':True}]
cats=[{'id':1,'categoria_padre':None,'grupo':'RIESGO_BIOLOGICO','nombre':'Biosanitarios','color_bolsa':'Rojo','activo':True},{'id':2,'categoria_padre':None,'grupo':'NO_PELIGROSO','nombre':'Aprovechables','color_bolsa':'Blanco','activo':True}]
mov={'id':1,'tipo_movimiento':'ROPA_SUCIA_ENTREGA','tipo_movimiento_display':'Entrega de ropa sucia','fecha':'2026-11-11','hora':'10:00:00','jornada':'MANANA','sede':1,'sede_nombre':'Clínica Pabón','area_origen':1,'servicio_nombre':'Hospitalización','estado':'CERRADO','peso_neto':'12.00','entrega_por':{'id':1,'nombre_completo':'Personal de demostración'},'creado_por':{'id':1,'nombre_completo':'Personal de demostración'},'creado_en':'2026-11-11T10:00:00-05:00','detalles_ropa':[],'detalles_residuo':[]}
def handler(route):
    p=urlparse(route.request.url).path.replace('/api/','')
    data=[]
    if p=='auth/me/':
        if not logged:
            route.fulfill(status=403,json={'detail':'Sin sesión'});return
        data={**user,'rol':role,'es_administradora':role=='ADMIN'}
    elif p=='catalogos/sedes/':data=sedes
    elif p=='catalogos/servicios/':data=servicios
    elif p=='usuarios/activos/':data=[{'id':2,'nombre_completo':'Operario de demostración'}]
    elif p=='catalogos/prendas/':data=[{'id':1,'nombre':'Sábana','disposicion':'REUTILIZABLE','controla_unidades':True,'activo':True}]
    elif p=='catalogos/categorias-residuo/':data=cats
    elif p=='catalogos/gestores-externos/':data=[{'id':1,'nombre':'Gestor de demostración','nit':'DEMO','tarifa_kg_vigente':'2500.00','activo':True}]
    elif p=='movimientos/hoy/':data={'fecha':'2026-11-11','movimientos':[mov]}
    elif p=='movimientos/':data={'count':1,'next':None,'previous':None,'results':[mov]}
    elif p=='rotulos/':data={'count':0,'next':None,'previous':None,'results':[]}
    elif p=='ropa/corte-control/':data={'fecha':'2026-11-11','entregas':[mov],'total':'12.00'}
    elif p=='residuos/recolecciones-sin-factura/':data=[{**mov,'tipo_movimiento':'RESIDUO_RECOLECCION'}]
    elif p=='validacion-entrega/desglose/':data={'filas':[{'movimiento':1,'servicio':'Hospitalización','kg':'12.00'}],'total':'12.00'}
    elif p.startswith('consolidados/'):
        data={'filas':[{'movimiento__sede__nombre':'Clínica Pabón','movimiento__area_origen__nombre':'Hospitalización','categoria_residuo__grupo':'NO_PELIGROSO','categoria_residuo__nombre':'Aprovechables','jornada':'MANANA','kg':'12.00','ropa_kg':'12.00','residuos_kg':'3.00','movimientos':1}],'total':'12.00'}
    elif p=='rh1/':data={'columnas':[{'id':1,'orden':1,'nombre':'Biosanitarios','grupo':'RIESGO_BIOLOGICO','categorias':[],'activo':True}],'filas':[{'fecha':'2026-11-11','celdas':['3.00'],'total':'3.00'}],'totales_columna':['3.00'],'total_mes':'3.00'}
    elif p=='facturacion/resumen/':data={'periodo':'2026-11-01','actual':[],'pendientes_anteriores':[],'total_actual':'0','total_pendientes':'0','total_general':'0'}
    elif p=='facturacion/conciliacion/':data={'filas':[]}
    elif p=='novedades/':data={'count':0,'next':None,'previous':None,'results':[]}
    route.fulfill(status=200,json=data,headers={'Access-Control-Allow-Origin':'http://127.0.0.1:5173','Access-Control-Allow-Credentials':'true'})

with sync_playwright() as pw:
    executable=next((Path(os.environ['LOCALAPPDATA'])/'ms-playwright/chromium_headless_shell-1243').rglob('chrome-headless-shell.exe'))
    browser=pw.chromium.launch(headless=True,executable_path=str(executable))
    page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
    page.route('http://127.0.0.1:8000/api/**',handler)
    page.emulate_media(reduced_motion='reduce')
    def snap(name,path,setup=None):
        page.goto('http://127.0.0.1:5173'+path)
        page.wait_for_timeout(1100)
        if setup: setup()
        page.wait_for_timeout(300)
        page.screenshot(path=str(OUT/(name+'.png')))
        print(name,page.locator('h1').all_text_contents())
    logged=False;snap('acceso','/acceso');logged=True
    snap('panel','/')
    def origen():
        page.locator('#sede').select_option('1');page.wait_for_timeout(250)
        area=page.locator('#area_origen')
        if area.count():area.select_option('1')
    snap('sucia','/ropa/entrega-sucia',origen)
    def peso():
        origen();page.get_by_role('button',name='Continuar').first.click();page.locator('#peso_total').fill('12.50');page.locator('#tara').fill('0.50')
    snap('pesaje','/ropa/entrega-sucia',peso)
    snap('recepcion','/ropa/limpia/recepcion',lambda:page.locator('#sede').select_option('1'))
    snap('distribucion','/ropa/limpia/distribucion',lambda:page.locator('#sede').select_option('1'))
    snap('rotulos','/ropa/rotulos',lambda:page.locator('#sede').select_option('1'))
    snap('validacion','/validacion')
    snap('generacion','/residuos/generacion')
    snap('recoleccion','/residuos/recoleccion')
    role='ADMIN'
    snap('reportes','/consolidados')
    snap('rh1','/rh1-facturacion')
    snap('gestor','/residuos/entrega-gestor')
    snap('novedades','/novedades')
    browser.close()
