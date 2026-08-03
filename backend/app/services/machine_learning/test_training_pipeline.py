from app.services.machine_learning.training_pipeline import TrainingPipeline

pipeline = TrainingPipeline()

pipeline.run("random_forest")