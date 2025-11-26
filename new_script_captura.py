import datetime, psutil, pandas as pd
import time as t
import ping3 as p3
import requests
import os
import socket

print("""
          .         .                                                                                                                            
         ,8.       ,8.           ,o888888o.     b.             8  8 8888 8888888 8888888888 ,o888888o.     8 888888888o.            .8.          
        ,888.     ,888.       . 8888     `88.   888o.          8  8 8888       8 8888    . 8888     `88.   8 8888    `88.          .888.         
       .`8888.   .`8888.     ,8 8888       `8b  Y88888o.       8  8 8888       8 8888   ,8 8888       `8b  8 8888     `88         :88888.        
      ,8.`8888. ,8.`8888.    88 8888        `8b .`Y888888o.    8  8 8888       8 8888   88 8888        `8b 8 8888     ,88        . `88888.       
     ,8'8.`8888,8^8.`8888.   88 8888         88 8o. `Y888888o. 8  8 8888       8 8888   88 8888         88 8 8888.   ,88'       .8. `88888.      
    ,8' `8.`8888' `8.`8888.  88 8888         88 8`Y8o. `Y88888o8  8 8888       8 8888   88 8888         88 8 888888888P'       .8`8. `88888.     
   ,8'   `8.`88'   `8.`8888. 88 8888        ,8P 8   `Y8o. `Y8888  8 8888       8 8888   88 8888        ,8P 8 8888`8b          .8' `8. `88888.    
  ,8'     `8.`'     `8.`8888.`8 8888       ,8P  8      `Y8o. `Y8  8 8888       8 8888   `8 8888       ,8P  8 8888 `8b.       .8'   `8. `88888.   
 ,8'       `8        `8.`8888.` 8888     ,88'   8         `Y8o.`  8 8888       8 8888    ` 8888     ,88'   8 8888   `8b.    .888888888. `88888.  
,8'         `         `8.`8888.  `8888888P'     8            `Yo  8 8888       8 8888       `8888888P'     8 8888     `88. .8'       `8. `88888. 
""")

ip_arquivo = "../ip_monitora.txt"

def verificacaoSO():
    if(os.name == "nt"):
        import win32pdh as win
        return "Windows"
    elif (os.name == "posix"):
        return "Linux"
    else:
        exit(1)

if os.path.exists(ip_arquivo):
    with open(ip_arquivo, "r") as f:
        ip_instancia = f.read().strip()
else:
    ip_instancia = "localhost"

try:
    uuid_path = os.path.join(os.path.dirname(__file__), '..', 'uuid_servidor.txt')
    uuid_path = os.path.abspath(uuid_path)
    with open(uuid_path, "r") as uidServidor:
        id = uidServidor.read().strip()
except FileNotFoundError:
    id = "0"

