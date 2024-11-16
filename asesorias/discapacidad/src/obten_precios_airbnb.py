import pandas as pd 
import numpy as np
import geopandas as gpd 

import os 
import glob
import re 

from shapely.geometry import Point

FILE_PATH = os.getcwd()

def build_path(PATH):
    return os.path.abspath(os.path.join(*PATH))


DATA_PATH = build_path([FILE_PATH, "..", "datos", "colonias_airbnb_132"])
DATA_AIRBNB_FILES_PATH = glob.glob(DATA_PATH + "/*.csv")


## --------- Cargamos poligonos de agebs 
agebs = gpd.read_file('https://github.com/milocortes/crecimiento_urbano/raw/main/datos/agebs_ZM_del_Valle_de_Mexico_2020.geojson')

agebs = agebs.query("CVE_ENT =='09'")
bounds = agebs.total_bounds


### -------- CARGAMOS DATOS DE AIRBNB 

airbnb_dta = pd.concat([pd.read_csv(i) for i in DATA_AIRBNB_FILES_PATH], ignore_index=True)

airbnb_dta = airbnb_dta.drop(columns="Unnamed: 0")

airbnb_dta = airbnb_dta[airbnb_dta.name.notnull()]


airbnb_dta['property_id'] = [re.findall(r'/rooms/(?:plus/)?(\d+)', url)[0] for url in 
                               airbnb_dta.url] 



airbnb_dta.drop_duplicates(subset = ['property_id','lat','lng'], inplace = True) 
tipo_aribnb = {'departamento':['apartment','loft'],
               'casa':['condo','place','home', 'guesthouse','vacation',
                       'cabin','hut', 'dome','chalet','townhouse','casa',
                       'villa', 'tiny', 'earthen', 'cottage','ranch','campsite',
                       'treehouse','nature', 'barn', 'houseboat', 'boat',
                       'yurt','farm','holiday','castle'],
               'cuarto':['room','guest','shared', 'bungalow', 'tower'],
               'hotel':['hotel', 'boutique', 'bed','hostel',
                        'aparthotel','resort','pension'],
               'otros':['shipping', 'camper/rv', 'tent','train', 'island',
                        'cave','nan']}
def LimpiarAirbnb(tipo):
    tipo = str(tipo).lower().split()[0]
    real_type = ''
    for element in tipo_aribnb:
        if tipo in tipo_aribnb[element]:
            real_type = element
    return real_type
airbnb_dta['tipo'] = airbnb_dta['name'].apply(LimpiarAirbnb)    

def LimpiarCuartos(beds):
    bed = np.nan
    if 'bed' in str(beds):
        bed = beds.split()[0]
    return bed
airbnb_dta['camas'] = airbnb_dta['rooms'].apply(LimpiarCuartos)        
airbnb_dta['camas'] = ['1' if (pd.isna(cama) and tipo in ['cuarto','hotel']) else cama for cama, tipo in zip(airbnb_dta.camas, airbnb_dta.tipo)]  

monedas = {'HKD':0.12769587, 'TWD':0.032159858, 'MXN':0.058635363,'COP':0.00024147869,
           'zł':0.24501856, 'SEK':0.092341206,'₺': 0.038461893,'₽': 0.011018397,
           'NOK': 0.093966986, 'CHF': 1.1146735, 'R$':0.20657099, 'S/': 0.20193284023668637, 
           '¥': 0.0069218008, '₩': 0.00077226686, '₪': 0.2699522 , '€': 1.0882822,
           'Rp': 0.000066303195, '₡': 0.0018358301, 'CLP': 0.0012543981, 
           'Ft': 0.0028539312, '฿': 0.028571305, 'Kč':0.045656116,
           'UYU': 0.026653931, 'MAD': 0.10247023, '￥':0.12008113283582089,
           '₱': 0.017996175, 'lei': 0.040488343, 'DKK': 0.14573806,
           'JMD': 0.0064633212, 'Rs': 0.012184037}


def limpiar_precio(pp):
    pp = pp.replace(',','')
    pattern = r"(\d+,*\d*)" 
    price = int(re.findall(pattern, pp)[0])
    for moneda in monedas:
        if moneda in pp:
            price  = price*monedas[moneda]
    return price

airbnb_dta['precio_dls'] = airbnb_dta['price'].apply(limpiar_precio)


airbnb_dta['precio_mx'] = np.round(airbnb_dta['precio_dls']/0.058635363,2)


airbnb_dta = airbnb_dta[['name', 'tipo', 'camas', 'precio_mx', 'lat', 'lng']]
airbnb_dta['descripcion'] = ['Tipo: ' + str(tipo) + '\n' + 'Camas: ' + str(camas) + 
                               '\n' + 'Cuartos: '  + '\n' + 
                               'Precio x noche: ' + str(precio_mx) for tipo, camas, precio_mx
                               in zip(airbnb_dta.tipo, airbnb_dta.camas,airbnb_dta.precio_mx)]

