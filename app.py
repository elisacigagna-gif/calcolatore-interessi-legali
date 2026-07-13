import streamlit as st
from datetime import date, timedelta
import io
import xlsxwriter

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

def formatta_euro(numero):
    return f"{numero:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# --- INTERFACCIA WEB ---
st.title("⚖️ Calcolatore Interessi Legali (con Formule Excel)")
st.write("Aggiungi i tuoi capitali. Il sistema creerà un file Excel con il dettaglio e le formule vere.")

num_capitali = st.number_input("Quante voci/capitali devi inserire?", min_value=1, max_value=20, value=1, step=1)
st.divider()

dati_capitali = []

for i in range(int(num_capitali)):
    st.markdown(f"### 📌 Pratica {i+1}")
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input(f"Nome Riferimento", key=f"nome_{i}", value=f"Pratica {i+1}")
        capitale = st.number_input(f"Capitale (€)", min_value=0.0, value=0.0, step=100.0, key=f"cap_{i}")
    with col2:
        data_inizio = st.date_input(f"Data Inizio", value=date(2023, 1, 1), key=f"inizio_{i}")
        data_fine = st.date_input(f"Data Fine", value=date.today(), key=f"fine_{i}")
        
    dati_capitali.append({
        "nome": nome,
        "capitale": capitale,
        "inizio": data_inizio,
        "fine": data_fine
    })
    st.divider()

# Calcolo e Creazione File Excel
if st.button("Calcola Tutto ed Esporta", type="primary"):
    st.header("🧾 Resoconto Calcoli")
    
    # Prepariamo il VERO file Excel dietro le quinte
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet('Calcolo Interessi')
    
    # Stili grafici per abbellire l'Excel
    formato_intestazione = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
    formato_valuta = workbook.add_format({'num_format': '#,##0.00 €', 'border': 1})
    formato_normale = workbook.add_format({'border': 1})
    formato_tasso = workbook.add_format({'num_format': '0.00"%"', 'border': 1})
    
    # Scrittura riga delle Intestazioni in Excel
    intestazioni = ["Nome Pratica", "Capitale", "Dal", "Al", "Giorni", "Tasso Annuo", "Interessi (FORMULA)"]
    for col, nome_col in enumerate(intestazioni):
        worksheet.write(0, col, nome_col, formato_intestazione)
        worksheet.set_column(col, col, 16) # Allarga le colonne
        
    riga_excel = 1
    totale_capitale_globale = 0.0
    totale_interessi_globale = 0.0
    
    for dato in dati_capitali:
        if dato["capitale"] > 0 and dato["inizio"] <= dato["fine"]:
            
            # Scomponiamo le date raggruppando i giorni per ogni tasso diverso
            data_corrente = dato["inizio"] + timedelta(days=1)
            periodi = []
            periodo_corrente = None
            
            while data_corrente <= dato["fine"]:
                tasso = ottieni_tasso(data_corrente)
                if periodo_corrente is None:
                    periodo_corrente = {'inizio': data_corrente, 'fine': data_corrente, 'tasso': tasso, 'giorni': 1}
                elif tasso == periodo_corrente['tasso']:
                    periodo_corrente['fine'] = data_corrente
                    periodo_corrente['giorni'] += 1
                else:
                    periodi.append(periodo_corrente)
                    periodo_corrente = {'inizio': data_corrente, 'fine': data_corrente, 'tasso': tasso, 'giorni': 1}
                data_corrente += timedelta(days=1)
            
            if periodo_corrente:
                periodi.append(periodo_corrente)
            
            interessi_pratica = 0.0
            
            # Scriviamo in Excel la riga per ogni "spezzone" di tasso
            for p in periodi:
                worksheet.write(riga_excel, 0, dato["nome"], formato_normale)
                worksheet.write_number(riga_excel, 1, dato["capitale"], formato_valuta)
                worksheet.write(riga_excel, 2, p["inizio"].strftime('%d/%m/%Y'), formato_normale)
                worksheet.write(riga_excel, 3, p["fine"].strftime('%d/%m/%Y'), formato_normale)
                worksheet.write_number(riga_excel, 4, p["giorni"], formato_normale)
                worksheet.write_number(riga_excel, 5, p["tasso"] / 100, formato_tasso)
                
                # INSERIAMO LA FORMULA VERA: =Capitale * Giorni * Tasso / 365
                riga_reale = riga_excel + 1
                formula = f"=B{riga_reale}*E{riga_reale}*F{riga_reale}/365"
                worksheet.write_formula(riga_excel, 6, formula, formato_valuta)
                
                # Teniamo traccia del totale a schermo
                interessi_riga = dato["capitale"] * (p["tasso"] / 100) * p["giorni"] / 365
                interessi_pratica += interessi_riga
                riga_excel += 1
            
            totale_capitale_globale += dato["capitale"]
            totale_interessi_globale += interessi_pratica
            
            # Stampa un mini-resoconto a schermo
            st.markdown(f"**{dato['nome']}**")
            st.write(f"- Capitale iniziale: € {formatta_euro(dato['capitale'])}")
            st.write(f"- Interessi maturati: € {formatta_euro(interessi_pratica)}")
            st.write(f"- **Subtotale da pagare: € {formatta_euro(dato['capitale'] + interessi_pratica)}**")
            st.write("") 
    
    # Creiamo la riga per il Somma Totale nell'Excel
    worksheet.write(riga_excel, 0, "TOTALE", formato_intestazione)
    worksheet.write_number(riga_excel, 1, totale_capitale_globale, formato_valuta)
    worksheet.write(riga_excel, 5, "TOT. INTERESSI:", formato_intestazione)
    
    if riga_excel > 1:
        # Inseriamo la formula della Somma =SUM(...)
        formula_somma = f"=SUM(G2:G{riga_excel})"
        worksheet.write_formula(riga_excel, 6, formula_somma, formato_valuta)
    
    workbook.close()
    
    st.success(f"### 💰 TOTALE GENERALE DA PAGARE: € {formatta_euro(totale_capitale_globale + totale_interessi_globale)}")
    st.divider()
    
    # Pulsante magico di Download per il VERO file Excel
    st.markdown("### 💾 Scarica il tuo Resoconto")
    st.download_button(
        label="📥 Scarica Foglio Excel (.xlsx)",
        data=output.getvalue(),
        file_name="Dettaglio_Interessi_Formule.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
