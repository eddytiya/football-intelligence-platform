from app.services.machine_learning.trainer import Trainer

trainer = Trainer()

trainer.setup()

trainer.train_model("random_forest")

trainer.predict_validation()

trainer.predict_test()