import datetime
import re

movieNameRegex = re.compile(r"[-.&'\w+\s]+")


class SubtitleEvent:
    def __init__(self, event, movie, videoName, hardcodedName, inSeconds, outSeconds):
        splitEvent = event.split("\n")

        self.movie = movie
        self.videoName = videoName
        self.hardcodedName = hardcodedName
        self.movieName = movieNameRegex.search(movie).group().strip()
        self.eventNumber = splitEvent[0]
        self.timestamp = splitEvent[1]
        self.inSeconds = inSeconds
        self.outSeconds = outSeconds
        self.subContent = ' '.join(splitEvent[2:])

    def in_time(self):
        splitTimestamp = self.timestamp.partition("-->")
        inTimeParsed = datetime.datetime.strptime(splitTimestamp[0].strip(), "%H:%M:%S,%f")
        newInTime = inTimeParsed - datetime.timedelta(seconds=self.inSeconds)
        newInTime = newInTime.strftime("%H:%M:%S.%f")
        return newInTime

    def out_time(self):
        splitTimestamp = self.timestamp.partition("-->")
        return re.sub(",", ".", splitTimestamp[2].strip())

    def scene_duration(self):
        inTime = datetime.datetime.strptime(self.in_time(), "%H:%M:%S.%f")
        outTime = datetime.datetime.strptime(self.out_time(), "%H:%M:%S.%f")
        return (outTime - inTime).seconds + self.outSeconds
