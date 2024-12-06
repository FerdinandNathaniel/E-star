import numpy as np
import faiss

def get_embedding(description, client, model="text-embedding-3-large"):
    """uses the OpenAI API to create an embedding of the given text string

    Args:
        description (str): description of an emotion to be embedded
        client (OpenAI): authenticated connection to OpenAI API
        model (str, optional): OpenAI API model to use for the embedding. Defaults "text-embedding-3-large".

    Returns:
        CreateEmbeddingResponse: class representing metadata and the embedding itself
    """
    # new lines can cause problems with accurate embedding
    description = str(description).replace("\n", " ")
    
    return client.embeddings.create(input = description, model = model).data[0].embedding

def get_faiss_index(df_embeddings):
    embedding_dim = len(df_embeddings['Embedding'].iloc[0])
    embedding_matrix = np.array(df_embeddings['Embedding'].tolist()).astype('float32')
    faiss_index = faiss.IndexFlatL2(embedding_dim)
    faiss_index.add(embedding_matrix)
    
    return faiss_index

def get_emotion_list(df_embeddings):
    return df_embeddings['Emotion'].tolist()

def find_relevant_emotions(user_input, emotion_list, openai_client, faiss_index, previous_emotions=[], top_k=3):
    """Find relevant emotions based on user input and previous selections."""
    # Generate embedding for the user input
    user_input_modified = 'This is a description of my experience: ' + user_input
    user_embedding = get_embedding(user_input_modified, openai_client)
    user_embedding = np.array(user_embedding, dtype='float32').reshape(1, -1)
    distances, indices = faiss_index.search(user_embedding, len(emotion_list))
    
    # Filter out selected emotions
    recommended_emotions = []
    for idx in indices[0]:
        emotion = emotion_list[idx]
        if emotion not in previous_emotions and emotion not in recommended_emotions:
            recommended_emotions.append(emotion)
        if len(recommended_emotions) == top_k:
            break
    
    if not recommended_emotions:
        # Handle end of list
        return []
    
    return recommended_emotions