def coletarDados():
    nic = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()
    entradaSaidaRede = psutil.net_io_counters(pernic=True)
    nomeInterface= ''
   

    for interface, addr_list in addrs.items():
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
            nomeInterface = interface
            break

    primeiraLeituraRede = psutil.net_io_counters(pernic=True)[nomeInterface]

    leituras = 12 # Quantas leituras vão ser realizadas
    periodo = 10 # De enquanto enquanto segundos vai ser realizada uma leitura
    while leituras > 0:
        quantidade_processos = sum(1 for _ in psutil.process_iter(['name']))
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cpu = psutil.cpu_percent(percpu=False)
        ram = psutil.virtual_memory()
        disco = psutil.disk_usage('/').percent
        ultimaLeituraRede = psutil.net_io_counters(pernic=True)[nomeInterface]
        bytesEnviados = ultimaLeituraRede.bytes_sent - primeiraLeituraRede.bytes_sent
        bytesRecebidos = ultimaLeituraRede.bytes_recv - primeiraLeituraRede.bytes_recv
        usoRede = bytesEnviados + bytesRecebidos
        # usoRedeMB = usoRede / (1024 * 1024)
        primeiraLeituraRede = ultimaLeituraRede
        tempoRespostaRede = float((f'{p3.ping("google.com"):.3f}'))
        io = psutil.net_io_counters(pernic=True)[nomeInterface]
        pckg_env = io.packets_sent
        pckg_rcbd = io.packets_recv
        pckg_perdidos = io.dropin + io.dropout
        uptime_segundos = int(datetime.datetime.now().timestamp() - psutil.boot_time())

        if verificacaoSO() == "Windows":
            import win32pdh as win
            ramFria = 0
            pastas = [
                win.MakeCounterPath((None, "Memória", None, None, -1, "Bytes de Prioridade Normal de Cache em Espera")), 
                win.MakeCounterPath((None, "Memória", None, None, -1, "Bytes de Reserva de Cache em Espera")),
                win.MakeCounterPath((None, "Memória", None, None, -1, "Bytes Principais de Cache em Espera"))
            ]
            for pasta in pastas:
                query = win.OpenQuery()
                counter = win.AddCounter(query, pasta)
                win.CollectQueryData(query)
                _, value = win.GetFormattedCounterValue(counter, win.PDH_FMT_LARGE)
                ramFria += value
            ramQuente = ram.used - ramFria
        else:
            ramQuente = ram.active
            ramFria = ram.inactive

        ramTotal = (f"{(ram.total)}")
        ramUsada = (f"{ram.used}")
        ramPercent = (f"{((ram.used/ram.total) * 100):.2f}")
        ramQuente = (f"{ramQuente}")
        ramFria = (f"{ramFria}")

        print(
        f"{timestamp} | "
        f"CPU: {cpu}% | "
        f"RAM Total: {ramTotal} Bytes | "
        f"RAM Usada: {ramUsada} Bytes | "
        f"RAM %: {ramPercent}% | "
        f"RAM Quente: {ramQuente} Bytes | "
        f"RAM Fria: {ramFria} Bytes | "
        f"Disco: {disco}% | "
        f"Bytes Enviados (Rede): {bytesEnviados} |"
        f"Bytes Recebidos (Rede): {bytesRecebidos} |"
        f"Latência: {tempoRespostaRede} | "
        f"Pacotes Enviados: {pckg_env} | "
        f"Pacotes Recebidos: {pckg_rcbd} | "
        f"Pacotes Perdidos: {pckg_perdidos} | "
        f"Processos: {quantidade_processos} | "
        f"Uptime (Segundos): {uptime_segundos}s"
    )

        df = pd.DataFrame([[id, timestamp, cpu, float(ramTotal), float(ramUsada), float(ramPercent), float(ramQuente), float(ramFria), disco, bytesEnviados, bytesRecebidos, tempoRespostaRede, pckg_env, pckg_rcbd, pckg_perdidos, quantidade_processos, uptime_segundos]],
            columns=['id','timestamp','cpu','total_ram','ram_usada','ram_percent','ram_quente','ram_fria','disco_percent','bytesEnv', 'bytesRecb','latencia','pacotes_enviados','pacotes_recebidos','pacotes_perdidos','qtd_processos','uptime_segundos'])

        df.to_csv(arquivo_csv, encoding="utf-8", header=not os.path.exists(arquivo_csv), index=False, mode='a', sep=';')
        leituras -= 1
        t.sleep(periodo)

def enviarCSV():
    url = f"http://{ip_instancia}:3333/bucket/upload"
    data = {"servidorId": id}
    try:
        with open(arquivo_csv, "rb") as f:
            files = {"file": (arquivo_csv, f, "text/csv")}
            requests.post(url, data=data, files=files, timeout=5)
    except:
        print("Sem conexão com o bucket!")
        pass

ultimo_csv = None
while True:
    dtHrCaptura = datetime.datetime.now().strftime('%H-%M')
    arquivo_csv = f"{dtHrCaptura}.csv"

    if ultimo_csv and os.path.exists(ultimo_csv):
        os.remove(ultimo_csv)

    ultimo_csv = arquivo_csv

    coletarDados()
    enviarCSV()