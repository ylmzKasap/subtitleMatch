import datetime
import os
from pathlib import Path
import re
import subprocess
import sys


PATH_OF_MOVIES = Path("F:", "dizifilmfalan", "subtitleMatch")
# WARNING: Every '.mp4' file in the output path will be deleted each time the script runs.
OUTPUT_PATH = Path.cwd() / "output"


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
        return (outTime - inTime).seconds + extra_output_seconds


if not OUTPUT_PATH.exists():
    OUTPUT_PATH.mkdir()

# First argument: Word or phrase to be searched.
try:
    KEYWORD = sys.argv[1].lower()
except IndexError:
    print("\nA word or a phrase is required to extract.\n")
    print("Example Use: 'main.py potato'\n")
    sys.exit()

# Second argument (optional): Manual export or extract all scenes.
try:
    if sys.argv[2] == "c":
        outputDecision = "chooseExports"
    else:
        outputDecision = "extractAll"
except IndexError:
    outputDecision = "extractAll"

# Third argument (optional): Stretch the end of a scene for 'x' seconds.
try:
    extra_output_seconds = sys.argv[3]
    extra_output_seconds = int(extra_output_seconds)
except IndexError:
    extra_output_seconds = 3
except ValueError:
    extra_output_seconds = 3

# Fourth argument (optional): Ignore long events.
# Pass 'shortS' to ignore events longer than 6 words.
if "shortS" in sys.argv:
    shortSentences = 1
else:
    shortSentences = 0
# Pass 'vshortS' to ignore events longer than 3 words.
if "vshortS" in sys.argv:
    veryShortSentences = 1
else:
    veryShortSentences = 0

# For debugging.
"""
KEYWORD = "random"
veryShortSentences = 1
shortSentences = 0
outputDecision = "chooseExports"
extra_output_seconds = 3
"""

movieNameRegex = re.compile(r"[-&'\w+\s]+")

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
    try:
        with open(PATH_OF_MOVIES / movie / subFile, encoding="utf8") as sub:
            subtitleEvents = sub.read().split("\n\n")[:-1]  # Last item is always blank.
    except UnicodeDecodeError:
        errorLog.append(
            f"Subtitle file of {movie} is corrupted. The movie will be excluded."
            + "\nTo solve this issue, open the subtitle file and go 'file -> save as'"
            + "\nSave it as a '.srt' file with 'utf-8' encoding."
        )
        continue

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
            textRegex = re.compile(fr"(?<![\[(\w]){KEYWORD}(?![:\[(\w])")
            matchSearch = textRegex.search(subContent)
            try:
                matchSearch.group()
            except AttributeError:
                continue

            # Save the match info and create an instance.
            totalMatchNumber = len(matches) + 1
            matches[f"match{totalMatchNumber}"] = SubtitleEvent(event, movie, movieFile)

allMatchInstances = list(matches.values())

# Remove previous output files.
for file in os.listdir(OUTPUT_PATH):
    if file.endswith(".mp4"):
        os.unlink(OUTPUT_PATH / file)

# Extract the scenes.
if outputDecision == "extractAll":
    # Delete long events if the optional arguments are passed.
    for match in allMatchInstances:
        if veryShortSentences == 1:
            if len(match.subContent.split()) > 3:
                continue
        elif shortSentences == 1:
            if len(match.subContent.split()) > 6:
                continue

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

elif outputDecision == "chooseExports":
    # Delete long events if the optional arguments are passed.
    indicesToDelete = []
    if veryShortSentences == 1:
        for i, match in enumerate(allMatchInstances):
            temp = match.subContent.split()
            if len(match.subContent.split()) > 3:
                indicesToDelete.append(i)
    elif shortSentences == 1:
        for i, match in enumerate(allMatchInstances):
            if len(match.subContent.split()) > 6:
                indicesToDelete.append(i)
    for i in range(len(indicesToDelete) - 1, -1, -1):
        del allMatchInstances[indicesToDelete[i]]

    exportedSegments = []
    if len(allMatchInstances) > 0:
        # Choose the segments to extract.
        while True:
            print("\nEnter 'exp' to end the selection. Enter '-' to delete the last decision.")
            print("\n\nEnter a number to extract its video segment:")
            for i, match in enumerate(allMatchInstances, 1):
                print(f"\n{i}. {match.movieName} | {match.subContent}")
            possibleExtractions = [str(i) for i in range(1, len(allMatchInstances) + 1)]

            if len(exportedSegments) > 0:
                print("\nSegments to be exported:")
                print(', '.join(exportedSegments))

            extractDecision = input("> ").strip()

            if extractDecision == "-":
                try:
                    os.system("cls")
                    exportedSegments.pop()
                    continue
                except IndexError:
                    continue

            if extractDecision == "exp":
                break

            if extractDecision not in possibleExtractions:
                os.system("cls")
                print(f"\nThere are {len(allMatchInstances)} instances in total.")
                continue

            if extractDecision in exportedSegments:
                os.system("cls")
                print("\nThis segment is already in the export list.")
                continue
            exportedSegments.append(extractDecision)
            os.system("cls")

        for exportNumber in exportedSegments:
            exportNumber = int(exportNumber)
            currentMatch = allMatchInstances[exportNumber - 1]
            outIndex = 1
            while True:
                if not (OUTPUT_PATH / f"{currentMatch.movieName} - {KEYWORD}_{outIndex}.mp4").exists():
                    outFilename = f"{currentMatch.movieName} - {KEYWORD}_{outIndex}.mp4"
                    break
                outIndex += 1

            # Extract.
            subprocess.run(
                ["ffmpeg/ffmpeg",
                 "-ss",
                 str(currentMatch.in_time()),
                 "-i",
                 str(PATH_OF_MOVIES / currentMatch.movie / currentMatch.videoName),
                 "-t",
                 str(currentMatch.scene_duration()),
                 "-c",
                 "copy",
                 "-avoid_negative_ts",
                 "1",
                 str(OUTPUT_PATH / outFilename)]
            )

if len(errorLog) > 0:
    os.system("cls")
    print()
    for error in errorLog:
        print(error)
    print("\nPress enter to continue.")
    input("> ")

if len(matches) == 0:
    print("\nNo match found.\n")
else:
    os.system("cls")
    print("\nDONE\n")
