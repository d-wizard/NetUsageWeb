
<html>
  <head>
    <link rel="stylesheet" type="text/css" href="netUsage.css">
    <meta name="viewport" content="width=device-width" />
    <title>RX Usage Sum</title>
    
    <?php
        /////////////////////////////////////////////////////////
        // This code will run every time something happens.
        /////////////////////////////////////////////////////////        
        $pythonScript = "python ".dirname(__FILE__)."/../getNetUsageChartArray.py";
        $plotTypeCmd = " --rx -u";

        // Default to 30 day view
        $time = 3600*24*7;
        $numPoints = 2000;
        $titleStr = "RX Usage Sum - 30 Days";

        if(isset($_GET["submit_1min"]))
        {
          $time = 60;
          $numPoints = 100;
          $titleStr = "RX Usage Sum - 1 Min";
        }
        if(isset($_GET["submit_5min"]))
        {
          $time = 5*60;
          $numPoints = 100;
          $titleStr = "RX Usage Sum - 5 Min";
        }
        if(isset($_GET["submit_15min"]))
        {
          $time = 15*60;
          $numPoints = 100;
          $titleStr = "RX Usage Sum - 15 Min";
        }
        if(isset($_GET["submit_1hr"]))
        {
          $time = 3600;
          $numPoints = 100;
          $titleStr = "RX Usage Sum - 1 Hr";
        }
        if(isset($_GET["submit_4hr"]))
        {
          $time = 3600*4;
          $numPoints = 400;
          $titleStr = "RX Usage Sum - 4 Hrs";
        }
        if(isset($_GET["submit_12hr"]))
        {
          $time = 3600*12;
          $numPoints = 500;
          $titleStr = "RX Usage Sum - 12 Hrs";
        }
        if(isset($_GET["submit_1day"]))
        {
          $time = 3600*24;
          $numPoints = 600;
          $titleStr = "RX Usage Sum - 1 Day";
        }
        if(isset($_GET["submit_3day"]))
        {
          $time = 3600*24*3;
          $numPoints = 800;
          $titleStr = "RX Usage Sum - 3 Days";
        }
        if(isset($_GET["submit_7day"]))
        {
          $time = 3600*24*7;
          $numPoints = 2000;
          $titleStr = "RX Usage Sum - 7 Days";
        }
        if(isset($_GET["submit_30day"]))
        {
          $time = 3600*24*7;
          $numPoints = 2000;
          $titleStr = "RX Usage Sum - 30 Days";
        }
    ?>
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <script type="text/javascript">
      google.charts.load('current', {'packages':['corechart']});
      google.charts.setOnLoadCallback(drawChart);

      var chartW = window.innerWidth;
      var chartH = window.innerHeight;

      var upperH = Math.floor(chartW/1.1);
      var lowerH = 200;
      chartH = chartH - 200;


      if (chartH > upperH) {
        chartH = upperH;
      }
      if (chartH < lowerH) {
        chartH = lowerH;
      }

      function drawChart() {
        var data = google.visualization.arrayToDataTable([
          [{type: 'datetime', label: 'Time'}, 'RX Usage Sum (GiB)'],
          <?php echo shell_exec($pythonScript.$plotTypeCmd." -t ".$time." -n ".$numPoints);?>
        ]);

        var options = {
          chartArea:{
            left:"12%",
            right:"4%",
            bottom:"12%",
            top:"4%",
            width:"95%",
            height:"90%"
          },
          titleTextStyle: { fontSize: 20},
          legend: { position: 'bottom' },

          vAxes: {
            // Adds titles to each axis.
            0: {title: 'RX Usage Sum (GiB)', textPosition: 'out'}
          },
          backgroundColor: '<?php echo $DeviceColor;?>',
          width: chartW,
          height: chartH
        };

        var chart = new google.visualization.LineChart(document.getElementById('curve_chart_usage'));

        chart.draw(data, options);
      }
    </script>
  </head>
   <body>
    <div class="navbar">
        <a href="txUsageGraph.php">TX Usage</a>
        <a href="rxUsageGraph.php">RX Usage</a>
        <a href="txRateGraph.php">TX Rate</a>
        <a href="rxRateGraph.php">RX Rate</a>
    </div>
    <br><br>
    <center>
    <br>
    <form action="rxUsageGraph.php" method="get">
      <input name="submit_1min" type="submit" value="1 Min" size="50"/>
      <input name="submit_5min" type="submit" value="5 Min" />
      <input name="submit_1hr" type="submit" value="1 Hr" />
      <input name="submit_4hr" type="submit" value="4 Hr" />
      <br>
      <br>
      <input name="submit_1day" type="submit" value="1 Day" />
      <input name="submit_7day" type="submit" value="7 Days" />
      <input name="submit_30day" type="submit" value="30 Days" />
    </form>
    <h1><?php echo $titleStr;?></h1>
    <div id="curve_chart_usage"></div>
    </center>
  </body>
</html>