mkdir -p "wav"

#find mp3/ -name *.mp3 -exec sh -c 'echo $(basename {} .mp3)' \;
find mp3/ -name *.mp3 -exec sh -c 'ffmpeg -y -i {} -acodec pcm_s16le -ac 1 -ar 16000 wav/$(basename {} .mp3).wav' \;
