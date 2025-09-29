import psutil
import time, datetime
import pandas as pd


def capturarProcessos():

   
    primeira_vez = True 
    try:
        print("Processos em execução:")
        while True:
            processos = []    
            
            for proc in psutil.process_iter(['name']):
                    proc.cpu_percent(None)

            time.sleep(1)

            for proc in psutil.process_iter(['name', 'memory_percent']):
                try: 
               
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    name= proc.info['name']
                    cpu_percent= proc.cpu_percent()
                    memory_percent= round(proc.info['memory_percent'])
                    
                    print(f"TimesTamp: {timestamp} |  Nome: {name} | CPU: {cpu_percent} | Memória: {memory_percent}" )
                    processos.append([timestamp, name, cpu_percent, memory_percent])

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue #caso ocorra um desses erros, não interrompe o looping, pula para o próximo 

            
            dfProcessos = pd.DataFrame(processos, columns=['timestamp', 'name', 'cpu_percent', 'memory_percent'])
            dfProcessos.to_csv(
                        "capturaProcessos.csv",
                        encoding="utf-8",
                        header=primeira_vez,
                        index=False,
                        mode='a',
                        sep=';'
                    )
            primeira_vez = False        
            time.sleep(10)    

    except KeyboardInterrupt:
            print("\nScript Interrompido.")

capturarProcessos()            
