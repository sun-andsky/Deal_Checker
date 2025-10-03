from fastapi import BackgroundTasks
from app.pipeline_runner import main_pipeline as run_pipeline

@app.post("/api/run_pipeline")
def run_full_pipeline(background_tasks: BackgroundTasks):
    """
    Trigger full OCR -> Classification -> Suggestions -> Highlight pipeline.
    Runs in background.
    """
    background_tasks.add_task(run_pipeline)
    return {"message": "Pipeline started in background"}
