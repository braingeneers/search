import os
from langchain import OpenAI, SQLDatabase, SQLDatabaseChain

from dotenv import load_dotenv
load_dotenv()

db = SQLDatabase.from_uri(os.environ['DATABASE_URL'])
llm = OpenAI(temperature=0, verbose=True)

db_chain = SQLDatabaseChain.from_llm(llm, db, verbose=True)

db_chain.run("How many experiments are there?")


db_chain.run("What is the most common number of wells?")


db_chain.run("What is the most number of images in an experiments?")