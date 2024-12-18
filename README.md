# E*star

E*star is an artwork initially made for the Creative AI Track of the NeurIPS 2024 conference held in Vancouver. Within this repository you will find the current state of the system behind the artwork, and any updates it may get into the future. 

**Test out the system via this link**: .......
(For the printing to work you will need a receipt printer that accepts ESC/POS formatted text, set as default printer of your computer, but you can still peruse the system to your heart's content without.)

**Other work of mine**: ferdinandnathaniel.github.io


## Project Goal

E*star has a few goals:

1) Help people discover new words from a variety of languages that describe human emotions. Hopefully in turn also discovering new language to help better understand own lived experiences.
2) Create a public dataset of words that describe emotional experiences, from as many languages as possible, with as rich a description in English as possible, for easy use in research and art. The strength of the dataset will fall and stand on the community to add to it and validate what's already there.
3) Exist as a broader artwork to ask the question: 'How can technology help humanity gain a better understanding of itself, and the world around?'

## Emotions Dataset

The `emotions_dataset.xlsx` contains a curated list of emotions and descriptions from a variety of languages. This dataset acts as the knowledge base for the system whilst in use. We encourage anyone to contribute by reviewing the existing entries, validating the descriptions, and adding new emotions to enrich the dataset. The dataset is kept intentionally in an excel format for easier editing for less technical folk.

If you're not as technically minded, feel free to click into the `data` folder above, then into 'raw', and download the file from there, sending any edits you make to me directly via the contact info at the bottom of this page.

## Overview program

The system is a Python Flask application. At its core is a database with emotions, their descriptions, and embeddings of them both combined. Users submit a textual description of an experience they've had, or are having, which gets stored as `user_input`. The initial `user_input` gets embedded, and distances are calculated for all emotions in the database's embeddings. A recommender system defines which 3 emotions then get shown to the user. From here, the system starts looping, where each choice by the user (an emotion chosen, or none chosen), gets added to the `user_input` by means of extra textual context, after which an embedding of the new `user_input` is used to recalculate embedding distances. 

The idea is that for each subsequent pass, the context of the `user_input` gets richer, leading to a better embedding of the user's intent, and thus more accurate distance metrics to fitting words.

Users can collect words they deem to be well fitting of their experience, and in the end finish by printing out a receipt with their initial description of their experience and the words and descriptions of the emotions they've gathered.

The main components of the system are:
- An embedded emotions dataset (data/processed/embeddings.pkl): contains an easy to load dataset with all emotions and corresponding descriptions and embeddings, gained through putting `data/raw/emotions_dataset.xlsx` through an embedder as can be seen in `data/data_processing.ipynb`. Used directly through `app.py` as database whilst running.
- An embedder: currently OpenAI's text-embedder-large. 
- Flask main file (app.py): contains all logic for building the flask webapp, and the routes to take for each interaction with the webapp. 
- Helper functions (utils.py): contains all helper functions (including logic for flask app routes) the program uses.
- Front-end files (anything in static/ and templates/): the styling and content of all pages the flask app can route towards.
- Printer: a small mobile printer able to use ESC/POS commands. For this installation a 58mm width receipt printer was used. 

## Getting Started

To run the model locally, you can use the Docker image hosted at Docker Hub under `ferdinandnathaniel/e_star`.

You can also fork this repo and run the model as such.

### Prerequisites

These are necessities for running a local version of the app, the online version can be found through my portfolio page (link).

- An up-to-date install of [Docker](https://www.docker.com/get-started) on your machine if you want to use docker to install the system.
- Python 3.11.0 and all packages within requirements.txt if not inclined to use Docker.

- Ensure you have an OpenAI API key (or any other embedder you'd like to use). Set it as an environment variable, being OPENAI_API_KEY.

## License
GNU GENERAL PUBLIC LICENSE - Version 3

See also COPYING.txt within this repository.

## Contact

You may either know me as Ferdinand or Fabian, and I am an AI Expert at the University of Applied Science in Utrecht (HU), specifically helping research(ers) with their data science and AI questions and execution of projects. 

I am also a starting artist interested in using technology to help humans make better sense of the world (and themselves). Love anything to do with art&science, technology&creativity. Always feel free to hit me up for a short conversation.

**Contact me by my work email**: fabian.kok@hu.nl
**Online portfolio**: ferdinandnathaniel.github.io

## Acknowledgments
This work has been made as part of my work within the Data Science Pool (DSP) at the University of Applied Science Utrecht (Hogeschool Utrecht), in The Netherlands, and part of the work done under the Responsible Applied Artificial InTelligence (RAAIT) program. Co-authors and great support being Stefan Leijnen and Marieke Peeters from the Research Group AI (Lectoraat AI) at the Hogeschool Utrecht.