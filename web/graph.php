<?php
   // Get the current settings.
   //include 'setGetSettings.php';
   //setGet("");
?>

<html>
  <head>
    <!--- <link rel="stylesheet" type="text/css" href="thermo.css"> --->
    <!--- <meta name="viewport" content="width=device-width" />     --->
    <!--- <title><?php echo $DeviceName;?></title>                  --->
    <!--- <link rel="icon" href="<?php echo $hotColdIconImgIcon;?>">--->
    
    <?php
        /////////////////////////////////////////////////////////
        // This code will run every time something happens.
        /////////////////////////////////////////////////////////        
        $pythonScript = "python /home/pi/NetUsageWeb/getNetUsageChartArray.py";
        $titleStr = "Network Usage - 1 Day";

        $time = 3600*24;
        $numPoints = 600;

        if(isset($_GET["submit_1hr"]))
        {
          $time = 3600;
          $numPoints = 100;
          $titleStr = "Network Usage - 1 Hr";
        }
        if(isset($_GET["submit_4hr"]))
        {
          $time = 3600*4;
          $numPoints = 400;
          $titleStr = "Network Usage - 4 Hrs";
        }
        if(isset($_GET["submit_12hr"]))
        {
          $time = 3600*12;
          $numPoints = 500;
          $titleStr = "Network Usage - 12 Hrs";
        }
        if(isset($_GET["submit_1day"]))
        {
          $time = 3600*24;
          $numPoints = 600;
          $titleStr = "Network Usage - 1 Day";
        }
        if(isset($_GET["submit_3day"]))
        {
          $time = 3600*24*3;
          $numPoints = 800;
          $titleStr = "Network Usage - 3 Days";
        }
        if(isset($_GET["submit_7day"]))
        {
          $time = 3600*24*7;
          $numPoints = 2000;
          $titleStr = "Network Usage - 7 Days";
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
          [{type: 'datetime', label: 'Time'}, 'Network Usage (bytes)'],
          <?php echo shell_exec($pythonScript." -t ".$time." -n ".$numPoints);?>
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
          // Gives each series an axis that matches the vAxes number below.
          series: {
            0: {targetAxisIndex: 1, color: '#F06846'},
            1: {targetAxisIndex: 0, color: '#3366CC'}
          },
          vAxes: {
            // Adds titles to each axis.
            1: {ticks: [0,1], textPosition: 'none'},
            0: {title: 'Network Usage (bytes)', textPosition: 'out'}
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
    <center>
    <form action="graph.php" method="get">
      <input name="submit_1hr" type="submit" value="1 Hr" />
      <input name="submit_4hr" type="submit" value="4 Hr" />
      <input name="submit_12hr" type="submit" value="12 Hr" />
      <input name="submit_1day" type="submit" value="1 Day" />
      <input name="submit_3day" type="submit" value="3 Day" />
      <input name="submit_7day" type="submit" value="7 Day" />
    </form>
    <h3>Usage</h3>
    <div id="curve_chart_usage"></div>
    </center>
  </body>
</html>