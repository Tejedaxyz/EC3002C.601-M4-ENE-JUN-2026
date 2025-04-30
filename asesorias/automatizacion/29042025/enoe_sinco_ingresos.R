####### AGREGANDO ESQUEMA DE MUESTREO

################# Cargamos las biblioecas necesarias ####################3
library(questionr)
library(survey)

###############################################
### Definimos una ruta temporal para guardar los microdatos
temporal <- tempfile()
download.file("https://www.inegi.org.mx/contenidos/programas/enoe/15ymas/microdatos/enoe_n_2021_trim4_csv.zip",temporal)
files = unzip(temporal, list=TRUE)$Name
unzip(temporal, files=files[grepl("csv",files)])

sdemt <- read.csv("ENOEN_SDEMT421.csv")
coe1 <- read.csv("ENOEN_COE1T421.csv")

sdemt$folio <- paste(sdemt$cd_a, sdemt$ent, sdemt$con, sdemt$v_sel, sdemt$n_hog, 
                     sdemt$h_mud, sdemt$n_ren)

coe1$folio <- paste(coe1$cd_a, coe1$ent, coe1$con, coe1$v_sel, coe1$n_hog, 
                    coe1$h_mud, coe1$n_ren)

enoe <- merge(coe1, sdemt, by = "folio")

# Se selecciona la población de referencia que es: población ocupada mayor de 15 años con entrevista completa y condición de residencia válida.
enoe <- subset(enoe, enoe$clase2 == 1 & enoe$eda.x>=15 & enoe$eda.x<=98 & enoe$r_def.x==0 & (enoe$c_res==1 | enoe$c_res==3))

## Sugiero dos opciones : 
## 1) Imputar ingresos
## 2) Remover los registros que no declaran ingresos
## Voy a escoger la opción 2 para el ejercicio, pero preferiría usar la opción 1.
enoe <- subset(enoe, ingocup!=0)

# Definimos el esquema de muestreo
enoedesign<-svydesign(id=~upm.x, strata=~est_d_tri, weight=~fac_tri.x, data=enoe, nest=TRUE)
options(survey.lonely.psu="adjust")

## Calculamos el ingreso promedio mensual de las categorías del sinco
ingreso_promedio_mensual_sinco <- svyby(~ingocup, ~p3, enoedesign, svymean, vartype=c("se","cv"))


