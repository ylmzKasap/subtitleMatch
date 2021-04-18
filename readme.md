
## Subtitle Match

Find and extract movie scenes from your archive for any word or phrase you like.

### Required Software
ffmpeg is required for exporting the movies segments.

Download ffmpeg from:
https://ffmpeg.org/download.html

Working download link for Windows:
https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z

After the download:
1. Extract the files.
2. Open 'bin' folder.
3. Copy and paste 'ffmpeg.exe' to a folder which is included in the system path.

**Organizing the Files**
Before starting, you should edit the input and output paths on main.py.

1. `PATH_OF_MOVIES` variable should have the path of your movie archive.
2. Each movie should have its own folder named after it. In the folder, there should be a video file and a subtitle file (.srt) for that particular movie.

Here is a sample archive structure:
```
My_Movie_Archive/
    Coco (2017)/
        Coco.2017.1080p.mp4         # Filenames are not important.
        English_sub.srt
    WALL-E (2008)/
        WALL-E.2008.1080p.mkv
        English_sub.srt
    The Good, the Bad and the Ugly (1966)/
	    The Good, the Bad and the Ugly (1966).mp4
        English_sub.srt
```
3. `OUTPUT_PATH` should lead to the path where you want the extracted scenes. Default is current working directory.

**Running the Script**
Make sure that project folder is in the system path, or create a separate batch file.

Let's say that you want to extract every scene that includes the phrase "thank you".
Launch the command prompt and run:

    main.py "thank you"

This way, every matching scene will be exported to the output path.

**Manual Selection**
After exporting the movies, going through them one by one to view their content can be time consuming.

For this reason, if you pass `-c` as the **second argument**, you can view the matching subtitle events beforehand and choose the ones you like manually to export.

     main.py "thank you" -c

**Omitting Long Matches**
Sometimes a subtitle event can be really crowded and the phrase you are searching for may not be as emphasized as you want.

Passing `-vshort` or `-short` arguments will only match the events which are shorter than 4 and 7 words respectively.

    main.py "thank you" -c -short

**Stretching the Out Time**
If you exported a scene, but it ends very abruptly, you can stretch its out time by entering a value as seconds **as the second or third argument**. Default is 3 seconds.

All scenes exported as below will last 4 seconds longer.

    main.py "thank you" 7 -vshort


Similarly, you can use this feature with manual selection as well.

    main.py "thank you" -c 7 -vshort