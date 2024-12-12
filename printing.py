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
    
    # Paper
    FEED_LINES = '\x1b\x64'
    FEED_UNITS = '\x1b\x4A'
    FEED_REVERSE = '\x1b\x65'  # Reverse feed
    CUT_PAPER = '\x1d\x56\x41\x00'

def print_receipt(text, options=None):
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
    formatted_text += '\n' + text     # Add an extra newline before the text
    
    # Add line feeds at the end
    if 'feed_lines' in options:
        formatted_text += ESC.FEED_LINES + chr(options.get('feed_lines', 3))
    else:
        formatted_text += '\n\n\n'
    
    # Add extra feed at the end before cutting
    feed_end = options.get('feed_end', 30)  # Default 30 dots
    formatted_text += ESC.FEED_UNITS + chr(feed_end)
    
    # Create a temporary file
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
        
        # Execute the print command
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"Print job sent successfully: {result.stdout}")
        
    except subprocess.CalledProcessError as e:
        print(f"Printing failed: {e}")
        print(f"Error output: {e.stderr}")
    finally:
        # Clean up the temporary file
        os.unlink(temp_filename)

def print_formatted_receipt():
    receipt = (
        ESC.BOLD_ON + ESC.DOUBLE_WIDTH_ON +
        "RECEIPT\n" +
        ESC.NORMAL_SIZE + ESC.BOLD_OFF +
        "-----------------\n" +
        "Regular text line\n" +
        ESC.BOLD_ON +
        "Bold text line\n" +
        ESC.BOLD_OFF +
        ESC.DOUBLE_HEIGHT_ON +
        "Tall text line\n" +
        ESC.NORMAL_SIZE +
        "-----------------\n"
    )
    
    options = {
        'copies': 1,
        'spacing': 24,
        'align': 'center',
        'feed_lines': 4,
        'feed_end': 100  # Increase this value for more feed at the end
    }
    
    print_receipt(receipt, options)

def print_full_receipt():
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
        'feed_end': 50  # Increase this value for more feed at the end
    }
    
    time.sleep(0.5)
    
    print_receipt(receipt, options)

def print_emotion_collection(df_embeddings, original_user_input, emotions, descriptions):
    """Print a receipt containing the collected emotions and their descriptions."""
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
    
    time.sleep(0.5)
    
    print_receipt(receipt, options)

