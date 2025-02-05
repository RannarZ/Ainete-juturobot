import numpy as np
from VectorStore import VectorStore
import os
import openai
import json

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

def check_fields_and_insert_course_to_table(course_info, vector):
    dict_keys = ["KURSUSE_NIMI", "KURSUSE_KOOD", "EAP", "KURSUSE_TYYP", "KURSUSE_KEELED", "VOTA", "KOHUSTUSLIKUD_EELDUSAINED",
                 "SOOVITUSLIKUD_EELDUSAINED", "SEMESTER", "OPPETYYP", "TUNDIDE_JAOTUS", "HINDAMISSKAALA", "KIRJELDUS"]
    final_values = []
    for key in dict_keys:
        if key in course_info.keys():
            if key == "VOTA":
                if course_info[key]:
                    final_values.append(1)
                else:
                    final_values.append(0)
            else:
                final_values.append(course_info[key])
        else:
            final_values.append(None)
    vectorStore.insert_to_table(vector, final_values[0], final_values[1], final_values[2], final_values[3], str(final_values[4]),
                                final_values[5], str(final_values[6]), str(final_values[7]), final_values[8], final_values[9],
                                str(final_values[10]), final_values[11], final_values[12])
    
    
def insert_all_courses_to_database():
    src_path = "./course_vectors_est"
    files_in_src = os.listdir(src_path)
    i = 0
    for file in files_in_src:
        print(f"{i}. {file}")
        bytes_vector = get_vector_from_file_and_turn_to_bytes(file)
        course_data_dict = read_json_from_file(file)
        check_fields_and_insert_course_to_table(course_data_dict, bytes_vector)
        i += 1

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

if __name__ == "__main__":

    api_key = os.environ["OPENAI_API_KEY"]
    api_version = "2023-07-01-preview"
    azure_endpoint = "https://tu-openai-api-management.azure-api.net/ltat-tartunlp"

    client = openai.AzureOpenAI(api_key=api_key, api_version=api_version, azure_endpoint=azure_endpoint)

    
    vectorStore = VectorStore("primitiivne_db", 3072)
    #vectorStore.remove_vectorstore()
    #vectorStore.create_vectorstore()
    #insert_all_courses_to_database()
    prompt = "Anna mulle humanitaaraine, milles ei pea väga palju tegema ning mis toimub kevadel."

    prompt_encode = client.embeddings.create(
        input = prompt,
        model = "text-embedding-3-large"
    )
    #This is workflow of bot
    vector = prompt_encode.data[0].embedding
    tokens = int(prompt_encode.usage.total_tokens)
    update_embedding_tokens_in_json(tokens)

    vectorized_prompt = np.array(vector)
    answer = vectorStore.find_k_nearest(vectorized_prompt, 5)
    for i in range(5):
        print(answer[i])

    

    
