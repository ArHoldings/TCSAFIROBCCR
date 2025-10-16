import sys
import requests
import datetime
import pyodbc
import os
import logging
import configparser
from dotenv import load_dotenv

def setup_logging(log_path):
    """Configura el sistema de logs"""
    os.makedirs(log_path, exist_ok=True)
    log_file = os.path.join(log_path, f'tipo_cambio_{datetime.date.today().strftime("%Y%m%d")}.log')
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def get_exchange_rate(logger):
    """Obtiene el tipo de cambio de la API del BCCR"""
    url = "https://api.hacienda.go.cr/indicadores/tc"
    try:
        logger.info("Conectando a la API del BCCR...")
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            dolar_info = data.get("dolar", {})
            compra = dolar_info.get("compra", {})
            venta = dolar_info.get("venta", {})
            compra_valor = compra.get("valor")
            venta_valor = venta.get("valor")
            if compra_valor and venta_valor:
                logger.info(f"Tipo de cambio obtenido - Compra: {compra_valor}, Venta: {venta_valor}")
                return float(compra_valor), float(venta_valor)
            logger.warning("No se encontraron valores en la respuesta de la API")
        else:
            logger.warning(f"La API respondió con código: {response.status_code}")
        return None, None
    except requests.Timeout:
        logger.error("Tiempo de espera agotado al contactar la API")
        return None, None
    except Exception as e:
        logger.error(f"Error al consultar la API: {str(e)}")
        return None, None

def read_config():
    """Lee la configuración desde el archivo config.ini y .env"""
    config_dir = r"C:\TipoCambioBCCR\config"
    config_path = os.path.join(config_dir, 'config.ini')
    env_path = os.path.join(config_dir, '.env')
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"No se encontró el archivo de configuración en {config_path}")
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"No se encontró el archivo .env en {env_path}")
    
    # Cargar variables de entorno
    load_dotenv(env_path)
    
    config = configparser.ConfigParser()
    config.read(config_path)
    
    return {
        'server': os.getenv('DB_SERVER'),
        'database': os.getenv('DB_NAME'),
        'username': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }

def save_to_database(compra, venta, logger):
    """Guarda los tipos de cambio en la base de datos"""
    conn = None
    cursor = None
    
    logger.info("Iniciando proceso de guardado en base de datos...")
    
    try:
        # Obtener configuración
        config = read_config()
    except Exception as e:
        logger.error(f"Error al leer el archivo de configuración: {str(e)}")
        return False

    try:
        # Conexión mínima a SQL Server
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={config['server']};"
            f"DATABASE={config['database']};"
            f"UID={config['username']};"
            f"PWD={config['password']}"
        )

        logger.info("Conectando a la base de datos...")
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # Fechas para la inserción
        fecha_hoy = datetime.date.today().strftime("%Y-%m-%d")
        fecha_datetime = datetime.datetime.strptime(fecha_hoy, '%Y-%m-%d')
        current_datetime = datetime.datetime.now()

        # Query de inserción y valores
        insert_query = """
        INSERT INTO [ARH].[SIS].[MSTTIPCAM] (
            TIPCAMFCH, TIPCAMCMPAMT, TIPCAMVTAAMT,
            CREFCH, MODFCH, CREUSR, MODUSR,
            CREIPS, MODIPS, CREHSN, MODHSN,
            TIPCAMPREMES, TIPCAMPRE
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        values = (
            fecha_datetime, compra, venta,
            current_datetime, current_datetime,
            config['username'], config['username'],
            '', '', '', '',
            compra, compra
        )

        # Ejecutar la inserción
        cursor.execute(insert_query, values)
        conn.commit()
        logger.info("Datos insertados correctamente")
        return True

    except pyodbc.Error as e:
        print(f"❌ Error de base de datos: {str(e)}")
        return False

    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        return False

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def get_config_dir():
    """Obtiene la ruta del directorio de configuración"""
    try:
        # Siempre usar la ruta fija C:\TipoCambioBCCR\config
        return "C:\\TipoCambioBCCR\\config"
    except Exception as e:
        print(f"Error al determinar la ruta de configuración: {str(e)}")
        raise

def main():
    """Función principal del programa"""
    try:
        # Obtener directorio de configuración
        config_dir = get_config_dir()
        print("\n=== Iniciando Actualización de Tipo de Cambio BCCR ===")
        print(f"\nDirectorio de configuración: {config_dir}")
        
        # Verificar que existe el directorio
        if not os.path.exists(config_dir):
            print(f"❌ Error: No se encuentra el directorio de configuración en: {config_dir}")
            print("Por favor, crea la siguiente estructura:")
            print("""
C:\\TipoCambioBCCR\\
    ├── bin\\
    │   └── tipo_cambio_bccr.exe
    ├── config\\
    │   ├── config.ini
    │   └── .env
    └── logs\\
            """)
            return False
            
        # Verificar archivos de configuración
        config_file = os.path.join(config_dir, 'config.ini')
        env_file = os.path.join(config_dir, '.env')
        
        if not os.path.exists(config_file):
            print(f"❌ Error: No se encuentra el archivo config.ini en: {config_file}")
            return False
            
        if not os.path.exists(env_file):
            print(f"❌ Error: No se encuentra el archivo .env en: {env_file}")
            return False
            
        # Leer configuración
        config = configparser.ConfigParser()
        config.read(config_file)
        
        # Configurar el sistema de logs
        log_dir = config.get('General', 'log_path', fallback=os.path.join("C:", "TipoCambioBCCR", "logs"))
        logger = setup_logging(log_dir)
        logger.info("=== Iniciando Actualización de Tipo de Cambio BCCR ===")
        
        # Obtener tipo de cambio
        compra, venta = get_exchange_rate(logger)
        if compra is None or venta is None:
            return False
            
        # Guardar en la base de datos
        return save_to_database(compra, venta, logger)
        
    except Exception as e:
        print(f"\nError inesperado: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)