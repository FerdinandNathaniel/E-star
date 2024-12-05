import os
import time
from openai import OpenAI
import pandas as pd
import numpy as np
import faiss
from flask import Flask, render_template, request, redirect, url_for
from flask_caching import Cache

import utils as utils

app = Flask(__name__)

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

# For storing previous emotions recommended
# (Somehow this needs to be a cache but others not??)
cache = Cache(app, config={
    'CACHE_TYPE': 'simple'
})

@app.route('/E*star', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/E*star', methods=['POST'])
def first_pass():
    
    # Get user_input
    user_input = request.form.get('user_input')
    
    # Initialise cache
    cache.set('previous_emotions', [])
    cache.set('chosen_emotions', [])
    cache.set('original_user_input', user_input)

    # Get recommended_emotions
    recommended_emotions = utils.find_relevant_emotions(
        user_input=user_input, 
        emotion_list=emotion_list,
        openai_client=client, 
        faiss_index=faiss_index
    )
    
    # Append recommended_emotions to previous_emotions
    previous_emotions = cache.get('previous_emotions')
    for emotion in recommended_emotions:
        previous_emotions.append(emotion)
    cache.set('previous_emotions', previous_emotions)
    
    print(f"User input: {user_input}\nRecommended emotions: {recommended_emotions}\nPrevious emotions: {previous_emotions}")

    return render_template('results.html', emotions=recommended_emotions, user_input=user_input, current_prompt=user_input, original_user_input=user_input)


@app.route('/E*star', methods=['POST'])
def get_emotions():
    
    # Get user_input
    original_user_input = cache.get('original_user_input')
    user_input = request.form.get('user_input')
    
    # Get previous emotions
    previous_emotions = cache.get('previous_emotions')
    
    # Get chosen_emotion and add it to list of chosen emotions
    # Keeping track needed (?) to show the path through the chosen emotions
    chosen_emotions = cache.get('chosen_emotions')
    chosen_emotion = request.form.get('chosen_emotion')
    # Not the best way to tackle it.....
    if chosen_emotion:
        print('In chosen_emotion loop')
        chosen_emotions.append(chosen_emotion)
    cache.set('chosen_emotions', chosen_emotions)
    
    # Find out the other emotions
    if chosen_emotion:
        other_emotions = cache.get('previous_emotions')[-3:]
        other_emotions.remove(chosen_emotion)
    
    # If not in the first loop, append chosen emotion and other emotions to user input
    if chosen_emotion:
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
    cache.set('previous_emotions', previous_emotions)
    
    print(f"User input: {user_input}\nChosen emotion: {chosen_emotion}\nRecommended emotions: {recommended_emotions}\nPrevious emotions: {previous_emotions}")
    
    # If no new emotions, inform the user
    if not recommended_emotions:
        return render_template('results.html', emotions=[], message="No new emotions found.", user_input=user_input, recommended_emotions=recommended_emotions, previous_emotions=previous_emotions, chosen_emotion=chosen_emotion, current_prompt=user_input)

    return render_template('results.html', emotions=recommended_emotions, user_input=user_input, chosen_emotion=chosen_emotion, original_user_input=original_user_input)

@app.route('/finish', methods=['POST'])
def finish():
    # Get final data
    user_input = request.form.get('user_input')
    selected_emotions = request.form.get('selected_emotions', '').split(',')
    return render_template('results.html', emotions=[], message="Process finished.", user_input=user_input, selected_emotions=selected_emotions, previous_emotions=[], chosen_emotion=None, current_prompt=user_input)

if __name__ == '__main__':
    app.run(debug=True)
