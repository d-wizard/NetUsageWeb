import os
import time
import math
from datetime import datetime
import argparse
import fcntl


################################################################################
# Constant Variables
################################################################################
THIS_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
THIS_SCRIPT_FILENAME_NO_EXT = os.path.splitext(os.path.realpath(__file__))[0] 
NET_USAGE_LOG_PATH = os.path.join(THIS_SCRIPT_DIR, 'netUsage.log')
NET_USAGE_LOCK_PATH = os.path.join(THIS_SCRIPT_DIR, 'netUsage.lock')

LOG_NEW_LINE = "\n"
LOG_MAX_TIME = 60*60*24*30*4 # 4 Months
LOG_MAX_TIME_TIME_TO_LEAVE_AFTER_TRIM = 60*60*24*30*2 # 2 Months
TIME_BETWEEN_LOG_UPDATES = 30

class NetStatTimePoint(object):
   def __init__(self):
      # Time (sec), Raw Usage Value (bytes), Usage Delta (bytes), Total Usage Since Beginning Of Time (bytes)
      self.time = None 
      self.rawUsage = None
      self.deltaUsage = None
      self.totalUsage = None


def readWholeFile(path):
   retVal = ""
   try:
      fileId = open(path, 'r')
      retVal = fileId.read()
      fileId.close()
   except:
      pass
   return retVal

def appendFile(path, fileText):
   try:
      fileId = open(path, 'a')
      fileId.write(fileText)
      fileId.close()
   except:
      pass

def writeWholeFile(path, fileText):
   try:
      fileId = open(path, 'w')
      fileId.write(fileText)
      fileId.close()
   except:
      pass

def readWholeFile_lines(path):
   lines = readWholeFile(path).split(LOG_NEW_LINE)
   # remove empty line at end.
   if lines[-1] == "":
      lines = lines[:-1]
   return lines

def lockFile(fileToLock):
   fd = open(fileToLock, 'w')
   fcntl.lockf(fd, fcntl.LOCK_EX)
   return fd

def unlockFile(fd):
   fcntl.lockf(fd, fcntl.LOCK_UN )



def timeToPrintStr(unixTime):
   dt = datetime.fromtimestamp(float(unixTime))
   dtStr = str(dt).replace("-", ",").replace(":", ",").replace(" ", ",")
   dtSplit = dtStr.split(",")

   # Convert to integers
   intVals = []
   for strVal in dtSplit:
      intVals.append(int(strVal))

   # Some idiot started months at 0. Not days. Days start at 1. But months start at 0.
   intVals[1] -= 1

   # Convert back to strings
   retStrs = []
   for intVal in intVals:
      retStrs.append(str(intVal))

   return ",".join(retStrs)

def getNowTimeUnix():
   nowUnixTime = time.mktime(datetime.now().timetuple())
   return int(nowUnixTime)

def lineToTime(line):
   return int(line.split(",")[0])

def findTimeIndex(lines, timeLimit):
   numLines = len(lines)
   # First test for some error values.
   if lineToTime(lines[0]) >= timeLimit:
      return 0
   if lineToTime(lines[-1]) < timeLimit:
      return -1
   if numLines < 2:
      return -1

   badIndex = 0
   goodIndex = numLines - 1

   bailOut = math.ceil(math.log(numLines, 2))
   bailOut += 4 # Add a few more to the loop; can't hurt.

   while ((goodIndex - badIndex) > 1) and (bailOut > 0):
      tryIndex = int(((goodIndex - badIndex) / 2) + badIndex)
      if lineToTime(lines[tryIndex]) >= timeLimit:
         goodIndex = tryIndex
      else:
         badIndex = tryIndex
      bailOut -= 1

   if bailOut == 0:
      return -1

   return goodIndex

def getLinesToChart(lines, numLinesToChart):
   retVal = []
   numLines = float(len(lines))
   skipOver = numLines / float(numLinesToChart-1)

   if skipOver < 1.0:
      skipOver = 1.0
   
   index = float(0.0)
   while index < numLines:
      retVal.append(lines[int(index)])
      index += skipOver
   
   # Make sure the last time is included.
   if retVal[-1] != lines[-1]:
      retVal.append(lines[-1])

   return retVal

