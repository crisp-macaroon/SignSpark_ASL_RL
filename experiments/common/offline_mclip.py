"""Build SignSparK's frozen M-CLIP text encoder from config only.

Upstream `Wilor_UNET.load_and_freeze_clip` calls
`MultilingualCLIP.from_pretrained('M-CLIP/XLM-Roberta-Large-Vit-B-16Plus')`, whose
__init__ in turn calls `AutoModel.from_pretrained('xlm-roberta-large')`: ~4.5 GB of
weights that the released SignSparK checkpoint then overwrites, because it already
bundles all `text_enc_model.*` tensors (verified: 560.55M params). Importing this module
replaces both calls with config-only construction (random init), so the only
downloads are config/tokenizer files. Callers MUST then load the SignSparK checkpoint
with strict=True, which guarantees every text-encoder weight comes from it.
Upstream files under third_party/ are not modified.
"""

import transformers
from multilingual_clip import pt_multilingual_clip, Config_MCLIP


def _init_from_config(self, config, *args, **kwargs):
    transformers.PreTrainedModel.__init__(self, config, *args, **kwargs)
    base_cfg = transformers.AutoConfig.from_pretrained(config.modelBase)
    self.transformer = transformers.AutoModel.from_config(base_cfg)
    self.LinearTransformation = __import__("torch").nn.Linear(
        in_features=config.transformerDimensions, out_features=config.numDims)


@classmethod
def _from_pretrained_config_only(cls, name, *args, **kwargs):
    return cls(Config_MCLIP.MCLIPConfig.from_pretrained(name))


pt_multilingual_clip.MultilingualCLIP.__init__ = _init_from_config
pt_multilingual_clip.MultilingualCLIP.from_pretrained = _from_pretrained_config_only
