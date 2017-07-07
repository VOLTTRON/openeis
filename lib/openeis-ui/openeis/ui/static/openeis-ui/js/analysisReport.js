// Copyright (c) 2014, Battelle Memorial Institute
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// 1. Redistributions of source code must retain the above copyright notice, this
//    list of conditions and the following disclaimer.
// 2. Redistributions in binary form must reproduce the above copyright notice,
//    this list of conditions and the following disclaimer in the documentation
//    and/or other materials provided with the distribution.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
// ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
// WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
// DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
// ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
// (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
// LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
// ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
// SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
// The views and conclusions contained in the software and documentation are those
// of the authors and should not be interpreted as representing official policies,
// either expressed or implied, of the FreeBSD Project.
//
//
// This material was prepared as an account of work sponsored by an
// agency of the United States Government.  Neither the United States
// Government nor the United States Department of Energy, nor Battelle,
// nor any of their employees, nor any jurisdiction or organization
// that has cooperated in the development of these materials, makes
// any warranty, express or implied, or assumes any legal liability
// or responsibility for the accuracy, completeness, or usefulness or
// any information, apparatus, product, software, or process disclosed,
// or represents that its use would not infringe privately owned rights.
//
// Reference herein to any specific commercial product, process, or
// service by trade name, trademark, manufacturer, or otherwise does
// not necessarily constitute or imply its endorsement, recommendation,
// or favoring by the United States Government or any agency thereof,
// or Battelle Memorial Institute. The views and opinions of authors
// expressed herein do not necessarily state or reflect those of the
// United States Government or any agency thereof.
//
// PACIFIC NORTHWEST NATIONAL LABORATORY
// operated by BATTELLE for the UNITED STATES DEPARTMENT OF ENERGY
// under Contract DE-AC05-76RL01830

