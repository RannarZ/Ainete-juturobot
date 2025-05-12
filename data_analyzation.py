import VectorStore

vecStore = VectorStore.VectorStore("database", 3072)

#Kõikide vastanute arv
count = vecStore.get_all_count_from_feedback()
print(f"Kokku oli vastanuid: {count[0]}\n")

#Vastanute arv valdkonniti
facCount = vecStore.count_all_faculty()
print(f"Valdkonniti oli vastanuid: {facCount}\n")

#Keskmine meeldivus arvuliselt
ratings = vecStore.get_all_ratings()
ratingCount = vecStore.count_all_ratings()
print(f"Kõik hinnangud loendatult: {ratingCount}")
average = 0
for rating in ratings:
    average += rating[0]
average = round(average / 87.0, 2)
print(f"Kõikide hinnangute keskmine: {average}\n")

#Suhe tagastatavate vektorite arvu ja meeldivuse vahel

retVectors = vecStore.count_all_occurances_vector_number()
for x in retVectors:
    print(f"Vektorite arvu {x[0]} juures oli keskmine hinnang {round(x[1]/x[2], 2)} ja kokku oli vastanuid {x[2]}")
print(retVectors)

#Suhe tagastatavate ainete arvu ja meeldivuse vahel

retVectors = vecStore.count_all_occurances_returned_course_number()
for x in retVectors:
    print(f"Ainete arvu {x[0]} juures oli keskmine hinnang {round(x[1]/x[2], 2)} ja kokku oli vastanuid {x[2]}")
print(retVectors)

