"""
Script de prueba para verificar la extracción de subdominio
Ejecutar desde la raíz del proyecto: python test_subdomain.py
"""

def extract_subdomain_test(host: str, base_domain: str) -> str | None:
    """Función de prueba para extracción de subdominio"""
    
    # Limpieza de puerto
    if ":" in host:
        host = host.split(":")[0]
    
    print(f"\n{'='*60}")
    print(f"Testing: '{host}'")
    print(f"Base Domain: '{base_domain}'")
    print(f"{'='*60}")
    
    # Caso especial: localhost
    if host.endswith('.localhost'):
        parts = host.split('.')
        if len(parts) >= 2:
            subdomain = parts[0]
            print(f"LOCALHOST: Subdominio detectado = '{subdomain}'")
            return subdomain
    
    # Caso: dominios personalizados
    if host.endswith(f".{base_domain}"):
        print(f"MATCH: Host termina con '.{base_domain}'")
        subdomain = host.replace(f".{base_domain}", "")
        print(f"RESULTADO: Subdominio = '{subdomain}'")
        return subdomain
    
    if host == base_domain:
        print(f"INFO: Host es exactamente el base_domain (sin subdominio)")
        return None
    
    print(f"NO MATCH: No se detectó subdominio")
    print(f"   Host: '{host}'")
    print(f"   Base: '{base_domain}'")
    print(f"   Endswith check: {host.endswith(f'.{base_domain}')}")
    return None


# ===== PRUEBAS =====
if __name__ == "__main__":
    # Tu configuración actual
    BASE_DOMAIN = "midominio.com"  # ⚠️ VERIFICA QUE ESTE SEA TU VALOR REAL
    
    test_cases = [
        "cliente1.midominio.com:8000",
        "cliente1.midominio.com",
        "cliente2.midominio.com:8000",
        "platform.midominio.com",
        "midominio.com",
        "localhost:8000",
        "cliente1.localhost:8000",
        "127.0.0.1:8000",
    ]
    
    print("\n" + "="*60)
    print("TEST DE EXTRACCIÓN DE SUBDOMINIO")
    print("="*60)
    
    for test_host in test_cases:
        result = extract_subdomain_test(test_host, BASE_DOMAIN)
        
    print("\n" + "="*60)
    print("TESTS COMPLETADOS")
    print("="*60)
    
    # Instrucciones
    print("\n📋 PASOS SIGUIENTES:")
    print("1. Si 'cliente1.midominio.com' NO muestra subdominio 'cliente1':")
    print("   → Tu BASE_DOMAIN en .env NO es 'midominio.com'")
    print("   → Verifica con: python -c \"from app.core.config import settings; print(settings.BASE_DOMAIN)\"")
    print("\n2. Si SÍ muestra 'cliente1':")
    print("   → El middleware actualizado debería funcionar")
    print("   → Reinicia el servidor FastAPI")