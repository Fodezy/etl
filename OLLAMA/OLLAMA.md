# Max Tokens for llama 3 8B
8192 tokens.

# Max Tokens for Gemma 3 12B and gemini flash 2.0
128K context 

# prompt-gen3.txt
contains most up to date prompt for context models with >8192 tokens

  |
  |
 \|/

# ollama-parse.py

## Random mode:
python OLLAMA/ollama-parser.py -n 3

## Course Code mode:
python OLLAMA/ollama-parser.py -c "CROP*4220"

  |
  |
 \|/

# update_golden_dataset.py

## Merge All Courses 
python OLLAMA/update_golden_dataset.py

## Merge All Courses (exclude specific courses)
python OLLAMA/update_golden_dataset.py --exclude "COURSE1,COURSE2"

## Force Merge All Courses
python OLLAMA/update_golden_dataset.py --force

## Force Merge All Courses (exclude specific courses)
python OLLAMA/update_golden_dataset.py --force --exclude "COURSE1,COURSE2"

# Add Specific Course  
python OLLAMA/update_golden_dataset.py --add "COURSE_CODE_TO_ADD"

# Add Specific Course --force  
python OLLAMA/update_golden_dataset.py --add "COURSE_CODE_TO_FORCE_ADD" --force

## Remove Specific Course 
python OLLAMA/update_golden_dataset.py --remove "COURSE_CODE_TO_REMOVE"


pip install --extra-index-url https://download.pytorch.org/whl/cu128 torch torchvision torchaudio "unsloth[cu121] @ git+https://github.com/unslothai/unsloth.git" bitsandbytes==0.46.0 transformers==4.52.4 accelerate==1.7.0 peft==0.15.2 datasets==3.6.0 trl==0.18.1 xformers==0.0.30

set env to: $env:PYTHONUTF8=1