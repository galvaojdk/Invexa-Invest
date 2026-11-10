import sqlite3
import os

DB_PATH = "invexa.db"

def add_columns():
    if not os.path.exists(DB_PATH):
        print(f"Banco de dados {DB_PATH} não encontrado.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check existing columns
    cursor.execute("PRAGMA table_info(users)")
    columns = [info[1] for info in cursor.fetchall()]
    
    print(f"Colunas atuais: {columns}")
    
    # Add is_admin
    if "is_admin" not in columns:
        print("Adicionando is_admin...")
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
    
    # Add is_premium
    if "is_premium" not in columns:
        print("Adicionando is_premium...")
        cursor.execute("ALTER TABLE users ADD COLUMN is_premium BOOLEAN DEFAULT 0")
        
    # Add role
    if "role" not in columns:
        print("Adicionando role...")
        cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'user'")
        
    conn.commit()
    conn.close()
    print("Migração concluída.")

if __name__ == "__main__":
    add_columns()
