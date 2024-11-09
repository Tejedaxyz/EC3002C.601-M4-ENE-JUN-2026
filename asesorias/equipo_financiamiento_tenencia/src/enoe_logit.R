####### AGREGANDO ESQUEMA DE MUESTREO

################# Cargamos las biblioecas necesarias ####################3
library(questionr)
library(survey)
library(ggplot2)

###############################################
### Definimos una ruta temporal para guardar los microdatos
temporal <- tempfile()
download.file("https://www.inegi.org.mx/contenidos/programas/enoe/15ymas/microdatos/enoe_n_2021_trim4_csv.zip",temporal)
files = unzip(temporal, list=TRUE)$Name
unzip(temporal, files=files[grepl("csv",files)])
sdemt <- read.csv("ENOEN_SDEMT421.csv")


# Se selecciona la población de referencia que es: población ocupada mayor de 15 años con entrevista completa y condición de residencia válida.
sdemt <- subset(sdemt, sdemt$clase2 == 1 & sdemt$eda>=15 & sdemt$eda<=98 & sdemt$r_def==0 & (sdemt$c_res==1 | sdemt$c_res==3))

## Regresión logística ponderada por el esquema de muestreo
## La siguiente regresión logística utiliza como variable de respuesta la variable binaria
## emp_ppal (1 - Empleo informal, 2 - Empleo formal) y las siguientes variables explicativas
## * anios_esc : Años de escolaridad
## * ingocup : Ingreso mensual
## * sex : Sexo (1 - Hombre, 2 - Mujer)

## Modificamos las etiquetas de las variables del modelo
sdemt$emp_ppal[sdemt$emp_ppal==1] <- 1 # 1 - Empleo informal
sdemt$emp_ppal[sdemt$emp_ppal==2] <- 0 # 0 - Empleo formal

sdemt$sex[sdemt$sex==1] <- 0 # 0 - Hombre
sdemt$sex[sdemt$sex==2] <- 1 # 1 - Mujer

# Definimos el esquema de muestreo
sdemtdesign<-svydesign(id=~upm, strata=~est_d_tri, weight=~fac_tri, data=sdemt, nest=TRUE)
options(survey.lonely.psu="adjust")


modelo <- svyglm( emp_ppal ~ sex + anios_esc + ingocup, design=sdemtdesign,family = quasibinomial(), na.action = na.omit)

modelo$coefficients

## Usaremos los coeficientes para calcular la probabilidad de tener un empleo informal dado que
## * Se es mujer (sex = 1)
## * Años de escolaridad promedio de una mujer
## * Ingresos promedio mensual de una mujer

## Calculamos los años de escolaridad promedio de mujeres y hombres
svyby(~anios_esc, ~sex, sdemtdesign, svymean, vartype=c("se","cv"))
# Años de escolaridad de mujeres --> 11 años

## Calculamos el ingreso promedio mensual de hombres y mujeres
svyby(~ingocup, ~sex, sdemtdesign, svymean, vartype=c("se","cv"))
# Ingresos promedio mensuales de mujeres  --> 4232.285 pesos mensuales

intercepto <- modelo$coefficients[1] # 2.442195 
beta_sexo <- modelo$coefficients[2] # 0.09178527
beta_escolaridad <- modelo$coefficients[3] # -0.1790409
beta_ingreso <- modelo$coefficients[4] # -7.116697e-05

probabilidad_predicha <- exp( intercepto + beta_sexo*1 + beta_escolaridad*11 + beta_ingreso*4232.285)/ (1 + exp( intercepto + beta_sexo*1 + beta_escolaridad*11 + beta_ingreso*4232.285))
probabilidad_predicha

## La probabilidad que una mujer con 11 años de escolaridad e ingreso mensual de 4232.285 pesos tenga un empleo informal es de 56.54%

## USAREMOS ESTOS COEFICIENTES PARA CALCULAR LAS PROBABILIDADES QUE UNA MUJER TENGA UN EMPLEO INFORMAL 
## DADO EL INGRESO Y LOS AÑOS DE ESCOLARIDAD PROMEDIO DEL MUNICIPIO.
## COMO INGRESO, USAREMOS EL DEL CENSO ECONÓMICO COMO PROXY DE INGRESO
## PARA LOS AÑOS DE ESCOLARIDAD USAREMOS LA VARIABLE "" DEL CENSO Y POBLACIÓN Y VIVIENDA