angular.module('openeis-ui.directives.analysis-report', [])
.directive('analysisReport', function ($compile) {
    return {
        restrict: 'E',
        terminal: true,
        transclude: true,
        scope: {
            arReport: '=',
            arData: '='
        },
        link: function (scope, element, attrs) {
            if (scope.arReport.description) {
                element.append('<p>' + scope.arReport.description + '</p>');
            }

            angular.forEach(scope.arReport.elements, function (reportElement) {
                if (reportElement.title) {
                    element.append('<h1>' + reportElement.title + '</h1>');
                }

                switch (reportElement.type) {
                case 'Table':
                    var table = angular.element('<table><thead><tr/></thead><tbody/></table>'),
                        tbody = table.find('tbody');

                    angular.forEach(reportElement.column_info, function (column) {
                        table.find('tr').append('<th>' + column[1] + '</th>');
                    });

                    angular.forEach(scope.arData[reportElement.table_name], function (row) {
                        var tr = angular.element('<tr/>');

                        angular.forEach(reportElement.column_info, function (column) {
                            tr.append('<td>' + row[column[0]] + '</td>');
                        });

                        tbody.append(tr);
                    });

                    element.append(table);
                    break;

                case 'TextBlurb':
                    element.append('<p class="text-blurb">' + reportElement.text + '</p>');
                    break;

                case 'LinePlot':
                    // TODO: plot all datasets on a single lineplot
                    angular.forEach(reportElement.xy_dataset_list, function (dataset) {
                        var data = [];
                        angular.forEach(scope.arData[dataset.table_name], function (row) {
                            data.push({ x: row[dataset.x_column], y: row[dataset.y_column] });
                        });
                        element.append(angular.element('<div class="line-plot" />').append(linePlotSVG(data, reportElement.x_label, reportElement.y_label)));
                    });
                    break;

                case 'BarChart':
                    angular.forEach(reportElement.xy_dataset_list, function (dataset) {
                        var data = [];
                        angular.forEach(scope.arData[dataset.table_name], function (row) {
                            data.push({ x: row[dataset.x_column], y: row[dataset.y_column] });
                        });
                        element.append(angular.element('<div class="bar-chart" />').append(barChartSVG(data, reportElement.x_label, reportElement.y_label)));
                    });
                    break;

                case 'ScatterPlot':
                    // TODO: plot all datasets on a single scatterplot
                    angular.forEach(reportElement.xy_dataset_list, function (dataset) {
                        var data = [];
                        angular.forEach(scope.arData[dataset.table_name], function (row) {
                            data.push({ x: row[dataset.x_column], y: row[dataset.y_column] });
                        });
                        element.append(angular.element('<div class="scatter-plot" />').append(scatterPlotSVG(data, reportElement.x_label, reportElement.y_label)));
                    });
                    break;

                case 'DatetimeScatterPlot':
                    // TODO: plot all datasets on a single scatterplot
                    angular.forEach(reportElement.xy_dataset_list, function (dataset) {
                        var data = [];
                        angular.forEach(scope.arData[dataset.table_name], function (row) {
                            data.push({ x: row[dataset.x_column], y: row[dataset.y_column] });
                        });
                        element.append(angular.element('<div class="scatter-plot scatter-plot--datetime" />').append(datetimeScatterPlotSVG(data, reportElement.x_label, reportElement.y_label)));
                    });
                    break;

                case 'HeatMap':
                    var data = [];
                    angular.forEach(scope.arData[reportElement.table_name], function (row) {
                        data.push({ x: row[reportElement.x_column], y: row[reportElement.y_column], z: row[reportElement.z_column] });
                    });
                    element.append(angular.element('<div class="heat-map" />').append(heatMapSVG(data, reportElement.x_label, reportElement.y_label)));
                    break;

                case 'RetroCommissioningAFDD':
                    element.append(angular.element('<div class="retro-commissioning-afdd" />').append(retroCommissioningAFDDSVG(scope.arData[reportElement.table_name],0)));
                    break;

                case 'SetpointDetector':
                    element.append(angular.element('<div class="setpoint-detector" />')
                        .html("<div id='temps-chart-box' class='rs-chart-container hidden'>\
                            <div class='title noselect'></div>\
                            <div class='rs-chart-area time-series'>\
                              <div class='rs-y-axis'></div>\
                              <div class='rs-chart'></div>\
                              <div class='rs-y-axis2'></div>\
                              <div class='rs-legend'></div>\
                              <div class='rs-slider'></div>\
                            </div>\
                          </div>"));
                    setpointDetectorSVG(scope.arData[reportElement.table_name],0);
                    break;

                case 'CyclingDetector':
                    var result_ele = angular.element("<div id='result' class='result' />");
                    var tab_ele = angular.element("\
                        <ul class='nav nav-tabs'>\
                            <li heading='data' id='data' class='active' style=''>\
                                <a href=''>data</a>\
                            </li>\
                            <li heading='analysis' id='analysis' class='' style=''>\
                                <a href=''>analysis</a>\
                            </li>\
                        </ul>");
                    var tab_content = angular.element("<div class='tab-content'></div>");
                    var data_ele = angular.element("\
                        <div id='data-content' class='tab-pane active' style=''>\
                            <div id='temps-chart-box' class='rs-chart-container hidden'>\
                                <div class='title noselect'></div>\
                                <div class='rs-chart-area time-series'>\
                                  <div class='rs-y-axis'></div>\
                                  <div class='rs-chart'></div>\
                                  <div class='rs-y-axis2'></div>\
                                  <div class='rs-legend'></div>\
                                  <div class='rs-slider'></div>\
                                </div>\
                            </div>\
                        </div>");
                    var rcx_tab = angular.element("<div id='analysis-content' class='tab-pane' style=''></div>");
                    var rcx_ele = angular.element("<div id='cycling-result' class='cycling-result' />");
                    rcx_tab.append(rcx_ele);
                    tab_content.append(data_ele);
                    tab_content.append(rcx_tab);
                    result_ele.append(tab_ele);
                    result_ele.append(tab_content);
                    element.append(result_ele);
                    cyclingDetectorSVG_Data(scope.arData[reportElement.table_name],0);
                    $compile(element.contents())(scope);
                    break;


                case 'ScheduleDetector':
                    element.append(angular.element('<div class="schedule-detector" />')
                        .html("<div id='temps-chart-box' class='rs-chart-container hidden'>\
                            <div class='title noselect'></div>\
                            <div class='rs-chart-area time-series'>\
                              <div class='rs-y-axis'></div>\
                              <div class='rs-chart'></div>\
                              <div class='rs-y-axis2'></div>\
                              <div class='rs-legend'></div>\
                              <div class='rs-slider'></div>\
                            </div>\
                          </div>"));
                    scheduleDetectorSVG(scope.arData[reportElement.table_name],0);
                    break;

                case 'LoadProfile':
                    element.append(angular.element('<div class="load-profile" />')
                        .html("<div id='loadprofile-chart-box' class='rs-chart-container hidden'>\
                            <div class='title noselect'></div>\
                            <div class='rs-chart-area time-series'>\
                              <div class='rs-y-axis'></div>\
                              <div class='rs-chart'></div>\
                              <div class='rs-legend'></div>\
                              <div class='rs-slider'></div>\
                            </div>\
                          </div>"));
                    loadProfileSVG(scope.arData[reportElement.table_name],0);
                    break;

                case 'LoadProfileRx':
                    element.append(angular.element('<div class="load-profile-rx" />')
                        .html("<div id='loadprofile-alldays-chart-box' class='rs-chart-container hidden'>\
                            <div class='title noselect'></div>\
                            <div class='rs-chart-area time-series'>\
                              <div class='rs-y-axis'></div>\
                              <div class='rs-chart'></div>\
                              <div class='rs-legend'></div>\
                              <div class='rs-slider'></div>\
                            </div>\
                          </div>\
                          <div id='loadprofile-weekdays-chart-box' class='rs-chart-container hidden'>\
                            <div class='title noselect'></div>\
                            <div class='rs-chart-area time-series'>\
                              <div class='rs-y-axis'></div>\
                              <div class='rs-chart'></div>\
                              <div class='rs-legend'></div>\
                              <div class='rs-slider'></div>\
                            </div>\
                          </div>\
                          <div id='loadprofile-sat-chart-box' class='rs-chart-container hidden'>\
                            <div class='title noselect'></div>\
                            <div class='rs-chart-area time-series'>\
                              <div class='rs-y-axis'></div>\
                              <div class='rs-chart'></div>\
                              <div class='rs-legend'></div>\
                              <div class='rs-slider'></div>\
                            </div>\
                          </div>\
                          <div id='loadprofile-sun-chart-box' class='rs-chart-container hidden'>\
                            <div class='title noselect'></div>\
                            <div class='rs-chart-area time-series'>\
                              <div class='rs-y-axis'></div>\
                              <div class='rs-chart'></div>\
                              <div class='rs-legend'></div>\
                              <div class='rs-slider'></div>\
                            </div>\
                          </div>\
                          <div id='loadprofile-holidays-chart-box' class='rs-chart-container hidden'>\
                            <div class='title noselect'></div>\
                            <div class='rs-chart-area time-series'>\
                              <div class='rs-y-axis'></div>\
                              <div class='rs-chart'></div>\
                              <div class='rs-legend'></div>\
                              <div class='rs-slider'></div>\
                            </div>\
                          </div>"));
                    loadProfileRxSVG(scope.arData[reportElement.table_name],0);
                    break;

                case 'RxStaticPressure':
                    element.append(angular.element('<div class="retro-commissioning-afdd" />').append(retroCommissioningAFDDSVG(scope.arData[reportElement.table_name],1)));
                    break;
                case 'RxSupplyTemp':
                    element.append(angular.element('<div class="retro-commissioning-afdd" />').append(retroCommissioningAFDDSVG(scope.arData[reportElement.table_name],2)));
                    break;
                case 'RxOperationSchedule':
                    element.append(angular.element('<div class="retro-commissioning-afdd" />').append(retroCommissioningAFDDSVG(scope.arData[reportElement.table_name],3)));
                    break;

                case 'RetroCommissioningAFDDEcam':
                    var result_ele = angular.element("<div id='result' class='result' />");
                    var tab_ele = angular.element("\
                        <ul class='nav nav-tabs'>\
                            <li heading='data' id='data' class='active' style=''>\
                                <a href=''>data</a>\
                            </li>\
                            <li heading='analysis' id='analysis' class='' style=''>\
                                <a href=''>analysis</a>\
                            </li>\
                        </ul>");
                    var tab_content = angular.element("<div class='tab-content'></div>");
                    var data_ele = angular.element("\
                        <div id='data-content' class='tab-pane active' style=''>\
                            <div id='ecam' class='ecam' />\
                                <div id='temps-chart-box' class='rs-chart-container hidden'>\
                                    <div class='title noselect'></div>\
                                    <div class='rs-chart-area time-series'>\
                                      <div class='rs-y-axis'></div>\
                                      <div class='rs-chart'></div>\
                                      <div class='rs-y-axis2'></div>\
                                      <div class='rs-legend'></div>\
                                      <div class='rs-slider'></div>\
                                    </div>\
                                </div>\
                                <div id='hcv-box' class='rs-chart-container hidden'>\
                                        <div class='title noselect'></div>\
                                        <div class='rs-chart-area time-series'>\
                                            <div class='rs-y-axis'></div>\
                                            <div class='rs-chart'></div>\
                                            <div class='rs-y-axis2'></div>\
                                            <div class='rs-legend'></div>\
                                            <div class='rs-slider'></div>\
                                        </div>\
                                </div>\
                                <div id='mat-oat-box' class='rs-chart-container hidden'>\
                                        <div class='title noselect'></div>\
                                        <div class='rs-chart-area'>\
                                            <div class='rs-y-axis'></div>\
                                            <div class='rs-chart'></div>\
                                            <div class='rs-legend'></div>\
                                        </div>\
                                </div>\
                            </div>\
                        </div>");
                    var rcx_tab = angular.element("<div id='analysis-content' class='tab-pane' style=''></div>");
                    var rcx_ele = angular.element("<div class='retro-commissioning-afdd' />")
                        .append(retroCommissioningAFDDSVG(scope.arData[reportElement.table_name],0));
                    rcx_tab.append(rcx_ele);
                    tab_content.append(data_ele);
                    tab_content.append(rcx_tab);
                    result_ele.append(tab_ele);
                    result_ele.append(tab_content);
                    element.append(result_ele);
                    economizer_rcx(scope.arData[reportElement.table_name]);
                    //$("#ecam").tabs();
                    $compile(element.contents())(scope);
                    break;

                case 'AhuEcam':
                    element.append(angular.element('<div class="ecam" />')
                        .html("<div id='oa-chart-box1' class='rs-chart-container hidden'>\
                            <div class='title noselect'></div>\
                            <div class='rs-chart-area time-series'>\
                              <div class='rs-y-axis'></div>\
                              <div class='rs-chart'></div>\
                              <div class='rs-y-axis2'></div>\
                              <div class='rs-legend'></div>\
                              <div class='rs-slider'></div>\
                            </div>\
                          </div>\
                          <div id='oa-chart-box2' class='rs-chart-container hidden'>\
                            <div class='title noselect'></div>\
                            <div class='rs-chart-area time-series'>\
                              <div class='rs-y-axis'></div>\
                              <div class='rs-chart'></div>\
                              <div class='rs-y-axis2'></div>\
                              <div class='rs-legend'></div>\
                              <div class='rs-slider'></div>\
                            </div>\
                          </div>\
                          <div id='sp-chart-box1' class='rs-chart-container hidden'>\
                            <div class='title noselect'></div>\
                            <div class='rs-chart-area time-series'>\
                              <div class='rs-y-axis'></div>\
                              <div class='rs-chart'></div>\
                              <div class='rs-y-axis2'></div>\
                              <div class='rs-legend'></div>\
                              <div class='rs-slider'></div>\
                            </div>\
                          </div>\
                          <div id='sp-chart-box2' class='rs-chart-container hidden'>\
                            <div class='title noselect'></div>\
                            <div class='rs-chart-area time-series'>\
                              <div class='rs-y-axis'></div>\
                              <div class='rs-chart'></div>\
                              <div class='rs-y-axis2'></div>\
                              <div class='rs-legend'></div>\
                              <div class='rs-slider'></div>\
                            </div>\
                          </div>\
                          <div id='coil-chart-box1' class='rs-chart-container hidden'>\
                            <div class='title noselect'></div>\
                            <div class='rs-chart-area time-series'>\
                              <div class='rs-y-axis'></div>\
                              <div class='rs-chart'></div>\
                              <div class='rs-y-axis2'></div>\
                              <div class='rs-legend'></div>\
                              <div class='rs-slider'></div>\
                            </div>\
                          </div>\
                          <div id='coil-chart-box2' class='rs-chart-container hidden'>\
                            <div class='title noselect'></div>\
                            <div class='rs-chart-area time-series'>\
                              <div class='rs-y-axis'></div>\
                              <div class='rs-chart'></div>\
                              <div class='rs-y-axis2'></div>\
                              <div class='rs-legend'></div>\
                              <div class='rs-slider'></div>\
                            </div>\
                          </div>\
                          <div id='discharge-chart-box1' class='rs-chart-container hidden'>\
                            <div class='title noselect'></div>\
                            <div class='rs-chart-area time-series'>\
                              <div class='rs-y-axis'></div>\
                              <div class='rs-chart'></div>\
                              <div class='rs-y-axis2'></div>\
                              <div class='rs-legend'></div>\
                              <div class='rs-slider'></div>\
                            </div>\
                          </div>\
                          <div id='discharge-chart-box2' class='rs-chart-container hidden'>\
                            <div class='title noselect'></div>\
                            <div class='rs-chart-area time-series'>\
                              <div class='rs-y-axis'></div>\
                              <div class='rs-chart'></div>\
                              <div class='rs-y-axis2'></div>\
                              <div class='rs-legend'></div>\
                              <div class='rs-slider'></div>\
                            </div>\
                          </div>\
                          <div id='fan-chart-box1' class='rs-chart-container hidden'>\
                            <div class='title noselect'></div>\
                            <div class='rs-chart-area time-series'>\
                              <div class='rs-y-axis'></div>\
                              <div class='rs-chart'></div>\
                              <div class='rs-y-axis2'></div>\
                              <div class='rs-legend'></div>\
                              <div class='rs-slider'></div>\
                            </div>\
                          </div>"));
                    ahu_ecam(scope.arData[reportElement.table_name]);
                    break;

                case 'ZoneEcam':
                    element.append(angular.element('<div class="ecam" />')
                        .html("<div id='temps-chart-box' class='rs-chart-container hidden'>\
                            <div class='title noselect'></div>\
                            <div class='rs-chart-area time-series'>\
                              <div class='rs-y-axis'></div>\
                              <div class='rs-chart'></div>\
                              <div class='rs-y-axis2'></div>\
                              <div class='rs-legend'></div>\
                              <div class='rs-slider'></div>\
                            </div>\
                          </div>"));
                    zone_ecam(scope.arData[reportElement.table_name]);
                    break;

                case 'HWPlantViz':
                    element.append(angular.element('<div class="ecam" />')
                    .html("<div id='temp-box' class='rs-chart-container hidden'>\
                        <div class='title noselect'></div>\
                        <div class='rs-chart-area time-series'>\
                          <div class='rs-y-axis'></div>\
                          <div class='rs-chart'></div>\
                          <div class='rs-y-axis2'></div>\
                          <div class='rs-legend'></div>\
                          <div class='rs-slider'></div>\
                        </div>\
                      </div>\
                      <div id='pressure-box' class='rs-chart-container hidden'>\
                        <div class='title noselect'></div>\
                        <div class='rs-chart-area time-series'>\
                          <div class='rs-y-axis'></div>\
                          <div class='rs-chart'></div>\
                          <div class='rs-y-axis2'></div>\
                          <div class='rs-legend'></div>\
                          <div class='rs-slider'></div>\
                        </div>\
                      </div>\
                      <div id='hws-oat-box' class='rs-chart-container hidden'>\
                        <div class='title noselect'></div>\
                        <div class='rs-chart-area time-series'>\
                          <div class='rs-y-axis'></div>\
                          <div class='rs-chart'></div>\
                          <div class='rs-y-axis2'></div>\
                          <div class='rs-legend'></div>\
                          <div class='rs-slider'></div>\
                        </div>\
                      </div>"));
                    hwplant_ecam(scope.arData[reportElement.table_name]);
                    break;
                }


            });

            //plot title clicked
            $(".rs-chart-container .title").click(function() {
                var plot = $(this).parent().find(".rs-chart-area");
                plot.toggle();
            });
            $("#data").click(function() {
                $("#data").removeClass("active").addClass("active");
                $("#data-content").removeClass("active").addClass("active");
                $("#analysis").removeClass("active");
                $("#analysis-content").removeClass("active");
            });
            $("#analysis").click(function() {
                $("#analysis").removeClass("active").addClass("active");
                $("#analysis-content").removeClass("active").addClass("active");
                $("#data").removeClass("active");
                $("#data-content").removeClass("active");
            });
        }
    };

    function linePlotSVG(data, xLabel, yLabel) {
        // Adapted from http://bl.ocks.org/mbostock/3883245

        var margin = {top: 20, right: 20, bottom: 30, left: 50},
            width = 920 - margin.left - margin.right,
            height = 300 - margin.top - margin.bottom;

        var x = d3.scale.linear().range([0, width]);

        var y = d3.scale.linear().range([height, 0]);

        var xAxis = d3.svg.axis().scale(x).orient('bottom');

        var yAxis = d3.svg.axis().scale(y).orient('left');

        var line = d3.svg.line()
            .x(function(d) { return x(d.x); })
            .y(function(d) { return y(d.y); })
            .interpolate('basis');

        var svg = d3.select(document.createElementNS('http://www.w3.org/2000/svg', 'svg'))
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom);

        var graph = svg.append('g')
            .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

        x.domain(d3.extent(data, function(d) { return d.x; }));
        y.domain(d3.extent(data, function(d) { return d.y; }));

        graph.append('g')
            .attr('class', 'line-plot__axis line-plot__axis--x')
            .attr('transform', 'translate(0,' + height + ')')
            .call(xAxis);

        graph.append('g')
            .attr('class', 'line-plot__axis line-plot__axis--y')
            .call(yAxis)
            .append('text')
            .attr('transform', 'rotate(-90)')
            .attr('y', 6)
            .attr('dy', '.71em')
            .style('text-anchor', 'end')
            .text(yLabel);

        graph.append('path')
            .datum(data)
            .attr('class', 'line-plot__line')
            .attr('d', line);

        return svg[0];
    }

    function barChartSVG(data, xLabel, yLabel) {
        // Adapted from http://bl.ocks.org/mbostock/3885304

        var margin = {top: 20, right: 20, bottom: 30, left: 50},
            width = 920 - margin.left - margin.right,
            height = 300 - margin.top - margin.bottom;

        var x = d3.scale.ordinal().rangeRoundBands([0, width], 0.1);

        var y = d3.scale.linear().range([height, 0]);

        var xAxis = d3.svg.axis()
            .scale(x)
            .orient("bottom");

        var yAxis = d3.svg.axis()
            .scale(y)
            .orient("left");

        var svg = d3.select(document.createElementNS('http://www.w3.org/2000/svg', 'svg'))
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom);

        var graph = svg.append('g')
            .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

        x.domain(data.map(function(d) { return d.x; }));
        y.domain([0, d3.max(data, function(d) { return d.y; })]);

        graph.append("g")
            .attr("class", "bar-chart__axis bar-chart__axis--x")
            .attr("transform", "translate(0," + height + ")")
            .call(xAxis)
            .text(xLabel);

        graph.append("g")
            .attr("class", "bar-chart__axis bar-chart__axis--y")
            .call(yAxis)
            .append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", 6)
            .attr("dy", ".71em")
            .style("text-anchor", "end")
            .text(yLabel);

        graph.selectAll("bar-chart__bar")
            .data(data)
            .enter().append("rect")
            .attr("class", "bar-chart__bar")
            .attr("x", function(d) { return x(d.x); })
            .attr("width", x.rangeBand())
            .attr("y", function(d) { return y(d.y); })
            .attr("height", function(d) { return height - y(d.y); });


        return svg[0];
    }

    function scatterPlotSVG(data, xLabel, yLabel) {
        var margin = {top: 20, right: 20, bottom: 30, left: 40},
            width = 920 - margin.left - margin.right,
            height = 300 - margin.top - margin.bottom;

        /*
         * value accessor - returns the value to encode for a given data object.
         * scale - maps value to a visual display encoding, such as a pixel position.
         * map function - maps from data value to display value
         * axis - sets up axis
         */

        // setup x
        var xValue = function(d) { return d.x;}, // data -> value
            xScale = d3.scale.linear().range([0, width]), // value -> display
            xMap = function(d) { return xScale(xValue(d));}, // data -> display
            xAxis = d3.svg.axis().scale(xScale).orient("bottom");

        // setup y
        var yValue = function(d) { return d.y;}, // data -> value
            yScale = d3.scale.linear().range([height, 0]), // value -> display
            yMap = function(d) { return yScale(yValue(d));}, // data -> display
            yAxis = d3.svg.axis().scale(yScale).orient("left");

        // setup fill color
        var cValue = function(d) { return 0;},
            color = d3.scale.category10();

        // add the graph canvas to the body of the webpage
        var svg = d3.select(document.createElementNS('http://www.w3.org/2000/svg', 'svg'))
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom);

        var graph = svg.append('g')
            .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');
            //replace svg with graph

        // add the tooltip area to the webpage
        var tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);

        // don't want dots overlapping axis, so add in buffer to data domain
        xScale.domain([d3.min(data, xValue)-1, d3.max(data, xValue)+1]);
        yScale.domain([d3.min(data, yValue)-1, d3.max(data, yValue)+1]);

        // x-axis
        graph.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(xAxis)
            .append("text")
            .attr("class", "label")
            .attr("x", width)
            .attr("y", -6)
            .style("text-anchor", "end")
            .text(xLabel);

        // y-axis
        graph.append("g")
            .attr("class", "y axis")
            .call(yAxis)
            .append("text")
            .attr("class", "label")
            .attr("transform", "rotate(-90)")
            .attr("y", 6)
            .attr("dy", ".71em")
            .style("text-anchor", "end")
            .text(yLabel);

        // draw dots
        graph.selectAll(".dot")
            .data(data)
            .enter().append("circle")
            .attr("class", "dot")
            .attr("r", 3.5)
            .attr("cx", xMap)
            .attr("cy", yMap)
            .style("fill", function(d) { return color(cValue(d));})
            .append("svg:title")
            .text(function (d) { return xLabel + ': ' + d.x + '\n' + yLabel + ': ' + d.y; });

        return svg[0];
    }

    function datetimeScatterPlotSVG(data, xLabel, yLabel) {
        var margin = {top: 20, right: 20, bottom: 180, left: 40},
            width = 920 - margin.left - margin.right,
            height = 450 - margin.top - margin.bottom;

        /*
         * value accessor - returns the value to encode for a given data object.
         * scale - maps value to a visual display encoding, such as a pixel position.
         * map function - maps from data value to display value
         * axis - sets up axis
         */

        // setup x
        var xValue = function(d) { return Date.parse(d.x);}, // data -> value
            xScale = d3.time.scale().range([0, width]), // value -> display
            xMap = function(d) { return xScale(xValue(d));}, // data -> display
            xAxis = d3.svg.axis().scale(xScale).orient("bottom").ticks(30);

        // setup y
        var yValue = function(d) { return d.y;}, // data -> value
            yScale = d3.scale.linear().range([height, 0]), // value -> display
            yMap = function(d) { return yScale(yValue(d));}, // data -> display
            yAxis = d3.svg.axis().scale(yScale).orient("left");

        // setup fill color
        var cValue = function(d) { return 0;},
            color = d3.scale.category10();

        // add the graph canvas to the body of the webpage
        var svg = d3.select(document.createElementNS('http://www.w3.org/2000/svg', 'svg'))
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom);

        var graph = svg.append('g')
            .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');
            //replace svg with graph

        // add the tooltip area to the webpage
        var tooltip = d3.select("body").append("div")
            .attr("class", "tooltip")
            .style("opacity", 0);

        // don't want dots overlapping axis, so add in buffer to data domain
        xScale.domain([d3.min(data, xValue)-1, d3.max(data, xValue)+1]);
        yScale.domain([d3.min(data, yValue)-1, d3.max(data, yValue)+1]);

        var formats = [
                // [format, test function] in order of granularity
                ['%Y-%m', function (d) { return d.getMonth(); }],
                ['%Y-%m-%d', function (d) { return d.getDate(); }],
                ['%Y-%m-%d %H:%M', function (d) { return d.getHours(); }],
                ['%Y-%m-%d %H:%M:%S', function (d) { return d.getSeconds(); }]
            ];

        xAxis.tickFormat(d3.time.format('%Y')); // default format
        xScale.ticks.apply(xScale, xAxis.ticks()).forEach(function (tick) {
            while (formats.length && formats[0][1](tick)) {
                // test returned true, update tickFormat
                xAxis.tickFormat(d3.time.format(formats[0][0]));
                // remove format from list
                formats.shift();
            }
        });

        // x-axis
        graph.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + height + ")")
            .call(xAxis)
            .append("text")
            .attr("class", "label")
            .attr("x", width)
            .attr("y", -6)
            .style("text-anchor", "end")
            .text(xLabel);

        graph.selectAll(".x.axis > .tick > text")
            .style("text-anchor", "end")
            .attr("transform", "rotate(-90)")
            .attr("dx", "-.5em")
            .attr("dy", "-.5em");

        // y-axis
        graph.append("g")
            .attr("class", "y axis")
            .call(yAxis)
            .append("text")
            .attr("class", "label")
            .attr("transform", "rotate(-90)")
            .attr("y", 6)
            .attr("dy", ".71em")
            .style("text-anchor", "end")
            .text(yLabel);

        // draw dots
        graph.selectAll(".dot")
            .data(data)
            .enter().append("circle")
            .attr("class", "dot")
            .attr("r", 3.5)
            .attr("cx", xMap)
            .attr("cy", yMap)
            .style("fill", function(d) { return color(cValue(d));})
            .append("svg:title")
            .text(function (d) { return xLabel + ': ' + d.x + '\n' + yLabel + ': ' + d.y; });

        return svg[0];
    }

    function heatMapSVG(data, xLabel, yLabel) {
        // Adapted from http://bl.ocks.org/tjdecke/5558084

        var margin = { top: 50, right: 0, bottom: 100, left: 100 },
            width = 960 - margin.left - margin.right,
            gridSize = Math.floor(width / 24),
            dates = d3.set(data.map(function (d) { return d.y; })).values();
            height = (dates.length + 1) * gridSize,
            legendElementWidth = gridSize*2,
            buckets = 9,
            colors = ["#ffffd9","#edf8b1","#c7e9b4","#7fcdbb","#41b6c4","#1d91c0","#225ea8","#253494","#081d58"]; // alternatively colorbrewer.YlGnBu[9]

        var colorScale = d3.scale.quantile()
            //.domain([buckets, d3.max(data, function (d) { return d.value; })])
            .domain(d3.extent(data, function(d) { return d.z; }))
            .range(colors);

        var svg = d3.select(document.createElementNS('http://www.w3.org/2000/svg', 'svg'))
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom);

        var graph = svg.append('g')
            .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

        var yLabels = graph.selectAll(".yLabel")
            .data(dates)
            .enter().append("text")
            .text(function (d) { return d; })
            .attr("x", 0)
            .attr("y", function (d, i) { return i * gridSize; })
            .style("text-anchor", "end")
            .attr("transform", "translate(-6," + gridSize / 1.5 + ")")
            .attr("class", "yLabel");

        var xLabels = graph.selectAll(".xLabel")
            .data(d3.range(24))
            .enter().append("text")
            .text(function(d) { return d; })
            .attr("x", function(d, i) { return i * gridSize; })
            .attr("y", 0)
            .style("text-anchor", "middle")
            .attr("transform", "translate(" + gridSize / 2 + ", -6)")
            .attr("class", "xLabel");

        var heatMap = graph.selectAll(".value")
            .data(data)
            .enter().append("rect")
            .attr("x", function(d) { return (d.x ) * gridSize; })
            .attr("y", function(d) { return dates.indexOf(d.y) * gridSize; })
            .attr("rx", 4)
            .attr("ry", 4)
            .attr("class", "value bordered")
            .attr("width", gridSize)
            .attr("height", gridSize)
            .style("fill", colors[0]);

        heatMap.transition().duration(1000)
            .style("fill", function(d) { return colorScale(d.z); });

        heatMap.append("title").text(function(d) { return d.z; });

        var legend = graph.selectAll(".legend")
            .data([0].concat(colorScale.quantiles()), function(d) { return d; })
            .enter().append("g")
            .attr("class", "legend");

        legend.append("rect")
            .attr("x", function(d, i) { return legendElementWidth * i; })
            .attr("y", height)
            .attr("width", legendElementWidth)
            .attr("height", gridSize / 2)
            .style("fill", function(d, i) { return colors[i]; });

        legend.append("text")
            .attr("class", "mono")
            .text(function(d) { return "≥ " + Math.round(d); })
            .attr("x", function(d, i) { return legendElementWidth * i; })
            .attr("y", height + gridSize);

        return svg[0];
    }

    function formatDate(d) {
        var dd = d.getDate();
        if (dd<10) dd= '0'+dd;
        var mm = d.getMonth() + 1;  // now moths are 1-12
        if (mm<10) mm= '0'+mm;
        var yy = d.getFullYear();
        return yy +'-' + mm + '-' + dd;
    }

    function formatFullDate(d) {
        var weekday = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
        var dn = weekday[d.getDay()];
        return dn + ' ' + formatDate(d);
    }

    function makeArray(lowEnd, highEnd) {
        var arr = [];
        while(lowEnd <= highEnd){
            arr.push(lowEnd++);
        }
        return arr;
    }

    function padDateTime(val) {
        var dec = val - Math.floor(val);
        val = val - dec;
        return ("0" + val).slice(-2) + dec.toString().substr(1);
    }

    function getTimeUnit(startTime, endTime, timeArr) {
        var dow = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        //var timeUnit = defTimeUnit(d[0][fTsName],d[-1][fTsName],[d[0][fTsName],d[1][fTsName],d[2][fTsName]]);
        //Determine timestamp using timeArr: (end-start)/step
        var stepArr = [];
        var sum = 0;
        for (i=1; i<timeArr.length; i++)
        {
            stepArr[i-1] = (timeArr[i]-timeArr[i-1]);
            sum += stepArr[i-1];
        }
        var step = sum/stepArr.length; //step is second-wise
        var noOfPoints = (endTime-startTime)/step;
        //Return appropirate timeUnit
        var time = new Rickshaw.Fixtures.Time();
        var tickStepInSec = (endTime-startTime)/6; //the width of the plot could hold ~6 tick marks
        //Find a whole-hour number closest to tickStepInSec
        var rickshawTimeUnit = [0.01,0.1,1,15,60,60*15,60*60,60*60*6,86400,86400*7,86400*30.5,86400*365.25,86400*365.25*10];
        var rickshawTime = [{
			name: 'decade',
			seconds: 86400 * 365.25 * 10,
			formatter: function(d) { return (parseInt(d.getUTCFullYear() / 10, 10) * 10) }
		}, {
			name: 'year',
			seconds: 86400 * 365.25,
			formatter: function(d) { return d.getUTCFullYear() }
		}, {
			name: 'month',
			seconds: 86400 * 30.5,
			formatter: function(d) { return (new Rickshaw.Fixtures.Time()).months[d.getUTCMonth()] }
		}, {
			name: 'week',
			seconds: 86400 * 7,
			formatter: function(d) { return (new Rickshaw.Fixtures.Time()).formatDate(d) }
		}, {
			name: 'day',
			seconds: 86400,
			formatter: function(d) {
                //return (new Rickshaw.Fixtures.Time()).formatDate(d);
                return dow[d.getDay()] + ' ' +d.getMonth() +
                    "-" + d.getDate() +
                    "-" + d.getFullYear().toString().substr(2,2);
            }
		}, {
			name: '6 hour',
			seconds: 3600 * 6,
			formatter: function(d) {
                if (d.getHours()==11) {
                    return padDateTime(d.getMonth()) + "-" + padDateTime(d.getDate()) +
                        " " + padDateTime(d.getHours()) + ":" + padDateTime(d.getMinutes());
                }
                return padDateTime(d.getHours()) + ":" + padDateTime(d.getMinutes());

                //return (new Rickshaw.Fixtures.Time()).formatTime(d)
            }
		}, {
			name: 'hour',
			seconds: 3600,
			formatter: function(d) {
                if (d.getHours()==11) {
                    return padDateTime(d.getMonth()) + "-" + padDateTime(d.getDate()) +
                        " " + padDateTime(d.getHours()) + ":" + padDateTime(d.getMinutes());
                }
                return padDateTime(d.getHours()) + ":" + padDateTime(d.getMinutes());

                //return (new Rickshaw.Fixtures.Time()).formatTime(d)
            }
		}, {
			name: '15 minute',
			seconds: 60 * 15,
			formatter: function(d) {
                if (d.getHours()==11) {
                    return padDateTime(d.getMonth()) + "-" + padDateTime(d.getDate()) +
                        " " + padDateTime(d.getHours()) + ":" + padDateTime(d.getMinutes());
                }
                return padDateTime(d.getHours()) + ":" + padDateTime(d.getMinutes());

                //return (new Rickshaw.Fixtures.Time()).formatTime(d)
            }
		}, {
			name: 'minute',
			seconds: 60,
			formatter: function(d) {
                if (d.getHours()==11) {
                    return padDateTime(d.getMonth()) + "-" + padDateTime(d.getDate()) +
                        " " + padDateTime(d.getHours()) + ":" + padDateTime(d.getMinutes());
                }
                return padDateTime(d.getHours()) + ":" + padDateTime(d.getMinutes());

                //return (new Rickshaw.Fixtures.Time()).formatTime(d)
            }
		}, {
			name: '15 second',
			seconds: 15,
			formatter: function(d) { return d.getUTCSeconds() + 's' }
		}, {
			name: 'second',
			seconds: 1,
			formatter: function(d) { return d.getUTCSeconds() + 's' }
		}, {
			name: 'decisecond',
			seconds: 1/10,
			formatter: function(d) { return d.getUTCMilliseconds() + 'ms' }
		}, {
			name: 'centisecond',
			seconds: 1/100,
			formatter: function(d) { return d.getUTCMilliseconds() + 'ms' }
		}];
        var curMinIdx = 0;
        var curMin = 86400*362.25*10;
        for (i=0; i<rickshawTime.length; i++)
        {
             if (Math.abs(tickStepInSec-rickshawTime[i].seconds) < curMin) {
                 curMin = Math.abs(tickStepInSec - rickshawTime[i].seconds);
                 curMinIdx = i;
             }
        }
        var tickStep = rickshawTime[curMinIdx].seconds;
        var formatter = rickshawTime[curMinIdx].formatter;

        var timeUnit = {};
        timeUnit.formatTime = function(d) {
            return formatter(d);
          //return d.toUTCString().match(/(\d+:\d+):/)[1];
        };
        timeUnit.formatter = function(d) { return this.formatTime(d)};
        timeUnit.name = "auto-defined";
        timeUnit.seconds = tickStep;

        return timeUnit;

        //        switch(true) {
//            case (step<0.01): //1/100 sec
//                timeUnit = time.unit('centisecond');
//                break;
//            case (step<0.1): //1/10 sec
//                timeUnit = time.unit('decisecond');
//                break;
//            case (step<1): //1 sec
//                timeUnit = time.unit('second');
//                break;
//            case (step<15): //15 secs
//                timeUnit = time.unit('15 second');
//                break;
//            case (step<60): //1 min
//                timeUnit = time.unit('minute');
//                break;
//            case (step<60*15): //15 min
//                timeUnit = time.unit('15 minute');
//                break;
//            case (step<60*60): //1 hour
//                timeUnit = time.unit('hour');
//                break;
//            case (step<60*60*6): //6 hours
//                timeUnit = time.unit('6 hour');
//                break;
//            case (step<86400): //day
//                timeUnit = time.unit('day');
//                break;
//            case (step<86400*7): //week
//                timeUnit = time.unit('week');
//                break;
//            case (step<86400*30.5): //month
//                timeUnit = time.unit('month');
//                break;
//            case (step<86400*365.25): //year
//                timeUnit = time.unit('year');
//                break;
//            case (step<86400*365.25*10): //decade
//                timeUnit = time.unit('decade');
//                break;
//            default:
//                timeUnit = time.unit('hour');//default
//        }

    }

    function getTimeUnit2(graph)
    {
        var time = new Rickshaw.Fixtures.Time();
        var unit;
        var units = time.units;

        var domain = graph.x.domain();
        var rangeSeconds = domain[1] - domain[0];

        units.forEach( function(u) {
          if (Math.floor(rangeSeconds / u.seconds) >= 2) {
            unit = unit || u;
          }
        } );
        var timeUnit =  (unit || time.units[time.units.length - 1]);
        timeUnit.name = "auto-defined";
        // timeUnit.formatter = function(d) {
        //   return new Date(d * 1000).toLocaleString();
        // };

        return timeUnit;
    }

    function afddAggregateData(inData, legends, diagnosticList) {
        // resData = {
        //      "date": {
        //                      "diagnostic_name": {
        //                                              datetime
        //                                              diagnostic_name:
        //                                              diagnostic_message:
        //                                              energy_impact:
        //                                              color_code:
        //                      }
        //                      state: //combined state of all diagnostics
        //      }
        // }
        // arrData = [{
        //            date: ,
        //            y: ,
        //            state: ,
        //            diagnostic: ,
        //            diagnostic_message: ,
        //            energy_impact: ,
        //            hourly_result: [arrHrData]
        // }]
        // Aggregate & filter duplicated data
        var resData = {};
        inData.forEach(function(d) {
            var diagnostic = d.diagnostic_name;
            if (diagnostic === null) { return; }
            //var dt1 = new Date(d.datetime);
            var dt1 = parseDate(d.datetime);
            //var tsParts = d.datetime.split("T");
            var dateParts = formatDate(dt1); //tsParts[0];
            //var hrParts = dt1.getHours().toString(); //tsParts[1].split(":")[0];
            //var tsParts = d.datetime.split("T");
            //var dateParts = tsParts[0];
            //var hrParts = tsParts[1].split(":")[0];
            var hrParts = dt1.getHours().toString();


            if (dateParts in resData) {
                if (diagnostic in resData[dateParts]) {
                    if (hrParts in resData[dateParts][diagnostic]) {
                        if (legends[d.color_code].state_value >= legends[resData[dateParts][diagnostic][hrParts].color_code].state_value) {
                            resData[dateParts][diagnostic][hrParts] = d;
                        }
                    } else {
                        resData[dateParts][diagnostic][hrParts] = d;
                    }
                } else {
                    resData[dateParts][diagnostic] = {};
                    resData[dateParts][diagnostic][hrParts] = d;
                }
            } else {
                resData[dateParts] = {};
                resData[dateParts][diagnostic] = {};
                resData[dateParts][diagnostic][hrParts] = d;
            }
        });

        var arrData = [];
        // Get Date min & max
        var arrDate = [];
        for (var dt in resData) {
            if (resData.hasOwnProperty(dt)) {
                var dateParts = dt.split("-");
                var tempDate = new Date(dateParts[0], dateParts[1] - 1, dateParts[2], 0, 0, 0, 0);
                arrDate.push(tempDate);
            }
        }
        var domain = d3.extent(arrDate);
        var domainMax = domain[1];
        var domainMin = domain[0];
        var noDays = Math.round(Math.abs((domainMax - domainMin)/(24*60*60*1000)));

        // Convert hash to array and keep only necessary values
        // Fill in default result for hours that have no result
        // ToDo: Push all green to missing dates, missing hours in a daily-green-circle
        // ToDo: Push all grey to missing hours in a daily-one-grey-circle
        for (var numberOfDaysToAdd = 0; numberOfDaysToAdd <= noDays; numberOfDaysToAdd++) {
            var curDate = new Date(domainMin.getTime());
            curDate.setDate(curDate.getDate() + numberOfDaysToAdd);
            var strCurDate = formatDate(curDate);
            if (resData.hasOwnProperty(strCurDate)) {
                for (var i = 0; i< diagnosticList.length; i++) {
                    var energy_impact = "NA";
                    if (resData[strCurDate].hasOwnProperty(diagnosticList[i])) {
                        var arrHrData = [];
                        // Find the state for this date and the default state for missing hours
                        var state = {
                            state: legends["GREY"].string,
                            diagnostic: "",
                            diagnostic_message: legends["GREY"].value,
                            energy_impact: "NA"
                        };
                        for (var hr = 0; hr < 24; hr++) {
                            var iStr = hr.toString();//formatHour(i);
                            if (resData[strCurDate][diagnosticList[i]].hasOwnProperty(iStr)) {
                                if (resData[strCurDate][diagnosticList[i]][iStr].energy_impact != null)
                                    energy_impact = resData[strCurDate][diagnosticList[i]][iStr].energy_impact;
                                if (legends[resData[strCurDate][diagnosticList[i]][iStr].color_code].state_value >=
                                    legends[state.state].state_value) {
                                    state = {
                                        state: resData[strCurDate][diagnosticList[i]][iStr].color_code,
                                        diagnostic: resData[strCurDate][diagnosticList[i]][iStr].diagnostic_name,
                                        diagnostic_message: resData[strCurDate][diagnosticList[i]][iStr].diagnostic_message,
                                        energy_impact: energy_impact
                                    };
                                }
                            }
                        }
                        var defaultStateStr = state.state;
                        if (state.state == legends["RED"].string) {
                            defaultStateStr = legends["GREEN"].string;
                        }
                        // Convert hash to array and fill in missing hours with default values
                        energy_impact = "NA";
                        for (var hr = 0; hr < 24; hr++) {
                            var iStr = hr.toString();//formatHour(i);
                            if (resData[strCurDate][diagnosticList[i]].hasOwnProperty(iStr)) {
                                if (resData[strCurDate][diagnosticList[i]][iStr].energy_impact != null)
                                    energy_impact = resData[strCurDate][diagnosticList[i]][iStr].energy_impact;
                                arrHrData.push({
                                    date: curDate,
                                    y: hr,
                                    state: resData[strCurDate][diagnosticList[i]][iStr].color_code,
                                    diagnostic: resData[strCurDate][diagnosticList[i]][iStr].diagnostic_name,
                                    diagnostic_message: resData[strCurDate][diagnosticList[i]][iStr].diagnostic_message,
                                    energy_impact: energy_impact
                                });
                            } else {
                                arrHrData.push({
                                    date: curDate,
                                    y: hr,
                                    state: defaultStateStr,
                                    diagnostic: "",
                                    diagnostic_message: legends[defaultStateStr].value,
                                    energy_impact: "NA"
                                });
                            }
                        }
                        // Set state for this date-diagnostic
                        arrData.push({
                            date: curDate,
                            y: i,
                            state: state.state,
                            diagnostic: state.diagnostic,
                            diagnostic_message: state.diagnostic_message,
                            energy_impact: state.energy_impact,
                            hourly_result: arrHrData
                        });
                    } else {
                        var arrHrData = [];
                        for (var hr=0; hr<24; hr++) {
                            arrHrData.push({
                                date: curDate,
                                y: hr,
                                state: legends["GREEN"].string,
                                diagnostic: "",
                                diagnostic_message: legends["GREEN"].value,
                                energy_impact: "NA"
                            });
                        }
                        arrData.push({
                            date: curDate,
                            y: i,
                            state: legends["GREEN"].string,
                            diagnostic: "",
                            diagnostic_message: legends["GREEN"].value,
                            energy_impact: "NA",
                            hourly_result: arrHrData
                        });
                    }
                }
            } else {
                for (var i = 0; i< diagnosticList.length; i++) {
                    var arrHrData = [];
                    for (var hr=0; hr<24; hr++) {
                        arrHrData.push({
                            date: curDate,
                            y: hr,
                            state: legends["GREEN"].string,
                            diagnostic: "",
                            diagnostic_message: legends["GREEN"].value,
                            energy_impact: "NA"
                        });
                    }
                    arrData.push({
                        date: curDate,
                        y: i,
                        state: legends["GREEN"].string,
                        diagnostic: "",
                        diagnostic_message: legends["GREEN"].value,
                        energy_impact: "NA",
                        hourly_result: arrHrData
                    });
                }
            }
        }

        return arrData;
    }

    function retroCommissioningAFDDSVG(data,dx_type) {
        var econDiagnosticList = [
            'Temperature Sensor Dx',
            'Not Economizing When Unit Should Dx',
            'Economizing When Unit Should Not Dx',
            'Excess Outdoor-air Intake Dx',
            'Insufficient Outdoor-air Intake Dx'];
        var hwDiagnosticList = [
            'HW Differential Pressure Control Loop Dx',
            'HW Supply Temperature Control Loop Dx',
            'HW loop High Differential Pressure Dx',
            'HW loop Differential Pressure Reset Dx',
            'HW loop High Supply Temperature Dx',
            'HW loop Supply Temperature Reset Dx',
            'HW loop Low Delta-T Dx'];
        var arDiagnosticList = [
            'Duct Static Pressure Set Point Control Loop Dx',
            'Low Duct Static Pressure Dx',
            'High Duct Static Pressure Dx',
            'No Static Pressure Reset Dx',
            'Supply-air Temperature Set Point Control Dx',
            'Low Supply-air Temperature Dx',
            'High Supply-air Temperature Dx',
            'No Supply-air Temperature Reset Dx',
            'Operational Schedule Dx'
        ];

        if (dx_type==1) {
            arDiagnosticList = [
                'Duct Static Pressure Set Point Control Loop Dx',
                'Low Duct Static Pressure Dx',
                'High Duct Static Pressure Dx',
                'No Static Pressure Reset Dx'
            ];
        }
        if (dx_type==2) {
            arDiagnosticList = [
                'Supply-air Temperature Set Point Control Dx',
                'Low Supply-air Temperature Dx',
                'High Supply-air Temperature Dx',
                'No Supply-air Temperature Reset Dx'
            ];
        }
        if (dx_type==3) {
            arDiagnosticList = [
                'Operational Schedule Dx'
            ];
        }

        var diagnosticList = null;
        var foundDiagnosticList = false;
        // For the purpose of deciding which Rcx is running
        for (var i = 0; i < data.length && !foundDiagnosticList; i++) {
            if (econDiagnosticList.indexOf(data[i].diagnostic_name) > -1) {
                diagnosticList = econDiagnosticList;
                foundDiagnosticList = true;
            }
            if (hwDiagnosticList.indexOf(data[i].diagnostic_name) > -1) {
                diagnosticList = hwDiagnosticList;
                foundDiagnosticList = true;
            }
            if (arDiagnosticList.indexOf(data[i].diagnostic_name) > -1) {
                diagnosticList = arDiagnosticList;
                foundDiagnosticList = true;
            }
        }
        if (!foundDiagnosticList) return;

        var containerWidth = 1024; //$(container_class).width();
        var containerHeight = 100 * diagnosticList.length; //$(container_class).height();
        var margin = {top: 40, right: 0, bottom: 150, left: 360}; //margin of the actual plot
        var padding = {top: 30, right: 30, bottom: 50, left: 30}; //padding of the actual plot
        var width = containerWidth - margin.left - margin.right;
        var height = containerHeight - margin.top - margin.bottom;
        if (height < 0) {
            containerHeight = 250;
            height = 80;
        }
        var radius = 8;
        var ref_stroke_clr = "#ccc";
        var format = d3.time.format("%b %d");//d3.time.format("%m/%d/%y");

        var yAxisLabels = diagnosticList;
        var legends = {
            "GREY": {
                value: "No Diagnosis",
                color: "#B3B3B3",
                state_value: 0,
                string: "GREY"
            },
            "GREEN": {
                value: "Normal",
                color: "#509E7A",
                state_value: 1,
                string: "GREEN"
            },
            "RED": {
                value: "Fault",
                color: "#E22400",
                state_value: 2,
                string: "RED"
            }
        };
        var yCategories = yAxisLabels;
        var y2Categories = diagnosticList;
        var svg = d3.select(document.createElementNS('http://www.w3.org/2000/svg', 'svg'))
            .attr("width", containerWidth)
            .attr("height", containerHeight);

        var sample_data = afddAggregateData(data, legends, diagnosticList);
        var xDomain = d3.extent(sample_data, function(d) { return d.date; });
        var items_per_dayCol = yAxisLabels.length;
        var items_per_viewport = 6;
        var inline_padding = Math.floor((width-padding.left-padding.right)/items_per_viewport);
        var plot_width = inline_padding * (sample_data.length/items_per_dayCol);

        var xScale = d3.time.scale()
                .domain(xDomain)
                .range([padding.left, padding.left + plot_width]); //~70
        var yScale = d3.scale.ordinal()
                .domain(yCategories)
                //.rangeRoundBands([0, height], .1);
                .rangePoints([height - padding.top, padding.bottom ]);

        //Create axises
        var xAxis = d3.svg.axis()
                .scale(xScale)
                .orient("bottom")
                .ticks(d3.time.day)
                .tickFormat(format);

        var yAxis = d3.svg.axis()
                    .scale(yScale)
                    .orient("left");

        var zoom = d3.behavior.zoom()
                .scaleExtent([1, 1])
                .on("zoom", zoomed);
        zoom.x(xScale);

        var plot_area = svg
                .append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        plot_area.append("rect")
                .attr("class", "pane")
                .attr("width", width)
                .attr("height", height)
                .call(zoom);

        //Tooltip
        var tip = d3.tip()
            .attr('class', 'd3-tip')
            .offset([-10, 0])
            .html(function(d) {
                return "Date: <strong>" + formatFullDate(d.date) + "</strong><br/>" +
                    "Diagnostic Message: <strong>" + d.diagnostic_message + "</strong>" + "</strong><br/>" +
                    "Energy Impact: <strong>" + d.energy_impact + "</strong>" + "</strong><br/>" +
                    "(Click to see hourly result)<br/>";
            });
        var hrTip = d3.tip()
            .attr('class', 'd3-tip')
            .offset([-10, 0])
            .html(function(d) {
                return "Date: <strong>" + formatFullDate(d.date) + "</strong><br/>" +
                    "Hour: <strong>" + (d.y+1) + "</strong><br/>" +
                    "Diagnostic Message: <strong>" + d.diagnostic_message + "</strong>" + "</strong><br/>" +
                    "Energy Impact: <strong>" + d.energy_impact + "</strong>" + "</strong><br/>";
            });
        plot_area.call(tip);
        plot_area.call(hrTip);

        //Legends
        var legend_svg = svg.append("g")
                .attr("transform", "translate(" + containerWidth/3 + "," + margin.top/3 + ")");
        var legend_width = 324;
        var legend_height = 34;
        var lpadding = 15;
        legend_svg.append("rect")
            .attr("width", legend_width)
            .attr("height", legend_height)
            .attr("x",0)
            .attr("y",0)
            .attr("rx",5)
            .attr("ry",5)
            .style("stroke","#909090")
            .style("stroke-width",1)
            .style("fill","none");

        var lx = lpadding;
        var arrLegends = [];
        for (var k in legends) {
            if (legends.hasOwnProperty(k)) {
                arrLegends.push(legends[k]);
            }
        }

        var litem = legend_svg.selectAll("g")
                .data(arrLegends)
                .enter()
                .append("g")
                .attr("transform", function(d,i) {
                    if (i>0) {
                        var circle_width = radius * 2;
                        var text_width = getTextWidth(arrLegends[i-1].value, "17pt sans-serif");
                        lx += circle_width + text_width;
                    }
                    return "translate("+ lx + "," + legend_height/2 + ")";
                });
        litem.append("circle")
            .attr("cx", 0)
            .attr("cy", 0)
            .attr("r", radius)
            .attr("fill", function(d) {
                return d.color;
            })
            .attr("opacity", 1)
            .on('mouseover', null)
            .on('mouseout', null);
        litem.append("text")
                .attr("x", radius*2+1)
                .attr("y", 0)
                .attr("dy", ".35em")
                .text(function(d) { return d.value; })
                .style("font-size","1em")
                .style("font-family","sans-serif");

        //Draw axises
        var xAxisEle = plot_area.append("g")
            .attr("id", "xAxisEle_AFDD")
            .attr("class", "x axis");
        xAxisEle.attr("clip-path","url(#clip_AFDD)")
            .attr("transform", "translate(0," + (height-5) + ")");

        plot_area.append("g")
            .attr("class", "y axis");

        //Draw y-grid lines for referencing
        plot_area.selectAll("line.y")
                .data(yCategories)
                .enter().append("line")
                .attr("class", "yAxis")
                .attr("x1", 0)
                //.attr("x2", width)
                .attr("x2", plot_width)
                .attr("y1", yScale)
                .attr("y2", yScale)
                .style("stroke", ref_stroke_clr);


        //Clip area
        plot_area.append("clipPath")
                .attr("id", "clip_AFDD")
                .append("rect")
                .attr("x", 0)
                .attr("y", 0)
                .attr("width", width)
                .attr("height", height);

        var radians = 2 * Math.PI, points = 20;
        var angle = d3.scale.linear()
                .domain([0, points-1])
                .range([0, radians]);

        var line = d3.svg.line.radial()
                .interpolate("basis")
                .tension(0)
                .radius(radius)
                .angle(function(d, i) { return angle(i); });

        var clip_area = plot_area.append("g")
                .attr("clip-path","url(#clip_AFDD)");

        clip_area.selectAll("circle")
            .data(sample_data)
            .enter()
            .append("circle")
            .attr("cx", function (d) {
                return xScale(d.date);
            })
            .attr("cy", function (d) {
                return yScale(yCategories[d.y]);
            })
            .attr("r", radius)
            .attr("fill", function(d) {
                return legends[d.state].color;
            })
            .attr("opacity", 1)
            .on('mouseover', tip.show)
            .on('mouseout', tip.hide)
            .on('mousedown', function(d) {
                d3.select("#hrData").remove();
                if (d.diagnostic === "No Supply-air Temperature Reset Dx" ||
                    d.diagnostic === "No Static Pressure Reset Dx" ||
                    (d.diagnostic === "Operational Schedule Dx"
                        && d.diagnostic_message === "Supply fan is operating excessively during unoccupied times.") ||
                    d.diagnostic === "") {
                    return;
                }

                var rectWidth = 24;
                var yDomainData = makeArray(1,24);
                var hrScale = d3.scale.ordinal()
                        .domain(yDomainData)
                        .rangeRoundBands([0, 24*rectWidth]);
                var hrAxis = d3.svg.axis()
                        .scale(hrScale)
                        .orient("bottom");
                var drawPosition = margin.left + 40;

                var hrDataArea = svg
                    .append("g")
                    .attr("id", "hrData")
                    .attr("width", 24*rectWidth)
                    .attr("height", rectWidth)
                    .attr("transform", "translate(0," + (height+100) + ")");

                hrDataArea.append("g")
                    .attr("class", "x axis")
                    .attr("transform", "translate(" + drawPosition + ","+ (rectWidth) +")")
                    .call(hrAxis);

                var hrLabelArea = hrDataArea.append("g")
                    .attr("class", "axis");
                hrLabelArea.append("text")
                    .attr("x", 80)
                    .attr("y", rectWidth-7)
                    .text(diagnosticList[d.y]);
                hrLabelArea.append("text")
                    .attr("x", 80)
                    .attr("y", rectWidth+20)
                    .text('(' + formatFullDate(d.date) + ')');

                hrDataArea.selectAll("rect")
                .data(d.hourly_result)
                .enter()
                .append("rect")
                .attr("x", function (d) {
                    return d.y*rectWidth + drawPosition;
                })
                .attr("y", 0)
                .attr("width", rectWidth)
                .attr("height", rectWidth)
                .attr("fill", function(d) {
                    return legends[d.state].color;
                })
                .attr("opacity", 1)
                .style({"stroke-width": 1, "stroke": "black"})
                .on('mouseover', hrTip.show)
                .on('mouseout', hrTip.hide);
            });
        zoomed();

        return svg[0];

        function zoomed() {
            plot_area.select("g.x.axis").call(xAxis);
            plot_area.select("g.y.axis").call(yAxis);
            //plot_area.select("g.y2.axis").call(yAxis2);

            clip_area.selectAll("circle").attr("cx", function(d) {
                var value = xScale(d.date);
                if (value < 0) value = -10000;
                //if (value > width) value = 10000;
                return value;
            });
        }

        function getTextWidth(text, font) {
            // re-use canvas object for better performance
            var canvas = getTextWidth.canvas || (getTextWidth.canvas = document.createElement("canvas"));
            var context = canvas.getContext("2d");
            context.font = font;
            var metrics = context.measureText(text);
            return metrics.width;
        };
    }

    function existPoint(p, points) {
        if (points.hasOwnProperty(p)) {
            return true;
        }
        return false;
        //return p != '' ? true : false;
    }

    function startWith(str, substr) {
        if (str.substring(0, substr.length+3) === substr+"___"){
            return true;
        }
        return false;
    }

    function existPointStartWith(p, points) {
        for (var point in points) {
            if (points.hasOwnProperty(point)) {
                if (startWith(point, p)) {
                    return true;
                }
            }
        }
        return false;
    }

    function labelX(text) {
        text = typeof text !== 'undefined' ? text : 'Temperature';
        var obj = {
            text: text,
            color: 'black',
            opacity: 0.5,
            fontSize: '12px',
            offsetX: '18.5em',
            offsetY: '30em'
        };
        return obj;
    }

    function labelY1(text) {
        text = typeof text !== 'undefined' ? text : 'Temperature';
        var obj = {
            text: text,
            color: 'black',
            opacity: 0.5,
            fontSize: '12px',
            offsetX: '0.8em',
            offsetY: '-8.5em'
        };
        return obj;
    }

    function labelY2(text) {
        text = typeof text !== 'undefined' ? text : 'Command/Status';
        var obj = {
            text: text,
            color: 'black',
            opacity: 0.5,
            fontSize: '12px',
            offsetX: '3em',
            offsetY: '-8em'
        };
        return obj;
    }

    function parseDataType(d, points, counts) {
        for (var key in points) {
            if (points.hasOwnProperty(key)) {
                if (d[points[key]] == null) {
                    delete d[points[key]];
                } else {
                    d[points[key]] = parseFloat(d[points[key]]);
                    counts[key] += 1;
                }
            }
        }
    }

    function parseDate(s) {
        var a = s.split(/[^0-9]/);
        return new Date (a[0],a[1]-1,a[2],a[3],a[4],a[5] );
    }

    function getColor(c) {
        //object to contain definition for point colors
        //http://www.w3schools.com/html/html_colornames.asp
        var arr = ["Blue","BlueViolet","Brown","BurlyWood","CadetBlue","DarkGray","DarkGrey",
            "DarkGreen","DarkKhaki","Magenta","Green","Red","Chocolate","HotPink","LightPink",
            "Gainsboro","AliceBlue","AntiqueWhite","Aqua","Aquamarine","Azure","Beige",
            "Bisque","Black","BlanchedAlmond","Chartreuse","Coral","CornflowerBlue","Cornsilk",
            "Crimson","Cyan","DarkBlue","DarkCyan","DarkGoldenRod","DarkMagenta","DarkOliveGreen",
            "Darkorange","DarkOrchid","DarkRed","DarkSalmon","DarkSeaGreen","DarkSlateBlue",
            "DarkSlateGray","DarkSlateGrey","DarkTurquoise","DarkViolet","DeepPink","DeepSkyBlue",
            "DimGray","DimGrey","DodgerBlue","FireBrick",
            "FloralWhite","ForestGreen","Fuchsia","GhostWhite","Gold","GoldenRod","Gray","Grey",
            "GreenYellow","HoneyDew","IndianRed","Indigo","Ivory","Khaki","Lavender",
            "LavenderBlush","LawnGreen","LemonChiffon","LightBlue","LightCoral","LightCyan",
            "LightGoldenRodYellow","LightGray","LightGrey","LightGreen","LightSalmon",
            "LightSeaGreen","LightSkyBlue","LightSlateGray","LightSlateGrey","LightSteelBlue","LightYellow",
            "Lime","LimeGreen","Linen","Maroon","MediumAquaMarine","MediumBlue","MediumOrchid",
            "MediumPurple","MediumSeaGreen","MediumSlateBlue","MediumSpringGreen","MediumTurquoise",
            "MediumVioletRed","MidnightBlue","MintCream","MistyRose","Moccasin","NavajoWhite","Navy",
            "OldLace","Olive","OliveDrab",
            "Orange","OrangeRed","Orchid","PaleGoldenRod","PaleGreen","PaleTurquoise","PaleVioletRed",
            "PapayaWhip","PeachPuff","Peru","Pink","Plum","PowderBlue","Purple","RosyBrown",
            "RoyalBlue","SaddleBrown","Salmon","SandyBrown","SeaGreen","SeaShell","Sienna","Silver",
            "SkyBlue","SlateBlue","SlateGray","SlateGrey","Snow","SpringGreen","SteelBlue","Tan","Teal",
            "Thistle","Tomato","Turquoise","Violet","Wheat","White","WhiteSmoke","Yellow","YellowGreen"];
        return arr[c];
    }

    function setUndefinedToNull(val)
    {
        return (typeof val === 'undefined') ? null : val;
    }

    function economizer_rcx(data) {
        //console.log(data);
        var rawTsName = 'datetime';

        //object to contain definition for points
        var allPoints = {
            //OATemp: 'OATemp',
            OAF: 'OutdoorAirFraction',
            OATemp: 'OutdoorAirTemperature',
            MATemp: 'MixedAirTemperature',
            RATemp: 'ReturnAirTemperature',
            DATemp: 'DischargeAirTemperature',
            DATempSetPoint: 'DischargeAirTemperatureSetPoint',
            OADamper: 'OutdoorDamper',
            CCValve: 'CCV',
            HCValve: 'HCV'
        };
        counts = {};
        points = {}; //Points actually used for visualization
        for (var prop in allPoints) {
            counts[prop] = 0;
            points[prop] = allPoints[prop];
        }

        //object to contain definition for point colors
        //http://www.w3schools.com/html/html_colornames.asp
        var colors = {
            OATemp: 'blue',
            MATemp: 'pink',
            RATemp: 'red',
            DATemp: 'green',
            OADamper: 'brown',
            OAF: 'blueviolet',
            CCValve: 'darkorange',
            HCValve: 'darkorchid',
            DATempSetPoint: 'darkred'
        };

        function plotTempsChart(data, allPoints, points, colors, args) {
            //Set UI Args
            var timeUnit = args.TimeUnit;
            var container = args.Container;
            var chartId = container + " .rs-chart";
            var chartY = container + " .rs-y-axis";
            var chartY2 = container + " .rs-y-axis2";
            var chartLegend = container + " .rs-legend";
            var chartTitle = container + " .title";
            var chartSlider = container + " .rs-slider";
            document.querySelector(chartTitle).innerHTML = args.Title;

            //if (!(existPoint(rawTsName) && existPoint(points.OATemp)
            if (!(existPoint('OATemp', points) && existPoint('MATemp', points)))
            {
                $(container).find(".rs-chart-area").toggle();
                return false;
            }

            //TODO: Change the min max of y1Scale
            var y1Scale = d3.scale.linear().domain([0, 100]);
            var y2Scale = d3.scale.linear().domain([0, 300]);
            //Set up data series: change this for different data sources

            var ySeries = {};
            if (existPoint('OATemp', points)) {
                ySeries['OATemp'] = {
                    name: 'Outdoor Air Temperature',
                    color: colors.OATemp,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: setUndefinedToNull(d[points.OATemp])};
                    }),
                    scale: y1Scale
                }
            }
            if (existPoint('MATemp', points)) {
                ySeries['MATemp'] = {
                    name: 'Mixed Air Temperature',
                    color: colors.MATemp,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: setUndefinedToNull(d[points.MATemp])};
                    }),
                    scale: y1Scale
                }
            }
            if (existPoint('RATemp', points)) {
                ySeries['RATemp'] = {
                    name: 'Return Air Temperature',
                    color: colors.RATemp,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: setUndefinedToNull(d[points.RATemp])};
                    }),
                    scale: y1Scale
                }
            }
            if (existPoint('OAF', points)) {
                ySeries['OAF'] = {
                    name: 'Outdoor Air Fraction',
                    color: colors.OAF,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: setUndefinedToNull(d[points.OAF])};
                    }),
                    scale: y2Scale
                }
            }

            if (existPoint('DATemp', points)) {
                ySeries['DATemp'] = {
                    name: 'Discharge Air Temperature',
                    color: colors.DATemp,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: setUndefinedToNull(d[points.DATemp])};
                    }),
                    scale: y1Scale
                }
            }
            if (existPoint('OADamper', points)) {
                ySeries['OADamper'] = {
                    name: 'Outdoor Damper Signal',
                    color: colors.OADamper,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: setUndefinedToNull(d[points.OADamper])};
                    }),
                    scale: y2Scale
                }
            }
            //Plotting
