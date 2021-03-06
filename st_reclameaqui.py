import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import datetime
import altair as alt
import spacy
from PIL import Image
from wordcloud import WordCloud, STOPWORDS
import numpy as np


# Importar dataset
url_dataset = "https://github.com/soilmo/ReclameAqui/blob/main/ra.xlsx?raw=true"
@st.cache(show_spinner=False)
def importar_base(url):
    df = pd.read_excel(url)
    return df

# Lista de empresas
@st.cache(persist=True, max_entries = 20, ttl = 1800, show_spinner=False)
def lista_empresas(df):
    return list(df['empresa'].unique())

# DF filtrado
@st.cache(persist=True, max_entries = 20, ttl = 1800, show_spinner=False)
def filtrar_df(df, empresas_escolhidas):
    for i in empresas_escolhidas:
        filtro = df['empresa']==i
        aux = df[filtro]

        if i == empresas_escolhidas[0]:
            df_filtrado = aux
        else:
            df_filtrado = df_filtrado.append(aux)

    return df_filtrado

# Grafico 6m - Linha
@st.cache(persist=True, max_entries = 20, ttl = 1800, show_spinner=False, allow_output_mutation=True)
def grafico_6m(df,metrica, janela):
    highlight = alt.selection(type='single', on='mouseover',
                          fields=['empresa'], nearest=True)

    base = alt.Chart(df).encode(
        x='data:T',
        y= str(metrica) + str(janela),
        color='empresa:N'
    )

    points = base.mark_circle().encode(
        opacity=alt.value(0),
        tooltip = ['empresa','data',str(metrica) + str(janela)]
    ).add_selection(
        highlight
    ).properties(
        width=600
    ).interactive()

    lines = base.mark_line().encode(
        size=alt.condition(~highlight, alt.value(1), alt.value(3))
    ).interactive()

    return points + lines

@st.cache(persist=True, max_entries = 20, ttl = 1800, show_spinner=False, allow_output_mutation=True)
def grafico_6m_scatter(df,metrica_1, metrica_2, empresas, janela):
    input_dropdown = alt.binding_select(options=empresas)
    selection = alt.selection_single(fields=['empresa'], bind=input_dropdown, name='Dados de')
    color = alt.condition(selection,
                        alt.Color('empresa:N', legend=None),
                        alt.value('lightgray'))

    points = alt.Chart(df).mark_point().encode(
        x=metrica_1 + str(janela),
        y=metrica_2 + str(janela),
        color=color,
        tooltip=['empresa',metrica_1+ str(janela),metrica_2+ str(janela)]
    ).add_selection(
        selection
    ).interactive()
    return points


metricas = ["Avalia????o do Reclame Aqui",'Quantidade de reclama????es','Quantidade de reclama????es respondidas',"Quantidade de reclama????es n??o respondidas",
                    'Percentual das reclama????es respondidas',"Percentual de consumidores que voltariam a fazer neg??cio",
                    '??ndice de solu????o','Nota do consumidor'
                    ]
dict_metricas = {
            'Avalia????o do Reclame Aqui':'nota_',
            'Quantidade de reclama????es':'reclamacao_',
            'Quantidade de reclama????es respondidas':'respondidas_',
            'Quantidade de reclama????es n??o respondidas':'nao_respondidas_',
            'Percentual das reclama????es respondidas':'perc_respondidas_',
            'Percentual de consumidores que voltariam a fazer neg??cio':'perc_voltaria_',
            '??ndice de solu????o':'indice_solucao_',
            'Nota do consumidor':'nota_consumidor_'
        }
dict_descricao = {
    'Avalia????o do Reclame Aqui':'M??dia ponderada dos outros crit??rios',
    'Quantidade de reclama????es':'',
    'Quantidade de reclama????es respondidas':'',
    'Quantidade de reclama????es n??o respondidas':'',
    'Percentual das reclama????es respondidas':'Porcentagem de reclama????es respondidas, sendo que apenas a primeira resposta ?? considerada.',
    'Percentual de consumidores que voltariam a fazer neg??cio':'Corresponde ?? porcentagem de reclama????es onde os consumidores, ao finalizar, informaram que voltariam a fazer neg??cios com a empresa.Leva em considera????o apenas reclama????es finalizadas e avaliadas. Tamb??m chamado de ??ndice de Novos Neg??cios',
    '??ndice de solu????o':'Corresponde ?? porcentagem de reclama????es onde os consumidores, ao finalizar, consideraram que o problema que originou a reclama????o foi resolvido. Leva em considera????o apenas reclama????es finalizadas e avaliadas.',
    'Nota do consumidor':'Corresponde ?? m??dia aritm??tica das notas (variando de 0 a 10) concedidas pelos reclamantes para avaliar o atendimento recebido. Leva em considera????o apenas reclama????es finalizadas e avaliadas.'
}
dict_janelas = {
    '6 meses':'6m',
    '12 meses':'12m',
    '36 meses':'itd'
}


# T??tulo
st.title("Acompanhamento Reclame Aqui")
senha = st.text_input("Senha","Digite a senha")

if senha == "indie2021":
    st.success("Acesso autorizado")
    # Funcionalidades ------------------------
    # Per??odo de an??lise
    st.header("Per??odo de an??lise")
    st.markdown("Dados dispon??veis a partir de 2021-01-01")
    
    dt_i = st.date_input("Qual o dia inicial?", datetime.datetime.now())
    dt_i = dt_i.strftime('%Y-%m-%d')
    
    dt_f = st.date_input("Qual o dia final?", datetime.datetime.now())
    dt_f = dt_f.strftime('%Y-%m-%d')
 
    # Importar base
    df = importar_base(url_dataset)
    filtro_1 = df['data']>=dt_i
    filtro_2 = df['data']<=dt_f
    df = df[(filtro_1) & (filtro_2)]
    
    st.success("Base importada")

    # Escolher as empresas para acompanhar
    empresas = lista_empresas(df)
    empresas_escolhidas = st.multiselect("Quais empresas quer ver?", options = empresas)
    
    if len(empresas_escolhidas)>0:
        df = filtrar_df(df, empresas_escolhidas)
    else:
        st.warning("Escolha pelo menos uma")

    janela = st.selectbox("Qual janela m??vel quer ver?", options = ['6 meses','12 meses','36 meses'])
    
    st.markdown("### Evolu????o temporal")
    # Escolher m??trica
    
    metrica = st.selectbox("Escolha a metrica", options=metricas)
    if dict_descricao[metrica]!="":
        st.success(dict_descricao[metrica])
    
    if len(empresas_escolhidas)>0:
        graf_6m = grafico_6m(df, dict_metricas[metrica], dict_janelas[janela])
        st.write(graf_6m.properties(height=500, width = 700).configure_axis(
                    labelFontSize=15,
                    titleFontSize=15
                ))

    st.markdown("### Dispers??o entre as m??tricas")
    metrica_1 = st.selectbox("Escolha a metrica 1", options=metricas)
    if dict_descricao[metrica_1]!="":
        st.success(dict_descricao[metrica_1])
    metrica_2 = st.selectbox("Escolha a metrica 2", options=metricas)
    if dict_descricao[metrica_2]!="":
        st.success(dict_descricao[metrica_2])
    
    if len(empresas_escolhidas)>0:
        graf_6m_scatter = grafico_6m_scatter(df,dict_metricas[metrica_1], dict_metricas[metrica_2], empresas_escolhidas, dict_janelas[janela])
        st.write(graf_6m_scatter.properties(height=500, width = 700).configure_axis(
                    labelFontSize=15,
                    titleFontSize=15
                ))
        
else:
    st.warning("Senha incorreta")