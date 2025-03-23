import random
import VectorStore

vecStore = VectorStore.VectorStore("database", 3072)
#vecStore.upgrade_feedback()
print(vecStore.get_all_from_table("FEEDBACK"))