//          var plotSeries = ySeries.map(function(value, index) {
//            return [value];
//          });
            var plotSeries = [];
            angular.forEach(ySeries, function (value, key) {
                plotSeries.push(value);
            });
            var graph = new Rickshaw.Graph({
                element: document.querySelector(chartId),
                renderer: 'line',
                series: plotSeries,
                interpolation: 'linear'
            });
            graph.render();

            //Tooltip for hovering
//            var hoverDetail = new Rickshaw.Graph.HoverDetail({
//                graph: graph,
//                formatter: function (series, x, y) {
//                    var date = '<span class="date">' + new Date(x * 1000).toUTCString() + '</span>';
//                    var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
//                    var content = swatch + series.name + ": " + parseFloat(y).toFixed(2) + '<br>' + date;
//                    return content;
//                }
//            });
            //Display & Toggle Legends
            var legend = new Rickshaw.Graph.Legend({
                graph: graph,
                element: document.querySelector(chartLegend)
            });
            var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
                graph: graph,
                legend: legend
            });
            //Render X Y Axes
            //var xAxis = new Rickshaw.Graph.Axis.Time({
            //  graph: graph,
            //  timeUnit: unit
            //});
            //var time = new Rickshaw.Fixtures.Time();
            //var timeUnit = time.unit('hour');
            var xAxis = new Rickshaw.Graph.Axis.ExtendedTime(
                {
                    graph: graph,
                    //tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                    pixelsPerTick: 50,
                    tickSpacing: 6 * 60 * 60, // 6 hours
                    timeUnit: timeUnit
                });
            xAxis.render();
            var yAxis = new Rickshaw.Graph.Axis.Y.Scaled({
                graph: graph,
                berthRate: 0.0,
                orientation: 'left',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY),
                scale: y1Scale,
                label: labelY1()
            });
            yAxis.render();

            var yAxis2 = new Rickshaw.Graph.Axis.Y.Scaled({
                graph: graph,
                berthRate: 0,
                orientation: 'right',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY2),
                scale: y2Scale,
                ticks: 5,
                label: labelY2()
                //tickValues: [0,20,40,60,80,100]
            });
            yAxis2.render();

            var slider = new Rickshaw.Graph.RangeSlider.Preview({
                graph: graph,
                element: document.querySelector(chartSlider)
            });

            //graph.render();


            //There is another way to give more granular control over Y axis: using scale that is ~ d3
            //This way you can control the stick on the X or Y Axis
            //new Rickshaw.Graph.Axis.Y.Scaled( {
            //  graph: graph,
            //  orientation: 'right',
            //  tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
            //  element: document.getElementById('y_axis_2'),
            //  scale: linearScale,
            //  grid: false
            //} );

        }

        function plotHCVChart(data, allPoints, points, colors, args) {
            //Set UI Args
            var timeUnit = args.TimeUnit;
            var container = args.Container;
            var chartId = container + " .rs-chart";
            var chartY = container + " .rs-y-axis";
            var chartY2 = container + " .rs-y-axis2";
            var chartLegend = container + " .rs-legend";
            var chartTitle = container + " .title";
            var chartSlider = container + " .rs-slider";
            document.querySelector(chartTitle).innerHTML = args.Title;

            //if (!(existPoint(rawTsName) && existPoint(points.OATemp)
            if (!(existPoint('OATemp', points)
                && existPoint('DATemp', points)))
            {
                $(container).find(".rs-chart-area").toggle();
                return false;
            }
//          if (!(existPoint(points.DATempSetPoint)
//              || existPoint(points.CCValve)
//              || existPoint(points.HCValve)
//              || existPoint(points.OADamper))) return false;

            //TODO: Change the min max of y1Scale
            var y1Scale = d3.scale.linear().domain([0, 100]);
            var y2Scale = d3.scale.linear().domain([0, 300]);
            //Set up data series: change this for different data sources

            var ySeries = {};
            if (existPoint('OATemp', points)) {
                ySeries['OATemp'] = {
                    name: 'Outdoor Air Temperature',
                    color: colors.OATemp,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: setUndefinedToNull(d[points.OATemp])};
                    }),
                    scale: y1Scale
                }
            }
            if (existPoint('DATemp', points)) {
                ySeries['DATemp'] = {
                    name: 'Discharge Air Temperature',
                    color: colors.DATemp,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: setUndefinedToNull(d[points.DATemp])};
                    }),
                    scale: y1Scale
                }
            }
            if (existPoint('DATempSetPoint', points)) {
                ySeries['DATempSetPoint'] = {
                    name: 'Discharge Air Temperature Set Point',
                    color: colors.DATempSetPoint,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: setUndefinedToNull(d[points.DATempSetPoint])};
                    }),
                    scale: y1Scale
                }
            }
            if (existPoint('OADamper', points)) {
                ySeries['OADamper'] = {
                    name: 'Outdoor Damper Signal',
                    color: colors.OADamper,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: setUndefinedToNull(d[points.OADamper])};
                    }),
                    scale: y2Scale
                }
            }
            if (existPoint('CCValve', points)) {
                ySeries['CCValve'] = {
                    name: 'Cooling Coil Valve Position',
                    color: colors.CCValve,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: setUndefinedToNull(d[points.CCValve])};
                    }),
                    scale: y2Scale
                }
            }
            if (existPoint('HCValve', points)) {
                ySeries['HCValve'] = {
                    name: 'Heating Coil Valve Position',
                    color: colors.HCValve,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: setUndefinedToNull(d[points.HCValve])};
                    }),
                    scale: y2Scale
                }
            }
            //Plotting
