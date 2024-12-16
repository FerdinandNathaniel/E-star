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
