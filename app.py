import os
import time
from openai import OpenAI
import pandas as pd
import numpy as np
import faiss
from flask import Flask, render_template, request, redirect, url_for, session
from flask_caching import Cache

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

# TO-DO: set number of emotions to show
# num_emotions = 3

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
    
    print(f"User input: {user_input}\nRecommended emotions: {recommended_emotions}\nPrevious emotions: {previous_emotions}")

    return render_template('results.html', 
                           emotions=recommended_emotions, 
                           user_input=user_input, 
                           previous_sets=[],
                           current_prompt=user_input, 
                           original_user_input=user_input)


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
        return render_template('results.html', 
                                emotions=recommended_emotions, 
                                message="No new emotions found",
                                user_input=user_input, 
                                previous_sets = previous_sets,
                                chosen_emotion=chosen_emotion, 
                                original_user_input=original_user_input)

    return render_template('results.html', 
                           emotions=recommended_emotions, 
                           user_input=user_input, 
                           previous_sets = previous_sets,
                           chosen_emotion=chosen_emotion, 
                           original_user_input=original_user_input)

@app.route('/finish', methods=['POST'])
def finish():
    # Get final data
    user_input = request.form.get('user_input')
    selected_emotions = request.form.get('selected_emotions', '').split(',')
    return render_template('results.html', emotions=[], message="Process finished.", user_input=user_input, selected_emotions=selected_emotions, previous_emotions=[], chosen_emotion=None, current_prompt=user_input)

if __name__ == '__main__':
    app.run(debug=True)