//          var plotSeries = ySeries.map(function(value, index) {
//            return [value];
//          });
            var plotSeries = [];
            angular.forEach(ySeries, function (value, key) {
                plotSeries.push(value);
            });
            var graph = new Rickshaw.Graph({
                element: document.querySelector(chartId),
                renderer: 'line',
                series: plotSeries,
                interpolation: 'linear'
            });
            graph.render();

            //Tooltip for hovering
//            var hoverDetail = new Rickshaw.Graph.HoverDetail({
//                graph: graph,
//                formatter: function (series, x, y) {
//                    var date = '<span class="date">' + new Date(x * 1000).toUTCString() + '</span>';
//                    var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
//                    var content = swatch + series.name + ": " + parseFloat(y).toFixed(2) + '<br>' + date;
//                    return content;
//                }
//            });
            //Display & Toggle Legends
            var legend = new Rickshaw.Graph.Legend({
                graph: graph,
                element: document.querySelector(chartLegend)
            });
            var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
                graph: graph,
                legend: legend
            });
            //Render X Y Axes
            //var xAxis = new Rickshaw.Graph.Axis.Time({
            //  graph: graph,
            //  timeUnit: unit
            //});
            //var time = new Rickshaw.Fixtures.Time();
            //var timeUnit = time.unit('hour');
            var xAxis = new Rickshaw.Graph.Axis.ExtendedTime({
                graph: graph,
                //tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                pixelsPerTick: 50,
                tickSpacing: 6 * 60 * 60, // 1 hour
                timeUnit: timeUnit
            });
            xAxis.render();
            var yAxis = new Rickshaw.Graph.Axis.Y.Scaled({
                graph: graph,
                berthRate: 0.0,
                orientation: 'left',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY),
                scale: y1Scale,
                label: labelY1()
            });
            yAxis.render();

            var yAxis2 = new Rickshaw.Graph.Axis.Y.Scaled({
                graph: graph,
                berthRate: 0,
                orientation: 'right',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY2),
                scale: y2Scale,
                ticks: 5,
                label: labelY2()
                //tickValues: [0,20,40,60,80,100]
            });
            yAxis2.render();

            var slider = new Rickshaw.Graph.RangeSlider.Preview({
                graph: graph,
                element: document.querySelector(chartSlider)
            });
        }

        function plotMaOaTempChart(data, allPoints, points, colors, args) {
            //Set UI Args
            var container = args.Container;
            var chartId = container + " .rs-chart";
            var chartY = container + " .rs-y-axis";
            var chartLegend = container + " .rs-legend";
            var chartTitle = container + " .title";
            document.querySelector(chartTitle).innerHTML = args.Title;

            if (!(existPoint('MATemp', points) && existPoint('OATemp', points)))
            {
                $(container).find(".rs-chart-area").toggle();
                return false;
            }

            //Set up data series: change this for different data sources
            data.sort(function (a, b) {
                if (a[allPoints.OATemp] < b[allPoints.OATemp])
                    return -1;
                if (a[allPoints.OATemp] > b[allPoints.OATemp])
                    return 1;
                return 0;
            });
            var ySeries = {
                MAOAT: {
                    name: allPoints.MATemp,
                    xName: allPoints.OATemp,
                    color: colors.MATemp,
                    data: data.map(function (d) {
                        return {x: d[points.OATemp], y: setUndefinedToNull(d[points.MATemp])};
                    })
                }
            }
            //Plotting
            var graph = new Rickshaw.Graph({
                element: document.querySelector(chartId),
                renderer: 'scatterplot',
                series: [ySeries.MAOAT]
            });
            graph.renderer.dotSize = 2;
            graph.render();
            //Tooltip for hovering
//            var hoverDetail = new Rickshaw.Graph.HoverDetail({
//                graph: graph,
//                formatter: function (series, x, y) {
//                    var xValue = '<span style="padding-right:50px;">' + series.xName + ": " + parseFloat(x) + '</span>';
//                    var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
//                    var content = swatch + series.name + ": " + parseFloat(y) + '<br>' + xValue;
//                    return content;
//                }
//            });
            //Display & Toggle Legends
            var legend = new Rickshaw.Graph.Legend({
                graph: graph,
                element: document.querySelector(chartLegend)
            });
            var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
                graph: graph,
                legend: legend
            });
            //Render X Y Axes
            var xAxis = new Rickshaw.Graph.Axis.X({
                graph: graph,
                label: labelX('Outdoor Temperature')
            });
            xAxis.render();
            var yAxis = new Rickshaw.Graph.Axis.Y({
                graph: graph,
                berthRate: 0.0,
                orientation: 'left',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY),
                label: labelY1('Mixed-Air Temperature')
            });
            yAxis.render();


        }

        var fTsName = 'FTimestamp';
        data = parseSortByTimestamp(data, rawTsName, fTsName, points, counts);
        //Delete key in points that have no data
        for (var prop in counts) {
            if (counts[prop] == 0) {
                delete points[prop];
            }
        }

        var timeUnit = getTimeUnit(data[0][fTsName], data[data.length - 1][fTsName], [data[0][fTsName], data[1][fTsName], data[2][fTsName]]);
        var tArgs = {
            Timestamp: fTsName,
            Title: 'AHU Economizer Performance Evaluation',
            Container: '#temps-chart-box',
            TimeUnit: timeUnit
        };
        plotTempsChart(data, allPoints, points, colors, tArgs);
        var hcvArgs = {
            Timestamp: fTsName,
            Title: 'AHU Discharge Cooling and Economizer Performance Analysis',
            Container: '#hcv-box',
            TimeUnit: timeUnit
        };
        plotHCVChart(data, allPoints, points, colors, hcvArgs);
        //Plot this one last because it sorts the data in-place
        var motArgs = {
            Timestamp: fTsName,
            Title: 'Seasonal AHU Mixed Air Temperature Response Analysis',
            Container: '#mat-oat-box'
        };
        plotMaOaTempChart(data, allPoints, points, colors, motArgs);


        $(".rs-chart-container.hidden").removeClass("hidden");
        //Fix styling of D3: when the min value is at the bottom of the Y axis, we can see only upper half of the value
        //$('.rickshaw_graph .y_ticks text').attr('dy', '0');

    }

    function ahu_ecam(data) {
        //console.log(data);
        var rawTsName = 'datetime';

        //object to contain definition for points
        var allPoints = { //all points available in the output_format from backend
            OutdoorAirTemperature: 'OutdoorAirTemperature',
            MixedAirTemperature: 'MixedAirTemperature',
            ReturnAirTemperature: 'ReturnAirTemperature',
            DischargeAirTemperature: 'DischargeAirTemperature',
            DischargeAirTemperatureSetPoint: 'DischargeAirTemperatureSetPoint',
            SupplyFanStatus: 'SupplyFanStatus',
            SupplyFanSpeed: 'SupplyFanSpeed',
            OutdoorDamper: 'OutdoorDamper',
            CCV: 'CCV',
            HCV: 'HCV',
            OutdoorAirFraction: 'OutdoorAirFraction',
            ReturnFanSpeed: 'ReturnFanSpeed',
            OccupancyMode: 'OccupancyMode',
            DuctStaticPressure: 'DuctStaticPressure',
            DuctStaticPressureSetPoint: 'DuctStaticPressureSetPoint'
        };
        counts = {};
        points = {}; //Points actually used for visualization
        for (var prop in allPoints) {
            counts[prop] = 0;
            points[prop] = allPoints[prop];
        }

        //object to contain definition for point colors
        //http://www.w3schools.com/html/html_colornames.asp
        var colors = {
            OutdoorAirTemperature: 'blue',
            MixedAirTemperature: 'LightPink',
            ReturnAirTemperature: 'HotPink',
            DischargeAirTemperature: 'Gainsboro',
            DischargeAirTemperatureSetPoint: 'DarkKhaki',
            SupplyFanStatus: 'BurlyWood',
            SupplyFanSpeed: 'Chocolate',
            OutdoorDamper: 'blueviolet',
            CCV: 'Green',
            HCV: 'Red',
            OutdoorAirFraction: 'DarkBlue',
            ReturnFanSpeed: 'CadetBlue',
            OccupancyMode: 'Brown',
            DuctStaticPressure: 'Magenta',
            DuctStaticPressureSetPoint: 'DarkMagenta'
        };

        function plotOAChart1(data, allPoints, points, colors, args) {
            //Set UI Args
            var timeUnit = args.TimeUnit;
            var container = args.Container;
            var chartId = container + " .rs-chart";
            var chartY = container + " .rs-y-axis";
            var chartY2 = container + " .rs-y-axis2";
            var chartLegend = container + " .rs-legend";
            var chartTitle = container + " .title";
            var chartSlider = container + " .rs-slider";
            document.querySelector(chartTitle).innerHTML = args.Title;

            //if (!(existPoint(rawTsName, points) && existPoint(allPoints.ZoneTemp, points))) return false;
            if (!existPoint('OutdoorAirTemperature', points) &&
                !existPoint('OutdoorDamper', points))
            {
                $(container).find(".rs-chart-area").toggle();
                return false;
            }

            //TODO: Change the min max of y1Scale
            var y1Scale = d3.scale.linear().domain([0, 200]);
            var y2Scale = d3.scale.linear().domain([0, 100]);
            //Set up data series: change this for different data sources

            var ySeries = {};
            if (existPoint('OutdoorAirTemperature', points)) {
                ySeries['OutdoorAirTemperature'] = {
                    name: 'Outdoor Air Temperature',
                    color: colors.OutdoorAirTemperature,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.OutdoorAirTemperature]};
                    }),
                    scale: y1Scale
                }
            }
            if (existPoint('OutdoorAirFraction', points)) {
                ySeries['OutdoorAirFraction'] = {
                    name: points.OutdoorAirFraction,
                    color: colors.OutdoorAirFraction,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.OutdoorAirFraction]};
                    }),
                    scale: y2Scale
                }
            }
            if (existPoint('OutdoorDamper', points)) {
                ySeries['OutdoorDamper'] = {
                    name: 'Outdoor Damper Signal',
                    color: colors.OutdoorDamper,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.OutdoorDamper]};
                    }),
                    scale: y2Scale
                }
            }
            if (existPoint('OccupancyMode', points)) {
                ySeries['OccupancyMode'] = {
                    name: 'Occupancy Mode',
                    color: colors.OccupancyMode,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.OccupancyMode]};
                    }),
                    scale: y2Scale
                }
            }
            //Plotting
            var plotSeries = [];
            angular.forEach(ySeries, function (value, key) {
                plotSeries.push(value);
            });
            var graph = new Rickshaw.Graph({
                element: document.querySelector(chartId),
                renderer: 'line',
                series: plotSeries,
                interpolation: 'linear'
            });
            graph.render();

            //Tooltip for hovering
