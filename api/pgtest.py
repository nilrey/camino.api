import psycopg2
#"postgresql://postgres:postgres@camino-pgdb:5432/camino"
connection = psycopg2.connect(database="camino", user="postgres", password="postgres", host="127.0.0.1", port=5432)
cursor = connection.cursor()
cursor.execute("SELECT table_schema,table_name FROM information_schema.tables ORDER BY table_schema,table_name;")
record = cursor.fetchall()
print("Data from Database:- ", record)