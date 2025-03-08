#!C:\Users\Rannar Zirk\anaconda3\envs\loputoo\python.exe
import sys
print(sys.executable)
import numpy as np
from VectorStore import VectorStore
import os
import openai
import json
import streamlit as st
import re

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

def find_all_valid_courses(allCourses):
    returnable_list = []
    for course in allCourses:
        splitted = course.split(":")
        courseCode = splitted[0].strip()
        isValid =  True if splitted[1].strip() == "valid" else False
        if len(courseCode) != 11:
            continue
        if isValid:
            returnable_list.append(courseCode)
    return returnable_list

def query_db_for_course_info(courseID, vectorStore):
    courseInfo = vectorStore.get_course_by_course_id(courseID)
    print(courseInfo)
    return courseInfo

def format_output(coursesInfo):
    #courses indexes: 0-course name, 1-course code, 2-EAP, 3-semester, 4-summary
    outputText = ""
    for course in coursesInfo:
        courseName = course[0]
        courseCode = course[1]
        courseEAP = f", EAP: {course[2]}" if course[2] != None else ""
        courseSemester = f", semester: {course[3]}" if course[3] != None else ""
        courseSummary = course[4]
        outputText += f"**{courseCode}, {courseName}{courseEAP}{courseSemester}** - {courseSummary} \n \n" 
    return outputText

def generate_response(prompt, vectorStore):

    #TODO: Random element on vaja sisse tuua
    #TODO: Tagasiside andmebaasi salvestamine on vaja implementeerida.

    #Changing session state to 1
    prompt_encode = client.embeddings.create(
        input = prompt,
        model = "text-embedding-3-large"
    )
    #This is workflow of bot
    vector = prompt_encode.data[0].embedding
    tokens = int(prompt_encode.usage.total_tokens)
    update_embedding_tokens_in_json(tokens)

    vectorized_prompt = np.array(vector)
    number_of_returned = 5
    answer = vectorStore.find_k_nearest(vectorized_prompt, number_of_returned)
    for_gpt_coruses = []
    for course in answer:
        print(f"{course[0]} {course[1]}")
        course_info = (course[1], course[5])
        for_gpt_coruses.append(course_info)
        
    number_of_valid_courses = 5
    response = client.chat.completions.create(model = "gpt-4o", messages=[
                {"role": "system", "content": f""" You are given codes and description of {number_of_returned} university courses and an user prompt.
                For each course return whether the course is valid with user prompt or not. There can only be {number_of_valid_courses} valid courses so choose the closest {number_of_valid_courses}.
                Look through all the courses and then make the decision.
                Let the answer format be "course code: valid/invalid". Make the answer as short as possible.
                The course descriptions and the prompt is in Estonian."""},
                {"role": "user", 
                "content": f"{str(for_gpt_coruses)}; {prompt}"
                }])
    
    gptText = response.choices[0].message.content

    validCourses = find_all_valid_courses(gptText.split("\n"))
    validCoursesInfo = []
    for course in validCourses:
        validCoursesInfo.append(query_db_for_course_info(course, vectorStore))
    formattedAnswer = format_output(validCoursesInfo)

    #Counting all the tokens for pricing calculations
    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens
    update_chosen_tokens_in_json(input_tokens, "input_tokens")
    update_chosen_tokens_in_json(output_tokens, "output_tokens")

    return formattedAnswer

if __name__ == "__main__":
    #OPENAI info and variables
    api_key = os.environ["OPENAI_API_KEY"]
    api_version = "2023-07-01-preview"
    azure_endpoint = "https://tu-openai-api-management.azure-api.net/ltat-tartunlp"

    #Initializing client and vector store
    client = openai.AzureOpenAI(api_key=api_key, api_version=api_version, azure_endpoint=azure_endpoint)
    vectorStore = VectorStore("primitiivne_db", 3072)
    prompt = ""
        
    if 'response' not in st.session_state:
        st.session_state.response = None
    if 'prompt' not in st.session_state:
        st.session_state.prompt = ""

    st.header("ÕIS II ainete juturobot")
    #If no response ahs been generated then show the input field
    if st.session_state.response is None:
        st.session_state.prompt = st.text_input("Sisesta enda küsimus:")
        if st.button("Kinnita"):
            if st.session_state.prompt:
                with st.spinner("Vastuse genereerimine"):
                    st.session_state.response = generate_response(st.session_state.prompt, vectorStore)
                    st.rerun()  # Refresh to show the answer.
    else: 
        #Displaying the response
        st.subheader("Juturoboti vastus: ")
        st.write(st.session_state.response)

        #Answer feedback
        st.subheader("Kuidas oled rahul juturoboti vastusega?")
        rating = st.radio("5 palli skaalal", [1, 2, 3, 4, 5])

        if st.button("Küsi uuesti"):
            st.session_state.response = None
            st.session_state.prompt = ""
            st.rerun()


#course indexes: 0-course name, 1-course code, 2-EAP, 3-semester, 4-hindamistüüp, 5-kirjeldus, 6-GPT kokkuvõte
        

    

    
