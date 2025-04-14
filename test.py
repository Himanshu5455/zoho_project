import psycopg2
from psycopg2 import Error

def create_test_table():
    try:
        # Connect to the database
        connection = psycopg2.connect(
            database="postgres",
            user="Flask",
            password="admin1234",
            host="flaskdb.cfscoawag2c7.eu-north-1.rds.amazonaws.com",
            port="5432"
        )

        # Create a cursor object to execute PostgreSQL commands
        cursor = connection.cursor()

        # SQL query to create a simple test table
        create_table_query = '''
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        '''

        # Execute the query
        cursor.execute(create_table_query)
        connection.commit()
        print("Table created successfully!")

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL:", error)

    finally:
        # Close database connection
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection closed.")

# Call the function
if __name__ == "__main__":
    create_test_table()