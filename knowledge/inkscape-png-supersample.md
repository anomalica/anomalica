# Cleaner SVG to PNG rendering with supersampling

Inkscape's default rasterisation is technically correct but produces visibly stair-stepped edges on curved or angled paths at typical avatar/icon resolutions (256-512 pixels). The fix is supersampling: render at 4x the target resolution, then downscale with a high-quality filter.

## The technique

```bash
# Render at 4x target resolution (2048 for a 512 target)
inkscape source.svg \
    --export-type=png \
    --export-filename=/tmp/oversize.png \
    --export-width=2048 \
    --export-height=2048

# Downscale to target with Lanczos resampling
python3 -c "
from PIL import Image
img = Image.open('/tmp/oversize.png')
img = img.resize((512, 512), Image.Resampling.LANCZOS)
img.save('output.png', optimize=True)
"
```

## Why this works

Direct rendering at 512x512: each output pixel is sampled once and gets a hard inside-or-outside-the-shape decision (modulated by the renderer's anti-aliasing, which is typically a 2x2 or 4x4 sample grid - not enough at this resolution).

Render at 2048x2048: each pixel's worth of the final image is now backed by 16 source pixels. When you downscale with Lanczos, those 16 pixels are weighted into one, producing genuine grey-scale anti-aliasing along edges instead of stair-stepping.

The trade-off is roughly 16x the rendering cost, which doesn't matter for icons - it's still under a second.

## When to use it

- Avatar/icon renders where edge quality is visible to a careful eye
- Anything that will be scaled down further by display software (browsers, GitHub thumbnails, etc.) - giving them a higher-quality starting point
- Logos with thin curved features

When NOT to use it:

- Build-step rendering where speed matters (e.g. generating thousands of icons)
- Very large output sizes where the source SVG complexity dominates render time

## Verification

To check the anti-aliasing quality of an existing PNG, take a small crop of an edge and upscale it 4x with NEAREST neighbour resampling. You should see soft gradient pixels along the edge boundary (good anti-aliasing) rather than sharp stair-stepping (bad).

```python
edge = img.crop((200, 30, 320, 150))
edge.resize((480, 480), Image.Resampling.NEAREST).save('/tmp/zoom.png')
```
