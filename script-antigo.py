import pandas as pd
import psutil as ps
import time as t
import ping3 as p3
import GPUtil

# Chamando função da biblioteca para pegar informações das gpus existentes
gpus = GPUtil.getGPUs()
# Neste for é guardado a informações de todas as gpus na máquina
for gpu in gpus:
    print(gpu.name)
    # Capturando a porcentagem de uso da cpu com .load(Que traz em decimal) e convertendo para porcentagem
    uso_gpu_percent = gpu.load * 100
    # Aqui o total da gpu que esta sendo utilazada
    total_gpu = gpu.memoryTotal

# Aqui esta sendo convertido os valores que vem em string para float(Deixados em string para trunca-los, deixando apenas dois números após vírgula)
total_armazenamento = float(f"{(ps.disk_usage('/')[0])/(1024 ** 3):.2f}")
total_ram = float(f"{(ps.virtual_memory()[0])/(1024 ** 3):.2f}")
rede = float((f'{p3.ping("google.com"):.3f}'))

count = 0
while True:
    dados = [{
        "Arma %": ps.disk_usage('C:\\')[3],
        "Arm_total": total_armazenamento,
        # "Total GPU": total_gpu,
        # "% uso GPU": uso_gpu_percent,
        "CPU": ps.cpu_percent(percpu=False),
        "RAM %": ps.virtual_memory()[2],
        "RAM total": total_ram,

#-----------------------------
# Tabelinha demonstrativa
#Cem ms | Dez ms | 1 ms  |
#0.1    |0.01    | 0.001 |
#-----------------------------

        "Rede": rede
    }]
    if count == 0:
        primeira_vez = True
    else:
        primeira_vez = False

    df = pd.DataFrame(dados)
    df.to_csv('Dados.csv', encoding='utf-8', header=primeira_vez, index=False, mode='a')
    print(dados)
    count += 1
    t.sleep(1)


    