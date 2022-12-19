import argparse
import os
import pathlib
import shutil
import subprocess
import sys

import ffmpeg


def video(video_path: str | pathlib.Path, frame_rate: float = None, fps: float = None, scale: float = 2, tile: int = 1000,
          model="realesr-animevideov3", ffmpeg_path: str = "ffmpeg"):
    """通过 ffmpeg 和 realesrgan 来增强处理视频, 默认新生成的视频名为：原视频名_X放大倍数。

    :param video_path: 视频文件路径
    :param frame_rate: 生成的视频的帧率，这里指的是视频每秒显示的图片数量, 默认为原视频的帧率
    :param fps: 生成的视频一秒多少帧，默认为原视频的帧率
    :param scale: 视频放大比例，默认 2 倍
    :param tile: 每个 tile 的像素大小，如果图片很大，则显卡负担很重，可能出现 GPU 内存异常。因此可以将每张图片按照指定的 tile 大小来分割成多块小图片，显卡每次处理这种小图片从而减轻显卡负担。这个数越大，则划分的小图片越少。
    :param model: 使用的模型名字
    :param ffmpeg_path: ffmpeg.exe 文件所在路径，如果是 None，则代表你已经将此程序加入环境变量中。
    :return:
    """
    video_path = pathlib.Path(video_path).resolve()
    video_name = video_path.stem
    video_suffix = video_path.suffix
    new_video_name = str(video_path.parent / (video_name + f"_X{scale}" + f"{video_suffix}"))  # 生成的新视频名字

    # 创建临时目录：input_frame_path 用来存放原视频提取的所有帧图片， out_frames_path 用来存放所有处理完成的帧图片
    input_frames_path = (video_path.parent / f"{video_name}_input_frames")
    out_frames_path = (video_path.parent / f"{video_name}_out_frames")
    input_frames_path.mkdir(parents=True, exist_ok=True)
    out_frames_path.mkdir(parents=True, exist_ok=True)

    input_frames_path = str(input_frames_path)
    out_frames_path = str(out_frames_path)
    video_path = str(video_path)

    video_info = get_video_info(video_path)
    if frame_rate is None:
        frame_rate = round(eval(video_info['avg_frame_rate']), 2)
    fps = frame_rate if fps is None else fps

    total_frames = int(video_info["nb_frames"])
    if total_frames != len(list(pathlib.Path(input_frames_path).iterdir())):
        cmd = f"{ffmpeg_path} -i {video_path} -qscale:v 1 -qmin 1 -qmax 1 -vsync 0 {input_frames_path}/frame%08d.jpg"  # 将原视频逐帧提取成图片放到 input_frames_path 文件夹中。
        os.system(cmd)

    try:
        cmd2 = f"{sys.executable} ./inference_realesrgan.py -i {input_frames_path} -o {out_frames_path} -n {model} -s {scale} -t {tile}"  # 将 input_frames_path 文件夹中的所有图片，批量放大处理，存到 out_frames_path 文件夹中
        subprocess.check_call(cmd2, shell=True)
    except subprocess.CalledProcessError as e:
        print(e)
        return

    try:
        cmd3 = rf'{ffmpeg_path} -framerate {frame_rate} -i {out_frames_path}\frame%08d_out.jpg -i {video_path} -map 0:v:0 -map 1:a:0 -c:a copy -c:v libx264 -r {fps} -pix_fmt yuv420p {new_video_name}'  # 将 out_frames_path 文件夹中的所有图片进行合并成视频，并使用原视频的音频添加到这个视频中
        subprocess.check_call(cmd3, shell=True)
    except subprocess.CalledProcessError as e:
        print(e)
    else:
        shutil.rmtree(input_frames_path)
        shutil.rmtree(out_frames_path)


def get_video_info(video_path):
    """使用 ffprobe（ffmpeg的一个工具）获取视频的信息。

    :param video_path: video path
    :return: frame rate of the video, e.g.
            {
                "index": 0,
                "codec_name": "h264",
                "codec_long_name": "H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10",
                "profile": "High",
                "codec_type": "video",
                "codec_tag_string": "avc1",
                "codec_tag": "0x31637661",
                "width": 3840,
                "height": 2160,
                "coded_width": 3840,
                "coded_height": 2160,
                "closed_captions": 0,
                "film_grain": 0,
                "has_b_frames": 1,
                "sample_aspect_ratio": "1:1",
                "display_aspect_ratio": "16:9",
                "pix_fmt": "yuv420p",
                "level": 52,
                "color_range": "tv",
                "color_space": "bt709",
                "color_transfer": "bt709",
                "color_primaries": "bt709",
                "chroma_location": "left",
                "field_order": "progressive",
                "refs": 1,
                "is_avc": "true",
                "nal_length_size": "4",
                "id": "0x1",
                "r_frame_rate": "60/1",
                "avg_frame_rate": "60/1",
                "time_base": "1/15360",
                "start_pts": 0,
                "start_time": "0.000000",
                "duration_ts": 1920512,
                "duration": "125.033333",
                "bit_rate": "10074608",
                "bits_per_raw_sample": "8",
                "nb_frames": "7502",
                "extradata_size": 46,
                "disposition": {
                    "default": 1,
                    "dub": 0,
                    "original": 0,
                    "comment": 0,
                    "lyrics": 0,
                    "karaoke": 0,
                    "forced": 0,
                    "hearing_impaired": 0,
                    "visual_impaired": 0,
                    "clean_effects": 0,
                    "attached_pic": 0,
                    "timed_thumbnails": 0,
                    "captions": 0,
                    "descriptions": 0,
                    "metadata": 0,
                    "dependent": 0,
                    "still_image": 0
                },
                "tags": {
                    "creation_time": "2022-12-14T23:54:15.000000Z",
                    "language": "und",
                    "handler_name": "VideoHandler",
                    "vendor_id": "[0][0][0][0]",
                    "timecode": "01:00:00:00"
                }
            }

    :rtype:
    """
    if not pathlib.Path(video_path).exists():
        raise FileNotFoundError(f"{video_path} Doesn't exists.")
    probe = ffmpeg.probe(video_path)
    video_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'video']
    return video_streams[0]


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
    parser.add_argument('--ffmpeg', type=str, default='ffmpeg', help='The path to ffmpeg')
    parser.add_argument('-t', '--tile', type=int, default=0, help='Tile size, 0 for no tile during testing')
    args = parser.parse_args()

    video(video_path=args.input, model=args.model_name, scale=args.outscale, fps=args.fps, ffmpeg_path=args.ffmpeg, tile=args.tile)
