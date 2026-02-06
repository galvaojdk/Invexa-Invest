import sqlite3
import sys

DB_PATH = "invexa.db"

def promote_user(email):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id, email, is_admin FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    if not user:
        print(f"Usuário {email} não encontrado.")
        conn.close()
        return

    print(f"Usuário encontrado: ID={user[0]}, Admin={user[2]}")
    
    # Promote
    cursor.execute("UPDATE users SET is_admin = 1, role = 'admin' WHERE email = ?", (email,))
    conn.commit()
    
    print(f"SUCESSO: Usuário {email} agora é ADMINISTRADOR.")
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/promote_user.py <email>")
    else:
        promote_user(sys.argv[1])
