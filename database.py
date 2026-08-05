import pyodbc


CONNECTION_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    r"SERVER=localhost\SQLEXPRESS;"
    "DATABASE=PalworldTCG;"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)


try:
    connection = pyodbc.connect(CONNECTION_STRING)
    cursor = connection.cursor()

    cursor.execute("SELECT DB_NAME();")
    database_name = cursor.fetchone()[0]

    print("Connection successful!")
    print(f"Connected to database: {database_name}")

except pyodbc.Error as error:
    print("Connection failed:")
    print(error)

finally:
    if "connection" in locals():
        connection.close()