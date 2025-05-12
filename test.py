import random
import VectorStore

vecStore = VectorStore.VectorStore("database", 3072)
#vecStore.upgrade_feedback()
"""
feed = vecStore.get_all_from_table("FEEDBACK")
sum = 0
for ent in feed:
    print(ent)
"""
kurs = vecStore.get_course()

for ent in kurs:
    print(ent)