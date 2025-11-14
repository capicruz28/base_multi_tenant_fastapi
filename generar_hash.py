# generar_hash.py
from app.core.security import get_password_hash

def main():
    password = input("Introduce la contraseña: ")
    hashed = get_password_hash(password)
    print(f"\nHash para '{password}':\n{hashed}\n")
    print("Copia este hash y reemplázalo en tu script de seed.")

if __name__ == "__main__":
    main()