# E*star is an artwork on discovering intercultural language that describes emotion.
# Copyright (C) 2024  Ferdinand Kok

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import numpy as np
import faiss
from flask import render_template, jsonify

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
    
    # newlines can cause problems with accurate embedding
    description = str(description).replace("\n", " ")
    
    return client.embeddings.create(input = description, model = model).data[0].embedding

def get_faiss_index(df_embeddings):
    """Create a Faiss index from the embeddings in the dataframe.

    Args:
        df_embeddings (pandas.core.frame.DataFrame): DataFrame of embeddings and metadata

    Returns:
        faiss.swigfaiss.IndexFlatL2: FAISS index of the embeddings
    """
    
    embedding_dim = len(df_embeddings['Embedding'].iloc[0])
    embedding_matrix = np.array(df_embeddings['Embedding'].tolist()).astype('float32')
    faiss_index = faiss.IndexFlatL2(embedding_dim)
    faiss_index.add(embedding_matrix)
    
    return faiss_index

def find_relevant_emotions(user_input, emotion_list, client, faiss_index, previous_emotions=[]):
    """Find relevant emotions based on user input and previous selections.
    
    Args:
        user_input (str): user input to generate embeddings from
        emotion_list (list): list of emotions to choose from
        client (OpenAI): OpenAI API client
        faiss_index (faiss.swigfaiss.IndexFlatL2): FAISS index of embeddings
        previous_emotions (list, optional): list of previously selected emotions. Defaults to [].

    Returns:
        list: list of recommended emotions
        
    """
    
    # Generate embedding for the user input
    user_input_modified = ('I am looking for NON ENGLISH emotions that best describe my experience. ' +
                           'This is a description of my experience: ' + 
                           user_input + 
                           ' Which emotion do you think best describes my experience?' + 
                           ' I want NON ENGLISH emotions! Only suggest English emotions if there are no other options available.')
    user_embedding = get_embedding(user_input_modified, client)
    user_embedding = np.array(user_embedding, dtype='float32').reshape(1, -1)
    distances, indices = faiss_index.search(user_embedding, len(emotion_list))
    
    # Filter out selected emotions
    recommended_emotions = []
    first_emotion_percentile = int(len(indices[0]) * 0.05)
    second_emotion_percentile = int(len(indices[0]) * 0.1)
    third_emotion_percentile = int(len(indices[0]) * 0.3)
    
    def get_emotion_from_percentile(start, end):
        #print out for debugging
        print(f"Finding emotion from indices {start} to {end} (percentiles {start/len(indices[0]):.2f} to {end/len(indices[0]):.2f})")
        if start >= end or start < 0 or end > len(indices[0]):
            print("Invalid range for indices, returning None")
            return None
        for idx in indices[0][start:end]:
            emotion = emotion_list[idx]
            if emotion not in previous_emotions and emotion not in recommended_emotions:
                return emotion

        # grab a random emotion that is not in previous_emotions or recommended_emotions
        try_num = 20
        for t in range(try_num):
            print(f"finding random emotion, try {t+1}/{try_num}")
            random_emotion = np.random.choice(emotion_list)
            if random_emotion not in previous_emotions and random_emotion not in recommended_emotions:
                return random_emotion
            
        print(f"No valid emotion found")
        return None
    
    recommended_emotions.append(get_emotion_from_percentile(0, first_emotion_percentile))
    recommended_emotions.append(get_emotion_from_percentile(first_emotion_percentile, second_emotion_percentile))
    recommended_emotions.append(get_emotion_from_percentile(second_emotion_percentile, third_emotion_percentile))
    
    if not recommended_emotions:
        # Handle end of list
        return []
    
    return recommended_emotions

