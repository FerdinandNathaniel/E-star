import numpy as np
import faiss
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

from printing import print_emotion_collection

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

def find_relevant_emotions(user_input, emotion_list, client, faiss_index, previous_emotions=[]):
    """Find relevant emotions based on user input and previous selections."""
    
    # Generate embedding for the user input
    user_input_modified = ('I am looking for NON ENGLISH emotions that best describe my experience. ' +
                           'This is a description of my experience: ' + 
                           user_input + 
                           ' Which emotion do you think best describes my experience?' + 
                           ' I want NON ENGLISH emotions!')
    user_embedding = get_embedding(user_input_modified, client)
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

def get_descriptions(df_embeddings, emotions):
    return {emotion: f"<strong>{emotion}</strong> [{df_embeddings.loc[df_embeddings['Emotion'] == emotion, 'Language'].iloc[0]}]<br>{df_embeddings.loc[df_embeddings['Emotion'] == emotion, 'Description'].iloc[0]}"
            for emotion in emotions}


def handle_first_pass(user_input, session, df_embeddings, emotion_list):
    
    if user_input[-1] != '.': 
        # Ensure user inputted sentence ends with a period
        user_input += '.'
    
    # Initialise session variables, for easy passing between routes/functions
    session['previous_emotions'] = []
    session['chosen_emotions'] = []
    session['original_user_input'] = user_input
    session['user_input'] = user_input
    session['collection'] = []
    session['emotion_list'] = emotion_list

    # Get recommended_emotions for the first pass
    recommended_emotions = find_relevant_base_emotions()
    
    # Append recommended_emotions to previous_emotions
    previous_emotions = session['previous_emotions']
    for emotion in recommended_emotions:
        previous_emotions.append(emotion)
    
    descriptions = get_descriptions(df_embeddings, recommended_emotions)
    return render_template('results.html', 
                           emotions=recommended_emotions, 
                           user_input=user_input, 
                           previous_sets=[],
                           current_prompt=user_input, 
                           original_user_input=user_input,
                           descriptions=descriptions)

def handle_get_emotions(user_input, chosen_emotion, df_embeddings, session, client, faiss_index):
    
    # Get user_input
    original_user_input = session['original_user_input']
    
    # Get previous emotions
    previous_emotions = session['previous_emotions']
    
    # Create sets of previous emotions (groups of 3)
    previous_sets = [previous_emotions[i:i+3] for i in range(0, len(previous_emotions), 3)]
    
    # Get chosen_emotion and add it to list of chosen emotions
    chosen_emotions = session['chosen_emotions']
    chosen_emotions.append(chosen_emotion)
    
    # Find out the other emotions
    other_emotions = previous_emotions[-3:].copy()
    other_emotions.remove(chosen_emotion)
    
    # Append chosen emotion and other emotions to user input
    user_input += f" I feel that '{chosen_emotion}' describes my experience better than '{other_emotions[0]}' and '{other_emotions[1]}'."
    
    # Get recommended_emotions
    recommended_emotions = find_relevant_emotions(
        user_input=user_input, 
        emotion_list=session['emotion_list'], 
        previous_emotions=previous_emotions, 
        client=client, 
        faiss_index=faiss_index
    )
    
    # Append recommended_emotions to previous_emotions
    for emotion in recommended_emotions:
        previous_emotions.append(emotion)

    # Session has been modified at this point
    session.modified = True

    descriptions = get_descriptions(df_embeddings, previous_emotions)
    return render_template('results.html', 
                           emotions=recommended_emotions, 
                           user_input=user_input, 
                           previous_sets = previous_sets,
                           chosen_emotion=chosen_emotion, 
                           chosen_emotions=chosen_emotions,
                           original_user_input=original_user_input,
                           descriptions=descriptions)
    