def getPrintStr(lines):
   retStr = ''
   for line in lines:
      try:
         [unixTime, netUsage, switchState] = line.split(",")

         # Don't have the .0 if the netUsage value is a whole number (i.e. save 2 bytes)
         tempFlt = float(netUsage)
         tempInt = int(tempFlt)
         tempStr = str(tempInt) if tempInt == tempFlt else str(tempFlt)

         appendStr = '["Date(' + timeToPrintStr(unixTime) + ')",' + str(int(switchState)) + ',' + tempStr + '],'
         retStr += appendStr
      except:
         pass
   
   if retStr[-1] == ',':
       retStr = retStr[:-1]
   return retStr

def getNetUsagePoint(logLines, lineNum):
   retVal = NetStatTimePoint()
   try:
      splitLine = logLines[lineNum].split(',')
      retVal.time       = int(splitLine[0])
      retVal.rawUsage   = int(splitLine[1])
      retVal.deltaUsage = int(splitLine[2])
      retVal.totalUsage = int(splitLine[3])
   except:
      print("getNetUsagePoint - Failed to parse line: " + str(lineNum))
      return None
   return retVal

def updateNetUsageLogFile(netUsage):
   nowUnixTime = getNowTimeUnix()

   lockFd = lockFile(NET_USAGE_LOCK_PATH)

   newUsagePoint = NetStatTimePoint()
   newUsagePoint.time = nowUnixTime
   newUsagePoint.rawUsage = netUsage

   logLines = readWholeFile_lines(NET_USAGE_LOG_PATH)

   lastUsagePoint = getNetUsagePoint(logLines, -1)
   if lastUsagePoint != None:
      newUsagePoint.deltaUsage = newUsagePoint.rawUsage - lastUsagePoint.rawUsage
      if newUsagePoint.deltaUsage < 0:
         newUsagePoint.deltaUsage = newUsagePoint.rawUsage # The router must have reset its count. Some usage info will have been lost. 
      newUsagePoint.totalUsage = lastUsagePoint.totalUsage + newUsagePoint.deltaUsage
   else:
      # Start the log file
      newUsagePoint.deltaUsage = 0
      newUsagePoint.totalUsage = newUsagePoint.deltaUsage

   # Log message format will be Time (sec), Raw Usage Value (bytes), Usage Delta (bytes), Total Usage Since Beginning Of Time (bytes)
   logPrint = str(newUsagePoint.time) + "," + str(newUsagePoint.rawUsage) + "," + str(newUsagePoint.deltaUsage) + "," + str(newUsagePoint.totalUsage) + LOG_NEW_LINE
   appendFile(NET_USAGE_LOG_PATH, logPrint)

   # Limit the log from getting too big
   try:
      logLines = readWholeFile_lines(NET_USAGE_LOG_PATH)
      # remove empty line at end.
      if logLines[-1] == "":
         logLines = logLines[:-1]

      oldestTime = lineToTime(logLines[0])
      if (nowUnixTime - oldestTime) > LOG_MAX_TIME:
         indexToKeep = findTimeIndex(logLines, nowUnixTime - LOG_MAX_TIME_TIME_TO_LEAVE_AFTER_TRIM)
         logLines = logLines[indexToKeep:]
         writeWholeFile(NET_USAGE_LOG_PATH, LOG_NEW_LINE.join(logLines)+LOG_NEW_LINE)
   except:
      pass

   unlockFile(lockFd)


# Main start
if __name__== "__main__":
   # Config argparse
   parser = argparse.ArgumentParser()
   parser.add_argument("-t", type=int, action="store", dest="chartTime", help="Chart Time", default=3600)
   parser.add_argument("-n", type=int, action="store", dest="numPoints", help="Num Points", default=100)
   args = parser.parse_args()

   # Process the Net Usage Log File
   lockFd = lockFile(NET_USAGE_LOCK_PATH)
   netUsageLogFile = readWholeFile(NET_USAGE_LOG_PATH)
   unlockFile(lockFd)

   lines = netUsageLogFile.split(LOG_NEW_LINE)

   # remove empty line at end.
   if lines[-1] == "":
      lines = lines[:-1]

   timeThresh = getNowTimeUnix() - args.chartTime
   index = findTimeIndex(lines, timeThresh)

   if index >= 0:
      lines = lines[index:]

      lines = getLinesToChart(lines, args.numPoints)
      
      print getPrintStr(lines)