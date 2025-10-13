import json, yaml, torch
from torchvision import models
from pathlib import Path

with open("/app/params.yaml") as f:
    P = yaml.safe_load(f)

if P["model_name"] == "mobilenet_v3_small":
    model = models.mobilenet_v3_small(weights=None)
    in_feats = model.classifier[3].in_features
    model.classifier[3] = torch.nn.Linear(in_feats, 2)
else:
    model = models.efficientnet_b0(weights=None)
    in_feats = model.classifier[1].in_features
    model.classifier[1] = torch.nn.Linear(in_feats, 2)

model.load_state_dict(torch.load("/app/artifacts/checkpoints/best.pt", map_location="cpu"))
model.eval()

dummy = torch.randn(1,3,P["img_size"],P["img_size"])
ts = torch.jit.trace(model, dummy)
out_dir = Path("/app/artifacts/model"); out_dir.mkdir(parents=True, exist_ok=True)
ts.save(str(out_dir/"model.torchscript.pt"))

with open(out_dir/"metadata.json","w") as f:
    json.dump({"img_size":P["img_size"],"model":P["model_name"],"classes":P["classes"]}, f, indent=2)
print("[export] model exported to TorchScript")
