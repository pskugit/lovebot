import numpy as np
from PIL import Image

import onnxruntime as ort
import torchvision
import torch.nn.functional as F
from src.utils import softmax

class ImageModel():
    def __init__(self, model_path):
        self.model_path = model_path
        if not model_path:
            raise AttributeError("model_path for ImageModel not specified")
        self.ort_sess = ort.InferenceSession(model_path)#, providers=['CUDAExecutionProvider'])
        print("ONNX model running on",ort.get_device())
               
    def inference(self, image, return_logits=False, apply_softmax=False):
        img_tensor = self.data_transforms(image).unsqueeze(0)
        logits = self.ort_sess.run(["output"], {'input': img_tensor.numpy()})[0]
        print(logits)
        if apply_softmax:
            logits = softmax(logits)
        pred_class = np.argmax(logits,axis=1).item()
        if return_logits:
            return self.classes[pred_class], logits
        else:
            return self.classes[pred_class]

    def inference_pathlist(self,pathlist,verbose=True, apply_softmax=False):
        preds = []
        logitss = []
        for img_path in pathlist:
            img = self.load_image(img_path)
            pred, logits = self.inference(img, return_logits=True, apply_softmax=apply_softmax)
            if verbose:
                print(f"{img_path}: {pred}, {logits}")
            preds.append(pred)
            logitss.append(logits)
        return preds, logitss
        
    def load_image(self, path):
        #print("loading...", path)
        return Image.open(path)

class BikiniModel(ImageModel):
    def __init__(self, model_path=""):
        self.crop_size = 448
        self.data_transforms = torchvision.transforms.Compose([
            torchvision.transforms.Resize(self.crop_size),
            torchvision.transforms.RandomCrop(self.crop_size),
            torchvision.transforms.ToTensor(),
            torchvision.transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225] )])
        self.classes = ("no_bikini","bikini")
    
        super().__init__(model_path)

class LikeModel(ImageModel):
    def __init__(self, model_path=""):
        self.crop_size = 448
        self.data_transforms = torchvision.transforms.Compose([
            torchvision.transforms.Resize(self.crop_size),
            torchvision.transforms.RandomCrop(self.crop_size),
            torchvision.transforms.ToTensor(),
            torchvision.transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225] )])
        self.classes = ("dislike","like")
    
        super().__init__(model_path)

TRAINED_MODELS = {
    "bikini": BikiniModel,
    "like": LikeModel,
}
