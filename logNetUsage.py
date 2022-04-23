import getNetUsageChartArray
import time

while (1):
   try:
      netUsageTx, netUsageRx = getNetUsageChartArray.getNetUsage()
      if netUsageTx != None and netUsageRx != None:
         getNetUsageChartArray.updateNetUsageLogFile(netUsageTx, netUsageRx)
   except:
      pass
   time.sleep(100)
