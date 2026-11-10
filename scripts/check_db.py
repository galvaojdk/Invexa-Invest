import sqlite3
import os

db_path = "invexa.db"
if not os.path.exists(db_path):
    print(f"Erro: {db_path} não encontrado.")
else:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"Colunas encontradas na tabela 'users': {column_names}")
        
        if "profile_pic" not in column_names:
            print("Coluna 'profile_pic' FALTANDO! Tentando adicionar...")
            cursor.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT")
            conn.commit()
            print("Coluna 'profile_pic' adicionada com sucesso.")
        else:
            print("Coluna 'profile_pic' já existe.")
        
        conn.close()
    except Exception as e:
        print(f"Erro ao acessar o banco: {e}")
