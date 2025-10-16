import pyodbc
import os
from dotenv import load_dotenv

def test_connection():
    print("\n=== Prueba de Conexión SQL Server ===\n")
    
    # Cargar variables de entorno
    print("Cargando configuración...")
    load_dotenv()
    
    # Obtener configuración
    config = {
        'server': os.getenv('DB_SERVER'),
        'database': os.getenv('DB_NAME'),
        'username': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    # Verificar configuración
    missing = [k for k, v in config.items() if not v]
    if missing:
        print("❌ Error: Faltan las siguientes variables en el archivo .env:")
        for var in missing:
            print(f"   • {var}")
        return
    
    print("\nIntentando conexión...")
    try:
        # Intentar conexión simple
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={config['server']};"
            f"DATABASE={config['database']};"
            f"UID={config['username']};"
            f"PWD={config['password']};"
            "TrustServerCertificate=yes"
        )
        
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Probar consulta simple
        print("\nVerificando acceso a la tabla...")
        cursor.execute("SELECT COUNT(*) FROM [ARH].[SIS].[MSTTIPCAM]")
        count = cursor.fetchone()[0]
        print(f"✔ Conexión exitosa!")
        print(f"✔ La tabla tiene {count} registros")
        
        # Verificar permisos de inserción
        print("\nVerificando permisos de inserción...")
        cursor.execute("""
            SELECT HAS_PERMS_BY_NAME(
                '[ARH].[SIS].[MSTTIPCAM]',
                'OBJECT',
                'INSERT'
            )
        """)
        has_insert = cursor.fetchone()[0]
        if has_insert:
            print("✔ El usuario tiene permisos de inserción en la tabla")
        else:
            print("❌ El usuario NO tiene permisos de inserción en la tabla")
        
        cursor.close()
        conn.close()
        
    except pyodbc.Error as e:
        print("\n❌ Error de conexión:")
        print(str(e))
        if 'VIEW SERVER STATE' in str(e):
            print("\nSugerencia: Este error puede ignorarse si solo necesitamos insertar datos.")
            print("La aplicación principal debería funcionar correctamente.")
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")

    input("\nPresione Enter para salir...")

if __name__ == "__main__":
    test_connection()