from pathlib import Path
import os
import re
import subprocess
import sys

from data import lastExport
from data.subtitleclass import SubtitleEvent

KEYWORD = lastExport.KEYWORD
veryShortSentences = lastExport.veryShortSentences
shortSentences = lastExport.shortSentences
exportedSegments = lastExport.exportedSegments
extra_output_seconds = int(sys.argv[1])


PATH_OF_MOVIES = Path("F:", "dizifilmfalan", "subtitleMatch")
OUTPUT_PATH = Path.cwd() / "output"

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
            matches[f"match{totalMatchNumber}"] = SubtitleEvent(event, movie, movieFile, extra_output_seconds)

allMatchInstances = list(matches.values())

# Remove previous output files.
for file in os.listdir(OUTPUT_PATH):
    if file.endswith(".mp4"):
        os.unlink(OUTPUT_PATH / file)

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

# Create a new list with the selected objects.
exportedInstances = []
for exportNumber in exportedSegments:
    exportNumber = int(exportNumber)
    exportedInstances.append(allMatchInstances[exportNumber - 1])

for currentMatch in exportedInstances:
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
    print("\nError Log:\n")
    for error in errorLog:
        print(error)
        print()
    print("\nPress enter to continue.")
    input("> ")

if len(matches) == 0:
    os.system("cls")
    print("\nNo match found.\n")
else:
    os.system("cls")
    print("\nDONE\n")
