import os

import ffmpeg


def convert_video_to_audio(video_file_path: str, audio_file_path: str, delete_original_file: bool = False) -> str:
    """
    Convert a video file to an audio file.

    :param video_file_path: The path to the video file to convert.
    :type video_file_path: str
    :param audio_file_path: The path to the audio file to create.
    :type audio_file_path: str
    :param delete_original_file: Whether to delete the original video file after conversion.
    :type delete_original_file: bool
    :return: The path to the audio file.
    :rtype: str
    """
    ffmpeg_command = ffmpeg.input(video_file_path)
    ffmpeg_command = ffmpeg.output(ffmpeg_command, audio_file_path)

    ffmpeg.run(ffmpeg_command, overwrite_output=True, quiet=True)

    if delete_original_file:
        os.remove(video_file_path)

    return audio_file_path


def trim_audio_file_to_length(audio_file_path: str, length_seconds: float, fade_in: bool = False,
                              fade_in_length: float = 0, fade_out: bool = False, fade_out_length: float = 0) -> str:
    """
    Trim an audio file to a specific length. Replaces the original audio file in-place.

    :param audio_file_path: The path to the audio file to trim.
    :type audio_file_path: str
    :param length_seconds: The length in seconds to trim the audio file to.
    :type length_seconds: float
    :param fade_in: Whether to fade in the audio.
    :type fade_in: bool
    :param fade_in_length: The length of the fade in.
    :type fade_in_length: float
    :param fade_out: Whether to fade out the audio.
    :type fade_out: bool
    :param fade_out_length: The length of the fade out.
    :type fade_out_length: float
    :return: The path to the trimmed audio file (should be the same as the input path).
    :rtype: str
    """
    ffmpeg_command = ffmpeg.input(audio_file_path, ss=0, t=length_seconds)
    if fade_in:
        ffmpeg_command = ffmpeg.filter(ffmpeg_command, "afade", t="in", st=0, d=fade_in_length)
    if fade_out:
        ffmpeg_command = ffmpeg.filter(ffmpeg_command, "afade", t="out", st=(length_seconds - fade_out_length),
                                       d=fade_out_length)
    temp_audio_file_path = audio_file_path.split(".")[0] + "_temp." + audio_file_path.split(".")[1]
    ffmpeg_command = ffmpeg.output(ffmpeg_command, temp_audio_file_path)

    ffmpeg.run(ffmpeg_command, overwrite_output=True, quiet=True)

    os.remove(audio_file_path)
    os.rename(temp_audio_file_path, audio_file_path)

    return audio_file_path
