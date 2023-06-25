import asyncio
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from diffusers import DiffusionPipeline, DPMSolverMultistepScheduler
from svdiff_pytorch import load_unet_for_svdiff, load_text_encoder_for_svdiff
import torch

app = FastAPI()

# CORS configuration
origins = ["*"]

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateImageRequest(BaseModel):
    prompt: str
    num_inference_steps: int = 25

class GenerateImageResponse(BaseModel):
    image: bytes

class ImageGenerator:
    def __init__(self):
        pretrained_model_name_or_path = "runwayml/stable-diffusion-v1-5"
        spectral_shifts_ckpt_dir = "ckpt-dir-path"
        unet = load_unet_for_svdiff(pretrained_model_name_or_path, spectral_shifts_ckpt=spectral_shifts_ckpt_dir, subfolder="unet")
        text_encoder = load_text_encoder_for_svdiff(pretrained_model_name_or_path, spectral_shifts_ckpt=spectral_shifts_ckpt_dir, subfolder="text_encoder")
        self.pipe = StableDiffusionPipeline.from_pretrained(
            pretrained_model_name_or_path,
            unet=unet,
            text_encoder=text_encoder,
        )
        self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(self.pipe.scheduler.config)
        self.pipe.to("cuda")

    async def generate_image(self, prompt: str, num_inference_steps: int = 25) -> bytes:
        try:
            image = await asyncio.to_thread(self.pipe, prompt, num_inference_steps=num_inference_steps).images[0]
            # Assuming the generated image is in PIL format, you can convert it to bytes
            image_bytes = image.tobytes()
            return image_bytes
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error") from e

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

generator = ImageGenerator()

@app.post("/generate-image", status_code=status.HTTP_200_OK, response_model=GenerateImageResponse)
async def generate_image(request: GenerateImageRequest):
    image_bytes = await generator.generate_image(request.prompt, request.num_inference_steps)
    return GenerateImageResponse(image=image_bytes)
