# ==============================================================================
# Google Colab Script to MERGE your LoRA Adapter into the Base Model
# (uses PEFT’s merge_and_unload instead of save_pretrained_merged)
# ==============================================================================
#
# HOW TO USE:
# 1. New notebook → Runtime > Change runtime type → GPU (e.g. T4).
# 2. Upload your extracted adapter folder (must directly contain adapter_config.json)
#    anywhere under `/content/`.
# 3. Add a Colab secret named HF_TOKEN with your Hugging Face token.
# 4. Paste this entire block into one cell and run.
#
# When done, you’ll find a folder `/content/llama-3-8b-prerequisite-parser-merged/`
# containing the merged 16-bit weights and tokenizer. Zip/download as needed.

# Step 1: Install / upgrade dependencies
!pip install --upgrade peft trl
!pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
!pip install -U transformers accelerate bitsandbytes

# Step 2: Imports & setup
import os, gc, torch, glob
from unsloth import FastLanguageModel
from peft import PeftConfig, PeftModel
from huggingface_hub import login
from google.colab import userdata

os.environ["WANDB_DISABLED"] = "true"  # disable WandB

# Step 3: Hugging Face auth
HF_TOKEN = userdata.get("HF_TOKEN")
if HF_TOKEN:
    login(token=HF_TOKEN)
    print("✅ Logged into Hugging Face Hub")
else:
    print("⚠️ HF_TOKEN not found; you may hit download limits")

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------
base_model_name = "unsloth/llama-3-8b-Instruct-bnb-4bit"
merged_folder   = "llama-3-8b-prerequisite-parser-merged"
max_seq_length  = 1024

# Auto-find adapter root by locating adapter_config.json under /content
print("🔍 Searching for adapter_config.json under /content …")
matches = glob.glob("/content/**/adapter_config.json", recursive=True)
if not matches:
    raise FileNotFoundError("Could not find adapter_config.json under /content/")
adapter_root = os.path.dirname(matches[0])
print(f"✅ Found adapter folder: {adapter_root}")

# Step 4: Load the base model in 4-bit
print(f"\n⏳ Clearing GPU & loading base model: {base_model_name}")
gc.collect(); torch.cuda.empty_cache()
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name     = base_model_name,
    max_seq_length = max_seq_length,
    dtype          = None,   # auto-detect bfloat16 if supported
    load_in_4bit   = True    # quantized
)
print("✅ Base model loaded.")

# Step 5: Wrap with PEFT & load your LoRA adapter
print(f"\n⏳ Applying LoRA adapter from: {adapter_root}")
peft_config = PeftConfig.from_pretrained(adapter_root, local_files_only=True)
peft_model  = PeftModel.from_pretrained(
    model,
    adapter_root,
    peft_config      = peft_config,
    local_files_only = True
)
print("✅ LoRA adapter applied.")

# Step 6: Merge LoRA into the base weights and unload the adapter
print(f"\n⏳ Merging LoRA weights into base model …")
merged_model = peft_model.merge_and_unload()  # returns a standard HF model with merged weights

# Step 7: Save merged model + tokenizer
print(f"\n⏳ Saving merged model to /content/{merged_folder} …")
os.makedirs(merged_folder, exist_ok=True)
merged_model.save_pretrained(merged_folder)
tokenizer.save_pretrained(merged_folder)
print(f"✅ Merged model saved in /content/{merged_folder}")

# Cleanup
del peft_model, merged_model, tokenizer
gc.collect(); torch.cuda.empty_cache()
