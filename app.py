import os
import time
from openai import OpenAI
import pandas as pd
import numpy as np
import faiss
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

import utils as utils

app = Flask(__name__)
app.secret_key = 'oooooooohsoseeeeecreeeeeeeet'

# Set up OpenAI API access
api_key = os.environ.get('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

# Choose dataset to use, do not put file ending at the end
dataset_embeddings = "embeddings_onlyLLM"

# Load data
df_embeddings = pd.read_pickle('Data/Processed/' + dataset_embeddings + '.pkl')

# Prepare FAISS index
faiss_index = utils.get_faiss_index(df_embeddings)
emotion_list = df_embeddings['Emotion'].tolist()

def get_descriptions(emotions):
    return {emotion: f"<strong>{emotion}</strong><br>{df_embeddings.loc[df_embeddings['Emotion'] == emotion, 'Description'].iloc[0]}"
            for emotion in emotions}

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/starting', methods=['POST'])
def first_pass():
    
    # Get user_input
    user_input = request.form.get('user_input')
    if user_input[-1] != '.': 
        # Ensure user inputted sentence ends with a period
        user_input += '.'
    
    # Initialise session variables
    session['previous_emotions'] = []
    session['chosen_emotions'] = []
    session['original_user_input'] = user_input
    session['user_input'] = user_input
    session['collection'] = []

    # Get recommended_emotions
    recommended_emotions = utils.find_relevant_emotions(
        user_input=user_input, 
        emotion_list=emotion_list,
        openai_client=client, 
        faiss_index=faiss_index
    )
    
    # Append recommended_emotions to previous_emotions
    previous_emotions = session['previous_emotions']
    for emotion in recommended_emotions:
        previous_emotions.append(emotion)
    
    descriptions = get_descriptions(recommended_emotions)
    return render_template('results.html', 
                           emotions=recommended_emotions, 
                           user_input=user_input, 
                           previous_sets=[],
                           current_prompt=user_input, 
                           original_user_input=user_input,
                           descriptions=descriptions)


@app.route('/wandering', methods=['POST'])
def get_emotions():
    
    # Get user_input
    original_user_input = session['original_user_input']
    user_input = request.form.get('user_input')
    
    # Get previous emotions
    previous_emotions = session['previous_emotions']
    
    # Create sets of previous emotions (groups of 3)
    previous_sets = [previous_emotions[i:i+3] for i in range(0, len(previous_emotions), 3)]
    
    # Get chosen_emotion and add it to list of chosen emotions
    chosen_emotions = session['chosen_emotions']
    chosen_emotion = request.form.get('chosen_emotion')
    chosen_emotions.append(chosen_emotion)
    
    # Find out the other emotions
    other_emotions = previous_emotions[-3:].copy()
    other_emotions.remove(chosen_emotion)
    
    # Append chosen emotion and other emotions to user input
    user_input += f" I feel that '{chosen_emotion}' describes my experience better than '{other_emotions[0]}' and '{other_emotions[1]}'."
    
    # Get recommended_emotions
    recommended_emotions = utils.find_relevant_emotions(
        user_input=user_input, 
        emotion_list=emotion_list, 
        previous_emotions=previous_emotions, 
        openai_client=client, 
        faiss_index=faiss_index
    )
    
    # Append recommended_emotions to previous_emotions
    for emotion in recommended_emotions:
        previous_emotions.append(emotion)
    
    print(f"User input: {user_input}\nChosen emotion: {chosen_emotion}\nRecommended emotions: {recommended_emotions}\nPrevious emotions: {previous_emotions}")
    
    # Session has been modified at this point
    session.modified = True
    
    # If no new emotions, inform the user
    if not recommended_emotions:
        descriptions = get_descriptions(recommended_emotions + previous_emotions)
        return render_template('results.html', 
                                emotions=recommended_emotions, 
                                message="No new emotions found",
                                user_input=user_input, 
                                previous_sets = previous_sets,
                                chosen_emotion=chosen_emotion, 
                                original_user_input=original_user_input,
                                descriptions=descriptions)

    descriptions = get_descriptions(recommended_emotions + previous_emotions)
    return render_template('results.html', 
                           emotions=recommended_emotions, 
                           user_input=user_input, 
                           previous_sets = previous_sets,
                           chosen_emotion=chosen_emotion, 
                           chosen_emotions=chosen_emotions,
                           original_user_input=original_user_input,
                           descriptions=descriptions)

@app.route('/rewind', methods=['POST'])
def rewind_to_emotion():
    # Get target emotion and set index
    target_emotion = request.form.get('target_emotion')
    target_set_index = int(request.form.get('target_set_index'))
    
    # Get current state
    previous_emotions = session['previous_emotions']
    chosen_emotions = session['chosen_emotions']
    original_user_input = session['original_user_input']
    
    # Calculate where to rewind to
    emotions_per_set = 3
    target_index = (target_set_index * emotions_per_set) + previous_emotions[target_set_index * emotions_per_set:
                                                                             (target_set_index + 1) * emotions_per_set].index(target_emotion)
    
    # Rewind the states
    # If emotion on first row is clicked, special case scenario......
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
    recommended_emotions = utils.find_relevant_emotions(
        user_input=user_input,
        emotion_list=emotion_list,
        previous_emotions=previous_emotions,
        openai_client=client,
        faiss_index=faiss_index
    )
    
    # Append recommended_emotions to previous_emotions
    for emotion in recommended_emotions:
        previous_emotions.append(emotion)
    
    descriptions = get_descriptions(recommended_emotions + previous_emotions)
    return render_template('results.html',
                            emotions=recommended_emotions,
                            user_input=user_input,
                            previous_sets=previous_sets,
                            chosen_emotions=chosen_emotions,
                            original_user_input=original_user_input,
                            descriptions=descriptions)

@app.route('/finish', methods=['POST'])
def finish():
    # Get final data
    user_input = request.form.get('user_input')
    selected_emotions = request.form.get('selected_emotions', '').split(',')
    return render_template('results.html', emotions=[], message="Process finished.", user_input=user_input, selected_emotions=selected_emotions, previous_emotions=[], chosen_emotion=None, current_prompt=user_input)

@app.route('/update_collection', methods=['POST'])
def update_collection():
    data = request.get_json()
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

if __name__ == '__main__':
    app.run(debug=True)
