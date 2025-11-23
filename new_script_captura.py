import datetime, psutil, pandas as pd
import time as t
import ping3 as p3
import requests
import os

# Essa biblioteca é do pywin32 pdh(Perfomance Data Helper) esse módulo da biblioteca que a gente usa para pegar processos do windows
import win32pdh as win
# Precisamos fazer instalacao do pywin no script sh (pip install pywin32)
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
# Linux "posix" | windows "nt"
def verificacaoSO():
    if(os.name == "nt"):
        return "Windows"
    elif (os.name == "posix"):
        return "Linux"
    else:
        print("Sistema não suportado!")
        exit(1)

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
    # id = 1

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
    i = 60

    try:
            
        while i > 0:
            quantidade_processos = sum(1 for _ in psutil.process_iter(['name']))
            
            # ITENS GERAIS
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cpu = psutil.cpu_percent(percpu=False)
            ram = psutil.virtual_memory()
            disco = psutil.disk_usage('/')
            ultimaLeituraRede = psutil.net_io_counters()
            usoRede = (ultimaLeituraRede.bytes_sent - primeiraLeituraRede.bytes_sent) + \
                    (ultimaLeituraRede.bytes_recv - primeiraLeituraRede.bytes_recv)
            usoRedeMB = usoRede / (1024 * 1024)
            primeiraLeituraRede = ultimaLeituraRede
            tempoRespostaRede = float((f'{p3.ping("google.com"):.3f}'))
            
            if verificacaoSO() == "Windows":
                ramFria = 0
                falhas_cache = 0
                # PEGANDO ITENS RAM
                try:
                    # Aqui envio os parametros que quero dentro de uma tupla. O sistema irá ate a pasta e irá pegar o conteudo. Para enteder melhor, se estiver usando windows 
                    #Utilize o comando windows r - digite perfmon, abra desempenho do sistema e clique no mais verde. Lá aparecerá itens e dados muito mais específicos do que no psutil
                    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------
                    #PDH identifica os contadores assim (\Objeto\Instância\Contador). Então é nessa ordem que a gente coloca. Estou deixando os paramêtros abaixo para
                    #(Máquina(none = local), objeto(Memory, Processor, Disk, etc.), instância, parent instância, instance index (as tres anteriores pode deixar none), nome do contador)
                    #--------------------------------------------------------------------------------------------------------------------------------------------------------------------
                   
                    pastas = [
                                win.MakeCounterPath((None, "Memória", None, None, -1, "Bytes de Prioridade Normal de Cache em Espera")), 
                                win.MakeCounterPath((None, "Memória", None, None, -1, "Bytes de Reserva de Cache em Espera")),
                                win.MakeCounterPath((None, "Memória", None, None, -1, "Bytes Principais de Cache em Espera")),
                                win.MakeCounterPath((None, "Memória", None, None, -1, "Falhas de cache/s"))
                              ]
                    
                    for pasta in pastas:
                        if (pasta == win.MakeCounterPath((None, "Memória", None, None, -1, "Falhas de cache/s"))):
                            print(pasta)
                            break
                        query = win.OpenQuery() # Este comando abre uma conexão para consulta
                        counter = win.AddCounter(query, pasta) # Aqui estamos pedindo para monitorar o item espcífico
                        win.CollectQueryData(query) # Aqui ele lê a query(Consulta)
                        _, value = win.GetFormattedCounterValue(counter, win.PDH_FMT_LARGE)
                        ramFria += value
                    
                    ramQuente = ram.used - ramFria

                except Exception as e:
                    print(e)    
                
            else:
                ramQuente = ram.active
                ramFria = ram.inactive

            converteGiga = 1024 ** 3
            print(f"ID: {id} | {timestamp} | CPU: {cpu}% | RAM-Total: {(ram.total/converteGiga):.2f}GB | RAM-Usada: {ram.used/converteGiga:.2f}GB | RAM-Percent: {((ram.used/ram.total) * 100):.2f}% | RAM-Quente: {ramQuente/converteGiga:.2f}GB | RAM-Fria: {ramFria/converteGiga:.2f}GB | Disco: {disco.percent}% | Uso de Rede: {usoRedeMB} MB | Latência: {tempoRespostaRede} | Quantidade de Processos: {quantidade_processos} | Falhas-Cache: {falhas_cache:.2f}")



            # Limitando decimais valores!
            ramTotal = (f"{(ram.total/converteGiga):.2f}")
            ramUsada = (f"{ram.used/converteGiga:.2f}")
            ramPercent = (f"{((ram.used/ram.total) * 100):.2f}")
            ramQuente = (f"{ramQuente/converteGiga:.2f}")
            ramFria = (f"{ramFria/converteGiga:.2f}")

            df = pd.DataFrame([[id, timestamp, cpu, float(ramTotal), float(ramUsada), float(ramPercent), float(ramQuente), float(ramFria), disco.percent, usoRedeMB, tempoRespostaRede, quantidade_processos]],
                              columns=['id', 'timestamp', 'cpu', 'total_ram', 'ram_usada', 'ram_percent', 'ram_quente', 'ram_fria', 'disco', 'usoRede', 'latencia', 'qtd_processos'])

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