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

def find_relevant_emotions(user_input, emotion_list, openai_client, faiss_index, previous_emotions=[]):
    """Find relevant emotions based on user input and previous selections."""
    
    # Generate embedding for the user input
    user_input_modified = ('I am looking for NON ENGLISH emotions that best describe my experience. ' +
                           'This is a description of my experience: ' + 
                           user_input + 
                           ' Which emotion do you think best describes my experience?' + 
                           ' I want NON ENGLISH emotions!')
    user_embedding = get_embedding(user_input_modified, openai_client)
    user_embedding = np.array(user_embedding, dtype='float32').reshape(1, -1)
    distances, indices = faiss_index.search(user_embedding, len(emotion_list))
    
    # Filter out selected emotions
    recommended_emotions = []
    first_emotion_percentile = int(len(indices[0]) * 0.05)
    second_emotion_percentile = int(len(indices[0]) * 0.10)
    third_emotion_percentile = int(len(indices[0]) * 0.40)
    
    def get_emotion_from_percentile(start, end):
        for idx in indices[0][start:end]:
            emotion = emotion_list[idx]
            if emotion not in previous_emotions and emotion not in recommended_emotions:
                return emotion
        return None
    
    recommended_emotions.append(get_emotion_from_percentile(0, first_emotion_percentile))
    recommended_emotions.append(get_emotion_from_percentile(first_emotion_percentile, second_emotion_percentile))
    recommended_emotions.append(get_emotion_from_percentile(second_emotion_percentile, third_emotion_percentile))
    
    if not recommended_emotions:
        # Handle end of list
        return []
    
    return recommended_emotions

def find_relevant_base_emotions():
    base_emotion_positive = [
        'Joy',
        'Awe',
        'Hope'
    ]
    
    base_emotion_neutral = [
        'Anticipation',
        'Surprise',
        'Trust'        
    ]
    
    base_emotion_negative = [
        'Anger',
        'Disgust',
        'Fear',
        'Sadness'    
    ]
    
    # return 1 random emotion from each base emotion category
    return [np.random.choice(base_emotion_positive), 
            np.random.choice(base_emotion_neutral),
            np.random.choice(base_emotion_negative)]
