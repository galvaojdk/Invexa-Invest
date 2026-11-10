import os
import subprocess
import re
import sys

def kill_process_on_port(port):
    print(f"Verificando processos na porta {port}...")
    try:
        # Executa netstat para encontrar processos ouvindo na porta
        output = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True).decode()
        
        # Filtra linhas que contêm "LISTENING" (opcional, mas bom pra garantir)
        lines = [line for line in output.strip().split('\n') if "LISTENING" in line]
        
        pids = set()
        for line in lines:
            # Pega o último elemento que é o PID
            parts = re.split(r'\s+', line.strip())
            if len(parts) >= 5:
                pid = parts[-1]
                pids.add(pid)
        
        if not pids:
            print(f"Nenhum processo encontrado na porta {port}.")
            return

        for pid in pids:
            if pid == "0": continue # Não mata PID 0
            print(f"Encerrando processo PID {pid}...")
            os.system(f"taskkill /PID {pid} /F")
            
    except subprocess.CalledProcessError:
        print(f"Nenhum processo ativo na porta {port} (limpo).")
    except Exception as e:
        print(f"Erro ao tentar limpar porta {port}: {e}")

if __name__ == "__main__":
    kill_process_on_port(8000)
    kill_process_on_port(8001)
