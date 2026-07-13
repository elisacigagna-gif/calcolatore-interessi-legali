import streamlit as st
from datetime import date, timedelta

# --- LOGICA DI CALCOLO ---
def ottieni_tasso(data_corrente):
    tassi_storici = [
        (date(2026, 1, 1), 1.60),  
        (date(2025, 1, 1), 2.00),  
        (date(2024, 1, 1), 2.50),  
        (date(2023, 1, 1), 5.00),  
    ]
    for data_tasso, tasso in tassi_storici:
        if data_corrente >= data_tasso:
            return tasso
    return 0.0

def calcola_interessi_legali(capitale, data_inizio, data_fine):
    interessi_totali = 0.0
    data_corrente = data_inizio + timedelta(days=1)
    
    while data_corrente <= data_fine:
        tasso_annuo = ottieni_tasso(data_corrente)
        interesse_giornaliero = capitale * (tasso_annuo / 100) / 365
        interessi_totali += interesse_giornaliero
        data_corrente += timedelta(days=1)
        
    return interessi_totali

def formatta_euro(numero):
    return f"{numero:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# --- INTERFACCIA WEB MULTIPLA ---
st.title("⚖️ Calcolatore Interessi Legali (Multiplo)")
st.write("Aggiungi i tuoi capitali e assegna a ciascuno un nome di riferimento.")

# Scelta del numero di capitali da inserire
num_capitali = st.number_input("Quante voci/capitali devi inserire?", min_value=1, max_value=20, value=1, step=1)
st.divider()

dati_capitali = []

# Creazione dinamica degli spazi di inserimento
for i in range(int(num_capitali)):
    st.markdown(f"### 📌 Pratica {i+1}")
    
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input(f"Nome Riferimento (es. Fattura 123)", key=f"nome_{i}")
        capitale = st.number_input(f"Capitale (€)", min_value=0.0, value=0.0, step=100.0, key=f"cap_{i}")
    with col2:
        data_inizio = st.date_input(f"Data Inizio", value=date(2023, 1, 1), key=f"inizio_{i}")
        data_fine = st.date_input(f"Data Fine", value=date.today(), key=f"fine_{i}")
        
    # Salviamo i dati inseriti dall'utente
    dati_capitali.append({
        "nome": nome if nome.strip() != "" else f"Pratica {i+1} (Senza Nome)",
        "capitale": capitale,
        "inizio": data_inizio,
        "fine": data_fine
    })
    st.divider()

# Calcolo e Resoconto finale
if st.button("Calcola Tutto", type="primary"):
    totale_interessi_globale = 0.0
    totale_capitale_globale = 0.0
    
    st.header("🧾 Resoconto Calcoli")
    
    for dato in dati_capitali:
        if dato["capitale"] > 0:
            if dato["inizio"] > dato["fine"]:
                st.error(f"Errore nella {dato['nome']}: la data di fine è precedente a quella di inizio.")
                continue
                
            interessi = calcola_interessi_legali(dato["capitale"], dato["inizio"], dato["fine"])
            totale_capitale = dato["capitale"] + interessi
            
            totale_capitale_globale += dato["capitale"]
            totale_interessi_globale += interessi
            
            # Stampa il dettaglio della singola voce
            st.markdown(f"**{dato['nome']}** (dal {dato['inizio'].strftime('%d/%m/%Y')} al {dato['fine'].strftime('%d/%m/%Y')})")
            st.write(f"- Capitale iniziale: € {formatta_euro(dato['capitale'])}")
            st.write(f"- Interessi maturati: € {formatta_euro(interessi)}")
            st.write(f"- **Subtotale da pagare: € {formatta_euro(totale_capitale)}**")
            st.write("") 
            
    # Stampa il totale generale
    st.success(f"### 💰 TOTALE GENERALE DA PAGARE: € {formatta_euro(totale_capitale_globale + totale_interessi_globale)}")
    st.info(f"*(Di cui € {formatta_euro(totale_capitale_globale)} di capitale e € {formatta_euro(totale_interessi_globale)} di interessi)*")
