import pyodbc

print("\n=== Verificación de Drivers ODBC Instalados ===\n")

drivers = pyodbc.drivers()
print("Drivers ODBC encontrados:")
print("-" * 50)
for driver in drivers:
    print(f"• {driver}")

print("\nBuscando 'ODBC Driver 17 for SQL Server'...")
if "ODBC Driver 17 for SQL Server" in drivers:
    print("✔ El driver necesario está instalado correctamente.")
else:
    print("❌ No se encontró el driver necesario.")
    print("\nPara instalar el driver:")
    print("1. Descargue el instalador de Microsoft:")
    print("   https://go.microsoft.com/fwlink/?linkid=2239256")
    print("2. Ejecute el instalador como administrador")
    print("3. Siga las instrucciones de instalación")

input("\nPresione Enter para salir...")