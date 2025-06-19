# ==============================================================================
# Gemma 3 12B Fine-Tuning Notebook for Google Colab
# ==============================================================================
#
# HOW TO USE THIS SCRIPT IN GOOGLE COLAB:
#
# 1. CREATE A NEW NOTEBOOK & ENABLE GPU
#    - Go to https://colab.research.google.com/ and click "New notebook".
#    - In the menu, go to `Runtime > Change runtime type`.
#    - In the dropdown, select "T4 GPU". This is a powerful GPU available
#      on the free tier of Colab.
#
# 2. UPLOAD YOUR DATASET
#    - On the left side of the Colab interface, click the "Files" icon (folder symbol).
#    - Click the "Upload to session storage" icon (page with an upward arrow).
#    - Select and upload your `Golden_DataSet.jsonl` file.
#
# 3. ADD YOUR HUGGING FACE TOKEN AS A SECRET
#    - On the left side, click the "Secrets" icon (key symbol).
#    - Click "+ New secret".
#    - For the "Name", enter `HF_TOKEN`.
#    - For the "Value", paste your Hugging Face access token.
#    - Make sure the "Notebook access" switch is turned ON for this secret.
#
# 4. RUN THIS SCRIPT
#    - Copy this entire code block into the first (and only) cell of your
#      Colab notebook.
#    - Click the "Play" button on the cell to run it. The script will handle
#      all installations and start the fine-tuning process.
#
# ==============================================================================

# Step 1: Install necessary libraries for Colab
# ------------------------------------------------------------------------------
# Unsloth has a specific build for Colab that is highly optimized.
# We also ensure the other libraries are up-to-date.
!pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
!pip install -U "transformers>=4.41.0" "datasets>=2.18.0" "accelerate" "peft" "trl"


# Step 2: Import all required modules
# ------------------------------------------------------------------------------
from unsloth import FastLanguageModel
import torch
import os
import json
from datasets import load_dataset
from transformers import AutoTokenizer
from transformers.training_args import TrainingArguments
from trl import SFTTrainer
from google.colab import userdata # For securely accessing the HF_TOKEN secret

# Step 3: Authenticate with Hugging Face using the Colab secret
# ------------------------------------------------------------------------------
from huggingface_hub import login
os.environ["WANDB_DISABLED"] = "true"
HF_TOKEN = userdata.get('HF_TOKEN')
login(token=HF_TOKEN)


# ==============================================================================
# Configuration
# ==============================================================================

# Model and dataset names
base_model_name = "unsloth/llama-3-8b-Instruct-bnb-4bit"

# base_model_name = "unsloth/gemma-3-12b-it-bnb-4bit"
dataset_name = "Golden_DataSet.jsonl" # This file should be uploaded to your session

# Name for your fine-tuned model adapter
new_model_name = "llama-3-12b-prerequisite-parser-unsloth"
# new_model_name = "gemma-3-12b-prerequisite-parser-unsloth"

# ==============================================================================
# Data Loading and Preparation
# ==============================================================================

# Load the dataset from the uploaded .jsonl file
dataset = load_dataset("json", data_files=dataset_name, split="train")

# Define the prompt creation function
def create_prompt(record):
    system_prompt = (
        "You are an advanced NLP engine trained to accurately parse university course "
        "prerequisite strings into structured JSON. Your response MUST be only the valid "
        "JSON object and must strictly adhere to the provided schema."
    )
    input_prompt = f"### Input:\n\"{record['raw_requisite']}\""
    output_prompt = f"### Output:\n{json.dumps(record['prerequisites'], separators=(',', ':'))}"
    
    # We will format our data into the instruction-following format.
    return {
        "text": f"<s>[INST] {system_prompt}\n\n{input_prompt} [/INST] {output_prompt}</s>"
    }

# Apply the formatting function to the dataset
formatted_dataset = dataset.map(create_prompt)

# ==============================================================================
# Model and Tokenizer Loading with Unsloth
# ==============================================================================

max_seq_length = 2048 # Choose a sequence length that fits your data and VRAM

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = base_model_name,
    max_seq_length = max_seq_length,
    dtype = None, # Let Unsloth auto-detect the best dtype
    load_in_4bit = True,
)

# ==============================================================================
# LoRA (Low-Rank Adaptation) Configuration
# ==============================================================================

model = FastLanguageModel.get_peft_model(
    model,
    r = 16, 
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 32,
    lora_dropout = 0.05,
    bias = "none",
    use_gradient_checkpointing = True,
    random_state = 42,
)

# ==============================================================================
# Training Configuration and Execution
# ==============================================================================

trainer = SFTTrainer(
    model = model,
    train_dataset = formatted_dataset,
    tokenizer = tokenizer,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    dataset_num_proc = 2,
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 10,
        num_train_epochs = 2,
        learning_rate = 2e-4,
        fp16 = not torch.cuda.is_bf16_supported(),
        bf16 = torch.cuda.is_bf16_supported(),
        logging_steps = 10,
        optim = "adamw_8bit",
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 42,
        output_dir = "outputs",
    ),
)

# Start the fine-tuning process
print("Starting Unsloth-powered fine-tuning on Google Colab...")
trainer.train()
print("Fine-tuning completed successfully!")

# ==============================================================================
# Save the Final Model Adapter
# ==============================================================================

trainer.save_model(new_model_name)
print(f"Model adapter saved to '{new_model_name}'")

# You can now download the saved model folder from the Colab file browser
# by right-clicking the folder and selecting "Download".