//            var hoverDetail = new Rickshaw.Graph.HoverDetail({
//                graph: graph,
//                formatter: function (series, x, y) {
//                    var date = '<span class="date">' + new Date(x * 1000).toUTCString() + '</span>';
//                    var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
//                    var content = swatch + series.name + ": " + parseFloat(y).toFixed(2) + '<br>' + date;
//                    return content;
//                }
//            });
            //Display & Toggle Legends
            var legend = new Rickshaw.Graph.Legend({
                graph: graph,
                element: document.querySelector(chartLegend)
            });
            var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
                graph: graph,
                legend: legend
            });
            //Render X Y Axes
            var xAxis = new Rickshaw.Graph.Axis.ExtendedTime(
                {
                    graph: graph,
                    orientation: "bottom",
                    //tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                    pixelsPerTick: 50,
                    tickSpacing: 6 * 60 * 60, // 6 hours
                    timeUnit: timeUnit

                });
            xAxis.render();
            var yAxis = new Rickshaw.Graph.Axis.Y.Scaled({
                graph: graph,
                berthRate: 0.0,
                orientation: 'left',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY),
                scale: y1Scale,
                label: labelY1()
            });
            yAxis.render();

            var yAxis2 = new Rickshaw.Graph.Axis.Y.Scaled({
                graph: graph,
                berthRate: 0,
                orientation: 'right',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY2),
                scale: y2Scale,
                ticks: 5,
                label: labelY2()
                //tickValues: [0,20,40,60,80,100]
            });
            yAxis2.render();

            var slider = new Rickshaw.Graph.RangeSlider.Preview({
                graph: graph,
                element: document.querySelector(chartSlider)
            });

        }
        function plotSPChart1(data, allPoints, points, colors, args) {
            //Set UI Args
            var timeUnit = args.TimeUnit;
            var container = args.Container;
            var chartId = container + " .rs-chart";
            var chartY = container + " .rs-y-axis";
            var chartY2 = container + " .rs-y-axis2";
            var chartLegend = container + " .rs-legend";
            var chartTitle = container + " .title";
            var chartSlider = container + " .rs-slider";
            document.querySelector(chartTitle).innerHTML = args.Title;

            //if (!(existPoint(rawTsName, points) && existPoint(allPoints.ZoneTemp, points))) return false;
            if (!existPoint('DuctStaticPressure', points) &&
                !existPoint('DuctStaticPressureSetPoint', points) &&
                !existPoint('SupplyFanSpeed', points))
            {
                $(container).find(".rs-chart-area").toggle();
                return false;
            }

            //TODO: Change the min max of y1Scale
            var y1Scale = d3.scale.linear().domain([0, 100]);
            var y2Scale = d3.scale.linear().domain([0, 200]);
            //Set up data series: change this for different data sources

            var ySeries = {};
            if (existPoint('DuctStaticPressure', points)) {
                ySeries['DuctStaticPressure'] = {
                    name: 'Duct Static Pressure',
                    color: colors.DuctStaticPressure,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.DuctStaticPressure]};
                    }),
                    scale: y1Scale
                }
            }
            if (existPoint('DuctStaticPressureSetPoint', points)) {
                ySeries['DuctStaticPressureSetPoint'] = {
                    name: 'Duct Static Pressure Set Point',
                    color: colors.DuctStaticPressureSetPoint,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.DuctStaticPressureSetPoint]};
                    }),
                    scale: y2Scale
                }
            }
            if (existPoint('SupplyFanSpeed', points)) {
                ySeries['SupplyFanSpeed'] = {
                    name: 'Supply Fan Speed',
                    color: colors.SupplyFanSpeed,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.SupplyFanSpeed]};
                    }),
                    scale: y2Scale
                }
            }
            //Plotting
            var plotSeries = [];
            angular.forEach(ySeries, function (value, key) {
                plotSeries.push(value);
            });
            var graph = new Rickshaw.Graph({
                element: document.querySelector(chartId),
                renderer: 'line',
                series: plotSeries,
                interpolation: 'linear'
            });
            graph.render();

            //Tooltip for hovering
//            var hoverDetail = new Rickshaw.Graph.HoverDetail({
//                graph: graph,
//                formatter: function (series, x, y) {
//                    var date = '<span class="date">' + new Date(x * 1000).toUTCString() + '</span>';
//                    var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
//                    var content = swatch + series.name + ": " + parseFloat(y).toFixed(2) + '<br>' + date;
//                    return content;
//                }
//            });
            //Display & Toggle Legends
            var legend = new Rickshaw.Graph.Legend({
                graph: graph,
                element: document.querySelector(chartLegend)
            });
            var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
                graph: graph,
                legend: legend
            });
            //Render X Y Axes
            var xAxis = new Rickshaw.Graph.Axis.ExtendedTime(
                {
                    graph: graph,
                    orientation: "bottom",
                    //tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                    pixelsPerTick: 50,
                    tickSpacing: 6 * 60 * 60, // 6 hours
                    timeUnit: timeUnit

                });
            xAxis.render();
            var yAxis = new Rickshaw.Graph.Axis.Y.Scaled({
                graph: graph,
                berthRate: 0.0,
                orientation: 'left',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY),
                scale: y1Scale,
                label: labelY1('Pressure')
            });
            yAxis.render();

            var yAxis2 = new Rickshaw.Graph.Axis.Y.Scaled({
                graph: graph,
                berthRate: 0,
                orientation: 'right',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY2),
                scale: y2Scale,
                ticks: 5,
                label: labelY2()
                //tickValues: [0,20,40,60,80,100]
            });
            yAxis2.render();

            var slider = new Rickshaw.Graph.RangeSlider.Preview({
                graph: graph,
                element: document.querySelector(chartSlider)
            });

        }
        function plotCoilChart1(data, allPoints, points, colors, args) {
            //Set UI Args
            var timeUnit = args.TimeUnit;
            var container = args.Container;
            var chartId = container + " .rs-chart";
            var chartY = container + " .rs-y-axis";
            var chartY2 = container + " .rs-y-axis2";
            var chartLegend = container + " .rs-legend";
            var chartTitle = container + " .title";
            var chartSlider = container + " .rs-slider";
            document.querySelector(chartTitle).innerHTML = args.Title;

            //if (!(existPoint(rawTsName, points) && existPoint(allPoints.ZoneTemp, points))) return false;
            if (!existPoint('CCV', points) &&
                !existPoint('HCV', points) &&
                !existPoint('OutdoorAirTemperature', points))
            {
                $(container).find(".rs-chart-area").toggle();
                return false;
            }

            //TODO: Change the min max of y1Scale
            var y1Scale = d3.scale.linear().domain([0, 200]);
            var y2Scale = d3.scale.linear().domain([0, 100]);
            //Set up data series: change this for different data sources

            var ySeries = {};
            if (existPoint('OutdoorAirTemperature', points)) {
                ySeries['OutdoorAirTemperature'] = {
                    name: 'Outdoor Air Temperature',
                    color: colors.OutdoorAirTemperature,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.OutdoorAirTemperature]};
                    }),
                    scale: y1Scale
                }
            }
            if (existPoint('CCV', points)) {
                ySeries['CCV'] = {
                    name: 'Cooling Coil Valve Position',
                    color: colors.CCV,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.CCV]};
                    }),
                    scale: y2Scale
                }
            }
            if (existPoint('HCV', points)) {
                ySeries['HCV'] = {
                    name: 'Heating Coil Valve Position',
                    color: colors.HCV,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.HCV]};
                    }),
                    scale: y2Scale
                }
            }
            //Plotting
            var plotSeries = [];
            angular.forEach(ySeries, function (value, key) {
                plotSeries.push(value);
            });
            var graph = new Rickshaw.Graph({
                element: document.querySelector(chartId),
                renderer: 'line',
                series: plotSeries,
                interpolation: 'linear'
            });
            graph.render();

            //Tooltip for hovering
//            var hoverDetail = new Rickshaw.Graph.HoverDetail({
//                graph: graph,
//                formatter: function (series, x, y) {
//                    var date = '<span class="date">' + new Date(x * 1000).toUTCString() + '</span>';
//                    var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
//                    var content = swatch + series.name + ": " + parseFloat(y).toFixed(2) + '<br>' + date;
//                    return content;
//                }
//            });
            //Display & Toggle Legends
            var legend = new Rickshaw.Graph.Legend({
                graph: graph,
                element: document.querySelector(chartLegend)
            });
            var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
                graph: graph,
                legend: legend
            });
            //Render X Y Axes
            var xAxis = new Rickshaw.Graph.Axis.ExtendedTime(
                {
                    graph: graph,
                    orientation: "bottom",
                    //tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                    pixelsPerTick: 50,
                    tickSpacing: 6 * 60 * 60, // 6 hours
                    timeUnit: timeUnit

                });
            xAxis.render();
            var yAxis = new Rickshaw.Graph.Axis.Y.Scaled({
                graph: graph,
                berthRate: 0.0,
                orientation: 'left',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY),
                scale: y1Scale,
                label: labelY1()
            });
            yAxis.render();

            var yAxis2 = new Rickshaw.Graph.Axis.Y.Scaled({
                graph: graph,
                berthRate: 0,
                orientation: 'right',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY2),
                scale: y2Scale,
                ticks: 5,
                label: labelY2()
                //tickValues: [0,20,40,60,80,100]
            });
            yAxis2.render();

            var slider = new Rickshaw.Graph.RangeSlider.Preview({
                graph: graph,
                element: document.querySelector(chartSlider)
            });

        }
        function plotDischargeTempChart1(data, allPoints, points, colors, args) {
            //Set UI Args
            var timeUnit = args.TimeUnit;
            var container = args.Container;
            var chartId = container + " .rs-chart";
            var chartY = container + " .rs-y-axis";
            var chartY2 = container + " .rs-y-axis2";
            var chartLegend = container + " .rs-legend";
            var chartTitle = container + " .title";
            var chartSlider = container + " .rs-slider";
            document.querySelector(chartTitle).innerHTML = args.Title;

            //if (!(existPoint(rawTsName, points) && existPoint(allPoints.ZoneTemp, points))) return false;
            if (!existPoint('DischargeAirTemperature', points) &&
                !existPoint('DischargeAirTemperatureSetPoint', points) &&
                !existPoint('OutdoorAirTemperature', points))
            {
                $(container).find(".rs-chart-area").toggle();
                return false;
            }

            //TODO: Change the min max of y1Scale
            var y1Scale = d3.scale.linear().domain([0, 200]);
            var y2Scale = d3.scale.linear().domain([0, 100]);
            //Set up data series: change this for different data sources

            var ySeries = {};
            if (existPoint('OutdoorAirTemperature', points)) {
                ySeries['OutdoorAirTemperature'] = {
                    name: 'Outdoor Air Temperature',
                    color: colors.OutdoorAirTemperature,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.OutdoorAirTemperature]};
                    }),
                    scale: y1Scale
                }
            }
            if (existPoint('DischargeAirTemperature', points)) {
                ySeries['DischargeAirTemperature'] = {
                    name: 'Discharge Air Temperature',
                    color: colors.DischargeAirTemperature,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.DischargeAirTemperature]};
                    }),
                    scale: y2Scale
                }
            }
            if (existPoint('DischargeAirTemperatureSetPoint', points)) {
                ySeries['DischargeAirTemperatureSetPoint'] = {
                    name: 'Discharge Air Temperature Set Point',
                    color: colors.DischargeAirTemperatureSetPoint,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.DischargeAirTemperatureSetPoint]};
                    }),
                    scale: y2Scale
                }
            }
            //Plotting
            var plotSeries = [];
            angular.forEach(ySeries, function (value, key) {
                plotSeries.push(value);
            });
            var graph = new Rickshaw.Graph({
                element: document.querySelector(chartId),
                renderer: 'line',
                series: plotSeries,
                interpolation: 'linear'
            });
            graph.render();

            //Tooltip for hovering
//            var hoverDetail = new Rickshaw.Graph.HoverDetail({
//                graph: graph,
//                formatter: function (series, x, y) {
//                    var date = '<span class="date">' + new Date(x * 1000).toUTCString() + '</span>';
//                    var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
//                    var content = swatch + series.name + ": " + parseFloat(y).toFixed(2) + '<br>' + date;
//                    return content;
//                }
//            });
            //Display & Toggle Legends
            var legend = new Rickshaw.Graph.Legend({
                graph: graph,
                element: document.querySelector(chartLegend)
            });
            var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
                graph: graph,
                legend: legend
            });
            //Render X Y Axes
            var xAxis = new Rickshaw.Graph.Axis.ExtendedTime(
                {
                    graph: graph,
                    orientation: "bottom",
                    //tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                    pixelsPerTick: 50,
                    tickSpacing: 6 * 60 * 60, // 6 hours
                    timeUnit: timeUnit

                });
            xAxis.render();
            var yAxis = new Rickshaw.Graph.Axis.Y.Scaled({
                graph: graph,
                berthRate: 0.0,
                orientation: 'left',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY),
                scale: y1Scale,
                label: labelY1()
            });
            yAxis.render();

            var slider = new Rickshaw.Graph.RangeSlider.Preview({
                graph: graph,
                element: document.querySelector(chartSlider)
            });

        }
        function plotFanChart1(data, allPoints, points, colors, args) {
            //Set UI Args
            var timeUnit = args.TimeUnit;
            var container = args.Container;
            var chartId = container + " .rs-chart";
            var chartY = container + " .rs-y-axis";
            var chartY2 = container + " .rs-y-axis2";
            var chartLegend = container + " .rs-legend";
            var chartTitle = container + " .title";
            var chartSlider = container + " .rs-slider";
            document.querySelector(chartTitle).innerHTML = args.Title;

            //if (!(existPoint(rawTsName, points) && existPoint(allPoints.ZoneTemp, points))) return false;
            if (!existPoint('SupplyFanSpeed', points) &&
                !existPoint('SupplyFanStatus', points) &&
                !existPoint('DuctStaticPressure', points) &&
                !existPoint('ReturnFanSpeed', points))
            {
                $(container).find(".rs-chart-area").toggle();
                return false;
            }

            //TODO: Change the min max of y1Scale
            var y1Scale = d3.scale.linear().domain([0, 200]);
            var y2Scale = d3.scale.linear().domain([0, 100]);
            //Set up data series: change this for different data sources

            var ySeries = {};

            if (existPoint('DuctStaticPressure', points)) {
                ySeries['DuctStaticPressure'] = {
                    name: 'Duct Static Pressure',
                    color: colors.DuctStaticPressure,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.DuctStaticPressure]};
                    }),
                    scale: y1Scale
                }
            }
            if (existPoint('SupplyFanSpeed', points)) {
                ySeries['SupplyFanSpeed'] = {
                    name: 'Supply Fan Speed',
                    color: colors.SupplyFanSpeed,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.SupplyFanSpeed]};
                    }),
                    scale: y2Scale
                }
            }
            if (existPoint('SupplyFanStatus', points)) {
                ySeries['SupplyFanStatus'] = {
                    name: 'Supply Fan Status',
                    color: colors.SupplyFanStatus,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.SupplyFanStatus]};
                    }),
                    scale: y2Scale
                }
            }
            if (existPoint('ReturnFanSpeed', points)) {
                ySeries['ReturnFanSpeed'] = {
                    name: 'Return Fan Speed',
                    color: colors.ReturnFanSpeed,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.ReturnFanSpeed]};
                    }),
                    scale: y2Scale
                }
            }

            //Plotting
            var plotSeries = [];
            angular.forEach(ySeries, function (value, key) {
                plotSeries.push(value);
            });
            var graph = new Rickshaw.Graph({
                element: document.querySelector(chartId),
                renderer: 'line',
                series: plotSeries,
                interpolation: 'linear'
            });
            graph.render();

            //Tooltip for hovering
