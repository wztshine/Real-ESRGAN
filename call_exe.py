"""
针对这个项目的 exe 版本软件，使用这个脚本可以调用它来处理视频和图片。
需要事先下载 ffmpeg 和 这个项目的 exe 版本软件。可以将这两个程序添加到环境变量，也可以在使用下面提供的接口时，手动传递两个程序的可执行文件路径。
"""
import os
import pathlib
import shutil
import typing

import ffmpeg

T_Scale = typing.Literal[2, 3, 4]
T_Model = typing.Literal["realesr-animevideov3", "realesrgan-x4plus", "realesrgan-x4plus-anime", "realesrnet-x4plus"]


def img(img_path: str | pathlib.Path, scale: T_Scale = 2, model: T_Model = "realesr-animevideov3", realesrgan_path: str = None):
    """通过 realesrgan 来增强处理图片

    :param img_path: 图片文件路径
    :param scale: 图片放大比例，默认 2 倍，可选值为：2,3,4
    :param model: 使用的模型名字
    :param realesrgan_path: realesrgan-ncnn-vulkan.exe 文件所在路径，如果是 None，则代表你已经将此程序加入环境变量中。
    :return:
    """
    img_path = pathlib.Path(img_path)
    new_img_name = img_path.stem + f"_X{scale}" + img_path.suffix
    new_img_path = img_path.parent / new_img_name
    cmd = f"{realesrgan_path} -i {str(img_path)} -o {str(new_img_path)} -s {scale} -n {model}"
    os.system(cmd)


def video(video_path: str | pathlib.Path, frame_rate: float = None, fps: float = None, scale: T_Scale = 2,
          model: T_Model = "realesr-animevideov3", realesrgan_path: str = None, ffmpeg_path: str = None):
    """通过 ffmpeg 和 realesrgan 来增强处理视频, 默认新生成的视频名为：原视频名_X放大倍数。

    :param video_path: 视频文件路径
    :param frame_rate: 生成的视频的帧率，这里指的是视频每秒显示的图片数量, 默认为原视频的帧率
    :param fps: 生成的视频一秒多少帧，默认为原视频的帧率
    :param scale: 视频放大比例，默认 2 倍, 可选值为 2，3，4
    :param model: 使用的模型名字
    :param realesrgan_path: realesrgan-ncnn-vulkan.exe 文件所在路径，如果是 None，则代表你已经将此程序加入环境变量中。
    :param ffmpeg_path: ffmpeg.exe 文件所在路径，如果是 None，则代表你已经将此程序加入环境变量中。
    :return:
    """
    video_path = pathlib.Path(video_path)
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
    else:
        if not realesrgan_path:
            realesrgan_path = "realesrgan-ncnn-vulkan.exe"

    frame_rate = get_frame_rate(video_path) if frame_rate is None else frame_rate
    fps = frame_rate if fps is None else fps

    cmd = f"{ffmpeg_path} -i {video_path} -qscale:v 1 -qmin 1 -qmax 1 -vsync 0 {input_frames}/frame%08d.jpg"  # 将原视频逐帧提取成图片放到 input_frames 文件夹中。
    cmd2 = f"{realesrgan_path} -i {input_frames} -o {out_frames} -n {model} -s {scale} -f jpg"  # 将 input_frames 文件夹中的所有图片，批量放大处理，存到 out_frames 文件夹中
    cmd3 = f'{ffmpeg_path} -framerate {frame_rate} -i {out_frames}/frame%08d.jpg -i {video_path} -map 0:v:0 -map 1:a:0 -c:a copy -c:v libx264 -r {fps} -pix_fmt yuv420p {new_video_name}.mp4'  # 将 out_frames 文件夹中的所有图片进行合并成视频，并使用原视频的音频添加到这个视频中

    os.system(cmd)
    os.system(cmd2)
    os.system(cmd3)

    shutil.rmtree(input_frames)
    shutil.rmtree(out_frames)


def get_frame_rate(video_path):
    """使用 ffprobe（ffmpeg的一个工具）获取视频的帧率。

    :param video_path: video path
    :return: frame rate of the video
    """
    probe = ffmpeg.probe(video_path)
    video_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'video']
    fps = eval(video_streams[0]['avg_frame_rate'])
    return fps


if __name__ == "__main__":
    video(r"D:\备份\documents\Projects\video_enhance\Real-ESRGAN-master\inputs\video\xx.mp4", realesrgan_path=r"C:\Users\wztshine\Downloads\realesrgan-ncnn-vulkan-20220424-windows\realesrgan-ncnn-vulkan.exe", ffmpeg_path=None)
    # img("xx.jpg", realesrgan_path=r"C:\Users\wztshine\Downloads\realesrgan-ncnn-vulkan-20220424-windows\realesrgan-ncnn-vulkan.exe")
