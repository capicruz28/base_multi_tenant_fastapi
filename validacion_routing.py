from app.core.multi_db import get_connection_metadata, get_database_type

# Test cliente SYSTEM
metadata = get_connection_metadata(1)
print(f"SYSTEM: {metadata['database_type']} - {metadata['nombre_bd']}")

# Test cliente Multi-DB (ACME)
metadata = get_connection_metadata(2)
print(f"ACME: {metadata['database_type']} - {metadata.get('nombre_bd', 'N/A')}")

# Test cliente Single-DB (TECH CORP)
metadata = get_connection_metadata(4)
print(f"TECH CORP: {metadata['database_type']} - {metadata['nombre_bd']}")


