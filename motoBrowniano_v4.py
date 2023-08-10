
import streamlit as st
import numpy as np
import plotly.graph_objects as go


def aggiorna_sistema(sistema, dt):
    # Estrai le proprietà del sistema
    num_molecole = sistema["num_molecole"]
    massa_molecola = sistema["massa_molecola"]
    massa_particella_browniana = sistema["massa_particella_browniana"]
    dimensione_sistema = sistema["dimensione_sistema"]
    posizioni = sistema["posizioni"]
    velocita = sistema["velocita"]
    posizione_browniana = sistema["posizione_browniana"]
    velocita_browniana = sistema["velocita_browniana"]

    # Trova tutte le molecole vicine alla molecola browniana
    distanza_collisione = 0.01  # Adegua questo valore come necessario
    distanze = np.linalg.norm(posizioni - posizione_browniana, axis=1)
    collisioni = np.where(distanze < distanza_collisione)[0]

    for i in collisioni:
        # Calcola le velocità finali per ciascuna componente
        m1 = massa_molecola
        m2 = massa_particella_browniana
        for dim in range(2):  # 0: x-component, 1: y-component
            v1i = velocita[i, dim]
            v2i = velocita_browniana[dim]

            v1f = ((m1 - m2) / (m1 + m2)) * v1i + (2 * m2 / (m1 + m2)) * v2i
            v2f = (2 * m1 / (m1 + m2)) * v1i - ((m1 - m2) / (m1 + m2)) * v2i

            # Aggiorna le velocità per la componente corrente
            velocita[i, dim] = v1f
            velocita_browniana[dim] = v2f

    # Calcola le nuove posizioni
    posizioni += velocita * dt
    posizione_browniana += velocita_browniana * dt

    # Gestisci le collisioni con le pareti
    riflessione = (posizioni < 0) | (posizioni > dimensione_sistema)
    velocita[riflessione] *= -1
    posizioni = np.clip(posizioni, 0, dimensione_sistema)

    riflessione_browniana = (posizione_browniana < 0) | (posizione_browniana > dimensione_sistema)
    velocita_browniana[riflessione_browniana] *= -1
    posizione_browniana = np.clip(posizione_browniana, 0, dimensione_sistema)

    # Aggiorna il sistema
    sistema["posizioni"] = posizioni
    sistema["velocita"] = velocita
    sistema["posizione_browniana"] = posizione_browniana
    sistema["velocita_browniana"] = velocita_browniana

    return sistema


def esegui_simulazione(sistema, num_passaggi=1000, dt=0.01):
    stati_simulazione = []
    for _ in range(num_passaggi):
        sistema = aggiorna_sistema(sistema, dt)
        stati_simulazione.append(sistema.copy())
    return stati_simulazione

def crea_animazione_plotly(stati_simulazione, mostra_molecole=True):
    # Configura l'animazione e i controlli
    animation_settings = {
        "frame": {"duration": 100, "redraw": True},
        "fromcurrent": True,
        "transition": {"duration": 100}
    }

    buttons = [
        {"label": "Play", "method": "animate", "args": [None, animation_settings]},
        {"label": "Pause", "method": "animate", "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate", "transition": {"duration": 0}}]},
    ]

    # Estrai il primo stato per configurare il grafico iniziale
    stato_iniziale = stati_simulazione[0]
    
    # Creazione del grafico iniziale
    traces = []
    
    if mostra_molecole:
        trace_molecole = go.Scatter(x=stato_iniziale["posizioni"][:, 0], 
                                    y=stato_iniziale["posizioni"][:, 1], 
                                    mode='markers', 
                                    marker=dict(size=5, opacity=0.5))
        traces.append(trace_molecole)

    trace_browniana = go.Scatter(x=[stato_iniziale["posizione_browniana"][0]], 
                                 y=[stato_iniziale["posizione_browniana"][1]], 
                                 mode='lines', 
                                 line=dict(color='red'))
    traces.append(trace_browniana)

    fig = go.Figure(data=traces)

    # Liste per accumulare le posizioni della molecola browniana
    x_browniana = []
    y_browniana = []
    
    # Lista per raccogliere i frames
    frames_list = []
    
    # Aggiungi frames per ciascun stato
    for stato in stati_simulazione:
        frame_data = []
        
        # Aggiungi la nuova posizione della molecola browniana alle liste
        x_browniana.append(stato["posizione_browniana"][0])
        y_browniana.append(stato["posizione_browniana"][1])
        
        if mostra_molecole:
            frame_molecole = go.Scatter(x=stato["posizioni"][:, 0], y=stato["posizioni"][:, 1], mode='markers')
            frame_data.append(frame_molecole)
        
        # Usa le liste accumulate per creare la traccia della molecola browniana
        frame_browniana = go.Scatter(x=x_browniana, y=y_browniana, mode='lines', marker=dict(size=10, color='red'), line=dict(color='red'))
        frame_data.append(frame_browniana)

        frame = go.Frame(data=frame_data)
        frames_list.append(frame)

    # Assegna la lista dei frames a fig.frames
    fig.frames = frames_list

    fig.update_layout(updatemenus=[{
    "type": 'buttons',
    "showactive": False,
    "buttons": buttons
    }])
    # Configura l'animazione
    #fig.update_layout(updatemenus=[dict(type='buttons', 
    #                                    showactive=False, 
    #                                    buttons=[dict(label='Play', 
    #                                                  method='animate', 
    #                                                  args=[None, dict(frame=dict(duration=100, redraw=True), 
    #                                                                   fromcurrent=True)])])])

    return fig


def app():
    st.title("Simulazione del Moto Browniano")
    
    # Sidebar per l'inserimento dei dati
    with st.sidebar:
        st.header("Parametri del Sistema")
        num_molecole = st.number_input("Numero di molecole", value=10000, min_value=1)
        massa_molecola = st.number_input("Massa della molecola", value=2.0, min_value=0.1)
        massa_particella_browniana = st.number_input("Massa della particella browniana", value=1.0, min_value=0.1)
        dimensione_sistema = st.number_input("Dimensione del sistema", value=1.0, min_value=0.1)
        velocita_media = st.number_input("Velocità media", value=0.1, min_value=0.0)
        mostra_molecole = st.checkbox("Mostra molecole", value=True)
        
        avvia_simulazione = st.button("Avvia Simulazione")

    if avvia_simulazione:
        # Impostare il sistema iniziale
        posizione_browniana = np.array([0.5, 0.5])
        velocita_browniana = np.array([0.1, 0.1], dtype=np.float64)
        posizioni = np.random.rand(num_molecole, 2) * dimensione_sistema
        velocita = np.random.randn(num_molecole, 2) * velocita_media
        
        sistema_iniziale = {
            "num_molecole": num_molecole,
            "massa_molecola": massa_molecola,
            "massa_particella_browniana": massa_particella_browniana,
            "dimensione_sistema": dimensione_sistema,
            "posizioni": posizioni,
            "velocita": velocita,
            "posizione_browniana": posizione_browniana,
            "velocita_browniana": velocita_browniana
        }
        
        # Esegui la simulazione
        stati_simulazione = esegui_simulazione(sistema_iniziale, num_passaggi=1000, dt=0.01)
        
        # Crea e visualizza il grafico animato
        fig = crea_animazione_plotly(stati_simulazione, mostra_molecole=mostra_molecole)
        fig.update_layout(width=800, height=800)
        st.plotly_chart(fig)

if __name__ == "__main__":
    app()