def handle_rewind_to_emotion(target_emotion, target_set_index, df_embeddings, session, client, faiss_index):
    
    # Get current state
    previous_emotions = session['previous_emotions']
    chosen_emotions = session['chosen_emotions']
    original_user_input = session['original_user_input']
    
    # Calculate where to rewind to
    emotions_per_set = 3
    target_index = (target_set_index * emotions_per_set) + previous_emotions[target_set_index * emotions_per_set:
                                                                             (target_set_index + 1) * emotions_per_set].index(target_emotion)
    
    # Rewind the states
    # Calculate end index based on target_index ranges
    end_index = ((target_index // 3) + 1) * 3 - 1  # 3 is emotions_per_set
    previous_emotions = previous_emotions[:end_index + 1]

    chosen_emotions = chosen_emotions[:target_set_index]
    chosen_emotions.append(target_emotion)
    
    # Reconstruct user input from the beginning
    user_input = original_user_input
    for i in range(len(chosen_emotions)):
        set_start = i * emotions_per_set
        current_set = previous_emotions[set_start:set_start + emotions_per_set]
        chosen = chosen_emotions[i]
        others = [e for e in current_set if e != chosen]
        user_input += f" I feel that '{chosen}' describes my experience better than '{others[0]}' and '{others[1]}'."
    
    # Update session
    session['previous_emotions'] = previous_emotions
    session['chosen_emotions'] = chosen_emotions
    session['user_input'] = user_input
    session.modified = True
    
    # Create sets of previous emotions
    previous_sets = [previous_emotions[i:i+3] for i in range(0, len(previous_emotions), 3)]
    
    # Get new recommendations based on rewound state
    recommended_emotions = find_relevant_emotions(
        user_input=user_input,
        emotion_list=session['emotion_list'],
        previous_emotions=previous_emotions,
        client=client,
        faiss_index=faiss_index
    )
    
    # Append recommended_emotions to previous_emotions
    for emotion in recommended_emotions:
        previous_emotions.append(emotion)
    
    descriptions = get_descriptions(df_embeddings, recommended_emotions + previous_emotions)
    return render_template('results.html',
                            emotions=recommended_emotions,
                            user_input=user_input,
                            previous_sets=previous_sets,
                            chosen_emotions=chosen_emotions,
                            original_user_input=original_user_input,
                            descriptions=descriptions)
    
def handle_skip_emotions(df_embeddings, user_input, session, client, faiss_index):
    original_user_input = session['original_user_input']
    
    # Get previous emotions
    previous_emotions = session['previous_emotions']
    
    # Get the latest recommended emotions
    skipped_emotions = previous_emotions[-3:]
    
    # Append message to user input
    user_input += f" None of the following emotions describe my experience in any way: '{skipped_emotions[0]}', '{skipped_emotions[1]}', '{skipped_emotions[2]}'."
    
    # Update session user_input
    session['user_input'] = user_input
    # Necessary for making session updates stick
    session.modified = True
    
    # Generate new recommended emotions
    recommended_emotions = find_relevant_emotions(
        user_input=user_input,
        emotion_list=session['emotion_list'],
        previous_emotions=previous_emotions,
        client=client,
        faiss_index=faiss_index
    )
    
    # Append recommended emotions to previous_emotions
    previous_emotions.extend(recommended_emotions)
    
    # Update previous sets
    previous_sets = [previous_emotions[i:i+3] for i in range(0, len(previous_emotions)-len(recommended_emotions), 3)]
    
    # Get descriptions
    descriptions = get_descriptions(df_embeddings, previous_emotions)
    
    return render_template('results.html',
                           emotions=recommended_emotions,
                           user_input=user_input,
                           previous_sets=previous_sets,
                           chosen_emotions=session['chosen_emotions'],
                           original_user_input=original_user_input,
                           descriptions=descriptions)
    
def handle_finish(df_embeddings, user_input, session):
    # Get final data
    original_user_input = session['original_user_input']  
    
    if session.get('collection'):
        # Get descriptions without HTML formatting for printing
        plain_descriptions = {
            emotion: df_embeddings.loc[df_embeddings['Emotion'] == emotion, 'Description'].iloc[0]
            for emotion in session['collection']
        }
        # Print the collection
        print_emotion_collection(df_embeddings, original_user_input, session['collection'], plain_descriptions)
        
    latest_emotions = session['previous_emotions'][-3:]
    previous_emotions = session['previous_emotions'][:-3]
    previous_sets = [previous_emotions[i:i+3] for i in range(0, len(previous_emotions), 3)]
    chosen_emotions = session['chosen_emotions']
    descriptions = get_descriptions(df_embeddings, latest_emotions + previous_emotions)
    
    return render_template('results.html', 
                            emotions=latest_emotions,
                            user_input=user_input,
                            previous_sets = previous_sets,
                            chosen_emotions=chosen_emotions,
                            original_user_input=original_user_input,
                            descriptions=descriptions)    
    
    
def handle_update_collection(data, session):
    action = data.get('action')
    emotion = data.get('emotion')
    
    # can prob be removed
    if 'collection' not in session:
        session['collection'] = []
    
    if action == 'add' and emotion not in session['collection']:
        session['collection'].append(emotion)
        session.modified = True
    elif action == 'remove' and emotion in session['collection']:
        session['collection'].remove(emotion)
        session.modified = True
    
    return jsonify({'success': True})