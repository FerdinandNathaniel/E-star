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

import os

import pandas as pd

from openai import OpenAI
from flask import Flask, render_template, request, session

import utils as utils

app = Flask(__name__)
# Has to be set for session variables, but 'unnecessary' for singular demo purposes
app.secret_key = 'oooooooohsoseeeeecreeeeeeeet'

# Set up OpenAI API access
api_key = os.environ.get('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

# Choose dataset to use, do not put file ending at the end
# Allows for easy 'hotswapping' of used databases
dataset_embeddings = "embeddings"

# Load data
df_embeddings = pd.read_pickle('data/processed/' + dataset_embeddings + '.pkl')

# Prepare FAISS index
faiss_index = utils.get_faiss_index(df_embeddings)
emotion_list = df_embeddings['Emotion'].tolist()

##### Landing page #####
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

##### First pass #####
@app.route('/starting', methods=['POST'])
def first_pass():
    
    user_input = request.form.get('user_input')

    return utils.handle_first_pass(user_input, session, df_embeddings, emotion_list)
    
##### Choose a new emotion #####
@app.route('/wandering', methods=['POST'])
def get_emotions():
    
    user_input = request.form.get('user_input')
    chosen_emotion = request.form.get('chosen_emotion')
    
    return utils.handle_get_emotions(user_input, chosen_emotion, df_embeddings, session, client, faiss_index)

##### Choose an old emotion #####
@app.route('/rewind', methods=['POST'])
def rewind_to_emotion():
    
    target_emotion = request.form.get('target_emotion')
    target_set_index = int(request.form.get('target_set_index'))

    return utils.handle_rewind_to_emotion(target_emotion, target_set_index, df_embeddings, session, client, faiss_index)

##### Choose no emotions #####
@app.route('/skip', methods=['POST'])
def skip_emotions():
    
    user_input = request.form.get('user_input')
    
    return utils.handle_skip_emotions(df_embeddings, user_input, session, client, faiss_index)

##### Print out receipt #####
@app.route('/finish', methods=['POST'])
def finish():
    
    # Ensure that refresh of page after printing keeps current user's input string
    user_input = request.form.get('user_input')
    
    return utils.handle_finish(df_embeddings, user_input, session)

##### Add/remove emotion to/from collection #####
@app.route('/update_collection', methods=['POST'])
def update_collection():
    
    # Get user action (add/remove) and target emotion
    data = request.get_json()
    
    return utils.handle_update_collection(data, session)

# Run main system
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
