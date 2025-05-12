import json
import os
import openai
from VectorStore import VectorStore
import numpy as np


def create_text_from_json(filename):
    """
    Method create_text_from_json creates one whole text from course JSON file.
    Returns the String of text.
    """
    with open(filename, "r") as f:
        data = json.load(f)
        final_text = ""
        for key in data:
            final_text = final_text + f" {key}: {data[key]}"
    return final_text

def get_json_from_file(filename):
    with open(filename, "r", encoding='ISO-8859-1') as file:
        content = file.read()
        return json.loads(content)

def get_course_desc_from_json(filename):
    """
    Function get_course_desc_from_json gets the course description from json "KIRJELDUS" field.
    """
    with open(filename, "r") as f:
        data = json.load(f)
        returnable = data["KIRJELDUS"]
        return returnable
    
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

def create_vector_of_text(text, client, model="text-embedding-3-large"):
    """
    Function create_vector_of_text gets text as argument and generates vector from that text using text-embedding-3-large model.
    """
    raw_data = client.embeddings.create(
        input = text,
        model = model
    )
    vector = raw_data.data[0].embedding
    tokens = int(raw_data.usage.total_tokens)
    update_embedding_tokens_in_json(tokens)
    return vector

def get_vector_from_file_and_turn_to_bytes(filename):
    #Length of vector is 3072
    with open(filename, "r") as f:
        vector_as_string_list = f.readline()[1:].split(", ")
    final_vector = np.empty((3072))
    for i in range(len(vector_as_string_list)):
        if (i == len(vector_as_string_list) - 1):
            vector_as_string_list[i] = vector_as_string_list[i][:-1]
        final_vector[i] = (float(vector_as_string_list[i]))
    bytes_array = final_vector.tobytes()
    return bytes_array

def save_info_to_file(filename, vector): #Vector can be a vector but also string. Depending on where you save
    with open(filename, "w") as f:
        f.write(str(vector)) 

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

def get_summary_from_file(filename):
    with open(filename, "r") as f:
        text = f.read()
        return text
    
def check_fields_and_insert_course_to_table(course_info, vector, summary, full_description):
    dict_keys = ["KURSUSE_NIMI", "KURSUSE_KOOD", "EAP", "KURSUSE_TYYP", "KURSUSE_KEELED", "VOTA", "KOHUSTUSLIKUD_EELDUSAINED",
                 "SOOVITUSLIKUD_EELDUSAINED", "SEMESTER", "OPPETYYP", "TUNDIDE_JAOTUS", "HINDAMISSKAALA"]
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
    vecStore.insert_to_courses_table(vector, final_values[0], final_values[1], final_values[2], final_values[3], str(final_values[4]),
                                final_values[5], str(final_values[6]), str(final_values[7]), final_values[8], final_values[9],
                                str(final_values[10]), final_values[11], full_description, summary)

if __name__ == "__main__":
    """
    #Creatingthe database
    vecStore = VectorStore("primitiivne_db", 3072)
    vecStore.create_feedback_table()
    """
    api_key = os.environ["OPENAI_API_KEY"]
    api_version = "2023-07-01-preview"
    azure_endpoint = "https://tu-openai-api-management.azure-api.net/ltat-tartunlp"
    client = openai.AzureOpenAI(api_key=api_key, api_version=api_version, azure_endpoint=azure_endpoint)

    #prompt = "Tere, mina olen Rannar!"
    model = "gpt-4o"

    vecStore = VectorStore("database", 3072)
    """
    vecStore.remove_vectorstore()
    vecStore.create_vectorstore()

    #Adding course info to database
    folder_receive_summary = "./course_descriptions_by_4o_EST"
    folder_receive_JSON = "./course_desc_est"
    folder_receive_vectors = "./course_vectors_est"
    sum_folder = os.listdir(folder_receive_summary) 
    desc_est_folder_list = os.listdir(folder_receive_JSON)
    for file in sum_folder:
        print(file)
        json_name = file.replace(".txt", ".json") #Also vector name because I saved vectors to JSON files
        cleaned_json_name = json_name
        #Cleaning the latest part in the file.
        if "LATEST" in file:
            cleaned_json_name = file.split("_")[0] + ".json"
        #Checking if the course exists in course_desc_est folder because some were imported in autumn and not correctly.
        if cleaned_json_name not in desc_est_folder_list:
            continue
        json_info = get_json_from_file(f"{folder_receive_JSON}/{cleaned_json_name}")
        vector = get_vector_from_file_and_turn_to_bytes(f"{folder_receive_vectors}/{cleaned_json_name}")
        summary = get_summary_from_file(f"{folder_receive_summary}/{file}")
        full_description = create_text_from_json(f"{folder_receive_JSON}/{cleaned_json_name}")
        json_keys = json_info.keys()
        check_fields_and_insert_course_to_table(json_info, vector, summary, full_description)
    """
    
    #Generating short summaries of each course using gpt-4o model
    #vecStore.print_all_from_table()
    folder_receive = "./course_desc_est/" #JSON folder
    folder_save = "./course_descriptions_by_4o_EST/" #New vectors folder
    desc_folder = os.listdir("./course_desc_est") 
    files_in_dest_folder = os.listdir("./course_descriptions_by_4o_EST") 
    i = 0

    for file in desc_folder:
        cleaned_file_name = file.split(".json")[0]
        print(cleaned_file_name)
        if f"{cleaned_file_name}.txt" in files_in_dest_folder or f"{cleaned_file_name}_LATEST.txt" in files_in_dest_folder:
            print(f"{cleaned_file_name} already in destination folder")
            i+=1
            continue
        #834 JÄI VAHELE ANDIS MINGI CONTENT ERRORI
        #1540 jäi vahele sama põhjus
        #1541 samuti
        if i >= 0:
            text = get_course_desc_from_json(folder_receive + file) #Converting JSON to text format
            #print(text)
            response = client.chat.completions.create(model = model, messages=[
                {"role": "user", 
                "content": text + """; Tee eelmisest tekstist lühikokkuvõte.
                    Tagasta ühtne tekst. Ära tee punktidega nimekirja.
                Tagasta ainult selline informatsioon, mis võiks huvitada tudengit, kes otsib uusi huvitavaid aineid.
                Võta terve jutt kokku kolme kuni viie lausega.

                Kui selles on midagi inglise keeles, siis tõlgi eesti keelde."""
                }])
            gptText = response.choices[0].message.content
            print(gptText)
            #Counting all the tokens for pricing calculations
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            update_chosen_tokens_in_json(input_tokens, "input_tokens")
            update_chosen_tokens_in_json(output_tokens, "output_tokens")
            fixed_text = gptText.replace('\u200b', ' ')
            save_info_to_file(folder_save + cleaned_file_name + ".txt", fixed_text)
        print(i)
        i += 1
    
    """
    client = openai.AzureOpenAI(api_key=api_key, api_version=api_version, azure_endpoint=azure_endpoint)

    #Creating the vectors from course texts
    folder_receive = "./course_desc_est/" #JSON folder
    folder_save = "./course_vectors_est_fixed/" #New vectors folder
    desc_folder = os.listdir("./course_desc_est") 
    i=0
    for file in desc_folder:
        text = create_text_from_json(folder_receive + file) #Converting JSON to text format
        vector = create_vector_of_text(text, client) #Creating vector from text
        save_info_to_file(f"{folder_save}{file}", vector) #Saving vector to files (accidentally .json files)
        i += 1
    # 0.01$ = 76923 embedding tookenit"
    """



