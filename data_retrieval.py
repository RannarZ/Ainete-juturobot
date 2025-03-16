import requests
import json
import os
from VectorStore import VectorStore

def ask_api_for_keys():
    """
    Function ask_api_for_keys retrieves all of the courses' keys
    that exist in ois2 and are accessible through the API.
    """
    indeks = 1
    answer = []
    #Getting all courses that take place in autumn
    response = requests.get(f"https://ois2.ut.ee/api/courses?start={indeks}&take=300&semester=autumn&is_expired=True")
    data = response.json()
    while len(data) != 0:
        response = requests.get(f"https://ois2.ut.ee/api/courses?start={indeks}&take=300&semester=autumn&is_expired=True")
        data = response.json()
        for key in data:
            code = key["code"]
            if code not in answer:
                answer.append(code)
                #print(f"Retrieved code {code} over index {indeks}")
            #else:
                #print(f"Code {code} already exists over index {indeks}")
        indeks += 300

    firstIndeks = indeks
    indeks = 1
    #Getting all courses that take place in spring
    response = requests.get(f"https://ois2.ut.ee/api/courses?start={indeks}&take=300&semester=spring&is_expired=True")
    data = response.json()
    while len(data) != 0:
        response = requests.get(f"https://ois2.ut.ee/api/courses?start={indeks}&take=300&semester=spring&is_expired=True")
        data = response.json()
        for key in data:
            code = key["code"]
            if code not in answer:
                answer.append(code)
                #print(f"Retrieved code {code} over index {indeks}")
            #else:
                #print(f"Code {code} already exists over index {indeks}")
        indeks += 300
    print(f"Indekseid kokku: {firstIndeks + indeks}")
    print(f"Algne indeks: {firstIndeks}")
    print(f"Teine indeks: {indeks}")
    print(f"Final answer length {len(answer)}")
    return answer

def ask_api_for_uuids():
    """
    Function ask_api_for_uuids retrieves all of the courses' UUIDs
    that exist in ois2 and are accessible trough the API
    """
    indeks = 1
    answer = []
    response = requests.get(f"https://ois2.ut.ee/api/courses?start={indeks}&take=300")
    data = response.json()
    while len(data) != 0:
        response = requests.get(f"https://ois2.ut.ee/api/courses?start={indeks}&take=300")
        data = response.json()
        for key in data:
            all_json_keys = key.keys()
            if "latest_version_uuid" not in all_json_keys:
                uuid = key["uuid"]
            else:
                uuid = key["latest_version_uuid"]
            print(f"Retrieved uuid {uuid} over index {indeks}")
            answer.append(uuid)
        indeks += 300
    return answer

#Save all of the keys to a text file
def save_keys_to_file(keys_list, file):
    with open(file, "w") as f:
        for key in keys_list:
            f.write(key +  "\n")

def save_keys_and_latest__uuids_to_file(keys_list, uuid_list, file):
    """
    Function save_keys_and_latest__uuids_to_file saves all of the courses keys and their latest version uuids to file.
    The format is "Course code: uuid".
    """
    with open(file, "w") as f:
        for i in range(len(keys_list)):
            f.write(f"{keys_list[i]}: {uuid_list[i]}\n")

def get_uuids_from_file(filename):
    uuids = []
    with open(filename, "r") as f:
        for rida in f:
            uuids.append(rida)
    return uuids

