# To download the bloom and whisper model locally

# Modules for Bloom
from transformers import AutoModelForCausalLM, AutoTokenizer
# Whisper libraries
import torch
import whisper

# Loading Whisper and Bloom models to be more efficient while executing our app
# Loading Whisper model. It will be stored by default in ~/.cache/whisper
model = whisper.load_model(name="small",download_root='C:/Users/manum/.cache/whispersmall')
# # Load Model and Tokenizer
# model_bloom = AutoModelForCausalLM.from_pretrained("bigscience/bloom-560m", use_cache=True)
# tokenizer = AutoTokenizer.from_pretrained("bigscience/bloom-560m")
# # Save the model in the desired directory
# model_bloom.save_pretrained(save_directory=r"C:\Users\manum\.cache\huggingface\hub\models-560m-try", is_main_process=True)
# tokenizer.save_pretrained(save_directory=r"C:\Users\manum\.cache\huggingface\hub\models-560m-try", is_main_process=True)