from openai import OpenAI
import os, logging

client = OpenAI()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)5s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

def delete_vector_store(v_id):
    files = client.vector_stores.files.list(
            vector_store_id=v_id).data
    for f in files:
        try:
            client.vector_stores.files.delete(
                vector_store_id=v_id,
                file_id=f.id)
            client.files.delete(f.id)
        except Exception as e:
            log.debug("Skip file %s: %s", f.id, e)

    # finally remove the store
    try:
        client.vector_stores.delete(v_id)
        log.info("Deleted vector store %s", v_id)
    except Exception as e:
        log.warning("Could not delete vector store: %s", e)

if __name__ == "__main__":
    j = 0
    while True:
        vector_stores = client.vector_stores.list(limit=100)
        if len(vector_stores.data) == 0:
            log.exception(f"Exitting program, no more vector stores.")
            quit()
        for i, v_store in enumerate(vector_stores):
            log.info(f"{j} + {i}: Deleting vector store {v_store.name}")
            delete_vector_store(v_store.id)
        j += 1
