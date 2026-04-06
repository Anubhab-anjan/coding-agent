import gradio as gr
from peft import PeftModel, PeftConfig
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

LORA_MODEL = "anubhabanjan1/anubhab-coding-agent"

print("Loading config...")
config = PeftConfig.from_pretrained(LORA_MODEL)
base_model_id = config.base_model_name_or_path
print(f"Base model: {base_model_id}")

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(LORA_MODEL)

print("Loading base model...")
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_id,
    dtype=torch.float16,
    device_map="auto",
)

print("Applying LoRA...")
model = PeftModel.from_pretrained(base_model, LORA_MODEL)
model = model.merge_and_unload()
print("Model ready!")

def ask_agent(user_message, history):
    messages = [
        {
            "role": "system",
            "content": "You are an expert coding agent. When given a user request, respond with:\n1. A step-by-step plan\n2. Complete working code files\nAlways output production-ready code."
        },
        {"role": "user", "content": user_message}
    ]

    # ← fix: encode returns a dict, get input_ids tensor directly
    encoded = tokenizer.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_tensors="pt",
        return_dict=True,
    )
    input_ids = encoded["input_ids"].to(model.device)

    outputs = model.generate(
        input_ids=input_ids,
        max_new_tokens=1024,
        temperature=0.3,
        do_sample=True,
        top_p=0.9,
    )
    return tokenizer.decode(
        outputs[0][input_ids.shape[1]:],
        skip_special_tokens=True
    )

gr.ChatInterface(
    fn=ask_agent,
    title="My Coding Agent",
    description="Tell me what to build and I will give you a plan + code!",
    examples=["make a todo app", "build a login page", "create a REST API"],
).launch(ssr_mode=False)
