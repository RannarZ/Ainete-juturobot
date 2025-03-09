import numpy as np
import sqlite3 as sql
from math import sqrt

class VectorStore:

    def __init__(self, dbName, vecSize) -> None:
        self.dbName = dbName
        self.vecSize = vecSize
        self.db = sql.connect(dbName)

    def vector_test_table(self, vector):
        cursor = self.db.cursor()
        #cursor.execute("""CREATE TABLE TESTIMINE (VEKTOR BLOB)""")
        cursor.execute("""INSERT INTO TESTIMINE (VEKTOR) VALUES (?)""", (vector, ))
        cursor.execute("SELECT VEKTOR FROM TESTIMINE")
        fetched = cursor.fetchall()
        for row in fetched:
            print(np.frombuffer(row[0]))
        cursor.close()


    def create_courses_table(self):
            cursor = self.db.cursor()
            #Kuidas salvestada eeldusaineid? Kuidas salvestada tundide jaotust (kas luua teine tabel või teha iga liigi jaoks eraldi tulp)?
            #Kuidas salvestada keeli?
            cursor.execute("""CREATE TABLE KURSUSED(
                        KURSUSE_NIMI VARCHAR2(50) NOT NULL,
                        KURSUSE_KOOD VARCHAR2(15) NOT NULL,
                        VEKTOR BLOB NOT NULL, 
                        EAP NUMBER,
                        KURSUSE_TYYP VARCHAR2(20),
                        KURSUSE_KEELED VARCHAR2(50),
                        VOTA INTEGER,
                        KOHUSTUSLIKUD_EELDUSAINED VARCHAR2(100),
                        SOOVITUSLIKUD_EELDUSAINED VARCHAR2(100),
                        SEMESTER VARCHAR2(10),
                        OPPETYYP VARCHAR2(20),
                        TUNDIDE_JAOTUS VARCHAR2(150),
                        HINDAMISSKAALA VARCHAR2(10),
                        KIRJELDUS TEXT NOT NULL,
                        KOKKUVOTE TEXT NOT NULL
                        )""")
            print("Table created")
            cursor.close()

    def create_feedback_table(self):
        cursor = self.db.cursor()
        cursor.execute("""CREATE TABLE FEEDBACK (
                       PROMPT TEXT NOT NULL,
                       RESPONSE TEXT NOT NULL,
                       RETURNED_VECTORS NUMBER NOT NULL,
                       RETURNED_COURSES NUMBER NOT NULL,
                       RATING NUMBER NOT NULL,
                       TEXT_FEEDBACK TEXT
                       )
                       """)
        print("Table created")
        cursor.close()

    def create_vectorstore(self):
        self.create_courses_table()
        self.create_feedback_table()


    

    def remove_vectorstore(self):
        cursor = self.db.cursor()
        cursor.execute("DROP TABLE IF EXISTS KURSUSED")
        cursor.execute("DROP TABLE IF EXISTS TESTIMINE") #Testing table
        cursor.execute("DROP TABLE IF EXISTS FEEDBACK") #Feedback table table
        cursor.close()

    def clear_table(self):
        cursor = self.db.cursor()
        cursor.execute("DELETE FROM KURSUSED")
        cursor.close()

    def insert_to_courses_table(self, vector, course_name, course_id, eap, course_type, course_languages, vota, mandatory_prereq,
                        reccomended_prereq, semester, study_type, hours, grading, description, summary):
        cursor = self.db.cursor()
        #vector = vector.tobytes()
        #print(vector)
        cursor.execute(f"""INSERT INTO KURSUSED(KURSUSE_NIMI, KURSUSE_KOOD, VEKTOR, EAP, KURSUSE_TYYP,
                        KURSUSE_KEELED, VOTA, KOHUSTUSLIKUD_EELDUSAINED, SOOVITUSLIKUD_EELDUSAINED, SEMESTER,
                        OPPETYYP, TUNDIDE_JAOTUS, HINDAMISSKAALA, KIRJELDUS, KOKKUVOTE)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (course_name, course_id, memoryview(vector),
                                                                                    eap, course_type, course_languages, vota, mandatory_prereq,
                                                                                    reccomended_prereq, semester, study_type, hours, grading, description, summary))
        self.db.commit()
        cursor.close()

    def insert_into_feedback_table(self, prompt, response, returned_vectors, returned_courses, rating, text_feedback):
        cursor = self.db.cursor()
        cursor.execute(f"""
                       INSERT INTO FEEDBACK(PROMPT, RESPONSE, RETURNED_VECTORS, RETURNED_COURSES, RATING, TEXT_FEEDBACK)
                       VALUES (?, ?, ?, ?, ?, ?)
                        """, (prompt, response, returned_vectors, returned_courses, rating, text_feedback))
        self.db.commit()
        cursor.close()

    def print_all_from_table(self):
        #Prints everything except vectors
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM KURSUSED")
        fetched = cursor.fetchall()
        for row in fetched:
            for i in range(15):
                if i != 2:
                    print(str(row[i]))
            print("")
        cursor.close()

    def get_all_from_table(self, table):
        cursor = self.db.cursor()
        cursor.execute(f"SELECT * FROM {table}")
        fetched = cursor.fetchall()
        cursor.close()
        return fetched

    
    def get_course_by_course_id(self, courseID):
        cursor = self.db.cursor()
        cursor.execute(f"SELECT KURSUSE_NIMI, KURSUSE_KOOD, EAP, SEMESTER, KOKKUVOTE FROM KURSUSED WHERE KURSUSE_KOOD = '{courseID}'")
        fetched = cursor.fetchone()
        cursor.close()
        return fetched
    
    def count_all_rows_courses(self):
        cursor = self.db.cursor()
        cursor.execute("SELECT COUNT(*) FROM KURSUSED")
        fetched = cursor.fetchall()
        cursor.close()
        return fetched

    def cosine_distance(self, vec1, vec2):
        top = 0
        bot1 = 0
        bot2 = 0
        for i in range(len(vec1)):
            top += vec1[i] + vec2[i]
            bot1 += vec1[i]**2
            bot2 += vec2[i]**2

        return float(top/(sqrt(bot1)*sqrt(bot2)))
    
    def euklidean_distance(self, vec1, vec2):
        sum = 0
        for i in range(len(vec1)):
            sum += (vec1[i] - vec2[i])**2
        return sqrt(sum)

    def find_k_nearest(self, query, k):
        """
        Method find_k_nearest finds the k nearest vectors to query vector from database and returns the representing course info.
        """
        all_courses = self.get_all_from_table("KURSUSED")
        nearest_dist = []
        nearest_info = []
        r = 0 #running size of nearest list
        for course in all_courses:
            vector = np.frombuffer(course[2])
            distance = self.euklidean_distance(query, vector)
            #If list is empty
            if r == 0:
                nearest_dist.append(distance)
                nearest_info.append((course[0], course[1], course[3], course[9], course[12], course[13], course[14])) #(course[0], course[1], course[3], course[9], course[12], course[13], course[14])
                r += 1
            #If last element is smaller than current distance
            elif abs(nearest_dist[-1]) < abs(distance):
                if r < k:
                    nearest_dist.append(distance)
                    nearest_info.append((course[0], course[1], course[3], course[9], course[12], course[13], course[14]))
                    r += 1
            #If last element of nearest is higher than current distance
            else:
                index = self.get_index_of_nearest(nearest_dist, distance)
                if r < k:
                    nearest_dist.insert(index, distance)
                    nearest_info.insert(index, (course[0], course[1], course[3], course[9], course[12], course[13], course[14]))
                    r += 1
                else:
                    #Adding the new vector and info to lists
                    nearest_dist.insert(index, distance)
                    nearest_info.insert(index, (course[0], course[1], course[3], course[9], course[12], course[13], course[14]))
                    #Deleting the last one from list
                    nearest_dist.remove(nearest_dist[-1])
                    nearest_info.remove(nearest_info[-1])
        print(nearest_dist)
        return nearest_info

    def get_index_of_nearest(self, nearest_dist, distance):
        for i in range(len(nearest_dist)):
            if abs(nearest_dist[i]) > abs(distance):
                return i
        return -1
