import os

from guess_who_is_sing import export_who_is_singing_video
from step_by_step_music import export_step_by_step_music_video

if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.abspath(__file__))

    # for i in ['love the way you lie', "105-1", "105-2", "zdht", "bbg", "dqsj", "dqsj-1"]:
    #     video_folder = os.path.join(root_dir, "assets", i)  # 视频文件夹路径
    #     export_video(video_folder)

    # video_folder = os.path.join(root_dir, "assets", "yourman")  # 视频文件夹路径
    # export_video(video_folder)

    # video_folder = os.path.join(root_dir, "assets", "cydd-1")  # 视频文件夹路径
    # export_video(video_folder)
    #
    video_folder = os.path.join(root_dir, "assets", "2")  # 视频文件夹路径
    export_step_by_step_music_video(video_folder)
    export_who_is_singing_video(video_folder)

    # video_folder = os.path.join(root_dir, "assets", "yellow")  # 视频文件夹路径
    # export_video(video_folder)
