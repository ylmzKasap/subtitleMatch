import os
from pathlib import Path
import re
import subprocess
import sys

from data.subtitleclass import SubtitleEvent

PATH_OF_MOVIES = Path("F:", "dizifilmfalan", "subtitleMatch")
# WARNING: Every '.mp4' file in the output path will be deleted each time the script runs.
OUTPUT_PATH = Path.cwd() / "output"

if not OUTPUT_PATH.exists():
    OUTPUT_PATH.mkdir()


def find_filename(keyword, movieName):
    outIndex = 1
    fileExists = 0
    while True:
        for file in os.listdir(OUTPUT_PATH):
            if f"{keyword}_{outIndex}" in file:
                fileExists = 1
                break
        if fileExists == 0:
            outFilename = f"{keyword}_{outIndex} - {movieName}.mp4"
            return outFilename, outIndex
        outIndex += 1
        fileExists = 0


# Optional: Repeat the last extraction for the manual exports.
# First argument: '-r'
# Second argument: A value in seconds that will stretch the end of the clips longer.
if sys.argv[1] == "-r":
    try:
        os.system(f"repeatlast.py {sys.argv[2]} {sys.argv[3]}")
    except IndexError:
        print("\nSample Usage:")
        print("\n>>> main.py -r 2 5\n")
    sys.exit()

# First argument: Word or phrase to be searched.
try:
    KEYWORD = sys.argv[1].lower()
except IndexError:
    print("\nA word or a phrase is required to extract.\n")
    print("Example Use: 'main.py potato'\n")
    sys.exit()


# Second argument: Pull the beginning of a scene 'x' seconds back.
try:
    pull_back_seconds = sys.argv[2]
    pull_back_seconds = int(pull_back_seconds) + 2
except IndexError:
    pull_back_seconds = 2
except ValueError:
    pull_back_seconds = 2


# Third argument (optional): Stretch the end of a scene for 'x' seconds.
try:
    extra_output_seconds = sys.argv[3]
    extra_output_seconds = int(extra_output_seconds) + 3
except IndexError:
    extra_output_seconds = 3
except ValueError:
    extra_output_seconds = 3


# # Optional argument: Manual export or extract all scenes.
try:
    if "-c" in sys.argv:
        outputDecision = "chooseExports"
    else:
        outputDecision = "extractAll"
except IndexError:
    outputDecision = "extractAll"

# Optional argument: Ignore long events.
# Pass '-short' to ignore events longer than 6 words.
if "-short" in sys.argv:
    shortSentences = 1
else:
    shortSentences = 0
# Pass '-vshort' to ignore events longer than 3 words.
if "-vshort" in sys.argv:
    veryShortSentences = 1
else:
    veryShortSentences = 0

# Optional argument: Export hardcoded videos if they exist.
if "-sub" in sys.argv:
    hardcodedVideos = 1
else:
    hardcodedVideos = 0

# For debugging.
"""
KEYWORD = "random"
outputDecision = "chooseExports"
extra_output_seconds = 3
shortSentences = 0
veryShortSentences = 1
hardcodedVideos = 0
"""

allMovies = os.listdir(PATH_OF_MOVIES)
matches = {}
errorLog = []

print("\nSearching...")

for movie in allMovies:
    movieFound = subFound = hardcodedSub = 0

    # Locate the video and subtitle files for a specific movie.
    for filename in os.listdir(PATH_OF_MOVIES / movie):
        if filename.endswith(".mp4") or filename.endswith(".mkv") or filename.endswith("avi"):
            if "HARDCODED" not in filename.upper():
                movieFile = filename
                movieFound = 1
            elif "HARDCODED" in filename.upper():
                hardcodedName = filename
                hardcodedSub = 1
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
    if hardcodedSub == 0:
        hardcodedName = None
        if hardcodedVideos == 1 and outputDecision == "extractAll":
            errorLog.append(f"Could not locate hardcoded video file for {movie}.")

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

        if KEYWORD in subContent:
            # Skip SDH markers.
            if subContent.startswith("[") or subContent.startswith("("):
                continue
            if subContent.endswith("]") or subContent.startswith(")"):
                continue

            # Skip speaker IDs.
            if ":" in subContent:
                colonSeparation = subContent.partition(":")
                if KEYWORD in colonSeparation[0]:
                    continue

            # Makes sure that the searched word is not a part of some other word.
            # As 'he' is a part of 'she'.
            textRegex = re.compile(fr"(?<![\[(\w]){KEYWORD}(?![:\])\w])")
            matchSearch = textRegex.search(subContent)
            try:
                matchSearch.group()
            except AttributeError:
                continue

            # Save the match info and create an instance.
            totalMatchNumber = len(matches) + 1
            matches[f"match{totalMatchNumber}"] = SubtitleEvent(
                event, movie, movieFile, hardcodedName, pull_back_seconds, extra_output_seconds)

