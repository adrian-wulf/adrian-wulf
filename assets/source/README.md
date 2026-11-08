# Profile graphics source

`gen.py` builds the SVGs in `../` from two OFL fonts: Archivo (variable, `wdth` 75 and 100) and IBM Plex Mono Medium, both from [Google Fonts](https://github.com/google/fonts). Text is converted to outlines because GitHub does not load fonts inside SVG images.

Put `Archivo-VF.ttf` and `IBMPlexMono-Medium.ttf` next to `gen.py`, then run:

```sh
pip install fonttools uharfbuzz
python3 gen.py
```
