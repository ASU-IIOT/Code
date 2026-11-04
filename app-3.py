import psycopg2 as pg

# --- Database connection parameters ---
DB_NAME = "MFG598"
USER = "postgres"        # change if your PostgreSQL username is different
PASSWORD = "******* "  # change this to your PostgreSQL password
HOST = "localhost"
PORT = "5432"

def createTable():
    createCMD = """
        CREATE TABLE IF NOT EXISTS manufacturing.temperature_readings (
            datappoint_id INTEGER,
            temperature DOUBLE PRECISION
        );

    """
    cur.execute(createCMD)



def bulkInsert():
    
    with open('temp.csv', 'r', encoding='utf-8') as f:
        cur.copy_expert("""
        COPY manufacturing.temperature_readings
        FROM STDIN WITH (FORMAT CSV, HEADER, DELIMITER ',')
        """, f)
    
 # --- Connect to PostgreSQL database ---
conn = pg.connect(
        dbname=DB_NAME,
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT
    )

cur=conn.cursor()



createTable()
#insertRow()
bulkInsert()
conn.commit()
