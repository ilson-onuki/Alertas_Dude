import glob
import pandas as pd
import re
from bs4 import BeautifulSoup

# Lista para armazenar os dados extraídos
all_data = []

# Encontra todos os arquivos messagesXX.html na pasta Telegram
for filepath in glob.glob("Telegram/messages*.html"):
    with open(filepath, "r", encoding="utf-8") as file:
        conteudo = file.read()
        
    # Parseia o conteúdo HTML
    soup = BeautifulSoup(conteudo, 'lxml')
    
    # Extrai as tags com classe "pull_right date details"
    date_tags = soup.find_all(class_="pull_right date details")
    
    # Extrai as tags com classe "text"
    text_tags = soup.find_all(class_="text")
    
    # Itera sobre as tags e armazena o texto, data/hora e título completo
    for date_tag, text_tag in zip(date_tags, text_tags):
        time_displayed = date_tag.get_text(strip=True)  # Texto visível da hora (05:52)
        datetime_full = date_tag.get('title')[:10]  # Atributo title com data e hora completas
        message_text = text_tag.get_text(strip=True)  # Texto da mensagem
        
        # Divide a mensagem em duas partes
        if "passou para o status" in message_text:
            part1, part2 = message_text.split("passou para o status", 1)
        else:
            part1, part2 = message_text, ""
        
        # Usando regex para dividir a parte do "Dispositivo" em duas partes
        match = re.match(r"(?i)O serviço\s(.*?)\sno dispositivo\s(.+)", part1.strip())
        if match:
            service = match.group(1).strip()  # Palavra entre "O serviço" e "no dispositivo"
            device = match.group(2).strip()  # Parte após "no dispositivo"
        else:
            service = part1.strip()  # Se não encontrar o padrão, usa o texto inteiro
            device = ""
        
        # Elimina tudo depois do primeiro parêntese em "Status"
        status_cleaned = re.sub(r"\(.*\)", "", part2.strip()).strip()

        all_data.append({
            "Data": datetime_full,
            "Hora": time_displayed,
            "Serviço": service,  # Agora contém o serviço sem "O serviço"
            "Dispositivo": device,  # Agora contém o dispositivo
            "Status": status_cleaned  # Status sem o conteúdo após os parênteses
        })

# Converte os dados em um DataFrame do pandas
df = pd.DataFrame(all_data)

# Filtra as linhas onde 'Dispositivo' não está vazio
df = df[df['Dispositivo'].str.strip() != '']

# Converte a coluna 'Data' para o formato de data
df["Data"] = pd.to_datetime(df["Data"], format="%d.%m.%Y")

# Converte a coluna 'Hora' para o formato de hora
df["Hora"] = pd.to_datetime(df["Hora"], format="%H:%M").dt.time

# Função para determinar a condição da nova coluna
def categorize_device(device):
    if device.startswith("PTP"):
        return "PTP"
    elif device.startswith("NET"):
        return "Setor"
    elif device.startswith("APM"):
        return "Escolas"
    elif device.startswith("L2"):
        return "Linktel"
    elif any(device.startswith(prefix) for prefix in ["MONITOR", "SWITCH", "VM"]):
        return "Estrutura"
    elif device.startswith("SKYNET"):
        return "BB"
    else:
        return "Clientes PF"

# Adiciona a nova coluna com a categorização
df["Categoria"] = df["Dispositivo"].apply(categorize_device)

# Remove linhas duplicadas
df = df.drop_duplicates(subset=['Data', 'Hora', 'Serviço', 'Dispositivo', 'Status'])

# Ordena o DataFrame pela coluna 'Data'
df = df.sort_values(by=['Data', 'Hora'])

# Salva em um arquivo CSV
df.to_csv("output.csv", index=False, encoding="utf-8")

#Confirmação de conversão
print("Dados salvos em output.csv")
