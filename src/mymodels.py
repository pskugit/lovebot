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
        self._load_weights()
        self.net.to(self.device)
        self.net.eval()
        
    def _load_weights(self):
        self.net.load_state_dict(torch.load(self.weights_path, map_location=torch.device('cpu')))
        
    def inference(self, image, return_logits=False):
        with torch.no_grad():
            img_tensor = self.data_transforms(image).unsqueeze(0).to(self.device)
            logits = self.net(img_tensor)
            pred_class = np.argmax(logits.cpu(),axis=1).item()
            if return_logits:
                return self.classes[pred_class], logits.cpu()
            else:
                return self.classes[pred_class]
        
    def load_image(self, path):
        #print("loading...", path)
        return Image.open(path)
    
    def get_cuda_device(self):
        return torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

class BikiniModel(ImageModel):
    def __init__(self, weights_path="/Users/philippskudlik/local_dev/tndr/models/bikini/wideresnet_20_07_21-12__89888888.pt", device="auto"):
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

class BeautyModel(ImageModel):
    def __init__(self, weights_path="/Users/philippskudlik/local_dev/tndr/models/beauty/wideresnet_21_07_22-47.pt", device="auto"):
        self.crop_size = 448
        self.data_transforms = torchvision.transforms.Compose([
            torchvision.transforms.Resize(self.crop_size),
            torchvision.transforms.RandomCrop(self.crop_size),
            torchvision.transforms.ToTensor(),
            torchvision.transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225] )])
        self.classes = ("not","hot")
    
        self.net = torchvision.models.wide_resnet50_2(num_classes=1000, weights=None)
        self.net.fc = torch.nn.Linear(2048, len(self.classes))
        super().__init__(weights_path, device)

TRAINED_MODELS = {
    "bikini": BikiniModel,
    "beauty": BeautyModel,
}
