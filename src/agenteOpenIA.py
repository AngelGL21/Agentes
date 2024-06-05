from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits import create_sql_agent
from langchain_community.vectorstores import FAISS
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_openai import OpenAIEmbeddings

from langchain_core.prompts import (
    ChatPromptTemplate,
    FewShotPromptTemplate,
    MessagesPlaceholder,
    PromptTemplate,
    SystemMessagePromptTemplate,
)

# Establecer la conexión a la base de datos MySQL "herber4"
db = SQLDatabase.from_uri("mysql+pymysql://root:angel123@localhost:3306/libreria")

# Clave de API de OpenAI
openai_api_key = "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"

# Crear un modelo de lenguaje natural de ChatOpenAI con la clave de API proporcionada
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=openai_api_key)

# Ejemplos de consultas SQL para interactuar con la base de datos
examples = [
    {"input": "Listar todos los libros de fantasía.", "query":
        "SELECT Libros.titulo FROM Libros "
        "JOIN Libros_Categorias ON Libros.libro_id = Libros_Categorias.libro_id "
        "JOIN Categorias ON Libros_Categorias.categoria_id = Categorias.categoria_id "
        "WHERE Categorias.nombre = 'Fantasía';"
    },
    {"input": "Listar los empleados que tienen un salario superior a $2500.", "query": """
        SELECT nombre, salario FROM Empleados WHERE salario > 2500;
    """},
    {"input": "Listar los clientes cuyo nombre comience con 'J'.", "query": """
        SELECT nombre FROM Clientes WHERE nombre LIKE 'J%';
    """},
    {"input": "Listar los libros publicados después del año 2000.", "query": """
        SELECT titulo, fecha_publicacion FROM Libros WHERE YEAR(fecha_publicacion) > 2000;
    """},
    {"input": "Listar los proveedores cuyo nombre contenga la palabra 'Editorial'.", "query": """
        SELECT nombre FROM Proveedores WHERE nombre LIKE '%Editorial%';
    """},
    # Agrega más ejemplos según sea necesario
]

# Seleccionador de ejemplos semánticamente similares
example_selector = SemanticSimilarityExampleSelector.from_examples(
    examples,
    OpenAIEmbeddings(openai_api_key=openai_api_key),  # Pasar la clave de API aquí
    FAISS,
    k=5,
    input_keys=["input"],
)

# Prefijo del mensaje del sistema
system_prefix = """Eres un agente diseñado para interactuar con una base de datos SQL.
Dada una pregunta de entrada, crea una consulta {dialect} sintácticamente correcta para ejecutar, luego mira los resultados de la consulta y devuelve la respuesta en un formato amigable para el usuario.
A menos que el usuario especifique un número específico de ejemplos que desee obtener, siempre limita tu consulta a un máximo de {top_k} resultados.
Puedes ordenar los resultados por una columna relevante para devolver los ejemplos más interesantes en la base de datos.
Nunca consultes todas las columnas de una tabla específica, solo solicita las columnas relevantes dada la pregunta.
Tienes acceso a herramientas para interactuar con la base de datos.
Solo usa las herramientas proporcionadas. Solo usa la información devuelta por las herramientas para construir tu respuesta final.
DEBES verificar tu consulta antes de ejecutarla. Si obtienes un error mientras ejecutas una consulta, reescribe la consulta y prueba nuevamente.

NO realices ninguna declaración DML (INSERT, UPDATE, DELETE, DROP, etc.) en la base de datos.

Si la pregunta no parece relacionada con la base de datos, simplemente devuelve "No sé" como respuesta.

Aquí hay algunos ejemplos de entradas de usuario y sus consultas SQL correspondientes:"""

# Plantilla de prompt de FewShot
few_shot_prompt = FewShotPromptTemplate(
    example_selector=example_selector,
    example_prompt=PromptTemplate.from_template(
        "Entrada del usuario: {input}\nConsulta SQL: {query}"
    ),
    input_variables=["input", "dialect", "top_k"],
    prefix=system_prefix,
    suffix="",
)

# Plantilla completa del prompt
full_prompt = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate(prompt=few_shot_prompt),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ]
)

# Obtener la pregunta desde la línea de comandos
question = input("Por favor, ingresa tu pregunta: ")

# Crear un agente para ejecutar las consultas
agent_executor = create_sql_agent(
    llm=llm,
    db=db,
    prompt=full_prompt,
    verbose=True,
    agent_type="openai-tools",
)

# Invocar al agente y obtener la respuesta
response = agent_executor.invoke({"input": question})

# Imprimir la respuesta del agente
print("Respuesta del agente:", response)
