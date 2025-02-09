#!C:\Users\Rannar Zirk\anaconda3\envs\loputoo\python.exe
import sys
print(sys.executable)
import numpy as np
from VectorStore import VectorStore
import os
import openai
import json
import streamlit as st

#Vektorite töötlemiseks järgmised read:
    #Peale tabelist pärimist vaja eemaldada esimene ning viimane element ehk [1:-1] või [2:-2]
    #np.fromstring(thing, dtype=float, sep=" ")

def get_vector_from_file_and_turn_to_bytes(filename):
    #Length of vector is 3072
    with open(f"./course_vectors_est/{filename}", "r") as f:
        vector_as_string_list = f.readline()[1:].split(", ")
    final_vector = np.empty((3072))
    for i in range(len(vector_as_string_list)):
        if (i == len(vector_as_string_list) - 1):
            vector_as_string_list[i] = vector_as_string_list[i][:-1]
        final_vector[i] = (float(vector_as_string_list[i]))
    bytes_array = final_vector.tobytes()
    return bytes_array

def read_json_from_file(filename):
    with open(f"./course_desc_est/{filename}", "r") as f:
        data = json.load(f)
    return data

def get_embedding(client, text, model="text-embedding-3-large"):
    text = text.replace("\n", " ")

    response = client.embeddings.create(input=prompt, model=model)
    return response

def generate_answer(client, text, model="gpt-4o"):
    response = client.chat.completions.create(model = model, messages=[{"role": "user", "content": text}])
    return response

def update_embedding_tokens_in_json(token_count):
    """
    Function update_embedding_tokens_in_json is for counting OpenAI embedding tokens.
    """
    with open("token_count.json", "r") as file_readable:
        tokens = json.load(file_readable)
        tokens["embedding_tokens"] = tokens["embedding_tokens"] + token_count
    with open("token_count.json", "w") as file_writable:
        tokens = str(tokens).replace("'", "\"")
        file_writable.write(tokens)

def update_chosen_tokens_in_json(token_count, token_type):
    """
    Function update_embedding_tokens_in_json is for counting OpenAI tokens depending on token type.
    """
    with open("token_count.json", "r") as file_readable:
        tokens = json.load(file_readable)
        tokens[token_type] = tokens[token_type] + token_count
    with open("token_count.json", "w") as file_writable:
        tokens = str(tokens).replace("'", "\"")
        file_writable.write(tokens)  

if __name__ == "__main__":

    #Saving the state variable for frontend
    if "count" not in st.session_state:
        st.session_state.count = 0
    st.header("Tartu Ülikooli ainete juturobot")

    #OPENAI info and variables
    api_key = os.environ["OPENAI_API_KEY"]
    api_version = "2023-07-01-preview"
    azure_endpoint = "https://tu-openai-api-management.azure-api.net/ltat-tartunlp"

    #Initializing client and vector store
    client = openai.AzureOpenAI(api_key=api_key, api_version=api_version, azure_endpoint=azure_endpoint)
    vectorStore = VectorStore("primitiivne_db", 3072)

    prompt = ""
    #Prompt text field
    if st.session_state.count == 0:
        prompt = st.text_input("Sisesta päring")
        original_prompt = prompt

    if len(prompt) != 0:
        #Changing session state to 1
        st.session_state.count = 1
        prompt_encode = client.embeddings.create(
            input = prompt,
            model = "text-embedding-3-large"
        )
        #This is workflow of bot
        vector = prompt_encode.data[0].embedding
        tokens = int(prompt_encode.usage.total_tokens)
        update_embedding_tokens_in_json(tokens)

        vectorized_prompt = np.array(vector)
        answer = vectorStore.find_k_nearest(vectorized_prompt, 100)
        for course in answer:
            print(course[0])

        #TODO: Parandada seda system päringut ning vaja uurida, kuidas teist päringut vormistada.
        response = client.chat.completions.create(model = "gpt-4o", messages=[
                    {"role": "system", "content": """Sinu ülesandeks on valida etteantud ülikooli ainete kirjelduste põhjal kasutaja päringule viis sobivaimat vastet.
                    Selleks tagasta nende ainete indeksid ja aine nimetus etteantud järjendis. Kasutaja poolt on ette antud järjend, kus on sulgude sees aine info ning need on eraldatud komaga. Loendamine algab nullist.
                    Järjendile järgneb peale semikoolonit kasutaja päring, millele on vaja vastet otsida. Tee võimalikul lühike vastus."""},
                    {"role": "user", 
                    "content": f"{str(answer)}; {prompt}"
                    }])
        
        gptText = response.choices[0].message.content
        print(gptText)
        st.write(gptText)
        #Counting all the tokens for pricing calculations
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        update_chosen_tokens_in_json(input_tokens, "input_tokens")
        update_chosen_tokens_in_json(output_tokens, "output_tokens")
        prompt = ""
    
    st.text("Kuidas hindate saadud vastust?")
    feedback = st.feedback("stars")

    send_button = st.button("Salvesta vastus")
    if send_button:
        st.session_state.count = 0
        #TODO: implementeerida tagasiside salvestamine




#course indexes: 0-course name, 1-course code, 2-EAP, 3-semester, 4-hindamistüüp, 5-kirjeldus, 6-GPT kokkuvõte
        

    

    