//            var hoverDetail = new Rickshaw.Graph.HoverDetail({
//                graph: graph,
//                formatter: function (series, x, y) {
//                    var date = '<span class="date">' + new Date(x * 1000).toUTCString() + '</span>';
//                    var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
//                    var content = swatch + series.name + ": " + parseFloat(y).toFixed(2) + '<br>' + date;
//                    return content;
//                }
//            });
            //Display & Toggle Legends
            var legend = new Rickshaw.Graph.Legend({
                graph: graph,
                element: document.querySelector(chartLegend)
            });
            var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
                graph: graph,
                legend: legend
            });
            //Render X Y Axes
            var xAxis = new Rickshaw.Graph.Axis.ExtendedTime(
                {
                    graph: graph,
                    orientation: "bottom",
                    //tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                    pixelsPerTick: 50,
                    tickSpacing: 6 * 60 * 60, // 6 hours
                    timeUnit: timeUnit

                });
            xAxis.render();
            var yAxis = new Rickshaw.Graph.Axis.Y.Scaled({
                graph: graph,
                berthRate: 0.0,
                orientation: 'left',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY),
                scale: y1Scale,
                label: labelY1('Pressure')
            });
            yAxis.render();

            var yAxis2 = new Rickshaw.Graph.Axis.Y.Scaled({
                graph: graph,
                berthRate: 0,
                orientation: 'right',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY2),
                scale: y2Scale,
                ticks: 5,
                label: labelY2()
                //tickValues: [0,20,40,60,80,100]
            });
            yAxis2.render();

            var slider = new Rickshaw.Graph.RangeSlider.Preview({
                graph: graph,
                element: document.querySelector(chartSlider)
            });

        }
        function plotOAChart2(data, allPoints, points, colors, args) {
            //Set UI Args
            var container = args.Container;
            var chartId = container + " .rs-chart";
            var chartY = container + " .rs-y-axis";
            var chartLegend = container + " .rs-legend";
            var chartTitle = container + " .title";
            document.querySelector(chartTitle).innerHTML = args.Title;

            //if (!(existPoint(rawTsName, points) && existPoint(allPoints.ZoneTemp, points))) return false;
            if (!existPoint('OutdoorAirTemperature', points) ||
                !existPoint('OutdoorDamper', points))
            {
                $(container).find(".rs-chart-area").toggle();
                return false;
            }

            //Set up data series: change this for different data sources
            data.sort(function (a, b) {
                if (a[points.OutdoorAirTemperature] < b[points.OutdoorAirTemperature])
                    return -1;
                if (a[points.OutdoorAirTemperature] > b[points.OutdoorAirTemperature])
                    return 1;
                return 0;
            });
            var ySeries = {};
            if (existPoint('OutdoorDamper', points)) {
                ySeries['OutdoorDamper'] = {
                    name: 'Outdoor Damper Signal',
                    xName: points.OutdoorAirTemperature,
                    color: colors.OutdoorDamper,
                    data: data.map(function (d) {
                        return {x: d[points.OutdoorAirTemperature], y: d[points.OutdoorDamper]};
                    })
                }
            }

            //Plotting
            var graph = new Rickshaw.Graph({
                element: document.querySelector(chartId),
                renderer: 'scatterplot',
                series: [ySeries['OutdoorDamper']]
            });
            graph.renderer.dotSize = 2;
            graph.render();
            //Tooltip for hovering
//            var hoverDetail = new Rickshaw.Graph.HoverDetail({
//                graph: graph,
//                formatter: function (series, x, y) {
//                    var xValue = '<span style="padding-right:50px;">' + series.xName + ": " + parseFloat(x) + '</span>';
//                    var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
//                    var content = swatch + series.name + ": " + parseFloat(y) + '<br>' + xValue;
//                    return content;
//                }
//            });
            //Display & Toggle Legends
            var legend = new Rickshaw.Graph.Legend({
                graph: graph,
                element: document.querySelector(chartLegend)
            });
            var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
                graph: graph,
                legend: legend
            });
            //Render X Y Axes
            var xAxis = new Rickshaw.Graph.Axis.X({
                graph: graph,
                label: labelX('Outdoor Temperature')
            });
            xAxis.render();
            var yAxis = new Rickshaw.Graph.Axis.Y({
                graph: graph,
                berthRate: 0.0,
                orientation: 'left',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY),
                label: labelY1('Outdoor Damper Position')
            });
            yAxis.render();
        }
        function plotSPChart2(data, allPoints, points, colors, args) {
            //Set UI Args
            var container = args.Container;
            var chartId = container + " .rs-chart";
            var chartY = container + " .rs-y-axis";
            var chartLegend = container + " .rs-legend";
            var chartTitle = container + " .title";
            document.querySelector(chartTitle).innerHTML = args.Title;

            //if (!(existPoint(rawTsName, points) && existPoint(allPoints.ZoneTemp, points))) return false;
            if (!existPoint('SupplyFanSpeed', points) ||
                !existPoint('ReturnFanSpeed', points))
            {
                $(container).find(".rs-chart-area").toggle();
                return false;
            }

            //Set up data series: change this for different data sources
            data.sort(function (a, b) {
                if (a[points.ReturnFanSpeed] < b[points.ReturnFanSpeed])
                    return -1;
                if (a[points.ReturnFanSpeed] > b[points.ReturnFanSpeed])
                    return 1;
                return 0;
            });
            var ySeries = {};
            if (existPoint('SupplyFanSpeed', points)) {
                ySeries['SupplyFanSpeed'] = {
                    name: 'Supply Fan Speed',
                    xName: points.ReturnFanSpeed,
                    color: colors.SupplyFanSpeed,
                    data: data.map(function (d) {
                        return {x: d[points.ReturnFanSpeed], y: d[points.SupplyFanSpeed]};
                    })
                }
            }

            //Plotting
            var graph = new Rickshaw.Graph({
                element: document.querySelector(chartId),
                renderer: 'scatterplot',
                series: [ySeries['SupplyFanSpeed']]
            });
            graph.renderer.dotSize = 2;
            graph.render();
            //Tooltip for hovering
//            var hoverDetail = new Rickshaw.Graph.HoverDetail({
//                graph: graph,
//                formatter: function (series, x, y) {
//                    var xValue = '<span style="padding-right:50px;">' + series.xName + ": " + parseFloat(x) + '</span>';
//                    var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
//                    var content = swatch + series.name + ": " + parseFloat(y) + '<br>' + xValue;
//                    return content;
//                }
//            });
            //Display & Toggle Legends
            var legend = new Rickshaw.Graph.Legend({
                graph: graph,
                element: document.querySelector(chartLegend)
            });
            var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
                graph: graph,
                legend: legend
            });
            //Render X Y Axes
            var xAxis = new Rickshaw.Graph.Axis.X({
                graph: graph,
                label: labelX('Return Fan Speed')
            });
            xAxis.render();
            var yAxis = new Rickshaw.Graph.Axis.Y({
                graph: graph,
                berthRate: 0.0,
                orientation: 'left',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY),
                label: labelY1('Supply Fan Speed')
            });
            yAxis.render();
        }
        function plotCoilChart2(data, allPoints, points, colors, args) {
            //Set UI Args
            var container = args.Container;
            var chartId = container + " .rs-chart";
            var chartY = container + " .rs-y-axis";
            var chartLegend = container + " .rs-legend";
            var chartTitle = container + " .title";
            document.querySelector(chartTitle).innerHTML = args.Title;

            //if (!(existPoint(rawTsName, points) && existPoint(allPoints.ZoneTemp, points))) return false;
            if (!existPoint('HCV', points) || !existPoint('CCV', points))
            {
                $(container).find(".rs-chart-area").toggle();
                return false;
            }

            //Set up data series: change this for different data sources
            data.sort(function (a, b) {
                if (a[points.CCV] < b[points.CCV])
                    return -1;
                if (a[points.CCV] > b[points.CCV])
                    return 1;
                return 0;
            });
            var ySeries = {};
            if (existPoint('HCV', points)) {
                ySeries['HCV'] = {
                    name: 'Heating Coil Valve Position',
                    xName: points.CCV,
                    color: colors.HCV,
                    data: data.map(function (d) {
                        return {x: d[points.CCV], y: d[points.HCV]};
                    })
                }
            }

            //Plotting
            var graph = new Rickshaw.Graph({
                element: document.querySelector(chartId),
                renderer: 'scatterplot',
                series: [ySeries['HCV']]
            });
            graph.renderer.dotSize = 2;
            graph.render();
            //Tooltip for hovering
//            var hoverDetail = new Rickshaw.Graph.HoverDetail({
//                graph: graph,
//                formatter: function (series, x, y) {
//                    var xValue = '<span style="padding-right:50px;">' + series.xName + ": " + parseFloat(x) + '</span>';
//                    var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
//                    var content = swatch + series.name + ": " + parseFloat(y) + '<br>' + xValue;
//                    return content;
//                }
//            });
            //Display & Toggle Legends
            var legend = new Rickshaw.Graph.Legend({
                graph: graph,
                element: document.querySelector(chartLegend)
            });
            var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
                graph: graph,
                legend: legend
            });
            //Render X Y Axes
            var xAxis = new Rickshaw.Graph.Axis.X({
                graph: graph,
                label: labelX('Cooling Coil Valve')
            });
            xAxis.render();
            var yAxis = new Rickshaw.Graph.Axis.Y({
                graph: graph,
                berthRate: 0.0,
                orientation: 'left',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY),
                label: labelY1('Heating Coil Valve')
            });
            yAxis.render();
        }
        function plotDischargeTempChart2(data, allPoints, points, colors, args) {
            //Set UI Args
            var container = args.Container;
            var chartId = container + " .rs-chart";
            var chartY = container + " .rs-y-axis";
            var chartLegend = container + " .rs-legend";
            var chartTitle = container + " .title";
            document.querySelector(chartTitle).innerHTML = args.Title;

            //if (!(existPoint(rawTsName, points) && existPoint(allPoints.ZoneTemp, points))) return false;
            if (!existPoint('DischargeAirTemperatureSetPoint', points) ||
                !existPoint('DischargeAirTemperature', points))
            {
                $(container).find(".rs-chart-area").toggle();
                return false;
            }

            //Set up data series: change this for different data sources
            data.sort(function (a, b) {
                if (a[points.DischargeAirTemperatureSetPoint] < b[points.DischargeAirTemperatureSetPoint])
                    return -1;
                if (a[points.DischargeAirTemperatureSetPoint] > b[points.DischargeAirTemperatureSetPoint])
                    return 1;
                return 0;
            });
            var ySeries = {};
            if (existPoint('DischargeAirTemperature', points)) {
                ySeries['DischargeAirTemperature'] = {
                    name: 'Discharge Air Temperature',
                    xName: points.DischargeAirTemperatureSetPoint,
                    color: colors.DischargeAirTemperature,
                    data: data.map(function (d) {
                        return {x: d[points.DischargeAirTemperatureSetPoint], y: d[points.DischargeAirTemperature]};
                    })
                }
            }

            //Plotting
            var graph = new Rickshaw.Graph({
                element: document.querySelector(chartId),
                renderer: 'scatterplot',
                series: [ySeries['DischargeAirTemperature']]
            });
            graph.renderer.dotSize = 2;
            graph.render();
            //Tooltip for hovering
//            var hoverDetail = new Rickshaw.Graph.HoverDetail({
//                graph: graph,
//                formatter: function (series, x, y) {
//                    var xValue = '<span style="padding-right:50px;">' + series.xName + ": " + parseFloat(x) + '</span>';
//                    var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
//                    var content = swatch + series.name + ": " + parseFloat(y) + '<br>' + xValue;
//                    return content;
//                }
//            });
            //Display & Toggle Legends
            var legend = new Rickshaw.Graph.Legend({
                graph: graph,
                element: document.querySelector(chartLegend)
            });
            var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
                graph: graph,
                legend: legend
            });
            //Render X Y Axes
            var xAxis = new Rickshaw.Graph.Axis.X({
                graph: graph,
                label: labelX('Discharge Temperature SetPoint')
            });
            xAxis.render();
            var yAxis = new Rickshaw.Graph.Axis.Y({
                graph: graph,
                berthRate: 0.0,
                orientation: 'left',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY),
                label: labelY1('Discharge Temperature')
            });
            yAxis.render();
        }
        var fTsName = 'FTimestamp';
        data = parseSortByTimestamp(data, rawTsName, fTsName, points, counts);
        //Delete key in points that have no data
        for (var prop in counts) {
            if (counts[prop] == 0) {
                delete points[prop];
            }
        }

        var timeUnit = getTimeUnit(data[0][fTsName], data[data.length - 1][fTsName], [data[0][fTsName], data[1][fTsName], data[2][fTsName]]);
        var tArgs = {
            Timestamp: fTsName,
            Title: 'AHU Economizer Response Analysis',
            Container: '#oa-chart-box1',
            TimeUnit: timeUnit
        };
        plotOAChart1(data, allPoints, points, colors, tArgs);


        var args = {
          Timestamp: fTsName,
          Title: 'AHU Discharge Static Pressure Control Performance Analysis',
          Container: '#sp-chart-box1'
        };
        plotSPChart1(data, allPoints, points, colors, args);

        var args = {
          Timestamp: fTsName,
          Title: 'AHU Simultaneous Heating and Cooling Performance Analysis',
          Container: '#coil-chart-box1'
        };
        plotCoilChart1(data, allPoints, points, colors, args);

        var args = {
          Timestamp: fTsName,
          Title: 'Discharge Air Temperature Set Point Performance Analysis',
          Container: '#discharge-chart-box1'
        };
        plotDischargeTempChart1(data, allPoints, points, colors, args);

        var args = {
          Timestamp: fTsName,
          Title: 'AHU Operational Day, Night and Weekend Operations Analysis',
          Container: '#fan-chart-box1'
        };
        plotFanChart1(data, allPoints, points, colors, args);

        //All scatter charts need to be after this point
        var args = {
          Timestamp: fTsName,
          Title: 'Seasonal AHU Economizer Damper Command Response Analysis',
          Container: '#oa-chart-box2'
        };
        plotOAChart2(data, allPoints, points, colors, args);

        var args = {
          Timestamp: fTsName,
          Title: 'AHU VFD-Driven Fan Tracking (Supply and Return) Performance Analysis',
          Container: '#sp-chart-box2'
        };
        plotSPChart2(data, allPoints, points, colors, args);

        var args = {
          Timestamp: fTsName,
          Title: 'AHU Heating and Cooling Coil Performance Analysis',
          Container: '#coil-chart-box2'
        };
        plotCoilChart2(data, allPoints, points, colors, args);

        var args = {
          Timestamp: fTsName,
          Title: 'Discharge Air Temperature Control Performance Analysis',
          Container: '#discharge-chart-box2'
        };
        plotDischargeTempChart2(data, allPoints, points, colors, args);

        $(".rs-chart-container.hidden").removeClass("hidden");
        //Fix styling of D3: when the min value is at the bottom of the Y axis, we can see only upper half of the value
        //$('.rickshaw_graph .y_ticks text').attr('dy', '0');

    }

    function zone_ecam(data) {
            var rawTsName = 'datetime';

            //object to contain definition for points:
            // this should match the output_format received from the server
            var allPointsPrefix = {
                ZoneTemp: 'ZoneTemperature',
                ZoneRhtVlvSignal: 'TerminalBoxReheatValvePosition',
                ZoneDamperPos: 'TerminalBoxDamperCommand',
                ZoneOcc: 'ZoneOccupancyMode',
                ZoneFanStatus: 'ZoneFanStatus',
                ZoneSetPoint: 'ZoneTemperatureSetPoint',
                ZoneCFM: 'TerminalBoxFanAirflow'
            };

            var allPoints = {};
            if (data.length > 0) {
                d = data[0];
                for (var k in d){ //k is input data point name
                    if (d.hasOwnProperty(k)) {
                        for (var point in allPointsPrefix) {
                            if (allPointsPrefix.hasOwnProperty(point)) {
                                if (startWith(k, allPointsPrefix[point])) {
                                    allPoints[k] = k;
                                }
                            }
                        }
                    }
                }
            }
            var counts = {};
            var points = {}; //Points actually used for visualization
            for (var prop in allPoints) {
                counts[prop] = 0;
                points[prop] = allPoints[prop];
            }

            var colors = {};
            var i = 0;
            for (var point in points) {
                //if (startWith(point, 'ZoneTemp')) {
                    colors[point] = getColor(i++);
                //}
            }

            function plotTsChart(data, allPoints, points, colors, args) {
                //Set UI Args
                var timeUnit = args.TimeUnit;
                var container = args.Container;
                var chartId = container + " .rs-chart";
                var chartY = container + " .rs-y-axis";
                var chartY2 = container + " .rs-y-axis2";
                var chartLegend = container + " .rs-legend";
                var chartTitle = container + " .title";
                var chartSlider = container + " .rs-slider";
                document.querySelector(chartTitle).innerHTML = args.Title;

                //if (!(existPoint(rawTsName, points) && existPoint(allPoints.ZoneTemp, points))) return false;
                if (!existPointStartWith(allPointsPrefix['ZoneTemp'], points))
            {
                $(container).find(".rs-chart-area").toggle();
                return false;
            }

                //TODO: Change the min max of y1Scale
                var y1Scale = d3.scale.linear().domain([0, 200]);
                var y2Scale = d3.scale.linear().domain([0, 100]);
                //Set up data series: change this for different data sources

                var ySeries = {};
                for (var point in points) {
                    if (startWith(point, allPointsPrefix['ZoneTemp']) ||
                        startWith(point, allPointsPrefix['ZoneSetPoint'])) {
                        ySeries[point] = {
                            name: point.replace(/^Zone/,'').replace(/^TerminalBox/,''),
                            color: colors[point],
                            data: data.map(function (d) {
                                return {x: d[args.Timestamp], y: d[point]};
                            }),
                            scale: y1Scale
                        }
                    }
                    if (startWith(point, allPointsPrefix['ZoneRhtVlvSignal']) ||
                        startWith(point, allPointsPrefix['ZoneDamperPos']) ||
                        startWith(point, allPointsPrefix['ZoneOcc']) ||
                        startWith(point, allPointsPrefix['ZoneFanStatus']) ||
                        startWith(point, allPointsPrefix['ZoneCFM'])) {
                        ySeries[point] = {
                            name: point.replace(/^Zone/,'').replace(/^TerminalBox/,''),
                            color: colors[point],
                            data: data.map(function (d) {
                                return {x: d[args.Timestamp], y: d[point]};
                            }),
                            scale: y2Scale
                        }
                    }
                }
                //Plotting
                var plotSeries = [];
                angular.forEach(ySeries, function (value, key) {
                    plotSeries.push(value);
                });
                var graph = new Rickshaw.Graph({
                    element: document.querySelector(chartId),
                    renderer: 'line',
                    series: plotSeries,
                    interpolation: 'linear'
                });
                graph.render();

                //Tooltip for hovering
//                var hoverDetail = new Rickshaw.Graph.HoverDetail({
//                    graph: graph,
//                    formatter: function (series, x, y) {
//                        var date = '<span class="date">' + new Date(x * 1000).toUTCString() + '</span>';
//                        var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
//                        var content = swatch + series.name + ": " + parseFloat(y).toFixed(2) + '<br>' + date;
//                        return content;
//                    }
//                });
                //Display & Toggle Legends
                var legend = new Rickshaw.Graph.Legend({
                    graph: graph,
                    element: document.querySelector(chartLegend)
                });
                var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
                    graph: graph,
                    legend: legend
                });
                //Render X Y Axes
                var xAxis = new Rickshaw.Graph.Axis.ExtendedTime(
                    {
                        graph: graph,
                        orientation: "bottom",
                        //tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                        pixelsPerTick: 50,
                        tickSpacing: 6 * 60 * 60, // 6 hours
                        timeUnit: timeUnit

                    });
                xAxis.render();
                var yAxis = new Rickshaw.Graph.Axis.Y.Scaled({
                    graph: graph,
                    berthRate: 0.0,
                    orientation: 'left',
                    tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                    element: document.querySelector(chartY),
                    scale: y1Scale,
                    label: labelY1('Temperature')
                });
                yAxis.render();

                var yAxis2 = new Rickshaw.Graph.Axis.Y.Scaled({
                    graph: graph,
                    berthRate: 0,
                    orientation: 'right',
                    tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                    element: document.querySelector(chartY2),
                    scale: y2Scale,
                    ticks: 5,
                    label: labelY2('Command Signal')

                    //tickValues: [0,20,40,60,80,100]
                });
                yAxis2.render();

                var slider = new Rickshaw.Graph.RangeSlider.Preview({
                    graph: graph,
                    element: document.querySelector(chartSlider)
                });

            }

            var fTsName = 'FTimestamp';
            data = parseSortByTimestamp(data, rawTsName, fTsName, points, counts);
            //Delete key in points that have no data
            for (var prop in counts) {
                if (counts[prop] == 0) {
                    delete points[prop];
                }
            }

            var timeUnit = getTimeUnit(data[0][fTsName], data[data.length - 1][fTsName], [data[0][fTsName], data[1][fTsName], data[2][fTsName]]);
            var tArgs = {
                Timestamp: fTsName,
                Title: 'Zone Terminal Box Performance Analysis',
                Container: '#temps-chart-box',
                TimeUnit: timeUnit
            };
            plotTsChart(data, allPoints, points, colors, tArgs);

            $(".rs-chart-container.hidden").removeClass("hidden");
            //Fix styling of D3: when the min value is at the bottom of the Y axis, we can see only upper half of the value
            //$('.rickshaw_graph .y_ticks text').attr('dy', '0');

        }

    function hwplant_ecam(data) {
        //console.log(data);
        var rawTsName = 'datetime';

        //object to contain definition for points
        var allPoints = { //all points available in the output_format from backend
            OutdoorAirTemperature: 'OutdoorAirTemperature',
            LoopDifferentialPressure: 'LoopDifferentialPressure',
            LoopDifferentialPressureSetPoint: 'LoopDifferentialPressureSetPoint',
            PumpStatus: 'PumpStatus',
            BoilerStatus: 'BoilerStatus',
            HotWaterPumpVfd: 'HotWaterPumpVfd',
            HotWaterSupplyTemperature: 'HotWaterSupplyTemperature',
            HotWaterTemperatureSetPoint: 'HotWaterTemperatureSetPoint',
            HotWaterReturnTemperature: 'HotWaterReturnTemperature'
        };
        counts = {};
        points = {}; //Points actually used for visualization
        for (var prop in allPoints) {
            counts[prop] = 0;
            points[prop] = allPoints[prop];
        }

        //object to contain definition for point colors
        //http://www.w3schools.com/html/html_colornames.asp
        var colors = {
          OutdoorAirTemperature: 'blue',
          HotWaterTemperatureSetPoint: 'HotPink',
          HotWaterReturnTemperature: 'LightPink',
          HotWaterSupplyTemperature: 'Red',
          LoopDifferentialPressure: 'DarkMagenta',
          LoopDifferentialPressureSetPoint: 'Magenta',
          PumpStatus: 'Chocolate',
          BoilerStatus: 'blueviolet',
          HotWaterPumpVfd: 'Green',
          HotWaterDeltaT: 'Brown'
        };

        function plotTempChart(data, allPoints, points, colors, args) {
            //Set UI Args
            var timeUnit = args.TimeUnit;
            var container = args.Container;
            var chartId = container + " .rs-chart";
            var chartY = container + " .rs-y-axis";
            var chartY2 = container + " .rs-y-axis2";
            var chartLegend = container + " .rs-legend";
            var chartTitle = container + " .title";
            var chartSlider = container + " .rs-slider";
            document.querySelector(chartTitle).innerHTML = args.Title;

            //if (!(existPoint(rawTsName, points) && existPoint(allPoints.ZoneTemp, points))) return false;
            if (!existPoint('HotWaterSupplyTemperature', points))
            {
                $(container).find(".rs-chart-area").toggle();
                return false;
            }

            //TODO: Change the min max of y1Scale
            var y1Scale = d3.scale.linear().domain([0, 200]);
            var y2Scale = d3.scale.linear().domain([0, 100]);
            //Set up data series: change this for different data sources

            var ySeries = {};
            if (existPoint('HotWaterSupplyTemperature', points)) {
                ySeries['HotWaterSupplyTemperature'] = {
                    name: 'Hot Water Supply Temperature',
                    color: colors.HotWaterSupplyTemperature,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.HotWaterSupplyTemperature]};
                    }),
                    scale: y1Scale
                }
            }
            if (existPoint('HotWaterReturnTemperature', points)) {
                ySeries['HotWaterReturnTemperature'] = {
                    name: points.HotWaterReturnTemperature,
                    color: colors.HotWaterReturnTemperature,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.HotWaterReturnTemperature]};
                    }),
                    scale: y1Scale
                }
                ySeries['HotWaterDeltaT'] = {
                    name: 'HotWaterDeltaT',
                    color: colors['HotWaterDeltaT'],
                    data: data.map(function (d) {
                        return {
                            x: d[args.Timestamp],
                            y: d[points.HotWaterSupplyTemperature]-d[points.HotWaterReturnTemperature]
                        };
                    }),
                    scale: y1Scale
                }



            }
            if (existPoint('HotWaterTemperatureSetPoint', points)) {
                ySeries['HotWaterTemperatureSetPoint'] = {
                    name: 'Hot Water Temperature Set Point',
                    color: colors.HotWaterTemperatureSetPoint,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.HotWaterTemperatureSetPoint]};
                    }),
                    scale: y1Scale
                }
            }
            if (existPoint('OutdoorAirTemperature', points)) {
                ySeries['OutdoorAirTemperature'] = {
                    name: 'Outdoor Air Temperature',
                    color: colors.OutdoorAirTemperature,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.OutdoorAirTemperature]};
                    }),
                    scale: y1Scale
                }
            }
            if (existPoint('ZoneSetPoint', points)) {
                ySeries['ZoneSetPoint'] = {
                    name: 'Zone Temperature Set Point',
                    color: colors.ZoneSetPoint,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.ZoneSetPoint]};
                    }),
                    scale: y1Scale
                }
            }
            //Plotting
            var plotSeries = [];
            angular.forEach(ySeries, function (value, key) {
                plotSeries.push(value);
            });
            var graph = new Rickshaw.Graph({
                element: document.querySelector(chartId),
                renderer: 'line',
                series: plotSeries,
                interpolation: 'linear'
            });
            graph.render();

            //Tooltip for hovering
