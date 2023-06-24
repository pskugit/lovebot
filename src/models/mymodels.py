import numpy as np
from PIL import Image

import torch
import torchvision
import torchvision.models
import torch.nn.functional as F
cuda_device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
cuda_device, torch.cuda.is_available(),torch.__version__, torch.version.cuda

class ImageModel():
    def __init__(self, model_path, device="auto"):
        if device=="auto":
            self.device = self.get_cuda_device()
        self.model_path = model_path
        if not model_path:
            raise AttributeError("weights_path for ImageModel not specified")
        self._load_weights()
        self.net.to(self.device)
        self.net.eval()
        
    def _load_weights(self):
        self.net.load_state_dict(torch.load(self.model_path, map_location=torch.device('cpu')))
        
    def inference(self, image, return_logits=False, apply_softmax=False):
        with torch.no_grad():
            img_tensor = self.data_transforms(image).unsqueeze(0).to(self.device)
            logits = self.net(img_tensor)
            if apply_softmax:
                logits = F.softmax(logits)
            pred_class = np.argmax(logits.cpu(),axis=1).item()
            if return_logits:
                return self.classes[pred_class], logits.cpu()
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
    
    def get_cuda_device(self):
        return torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

class BikiniModel(ImageModel):
    def __init__(self, model_path="", device="auto"):
        self.crop_size = 448
        self.data_transforms = torchvision.transforms.Compose([
            torchvision.transforms.Resize(self.crop_size),
            torchvision.transforms.RandomCrop(self.crop_size),
            torchvision.transforms.ToTensor(),
            torchvision.transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225] )])
        self.classes = ("no_bikini","bikini")
    
        self.net = torchvision.models.wide_resnet50_2(num_classes=1000, weights=None)
        self.net.fc = torch.nn.Linear(2048, len(self.classes))
        super().__init__(model_path, device)

class LikeModel(ImageModel):
    def __init__(self, model_path="", device="auto"):
        self.crop_size = 448
        self.data_transforms = torchvision.transforms.Compose([
            torchvision.transforms.Resize(self.crop_size),
            torchvision.transforms.RandomCrop(self.crop_size),
            torchvision.transforms.ToTensor(),
            torchvision.transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225] )])
        self.classes = ("dislike","like")
    
        self.net = torchvision.models.wide_resnet50_2(num_classes=1000, weights=None)
        self.net.fc = torch.nn.Linear(2048, len(self.classes))
        super().__init__(model_path, device)

TRAINED_MODELS = {
    "bikini": BikiniModel,
    "like": LikeModel,
}
