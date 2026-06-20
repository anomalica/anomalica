# Centring a triangle inside a circular crop

For an upward-pointing equilateral triangle inside a square that will be cropped to a circle (like a GitHub avatar), the geometrically correct centring is **centroid at canvas centre**, not bounding-box centre.

## Why centroid, not bounding box

For an equilateral triangle, the centroid is the point equidistant from all three vertices (it's the centre of the triangle's circumscribed circle, by definition the **circumcentre** which coincides with the centroid for equilateral triangles only). Placing the centroid at the canvas centre means all three vertices sit at the same distance from the canvas centre - and therefore the same distance from the cropping circle's edge.

The centroid of an equilateral triangle is at 1/3 of the height from the base, not at the middle of the height. So centring by **bounding box** instead of centroid leaves the centroid below the canvas centre, and the visual effect is a triangle that looks "heavy at the bottom" - the vertices end up at different distances from the circle edge.

## Math

For an equilateral triangle with side length `s`:
- Height `h = s * √3/2`
- Centroid is at `h/3` from the base, `2h/3` from the apex
- Circumradius (distance from centroid to any vertex) = `s/√3 = 2h/3`

If you want the triangle's vertices to sit at distance `r` from the canvas centre (so they're all `R - r` from the circle edge, where `R` is the circle's radius), set `s = r * √3` and `h = r * 3/2`.

## Translating an existing path

If your SVG path was authored with the bounding box centred but you need the centroid centred, the translation is straightforward: shift the triangle vertically by `(bbox_centre_y - centroid_y)`. For an equilateral triangle that translation is `h/6` upward (or equivalently, the centroid is `h/6` below the bbox centre, where `h` is the triangle's height).

For a 512x512 canvas with a triangle of height 323 (the size used for the Anomalica avatar), the bbox-centred position needs to shift up by about 54 pixels to put the centroid at canvas centre. In practice the shift was 28 pixels because the original wasn't strictly bbox-centred either.

## Optical illusions to watch for

Even when geometrically centred, an upward-pointing triangle in a circle can look "off" because:

- The flat base looks heavier than the pointed apex (more visual weight at the base)
- The base line is far from the circle's bottom edge while the apex is near the top
- These create a subjective bias that the triangle is "too high"

This is just perception - the geometry is correct. If you want to fight the illusion, you can shift the triangle slightly down from the centroid-at-centre position, but it's a judgment call that depends on the rest of the visual context.

## How to verify

Render the PNG, find the white pixels (or whatever colour the triangle is), compute their centre of mass:

```python
import numpy as np
from PIL import Image
arr = np.array(Image.open('avatar.png'))
white = (arr[:,:,0] > 200) & (arr[:,:,1] > 200) & (arr[:,:,2] > 200)
ys, xs = np.where(white)
print(f"centre of mass: ({xs.mean():.1f}, {ys.mean():.1f})")
```

If centre-of-mass equals canvas centre (within sub-pixel rounding), the triangle is correctly centred.