//                var hoverDetail = new Rickshaw.Graph.HoverDetail({
//                    graph: graph,
//                    formatter: function (series, x, y) {
//                        var date = '<span class="date">' + new Date(x * 1000).toUTCString() + '</span>';
//                        var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
//                        var content = swatch + series.name + ": " + parseFloat(y).toFixed(2) + '<br>' + date;
//                        return content;
//                    }
//                });
            //Display & Toggle Legends
            var legend = new Rickshaw.Graph.Legend({
                graph: graph,
                element: document.querySelector(chartLegend)
            });
            var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
                graph: graph,
                legend: legend
            });
            //Render X Y Axes
            var xAxis = new Rickshaw.Graph.Axis.ExtendedTime(
                {
                    graph: graph,
                    orientation: "bottom",
                    //tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                    pixelsPerTick: 50,
                    tickSpacing: 6 * 60 * 60, // 6 hours
                    timeUnit: timeUnit

                });
            xAxis.render();
            var yAxis = new Rickshaw.Graph.Axis.Y.Scaled({
                graph: graph,
                berthRate: 0.0,
                orientation: 'left',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY),
                scale: y1Scale,
                label: labelY1('Temperature')
            });
            yAxis.render();

            var slider = new Rickshaw.Graph.RangeSlider.Preview({
                graph: graph,
                element: document.querySelector(chartSlider)
            });

        }

        function plotPressureChart(data, allPoints, points, colors, args) {
            //Set UI Args
            var timeUnit = args.TimeUnit;
            var container = args.Container;
            var chartId = container + " .rs-chart";
            var chartY = container + " .rs-y-axis";
            var chartY2 = container + " .rs-y-axis2";
            var chartLegend = container + " .rs-legend";
            var chartTitle = container + " .title";
            var chartSlider = container + " .rs-slider";
            document.querySelector(chartTitle).innerHTML = args.Title;

            //if (!(existPoint(rawTsName, points) && existPoint(allPoints.ZoneTemp, points))) return false;
            if (!existPoint('LoopDifferentialPressure', points))
        {
            $(container).find(".rs-chart-area").toggle();
            return false;
        }

            //TODO: Change the min max of y1Scale
            var y1Scale = d3.scale.linear().domain([0, 200]);
            var y2Scale = d3.scale.linear().domain([0, 100]);
            //Set up data series: change this for different data sources

            var ySeries = {};
            if (existPoint('LoopDifferentialPressure', points)) {
                ySeries['LoopDifferentialPressure'] = {
                    name: 'Loop Differential Pressure',
                    color: colors.LoopDifferentialPressure,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.LoopDifferentialPressure]};
                    }),
                    scale: y1Scale
                }
            }
            if (existPoint('LoopDifferentialPressureSetPoint', points)) {
                ySeries['LoopDifferentialPressureSetPoint'] = {
                    name: 'Loop Differential Pressure SetPoint',
                    color: colors.LoopDifferentialPressureSetPoint,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.LoopDifferentialPressureSetPoint]};
                    }),
                    scale: y1Scale
                }
            }
            if (existPoint('HotWaterPumpVfd', points)) {
                ySeries['HotWaterPumpVfd'] = {
                    name: 'Hot Water Pump Vfd',
                    color: colors.HotWaterPumpVfd,
                    data: data.map(function (d) {
                        return {x: d[args.Timestamp], y: d[points.HotWaterPumpVfd]};
                    }),
                    scale: y2Scale
                }
            }
            //Plotting
            var plotSeries = [];
            angular.forEach(ySeries, function (value, key) {
                plotSeries.push(value);
            });
            var graph = new Rickshaw.Graph({
                element: document.querySelector(chartId),
                renderer: 'line',
                series: plotSeries,
                interpolation: 'linear'
            });
            graph.render();

            //Tooltip for hovering
