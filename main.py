from typing import Optional

# from fastapi import FastAPI

# app = FastAPI()


# @app.get("/")
# async def root():
#     return {"message": "Hello World"}

# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: Optional[str] = None):
#     return {"item_id": item_id, "q": q}


from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import httpx
from fastapi.responses import StreamingResponse

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your specific frontend origin, e.g., ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

class VideoRequest(BaseModel):
    url: str
    platform: str

@app.post("/get-download-link")
async def get_download_link(video_request: VideoRequest):
    try:
        url = video_request.url
        platform = video_request.platform.lower()
        print("Platform: ", platform)

        if platform in ["youtube", "instagram", "facebook"]:
            try:
                # Use yt-dlp to get the download URL
                ydl_opts = {
                    "quiet": True,
                    "format": "best[ext=mp4]",
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(url, download=False)
                    download_url = info_dict.get("url")
                    video_title = info_dict.get("title")  # Get the video title
                    if not download_url:
                        raise HTTPException(
                            status_code=404, detail="Failed to retrieve download URL"
                        )
                    print(f"Download URL: {download_url}")
                    return {"downloadUrl": download_url, "filename": video_title}
            except Exception as yt_error:
                print(f"Error with {platform} handling: {yt_error}")
                raise HTTPException(status_code=500, detail=f"{platform} error: {yt_error}")

        else:
            raise HTTPException(status_code=400, detail="Platform not supported")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/proxy")
async def proxy(url: str = Query(..., description="The video URL to fetch")):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, follow_redirects=True)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail="Failed to fetch the video"
                )
            
            # Stream the response back to the client
            return StreamingResponse(
                response.iter_bytes(),
                media_type=response.headers.get("content-type", "application/octet-stream"),
                headers={"Content-Disposition": f"attachment; filename=video.mp4"}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {str(e)}")

# # For development purposes
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=3001)