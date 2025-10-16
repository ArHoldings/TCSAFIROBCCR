import requests
import datetime
import pyodbc
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DB_SERVER = os.getenv('DB_SERVER')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# Fecha actual
fecha_hoy = datetime.date.today().strftime("%Y-%m-%d")

# URL de la API
url = "https://api.hacienda.go.cr/indicadores/tc"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()

    dolar_info = data.get("dolar", {})

    compra = dolar_info.get("compra", {})
    venta = dolar_info.get("venta", {})

    compra_valor = compra.get("valor", None)
    venta_valor = venta.get("valor", None)

    if compra_valor and venta_valor:
        try:
            # Conexión a la base de datos
            conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={DB_SERVER};DATABASE={DB_NAME};UID={DB_USER};PWD={DB_PASSWORD}'
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            # Fecha y hora actual para los campos de auditoría
            current_datetime = datetime.datetime.now()

            # Valores por defecto para los campos de auditoría
            hostname = "sa"
            ip = "<local machine>"

            # Query para insertar los tipos de cambio
            insert_query = """
            INSERT INTO [ARH].[SIS].[MSTTIPCAM] (
                TIPCAMFCH, TIPCAMCMPAMT, TIPCAMVTAAMT,
                CREFCH, MODFCH, CREUSR, MODUSR,
                CREIPS, MODIPS, CREHSN, MODHSN,
                TIPCAMPREMES, TIPCAMPRE
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            # Convertir fecha_hoy a datetime
            fecha_datetime = datetime.datetime.strptime(fecha_hoy, '%Y-%m-%d')
            
            # Preparar los valores para la inserción
            values = (
                fecha_datetime,             # TIPCAMFCH
                float(compra_valor),        # TIPCAMCMPAMT
                float(venta_valor),         # TIPCAMVTAAMT
                current_datetime,           # CREFCH
                current_datetime,           # MODFCH
                DB_USER,                    # CREUSR
                DB_USER,                    # MODUSR
                ip,                         # CREIPS
                ip,                         # MODIPS
                hostname,                   # CREHSN
                hostname,                   # MODHSN
                float(compra_valor),        # TIPCAMPREMES (mismo valor que compra)
                float(compra_valor)         # TIPCAMPRE (mismo valor que compra)
            )
            
            cursor.execute(insert_query, values)
            conn.commit()
            
            print(f"✔ Tipo de cambio del día {fecha_hoy} guardado exitosamente:")
            print(f"   Compra: {compra_valor}")
            print(f"   Venta: {venta_valor}")
            
            cursor.close()
            conn.close()
            
        except pyodbc.Error as e:
            print(f"❌ Error al guardar en la base de datos: {str(e)}")
    else:
        print("⚠ No se encontraron valores de tipo de cambio.")
else:
    print(f"❌ Error al consultar la API: Código {response.status_code}")
