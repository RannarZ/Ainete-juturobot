#!C:\Users\Rannar Zirk\anaconda3\envs\loputoo\python.exe
import sys
print(sys.executable)
import numpy as np
from VectorStore import VectorStore
import os
import openai
import json
import streamlit as st
import random
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
    Function update_chosen_tokens_in_json is for counting OpenAI tokens depending on token type.
    """
    with open("token_count.json", "r") as file_readable:
        tokens = json.load(file_readable)
        tokens[token_type] = tokens[token_type] + token_count
    with open("token_count.json", "w") as file_writable:
        tokens = str(tokens).replace("'", "\"")
        file_writable.write(tokens)  

def find_all_valid_courses(allCourses):
    """
    Function find_all_valid_courses finds all the valid courses from gpt-4o response.
    The expected input for a course is "course code: valid/invalid" i.e HVAV.05.011: valid.
    Function returns all the course codes that are considered valid by GPT-4o.
    """
    returnable_list = []
    for course in allCourses:
        splitted = course.split(":")
        if len(splitted) > 1:
            courseCode = splitted[0].strip()
            isValid =  True if splitted[1].strip() == "valid" else False
            if len(courseCode) != 11:
                #Using regex to find combinations of course codes. For example HVAV.05.011.
                courseCode = re.match('[A-Z:0-9]{4}\.\d{2}\.\d{3}', courseCode).group(0)
            if isValid:
                returnable_list.append(courseCode)
        else:
            #TODO: Mõelda välja, mis saab siis, kui ei ole koolonit, mille kohal splittida vastust.
            print(splitted)
    return returnable_list

def query_db_for_course_info(courseID, vectorStore):
    courseInfo = vectorStore.get_course_by_course_id(courseID)
    #print(courseInfo)
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
        outputText += f"<span style='font-size:24px;'>**{courseCode}, {courseName}{courseEAP}{courseSemester}**</span> - {courseSummary} \n \n" 
    return outputText

def generate_response(prompt, vectorStore, number_of_returned, number_of_valid_courses):

    """
    Function generate_response generates a response for the user's query.
    It fetches nearest k courses by vector comparison from the database where k is randomly generated and it is between 10 and 100.
    k also divides by ten. After returning the courses by vector comparison GPT-4o model chooses 5 courses that fit the best for user's query.
    Function also formats the answer.
    """

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
    #Generating the number randombly for user feedback
    
    answer = vectorStore.find_k_nearest(vectorized_prompt, number_of_returned)
    for_gpt_coruses = []
    for course in answer:
        #print(f"{course[0]} {course[1]}")
        course_info = (course[1], course[5])
        for_gpt_coruses.append(course_info)
        
    response = client.chat.completions.create(model = "gpt-4o", temperature=0, messages=[
                {"role": "system", "content": f"""There are university students trying to find new courses to take. They ask from you what type of course they want to take. 
                You are given codes and description of {number_of_returned} university courses and an university student's prompt.
                For each course return whether the course is corresponds to the student's prompt or not. There can only be {number_of_valid_courses} valid courses so choose the best matching {number_of_valid_courses} courses.
                First investigate all of the courses and then make the valid or invalid decision.
                Take into consideration everything the student says. Consider whether a student already can or can not do something and when he or she wants to take the course.
                Let the answer format be "course code: valid/invalid". Do not insert an index before the course code. Make the answer as short as possible.
                The course descriptions and the student's prompt are in Estonian."""},
                {"role": "user", 
                "content": f"{str(for_gpt_coruses)}; {prompt}"
                }])
    
    gptText = response.choices[0].message.content
    #print(gptText)
    validCourses = find_all_valid_courses(gptText.split("\n"))
    #In case gpt does not return a colon inside teh strings then say that something went wrong.
    if len(validCourses) == 0:
        return "Midagi läks valesti."
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

    #Hiding the deploy button (EI TÖÖTA)
    hide_menu_style = """<style>#stAppDeployButton {visibility: hidden;} footer {visibility: hidden;}</style>"""
    st.markdown(hide_menu_style, unsafe_allow_html=True)

    #OPENAI info and variables
    api_key = os.environ["OPENAI_API_KEY"]
    api_version = "2023-07-01-preview"
    azure_endpoint = "https://tu-openai-api-management.azure-api.net/ltat-tartunlp"

    #Initializing client and vector store
    client = openai.AzureOpenAI(api_key=api_key, api_version=api_version, azure_endpoint=azure_endpoint) 
    
        
    #If runned for the first time then we add a response and a prompt variable to session_state
    if 'response' not in st.session_state:
        st.session_state.response = None
        st.session_state.number_of_valid_courses = random.randint(1, 2) * 5 #Number of final returnable courses
        st.session_state.number_of_returned_by_vectors = random.randint(1, 10) * 10 #Number of returned courses by vector comparison

    if 'prompt' not in st.session_state:
        st.session_state.prompt = ""

    st.header("Tartu Ülikooli õppeainete soovitaja")
    st.markdown("""Olen informaatika bakalaureuse kolmanda aasta tudeng Rannar Zirk ning teen oma lõputööks keskkonnas ÕIS II leiduvate Tartu Ülikooli õppeainete soovitajat.
                Soovitaja eesmärk on lihtsustada tudengitel uute ainete avastamist.
                Selleks saab juturobotile sisestada vabas vormis teksti ning vastavalt Teie päringule tagastatakse sobivaimate ainete info. 
                \nJuturoboti loomisel on rakendatud OpenAI mudeleid.
                \nPeale juturoboti kasutamist **küsitakse Teilt tagasisidet** saadud vastuse kohta. Teie päring, soovitaja genereeritud vastus ja tagasiside salvestatakse teaduslikel eesmärkidel. 
                Palun täitke kindlasti tagasisidet, kuna see on lõpitöö väga oluline osa.
                \nÕppeainete soovitaja on välja arendatud tudengiprojektina Tartu Ülikoolis ning ei ole seotud ühegi ülikoolivälise ettevõttega.
                """)
    #If no response has been generated then show the input field
    if st.session_state.response is None:
        st.session_state.prompt = st.text_input("Sisesta enda päring:")
        if st.button("Kinnita"):
            if st.session_state.prompt:
                with st.spinner("Vastuse genereerimine"):
                    vectorStore = VectorStore("database", 3072)
                    st.session_state.response = generate_response(st.session_state.prompt, vectorStore, st.session_state.number_of_returned_by_vectors, st.session_state.number_of_valid_courses)
                    vectorStore.close_connection()
                    st.rerun()  # Refresh to show the answer.
    else:
        vectorStore = VectorStore("database", 3072) 
        #Displaying the response
        st.subheader("Kasutaja päring: ")
        st.write(st.session_state.prompt)

        st.subheader("Soovitaja vastus vastus: ")
        st.markdown(st.session_state.response, unsafe_allow_html=True)
        #Answer feedback
        st.subheader("Mis valdkonnas Te tegutsete?")
        faculty = st.radio("Valige allolevast nimekirjast", ["Loodus-ja täppisteadused", "Sotsiaalteadused", "Humanitaarteadused ja kunst", "Meditsiiniteadus"])

        st.subheader("Hinnake, kuidas soovitused vastasid Teie päringule")
        rating = st.radio("Vastake viie palli skaalal", [1, 2, 3, 4, 5], horizontal=True)

        st.subheader("Põhjendage oma hinnangut (pole kohustuslik, aga annab väga palju tööle juurde)")
        st.session_state.feedback_text = st.text_input("Sisestage tekst")
        #Kui on vajutatud nuppu küsi uuest, siis salvestab kõik tagasiside
        if st.button("Salvesta tagasiside ja küsi uuesti"):
            vectorStore.insert_into_feedback_table(st.session_state.prompt, 
                                      st.session_state.response, 
                                      st.session_state.number_of_returned_by_vectors, 
                                      st.session_state.number_of_valid_courses,
                                      faculty, rating, st.session_state.feedback_text)
            st.session_state.response = None
            st.session_state.prompt = ""
            #Genereerime uue sisendi pikkuse jaoks uued arvud
            st.session_state.number_of_valid_courses = random.randint(1, 2) * 5 #Number of final returnable courses
            st.session_state.number_of_returned_by_vectors = random.randint(1, 10) * 10 #Number of returned courses by vector comparison
            #print(vectorStore.get_all_from_table("FEEDBACK"))
            vectorStore.close_connection()
            st.rerun()


#course indexes: 0-course name, 1-course code, 2-EAP, 3-semester, 4-hindamistüüp, 5-kirjeldus, 6-GPT kokkuvõte
        

    

    
