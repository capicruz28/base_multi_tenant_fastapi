from app.core.encryption import encrypt_credential, decrypt_credential

# Test rápido
original = "mi_password_secreto"
encrypted = encrypt_credential(original)
decrypted = decrypt_credential(encrypted)

print(f"Original:    {original}")
print(f"Encriptado:  {encrypted[:50]}...")
print(f"Recuperado:  {decrypted}")
print(f"Match: {original == decrypted}")  # Debe ser True