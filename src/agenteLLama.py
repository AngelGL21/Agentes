import mysql.connector
from langchain_community.llms import Ollama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Función para realizar consultas a la base de datos
def query_database(query, parameters=None):
    try:
        # Establecer conexión a la base de datos
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="angel123",
            database="libreria"
        )
        cursor = connection.cursor()

        # Ejecutar la consulta
        cursor.execute(query, parameters)

        # Obtener resultados
        result = cursor.fetchall()

        # Cerrar conexión
        cursor.close()
        connection.close()

        return result

    except mysql.connector.Error as error:
        print("Error al ejecutar la consulta:", error)
        return None

# Configuración de la cadena de procesamiento
llm = Ollama(model="llama2")
prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Eres un agente diseñado para interactuar exclusivamente con la base de datos SQL. "
     "Solo debes proporcionar respuestas basadas en la información almacenada en la base de datos. "
     "Evita hacer suposiciones o inferencias no respaldadas por los datos. "
     "Prioriza la precisión y relevancia de la información en tus respuestas. "
     "Limita tus consultas a la base de datos para garantizar la eficiencia en la obtención de respuestas. "
     "Tu función principal es consultar la base de datos para obtener la información solicitada por el usuario. "
     "Proporciona respuestas precisas y relevantes basadas en los datos almacenados en la base de datos. "
     "Evita especular o proporcionar información no respaldada por la base de datos. "
     "Cuando respondas con valores de moneda, utiliza 'Q' seguido del monto en quetzales. "
     "No quiero que des explicaciones adicionales, solo respuestas cortas y directas."
     ),

    ("user", "{input}")
])
output_parser = StrOutputParser()
chain = prompt | llm | output_parser

# Función para manejar la entrada del usuario y generar una respuesta
def handle_input(user_input):
    try:
        database_response = None
        if "libros de fantasía" in user_input:
            query = """
                SELECT Libros.titulo FROM Libros
                JOIN Libros_Categorias ON Libros.libro_id = Libros_Categorias.libro_id
                JOIN Categorias ON Libros_Categorias.categoria_id = Categorias.categoria_id
                WHERE Categorias.nombre = 'Fantasía'
            """
            database_response = query_database(query)
            formatted_response = "Los libros de fantasía son: " + ", ".join([row[0] for row in database_response])
        elif "clientes que han realizado pedidos" in user_input:
            query = """
                SELECT c.nombre, c.apellidos
                FROM Clientes c
                JOIN Pedidos p ON c.cliente_id = p.cliente_id;
            """
            database_response = query_database(query)
            formatted_response = "Los clientes que han realizado pedidos son: " + ", ".join([row[0] for row in database_response])
        elif "Autores que han escrito libros de ficción" in user_input:
            query = """
               SELECT Libros.autor FROM Libros
                JOIN Libros_Categorias ON Libros.libro_id = Libros_Categorias.libro_id
                JOIN Categorias ON Libros_Categorias.categoria_id = Categorias.categoria_id
                WHERE Categorias.nombre = 'Ficción';
            """
            database_response = query_database(query)
            formatted_response = "Los autores que tienen libros de ficción son: " + ", ".join([row[0] for row in database_response])
        else:
            response = chain.invoke({"input": user_input})
            return response

        if database_response:
            return formatted_response
        else:
            response = chain.invoke({"input": user_input})
            return response

    except Exception as e:
        print("Error al manejar la entrada:", e)
        return "Lo siento, hubo un error al procesar tu solicitud."

# Ejemplo de uso
user_input = input("Por favor, introduce tu pregunta: ")
response = handle_input(user_input)
print("Respuesta:", response)
