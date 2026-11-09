"""E0.5 Windows rendering feasibility + review renders (Stage 4 rev. 3.3a, §15.5).

Renders 3 dev clips x {reference, KF2P, GF} as one side-by-side video per clip, for the user's
review only. Generated panels come from the existing released-checkpoint dev dumps (repetition
0); nothing is sampled here. This is not a paper reproduction (R10).

Pre-specified: clips 0, 1, 2 of the dev dumps (the first three E0.4 clips); SMPL-X neutral,
betas 0, flat_hand_mean, flip_left_hand=True (E0.4 C4); upstream build_smplx_input; neutral face
(the face stream is excluded from P1 and the SMPL-X face basis differs from the authors', A4);
fixed upper-body camera shared by all panels and clips; 20 fps (upstream visualiser default; the
How2Sign frame rate is not in the metadata, D2). Renderer: pyrender offscreen via pyglet (WGL).

The videos contain SMPL-X meshes (licensed model): personal research use on this machine only,
never redistributed.

    python -E -s experiments/stage4/e0/render_review.py --out experiments/stage4/out/e0/renders
"""

import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "third_party" / "SignSparK" / "tools"))
import visualize as upstream  # noqa: E402

import os  # noqa: E402
os.environ.pop("PYOPENGL_PLATFORM", None)  # upstream defaults to EGL (Linux); Windows uses pyglet/WGL
import pyrender  # noqa: E402
import trimesh  # noqa: E402

RUN = "debug0_eulerstepsize10_can1_anchor0_samples/seed102_clampstep0_h2s_dev_{r}_s10.npy"
MODELS = ROOT / "models" / "smplx"
CLIPS = [0, 1, 2]
PANELS = [("Reference (pseudo-GT)", None), ("KF2P released ckpt", "kf2p"), ("GF released ckpt", "gf")]
SIZE, FPS, NECK = 448, 20, 12


def load(path):
    # Dumps are produced locally by our own sampling runs (dict pickled by np.save).
    return np.load(path, allow_pickle=True).item()


def dump(stream, regime):
    return load(ROOT / f"experiments/baseline/runs/{stream}/h2s_dev_{regime}_s10" / RUN.format(r=regime))


def verts(model, body, lh, rh):
    kw = upstream.build_smplx_input(torch.from_numpy(body), torch.from_numpy(lh), torch.from_numpy(rh),
                                    num_expression=10, flip_left_hand=True)
    with torch.no_grad():
        return model(**kw).vertices.numpy()


def make_scene(center):
    scene = pyrender.Scene(bg_color=[1, 1, 1, 1], ambient_light=[0.3, 0.3, 0.3])
    cam = np.eye(4)
    cam[:3, 3] = center + np.array([0.0, 0.0, 1.5])
    scene.add(pyrender.PerspectiveCamera(yfov=np.deg2rad(40)), pose=cam)
    for dx, intensity in [(0.5, 1.5), (-0.5, 0.9), (0.0, 1.2)]:  # upstream light rig at half intensity
        lp = np.eye(4); lp[0, 3] = dx; lp[1, 3] = 0.4
        scene.add(pyrender.DirectionalLight(color=np.ones(3), intensity=intensity), pose=lp)
    return scene


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    import smplx
    model = smplx.create(str(MODELS), model_type="smplx", gender="neutral", use_pca=False, flat_hand_mean=True,
                         num_betas=10, num_expression_coeffs=10, ext="npz").eval()
    faces = model.faces
    with torch.no_grad():
        center = model().joints[0, NECK].numpy() - np.array([0.0, 0.12, 0.0])
    mat = pyrender.MetallicRoughnessMaterial(baseColorFactor=[0.62, 0.70, 0.85, 1.0], metallicFactor=0.1)

    d = {(s, r): dump(s, r) for s in ("body", "hand") for r in ("gf", "kf2p")}
    renderer = pyrender.OffscreenRenderer(SIZE, SIZE)
    meta = []
    for i in CLIPS:
        name = str(d["body", "gf"]["video_names"][0, i])
        L = int(d["body", "gf"]["lengths"][0, i])
        for k, v in d.items():
            assert str(v["video_names"][0, i if k[0] == "body" else 2 * i]) == name and int(v["lengths"][0, i if k[0] == "body" else 2 * i]) == L
        seqs, kf = [], d["body", "kf2p"]["keyframes"][0, i, :, :L].any(0)
        for _, regime in PANELS:
            src, key = ("gt_poses", "gf") if regime is None else ("pred_poses", regime)
            b = d["body", key][src][0, i, :, :L].T.copy()
            lh = d["hand", key][src][0, 2 * i, :, :L].T.copy()
            rh = d["hand", key][src][0, 2 * i + 1, :, :L].T.copy()
            seqs.append(verts(model, b, lh, rh))

        t0 = time.time()
        path = out / f"e0_review_clip{i}_{name}.mp4"
        writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (SIZE * 3, SIZE + 40))
        for f in range(L):
            tiles = []
            for (label, regime), V in zip(PANELS, seqs):
                scene = make_scene(center)
                scene.add(pyrender.Mesh.from_trimesh(trimesh.Trimesh(V[f], faces, process=False), material=mat,
                                                     smooth=True))
                color, depth = renderer.render(scene)
                img = cv2.cvtColor(color, cv2.COLOR_RGB2BGR)
                img[depth == 0] = 245  # bg_color is not honoured by the WGL context; composite by depth
                cv2.putText(img, label, (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (30, 30, 30), 1, cv2.LINE_AA)
                if regime == "kf2p" and kf[f]:
                    cv2.putText(img, "keyframe", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 200), 1, cv2.LINE_AA)
                tiles.append(img)
            frame = np.concatenate(tiles, axis=1)
            bar = np.full((40, frame.shape[1], 3), 255, np.uint8)
            cv2.putText(bar, f"dev clip {i}  frame {f + 1}/{L}  released-checkpoint outputs, not a paper reproduction",
                        (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (60, 60, 60), 1, cv2.LINE_AA)
            writer.write(np.concatenate([frame, bar], axis=0))
        writer.release()
        rec = {"clip": i, "name": name, "frames": L, "text": str(d["body", "gf"]["text"][0, i]),
               "file": path.name, "render_seconds": round(time.time() - t0, 1),
               "kf2p_keyframe_frames": int(kf.sum())}
        meta.append(rec)
        print(json.dumps(rec))
    renderer.delete()
    (out / "renders.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
