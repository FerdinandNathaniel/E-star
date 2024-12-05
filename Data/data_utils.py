####################
#
# Data processing.py
#
# Contains functions for processing the raw data into processed data
#
####################

def get_embedding(description, client, model="text-embedding-3-large"):
    """uses the OpenAI API to create an embedding of the given text string

    Args:
        description (str): description of an emotion to be embedded
        client (OpenAI): authenticated connection to OpenAI API
        model (str, optional): OpenAI API model to use for the embedding. Defaults "text-embedding-3-large"

    Returns:
        CreateEmbeddingResponse: class representing metadata and the embedding itself
    """
    # new lines can cause problems with accurate embedding
    description = str(description).replace("\n", " ")
    
    return client.embeddings.create(input = description, model = model).data[0].embedding
