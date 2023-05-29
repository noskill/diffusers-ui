import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler


def load_model(model_id):
    pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float32)
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to("cuda")
    return pipe
    
def generate(pipe, prompt, steps, seed, height, width):
    generator = torch.Generator("cuda").manual_seed(seed)
    for image in pipe(prompt=prompt, num_inference_steps=steps, generator=generator,
                      height=height, width=width, guidance_scale=1).images:
        return image
    

if __name__ == '__main__':
    generate(load_model(), 'a little girl riding a horse', 50)
