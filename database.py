import pyodbc


CONNECTION_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    r"SERVER=localhost\SQLEXPRESS;"
    "DATABASE=PalworldTCG;"
    "Trusted_Connection=yes;"
    "Encrypt=yes;"
    "TrustServerCertificate=yes;"
)


def get_connection():
    """Create and return a connection to the PalworldTCG database."""
    return pyodbc.connect(CONNECTION_STRING)


def test_connection():
    """Check that Python can connect to the database."""
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT DB_NAME();")
            database_name = cursor.fetchone()[0]

            print("Connection successful!")
            print(f"Connected to database: {database_name}")

    except pyodbc.Error as error:
        print("Connection failed:")
        print(error)


if __name__ == "__main__":
    test_connection()