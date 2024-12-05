import os
import openai
import csv
import time
from pathlib import Path
import logging
from typing import Tuple, Optional
import re
from openai import OpenAI

# Big problem: chunk sizes/paragraphs too small, regex needs a look over,
# currently get multiple rows per emotion with large paragraph

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmotionProcessor:
    def __init__(self, api_key: str):
        """Initialize the processor with API key and set up OpenAI client."""
        self.client = OpenAI(api_key=api_key)
        self.processed_count = 0

    def read_emotion_descriptions(self, file_path: str) -> list[str]:
        """
        Read and split the input file into emotion descriptions.
        Uses regex to identify complete description blocks.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                # Split on double newlines or other clear section markers
                # Needs to be SO MUCH better, currently cuts up mid description
                descriptions = re.split(r'\n\n+', content)
                return [desc.strip() for desc in descriptions if desc.strip()]
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            raise

    def process_emotion_description(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """Process text using OpenAI API with improved error handling and validation."""
        prompt = f"""
        Analyze this emotion description and provide:
        1. The exact name of the emotion (single word or short phrase)
        2. A concise summary (max 50 words) that preserves key context and information

        Text: {text}

        Format response exactly as:
        Emotion: [emotion name]
        Description: [concise summary]
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-2024-11-20",
                messages=[
                    {"role": "system", "content": "You are a precise assistant that extracts and summarizes"
                     + " emotion descriptions while maintaining their essential meaning."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent outputs
                max_tokens=150
            )
            
            response_text = response.choices[0].message.content
            
            # Use regex for more robust extraction
            emotion_match = re.search(r'Emotion:\s*(.+)', response_text)
            description_match = re.search(r'Description:\s*(.+)', response_text)
            
            if not emotion_match or not description_match:
                logger.warning(f"Invalid API response format: {response_text}")
                return None, None
                
            return emotion_match.group(1).strip(), description_match.group(1).strip()

        except Exception as e:
            logger.error(f"API Error: {e}")
            return None, None

    def process_file(self, input_file: str, output_file: str, batch_size: int = 10):
        """Process the entire file with batching and progress tracking."""
        try:
            descriptions = self.read_emotion_descriptions(input_file)
            total_descriptions = len(descriptions)
            
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Emotion", "Description", "Source"])
                
                for i in range(0, total_descriptions, batch_size):
                    batch = descriptions[i:i + batch_size]
                    
                    for description in batch:
                        emotion, summary = self.process_emotion_description(description)
                        
                        if emotion and summary:
                            writer.writerow([emotion, summary, "The Book of Human Emotions"])
                            self.processed_count += 1
                            logger.info(f"Processed {self.processed_count}/{total_descriptions} descriptions")
                        
                        # Rate limiting
                        time.sleep(1)
                    
                    # Save progress after each batch
                    csvfile.flush()
                    
            logger.info(f"Processing complete. {self.processed_count} descriptions processed.")
            
        except Exception as e:
            logger.error(f"Error during file processing: {e}")
            raise

def main():
    # Configuration
    INPUT_FILE = "Data/Raw/The Book of Human Emotions.txt"
    OUTPUT_FILE = "The Book of Human Emotions.csv"
    API_KEY = os.environ["OPENAI_API_KEY"]
    
    try:
        processor = EmotionProcessor(API_KEY)
        processor.process_file(INPUT_FILE, OUTPUT_FILE)
    except Exception as e:
        logger.error(f"Process failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()
