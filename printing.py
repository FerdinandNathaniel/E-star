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

import subprocess
import tempfile
import os
import time

class ESC:
    # Printer initialization
    INIT = '\x1b\x40'
    RESET = '\x1b\x3F\x0A'
    
    # Line spacing
    LINE_SPACING_DEFAULT = '\x1b\x32'
    LINE_SPACING_SET = '\x1b\x33'
    
    # Text formatting
    ALIGN_LEFT = '\x1b\x61\x00'
    ALIGN_CENTER = '\x1b\x61\x01'
    ALIGN_RIGHT = '\x1b\x61\x02'
    
    BOLD_ON = '\x1b\x45\x01'
    BOLD_OFF = '\x1b\x45\x00'
    
    DOUBLE_HEIGHT_ON = '\x1b\x21\x10'
    DOUBLE_WIDTH_ON = '\x1b\x21\x20'
    NORMAL_SIZE = '\x1b\x21\x00'
    
    # Paper handling
    FEED_LINES = '\x1b\x64'
    FEED_UNITS = '\x1b\x4A'
    FEED_REVERSE = '\x1b\x65'
    CUT_PAPER = '\x1d\x56\x41\x00'  # if printer has a cutter

def print_receipt(text, options=None):
    """Prints a receipt with the given text and options. Uses the system's default printer. 
    Made for ESC/POS printers, on MacOS and Linux (unsure about Windows support).
    
    Options:
    - spacing: line spacing in dots
    - align: text alignment ('left', 'center', 'right')
    - copies: number of copies to print (default 1)
    - feed_lines: number of lines to feed after the text (default 3)
    - feed_end: number of dots to feed at the end before cutting

    Args:
        text (str): text to print on the receipt
        options (dict, optional): dictionary containing printing options. Defaults to None.
    """ 
    
    if options is None:
        options = {}
    
    # Create a robust initialization sequence
    formatted_text = (
        ESC.INIT +                    # Initialize printer
        ESC.RESET +                   # Reset printer
        '\n' * 2 +                    # Add some newlines
        ESC.FEED_UNITS + chr(120) +   # Feed forward 120 dots
        ESC.FEED_REVERSE + chr(60) +  # Feed backward 60 dots
        ESC.INIT                      # Initialize again
    )
    
    # Set line spacing
    if 'spacing' in options:
        formatted_text += ESC.LINE_SPACING_SET + chr(options.get('spacing', 24))
    else:
        formatted_text += ESC.LINE_SPACING_DEFAULT
    
    # Set alignment
    if 'align' in options:
        if options['align'] == 'center':
            formatted_text += ESC.ALIGN_CENTER
        elif options['align'] == 'right':
            formatted_text += ESC.ALIGN_RIGHT
        else:
            formatted_text += ESC.ALIGN_LEFT
    
    # Add the main text
    formatted_text += '\n' + text
    
    # Add line feeds at the end
    if 'feed_lines' in options:
        formatted_text += ESC.FEED_LINES + chr(options.get('feed_lines', 3))
    else:
        formatted_text += '\n\n\n'
    
    # Add extra feed at the end before (manual) cutting
    feed_end = options.get('feed_end', 30)  # Default 30 dots
    formatted_text += ESC.FEED_UNITS + chr(feed_end)
    
    # Create a temporary file for printing
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write(formatted_text)
        temp_filename = f.name
    
    try:
        cmd = ['lp', '-o', 'raw']
        
        # Number of copies
        if 'copies' in options:
            cmd.extend(['-n', str(options['copies'])])
        
        # Add filename at the end
        cmd.append(temp_filename)
        
        try:
        # Execute the print command
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            # Add timeout to avoid printer starting before the text is fully passed
            time.sleep(0.2)
            
            print(f"Print job sent successfully: {result.stdout}")
        
        except FileNotFoundError as e:
            print(f"Printing failed: {e}")
            print("Likely no printer configured on this system.")
        
    except subprocess.CalledProcessError as e:
        print(f"Printing failed: {e}")
        print(f"Error output: {e.stderr}")
    finally:
        # Clean up the temporary file
        os.unlink(temp_filename)

def print_full_receipt():
    """
    Print an example receipt with a full set of options.
    """
    
    receipt = (
        "\n\n\n\n\n" +
        ESC.ALIGN_CENTER +
        "Testing receipt\n" +
        "Leven is mooi\n" +
        "Life is life\n\n" +
        ESC.ALIGN_LEFT +
        "Order #: 1234\n" +
        "Date: today\n" +
        "-----------------\n" +
        "Items:\n" +
        "1x Emotions      $10.00\n" +
        "2x Tech stuff    $30.00\n" +
        "-----------------\n" +
        ESC.ALIGN_RIGHT +
        "Total: $40.00\n"
    )

    options = {
        'copies': 1,
        'spacing': 24,
        'feed_lines': 4,
        'feed_end': 50
        # 'align': 'center' # useless here since ESC.ALIGN_CENTER is already set
    }
    
    # Add timeout to avoid printer starting before the text is fully passed
    time.sleep(0.2)
    
    print_receipt(receipt, options)

def print_emotion_collection(df_embeddings, original_user_input, emotions, descriptions):
    """
    Print a receipt containing the collected emotions and their descriptions.
    
    Args:
    df_embeddings (Pandas.DataFrame): DataFrame containing embeddings and metadata
    original_user_input (str): original user input string
    emotions (list): list of emotions to print
    descriptions (dict): dictionary of descriptions for each emotion
    """
    
    receipt = (
        ESC.INIT +
        ESC.ALIGN_CENTER +
        "-----------------\n\n\n" +
        f"'{original_user_input}'\n\n\n" +
        "-----------------\n\n" +
        ESC.ALIGN_LEFT
    )
    
    for emotion in emotions:
        language = df_embeddings.loc[df_embeddings['Emotion'] == emotion, 'Language'].iloc[0]
        receipt += (
            ESC.BOLD_ON +
            f"{emotion} [{language}]\n" +
            ESC.BOLD_OFF +
            f"{descriptions[emotion]}\n\n"
        )
    
    receipt += "-----------------\n"
    
    options = {
        'copies': 1,
        'spacing': 24,
        'align': 'left',
        'feed_lines': 4,
        'feed_end': 50
    }
    
    # Add timeout to avoid printer starting before the text is fully passed
    time.sleep(0.2)
    
    print_receipt(receipt, options)

