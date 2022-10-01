import os
import csv
import time
import random
import cv2
import tqdm
import numpy as np
import seaborn as sn
import sklearn.metrics as sklm
import matplotlib.pyplot as plt
from PIL import Image
from pathlib import Path
from skimage.util import img_as_ubyte
from skimage.util import img_as_float

import torch
import torchvision
import torchvision.models
import torch.nn.functional as F
from torch.utils import data
from torch.autograd.variable import Variable
cuda_device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
cuda_device, torch.cuda.is_available(),torch.__version__, torch.version.cuda

class ImageModel():
    def __init__(self, weights_path, device="auto"):
        if device=="auto":
            self.device = self.get_cuda_device()
        self.weights_path = weights_path
        if not weights_path:
            raise AttributeError("weights_path for ImageModel not specified")
        self._load_weights()
        self.net.to(self.device)
        self.net.eval()
        
    def _load_weights(self):
        self.net.load_state_dict(torch.load(self.weights_path, map_location=torch.device('cpu')))
        
    def inference(self, image, return_logits=False, softmax=False):
        with torch.no_grad():
            img_tensor = self.data_transforms(image).unsqueeze(0).to(self.device)
            logits = self.net(img_tensor)
            if softmax:
                logits = F.softmax(logits)
            pred_class = np.argmax(logits.cpu(),axis=1).item()
            if return_logits:
                return self.classes[pred_class], logits.cpu()
            else:
                return self.classes[pred_class]

    def inference_pathlist(self,pathlist,verbose=True, softmax=False):
        preds = []
        logitss = []
        for img_path in pathlist:
            img = self.load_image(img_path)
            pred, logits = self.inference(img, return_logits=True, softmax=softmax)
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
    def __init__(self, weights_path="", device="auto"):
        self.crop_size = 448
        self.data_transforms = torchvision.transforms.Compose([
            torchvision.transforms.Resize(self.crop_size),
            torchvision.transforms.RandomCrop(self.crop_size),
            torchvision.transforms.ToTensor(),
            torchvision.transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225] )])
        self.classes = ("no_bikini","bikini")
    
        self.net = torchvision.models.wide_resnet50_2(num_classes=1000, weights=None)
        self.net.fc = torch.nn.Linear(2048, len(self.classes))
        super().__init__(weights_path, device)

class LikeModel(ImageModel):
    def __init__(self, weights_path="", device="auto"):
        self.crop_size = 448
        self.data_transforms = torchvision.transforms.Compose([
            torchvision.transforms.Resize(self.crop_size),
            torchvision.transforms.RandomCrop(self.crop_size),
            torchvision.transforms.ToTensor(),
            torchvision.transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225] )])
        self.classes = ("dislike","like")
    
        self.net = torchvision.models.wide_resnet50_2(num_classes=1000, weights=None)
        self.net.fc = torch.nn.Linear(2048, len(self.classes))
        super().__init__(weights_path, device)

TRAINED_MODELS = {
    "bikini": BikiniModel,
    "like": LikeModel,
}
