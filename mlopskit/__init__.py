import warnings

from mlopskit.core.library import ModelLibrary, load_model  # NOQA
from mlopskit.core.model import Model  # NOQA
from mlopskit.api import serving

from mlopskit.pastry.api import make
from .api import Client

# from .pipe import Pipe

# Silence Tensorflow warnings
# https://github.com/tensorflow/tensorflow/issues/30427
warnings.simplefilter(action="ignore", category=FutureWarning)


__version__ = "2.0.2"
