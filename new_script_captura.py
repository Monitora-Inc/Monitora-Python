import datetime, psutil, pandas as pd
import time as t
import ping3 as p3
import requests
import os
import socket

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

    i = 60

    try:
        nic = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()
        entradaSaidaRede = psutil.net_io_counters(pernic=True)
        nomeInterface= ''
        capacidadeNic = 0 
        

        for  interface, addr_list in addrs.items():
            
            if interface.lower().startswith(("lo", "docker", "veth", "vm", "br-", "wlx", "virbr", "tap", "ham")):
                continue

            tem_ipv4 = any(a.family == socket.AF_INET for a in addr_list)
            if not tem_ipv4:
                continue


            infoNic = nic.get(interface)
            io = entradaSaidaRede.get(interface)

            if not io or not infoNic:
                 continue
            
            ativa = (io.bytes_recv + io.bytes_sent) > 0
        
            if ativa:
             print(f"{interface} {infoNic.speed} Mbps")
             capacidadeNic = infoNic.speed
             nomeInterface = interface
             break
        
        primeiraLeituraRede = psutil.net_io_counters(pernic=True)[nomeInterface]
        

        while i > 0:

          

            quantidade_processos = sum(1 for _ in psutil.process_iter(['name']))
            
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cpu = psutil.cpu_percent(percpu=False)
            ram = psutil.virtual_memory().percent
            disco = psutil.disk_usage('/').percent
            ultimaLeituraRede = psutil.net_io_counters(pernic=True)[nomeInterface]
            usoRede = (ultimaLeituraRede.bytes_sent - primeiraLeituraRede.bytes_sent) + \
                      (ultimaLeituraRede.bytes_recv - primeiraLeituraRede.bytes_recv)
            usoRedeMB = usoRede / (1024 * 1024)
            primeiraLeituraRede = ultimaLeituraRede
            tempoRespostaRede = float((f'{p3.ping("google.com"):.3f}'))
            io = psutil.net_io_counters(pernic=True)[nomeInterface]
            pckg_env =   io.packets_sent
            pckg_rcbd =   io.packets_recv
            pckg_perdidos =    io.dropin +   io.dropout 
            

            print(f"ID: {id} | {timestamp} | CPU: {cpu}% | RAM: {ram}% | Disco: {disco}% | Uso de Rede: {usoRedeMB} MB | Latência: {tempoRespostaRede} | Capacidade NIC: {capacidadeNic} |" +
                  f"Pacotes enviados: {pckg_env} | Pacotes Recebidos: {pckg_rcbd} | Pacotes Perdidos: {pckg_perdidos} | Quantidade de Processos: {quantidade_processos}")

            df = pd.DataFrame([[id, timestamp, cpu, ram, disco, usoRedeMB, tempoRespostaRede, capacidadeNic, pckg_env, pckg_rcbd, pckg_perdidos, quantidade_processos]],
                              columns=['id', 'timestamp', 'cpu', 'ram', 'disco', 'usoRede', 'latencia', 'nic_mbps', 'pacotes_enviados', 'pacotes_recebidos', 'pacotes_perdidos', 'qtd_processos'])

            df.to_csv(arquivo_csv, encoding="utf-8", header=primeira_vez, index=False, mode='a', sep=';')
            primeira_vez = False
            i -= 1
            t.sleep(10)

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