def find_relevant_base_emotions():
    """Randomly select one emotion from each base emotion category. Only to be used in first pass.

    Returns:
        list[str]: list of recommended emotions
    """
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
    """Get descriptions of emotions from the embeddings dataframe.

    Args:
        df_embeddings (pandas.core.frame.DataFrame): DataFrame of embeddings and metadata
        emotions (list): list of emotions to get descriptions for

    Returns:
        dict: dictionary of emotion descriptions
    """
    return {emotion: f"<strong>{emotion}</strong> [{df_embeddings.loc[df_embeddings['Emotion'] == emotion, 'Language'].iloc[0]}]<br>{df_embeddings.loc[df_embeddings['Emotion'] == emotion, 'Description'].iloc[0]}"
            for emotion in emotions}


##########################
##### Route handlers #####
##########################

def handle_first_pass(user_input, session, df_embeddings):
    """Handle the first pass of the emotion selection process.

    Args:
        user_input (str): user input of current state
        session (flask.sessions.SecureCookieSession): session object storing user state
        df_embeddings (pandas.core.frame.DataFrame): DataFrame of embeddings and metadata
        
    Returns:
        render_template: render the results.html template with the first pass results
    """
    
    if user_input[-1] != '.': 
        # Ensure user inputted sentence ends with a period
        user_input += '.'
    
    # Initialise session variables, for easy passing between routes/functions
    session['previous_emotions'] = []
    session['chosen_emotions'] = []
    session['original_user_input'] = user_input
    session['user_input'] = user_input
    session['collection'] = []

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

def handle_get_emotions(user_input, chosen_emotion, df_embeddings, session, client, faiss_index, emotion_list):
    """Handle the selection of a new emotion.

    Args:
        user_input (str): user input of current state
        chosen_emotion (str): emotion chosen by the user
        df_embeddings (pandas.core.frame.DataFrame): DataFrame of embeddings and metadata
        session (flask.sessions.SecureCookieSession): session object storing user state
        client (OpenAI): OpenAI API client
        faiss_index (faiss.swigfaiss.IndexFlatL2): FAISS index of embeddings

    Returns:
        render_template: render the results.html template with the updated results
    """
    
    print(f"Session: {session}")
    
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
        emotion_list=emotion_list, 
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
    
def handle_rewind_to_emotion(target_emotion, target_set_index, df_embeddings, session, client, faiss_index, emotion_list):
    """Handle the rewinding to a previous emotion, and corresponding system state.

    Args:
        target_emotion (str): emotion to rewind to
        target_set_index (int): index of the set to rewind to
        df_embeddings (pandas.core.frame.DataFrame): DataFrame of embeddings and metadata
        session (flask.sessions.SecureCookieSession): session object storing user state
        client (OpenAI): OpenAI API client
        faiss_index (faiss.swigfaiss.IndexFlatL2): FAISS index of embeddings

    Returns:
        render_template: render the results.html template with the updated results
    """
    
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
        emotion_list=emotion_list,
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
    
def handle_skip_emotions(df_embeddings, user_input, session, client, faiss_index, emotion_list):
    """Handle the skipping of emotions.

    Args:
        df_embeddings (pandas.core.frame.DataFrame): DataFrame of embeddings and metadata
        user_input (str): user input of current state
        session (flask.sessions.SecureCookieSession): session object storing user state
        client (OpenAI): OpenAI API client
        faiss_index (faiss.swigfaiss.IndexFlatL2): FAISS index of embeddings

    Returns:
        render_template: render the results.html template with the updated results
    """
    
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
        emotion_list=emotion_list,
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
    """Handle the printing of the receipt with emotions from collection.

    Args:
        df_embeddings (pandas.core.frame.DataFrame): DataFrame of embeddings and metadata
        user_input (str): original user input string of user experience
        session (flask.sessions.SecureCookieSession): session object storing user state

    Returns:
        render_template: re-render the results.html template with the current state
    """
    
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
    """Handle the addition or removal of an emotion from the collection.

    Args:
        data (dict): dictionary containing the action and emotion to be added/removed
        session (flask.sessions.SecureCookieSession): session object storing user state

    Returns:
        jsonify: JSON response indicating success
    """
    
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