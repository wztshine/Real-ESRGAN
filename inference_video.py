import argparse
import os
import pathlib
import shutil
import subprocess
import sys

import ffmpeg


def video(video_path: str | pathlib.Path, frame_rate: float = None, fps: float = None, scale: float = 2,
          model = "realesr-animevideov3", ffmpeg_path: str = None):
    """通过 ffmpeg 和 realesrgan 来增强处理视频, 默认新生成的视频名为：原视频名_X放大倍数。

    :param video_path: 视频文件路径
    :param frame_rate: 生成的视频的帧率，这里指的是视频每秒显示的图片数量, 默认为原视频的帧率
    :param fps: 生成的视频一秒多少帧，默认为原视频的帧率
    :param scale: 视频放大比例，默认 2 倍
    :param model: 使用的模型名字
    :param ffmpeg_path: ffmpeg.exe 文件所在路径，如果是 None，则代表你已经将此程序加入环境变量中。
    :return:
    """
    video_path = pathlib.Path(video_path).resolve()
    video_name = video_path.stem
    video_suffix = video_path.suffix
    new_video_name = str(video_path.parent / (video_name + f"_X{scale}" + f".{video_suffix}"))  # 生成的新视频名字

    input_frames = (video_path.parent / f"{video_name}_input_frames")
    out_frames = (video_path.parent / f"{video_name}_out_frames")
    input_frames.mkdir(parents=True, exist_ok=True)
    out_frames.mkdir(parents=True, exist_ok=True)

    input_frames = str(input_frames)
    out_frames = str(out_frames)
    video_path = str(video_path)

    if not ffmpeg_path:
        ffmpeg_path = "ffmpeg"

    frame_rate = get_frame_rate(video_path) if frame_rate is None else frame_rate
    fps = frame_rate if fps is None else fps

    cmd = f"{ffmpeg_path} -i {video_path} -qscale:v 1 -qmin 1 -qmax 1 -vsync 0 {input_frames}/frame%08d.jpg"  # 将原视频逐帧提取成图片放到 input_frames 文件夹中。
    cmd2 = f"{sys.executable} ./inference_realesrgan.py -i {input_frames} -o {out_frames} -n {model} -s {scale}"  # 将 input_frames 文件夹中的所有图片，批量放大处理，存到 out_frames 文件夹中
    cmd3 = rf'{ffmpeg_path} -framerate {frame_rate} -i {out_frames}\frame%08d_out.jpg -i {video_path} -map 0:v:0 -map 1:a:0 -c:a copy -c:v libx264 -r {fps} -pix_fmt yuv420p {new_video_name}'  # 将 out_frames 文件夹中的所有图片进行合并成视频，并使用原视频的音频添加到这个视频中

    os.system(cmd)
    os.system(cmd2)
    try:e
        subprocess.check_call(cmd3, shell=True)
    except subprocess.CalledProcessError as e:
        print(e)
    else:
        shutil.rmtree(input_frames)
        shutil.rmtree(out_frames)


def get_frame_rate(video_path):
    """使用 ffprobe（ffmpeg的一个工具）获取视频的帧率。

    :param video_path: video path
    :return: frame rate of the video
    """
    if not pathlib.Path(video_path).exists():
        raise FileNotFoundError(f"{video_path} Doesn't exists.")
    probe = ffmpeg.probe(video_path)
    video_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'video']
    fps = eval(video_streams[0]['avg_frame_rate'])
    fps = round(fps, 2)
    return fps


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', type=str, default='./inputs/video/onepiece_demo.mp4', help='Input video file path.')
    parser.add_argument(
        '-n',
        '--model_name',
        type=str,
        default='realesr-animevideov3',
        help=('Model names: realesr-animevideov3 | RealESRGAN_x4plus_anime_6B | RealESRGAN_x4plus | RealESRNet_x4plus |'
              ' RealESRGAN_x2plus | realesr-general-x4v3'
              'Default:realesr-animevideov3'))
    parser.add_argument('-s', '--outscale', type=float, default=2, help='The final upsampling scale of the image')
    parser.add_argument('--fps', type=float, default=None, help='FPS of the output video')
    parser.add_argument('--ffmpeg_bin', type=str, default='ffmpeg', help='The path to ffmpeg')
    args = parser.parse_args()

    video(video_path=args.input, model=args.model_name, scale=args.outscale, fps=args.fps, ffmpeg_path=args.ffmpeg_bin)
