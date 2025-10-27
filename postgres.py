import psycopg2 as pg


# --- Database connection parameters ---
DB_NAME = "MFG598"
USER = "postgres"        # change if your PostgreSQL username is different
PASSWORD = "yourpw"  # change this to your PostgreSQL password
HOST = "localhost"
PORT = "5432"

def createTable():
    createCMD = """
        CREATE TABLE IF NOT EXISTS manufacturing.machine_cell (
            cell_id SERIAL PRIMARY KEY,
            cell_name TEXT NOT NULL
        );
    """
    cur.execute(createCMD)


def insertRow():
    insertCMD= """  INSERT INTO manufacturing.machine_cell VALUES (%s,%s) """
    values = (11, "milling cell")
    cur.execute (insertCMD,values)


def bulkInsert():
 
    with open('machinedata.csv', 'r', encoding='utf-8') as f:
        cur.copy_expert("""
        COPY manufacturing.machine_asset_1
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
insertRow()
bulkInsert()
conn.commit()


