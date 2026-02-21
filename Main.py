import ffmpeg
import json

probe = ffmpeg.probe('video.mp4')

print(json.dumps(probe, indent=2))

video_stream = next(s for s in probe['streams'] if s['codec_type'] == 'video')

codec_name = str(video_stream['codec_name']+"/"+video_stream['codec_long_name'])
width = video_stream['width']
height = video_stream['height']
fps = eval(video_stream['r_frame_rate'])
duration = float(probe['format']['duration'])
bitrate = int(probe['format']['bit_rate'])

print("res:",width,"x",height,"| fps:",fps,"| duration:",duration,"| bitrate:",bitrate,"| codec:",codec_name)




#can change video format


#ffmpeg.input('video.mp4').\
#    output('video.avi').run()


# can use output(X, an=None) for stripping audio
# you can also trim videos | resize/rescale | speed/slow down | text/captions | rotate | clip merge | crop | blur/borders | others(not my business)