def retrieve_data_about_course(filename, language): #Language either "et" or "en"
    """
    Function retrieve_data_about_course retrieves data about a course to a list.
    The list elements are: course title(0), course code(1), ECTS (2), course type (3), course languages(4),
    is VÕTA (5), prerequisites required (6), prerequisites not required (7),
    semester (8), study type (9), work hours (10), grade type(11), description (12)
    """
    with open(f"./API_jsons/{filename}", "r") as f:
        data = json.load(f)
        if (data == None):
            print(filename)
    #print(data)
    erandid = ["Doktoritöö", "Ettevõttepraktika", "Doktoriseminar", "Magistriseminar keskkonnafüüsikas"]
    if data["title"][language] in erandid:
        return

    #Saving course key
    course_key = filename.split(".j")[0]

    additional_info_dict = data["additional_info"]
    coursename = data["title"][language]
    course_languages = [x[language] for x in data["general"]["input_languages"]]
    is_vota = additional_info_dict["is_vota_course"]
    combined_description = create_combined_course_description(data, language)

    info = {}
    info["KURSUSE_NIMI"] = coursename
    info["KURSUSE_KOOD"] = course_key
    if "credits" in data.keys():
        info["EAP"] = data["credits"] #How many ECT-s
    info["KURSUSE_TYYP"] = data["general"]["type"][language]#Type of the course
    info["KURSUSE_KEELED"] = course_languages
    info["VOTA"] = is_vota

    #Finding prerequisite courses
    if "prerequisites" in additional_info_dict.keys():
        prerequisiteList = additional_info_dict["prerequisites"]
        prerequisites_req = [x["title"][language] for x in prerequisiteList if x["required"]]
        prerequisites_not_req = [x["title"][language] for x in prerequisiteList if not x["required"]]
        info["KOHUSTUSLIKUD_EELDUSAINED"] = prerequisites_req #required prereqs
        info["SOOVITUSLIKUD_EELDUSAINED"] = prerequisites_not_req #not required prereqs

    #Here are attributes that exist in latest version but not in regular
    semester = data["target"]["semester"][language]
    study_type = data["target"]["study_type"][language]

    hour_dict = data["additional_info"]["hours"] #Dealing with it when saving to file.
    assessment_scale = data["grading"]["assessment_scale"]["code"]
    add_grading_to_description(combined_description, data, language)

    info["SEMESTER"] = semester
    info["OPPETYYP"] = study_type
    if "study_levels" in data["additional_info"] and language in data["additional_info"]["study_levels"]:
        levels = data["additional_info"]["study_levels"][language]
        info["OPPETASE"] = levels
    info["TUNDIDE_JAOTUS"] = hour_dict
    info["HINDAMISSKAALA"] = assessment_scale

    #Combined description is last because it will be changed when looking at course latest version
    #It is also a long text
    info["KIRJELDUS"] = combined_description
    #print(info)
    return info

def create_combined_course_description(data, language):
    """
    Creating the course description String.
    """
    overview_dict = data["overview"]

    description = ""
    if language in overview_dict["description"].keys():
        description = overview_dict["description"][language]
    objectives = []
    learning_outcomes = []
    if "objectives" in overview_dict.keys():
        objectives = [x[language] for x in overview_dict["objectives"] if language in x.keys()]
    if "learning_outcomes" in overview_dict.keys():
        learning_outcomes = [x[language] for x in overview_dict["learning_outcomes"] if language in x.keys()]

    combined_description = description
    combined_description = combined_description + "Objectives/eesmärkid: "
    for objective in objectives:
        combined_description = combined_description + " " + objective
    combined_description = combined_description + "Learning outcomes/õpiväljund: "
    for outcome in learning_outcomes:
        combined_description = combined_description + " " + outcome
    if "notes" in overview_dict.keys():
        if len(overview_dict["notes"].keys()) != 0 and language in overview_dict["notes"].keys():
            combined_description = combined_description + " " + overview_dict["notes"][language]
    return combined_description

def add_grading_to_description(combined_description, data, language):
    """
    Adding grading info to course description.
    """
    grading = data["grading"]
    grading_info = ""
    for key in grading:
        if isinstance(grading[key], list):
            for x in grading[key]:
                if "description" in x.keys():
                    if language in x["work_type"].keys():
                        grading_info = grading_info + " " + x["work_type"][language] + " "
                    if language in x["description"].keys():
                        grading_info = grading_info + " " + x["description"][language] + " "
                if language in x.keys():
                    grading_info = grading_info + " " + x[language] + " "
        elif isinstance(grading[key], dict):
            if language in grading[key].keys():
                grading_info = grading_info + " " + grading[key][language] + " "
        elif isinstance(grading[key], int):
             grading_info = grading_info + " " + key + " " + str(grading[key]) + " "

    combined_description = combined_description + grading_info + " "

def save_course_info_to_file(course_info, filename):
    if course_info == None:
        return
    with open(filename, "w", ) as f:
        jsonInput = json.dumps(course_info, ensure_ascii=False)
        f.write(jsonInput)
        #print("done")
        #for key in course_info.keys():
            #f.write(str(key) + ": " + str(course_info[key]) + "\n")

