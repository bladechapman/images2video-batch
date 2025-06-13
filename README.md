
Stitch images into a video using batched ffmpeg passes.

```python
python3 images2video -i frames -a test-input.mp4 -o out.mp4
```

#### Why?
ffmpeg seems to consume a lot of memory when concatenating images into a video. This script allows you to concatenate images in batches before stitching the video parts together, reducing memory load.

#### ffmpeg doesn't do this already?
Maybe. I fiddled with adjusting the look-ahead-buffer and group-of-picture settings but still encountered ballooning memory consumption. ffmpeg is a pretty sopshisticated tool though and I'm but a novice. Maybe a video codec wizard has the answer.

#### Validated with:
ffmpeg v7.0.2 built with Apple clang version 15.0.0 (clang-1500.3.9.4)
