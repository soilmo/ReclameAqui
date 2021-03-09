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


metricas = ["Avaliação do Reclame Aqui",'Quantidade de reclamações','Quantidade de reclamações respondidas',"Quantidade de reclamações não respondidas",
                    'Percentual das reclamações respondidas',"Percentual de consumidores que voltariam a fazer negócio",
                    'Índice de solução','Nota do consumidor'
                    ]
dict_metricas = {
            'Avaliação do Reclame Aqui':'nota_',
            'Quantidade de reclamações':'reclamacao_',
            'Quantidade de reclamações respondidas':'respondidas_',
            'Quantidade de reclamações não respondidas':'nao_respondidas_',
            'Percentual das reclamações respondidas':'perc_respondidas_',
            'Percentual de consumidores que voltariam a fazer negócio':'perc_voltaria_',
            'Índice de solução':'indice_solucao_',
            'Nota do consumidor':'nota_consumidor_'
        }
dict_descricao = {
    'Avaliação do Reclame Aqui':'Média ponderada dos outros critérios',
    'Quantidade de reclamações':'',
    'Quantidade de reclamações respondidas':'',
    'Quantidade de reclamações não respondidas':'',
    'Percentual das reclamações respondidas':'Porcentagem de reclamações respondidas, sendo que apenas a primeira resposta é considerada.',
    'Percentual de consumidores que voltariam a fazer negócio':'Corresponde à porcentagem de reclamações onde os consumidores, ao finalizar, informaram que voltariam a fazer negócios com a empresa.Leva em consideração apenas reclamações finalizadas e avaliadas. Também chamado de Índice de Novos Negócios',
    'Índice de solução':'Corresponde à porcentagem de reclamações onde os consumidores, ao finalizar, consideraram que o problema que originou a reclamação foi resolvido. Leva em consideração apenas reclamações finalizadas e avaliadas.',
    'Nota do consumidor':'Corresponde à média aritmética das notas (variando de 0 a 10) concedidas pelos reclamantes para avaliar o atendimento recebido. Leva em consideração apenas reclamações finalizadas e avaliadas.'
}
dict_janelas = {
    '6 meses':'6m',
    '12 meses':'12m',
    '36 meses':'itd'
}


# Título
st.title("Acompanhamento Reclame Aqui")
senha = st.text_input("Senha","Digite a senha")

if senha == "indie2021":
    st.success("Acesso autorizado")
    # Funcionalidades ------------------------
    # Período de análise
    st.header("Período de análise")
    st.markdown("Dados disponíveis a partir de 2021-01-01")
    
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

    janela = st.selectbox("Qual janela móvel quer ver?", options = ['6 meses','12 meses','36 meses'])
    
    st.markdown("### Evolução temporal")
    # Escolher métrica
    
    metrica = st.selectbox("Escolha a metrica", options=metricas)
    if dict_descricao[metrica]!="":
        st.success(dict_descricao[metrica])
    
    if len(empresas_escolhidas)>0:
        graf_6m = grafico_6m(df, dict_metricas[metrica], dict_janelas[janela])
        st.write(graf_6m.properties(height=500, width = 700).configure_axis(
                    labelFontSize=15,
                    titleFontSize=15
                ))

    st.markdown("### Dispersão entre as métricas")
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