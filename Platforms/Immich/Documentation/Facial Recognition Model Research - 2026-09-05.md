# Facial Recognition Model Research

**Created:** 2026-09-05  
**Last updated:** 2026-09-05

I looked into whether a better facial recognition model than `buffalo_l` exists for Immich 3.1.0, and what other people have found. This note backs the face-model decision in the [CUDA machine learning record](Change%20Records/GTX%201080%20Ti%20CUDA%20Machine%20Learning%20-%202026-09-05.md).

## What Immich can run

The v3.1.0 machine-learning service accepts exactly four InsightFace packages: `antelopev2`, `buffalo_s`, `buffalo_m`, and `buffalo_l`. Detection and recognition are bundled per package and cannot be mixed. Immich's facial recognition documentation says the default is typically considered the best and offers the others for constrained systems.

| Package | Detection | Recognition | Size |
| --- | --- | --- | --- |
| `buffalo_l` (default) | RetinaFace-10GF (SCRFD) | ResNet50 on WebFace600K | 326 MB |
| `buffalo_m` | RetinaFace-2.5GF | ResNet50 on WebFace600K | 313 MB |
| `buffalo_s` | RetinaFace-500MF | MobileFaceNet on WebFace600K | 159 MB |
| `antelopev2` | RetinaFace-10GF | ResNet100 on Glint360K | 407 MB |

InsightFace's own model zoo publishes accuracy only for the buffalo family: `buffalo_l` scores 99.83 % LFW, 99.33 % CFP-FP, 98.23 % AgeDB-30, 97.25 % IJB-C, and 91.25 % MR-ALL, with `buffalo_m` at the same accuracy and `buffalo_s` far below at 71.87 % MR-ALL. InsightFace does not promote `antelopev2` and publishes no comparable figures for it.

## What people found

- Maintainer mertalev, March 2024: no need to change to `antelopev2` unless you feel like experimenting.
- Community testing in discussion 5028 concluded `antelopev2` is not better; the ResNet100 Glint360K recogniser was trained on fewer identities and an older schedule than `buffalo_l`'s WebFace600K run, and `antelopev2` uses the same detector anyway.
- A January 2026 report against a 60,000-face library settled on `buffalo_l` with detection score 0.7, recognition distance 0.6, and minimum faces 7 as the best precision and recall balance.
- Changing the face model erases all existing person assignments, because clustering and inference are not separate jobs. That is a strong reason not to swap models for a marginal gain.

## Requests for other models

- February 2026, discussion 25851: a proposal to replace InsightFace with DeepFace. Maintainer bo0tzz saw no benefit and it was closed.
- March 2026, discussion 26901: a proposal to decouple detection from recognition and add RetinaFace-R50, which is more accurate on hard detection cases. Open, with no maintainer response as of this note.
- Custom face models have no supported path: the ML service only downloads packages from Immich's Hugging Face organisation and the name list is fixed in code.

## Decision

Stay on `buffalo_l`. The gains available are in the settings rather than the model, and Immich's own cluster-tuning guide works that way: tighten the recognition distance toward 0.4 for a library with similar-looking people, raise minimum faces while clustering, then relax it in steps with the Missing job. My library has 4,580 detected faces, 1,050 of them unassigned and most from video frames. The thresholds I chose from this are in the [threshold tuning record](Change%20Records/Facial%20Recognition%20Threshold%20Tuning%20-%202026-09-05.md).

## Sources

- [Immich facial recognition documentation](https://docs.immich.app/features/facial-recognition)
- [Immich guide: better facial clusters](https://docs.immich.app/guides/better-facial-clusters)
- [Immich discussion 7838, buffalo_l or antelopev2](https://github.com/immich-app/immich/discussions/7838)
- [Immich discussion 5028, switching to a newer model](https://github.com/immich-app/immich/discussions/5028)
- [Immich discussion 25851, new face-recognition backend](https://github.com/immich-app/immich/discussions/25851)
- [Immich discussion 26901, decouple detection and recognition](https://github.com/immich-app/immich/discussions/26901)
- [InsightFace model zoo](https://github.com/deepinsight/insightface/blob/master/model_zoo/README.md)
- [Immich v3.1.0 model list](https://github.com/immich-app/immich/blob/v3.1.0/machine-learning/immich_ml/models/constants.py)
