import asyncio
import base64
import uuid
from aiohttp import web
import logging
from log import setup_logger
from mygen import load_model, generate
import io

logger = logging.getLogger(__name__)


def generate_image(text_prompt, inference_steps):
    global model
    # Your image generation logic here
    # This function should perform the long-running image generation process
    # You can use asyncio.sleep() to simulate the process
    image = generate(model, text_prompt, inference_steps)
    img_bytes_io = io.BytesIO()
    image.save(img_bytes_io, format='PNG')
    # Replace the image_bytes variable with your actual image data
    image_bytes = img_bytes_io.getvalue()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    logger.info("return image")
    return image_base64


async def generate_image_handler(request):
    data = await request.json()
    text_prompt = data.get("textPrompt")
    inference_steps = int(data.get("inferenceSteps"))
    
    # Generate a UUID for the task
    jobId = str(uuid.uuid4())

    # Run the image generation task in the asyncio threadpool executor
    loop = asyncio.get_event_loop()
    task = loop.run_in_executor(None, generate_image, text_prompt, inference_steps)
    
    # Store the task in a global dictionary or database using the task_id as the key
    # Replace `tasks` with your preferred storage mechanism
    tasks[jobId] = task
    logger.info("created task with id " + str(jobId))
    return web.json_response({"jobId": jobId})


async def check_task_status_handler(request):
    task_id = request.query.get("jobId")

    # Retrieve the task from the global dictionary or database using the task_id
    task = tasks.get(task_id)

    if task is None:
        return web.json_response({"status": "error", "message": "Task not found"})

    if task.done():
        try:
            logger.info("task " + task_id + " is done, getting result")
            image_base64 = task.result()  # Get the result of the completed task (generated image as Base64)
            logger.info("got the result")
            return web.json_response({"status": "completed", "image_base64": image_base64})
        except Exception as e:
            logger.error("error generating image", exc_info=e)
            return web.json_response({"status": "error", "message": str(e)})
        finally:
            del tasks[task_id]
    else:
        logger.info("returning pending for " + task_id)
        return web.json_response({"status": "pending"})


async def index(request):
    # Read the index.html file and return it
    with open("static/index.html", "r") as f:
        return web.Response(text=f.read(), content_type="text/html")


# Create an empty dictionary to store the tasks
# Replace `tasks` with your preferred storage mechanism
tasks = {}
setup_logger()
app = web.Application()
model = load_model()

# Route for serving the index.html file
app.router.add_route("GET", "/", index)
app.router.add_post("/api/generate", generate_image_handler)
app.router.add_get("/api/check", check_task_status_handler)
app.router.add_static("/static", path="./static", name="static")

web.run_app(app)
