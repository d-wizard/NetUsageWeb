import os
import time
import math
from datetime import datetime
import argparse
import fcntl
import subprocess
import json

################################################################################
# Constant Variables
################################################################################
THIS_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
THIS_SCRIPT_FILENAME_NO_EXT = os.path.splitext(os.path.realpath(__file__))[0] 
JSON_PATH = THIS_SCRIPT_FILENAME_NO_EXT + '.json'
NET_USAGE_LOG_PATH = os.path.join(THIS_SCRIPT_DIR, 'netUsage.log')
NET_USAGE_LOCK_PATH = os.path.join(THIS_SCRIPT_DIR, 'netUsage.lock')

LOG_NEW_LINE = "\n"
LOG_MAX_TIME = 60*60*24*30*4 # 4 Months
LOG_MAX_TIME_TIME_TO_LEAVE_AFTER_TRIM = 60*60*24*30*2 # 2 Months
TIME_BETWEEN_LOG_UPDATES = 30

class NetStatTimePoint(object):
   def __init__(self):
      # Time (sec), Raw Usage Value (bytes), Total Usage Since Beginning Of Time (bytes)
      self.time = None 
      self.rawUsage_tx = None
      self.rawUsage_rx = None
      self.totalUsage_tx = None
      self.totalUsage_rx = None


################################################################################
# Helper Functions
################################################################################
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