# quitar cosas fuera de la cdmx: 
airbnb_dta['no_drop'] = [1 if (bounds[1] <= lat <= bounds[3]) and 
                              (bounds[0] <= lng <= bounds[2]) else 0 
                              for lat,lng in zip(airbnb_dta['lat'],
                                                 airbnb_dta['lng'])] 


airbnb_dta = airbnb_dta[airbnb_dta.no_drop == 1]  
airbnb_dta['geometry'] = airbnb_dta.apply(lambda x: Point((x.lng, x.lat)), axis = 1)
airbnb_crs = {'init': 'epsg:4326'}

## Convertimos el dataframe de airbnb a geodataframe
airbnb_geo = gpd.GeoDataFrame(airbnb_dta, 
                                crs = airbnb_crs, 
                                geometry = airbnb_dta.geometry)


#agebs.boundary.plot(figsize=(10, 10),ax=airbnb_geo.plot(figsize=(15, 15),color ='red'))

agebs_precio_promedio = {}
agebs_conteos_airbnb = {}

for i in range(agebs.shape[0]):
    print(i)
    try:
        agebs_precio_promedio[agebs["CVEGEO"].iloc[i]] = airbnb_geo[agebs["geometry"].iloc[i].contains(airbnb_geo["geometry"])].precio_mx.mean()
        agebs_conteos_airbnb[agebs["CVEGEO"].iloc[i]] = airbnb_geo[agebs["geometry"].iloc[i].contains(airbnb_geo["geometry"])].shape[0]

    except:
        agebs_precio_promedio[agebs["CVEGEO"].iloc[i]] = 0.0
        agebs_conteos_airbnb[agebs["CVEGEO"].iloc[i]] = 0


agebs["precio_promedio_x_noche_pesos_airbnb"] = agebs["CVEGEO"].replace(agebs_precio_promedio).replace(np.nan, 0.0)
agebs["conteos_airbnb"] = agebs["CVEGEO"].replace(agebs_conteos_airbnb).replace(np.nan, 0.0)

## Visualizamos los precios promedio por agebs
agebs.plot(column='precio_promedio_x_noche_pesos_airbnb', legend=True,figsize=(10, 10))
plt.title("Precio promedio por noche de airbnb)")
plt.show()

### Agregamos datos de complejidad
## Complejidad agebs
complejidad_agebs = pd.read_csv("complejidad_agebs.zip").drop_duplicates(subset=["CVEGEO"])

## Hacemos el merge
agebs = agebs.merge(right=complejidad_agebs, on = "CVEGEO", how = "inner")

agebs.plot(column='eci', legend=True,figsize=(10, 10))
plt.title("Indice de complejida económica para AGEBs de CDMX.\n(Estimado usando unidades económicas de DENUE)")
plt.show()



#### CONSTRUYE INDICADOR RANKING CON LOS PESOS ASOCIADOS AL ECI Y AL PRECIO AIRBNB
agebs["precio_promedio_x_noche_pesos_airbnb_normalizado"] = (agebs["precio_promedio_x_noche_pesos_airbnb"] - agebs["precio_promedio_x_noche_pesos_airbnb"].mean())/ agebs["precio_promedio_x_noche_pesos_airbnb"].std()

peso_eci = 0.8
peso_airbnb = 0.2

agebs["ranking"] = peso_eci * agebs["eci"] + peso_airbnb * agebs["precio_promedio_x_noche_pesos_airbnb_normalizado"]


agebs["eci_deciles"] = pd.qcut(agebs['ranking'], 10, labels=False)

fig, ax = plt.subplots(1, figsize=(14,8))
agebs.plot(column='eci_deciles', categorical=True, cmap='Spectral', linewidth=.6, edgecolor='0.2',
         legend=True, legend_kwds={'bbox_to_anchor':(.3, 1.05),'fontsize':16,'frameon':False}, ax=ax)

plt.show()

#### Graficamos los 80 agebs de los deciles 4 y 5 que estan mejor rankeados
agebs_priorizados = agebs.query("eci_deciles==5 or eci_deciles==6").sort_values("ranking").iloc[-80:]["CVEGEO"].to_list()
agebs["agebs_priorizados"] = 0
agebs.loc[agebs.CVEGEO.isin(agebs_priorizados), "agebs_priorizados"] = 1

fig, ax = plt.subplots(1, figsize=(14,8))
agebs.plot(column='agebs_priorizados', categorical=True, linewidth=.6, edgecolor='0.2',
         legend=True, legend_kwds={'bbox_to_anchor':(.3, 1.05),'fontsize':16,'frameon':False}, ax=ax)

plt.show()


agebs.to_csv("agebs_priorizado.csv", index = False)