def retrieve_save_jsons_from_api_to_files(course_code, version_uuid):
    """
    This method queries data from ÕIS II API and saves all retrieved JSONs to files.
    The files are located in API_jsons.
    """
    url = f"https://ois2.ut.ee/api/courses/{course_code}/versions/{version_uuid}"
    print(url)
    course_info = requests.get(url)
    data = course_info.json()

    with open(f"./API_jsons_fixed/{course_code}.json", "w", errors="ignore") as f:
        jsonOfData = json.dumps(data, ensure_ascii=False)
        f.write(jsonOfData)
        print(f"{course_code} data saved to file.")
    
def ask_api_for_keys_and_latest_versions_and_save_to_file():
    keys = ask_api_for_keys()
    matched_courses = []
    matched_course_versions = []
    years = [] #For checking the latest version of course
    course_index = 0
    for key in keys:
        newUrl = f"https://ois2.ut.ee/api/courses/{key}/versions"
        data = requests.get(newUrl).json()
        appended = False #Variable for if the course was appended to the list
        for i in range(len(data)):
            #If there exists a course that has the latest year marked earlier than 2024 then we skip that course.
            #Here we only enter the if statement when the last version of year 2025 is found.
            if data[i]["target"]["year"]["code"] == "2025" and (i == len(data) - 1 or data[i+1]["target"]["year"]["code"] != "2025"):
                if key not in matched_courses:
                    matched_courses.append(key)
                    matched_course_versions.append(data[i]["uuid"])
                    years.append(2025)
                    appended = True
                else:
                    matched_course_versions[course_index] = data[i]["uuid"]
                    years[course_index] == 2025 #Updating the year
                    appended = True

                    #print(f"{course_index}. Removing the 2024 version of {key}.")
                #print(f"{course_index}. Adding the latest version of {key} for year 2025.")
            #Here we only enter the if statement when the last version of year 2024 is found.
            if data[i]["target"]["year"]["code"] == "2024" and (i == len(data) - 1 or data[i+1]["target"]["year"]["code"] != "2024"): 
                if key not in matched_courses:
                    matched_courses.append(key)
                    matched_course_versions.append(data[i]["uuid"])
                    years.append(2024)
                    appended = True
                    #print(f"{course_index}. Adding the latest version of {key} for year 2024.")
        if appended:
            course_index+=1
            #print("---------------------")
    
    #print(len(matched_courses))
    #print(len(matched_course_versions))
    #print(len(years))
    if len(matched_courses) == len(matched_course_versions) == len(years):
        save_keys_and_latest__uuids_to_file(matched_courses, matched_course_versions, "Course_codes.txt")
    else:
        print(f"Lists are not the same size.\nmatched_courses {len(matched_courses)}\nmatched_course_versions {len(matched_course_versions)}\nyears{len(matched_course_versions)}")


def retrieve_course_codes_and_uuids_from_file():
    courses = []
    with open("Course_codes.txt", "r") as f:
        for rida in f:
            courses.append(rida)
    return courses

"""
Structure of course info file:

"""
if __name__ == "__main__":
    
    #vecStore = VectorStore("primitiivne_db", 3072)
    #print(len(vecStore.get_all_from_table("KURSUSED")))
    
    #save_keys_to_file(keys, "Course_codes.txt")
    #print(find_how_many_codes_doubled("Course_codes.txt", "Testimise_koodid.txt"))

    """
    #This block is saving all fetched JSON-s to files.
    courses = retrieve_course_codes_and_uuids_from_file()
    for course in courses:
        print(f"Kursuse {course} salvestamine.")
        splitted = course.split(": ")
        code = splitted[0].strip()
        uuid = splitted[1].strip()
        retrieve_save_jsons_from_api_to_files(code, uuid)
    """
    """
    This is the code for retrieving data from ÕIS II API
    uuids = get_uuids_from_file("Course_codes.txt")
    for key in uuids:
        print(key.strip())
        retrieve_save_jsons_from_api_to_files(key.strip())
    """
    """
    fileList = os.listdir("./API_jsons")
    i = 0
    for file in fileList:
        #print(file)
        course_info = retrieve_data_about_course(file, "et") #FLGR.01.138
        save_course_info_to_file(course_info, "./course_desc_est_fixed/"+file.strip())
        i+=1
    """


        
        
