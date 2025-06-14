import argparse
from pathlib import Path
import logging
import shutil
import subprocess

parser = argparse.ArgumentParser(description="Stitch together images into video, in batches")
parser.add_argument("-i", "--image-input", help="input directory of images to stitch together", type=Path)
parser.add_argument("-a", "--audio-input", help="path to original movie, for audio extraction", type=Path)
parser.add_argument("-o", "--output", type=Path)
parser.add_argument("--batch-size", type=int)
parser.add_argument("--framerate", type=int, required=False, default=24)
parser.add_argument("--image_suffix", type=str, required=False, default="jpg")
parser.add_argument("-crf", help="h264 constant rate factor. Valid values 0-51, lower is higher quality & more space.", type=int, required=False, default=23)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("video-stitch")

def main():
    args = parser.parse_args()
    logger.info(args)

    # validate params
    image_input_folder = args.image_input.resolve()
    if not image_input_folder.is_dir():
        raise Exception("-i: image input must point to a folder of images to stitch")
    audio_input_file = args.audio_input.resolve()
    if not audio_input_file.is_file():
        raise Exception("-a: audio input must point to a movie with an audio track")

    # determine job parameters
    folder_contents = sorted([x for x in image_input_folder.iterdir() if x.is_file()])
    num_images = len(folder_contents)
    batch_size = args.batch_size
    f_padding = len(str(num_images))

    tmp_dir = Path("stitch_tmp").resolve()
    tmp_dir.mkdir(exist_ok=True)
    folder_contents_iterator = iter(folder_contents)
    mov_parts_subdir = tmp_dir.joinpath("mov_parts").resolve()
    mov_parts_subdir.mkdir(exist_ok=True)
    for i in range(0, num_images, batch_size):
        tmp_subdir = tmp_dir.joinpath(f"{i:0{f_padding}d}").resolve()
        tmp_subdir.mkdir(exist_ok=True)
        
        # create a batch of images for processing
        for j in range(0, batch_size):
            try:
                image_path = next(folder_contents_iterator)
                shutil.copy(image_path, tmp_subdir.joinpath(f"frame_{j}.{args.image_suffix}"))
            except StopIteration:
                break

        # process batches into videos
        subprocess.run([
                "ffmpeg",
                "-framerate", f"{args.framerate}",
                "-i", tmp_subdir.joinpath(f"frame_%d.{args.image_suffix}"),
                "-map", "0:v:0",
                "-c:v", "libx264",
                "-crf", str(args.crf),
                "-r", f"{args.framerate}",
                "-pix_fmt", "yuv420p",
                mov_parts_subdir.joinpath(f"{int(i/batch_size):0{f_padding}d}.mp4"),
                "-y"])

        # clean up temp subdir for this batch
        shutil.rmtree(tmp_subdir)

    # stitch video parts together
    mov_parts = sorted(mov_parts_subdir.glob("**/*.mp4"))
    stitch_input_file = tmp_dir.joinpath("inputs.txt")
    with open(stitch_input_file.as_posix(), "w") as f:
        for file in mov_parts:
            f.write(f"file '{file.as_posix()}'\n")
    subprocess.run([
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", stitch_input_file.as_posix(),
        "-c", "copy",
        tmp_dir.joinpath("stitched_no_audio.mp4").as_posix() ])

    # add audio
    subprocess.run([
        "ffmpeg",
        "-r", f"{args.framerate}",
        "-i", args.audio_input.as_posix(),
        "-i", tmp_dir.joinpath("stitched_no_audio.mp4").as_posix(),
        "-map", "0:a:0?",
        "-map", "1:v:0",
        "-c:a", "copy",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-r", f"{args.framerate}",
        args.output.as_posix(),
        "-y",
        ])
    
    # delete tmp
    shutil.rmtree(tmp_dir)

main()