allMatchInstances = list(matches.values())
os.system("cls")

# Extract the scenes.
if outputDecision == "extractAll":
    # Remove previous output files.
    for file in os.listdir(OUTPUT_PATH):
        if file.endswith(".mp4"):
            os.unlink(OUTPUT_PATH / file)

    for match in allMatchInstances:
        # Delete long events if the optional arguments are passed.
        if veryShortSentences == 1:
            if len(match.subContent.split()) > 3:
                continue
        elif shortSentences == 1:
            if len(match.subContent.split()) > 6:
                continue

        # Find an available file name.
        outFilename, outIndex = find_filename(KEYWORD, match.movieName)

        # Extract the segment.
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

        # Extract the segments for hardcoded videos.
        if match.hardcodedName is not None and hardcodedVideos == 1:
            outFilename = f"{KEYWORD}_{outIndex} - HARDCODED - {match.movieName}.mp4"
            subprocess.run(
                ["ffmpeg/ffmpeg",
                 "-ss",
                 str(match.in_time()),
                 "-i",
                 str(PATH_OF_MOVIES / match.movie / match.hardcodedName),
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
            if len(match.subContent.split()) > 3:
                indicesToDelete.append(i)
    elif shortSentences == 1:
        for i, match in enumerate(allMatchInstances):
            if len(match.subContent.split()) > 6:
                indicesToDelete.append(i)

    # Delete longer sentences based on the preferences above.
    for i in range(len(indicesToDelete) - 1, -1, -1):
        del allMatchInstances[indicesToDelete[i]]

    exportedSegments = []
    if len(allMatchInstances) > 0:
        # List all matching scenes.
        print("\nScenes found:")
        for i, match in enumerate(allMatchInstances, 1):
            print(f"\n{i}. {match.movieName} | {match.subContent}")
        print("_" * 100)
        possibleExtractions = [str(i) for i in range(1, len(allMatchInstances) + 1)]
        print("\nEnter 'exp' to end the selection. Enter '-' to delete the last selection.")
        print("Enter a number to extract its video segment:")

        # Choose the segments to extract.
        while True:
            if len(exportedSegments) > 0:
                print("\n\nSegments to be exported:")
                print(', '.join(exportedSegments))

            extractDecision = input("> ").strip()

            if extractDecision == "-":
                try:
                    exportedSegments.pop()
                    continue
                except IndexError:
                    continue

            elif extractDecision == "exp":
                break

            elif extractDecision not in possibleExtractions:
                print(f"\nThere are {len(allMatchInstances)} instances in total.")
                continue

            elif extractDecision in exportedSegments:
                print("\nThis segment is already in the export list.")
                continue
            exportedSegments.append(extractDecision)

        # Create a new list with the selected objects.
        exportedInstances = []
        for exportNumber in exportedSegments:
            exportNumber = int(exportNumber)
            exportedInstances.append(allMatchInstances[exportNumber - 1])

        # Remove previous output files.
        for file in os.listdir(OUTPUT_PATH):
            if file.endswith(".mp4"):
                os.unlink(OUTPUT_PATH / file)

        for match in exportedInstances:
            # Find an available file name.
            outFilename, outIndex = find_filename(KEYWORD, match.movieName)

            # Extract the segment.
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

            # Extract the segments for hardcoded videos.
            if match.hardcodedName is not None and hardcodedVideos == 1:
                outFilename = f"{KEYWORD}_{outIndex} - HARDCODED - {match.movieName}.mp4"
                subprocess.run(
                    ["ffmpeg/ffmpeg",
                     "-ss",
                     str(match.in_time()),
                     "-i",
                     str(PATH_OF_MOVIES / match.movie / match.hardcodedName),
                     "-t",
                     str(match.scene_duration()),
                     "-c",
                     "copy",
                     "-avoid_negative_ts",
                     "1",
                     str(OUTPUT_PATH / outFilename)]
                )
            elif match.hardcodedName is None and hardcodedVideos == 1:
                errorLog.append(f"Could not locate hardcoded video file for {match.movieName}.")

    # Save the last selections.
    with open(Path("data", "lastExport.py"), "w") as lastExport:
        lastExport.write(f"KEYWORD = \"{KEYWORD}\"\n")
        lastExport.write(f"veryShortSentences = {veryShortSentences}\n")
        lastExport.write(f"shortSentences = {shortSentences}\n")
        lastExport.write(f"exportedSegments = {exportedSegments}\n")
        lastExport.write(f"hardcodedVideos = {hardcodedVideos}\n")

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
