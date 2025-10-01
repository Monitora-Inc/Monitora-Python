import datetime, psutil, pandas as pd
import time as t
import ping3 as p3

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

def coletarDados():
    id = "C0D000"  # Colocar ID aqui <----------------------
    arquivo_csv = f"captura_{id}.csv"

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
            
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cpu = psutil.cpu_percent(percpu=False)
            ram = psutil.virtual_memory().percent
            disco = psutil.disk_usage('/').percent
            ultimaLeituraRede = psutil.net_io_counters()
            usoRede = (ultimaLeituraRede.bytes_sent - primeiraLeituraRede.bytes_sent) + \
                      (ultimaLeituraRede.bytes_recv - primeiraLeituraRede.bytes_recv)
            usoRedeMB = round(usoRede / (1024 * 1024), 2)
            primeiraLeituraRede = ultimaLeituraRede
            tempoRespostaRede = float((f'{p3.ping("google.com"):.3f}'))

            print(f"ID: {id} | {timestamp} | CPU: {cpu}% | RAM: {ram}% | Disco: {disco}% | Uso de Rede: {usoRedeMB} MB | Latência: {tempoRespostaRede} | Quantidade de Processos: {quantidade_processos}")

            df = pd.DataFrame([[id, timestamp, cpu, ram, disco, usoRedeMB, tempoRespostaRede, quantidade_processos]],
                              columns=['id', 'timestamp', 'cpu', 'ram', 'disco', 'usoRede', 'latencia', 'qtd_processos'])

            df.to_csv(arquivo_csv, encoding="utf-8", header=primeira_vez, index=False, mode='a', sep=';')
            primeira_vez = False
            i -= 1
            t.sleep(10)

    except Exception as e:
        print(f"Erro: {e}")
    except KeyboardInterrupt:
        print("\nScript Interrompido.")

coletarDados()
