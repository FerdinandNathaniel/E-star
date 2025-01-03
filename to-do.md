## To-do's

### Bugs
- After 10+ calls, it's increasingly likely there won't be enough options left for the 'recommender' in utils.find_relevant_emotions() to recommend 'far distance' emotiosn, leading to index out of bounds error when trying to retrieve a description from a None value.
- Clicking on 'add to collection' just after clicking on an emotion will not register as the screen refreshes. Due to API call taking time, whilst not blocking any inputs from user, after which it refreshes page with information it had when user originally clicked the big emotion button.

### Short-term
- When pushing the repo online, do a fresh install on new env to see which installs are actually necessary to run the program
- Special characters get printed weirdly (é etc)
- Make users able to change input on the fly
- Make bold text in description be color of brown
- Make both sidebars the same width
- Stop the starting of the model to send print requests
- Fix title of pop-up for printing
- Make it possible to skip suggestions, with a line indicating 'none of these emotions fit well:'
- Make it possible to select multiple emotions at the same time (often requested!!)
- Once user clicks big emotion bubble, disable possibility to click on any other button (or buffer their input). Currently, users click multiple things in the span that it takes the system to generate new items, which get invalidated once it finished creating the new items.
- Let new emotions not lead to refresh of entire page but just addition of new elements on page (or atleast upon refresh go back to bottom of page)
- Proper case handling (no new emotions, etc.)

### Long-term
- Enrich dataset
  - Add example sentences
  - Add extra context
  - More emotions
  - Add field for 'general familiarity' (for recommender system, start 'basic', delve deeper later)
  - Add more modalities (spoken voice for each word by indigenous people, artworks, music, etc.)
- Improve recommender system
  - Add scalars/weights to strengthen/weaken certain candidate recommendations based on various aspects (sentiment, language, ...)
  - Have recommender system start with 'more familiar' / base emotions to allow for easier starting
- Make it possible to explore the words within the system without a personal experience input prompt, and still collect your favourite words you come across.
- Allow users to choose various forms of dataset to use (Include emotional actions or not, only certain types of content, etc.)

### Web deployment
- See if portfolio can be a github pages, and then flask apps to be deployed on railway.app (current preference) or render (have free tiers)
  - more expensive option is to use Webflow, and embed custom code within.
- Gunicorn implementation
