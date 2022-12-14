import os
import numpy as np
import configparser
from dotenv import load_dotenv

# copied from scikit-learn
def softmax(X, theta = 1.0, axis = None):
    """
    Compute the softmax of each element along an axis of X.
    Parameters
    ----------
    X: ND-Array. Probably should be floats. 
    theta (optional): float parameter, used as a multiplier
        prior to exponentiation. Default = 1.0
    axis (optional): axis to compute values along. Default is the 
        first non-singleton axis.

    Returns an array the same size as X. The result will sum to 1
    along the specified axis.
    """
    # make X at least 2d
    y = np.atleast_2d(X)
    # find axis
    if axis is None:
        axis = next(j[0] for j in enumerate(y.shape) if j[1] > 1)
    # multiply y against the theta parameter, 
    y = y * float(theta)
    # subtract the max for numerical stability
    y = y - np.expand_dims(np.max(y, axis = axis), axis)
    # exponentiate y
    y = np.exp(y)
    # take the sum along the specified axis
    ax_sum = np.expand_dims(np.sum(y, axis = axis), axis)
    # finally: divide elementwise
    p = y / ax_sum
    # flatten if X was 1D
    if len(X.shape) == 1: p = p.flatten()
    return p

def load_config():
    load_dotenv()
    path_prefix = os.environ["LOVEBOT_PATH"]
    path_prefix = path_prefix if path_prefix.endswith("/") else path_prefix+"/"
    config = configparser.ConfigParser()
    config_path = path_prefix+"config.ini"
    config.read(config_path)
    return path_prefix, config