def runProcess(exe):
   retVal = []  
   p = subprocess.Popen(exe.split(' '), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
   while(True):
      retcode = p.poll() #returns None while subprocess is running
      line = p.stdout.readline()
      retVal.append(line)
      if(retcode is not None):
         break
   return retVal


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

def getNetUsagePoint(logLines, lineNum):
   retVal = NetStatTimePoint()
   try:
      splitLine = logLines[lineNum].split(',')
      retVal.time          = int(splitLine[0])
      retVal.rawUsage_tx   = int(splitLine[1])
      retVal.rawUsage_rx   = int(splitLine[2])
      retVal.totalUsage_tx = int(splitLine[3])
      retVal.totalUsage_rx = int(splitLine[4])
   except:
      print("getNetUsagePoint - Failed to parse line: " + str(lineNum))
      return None
   return retVal

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

def getPrintStr_usage(lines, isTx):
   retStr = ''

   startUsage = 0
   for lineIndex in range(len(lines)):
      try:
         point = getNetUsagePoint(lines, lineIndex)
         totalUsage = point.totalUsage_tx if isTx else point.totalUsage_rx
         if lineIndex == 0: # set startUsage on first point
            startUsage = totalUsage

         # Don't have the .0 if the netUsage value is a whole number (i.e. save 2 bytes)
         tempFlt = float(totalUsage - startUsage)/float(1024*1024*1024) # Retun in GiB
         tempInt = int(tempFlt)
         tempStr = str(tempInt) if tempInt == tempFlt else "{:.2f}".format(tempFlt)

         appendStr = '["Date(' + timeToPrintStr(point.time) + ')",' + tempStr + '],'
         retStr += appendStr
      except:
         pass
   
   if len(retStr) > 0 and retStr[-1] == ',':
       retStr = retStr[:-1]
   return retStr

def getPrintStr_rate(lines, isTx):
   retStr = ''

   lastTime = 0
   lastData = 0
   for lineIndex in range(len(lines)):
      try:
         point = getNetUsagePoint(lines, lineIndex)
         totalUsage = point.totalUsage_tx if isTx else point.totalUsage_rx

         # Don't have the .0 if the netUsage value is a whole number (i.e. save 2 bytes)
         tempFlt = float(totalUsage - lastData) / float(point.time - lastTime) / float(125000)
         tempInt = int(tempFlt)
         tempStr = str(tempInt) if tempInt == tempFlt else "{:.2f}".format(tempFlt)

         if lineIndex != 0:
            appendStr = '["Date(' + timeToPrintStr(point.time) + ')",' + tempStr + '],'
            retStr += appendStr

         lastTime = point.time
         lastData = totalUsage
      except:
         pass
   
   if len(retStr) > 0 and retStr[-1] == ',':
       retStr = retStr[:-1]
   return retStr

def updateNetUsageLogFile(netUsage_tx, netUsage_rx):
   nowUnixTime = getNowTimeUnix()

   lockFd = lockFile(NET_USAGE_LOCK_PATH)

   newUsagePoint = NetStatTimePoint()
   newUsagePoint.time = nowUnixTime
   newUsagePoint.rawUsage_tx = netUsage_tx
   newUsagePoint.rawUsage_rx = netUsage_rx

   logLines = readWholeFile_lines(NET_USAGE_LOG_PATH)

   lastUsagePoint = getNetUsagePoint(logLines, -1)
   if lastUsagePoint != None:
      # TX
      deltaUsage_tx = newUsagePoint.rawUsage_tx - lastUsagePoint.rawUsage_tx
      if deltaUsage_tx < 0:
         deltaUsage_tx = newUsagePoint.rawUsage_tx # The router must have reset its count. Some usage info will have been lost. 
      newUsagePoint.totalUsage_tx = lastUsagePoint.totalUsage_tx + deltaUsage_tx

      # RX
      deltaUsage_rx = newUsagePoint.rawUsage_rx - lastUsagePoint.rawUsage_rx
      if deltaUsage_rx < 0:
         deltaUsage_rx = newUsagePoint.rawUsage_rx # The router must have reset its count. Some usage info will have been lost. 
      newUsagePoint.totalUsage_rx = lastUsagePoint.totalUsage_rx + deltaUsage_rx
   else:
      # Start the log file
      newUsagePoint.totalUsage_tx = 0
      newUsagePoint.totalUsage_rx = 0

   # Log message format will be Time (sec), Raw Usage Value (bytes), Usage Delta (bytes), Total Usage Since Beginning Of Time (bytes)
   logPrint = str(newUsagePoint.time) + "," + str(newUsagePoint.rawUsage_tx) + "," + str(newUsagePoint.rawUsage_rx) + "," + str(newUsagePoint.totalUsage_tx) + "," + str(newUsagePoint.totalUsage_rx) + LOG_NEW_LINE
   appendFile(NET_USAGE_LOG_PATH, logPrint)

   # Limit the log from getting too big
   try:
      logLines = readWholeFile_lines(NET_USAGE_LOG_PATH)

      oldestTime = lineToTime(logLines[0])
      if (nowUnixTime - oldestTime) > LOG_MAX_TIME:
         indexToKeep = findTimeIndex(logLines, nowUnixTime - LOG_MAX_TIME_TIME_TO_LEAVE_AFTER_TRIM)
         logLines = logLines[indexToKeep:]
         writeWholeFile(NET_USAGE_LOG_PATH, LOG_NEW_LINE.join(logLines)+LOG_NEW_LINE)
   except:
      pass

   unlockFile(lockFd)

NetUsageCmd = None
NetUsageStartKeyWord_TX = None
NetUsageStartKeyWord_RX = None
NetUsageEndKeyWord_TX = None
NetUsageEndKeyWord_RX = None

def fillInNetUsageFromJson():
   global NetUsageCmd
   global NetUsageStartKeyWord_TX
   global NetUsageStartKeyWord_RX
   global NetUsageEndKeyWord_TX
   global NetUsageEndKeyWord_RX
   if NetUsageCmd == None:
      THIS_FILE_JSON = json.loads(readWholeFile(JSON_PATH))
      NetUsageCmd = THIS_FILE_JSON["NetUsageCmd"]
      NetUsageStartKeyWord_TX = THIS_FILE_JSON["NetUsageStartKeyWord_TX"]
      NetUsageStartKeyWord_RX = THIS_FILE_JSON["NetUsageStartKeyWord_RX"]
      NetUsageEndKeyWord_TX = THIS_FILE_JSON["NetUsageEndKeyWord_TX"]
      NetUsageEndKeyWord_RX = THIS_FILE_JSON["NetUsageEndKeyWord_RX"]


def getNetUsage():
   # Read the JSON contents of this file every time it is used.
   txUsage = None
   rxUsage = None
   try:
      global NetUsageCmd
      global NetUsageStartKeyWord_TX
      global NetUsageStartKeyWord_RX
      global NetUsageEndKeyWord_TX
      global NetUsageEndKeyWord_RX
      fillInNetUsageFromJson()

      cmdResults = runProcess(NetUsageCmd)

      for line in cmdResults:
         if NetUsageStartKeyWord_TX in line:
            subStr = line.split(NetUsageStartKeyWord_TX)[1].split(NetUsageEndKeyWord_TX)[0]
            txUsage = int(subStr)
         if NetUsageStartKeyWord_RX in line:
            subStr = line.split(NetUsageStartKeyWord_RX)[1].split(NetUsageEndKeyWord_RX)[0]
            rxUsage = int(subStr)
         if txUsage != None and rxUsage != None:
            return txUsage, rxUsage
   except:
      pass
   return None, None

# Main start
if __name__== "__main__":
   # Config argparse
   parser = argparse.ArgumentParser()
   parser.add_argument("-t", type=int, action="store", dest="chartTime", help="Chart Time", default=3600)
   parser.add_argument("-n", type=int, action="store", dest="numPoints", help="Num Points", default=100)
   parser.add_argument("-u", action="store_true", dest="Usage")
   parser.add_argument("-r", action="store_true", dest="Rate")
   parser.add_argument("--rx", action="store_true", dest="RX")
   parser.add_argument("--tx", action="store_true", dest="TX")
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
      
      if args.Rate:
         print(getPrintStr_rate(lines, args.TX))
      else:
         print(getPrintStr_usage(lines, args.TX))