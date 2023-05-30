import torch

import importlib

import yaml
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler


def load_model(model_id):
    with open("models.yaml", "r") as f:
        config = yaml.safe_load(f)

    # Find the model configuration matching the given model_id
    model_config = next((model for model in config["models"] if model["name"] == model_id), None)

    if model_config is None:
        raise RuntimeError(f"Model ID '{model_id}' not found in config.yaml")

    # Use the path from the matching model configuration, or fall back to model_id
    path_or_model_id = model_config.get("path", model_id)

    pipe = StableDiffusionPipeline.from_pretrained(path_or_model_id, torch_dtype=torch.float32)
    # This option is essential for VAE to be able to render the image at the end of pipeline
    pipe.vae.enable_tiling()
    pipe.enable_xformers_memory_efficient_attention()
    pipe = pipe.to("cuda")
    return pipe


def generate(pipe, prompt, steps, height, width, seed, **kwargs):
    scheduler = kwargs.get('scheduler', None)
    if scheduler is None:
        # Use the existing scheduler if scheduler is None
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    else:
        # Import the scheduler class dynamically based on the provided name
        try:
            module_name = "diffusers.schedulers"
            class_name = scheduler
            module = importlib.import_module(module_name)
            scheduler_class = getattr(module, class_name)
            pipe.scheduler = scheduler_class.from_config(pipe.scheduler.config)
        except (ImportError, AttributeError):
            raise ValueError("Invalid scheduler specified")
    
    kwargs.pop('scheduler')
    generator = torch.Generator("cuda").manual_seed(seed)
    for image in pipe(prompt=prompt, num_inference_steps=steps, generator=generator,
                      height=height, width=width, **kwargs).images:
        return image
    

if __name__ == '__main__':
    generate(load_model(), 'a little girl riding a horse', 50)
