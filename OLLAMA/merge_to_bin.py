# merge_to_bin.py
import os, torch
from unsloth import FastLanguageModel
from unsloth_zoo.saving_utils import merge_and_get_checkpoint

BASE="unsloth/llama-3-8b-Instruct-bnb-4bit"
ADAPTER="D:/FineTuned_Models/content/llama-3-8b-prerequisite-parser-unsloth"
OUT="D:/Merged_Models/llama-3-8b-merged-bin"

os.makedirs(OUT, exist_ok=True)
model, tok = FastLanguageModel.from_pretrained(BASE, load_in_4bit=False, dtype="float16", max_seq_length=1024)
model = FastLanguageModel.get_peft_model(model, r=16, target_modules=[...], lora_alpha=32, lora_dropout=0, bias="none", use_gradient_checkpointing=True)
model.load_adapter(ADAPTER, adapter_name="fine_tuned_adapter")
sd = merge_and_get_checkpoint(model, "fine_tuned_adapter")
torch.save(sd, os.path.join(OUT, "pytorch_model.bin"))
tok.save_pretrained(OUT)
