

input_file = "Data/Raw/The Book of Human Emotions.txt"
max_lines_per_chunk = 1000


def split_text_file(input_file, max_lines_per_chunk):
    chunks = []
    current_chunk = []
    current_lines = 0
    
    with open(input_file, 'r', encoding='utf-8') as file:
        text = file.read()
        paragraphs = text.split('\n\n')
    
    i = 0
    while i < len(paragraphs):
        paragraph = paragraphs[i]
        paragraph_lines = len(paragraph.split('\n'))
        words_in_paragraph = len(paragraph.split())
        
        # Check if next paragraph exists and is a single word
        next_is_single_word = False
        if i + 1 < len(paragraphs):
            next_paragraph = paragraphs[i + 1]
            if len(next_paragraph.split()) == 1:
                next_is_single_word = True
                
        # If adding this paragraph would exceed the limit and we have content
        if current_lines + paragraph_lines > max_lines_per_chunk and current_chunk:
            # Don't split if current paragraph is a single word
            if words_in_paragraph == 1 or next_is_single_word:
                # Add current chunk to chunks list and start new one
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [paragraph]
                current_lines = paragraph_lines
            else:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [paragraph]
                current_lines = paragraph_lines
        else:
            current_chunk.append(paragraph)
            current_lines += paragraph_lines
        
        i += 1
    
    # Add the last chunk if it exists
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    # Write chunks to separate files
    for i, chunk in enumerate(chunks):
        output_file = f"{input_file.rsplit('.', 1)[0]}_part{i+1}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(chunk)
    
    return len(chunks)

# Example usage:
# file_path = "your_text_file.txt"
# num_chunks = split_text_file(file_path, 50)  # 50 lines per chunk

print(f"Splitting {input_file} into chunks of {max_lines_per_chunk} lines.")
split_text_file(input_file, max_lines_per_chunk)
print("Finished.")