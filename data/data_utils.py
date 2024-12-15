import time
from openai import OpenAIError

####################
#
# Data processing.py
#
# Contains functions for processing the raw data into processed data
#
####################

def get_embedding(description, client, model="text-embedding-3-large", retries=10, delay=5):
    """uses the OpenAI API to create an embedding of the given text string

    Args:
        description (str): description of an emotion to be embedded
        client (OpenAI): authenticated connection to OpenAI API
        model (str, optional): OpenAI API model to use for the embedding. Defaults "text-embedding-3-large"
        retries (int, optional): number of times to retry in case of a timeout. Defaults to 10.
        delay (int, optional): delay between retries in seconds. Defaults to 5.

    Returns:
        CreateEmbeddingResponse: class representing metadata and the embedding itself
    """
    # new lines can cause problems with accurate embedding
    description = str(description).replace("\n", " ")
    
    for attempt in range(retries):
        try:
            return client.embeddings.create(input=description, model=model).data[0].embedding
        except OpenAIError as e:
            print(f"Error during embedding: {e}\nAmount of retries left: {retries - attempt}")
            print(f"current description: {description}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise
