import datetime, psutil, pandas as pd
import time as t
import ping3 as p3
import requests
import os

print("""
$$\      $$\  $$$$$$\  $$\   $$\ $$$$$$\ $$$$$$$$\  $$$$$$\  $$$$$$$\   $$$$$$\  
$$$\    $$$ |$$  __$$\ $$$\  $$ |\_$$  _|\__$$  __|$$  __$$\ $$  __$$\ $$  __$$\
$$$$\  $$$$ |$$ /  $$ |$$$$\ $$ |  $$ |     $$ |   $$ /  $$ |$$ |  $$ |$$ /  $$ |
$$\$$\$$ $$ |$$ |  $$ |$$ $$\$$ |  $$ |     $$ |   $$ |  $$ |$$$$$$$  |$$$$$$$$ |
$$ \$$$  $$ |$$ |  $$ |$$ \$$$$ |  $$ |     $$ |   $$ |  $$ |$$  __$$< $$  __$$ |
$$ |\$  /$$ |$$ |  $$ |$$ |\$$$ |  $$ |     $$ |   $$ |  $$ |$$ |  $$ |$$ |  $$ |
$$ | \_/ $$ | $$$$$$  |$$ | \$$ |$$$$$$\    $$ |    $$$$$$  |$$ |  $$ |$$ |  $$ |
\__|     \__| \______/ \__|  \__|\______|   \__|    \______/ \__|  \__|\__|  \__|
                                                                                 
                                                                                 
                                                                                 """)

ip_arquivo = "../ip_monitora.txt"


# Pega IP da instância
if os.path.exists(ip_arquivo):
    with open(ip_arquivo, "r") as f:
        ip_instancia = f.read().strip()
    print(f"IP encontrado no arquivo: {ip_instancia}")
else:
    print("Arquivo ip_monitora.txt não encontrado, usando IP padrão.")
    ip_instancia = "localhost" 

try:
    uuid_path = os.path.join(os.path.dirname(__file__), '..', 'uuid_servidor.txt')
    uuid_path = os.path.abspath(uuid_path)

    with open(uuid_path, "r") as uidServidor:
        id = uidServidor.read().strip()  # strip remove espaços em branco

    dtHrCaptura = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M')
    arquivo_csv = f"captura_{dtHrCaptura}.csv"

except FileNotFoundError:
    print("Arquivo uuid_servidor.txt não encontrado!")
    exit(1)

def coletarDados():

    try:
        pd.read_csv(arquivo_csv, sep=';')
        primeira_vez = False
    except FileNotFoundError:
        primeira_vez = True

    primeiraLeituraRede = psutil.net_io_counters()
    i = 1

    try:
        while i > 0:
            quantidade_processos = sum(1 for _ in psutil.process_iter(['name']))
            
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cpu = psutil.cpu_percent(percpu=False)
            ram = psutil.virtual_memory().percent
            disco = psutil.disk_usage('/').percent
            ultimaLeituraRede = psutil.net_io_counters()
            usoRede = (ultimaLeituraRede.bytes_sent - primeiraLeituraRede.bytes_sent) + \
                      (ultimaLeituraRede.bytes_recv - primeiraLeituraRede.bytes_recv)
            usoRedeMB = usoRede / (1024 * 1024)
            primeiraLeituraRede = ultimaLeituraRede
            tempoRespostaRede = float((f'{p3.ping("google.com"):.3f}'))

            print(f"ID: {id} | {timestamp} | CPU: {cpu}% | RAM: {ram}% | Disco: {disco}% | Uso de Rede: {usoRedeMB} MB | Latência: {tempoRespostaRede} | Quantidade de Processos: {quantidade_processos}")

            df = pd.DataFrame([[id, timestamp, cpu, ram, disco, usoRedeMB, tempoRespostaRede, quantidade_processos]],
                              columns=['id', 'timestamp', 'cpu', 'ram', 'disco', 'usoRede', 'latencia', 'qtd_processos'])

            df.to_csv(arquivo_csv, encoding="utf-8", header=primeira_vez, index=False, mode='a', sep=';')
            primeira_vez = False
            i -= 1
            t.sleep(1)

    except Exception as e:
        print(f"Erro: {e}")
    except KeyboardInterrupt:
        print("\nScript Interrompido.")

coletarDados()


def enviarCSV():

    url = f"http://{ip_instancia}:3333/bucket/upload" #<--- trocar localHost pelo ip da instancia
    
    data = {  
            "servidorId": id   
        }
    print(id)
    
    with open(arquivo_csv, "rb") as f:
        files = {"file": (arquivo_csv, f, "text/csv")}
        response = requests.post(url, data=data, files=files)

    print(response.status_code)
    print(response.json())

enviarCSV()