//                var hoverDetail = new Rickshaw.Graph.HoverDetail({
//                    graph: graph,
//                    formatter: function (series, x, y) {
//                        var date = '<span class="date">' + new Date(x * 1000).toUTCString() + '</span>';
//                        var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
//                        var content = swatch + series.name + ": " + parseFloat(y).toFixed(2) + '<br>' + date;
//                        return content;
//                    }
//                });
            //Display & Toggle Legends
            var legend = new Rickshaw.Graph.Legend({
                graph: graph,
                element: document.querySelector(chartLegend)
            });
            var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
                graph: graph,
                legend: legend
            });
            //Render X Y Axes
            var xAxis = new Rickshaw.Graph.Axis.ExtendedTime(
                {
                    graph: graph,
                    orientation: "bottom",
                    //tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                    pixelsPerTick: 50,
                    tickSpacing: 6 * 60 * 60, // 6 hours
                    timeUnit: timeUnit
                });
            xAxis.render();
            var yAxis = new Rickshaw.Graph.Axis.Y.Scaled({
                graph: graph,
                berthRate: 0.0,
                orientation: 'left',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY),
                scale: y1Scale,
                label: labelY1('Pressure')
            });
            yAxis.render();

            var yAxis2 = new Rickshaw.Graph.Axis.Y.Scaled({
                graph: graph,
                berthRate: 0,
                orientation: 'right',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY2),
                scale: y2Scale,
                ticks: 5,
                label: labelY2('Command Signal')
                //tickValues: [0,20,40,60,80,100]
            });
            yAxis2.render();

            var slider = new Rickshaw.Graph.RangeSlider.Preview({
                graph: graph,
                element: document.querySelector(chartSlider)
            });
        }

        function plotHWS_OATChart(data, allPoints, points, colors, args) {
        //Set UI Args
        var container = args.Container;
        var chartId = container + " .rs-chart";
        var chartY = container + " .rs-y-axis";
        var chartLegend = container + " .rs-legend";
        var chartTitle = container + " .title";
        document.querySelector(chartTitle).innerHTML = args.Title;

        //if (!(existPoint(rawTsName, points) && existPoint(allPoints.ZoneTemp, points))) return false;
        if (!existPoint('HotWaterSupplyTemperature', points) ||
            !existPoint('OutdoorAirTemperature', points))
        {
            $(container).find(".rs-chart-area").toggle();
            return false;
        }

        //Set up data series: change this for different data sources
        data.sort(function (a, b) {
            if (a[points.OutdoorAirTemperature] < b[points.OutdoorAirTemperature])
                return -1;
            if (a[points.OutdoorAirTemperature] > b[points.OutdoorAirTemperature])
                return 1;
            return 0;
        });
        var ySeries = {};
        if (existPoint('HotWaterSupplyTemperature', points)) {
            ySeries['HotWaterSupplyTemperature'] = {
                name: 'Hot Water Supply Temperature',
                xName: points.OutdoorAirTemperature,
                color: colors.HotWaterSupplyTemperature,
                data: data.map(function (d) {
                    return {x: d[points.OutdoorAirTemperature], y: d[points.HotWaterSupplyTemperature]};
                })
            }
        }

        //Plotting
        var graph = new Rickshaw.Graph({
            element: document.querySelector(chartId),
            renderer: 'scatterplot',
            series: [ySeries['HotWaterSupplyTemperature']]
        });
        graph.renderer.dotSize = 2;
        graph.render();
        //Tooltip for hovering
//            var hoverDetail = new Rickshaw.Graph.HoverDetail({
//                graph: graph,
//                formatter: function (series, x, y) {
//                    var xValue = '<span style="padding-right:50px;">' + series.xName + ": " + parseFloat(x) + '</span>';
//                    var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
//                    var content = swatch + series.name + ": " + parseFloat(y) + '<br>' + xValue;
//                    return content;
//                }
//            });
        //Display & Toggle Legends
        var legend = new Rickshaw.Graph.Legend({
            graph: graph,
            element: document.querySelector(chartLegend)
        });
        var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
            graph: graph,
            legend: legend
        });
        //Render X Y Axes
        var xAxis = new Rickshaw.Graph.Axis.X({
            graph: graph,
            label: labelX('Outdoor Air Temperature')
        });
        xAxis.render();
        var yAxis = new Rickshaw.Graph.Axis.Y({
            graph: graph,
            berthRate: 0.0,
            orientation: 'left',
            tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
            element: document.querySelector(chartY),
            label: labelY1('Hot Water Supply Temperature')
        });
        yAxis.render();
    }

        var fTsName = 'FTimestamp';
        data = parseSortByTimestamp(data, rawTsName, fTsName, points, counts);

        //Delete key in points that have no data
        for (var prop in counts) {
            if (counts[prop] == 0) {
                delete points[prop];
            }
        }

        var timeUnit = getTimeUnit(data[0][fTsName], data[data.length - 1][fTsName], [data[0][fTsName], data[1][fTsName], data[2][fTsName]]);
        var tArgs = {
            Timestamp: fTsName,
            Title: 'Hot Water Plant Set Point Performance Analysis',
            Container: '#temp-box',
            TimeUnit: timeUnit
        };
        plotTempChart(data, allPoints, points, colors, tArgs);
        //Plot this one last because it sorts the data in-place
        var args = {
          Timestamp: fTsName,
          Title: 'Hot Water Plant Loop Differential Pressure Set Point Performance Analysis',
          Container: '#pressure-box',
          TimeUnit: timeUnit
        };
        plotPressureChart(data, allPoints, points, colors, args);
        var args = {
          Timestamp: fTsName,
          Title: 'Seasonal Hot Water Temperature Response Analysis',
          Container: '#hws-oat-box'
        };
        plotHWS_OATChart(data, allPoints, points, colors, args);

        $(".rs-chart-container.hidden").removeClass("hidden");
        //Fix styling of D3: when the min value is at the bottom of the Y axis, we can see only upper half of the value
        //$('.rickshaw_graph .y_ticks text').attr('dy', '0');

    }

    function setpointDetectorSVG(data) {
        if (data.length == 0) return;
        var rawTsName = 'datetime';

        //object to contain definition for points:
        // this should match the output_format received from the server
        var allPointsPrefix = {
            ZoneTemperature: 'ZoneTemperature',
            ZoneTemperatureSetPoint: 'ZoneTemperatureSetPoint',
            FanStatus: 'FanStatus'
        };

        var allPoints = {};
        if (data.length > 0) {
            d = data[0];
            for (var k in d){ //k is input data point name
                if (d.hasOwnProperty(k)) {
                    for (var point in allPointsPrefix) {
                        if (allPointsPrefix.hasOwnProperty(point)) {
                            if (k == allPointsPrefix[point]) {
                                allPoints[k] = k;
                            }
                        }
                    }
                }
            }
        }


        var counts = {};
        var points = {}; //Points actually used for visualization
        for (var prop in allPoints) {
            counts[prop] = 0;
            points[prop] = allPoints[prop];
        }

        var colors = {};
        var i = 0;
        for (var point in points) {
            colors[point] = getColor(i++);
        }

        function plotSetPointChart(data, allPoints, points, colors, args) {
            //Set UI Args
            var timeUnit = args.TimeUnit;
            var container = args.Container;
            var chartId = container + " .rs-chart";
            var chartY = container + " .rs-y-axis";
            var chartY2 = container + " .rs-y-axis2";
            var chartLegend = container + " .rs-legend";
            var chartTitle = container + " .title";
            var chartSlider = container + " .rs-slider";
            document.querySelector(chartTitle).innerHTML = args.Title;

            //if (!(existPoint(rawTsName, points) && existPoint(allPoints.ZoneTemp, points))) return false;
            if (!existPoint('ZoneTemperature', points))
            {
                $(container).find(".rs-chart-area").toggle();
                return false;
            }

            //TODO: Change the min max of y1Scale
            var y1Scale = d3.scale.linear().domain([60, 80]);
            var y2Scale = d3.scale.linear().domain([0, 5]);
            //Set up data series: change this for different data sources

            var ySeries = {};
            var real_data = data.filter(function(d){
                if (d['type'] == 'data') {
                    return true;
                }
                return false;
            });
            if (existPoint('ZoneTemperature', points)) {
                var filteredData = filterAndMapData(real_data, args.Timestamp, points.ZoneTemperature);
                if (filteredData.length > 0) {
                    ySeries['ZoneTemperature'] = {
                        name: 'Zone Temperature',
                        color: colors.ZoneTemperature,
                        renderer: 'line',
                        //interpolation: 'linear',
                        data: filteredData,
                        scale: y1Scale
                    }
                }
            }
            if (existPoint('FanStatus', points)) {
                var filteredData = filterAndMapData(real_data, args.Timestamp, points.FanStatus);
                if (filteredData.length > 0) {
                    ySeries['FanStatus'] = {
                        name: 'Fan Status',
                        color: colors.FanStatus,
                        renderer: 'bar',
                        //interpolation: 'linear',
                        data: filteredData,
                        scale: y2Scale
                    }
                }
            }
            if (existPoint('ZoneTemperatureSetPoint', points)) {
                //Filter out setpoint values
                setpoints = data.filter(function(d) {
                    if (d['type'] == 'setpoint')
                            return true;
                        return false;
                });
                //Build new setpoint values (based on zone temp) for displaying
                numSetpoints = setpoints.length;
                if (numSetpoints > 0) {
                    //Sort setpoints first
                    setpoints.sort(function(a,b) {return a[args.Timestamp]-b[args.Timestamp]});
                    //Interpolate setpoint values for visualization purpose
                    setpoints_viz = real_data.map(function (d) {
                        for (i=0; i<numSetpoints; i++){
                            if (d[args.Timestamp] < setpoints[i][args.Timestamp])
                                break;
                        }
                        if (i>=numSetpoints) {
                            i = numSetpoints - 1;
                        }
                        return {x: d[args.Timestamp], y: setpoints[i][points.ZoneTemperatureSetPoint]};
                    });
                    ySeries['ZoneTemperatureSetPoint'] = {
                        name: 'Zone Temperature Set Point',
                        color: colors.ZoneTemperatureSetPoint,
                        renderer: 'line',
                        //interpolation: 'step-after',
                        data: setpoints_viz,
                        scale: y1Scale
                    }
                }
            }
            //Plotting
            var plotSeries = [];
            angular.forEach(ySeries, function (value, key) {
                plotSeries.push(value);
            });
            var graph = new Rickshaw.Graph({
                element: document.querySelector(chartId),
                series: plotSeries,
                renderer: 'multi'
                //interpolation: 'linear'
            });
            graph.render();

            //Tooltip for hovering
           var hoverDetail = new Rickshaw.Graph.HoverDetail({
               graph: graph,
               formatter: function (series, x, y) {
                   var date = '<span class="date">' + new Date(x * 1000).toLocaleString() + '</span>';
                   var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
                   var content = swatch + series.name + ": " + parseFloat(y).toFixed(2) + '<br>' + date;
                   return content;
               }
           });
            //Display & Toggle Legends
            var legend = new Rickshaw.Graph.Legend({
                graph: graph,
                element: document.querySelector(chartLegend)
            });
            var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
                graph: graph,
                legend: legend
            });
            //Render X Y Axes
            var timeUnit = getTimeUnit2(graph);
            timeUnit.formatter = function(d) {
              return d.toLocaleDateString(); //d.toDateString();
            };
            var xAxis = new Rickshaw.Graph.Axis.ExtendedTime(
                {
                    graph: graph,
                    orientation: "bottom",
                    //tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                    pixelsPerTick: 50,
                    tickSpacing: 24 * 60 * 60, // 6 hours
                    timeUnit: timeUnit

                });
            xAxis.render();
            var yAxis = new Rickshaw.Graph.Axis.Y.Scaled({
                graph: graph,
                berthRate: 0.0,
                orientation: 'left',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY),
                scale: y1Scale,
                label: labelY1()
            });
            yAxis.render();

            var yAxis2 = new Rickshaw.Graph.Axis.Y.Scaled({
                graph: graph,
                berthRate: 0,
                orientation: 'right',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY2),
                scale: y2Scale,
                ticks: 5,
                label: labelY2()
                //tickValues: [0,20,40,60,80,100]
            });
            yAxis2.render();

            var slider = new Rickshaw.Graph.RangeSlider.Preview({
                graph: graph,
                element: document.querySelector(chartSlider)
            });

        }

        var fTsName = 'FTimestamp';
        data = parseSortByTimestamp(data, rawTsName, fTsName, points, counts);

        //Delete key in points that have no data
        for (var prop in counts) {
            if (counts[prop] == 0) {
                delete points[prop];
            }
        }

        var timeUnit = getTimeUnit(data[0][fTsName], data[data.length - 1][fTsName], [data[0][fTsName], data[1][fTsName], data[2][fTsName]]);
        var tArgs = {
            Timestamp: fTsName,
            Title: 'Temperature Set Point Detection',
            Container: '#temps-chart-box',
            TimeUnit: timeUnit
        };
        plotSetPointChart(data, allPoints, points, colors, tArgs);

        $(".rs-chart-container.hidden").removeClass("hidden");
    }
    function parseSortByTimestamp(data, rawTsName, fTsName, points, counts){
        data.forEach(function (d) {
            //Output from OpenEIS in the format of YYYY-MM-DD HH:mm:ss+xx:xx
            var t = d[rawTsName].split('+')[0];
            t = t.replace(' ', 'T');
            t = Date.parse(t) / 1000;
            d[fTsName] = t;
            parseDataType(d, points, counts);
        });
        data.sort(function(a,b) { return a[fTsName]-b[fTsName]; });
        return data;
    }

    function filterAndMapData(data, ts, pointName) {
        var real_data = data.filter(function(d){
            if (d[pointName] > -9999) {
                return true;
            }
            return false;
        }).map(function (d) {
            return {x: d[ts], y: setUndefinedToNull(d[pointName])};
        });
        return real_data;
    }

    function filterAndMapDataEx(data, ts, pointName, exArr) {
        var real_data = data.filter(function(d){
            if (d[pointName] > -9999) {
                return true;
            }
            return false;
        }).map(function (d) {
            var res = {x: d[ts], y: d[pointName]};
            for (var i = 0; i < exArr.length; ++i) {
                res[exArr[i]] = d[exArr[i]];
            }
            return res;
        });
        return real_data;
    }

    function cyclingDetectorSVG_Data(data) {
        var rawTsName = 'datetime';

        //object to contain definition for points:
        // this should match the output_format received from the server
        var allPointsPrefix = {
            ZoneTemperature: 'ZoneTemperature',
            ZoneTemperatureSetPoint: 'ZoneTemperatureSetPoint',
            FanStatus: 'FanStatus',
            ComprStatus: 'ComprStatus',
            cycling: 'cycling'
        };
        if (data.length == 0) return;

        var allPoints = {};
        if (data.length > 0) {
            d = data[0];
            for (var k in d){ //k is input data point name
                if (d.hasOwnProperty(k)) {
                    for (var point in allPointsPrefix) {
                        if (allPointsPrefix.hasOwnProperty(point)) {
                            if (k == allPointsPrefix[point]) {
                                allPoints[k] = k;
                            }
                        }
                    }
                }
            }
        }

        var counts = {};
        var points = {}; //Points actually used for visualization
        for (var prop in allPoints) {
            counts[prop] = 0;
            points[prop] = allPoints[prop];
        }

        var colors = {};
        var i = 0;
        for (var point in points) {
            colors[point] = getColor(i++);
        }

        function plotCyclingData(data, allPoints, points, colors, args) {
            //Set UI Args
            var timeUnit = args.TimeUnit;
            var container = args.Container;
            var chartId = container + " .rs-chart";
            var chartY = container + " .rs-y-axis";
            var chartY2 = container + " .rs-y-axis2";
            var chartLegend = container + " .rs-legend";
            var chartTitle = container + " .title";
            var chartSlider = container + " .rs-slider";
            document.querySelector(chartTitle).innerHTML = args.Title;

            //if (!(existPoint(rawTsName, points) && existPoint(allPoints.ZoneTemp, points))) return false;
            if (!existPoint('ZoneTemperature', points) &&
                !existPoint('FanStatus', points))
            {
                $(container).find(".rs-chart-area").toggle();
                return false;
            }

            //TODO: Change the min max of y1Scale
            var y1Scale = d3.scale.linear().domain([60, 80]);
            var y2Scale = d3.scale.linear().domain([0, 15]);
            //Set up data series: change this for different data sources

            var ySeries = {};
            if (existPoint('ZoneTemperature', points)) {
                var filteredData = filterAndMapData(data, args.Timestamp, points.ZoneTemperature);
                if (filteredData.length > 0) {
                    ySeries['ZoneTemperature'] = {
                        name: 'Zone Temperature',
                        color: colors.ZoneTemperature,
                        renderer: 'line',
                        interpolation: 'linear',
                        data: filteredData,
                        scale: y1Scale
                    }
                }
            }
            if (existPoint('FanStatus', points)) {
                var filteredData = filterAndMapData(data, args.Timestamp, points.FanStatus);
                if (filteredData.length > 0) {
                    ySeries['FanStatus'] = {
                        name: 'Fan Status',
                        color: colors.FanStatus,
                        //renderer: 'bar',
                        renderer: 'line',
                        interpolation: 'step-after',
                        data: filteredData,
                        scale: y2Scale
                    }
                }
            }
            if (existPoint('ZoneTemperatureSetPoint', points)) {
                var filteredData = filterAndMapData(data, args.Timestamp, points.ZoneTemperatureSetPoint);
                if (filteredData.length > 0) {
                    ySeries['ZoneTemperatureSetPoint'] = {
                        name: 'Zone Temperature SetPoint',
                        color: colors.ZoneTemperatureSetPoint,
                        renderer: 'line',
                        interpolation: 'linear',
                        data: filteredData,
                        scale: y1Scale
                    }
                }
            }
            if (existPoint('ComprStatus', points)) {
                var filteredData = filterAndMapData(data, args.Timestamp, points.ComprStatus);
                if (filteredData.length > 0) {
                    ySeries['ComprStatus'] = {
                        name: 'Compressor Status',
                        color: colors.ComprStatus,
                        renderer: 'bar',
                        //interpolation: 'step-after',
                        data: filteredData,
                        scale: y2Scale
                    }
                }
            }
            //Plotting
            var plotSeries = [];
            angular.forEach(ySeries, function (value, key) {
                plotSeries.push(value);
            });
            var graph = new Rickshaw.Graph({
                element: document.querySelector(chartId),
                series: plotSeries,
                renderer: 'multi'
                //interpolation: 'linear'
            });
            graph.render();

            //Tooltip for hovering
           var hoverDetail = new Rickshaw.Graph.HoverDetail({
               graph: graph,
               formatter: function (series, x, y) {
                   var date = '<span class="date">' + new Date(x * 1000).toLocaleString() + '</span>';
                   var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
                   var content = swatch + series.name + ": " + parseFloat(y).toFixed(2) + '<br>' + date;
                   return content;
               }
           });
            //Display & Toggle Legends
            var legend = new Rickshaw.Graph.Legend({
                graph: graph,
                element: document.querySelector(chartLegend)
            });
            var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
                graph: graph,
                legend: legend
            });
            //Render X Y Axes
            var timeUnit = getTimeUnit2(graph);
            timeUnit.formatter = function(d) {
              return d.toLocaleDateString(); //d.toDateString();
            };
            var xAxis = new Rickshaw.Graph.Axis.ExtendedTime(
                {
                    graph: graph,
                    orientation: "bottom",
                    //tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                    pixelsPerTick: 50,
                    tickSpacing: 24 * 60 * 60, // 6 hours
                    timeUnit: timeUnit

                });
            xAxis.render();
            var yAxis = new Rickshaw.Graph.Axis.Y.Scaled({
                graph: graph,
                berthRate: 0.0,
                orientation: 'left',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY),
                scale: y1Scale,
                label: labelY1()
            });
            yAxis.render();

            var yAxis2 = new Rickshaw.Graph.Axis.Y.Scaled({
                graph: graph,
                berthRate: 0,
                orientation: 'right',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY2),
                scale: y2Scale,
                ticks: 5,
                label: labelY2()
                //tickValues: [0,20,40,60,80,100]
            });
            yAxis2.render();

            var slider = new Rickshaw.Graph.RangeSlider.Preview({
                graph: graph,
                element: document.querySelector(chartSlider)
            });

        }

        function plotCyclingResult(data, points, args) {
            var cycling_data = [];
            if (existPoint('cycling', points)) {
                var penalty_point = 'penalty';
                var exArr = [penalty_point];
                var filteredData = filterAndMapDataEx(data, args.Timestamp, points.cycling, exArr);
                var real_data = filteredData.filter(function(d){
                   if (d.y > 0) return true;
                   return false;
                }).map(function (d) {
                    var res = {x: new Date(1000*d.x), y: d.y, };
                    for (var i = 0; i < exArr.length; ++i) {
                        res[exArr[i]] = d[exArr[i]];
                    }
                    return res;
                });
                if (real_data.length > 0) {
                    //Sum cycles per day
                    real_data.sort(function(a,b) { return a.x-b.x; });

                    var prevDatePart = null;
                    var curDatePart = null;
                    var curSum = 0;
                    var curPenalty = 0;
                    real_data.forEach(function(d) {
                        curDatePart = formatDate(d.x);
                        if (prevDatePart == null || curDatePart == prevDatePart) {
                            curSum += d.y;
                            curPenalty += d[penalty_point];
                            prevDatePart = curDatePart;
                        }
                        if (curDatePart != prevDatePart) {
                            cycling_data.push({x: prevDatePart, y: curSum, ex1: curPenalty});
                            curSum = d.y;
                            curPenalty = d[penalty_point];
                            prevDatePart = curDatePart;
                        }
                    });
                    //push the last one
                    cycling_data.push({x: prevDatePart, y: curSum, ex1: curPenalty});
                }
            }
            //Output HTML result
            var html = '<div><ul>';
            if (cycling_data.length > 0 )
            {
                cycling_data.forEach(function(d){
                    html += '<li>' + d.x + ': ' + d.y + ' cycles detected. Energy penalty (%): ' + d.ex1 + '</li>'
                });
            }
            html += '</ul></div>';
            document.querySelector(args.Container).innerHTML = html;
        }

        var fTsName = 'FTimestamp';
        data = parseSortByTimestamp(data, rawTsName, fTsName, points, counts);
        //Delete key in points that have no data
        for (var prop in counts) {
            if (counts[prop] == 0) {
                delete points[prop];
            }
        }

        var timeUnit = getTimeUnit(data[0][fTsName], data[data.length - 1][fTsName], [data[0][fTsName], data[1][fTsName], data[2][fTsName]]);
        var tArgs = {
            Timestamp: fTsName,
            Title: 'Compressor Cycling Diagnostics',
            Container: '#temps-chart-box',
            TimeUnit: timeUnit
        };
        plotCyclingData(data, allPoints, points, colors, tArgs);

        tArgs = {
            Timestamp: fTsName,
            Title: 'Compressor Cycling Diagnostics',
            Container: '#cycling-result'
        };
        plotCyclingResult(data, points, tArgs);

        $(".rs-chart-container.hidden").removeClass("hidden");
    }

    function scheduleDetectorSVG(data) {
        if (data.length == 0) return;
        var rawTsName = 'datetime';

        //object to contain definition for points:
        // this should match the output_format received from the server
        var allPointsPrefix = {
            ZoneTemperature: 'ZoneTemperature',
            schedule: 'schedule'
        };

        var allPoints = {};
        if (data.length > 0) {
            d = data[0];
            for (var k in d){ //k is input data point name
                if (d.hasOwnProperty(k)) {
                    for (var point in allPointsPrefix) {
                        if (allPointsPrefix.hasOwnProperty(point)) {
                            if (k == allPointsPrefix[point]) {
                                allPoints[k] = k;
                            }
                        }
                    }
                }
            }
        }

        var counts = {};
        var points = {}; //Points actually used for visualization
        for (var prop in allPoints) {
            counts[prop] = 0;
            points[prop] = allPoints[prop];
        }

        var colors = {};
        var i = 0;
        for (var point in points) {
            colors[point] = getColor(i++);
        }

        function plotScheduleChart(data, allPoints, points, colors, args) {
            //Set UI Args
            var timeUnit = args.TimeUnit;
            var container = args.Container;
            var chartId = container + " .rs-chart";
            var chartY = container + " .rs-y-axis";
            var chartY2 = container + " .rs-y-axis2";
            var chartLegend = container + " .rs-legend";
            var chartTitle = container + " .title";
            var chartSlider = container + " .rs-slider";
            document.querySelector(chartTitle).innerHTML = args.Title;

            //if (!(existPoint(rawTsName, points) && existPoint(allPoints.ZoneTemp, points))) return false;
            if (!existPoint('ZoneTemperature', points))
            {
                $(container).find(".rs-chart-area").toggle();
                return false;
            }

            //TODO: Change the min max of y1Scale
            var y1Scale = d3.scale.linear().domain([60, 80]);
            var y2Scale = d3.scale.linear().domain([0, 5]);
            //Set up data series: change this for different data sources

            var ySeries = {};
            if (existPoint('ZoneTemperature', points)) {
                var filteredData = filterAndMapData(data, args.Timestamp, points.ZoneTemperature);
                if (filteredData.length > 0) {
                    ySeries['ZoneTemperature'] = {
                        name: 'Zone Temperature',
                        color: colors.ZoneTemperature,
                        renderer: 'line',
                        //interpolation: 'linear',
                        data: filteredData,
                        scale: y1Scale
                    }
                }
            }
            if (existPoint('schedule', points)) {
                var filteredData = filterAndMapData(data, args.Timestamp, points.schedule);
                if (filteredData.length > 0) {
                    ySeries['Schedule'] = {
                        name: 'Schedule Status',
                        color: colors.schedule,
                        renderer: 'bar',
                        //interpolation: 'linear',
                        data: filteredData,
                        scale: y2Scale
                    }
                }
            }

            //Plotting
            var plotSeries = [];
            angular.forEach(ySeries, function (value, key) {
                plotSeries.push(value);
            });
            var graph = new Rickshaw.Graph({
                element: document.querySelector(chartId),
                series: plotSeries,
                renderer: 'multi',
                interpolation: 'linear'
                //interpolation: 'step-after'
            });
            graph.render();

            //Tooltip for hovering
           var hoverDetail = new Rickshaw.Graph.HoverDetail({
               graph: graph,
               formatter: function (series, x, y) {
                   var date = '<span class="date">' + new Date(x * 1000).toLocaleString() + '</span>';
                   var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
                   var content = swatch + series.name + ": " + parseFloat(y).toFixed(2) + '<br>' + date;
                   return content;
               }
           });
            //Display & Toggle Legends
            var legend = new Rickshaw.Graph.Legend({
                graph: graph,
                element: document.querySelector(chartLegend)
            });
            var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
                graph: graph,
                legend: legend
            });
            var timeUnit = getTimeUnit2(graph);
            timeUnit.formatter = function(d) {
              return d.toLocaleDateString(); //d.toDateString();
            };
            var xAxis = new Rickshaw.Graph.Axis.ExtendedTime({
                graph: graph,
                orientation: "bottom",
                //tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                pixelsPerTick: 50,
                tickSpacing: 24 * 60 * 60, // in seconds
                timeUnit: timeUnit
            });
            xAxis.render();
            var yAxis = new Rickshaw.Graph.Axis.Y.Scaled({
                graph: graph,
                berthRate: 0.0,
                orientation: 'left',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY),
                scale: y1Scale,
                label: labelY1()
            });
            yAxis.render();

            var yAxis2 = new Rickshaw.Graph.Axis.Y.Scaled({
                graph: graph,
                berthRate: 0,
                orientation: 'right',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY2),
                scale: y2Scale,
                ticks: 5,
                label: labelY2()
                //tickValues: [0,20,40,60,80,100]
            });
            yAxis2.render();

            var slider = new Rickshaw.Graph.RangeSlider.Preview({
                graph: graph,
                element: document.querySelector(chartSlider)
            });

        }

        var fTsName = 'FTimestamp';
        data = parseSortByTimestamp(data, rawTsName, fTsName, points, counts);
        //Delete key in points that have no data
        for (var prop in counts) {
            if (counts[prop] == 0) {
                delete points[prop];
            }
        }

        var timeUnit = getTimeUnit(data[0][fTsName], data[data.length - 1][fTsName], [data[0][fTsName], data[1][fTsName], data[2][fTsName]]);
        var tArgs = {
            Timestamp: fTsName,
            Title: 'Temperature Set Point Detection',
            Container: '#temps-chart-box',
            TimeUnit: timeUnit
        };
        plotScheduleChart(data, allPoints, points, colors, tArgs);

        $(".rs-chart-container.hidden").removeClass("hidden");
    }

    function loadProfileSVG(data) {
        if (data.length == 0) return;
        var rawTsName = 'datetime';

        //object to contain definition for points:
        // this should match the output_format received from the server
        var allPoints = {
            Load: 'load'
        };

        var counts = {};
        var points = {}; //Points actually used for visualization
        for (var prop in allPoints) {
            counts[prop] = 0;
            points[prop] = allPoints[prop];
        }

        var colors = {};
        var i = 0;
        // for (var point in points) {
        //     colors[point] = getColor(i++);
        // }
        for (i=0; i<5; i++)
        {
            colors[i] = getColor(i);
        }

        function plotLoadProfileChart(allPoints, points, colors, args,
                                      allDays, allWeekdays, allSatdays, allSundays, allHolidays) {
            //Set UI Args
            var container = args.Container;
            var chartId = container + " .rs-chart";
            var chartY = container + " .rs-y-axis";
            var chartLegend = container + " .rs-legend";
            var chartTitle = container + " .title";
            document.querySelector(chartTitle).innerHTML = args.Title;

            //if (!(existPoint(rawTsName, points) && existPoint(allPoints.ZoneTemp, points))) return false;
            if (!existPoint('Load', points))
            {
                $(container).find(".rs-chart-area").toggle();
                return false;
            }

            var ySeries = {};
            ySeries['DailyLoad'] = {
                    name: 'Daily Load',
                    xName: 'Hour',
                    color: colors[0],
                    data: allDays.map(function (d) {
                        return {x: d['Hour'], y: d[points.Load]};
                    })
                };
            ySeries['WeekdayLoad'] = {
                    name: 'Weekday Load',
                    xName: 'Hour',
                    color: colors[1],
                    data: allWeekdays.map(function (d) {
                        return {x: d['Hour'], y: d[points.Load]};
                    })
                };
            ySeries['SaturdayLoad'] = {
                    name: 'Saturday Load',
                    xName: 'Hour',
                    color: colors[2],
                    data: allSatdays.map(function (d) {
                        return {x: d['Hour'], y: d[points.Load]};
                    })
                };
            ySeries['SundayLoad'] = {
                    name: 'Sunday Load',
                    xName: 'Hour',
                    color: colors[3],
                    data: allSundays.map(function (d) {
                        return {x: d['Hour'], y: d[points.Load]};
                    })
                };
            ySeries['HolidayLoad'] = {
                    name: 'Holiday Load',
                    xName: 'Hour',
                    color: colors[4],
                    data: allHolidays.map(function (d) {
                        return {x: d['Hour'], y: d[points.Load]};
                    })
                };

            //Plotting
            var graph = new Rickshaw.Graph({
                element: document.querySelector(chartId),
                renderer: 'line',
                series: [
                    ySeries['DailyLoad'],
                    ySeries['WeekdayLoad'],
                    ySeries['SaturdayLoad'],
                    ySeries['SundayLoad'],
                    ySeries['HolidayLoad'],
                ]
            });
            graph.renderer.dotSize = 2;
            graph.render();
            //Tooltip for hovering
//            var hoverDetail = new Rickshaw.Graph.HoverDetail({
//                graph: graph,
//                formatter: function (series, x, y) {
//                    var xValue = '<span style="padding-right:50px;">' + series.xName + ": " + parseFloat(x) + '</span>';
//                    var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
//                    var content = swatch + series.name + ": " + parseFloat(y) + '<br>' + xValue;
//                    return content;
//                }
//            });
            //Display & Toggle Legends
            var legend = new Rickshaw.Graph.Legend({
                graph: graph,
                element: document.querySelector(chartLegend)
            });
            var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
                graph: graph,
                legend: legend
            });
            //Render X Y Axes
            var xAxis = new Rickshaw.Graph.Axis.X({
                graph: graph,
                label: labelX('Hour')
            });
            xAxis.render();
            var yAxis = new Rickshaw.Graph.Axis.Y({
                graph: graph,
                berthRate: 0.0,
                orientation: 'left',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY),
                label: labelY1('Energy (kWh)')
            });
            yAxis.render();
        }

        var fTsName = 'FTimestamp';
        data = parseSortByTimestamp(data, rawTsName, fTsName, points, counts);
        //Delete key in points that have no data
        for (var prop in counts) {
            if (counts[prop] == 0) {
                delete points[prop];
            }
        }

        //Load profile for all data'
        var args = {
          Timestamp: fTsName,
          Title: 'Daily Load Profile - All Days',
          Container: '#loadprofile-chart-box'
        };
        var allDays = parseLoadProfileAllData(data,'A');
        var allWeekdays = parseLoadProfileAllData(data,'W');
        var allSatdays = parseLoadProfileAllData(data,'Sat');
        var allSundays = parseLoadProfileAllData(data,'Sun');
        var allHolidays = parseLoadProfileAllData(data,'H');
        plotLoadProfileChart(allPoints, points, colors, args, allDays, allWeekdays, allSatdays, allSundays, allHolidays);

        $(".rs-chart-container.hidden").removeClass("hidden");
    }

    function loadProfileRxSVG(data) {
        var rawTsName = 'datetime';

        //object to contain definition for points:
        // this should match the output_format received from the server
        var allPoints = {
            Load: 'load'
        };

        var counts = {};
        var points = {}; //Points actually used for visualization
        for (var prop in allPoints) {
            counts[prop] = 0;
            points[prop] = allPoints[prop];
        }

        var colors = {};
        var i = 0;
        // for (var point in points) {
        //     colors[point] = getColor(i++);
        // }
        for (i=0; i<5; i++)
        {
            colors[i] = getColor(i);
        }

        function plotLoadProfileRxChart(allPoints, points, colors, args, predays, postdays) {
            //Set UI Args
            var container = args.Container;
            var chartId = container + " .rs-chart";
            var chartY = container + " .rs-y-axis";
            var chartLegend = container + " .rs-legend";
            var chartTitle = container + " .title";
            document.querySelector(chartTitle).innerHTML = args.Title;

            //if (!(existPoint(rawTsName, points) && existPoint(allPoints.ZoneTemp, points))) return false;
            if (!existPoint('Load', points))
            {
                $(container).find(".rs-chart-area").toggle();
                return false;
            }

            var ySeries = {};
            ySeries['PreLoad'] = {
                    name: 'Pre Rx Load',
                    xName: 'Hour',
                    color: colors[0],
                    data: predays.map(function (d) {
                        return {x: d['Hour'], y: d[points.Load]};
                    })
                };
            ySeries['PostLoad'] = {
                    name: 'Post Rx Load',
                    xName: 'Hour',
                    color: colors[1],
                    data: postdays.map(function (d) {
                        return {x: d['Hour'], y: d[points.Load]};
                    })
                };

            //Plotting
            var graph = new Rickshaw.Graph({
                element: document.querySelector(chartId),
                renderer: 'line',
                series: [
                    ySeries['PreLoad'],
                    ySeries['PostLoad']
                ]
            });
            graph.renderer.dotSize = 2;
            graph.render();
            //Tooltip for hovering
//            var hoverDetail = new Rickshaw.Graph.HoverDetail({
//                graph: graph,
//                formatter: function (series, x, y) {
//                    var xValue = '<span style="padding-right:50px;">' + series.xName + ": " + parseFloat(x) + '</span>';
//                    var swatch = '<span class="detail_swatch" style="background-color: ' + series.color + '"></span>';
//                    var content = swatch + series.name + ": " + parseFloat(y) + '<br>' + xValue;
//                    return content;
//                }
//            });
            //Display & Toggle Legends
            var legend = new Rickshaw.Graph.Legend({
                graph: graph,
                element: document.querySelector(chartLegend)
            });
            var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
                graph: graph,
                legend: legend
            });
            //Render X Y Axes
            var xAxis = new Rickshaw.Graph.Axis.X({
                graph: graph,
                label: labelX('Hour')
            });
            xAxis.render();
            var yAxis = new Rickshaw.Graph.Axis.Y({
                graph: graph,
                berthRate: 0.0,
                orientation: 'left',
                tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
                element: document.querySelector(chartY),
                label: labelY1('Energy (kWh)')
            });
            yAxis.render();
        }

        var fTsName = 'FTimestamp';
        data = parseSortByTimestamp(data, rawTsName, fTsName, points, counts);
        //Delete key in points that have no data
        for (var prop in counts) {
            if (counts[prop] == 0) {
                delete points[prop];
            }
        }

        //Load profile for all data'
        var alldays_args = {
          Timestamp: fTsName,
          Title: 'Daily Load Profile - All Days',
          Container: '#loadprofile-alldays-chart-box'
        };
        var weekdays_args = {
          Timestamp: fTsName,
          Title: 'Daily Load Profile - Week Days',
          Container: '#loadprofile-weekdays-chart-box'
        };
        var sat_args = {
          Timestamp: fTsName,
          Title: 'Daily Load Profile - Saturday',
          Container: '#loadprofile-sat-chart-box'
        };
        var sun_args = {
          Timestamp: fTsName,
          Title: 'Daily Load Profile - Sunday',
          Container: '#loadprofile-sun-chart-box'
        };
        var holidays_args = {
          Timestamp: fTsName,
          Title: 'Daily Load Profile - Holidays',
          Container: '#loadprofile-holidays-chart-box'
        };
        var pre_allDays = parseLoadProfileAllDataRx(data,'A','pre');
        var pre_allWeekdays = parseLoadProfileAllDataRx(data,'W','pre');
        var pre_allSatdays = parseLoadProfileAllDataRx(data,'Sat','pre');
        var pre_allSundays = parseLoadProfileAllDataRx(data,'Sun','pre');
        var pre_allHolidays = parseLoadProfileAllDataRx(data,'H','pre');
        var post_allDays = parseLoadProfileAllDataRx(data,'A','post');
        var post_allWeekdays = parseLoadProfileAllDataRx(data,'W','post');
        var post_allSatdays = parseLoadProfileAllDataRx(data,'Sat','post');
        var post_allSundays = parseLoadProfileAllDataRx(data,'Sun','post');
        var post_allHolidays = parseLoadProfileAllDataRx(data,'H','post');
        plotLoadProfileRxChart(allPoints, points, colors, alldays_args, pre_allDays, post_allDays);
        plotLoadProfileRxChart(allPoints, points, colors, weekdays_args, pre_allWeekdays, post_allWeekdays);
        plotLoadProfileRxChart(allPoints, points, colors, sat_args, pre_allSatdays, post_allSatdays);
        plotLoadProfileRxChart(allPoints, points, colors, sun_args, pre_allSundays, post_allSundays);
        plotLoadProfileRxChart(allPoints, points, colors, holidays_args, pre_allHolidays, post_allHolidays);

        $(".rs-chart-container.hidden").removeClass("hidden");
    }

    function parseLoadProfileAllData(data, filter) {
        //filter: 'A' alldays, 'W', 'H', 'Sat', 'Sun', 'H'

        sums = [];
        counts = [];
        avgs = [];
        result = [];
        for (i=0; i<24; i++)
        {
            sums[i] = 0;
            counts[i] = 0;
            avgs[i] = 0;
        }

        data.forEach(function(d) {
            if (filter=='A' || d.daytype==filter) {
                var dt1 = parseDate(d.datetime);
                var dateParts = formatDate(dt1);
                var hr = dt1.getHours(); //0-based
                sums[hr] += d.load;
                counts[hr] += 1;
            }
        });

        for (i=0; i<24; i++) {
            if (counts[i]>0)
                avgs[i] = sums[i]/counts[i];
            result.push({'Hour': i, 'load':avgs[i]});
        }
        return result;
    }

    function parseLoadProfileAllDataRx(data, daytype_filter, rx_filter) {
        //daytype_filter: 'A' alldays, 'W', 'H', 'Sat', 'Sun', 'H'

        sums = [];
        counts = [];
        avgs = [];
        result = [];
        for (i=0; i<24; i++)
        {
            sums[i] = 0;
            counts[i] = 0;
            avgs[i] = 0;
        }

        data.forEach(function(d) {
            if ((daytype_filter=='A' || d.daytype==daytype_filter) && d.rxtype==rx_filter) {
                var dt1 = parseDate(d.datetime);
                var dateParts = formatDate(dt1);
                var hr = dt1.getHours(); //0-based
                sums[hr] += d.load;
                counts[hr] += 1;
            }
        });

        for (i=0; i<24; i++) {
            if (counts[i]>0)
                avgs[i] = sums[i]/counts[i];
            result.push({'Hour': i, 'load':avgs[i]});
        }
        return result;
    }

});

