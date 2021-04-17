import datetime
import os
from pathlib import Path
import re
import subprocess


PATH_OF_MOVIES = Path.cwd() / "movies"
OUTPUT_PATH = Path.cwd() / "output"
KEYWORD = "well then".lower()

if not OUTPUT_PATH.exists():
    OUTPUT_PATH.mkdir()

movieNameRegex = re.compile(r"[-&'\w+\s]+")


class SubtitleEvent:
    def __init__(self, event, movie, videoName):
        splitEvent = event.split("\n")

        self.movie = movie
        self.videoName = videoName
        self.movieName = movieNameRegex.search(movie).group().strip()
        self.eventNumber = splitEvent[0]
        self.timestamp = splitEvent[1]
        self.subContent = ' '.join(splitEvent[2:])

    def in_time(self):
        splitTimestamp = self.timestamp.partition("-->")
        inTimeParsed = datetime.datetime.strptime(splitTimestamp[0].strip(), "%H:%M:%S,%f")
        newInTime = inTimeParsed - datetime.timedelta(seconds=2)
        newInTime = newInTime.strftime("%H:%M:%S.%f")
        return newInTime

    def out_time(self):
        splitTimestamp = self.timestamp.partition("-->")
        return re.sub(",", ".", splitTimestamp[2].strip())

    def scene_duration(self):
        inTime = datetime.datetime.strptime(self.in_time(), "%H:%M:%S.%f")
        outTime = datetime.datetime.strptime(self.out_time(), "%H:%M:%S.%f")
        return (outTime - inTime).seconds + 3


allMovies = os.listdir(PATH_OF_MOVIES)
matches = {}
errorLog = []

for movie in allMovies:
    movieFound = subFound = 0

    # Locate the video and subtitle files for a specific movie.
    for filename in os.listdir(PATH_OF_MOVIES / movie):
        if filename.endswith(".mp4") or filename.endswith(".mkv"):
            movieFile = filename
            movieFound = 1
        if filename.endswith(".srt"):
            subFile = filename
            subFound = 1

    # Abort if there are missing video or subtitle files.
    if movieFound == 0:
        errorLog.append(f"Could not locate the video file for {movie}")
        continue
    if subFound == 0:
        errorLog.append(f"Could not locate the subtitle file for {movie}")
        continue

    # Open the subtitle file.
    with open(PATH_OF_MOVIES / movie / subFile) as sub:
        subtitleEvents = sub.read().split("\n\n")[:-1]  # Last item is always blank.

    # Search the keyword in the subtitle file.
    for index, event in enumerate(subtitleEvents):
        splitEvent = event.split("\n")
        subContent = ' '.join(splitEvent[2:]).lower()
        subContent = re.sub(",", "", subContent)

        # Skip SDH markers.
        if KEYWORD in subContent:
            if subContent.startswith("[") or subContent.startswith("("):
                continue
            if subContent.endswith("]") or subContent.startswith(")"):
                continue

            # Makes sure that the searched word is not a part of some other word.
            # As 'he' is a part of 'she'.
            textRegex = re.compile(fr"(?<![\[(\w]){KEYWORD}(?![\[(\w])")
            matchSearch = textRegex.search(subContent)
            try:
                matchSearch.group()
            except AttributeError:
                continue

            # Save the match info and create an instance.
            totalMatchNumber = len(matches) + 1
            matches[f"match{totalMatchNumber}"] = SubtitleEvent(event, movie, movieFile)

# Remove previous output files.
for file in os.listdir(OUTPUT_PATH):
    os.unlink(OUTPUT_PATH / file)

# Extract the scenes.
for i, match in enumerate(matches.values(), 1):
    # Find an available filename.
    outIndex = 1
    while True:
        if not (OUTPUT_PATH / f"{match.movieName} - {KEYWORD}_{outIndex}.mp4").exists():
            outFilename = f"{match.movieName} - {KEYWORD}_{outIndex}.mp4"
            break
        outIndex += 1

    # Extract.
    subprocess.run(
        ["ffmpeg/ffmpeg",
         "-ss",
         str(match.in_time()),
         "-i",
         str(PATH_OF_MOVIES / match.movie / match.videoName),
         "-t",
         str(match.scene_duration()),
         "-c",
         "copy",
         "-avoid_negative_ts",
         "1",
         str(OUTPUT_PATH / outFilename)]
    )

if len(errorLog) > 0:
    for error in errorLog:
        print(error)
    input()

if len(matches) == 0:
    print("\nNo match found.")
