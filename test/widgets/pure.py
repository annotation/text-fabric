import streamlit as st
from tf.app import use


def dh(html):
    st.markdown(html, unsafe_allow_html=True)


# @st.cache
def loadCorpus():
    A = use("bhsa", silent="deep")
    return A


def initDisplay(A):
    css = A.getCss()
    dh(css)


A = loadCorpus()
initDisplay(A)

T = A.api.T
v = T.nodeFromSection(("Genesis", 1, 1))
html = A.pretty(v, _asString=True)


st.title('Editable')

dh(html)
