import json
import os
import openai

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
    raw_data = client.embeddings.create(
        input = text,
        model = model
    )
    vector = raw_data.data[0].embedding
    tokens = int(raw_data.usage.total_tokens)
    update_embedding_tokens_in_json(tokens)
    return vector

def save_vector_to_file(filename, vector):
    with open(filename, "w") as f:
        f.write(str(vector))


if __name__ == "__main__":
    api_key = os.environ["OPENAI_API_KEY"]
    api_version = "2023-07-01-preview"
    azure_endpoint = "https://tu-openai-api-management.azure-api.net/ltat-tartunlp"
    prompt = "Tere, mina olen Rannar!"

    client = openai.AzureOpenAI(api_key=api_key, api_version=api_version, azure_endpoint=azure_endpoint)
    """
    #Creating the vectors from course texts
    folder_receive = "./course_desc_est/" #JSON folder
    folder_save = "./course_vectors_est/" #New vectors folder
    desc_folder = os.listdir("./course_desc_est") 
    i=0
    for file in desc_folder:
        text = create_text_from_json(folder_receive + file) #Converting JSON to text format
        vector = create_vector_of_text(text, client) #Creating vector from text
        save_vector_to_file(f"{folder_save}{file}", vector) #Saving vector to files (accidentally .json files)
        i += 1
    # 0.01$ = 76923 tookenit
    """



