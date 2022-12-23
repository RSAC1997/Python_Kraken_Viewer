#Usar poetry para instalar las dependencias del proyecto
#pyproject.toml contiene las versiones utilizadas de las librerias
#en la terminal usar el comando streamlit run main.py para ejecutar el proyecto

import krakenex
import pandas as pd
from pykrakenapi import KrakenAPI
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
#Importamos la clase creada valores
from Valores import valores

#iniciamos la conexion al API
api = krakenex.API()
k = KrakenAPI(api)
#En la variable pairs obtenemos un dataframe con todos los pares disponibles en el exchange
pairs = k.get_tradable_asset_pairs()

#Establecemos el titulo a mostrar en streamlit
st.title('Cotizaciones')

#Definimos una funcion que inicalice los valores por defecto que va a tener el grafico al abrirse por primera vez
def valores_predeterminados():
    #generamos un dataframe nuevo unicamenente con la columna altname que tiene el nombre del par
    pairs2 = pairs['altname'].copy()
    #hacemos reset a los indices para que estos queden en indices numericos
    pairs2 = pairs2.reset_index()
    #declaramos la variable valor que es un objeto de clase valores, al enviar sin parametros se colocan los que estan por defecto
    valor = valores()
    try:
        #En esta variable guardamos el indice donde pairs2['altname'] es igual a valor.par (por defecto evalua 'ETHUSDT')
        indice_default = pairs2.index[pairs2['altname'] == valor.par].tolist()
        #Creamos seleccionamos el primer elemento de la lista indice default, que en este caso es el indice, y lo convertimos a int
        indice_default2 = int(indice_default[0])
        #retornamos la variable de tipo valores y el indice que le corresponde al par de la variable valor.par
        return valor,indice_default2
    except:
        #En caso de que no se encuentre el indice del par por defecto se retorna el indice con valor 0
        return valor,0

#en la siguiente linea asignamos los valores a las variable a traves de la funcion valores_predeterminados()
valor, indice_default = valores_predeterminados()

#en la variable par agregamos a streamlit un selectbox donde se muestan todos los pares en pairs['altname'] y en index por defecto se coloca
#el valor que esta en indice_default
par = st.selectbox('Escoge un par:', pairs['altname'],index=indice_default)

#por medio del metodo get_ohlc_data se inicializan las variables ohlc y last
#el parametro pair recibe el valor seleccionado en el selectbox de streamlit y el intervalo se refiere a los minutos presentes en 1 dia
#60 minutos x 24 horas = 1440, es decir que las velas en el grafico de velas representan 1 dia cada una
ohlc, last = k.get_ohlc_data(pair=par, interval=1440)
#hacemos un reset de indices para que estos sean numericos
ohlc = ohlc.reset_index()
#agregamos una columna tiempo al dataframe y le asignamos el valor de ohlc['dtime'] convertido a datetime
ohlc['tiempo'] = pd.to_datetime(ohlc['dtime'])


# media móvil

#Definimos la funcion calculos que recibe el parametro dias y calcula media movil y RSI
#dias es un parametro de tipo int
def calculos(dias):
    try:
        #nos aseguramos que el valor en dias efectivamente sea de tipo entero
        dias = int(dias)
        #agregamos al dataframe una columna de media movil, esta se genera con la media de la columna close con los dias insertados de parametro
        ohlc['media_móvil'] = ohlc['close'].rolling(dias).mean()

        # Cálculo del Rsi
        #calculamos la diferencia de los cierres
        diferencia = ohlc['close'].diff(1)

        #creamos dos arreglos vacios ganancia y perdida, para llenarlos mas adelante
        ganancia = []
        perdida = []

        #En el siguiente for loop evaluamos si la difrencia es positiva o negativa para
        #agregarla al arreglo de ganacia o perdida
        for i in diferencia:

            if i > 0:
                ganancia.append(i)
                perdida.append(0)
            else:
                perdida.append(i)
                ganancia.append(0)

        #una vez culminado el for loop asignamos a perdida el valor absoluto para todos sus valores
        perdida = [abs(x) for x in perdida]
        #convertimos ganancia y perdida en dataframes
        ganancia = pd.DataFrame(ganancia)
        perdida = pd.DataFrame(perdida)

        #obtememos la media ganancia y perdida utilizando el parametro dias y la funcion .mean()
        media_ganancia = ganancia.rolling(dias).mean()
        media_perdida = perdida.rolling(dias).mean()

        #por ultimo obtemos el RSI usando la siguiente formula
        RSI = 100 - (100 / (1 + (media_ganancia / media_perdida)))

        #agregamos al dataframe la columna RSI
        ohlc['RSI'] = RSI

    except ValueError:
        #En caso de que se ingrese un valor en la variable dias que no sea entero se obtiene el siguiente error
        print('El número debe ser un entero')

    return ohlc

#en intervalo almacenamos el input del usuario que inserta en la interfaz de streamlit, se esblece por defecto el valor de valor.dias
intervalo = st.number_input('Escoge un intervalo para la media móvil:', min_value=0, value=valor.dias)

#actualizamos ohlc para que tenga el resultado de la funcion calculos() definida anteriormente
ohlc = calculos(intervalo)

#creamos una variable figura, donde se mostratran las graficas
fig = go.Figure()

#Determinamos el layout y las sub plots que tendra el grafico, en este caso tendra 2 filas y 1 columna
#La primera corresponde a Cotizaciones que es el Grafico de velas y las segunda al grafico de RSI
fig = make_subplots(
    rows=2, cols=1, shared_xaxes=True, subplot_titles=('Cotizaciones', 'RSI'), row_width=[0.3, 0.7]
)
#con add trace agregamos la grafica de velas indicando los parametros respectivos y su posicion en row y column
fig.add_trace(
    go.Candlestick(x=ohlc['tiempo'], open=ohlc['open'], high=ohlc['high'], low=ohlc['low'], close=ohlc['close'],
                   name='Cotizaciones'), row=1, col=1)
#agregamos en el mismo grafico de velas, la linea de media movil para que se muestren en un mismo plano
fig.add_trace(go.Line(x=ohlc['tiempo'], y=ohlc['media_móvil'], marker={'color': 'yellow'}, name='Media_móvil'), row=1,
              col=1)
#Ahora en la segunda fila se agrega el grafico de RSI
fig.add_trace(go.Line(x=ohlc['tiempo'], y=ohlc['RSI'], marker={'color': 'pink'}, name='RSI'), row=2, col=1)

#Finalmente actualizamos el layout y ponemos umbrales(tresholds) en la grafica de RSI que indican los limites superior e inferior
fig.update_layout(
     shapes=[# Top Threshold line
                    {
                        'type': 'line',
                        'xref': 'paper',
                        'yref': 'y2',
                        'x0': 0,
                        'y0': 70, # use absolute value or variable here
                        'x1': 1,
                        'y1': 70, # ditto
                        'line': {
                            'color': 'rgb(0, 100, 0)',
                            'width': 1,
                            'dash': 'dash',
                        },
                    },
                    # Bottom Threshold Line
                    {
                        'type': 'line',
                        'xref': 'paper',
                        'yref': 'y2',
                        'x0': 0,
                        'y0': 30, # use absolute value or variable here
                        'x1': 1,
                        'y1': 30, # ditto
                        'line': {
                            'color': 'rgb(255, 0, 0)',
                            'width': 1,
                            'dash': 'dash',
                        },
                    }])
#Para terminar se muestra en streamlit la grafica creada
st.plotly_chart(fig)

#st.dataframe(ohlc)